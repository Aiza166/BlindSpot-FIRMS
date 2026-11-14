import { afterEach, describe, expect, it, vi } from "vitest";
import { AssetMissing, clearMemo, computeNrt, NrtError, parseFirmsCsv, snapBbox, TokenBucket, windows, type DetCache } from "./_lib/nrt-core";
import { limiter, onRequestGet } from "./api/nrt";
import { bboxParam, nrtMonthAllowed } from "../lib/nrt";
import { knownRegions } from "../lib/reliability";

// Hand-made fixtures, not FIRMS data. The key below is a dummy used to check redaction.
const KEY = "dummykey0123456789abcdef01234567";
const NOW = new Date("2026-11-14T06:00:00Z");
const HEAD = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight";
const row = (lat: number, lon: number, date: string, time: string, conf: string) => `${lat},${lon},330.1,0.4,0.4,${date},${time},N20,VIIRS,${conf},2.0NRT,290.2,5.1,D`;

const assets: Record<string, unknown> = {
  "data/constants.json": { coverage_box: { lon_min: 60, lon_max: 80, lat_min: 23, lat_max: 37 }, nrt_label: "near-real-time, provisional" },
  "data/nrt/mask_cells.json": { grid_deg: 0.01, cells: [[3050, 7550]] },
  "data/index.json": { regions: { IN_Punjab: "regions/in_punjab.json" }, districts: [{ id: "D1", bbox: [75, 30, 76, 32] }, { id: "EDGE", bbox: [79.5, 30, 80.00004, 31] }] },
  "data/districts/EDGE.json": { median: { NOAA20: { values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], baseline_years: [2019, 2025] } } },
  "data/districts/D1.json": { median: { NOAA20: { values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 40, 5], baseline_years: [2019, 2025] } } },
  "data/districts.geojson": { features: [{ properties: { id: "D1" }, geometry: { type: "Polygon", coordinates: [[[75, 30], [76, 30], [76, 31], [75, 31], [75, 30]]] } }] },
};
const readAsset = async (p: string) => { if (!Object.hasOwn(assets, p)) throw new AssetMissing(p); return assets[p]; };

function firmsMock(csvByStart: Record<string, string>) {
  return vi.fn(async (url: string) => {
    const start = url.split("/").pop()!;
    return new Response(csvByStart[start] ?? HEAD + "\n", { status: 200 });
  });
}

afterEach(() => { clearMemo(); limiter.reset(); });

describe("windows", () => {
  it("covers the local solar month from the previous UTC day up to today, ≤ 5 days each", () => {
    const w = windows("2026-11", NOW);
    expect(w[0]).toEqual({ start: "2026-10-31", days: 5 });
    expect(w.reduce((s, x) => s + x.days, 0)).toBe(15); // 31 Oct .. 14 Nov
    expect(w.every((x) => x.days <= 5)).toBe(true);
  });
});

describe("parseFirmsCsv", () => {
  it("keeps nominal/high confidence and converts to local solar date", () => {
    const d = parseFirmsCsv([HEAD, row(30.2, 75.2, "2026-10-31", "2100", "n"), row(30.2, 75.2, "2026-11-02", "0800", "l"), row(30.3, 75.3, "2026-11-02", "0800", "high")].join("\n"));
    expect(d).toHaveLength(2);
    expect(d[0]!.localDate).toBe("2026-11-01"); // 21:00 UTC + 5 h 01 min
  });
  it("rejects a plain-text FIRMS error", () => {
    expect(() => parseFirmsCsv("Invalid MAP_KEY.")).toThrow(NrtError);
  });
});

describe("computeNrt", () => {
  const csv = [HEAD,
    row(30.2, 75.2, "2026-11-01", "0800", "n"), // kept
    row(30.505, 75.505, "2026-11-01", "0800", "h"), // masked cell 3050,7550
    row(30.4, 75.4, "2026-11-02", "0800", "l"), // low confidence
    row(30.4, 75.4, "2026-10-30", "0800", "n"), // October local date
    row(31.5, 75.5, "2026-11-03", "0800", "n"), // in bbox, outside the polygon
  ].join("\n");

  it("filters, masks, clips to the polygon and attaches the NOAA-20 median", async () => {
    const fetchFirms = firmsMock({ "2026-10-31": csv });
    const body = await computeNrt(new URLSearchParams({ bbox: "75,30,76,32", area: "D1" }), { key: KEY, fetchFirms, readAsset, now: () => NOW });
    expect(body).toMatchObject({ status: "ok", provisional: true, month: "2026-11", noaa20: 1, masked: 1, daysCovered: 14, daysInMonth: 30, geometry: "polygon", median: { value: 40, years: [2019, 2025] }, label: "near-real-time, provisional" });
    expect(fetchFirms).toHaveBeenCalledTimes(3);
    expect(fetchFirms.mock.calls[0]![0]).toContain("/VIIRS_NOAA20_NRT/75,30,76,32/5/2026-10-31");
    expect(JSON.stringify(body)).not.toContain(KEY);
  });

  it("caches for 3 h", async () => {
    const fetchFirms = firmsMock({ "2026-10-31": csv });
    const p = new URLSearchParams({ bbox: "75,30,76,32" });
    await computeNrt(p, { key: KEY, fetchFirms, readAsset, now: () => NOW });
    await computeNrt(p, { key: KEY, fetchFirms, readAsset, now: () => new Date(NOW.getTime() + 2.9 * 3600e3) });
    expect(fetchFirms).toHaveBeenCalledTimes(3);
    await computeNrt(p, { key: KEY, fetchFirms, readAsset, now: () => new Date(NOW.getTime() + 3.1 * 3600e3) });
    expect(fetchFirms).toHaveBeenCalledTimes(6);
  });

  it("bbox-only areas have no median", async () => {
    const body = await computeNrt(new URLSearchParams({ bbox: "75,30,76,32" }), { key: KEY, fetchFirms: firmsMock({ "2026-10-31": csv }), readAsset, now: () => NOW });
    expect(body.median).toBeNull();
    expect(body.geometry).toBe("bbox");
    expect(body.noaa20).toBe(2);
  });

  it("validates input and refuses without a key", async () => {
    const deps = { key: KEY, fetchFirms: firmsMock({}), readAsset, now: () => NOW };
    await expect(computeNrt(new URLSearchParams({ bbox: "50,30,55,32" }), deps)).rejects.toMatchObject({ status: 400 });
    await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32", area: "../x" }), deps)).rejects.toMatchObject({ status: 400 });
    await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32" }), { ...deps, key: undefined })).rejects.toMatchObject({ status: 503 });
  });

  it("redacts the key from network errors", async () => {
    const fetchFirms = vi.fn(async (url: string) => { throw new Error(`connect failed for ${url}`); });
    const err = await computeNrt(new URLSearchParams({ bbox: "75,30,76,32" }), { key: KEY, fetchFirms, readAsset, now: () => NOW }).then(() => new Error("no error"), (e: Error) => e);
    expect(err.message).not.toContain(KEY);
    expect(err.message).toContain("[MAP_KEY]");
  });
});

describe("onRequestGet (Pages Function)", () => {
  it("returns JSON with cache headers and no key", async () => {
    const realFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(async (u: string | URL | Request) => new Response(String(u).endsWith("2026-10-31") ? [HEAD, row(30.2, 75.2, "2026-11-01", "0800", "n")].join("\n") : HEAD)) as typeof fetch;
    vi.useFakeTimers(); vi.setSystemTime(NOW);
    try {
      const env = { FIRMS_MAP_KEY: KEY, ASSETS: { fetch: async (u: Request | string) => { const p = new URL(String(u)).pathname.slice(1); return p in assets ? Response.json(assets[p]) : new Response("", { status: 404 }); } } };
      const r = await onRequestGet({ request: new Request("https://x.test/api/nrt?bbox=75,30,76,32"), env });
      const text = await r.text();
      expect(r.status).toBe(200);
      expect(r.headers.get("cache-control")).toContain("s-maxage=10800");
      expect(JSON.parse(text).noaa20).toBe(1);
      expect(text).not.toContain(KEY);
      const bad = await onRequestGet({ request: new Request("https://x.test/api/nrt?bbox=75,30,76,32&area=NOPE"), env });
      expect(bad.status).toBe(404);
      expect(await bad.text()).not.toContain(KEY);
    } finally { globalThis.fetch = realFetch; vi.useRealTimers(); }
  });
});

const COV = { lon_min: 60, lon_max: 80, lat_min: 23, lat_max: 37 };
const deps0 = (over: Partial<Parameters<typeof computeNrt>[1]> = {}) => ({ key: KEY, fetchFirms: firmsMock({}), readAsset, now: () => NOW, ...over });

describe("review fixes (docs/review/TS_REACT_REVIEW.md)", () => {
  it("HIGH-1: snaps the FIRMS bbox to a 0.25° grid so shifted boxes share one cache entry", async () => {
    expect(snapBbox([75.0001, 30.1, 75.9, 30.6], COV)).toEqual([75, 30, 76, 30.75]);
    const fetchFirms = firmsMock({});
    await computeNrt(new URLSearchParams({ bbox: "75.0001,30.1,75.9,30.6" }), deps0({ fetchFirms }));
    await computeNrt(new URLSearchParams({ bbox: "75.0002,30.1,75.9,30.6" }), deps0({ fetchFirms }));
    expect(fetchFirms).toHaveBeenCalledTimes(3);
    expect(fetchFirms.mock.calls[0]![0]).toContain("/75,30,76,30.75/");
  });
  it("HIGH-1: unknown area ids are refused before any FIRMS call", async () => {
    const fetchFirms = firmsMock({});
    await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32", area: "NOPE" }), deps0({ fetchFirms }))).rejects.toMatchObject({ status: 404, code: "unknown_area" });
    expect(fetchFirms).not.toHaveBeenCalled();
  });
  it("HIGH-1: never more than 7 FIRMS calls per request", async () => {
    const fetchFirms = firmsMock({});
    await computeNrt(new URLSearchParams({ bbox: "75,30,76,32", month: "2026-10" }), deps0({ fetchFirms }));
    expect(fetchFirms.mock.calls.length).toBeLessThanOrEqual(7);
  });
  it("HIGH-1: token bucket allows a burst then refuses until refill", () => {
    const b = new TokenBucket(2, 1);
    expect([b.take("a", 0), b.take("a", 0), b.take("a", 0)]).toEqual([true, true, false]);
    expect(b.take("b", 0)).toBe(true);
    expect(b.take("a", 1000)).toBe(true);
  });
  it("HIGH-2: only the current and previous UTC month", async () => {
    for (const month of ["2005-03", "0001-01", "2026-09", "2026-12"]) {
      await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32", month }), deps0())).rejects.toMatchObject({ status: 400, code: "month_out_of_window", message: expect.stringContaining("near-real-time window") });
    }
    await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32", month: "2026-10" }), deps0())).resolves.toMatchObject({ month: "2026-10", daysCovered: 31 });
    expect(nrtMonthAllowed("2026-11", NOW)).toBe(true);
    expect(nrtMonthAllowed("2026-10", NOW)).toBe(true);
    expect(nrtMonthAllowed("2026-09", NOW)).toBe(false);
    expect(nrtMonthAllowed("2025-12", new Date("2026-01-03T00:00:00Z"))).toBe(true);
  });
  it("MEDIUM-1: a hanging FIRMS call ends in 504", async () => {
    const fetchFirms = vi.fn((_u: string, signal?: AbortSignal) => new Promise<Response>((_r, rej) => signal?.addEventListener("abort", () => rej(signal.reason))));
    await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32" }), deps0({ fetchFirms, timeoutMs: 20 }))).rejects.toMatchObject({ status: 504, code: "timeout" });
  });
  it("MEDIUM-2: clamps a bbox that pokes past the coverage box; edge district works", async () => {
    const body = await computeNrt(new URLSearchParams({ bbox: "79.5,30,80.0001,31" }), deps0());
    expect(body.status).toBe("ok");
    await expect(computeNrt(new URLSearchParams({ bbox: "79.5,30,80.0001,31", area: "EDGE" }), deps0())).resolves.toMatchObject({ status: "ok" });
    await expect(computeNrt(new URLSearchParams({ bbox: "81,30,82,31" }), deps0())).rejects.toMatchObject({ status: 400 });
    expect(bboxParam([75.12345, 30.98761, 77.84999, 31.00001])).toBe("75.1234,30.9876,77.8500,31.0001");
  });
  it("MEDIUM-3: prototype keys are not areas", async () => {
    for (const area of ["constructor", "__proto__", "toString"]) {
      await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32", area }), deps0())).rejects.toMatchObject({ status: 404, code: "unknown_area" });
    }
  });
  it("MEDIUM-4: a missing core file is a 500 missing_data, not 'unknown area'", async () => {
    const ra = async (p: string) => { if (p === "data/nrt/mask_cells.json") throw new AssetMissing(p); return readAsset(p); };
    await expect(computeNrt(new URLSearchParams({ bbox: "75,30,76,32" }), deps0({ readAsset: ra }))).rejects.toMatchObject({ status: 500, code: "missing_data", message: expect.stringContaining("nrt/mask_cells.json") });
  });
  it("LOW-1: stale or old-format shared-cache entries are ignored; fresh ones are used", async () => {
    const store = new Map<string, DetCache>();
    const cache = { get: async (k: string) => store.get(k), put: async (k: string, v: DetCache) => { store.set(k, v); } };
    const fetchFirms = firmsMock({});
    const p = new URLSearchParams({ bbox: "75,30,76,32" });
    await computeNrt(p, deps0({ fetchFirms, cache }));
    clearMemo();
    await computeNrt(p, deps0({ fetchFirms, cache, now: () => new Date(NOW.getTime() + 3600e3) }));
    expect(fetchFirms).toHaveBeenCalledTimes(3); // shared hit
    const [k, v] = [...store][0]!;
    store.set(k, { ...v, fetchedAt: new Date(NOW.getTime() - 4 * 3600e3).toISOString() });
    clearMemo();
    await computeNrt(p, deps0({ fetchFirms, cache }));
    expect(fetchFirms).toHaveBeenCalledTimes(6); // stale hit refetched
    store.set(k, { ...store.get(k)!, v: 1 });
    clearMemo();
    await computeNrt(p, deps0({ fetchFirms, cache }));
    expect(fetchFirms).toHaveBeenCalledTimes(9); // old version refetched
  });
  it("LOW-3: daysCovered uses the local solar date at the bbox centre", async () => {
    const late = new Date("2026-11-14T20:00:00Z"); // 75.5°E: 01:02 local on 15 Nov
    const body = await computeNrt(new URLSearchParams({ bbox: "75,30,76,32" }), deps0({ now: () => late }));
    expect(body.daysCovered).toBe(15);
  });
  it("LOW-5: regions without an index entry are dropped", () => {
    expect(knownRegions(["IN_Punjab", "X", "constructor"], { IN_Punjab: "a.json" })).toEqual(["IN_Punjab"]);
  });
});

describe("onRequestGet: origin, rate limit, error codes", () => {
  const env = (extra: Record<string, string> = {}) => ({ FIRMS_MAP_KEY: KEY, ...extra, ASSETS: { fetch: async (u: Request | string) => { const p = new URL(String(u)).pathname.slice(1); return Object.hasOwn(assets, p) ? Response.json(assets[p]) : new Response("<html>fallback</html>", { status: 200, headers: { "content-type": "text/html" } }); } } });
  const req = (q: string, h: Record<string, string> = {}) => new Request(`https://x.test/api/nrt?${q}`, { headers: h });
  it("refuses foreign origins, allows ALLOWED_ORIGIN and same origin, never '*'", async () => {
    const bad = await onRequestGet({ request: req("bbox=75,30,76,32&month=1999-01", { origin: "https://evil.test" }), env: env() });
    expect(bad.status).toBe(403);
    const ok = await onRequestGet({ request: req("bbox=75,30,76,32&month=1999-01", { origin: "https://site.test" }), env: env({ ALLOWED_ORIGIN: "https://site.test" }) });
    expect(ok.headers.get("access-control-allow-origin")).toBe("https://site.test");
    const same = await onRequestGet({ request: req("bbox=75,30,76,32&month=1999-01"), env: env() });
    expect(same.headers.get("access-control-allow-origin")).toBeNull();
    expect((await same.json()).code).toBe("month_out_of_window");
  });
  it("rate-limits per IP with 429", async () => {
    let last = 0;
    for (let i = 0; i < 25; i++) last = (await onRequestGet({ request: req("bbox=x", { "cf-connecting-ip": "203.0.113.9" }), env: env() })).status;
    expect(last).toBe(429);
    expect((await onRequestGet({ request: req("bbox=x", { "cf-connecting-ip": "203.0.113.10" }), env: env() })).status).toBe(400);
  });
  it("an HTML fallback for a core file is a 500 missing_data", async () => {
    const e = env();
    const broken = { ...e, ASSETS: { fetch: async (u: Request | string) => String(u).includes("constants") ? new Response("<html/>", { headers: { "content-type": "text/html" } }) : e.ASSETS.fetch(u) } };
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const r = await onRequestGet({ request: req("bbox=75,30,76,32"), env: broken });
    expect(r.status).toBe(500);
    expect((await r.json()).code).toBe("missing_data");
    spy.mockRestore();
  });
});
