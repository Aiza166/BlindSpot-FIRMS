// Near-real-time NOAA-20 count for an area (PLAN §6, D-010, D-040). Runs only on the server:
// the FIRMS MAP_KEY comes from the host environment and never leaves this module, not even in
// error messages or logs. Pure logic with injected fetch/cache/assets so it can be unit-tested.

export const SOURCE = "VIIRS_NOAA20_NRT";
export const FIRMS_AREA = "https://firms.modaps.eosdis.nasa.gov/api/area/csv";
export const CACHE_SECONDS = 3 * 60 * 60;
/** Bumped when the body or detection-cache format changes, so old shared-cache entries are ignored. */
export const CACHE_VERSION = 2;
/** FIRMS requests use a bbox snapped outward to this grid, so cache keys repeat (review HIGH-1). */
export const SNAP_DEG = 0.25;
/** Hard cap on FIRMS calls per request (a 31-day month + 1 lead day = 7 five-day windows). */
export const MAX_FIRMS_CALLS = 7;
/** Per-call FIRMS timeout and overall time budget (review MEDIUM-1). */
export const FIRMS_TIMEOUT_MS = 10_000;
export const FIRMS_BUDGET_MS = 25_000;
const MAX_DAY_RANGE = 5; // FIRMS area API limit (docs/DATA_SCHEMA.md §4)
const EPS = 1e-9; // same guard as pipeline/blindspot/mask.py cell_index
const KEEP_CONF = new Set(["n", "h", "nominal", "high"]); // VIIRS confidence n/h (CLAUDE.md rule 3)

export type Bbox = [number, number, number, number];

export interface NrtDeps {
  /** FIRMS_MAP_KEY from the server environment. */
  key: string | undefined;
  /** fetch for FIRMS (outbound); must honour the signal. */
  fetchFirms: (url: string, signal?: AbortSignal) => Promise<Response>;
  /** Reads a static data file, e.g. "data/constants.json" (same deployment). Throws AssetMissing. */
  readAsset: (path: string) => Promise<unknown>;
  /** Clock, injectable for tests. */
  now?: () => Date;
  /** Optional shared cache (e.g. Cloudflare caches.default); an in-memory map is always used too. */
  cache?: { get(k: string): Promise<DetCache | undefined>; put(k: string, v: DetCache): Promise<void> };
  /** Per-call FIRMS timeout, injectable for tests. */
  timeoutMs?: number;
}

/** Cached FIRMS result for one snapped bbox and month (shared across exact bboxes inside it). */
export interface DetCache { v: number; fetchedAt: string; dets: Detection[] }

export interface NrtBody {
  status: "ok";
  provisional: true;
  label: string;
  source: typeof SOURCE;
  month: string;
  /** NOAA-20 NRT hotspots, filtered (confidence n/h), local solar month, persistent mask applied. */
  noaa20: number;
  /** Detections removed by the persistent-hotspot mask. */
  masked: number;
  /** Local solar days of the month covered so far, and days in the month. */
  daysCovered: number;
  daysInMonth: number;
  /** NOAA-20 standard-archive median of the same calendar month (D-010); null for custom areas. */
  median: { value: number | null; years: [number, number] } | null;
  /** Counted inside the area's polygon (district or region) or only its bounding box. */
  geometry: "polygon" | "bbox";
  fetchedAt: string;
}

export type NrtCode = "bad_request" | "unknown_area" | "month_out_of_window" | "not_configured" | "upstream" | "timeout" | "missing_data" | "rate_limited" | "forbidden_origin" | "internal";

export class NrtError extends Error {
  constructor(public status: number, message: string, public code: NrtCode = status === 400 ? "bad_request" : "internal") { super(message); }
}

/** Thrown by readAsset when a static file is absent or not JSON (e.g. an HTML fallback page). */
export class AssetMissing extends Error {
  constructor(public path: string) { super(`data file missing: ${path}`); }
}

interface Constants { coverage_box: { lon_min: number; lon_max: number; lat_min: number; lat_max: number }; nrt_label: string }
interface MaskDoc { grid_deg: number; cells: [number, number][] }
interface AreaDoc { median: Record<string, { values: (number | null)[]; baseline_years: [number, number] }> }
interface IndexDoc { regions: Record<string, string>; districts?: { id: string; bbox?: Bbox }[] }
type Geometry = { type: "Polygon"; coordinates: number[][][] } | { type: "MultiPolygon"; coordinates: number[][][][] };

const memo = new Map<string, { at: number; det: DetCache }>();
export function clearMemo(): void { memo.clear(); }

export function redact(text: string, key: string | undefined): string {
  return key ? text.split(key).join("[MAP_KEY]") : text;
}

const ym = (t: number) => new Date(t).toISOString().slice(0, 7);

/** The months FIRMS NRT serves here: the current and the previous UTC month (review HIGH-2). */
export function allowedMonths(now: Date): [string, string] {
  const cur = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1);
  return [ym(cur), ym(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, 1))];
}

/** Snaps a bbox outward to the SNAP_DEG grid and clamps it to the coverage box. */
export function snapBbox([w, s, e, n]: Bbox, cov: Constants["coverage_box"]): Bbox {
  const f = (v: number) => Math.floor(v / SNAP_DEG + EPS) * SNAP_DEG, c = (v: number) => Math.ceil(v / SNAP_DEG - EPS) * SNAP_DEG;
  return [Math.max(cov.lon_min, f(w)), Math.max(cov.lat_min, f(s)), Math.min(cov.lon_max, c(e)), Math.min(cov.lat_max, c(n))];
}

export function parseQuery(params: URLSearchParams, cov: Constants["coverage_box"], now: Date): { bbox: Bbox; month: string; area: string | null } {
  const parts = (params.get("bbox") ?? "").split(",").map(Number);
  if (parts.length !== 4 || parts.some((v) => !Number.isFinite(v))) throw new NrtError(400, "bbox must be west,south,east,north in decimal degrees");
  const [w0, s0, e0, n0] = parts as Bbox;
  if (!(w0 < e0 && s0 < n0)) throw new NrtError(400, "bbox needs west < east and south < north");
  // Clamp to the coverage box instead of rejecting edge districts (review MEDIUM-2).
  const w = Math.max(w0, cov.lon_min), s = Math.max(s0, cov.lat_min), e = Math.min(e0, cov.lon_max), n = Math.min(n0, cov.lat_max);
  if (!(w < e && s < n)) throw new NrtError(400, "bbox is outside the coverage box");
  if ((e - w) * (n - s) > 50) throw new NrtError(400, "bbox larger than 50 square degrees; choose a smaller area");
  const allowed = allowedMonths(now);
  const month = params.get("month") ?? allowed[0];
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) throw new NrtError(400, "month must be YYYY-MM");
  if (!allowed.includes(month)) throw new NrtError(400, `month outside the near-real-time window (only ${allowed[0]} and ${allowed[1]})`, "month_out_of_window");
  const area = params.get("area");
  if (area !== null && !/^[A-Za-z0-9_]{1,64}$/.test(area)) throw new NrtError(400, "area must be a district or region id");
  return { bbox: [w, s, e, n], month, area };
}

export function daysIn(month: string): number {
  const [y, m] = month.split("-").map(Number) as [number, number];
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

/** UTC request windows (start date, day range ≤ 5) covering the local solar month up to today. */
export function windows(month: string, now: Date): { start: string; days: number }[] {
  const [y, m] = month.split("-").map(Number) as [number, number];
  // Local solar time runs ahead of UTC by lon/15 h (≤ 5.4 h in the box), so the first local day
  // starts on the previous UTC day.
  const first = Date.UTC(y, m - 1, 1) - 86400000;
  const lastOfMonth = Date.UTC(y, m - 1, daysIn(month));
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const last = Math.min(lastOfMonth, today);
  const out: { start: string; days: number }[] = [];
  for (let t = first; t <= last; t += MAX_DAY_RANGE * 86400000) {
    const days = Math.min(MAX_DAY_RANGE, Math.round((last - t) / 86400000) + 1);
    out.push({ start: new Date(t).toISOString().slice(0, 10), days });
  }
  return out;
}

export interface Detection { lat: number; lon: number; localDate: string }

/** Parses a FIRMS area-API CSV; keeps confidence n/h; returns local solar dates. */
export function parseFirmsCsv(text: string): Detection[] {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
  if (lines.length === 0) return [];
  const head = lines[0]!.split(",").map((h) => h.trim().toLowerCase());
  const ix = (k: string) => head.indexOf(k);
  const iLat = ix("latitude"), iLon = ix("longitude"), iDate = ix("acq_date"), iTime = ix("acq_time"), iConf = ix("confidence");
  // FIRMS answers HTTP 200 with a plain-text message for errors (bad key, limit), DATA_SCHEMA §4.
  if (iLat < 0 || iLon < 0 || iDate < 0 || iTime < 0 || iConf < 0) throw new NrtError(502, "FIRMS did not return a CSV (check the key and the transaction limit)");
  const out: Detection[] = [];
  for (const line of lines.slice(1)) {
    const c = line.split(",");
    if (!KEEP_CONF.has((c[iConf] ?? "").trim().toLowerCase())) continue;
    const lat = Number(c[iLat]), lon = Number(c[iLon]);
    const t = (c[iTime] ?? "").trim().padStart(4, "0");
    const utc = Date.parse(`${(c[iDate] ?? "").trim()}T${t.slice(0, 2)}:${t.slice(2, 4)}:00Z`);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(utc)) continue;
    const local = new Date(utc + (lon / 15) * 3600000);
    out.push({ lat, lon, localDate: local.toISOString().slice(0, 10) });
  }
  return out;
}

function inRing(lon: number, lat: number, ring: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i]![0]!, yi = ring[i]![1]!, xj = ring[j]![0]!, yj = ring[j]![1]!;
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
export function inGeometry(lon: number, lat: number, g: Geometry): boolean {
  const poly = (rings: number[][][]) => !!rings[0] && inRing(lon, lat, rings[0]) && !rings.slice(1).some((h) => inRing(lon, lat, h));
  return g.type === "Polygon" ? poly(g.coordinates) : g.coordinates.some(poly);
}

async function core(path: string, deps: NrtDeps): Promise<unknown> {
  try { return await deps.readAsset(path); } catch (e) {
    if (e instanceof AssetMissing) throw new NrtError(500, `server data file missing (${path.replace(/^data\//, "")})`, "missing_data");
    throw e;
  }
}

async function loadArea(id: string, deps: NrtDeps): Promise<{ doc: AreaDoc; geom: Geometry | null; bbox: Bbox | null }> {
  const index = (await core("data/index.json", deps)) as IndexDoc;
  // Only ids listed in index.json; own keys only, so "constructor" or "__proto__" never match (MEDIUM-3).
  if (Object.hasOwn(index.regions, id)) {
    const doc = (await core(`data/${index.regions[id]}`, deps)) as AreaDoc & { bbox?: Bbox };
    const cal = (await core("data/results/calibration.json", deps)) as { punjab_polygons: Record<string, Geometry> };
    return { doc, geom: Object.hasOwn(cal.punjab_polygons, id) ? cal.punjab_polygons[id]! : null, bbox: doc.bbox ?? null };
  }
  const entry = (index.districts ?? []).find((d) => d.id === id);
  if (!entry) throw new NrtError(404, "unknown area", "unknown_area");
  const doc = (await core(`data/districts/${id}.json`, deps)) as AreaDoc;
  const gj = (await core("data/districts.geojson", deps)) as { features: { properties: { id: string }; geometry: Geometry }[] };
  return { doc, geom: gj.features.find((f) => f.properties.id === id)?.geometry ?? null, bbox: entry.bbox ?? null };
}

/** Local solar date (YYYY-MM-DD) at longitude lon (review LOW-3). */
export function localDate(now: Date, lon: number): string {
  return new Date(now.getTime() + (lon / 15) * 3600000).toISOString().slice(0, 10);
}

function isTimeout(e: unknown): boolean {
  return e instanceof Error && (e.name === "TimeoutError" || e.name === "AbortError");
}

async function fetchDetections(bbox: Bbox, month: string, now: Date, deps: NrtDeps): Promise<Detection[]> {
  const ws = windows(month, now);
  if (ws.length > MAX_FIRMS_CALLS) throw new NrtError(400, "request would need too many FIRMS calls");
  const deadline = Date.now() + FIRMS_BUDGET_MS;
  const dets: Detection[] = [];
  for (const w of ws) {
    if (Date.now() > deadline) throw new NrtError(504, "FIRMS took too long to answer", "timeout");
    const url = `${FIRMS_AREA}/${deps.key}/${SOURCE}/${bbox.join(",")}/${w.days}/${w.start}`;
    let r: Response;
    try { r = await deps.fetchFirms(url, AbortSignal.timeout(deps.timeoutMs ?? FIRMS_TIMEOUT_MS)); } catch (e) {
      if (isTimeout(e)) throw new NrtError(504, "FIRMS did not answer in time", "timeout");
      throw new NrtError(502, redact(`FIRMS request failed: ${e instanceof Error ? e.message : String(e)}`, deps.key), "upstream");
    }
    if (!r.ok) throw new NrtError(502, `FIRMS answered HTTP ${r.status}`, "upstream");
    dets.push(...parseFirmsCsv(await r.text()));
  }
  return dets;
}

/** Handles one GET /api/nrt request; returns the JSON body or throws NrtError. */
export async function computeNrt(params: URLSearchParams, deps: NrtDeps): Promise<NrtBody> {
  const now = deps.now?.() ?? new Date();
  const cons = (await core("data/constants.json", deps)) as Constants;
  const q = parseQuery(params, cons.coverage_box, now);
  const area = q.area ? await loadArea(q.area, deps) : null;
  // A known area is counted on its own server-side bbox, so the client's rounding does not matter.
  const cov = cons.coverage_box;
  const exact: Bbox = area?.bbox ? [Math.max(area.bbox[0], cov.lon_min), Math.max(area.bbox[1], cov.lat_min), Math.min(area.bbox[2], cov.lon_max), Math.min(area.bbox[3], cov.lat_max)] : q.bbox;
  const snapped = snapBbox(exact, cons.coverage_box);
  const cacheKey = `nrt:v${CACHE_VERSION}:${snapped.join(",")}:${q.month}`;
  const fresh = (d: DetCache | undefined) => !!d && d.v === CACHE_VERSION && now.getTime() - Date.parse(d.fetchedAt) < CACHE_SECONDS * 1000;

  let det = memo.get(cacheKey)?.det;
  if (!fresh(det)) {
    det = undefined;
    const shared = await deps.cache?.get(cacheKey);
    if (fresh(shared)) { det = shared!; remember(cacheKey, det, now); } // LOW-1: check age, memoize
  } else {
    memo.delete(cacheKey); memo.set(cacheKey, { at: now.getTime(), det: det! }); // LRU touch (LOW-2)
  }
  if (!det) {
    if (!deps.key) throw new NrtError(503, "Near-real-time service is not configured (FIRMS_MAP_KEY missing on the server)", "not_configured");
    det = { v: CACHE_VERSION, fetchedAt: now.toISOString(), dets: await fetchDetections(snapped, q.month, now, deps) };
    remember(cacheKey, det, now);
    await deps.cache?.put(cacheKey, det);
  }

  const mask = (await core("data/nrt/mask_cells.json", deps)) as MaskDoc;
  const masked = new Set(mask.cells.map(([a, b]) => `${a},${b}`));
  const [w, s, e, n] = exact;
  let count = 0, removed = 0;
  for (const d of det.dets) {
    if (d.localDate.slice(0, 7) !== q.month) continue;
    if (d.lon < w || d.lon > e || d.lat < s || d.lat > n) continue;
    if (area?.geom && !inGeometry(d.lon, d.lat, area.geom)) continue;
    const cell = `${Math.floor(d.lat / mask.grid_deg + EPS)},${Math.floor(d.lon / mask.grid_deg + EPS)}`;
    if (masked.has(cell)) { removed++; continue; }
    count++;
  }
  const dim = daysIn(q.month);
  // Days covered in local solar time at the bbox centre, the same clock used for counting (LOW-3).
  const today = localDate(new Date(det.fetchedAt), (w + e) / 2);
  const covered = q.month < today.slice(0, 7) ? dim : Math.min(dim, Number(today.slice(8, 10)));
  const m = Number(q.month.slice(5, 7)) - 1;
  const med = area?.doc.median.NOAA20;
  return {
    status: "ok",
    provisional: true,
    label: cons.nrt_label,
    source: SOURCE,
    month: q.month,
    noaa20: count,
    masked: removed,
    daysCovered: covered,
    daysInMonth: dim,
    median: med ? { value: med.values[m] ?? null, years: med.baseline_years } : null,
    geometry: area?.geom ? "polygon" : "bbox",
    fetchedAt: det.fetchedAt,
  };
}

function remember(k: string, det: DetCache, now: Date): void {
  for (const [key, v] of memo) if (now.getTime() - v.at >= CACHE_SECONDS * 1000) memo.delete(key); else break;
  if (memo.size >= 500) memo.delete(memo.keys().next().value as string); // bound isolate memory
  memo.set(k, { at: now.getTime(), det });
}

/** In-memory token bucket per client key (e.g. CF-Connecting-IP), per isolate. */
export class TokenBucket {
  private b = new Map<string, { tokens: number; at: number }>();
  constructor(private capacity: number, private refillPerSec: number, private maxKeys = 5000) {}
  reset(): void { this.b.clear(); }
  take(key: string, nowMs: number): boolean {
    const cur = this.b.get(key) ?? { tokens: this.capacity, at: nowMs };
    const tokens = Math.min(this.capacity, cur.tokens + (Math.max(0, nowMs - cur.at) / 1000) * this.refillPerSec);
    this.b.delete(key);
    if (this.b.size >= this.maxKeys) this.b.delete(this.b.keys().next().value as string);
    const ok = tokens >= 1;
    this.b.set(key, { tokens: ok ? tokens - 1 : tokens, at: nowMs });
    return ok;
  }
}
