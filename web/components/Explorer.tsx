"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MapView } from "./MapView";
import { Calendar } from "./Calendar";
import { MonthCard } from "./MonthCard";
import { getJson, loadCalibration, loadConstants, loadDistrict, loadIndex } from "@/lib/data";
import { aoiBbox, aquaPoints, countHotspots, monthlyByPlatform, queryHotspots, tilesFor, type HotspotRow } from "@/lib/duck";
import { bboxPolygon, circlePolygon, geometryBbox } from "@/lib/geo";
import { monthRange, daysInMonth, ymLabel } from "@/lib/months";
import { fetchNrt, type NrtResult } from "@/lib/nrt";
import { customDoc, MODE_LABEL, seriesFromDoc, type CustomDoc, type Mode } from "@/lib/series";
import type { Aoi, AreaDoc, Bbox, Constants, DistrictEntry, IndexDoc, Platform } from "@/lib/types";
import { downloadText, toCsv } from "@/lib/csv";
import { computeCritical } from "@/lib/criticalCalc";
import { CriticalPanel } from "@/components/CriticalPanel";
import { flaggedInRange, knownRegions, mergeFlags, overlappedRegions, plainReason, type Flags } from "@/lib/reliability";
import { FlagIcon } from "./Calendar";
import { landing, storyFromT1, type Story } from "@/lib/story";
import type { T1 } from "@/lib/results";

type Tab = "district" | "box" | "radius";
type Doc = (AreaDoc | (CustomDoc & { eras: AreaDoc["eras"]; name: string })) & { name: string };

/** Browser budget for a custom AOI series (tile rows read for the full record). Not shown to users. */
const REGION_LABEL: Record<string, string> = { PK_Punjab: "Punjab (Pakistan)", IN_Punjab: "Punjab (India)", rest_of_box: "elsewhere" };

const MAX_SERIES_ROWS = 2_500_000;

interface Preset { id: string; name: string; sub: string; kind: "district" | "region"; path: string; bbox: Bbox; country: string }

function presets(index: IndexDoc): Preset[] {
  const regions: Preset[] = Object.entries(index.regions)
    .filter(([id]) => id !== "rest_of_box")
    .map(([id, path]) => ({ id, name: id === "PK_Punjab" ? "Punjab (Pakistan)" : "Punjab (India)", sub: "province / state, calibration region", kind: "region", path, bbox: [0, 0, 0, 0] as Bbox, country: id.slice(0, 2) }));
  const ds: Preset[] = index.districts.map((d: DistrictEntry) => ({
    id: d.id, name: d.name, sub: `${d.adm1}, ${d.country === "PAK" ? "Pakistan" : "India"}`, kind: "district", path: `districts/${d.id}.json`, bbox: d.bbox, country: d.country,
  }));
  return [...regions, ...ds];
}

function stamp(): string {
  return new Date().toISOString().slice(0, 10);
}

export function Explorer() {
  const [index, setIndex] = useState<IndexDoc | null>(null);
  const [cons, setCons] = useState<Constants | null>(null);
  const [geo, setGeo] = useState<GeoJSON.FeatureCollection | null>(null);
  const [tab, setTab] = useState<Tab>("district");
  const [aoi, setAoi] = useState<Aoi | null>(null);
  const [doc, setDoc] = useState<Doc | null>(null);
  const [status, setStatus] = useState<{ text: string; warn?: boolean }>({ text: "Loading data…" });
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<"harmonized" | "raw">("harmonized");
  const [rawMode, setRawMode] = useState<Exclude<Mode, "harmonized">>("recorded");
  const [range, setRange] = useState<[string, string]>(["2003-01", "2025-12"]);
  const [showValues, setShowValues] = useState(false);
  const [drawing, setDrawing] = useState(false);
  const [query, setQuery] = useState("");
  const [sel, setSel] = useState(0);
  const [box, setBox] = useState({ w: "", s: "", e: "", n: "" });
  const [pt, setPt] = useState({ lat: "", lon: "", km: "" });
  const [nrt, setNrt] = useState<NrtResult | null>(null);
  const [flags, setFlags] = useState<Flags | null>(null);
  const [exportMsg, setExportMsg] = useState<{ text: string; warn?: boolean }>({ text: "" });
  const [pickerOpen, setPickerOpen] = useState(false);
  // First-screen story (W-07): raw record of one region until the visitor picks an area of their own.
  const [story, setStory] = useState<Story | null>(null);
  const endStory = () => { if (story) { setStory(null); setView("harmonized"); } };
  const toggleRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const focusPanel = useRef(false);
  const calRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const reqId = useRef(0);
  const nrtAbort = useRef<AbortController | null>(null);
  useEffect(() => () => nrtAbort.current?.abort(), []);

  // Phone picker (D-046): collapsed behind "Change area"; on wider screens the panel is always shown (CSS).
  const isPhone = () => window.matchMedia("(max-width: 900px)").matches;
  const openPicker = () => { focusPanel.current = true; setPickerOpen(true); };
  const closePicker = (refocus = true) => { setPickerOpen(false); if (refocus && isPhone()) toggleRef.current?.focus(); };
  const afterPick = () => { if (isPhone()) closePicker(); };
  useEffect(() => {
    if (!pickerOpen || !focusPanel.current) return;
    focusPanel.current = false;
    panelRef.current?.querySelector<HTMLElement>("button, input, select")?.focus();
  }, [pickerOpen]);

  useEffect(() => {
    Promise.all([loadIndex(), loadConstants(), getJson<GeoJSON.FeatureCollection>("districts.geojson")])
      .then(([i, c, g]) => {
        setIndex(i);
        setCons(c);
        setGeo(g);
        // Deep link from the use-case page: ?area=<district id>&from=YYYY-MM&to=YYYY-MM
        const qs = new URLSearchParams(window.location.search);
        const ymOk = (v: string | null): v is string => !!v && /^\d{4}-\d{2}$/.test(v) && v >= i.period.first && v <= i.period.last;
        const qf = qs.get("from"), qt = qs.get("to");
        setRange([ymOk(qf) ? qf : i.period.first, ymOk(qt) && (!ymOk(qf) || qt >= qf) ? qt : i.period.last]);
        const land = landing(i, qs.get("area"));
        if (!land) return;
        if (land.story) {
          // Region bbox is filled in by loadAoi; the story text needs t1.json, so the raw view waits for it.
          setAoi({ kind: "district", id: land.id, name: REGION_LABEL[land.id] ?? land.id, bbox: [0, 0, 0, 0], country: land.id.slice(0, 2) });
          getJson<T1>("results/t1.json")
            .then((t1) => { const s = storyFromT1(t1, land.id); if (s) { setStory(s); setView("raw"); } })
            .catch(() => undefined); // no story strip without the results file; the Explorer still works
          return;
        }
        const first = i.districts.find((d) => d.id === land.id);
        if (!first) return;
        if (qs.get("area") === first.id) setQuery(first.name);
        setAoi({ kind: "district", id: first.id, name: first.name, bbox: first.bbox, country: first.country });
      })
      .catch((e: Error) => setStatus({ text: e.message, warn: true }));
  }, []);

  const allPresets = useMemo(() => (index ? presets(index) : []), [index]);
  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allPresets.slice(0, 2);
    return allPresets.filter((p) => p.name.toLowerCase().includes(q) || p.sub.toLowerCase().includes(q)).slice(0, 30);
  }, [allPresets, query]);

  // The list is shown (and aria-expanded true) while it has options; empty list = collapsed.
  const listOpen = matches.length > 0;

  const loadAoi = useCallback(async (a: Aoi) => {
    if (!index) return;
    const id = ++reqId.current;
    nrtAbort.current?.abort();
    const ctrl = new AbortController();
    nrtAbort.current = ctrl;
    setBusy(true);
    setNrt(null);
    setFlags(null);
    try {
      let nrtBbox: Bbox = aoiBbox(a);
      if (a.kind === "district") {
        const isRegion = Object.hasOwn(index.regions, a.id);
        const d = isRegion ? await getJson<AreaDoc>(index.regions[a.id]!) : await loadDistrict(a.id);
        if (id !== reqId.current) return;
        setDoc({ ...d, name: isRegion ? (allPresets.find((p) => p.id === a.id)?.name ?? d.name) : d.name });
        setFlags(d.reliability ? mergeFlags([d.reliability]) : null);
        if (d.bbox) nrtBbox = d.bbox;
        setStatus({ text: isRegion ? "Calibration region, precomputed by the pipeline." : "District series precomputed by the pipeline." });
        if (isRegion && d.bbox) setAoi((cur) => (cur && cur.kind === "district" && cur.id === a.id && cur.bbox[2] === 0 ? { ...cur, bbox: d.bbox } : cur));
      } else {
        const bbox = aoiBbox(a);
        const tiles = await tilesFor(bbox, [Number(index.period.first.slice(0, 4)), Number(index.period.last.slice(0, 4))]);
        const rows = tiles.reduce((s, t) => s + t.rows, 0);
        if (rows > MAX_SERIES_ROWS) {
          setStatus({ text: "This area holds too many detections to compute in the browser. Draw a smaller box or radius, or pick a district.", warn: true });
          return;
        }
        setStatus({ text: "Loading hotspot tiles…" });
        const [cal, ref] = await Promise.all([loadCalibration(), getJson<AreaDoc>(index.regions.rest_of_box ?? "regions/rest_of_box.json")]);
        const from = `${index.period.first}-01`;
        const to = `${index.period.last}-${String(daysInMonth(index.period.last)).padStart(2, "0")}`;
        const onProgress = (d: number, t: number) => { if (id === reqId.current) setStatus({ text: `Loading hotspot tiles ${d} of ${t}…` }); };
        const counts = await monthlyByPlatform({ aoi: a, from, to, onProgress });
        const pts = await aquaPoints({ aoi: a, from, to });
        if (id !== reqId.current) return;
        const map = new Map(counts.map((c) => [`${c.platform}|${c.ym}`, c.n]));
        const months = monthRange(index.period.first, index.period.last);
        const baselines = Object.fromEntries((["harmonized", "Terra", "Aqua", "SNPP", "NOAA20"] as const).map((k) => [k, ref.median[k].baseline_years])) as Record<"harmonized" | Platform, [number, number]>;
        const cd = customDoc({ months, counts: map, aquaPts: pts, cal, aoiBbox: bbox, baselines, units: ref.units, partialCoverage: cons?.partial_coverage ?? (await loadConstants()).partial_coverage });
        const name = a.kind === "box" ? `Box ${a.bbox.join(", ")}` : `${a.km} km around ${a.lat}, ${a.lon}`;
        // Custom areas take the flags of every calibration region they overlap (D-040).
        const regs = knownRegions(overlappedRegions(a, bbox, cal.punjab_polygons), index.regions);
        const blocks = await Promise.all(regs.map((r) => (r === "rest_of_box" ? Promise.resolve(ref) : getJson<AreaDoc>(index.regions[r]!))));
        if (id !== reqId.current) return;
        const rel = blocks.map((b) => b.reliability).filter((x): x is NonNullable<typeof x> => !!x);
        const merged = rel.length ? mergeFlags(rel) : null;
        setFlags(merged);
        // Critical period and median excluding flagged years: same definitions as districts (D-042), caution years = that union (D-043).
        const cc = computeCritical({ months, value: cd.harmonized.value, partial: cd.harmonized.partial, baseline: baselines.harmonized, cautionYears: merged ? [...merged.years.keys()] : [] });
        setDoc({ ...cd, ...cc, eras: ref.eras, name } as Doc);
        const share = Object.entries(cd.regionShare).map(([r, n]) => `${REGION_LABEL[r] ?? r} ${n.toLocaleString("en-GB")}`).join(", ");
        setStatus({ text: `Computed in your browser from ${tiles.length} tiles with the pipeline's calibration factors${share ? ` (Aqua detections by calibration region: ${share})` : ""}.` });
      }
      const nr = await fetchNrt(nrtBbox, a.kind === "district" ? a.id : null, ctrl.signal);
      if (id === reqId.current) setNrt(nr);
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      if (id === reqId.current) setStatus({ text: e instanceof Error ? e.message : String(e), warn: true });
    } finally {
      if (id === reqId.current) setBusy(false);
    }
  }, [index, allPresets, cons]);

  useEffect(() => {
    if (aoi) void loadAoi(aoi);
    // Only re-run when the AOI identity changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aoi && JSON.stringify({ ...aoi, bbox: aoi.kind === "district" ? null : aoiBbox(aoi) }), loadAoi]);

  const pickPreset = (p: Preset) => {
    afterPick();
    endStory();
    setQuery(p.name);
    setAoi({ kind: "district", id: p.id, name: p.name, bbox: p.bbox, country: p.country });
  };

  const cov = cons?.coverage_box;
  const inCov = (lat: number, lon: number) => !!cov && lat >= cov.lat_min && lat <= cov.lat_max && lon >= cov.lon_min && lon <= cov.lon_max;

  const applyBox = (b?: Bbox) => {
    const bb: Bbox = b ?? [Number(box.w), Number(box.s), Number(box.e), Number(box.n)];
    if (bb.some((v) => Number.isNaN(v)) || bb[0] >= bb[2] || bb[1] >= bb[3]) {
      setStatus({ text: "Enter west < east and south < north, in decimal degrees.", warn: true });
      return;
    }
    if (!inCov(bb[1], bb[0]) && !inCov(bb[3], bb[2])) {
      setStatus({ text: "This box is outside the coverage area (Pakistan and northern India).", warn: true });
      return;
    }
    setBox({ w: String(bb[0]), s: String(bb[1]), e: String(bb[2]), n: String(bb[3]) });
    setDrawing(false);
    afterPick();
    endStory();
    setAoi({ kind: "box", bbox: bb });
  };

  const applyRadius = () => {
    const lat = Number(pt.lat), lon = Number(pt.lon), km = Number(pt.km);
    if ([lat, lon, km].some((v) => Number.isNaN(v)) || km <= 0 || pt.lat === "" || pt.lon === "" || pt.km === "") {
      setStatus({ text: "Enter a latitude, a longitude and a radius in km greater than zero.", warn: true });
      return;
    }
    if (!inCov(lat, lon)) {
      setStatus({ text: "This point is outside the coverage area (Pakistan and northern India).", warn: true });
      return;
    }
    afterPick();
    endStory();
    setAoi({ kind: "radius", lat, lon, km });
  };

  const mode: Mode = view === "harmonized" ? "harmonized" : rawMode;
  const series = useMemo(() => (doc ? seriesFromDoc(doc as AreaDoc, mode) : null), [doc, mode]);

  const aoiShape = useMemo<GeoJSON.Geometry | null>(() => {
    if (!aoi) return null;
    if (aoi.kind === "radius") return circlePolygon(aoi.lat, aoi.lon, aoi.km);
    if (aoi.kind === "box") return bboxPolygon(aoi.bbox);
    const f = geo?.features.find((x) => x.properties?.id === aoi.id);
    if (f) return f.geometry;
    if (doc && "bbox" in doc && doc.bbox) return bboxPolygon(doc.bbox);
    return null;
  }, [aoi, geo, doc]);
  const fitBbox = useMemo<Bbox | null>(() => (aoiShape ? geometryBbox(aoiShape) : null), [aoiShape]);

  // Exports
  const exportCalendar = () => {
    if (!series || !doc) return;
    const ad = doc as AreaDoc;
    const crit = ad.critical, ex = ad.median_excl_flagged;
    const rows = series.months.map((ym, i) => {
      const m = Number(ym.slice(5, 7));
      const base = { month: ym, value: series.value[i] ?? "", partial: series.partial[i] ?? "", provisional: series.provisional?.[i] ? "yes" : "no", source_platform: series.source[i] ?? "" };
      return mode === "harmonized" && crit && ex
        ? { ...base, median_all_years: series.median[m - 1] ?? "", median_excl_flagged_years: ex.values[m - 1] ?? "", critical_month: crit.months.includes(m) ? "yes" : "no" }
        : base;
    }).filter((r) => r.month >= range[0] && r.month <= range[1]);
    const head = [`# Blind Spot calendar: ${doc.name}`, `# series: ${series.label}; unit: ${series.unit}`, `# ${cons?.scope ?? ""}`];
    if (series.provisional?.some(Boolean)) head.push("# provisional = yes: near-real-time FIRMS data, will change when the standard data replace it");
    if (crit && ex && mode === "harmonized") {
      head.push(`# critical months (month level, not daily): ${crit.months.join(" ") || "none"}; onset ${crit.onset ?? "n/a"}, peak ${crit.peak ?? "n/a"}, end ${crit.end ?? "n/a"} (month numbers); ${crit.rule}`);
      if (!("level" in doc)) head.push("# drawn area: critical months and median_excl_flagged_years computed in the browser; flagged years = union of the calibration regions the area overlaps (D-043)");
      head.push(`# median_all_years uses ${ex.baseline_years[0]}-${ex.baseline_years[1]}; median_excl_flagged_years leaves out ${ex.excluded_years.join(", ") || "no years"}`);
    }
    downloadText(`blindspot-calendar-${mode}-${stamp()}.csv`, head.join("\n") + "\n" + toCsv(rows));
    setExportMsg({ text: `Calendar CSV saved (${rows.length} months).` });
  };

  const exportHotspots = async () => {
    if (!aoi || !cons) return;
    const from = `${range[0]}-01`;
    const to = `${range[1]}-${String(daysInMonth(range[1])).padStart(2, "0")}`;
    setExportMsg({ text: "Counting hotspots…" });
    try {
      const bboxAoi: Aoi = aoi.kind === "district" ? { kind: "box", bbox: fitBbox ?? aoi.bbox } : aoi;
      // ADM2 districts: filter by the exact shape_id written into the tiles (D-038), so rows
      // match the calendar. Regions (ADM1/rest of box) still use the simplified polygon.
      const adm2 = aoi.kind === "district" && doc && "level" in doc && doc.level === "ADM2" ? aoi.id : undefined;
      const n = await countHotspots({ aoi: bboxAoi, from, to, adm2 });
      if (n > cons.csv_row_cap) {
        setExportMsg({ text: cons.csv_cap_message.replace("{cap}", cons.csv_row_cap.toLocaleString("en-GB")), warn: true });
        return;
      }
      let rows: HotspotRow[] = await queryHotspots({ aoi: bboxAoi, from, to, adm2 }, cons.csv_row_cap);
      if (aoi.kind === "district" && !adm2 && aoiShape) {
        const { pointInGeometry } = await import("@/lib/geo");
        rows = rows.filter((r) => pointInGeometry(r.lon, r.lat, aoiShape));
      }
      const head = [`# Blind Spot hotspots: ${doc?.name ?? ""}, ${range[0]} to ${range[1]}`, `# ${cons.units.raw}; acq_date and local_time are local solar time`, "# Source: NASA FIRMS (see Attribution page)"];
      downloadText(`blindspot-hotspots-${stamp()}.csv`, head.join("\n") + "\n" + toCsv(rows as unknown as Record<string, unknown>[]));
      setExportMsg({ text: `Hotspot CSV saved (${rows.length.toLocaleString("en-GB")} rows).` });
    } catch (e) {
      setExportMsg({ text: e instanceof Error ? e.message : String(e), warn: true });
    }
  };

  const exportPng = async (el: HTMLElement | null, name: string) => {
    if (!el) return;
    const { toPng } = await import("html-to-image");
    const bg = getComputedStyle(document.body).backgroundColor;
    const url = await toPng(el, { backgroundColor: bg, pixelRatio: 2 });
    const a = document.createElement("a");
    a.href = url;
    a.download = `blindspot-${name}-${stamp()}.png`;
    a.click();
    setExportMsg({ text: `${name === "calendar" ? "Calendar" : "Card"} PNG saved.` });
  };

  const covBbox: Bbox = cov ? [cov.lon_min, cov.lat_min, cov.lon_max, cov.lat_max] : [60, 23, 80, 37];
  const sub = doc && "adm1" in doc && doc.adm1 ? `${doc.adm1.name}, ${doc.country === "PAK" ? "Pakistan" : doc.country === "IND" ? "India" : doc.country}` : aoi?.kind === "box" ? "Drawn box" : aoi?.kind === "radius" ? "Point and radius" : "";

  return (
    <main id="main" className="explorer">
      <div className="aoi-head">
        <div className="aoi-text">
          <h1 className="aoi-title" data-testid="aoi-title">{doc?.name ?? "Choose an area"}</h1>
          {sub && <p className="aoi-sub">{sub}</p>}
        </div>
        <button ref={toggleRef} type="button" className="btn ghost picker-toggle" aria-expanded={pickerOpen} aria-controls="picker" onClick={() => (pickerOpen ? closePicker() : openPicker())} data-testid="picker-toggle">Change area</button>
        {status.warn && !pickerOpen && <p className="phone-status warn">{status.text}</p>}
      </div>

      <section ref={panelRef} id="picker" className="controls" data-open={pickerOpen} aria-label="Choose an area and period"
        onKeyDown={(e) => { if (e.key === "Escape" && pickerOpen && isPhone()) { e.preventDefault(); closePicker(); } }}>
        <fieldset>
          <legend><span className="step" aria-hidden="true">1</span>Area</legend>
          <div className="seg" role="group" aria-label="How to choose the area">
            {(["district", "box", "radius"] as Tab[]).map((t) => (
              <button key={t} type="button" aria-pressed={tab === t} onClick={() => { setTab(t); setDrawing(false); }}>
                {t === "district" ? "District" : t === "box" ? "Box" : "Point + radius"}
              </button>
            ))}
          </div>
        </fieldset>

        {tab === "district" && (
          <fieldset>
            <label className="label" htmlFor="q">Find a district</label>
            <input id="q" type="search" role="combobox" aria-expanded={listOpen} aria-controls="q-list" aria-autocomplete="list" autoComplete="off" placeholder="Type a district name"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setSel(0); }}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") { e.preventDefault(); setSel((s) => Math.min(matches.length - 1, s + 1)); }
                if (e.key === "ArrowUp") { e.preventDefault(); setSel((s) => Math.max(0, s - 1)); }
                if (e.key === "Enter" && matches[sel]) { e.preventDefault(); pickPreset(matches[sel]); }
                if (e.key === "Escape" && query) { e.preventDefault(); e.stopPropagation(); setQuery(""); setSel(0); }
              }}
              aria-activedescendant={matches[sel] ? `opt-${matches[sel].id}` : undefined}
              data-testid="district-search" />
            <ul className="results-list" id="q-list" role="listbox" aria-label="Matching areas" hidden={!listOpen}>
              {matches.map((p, k) => (
                <li key={p.id} id={`opt-${p.id}`} role="option" aria-selected={k === sel} onClick={() => pickPreset(p)}>
                  <span>{p.name}</span><small>{p.sub}</small>
                </li>
              ))}
            </ul>
            {!listOpen && (
              <div className="empty-mini" role="status">
                <strong>No district matches &ldquo;{query.trim()}&rdquo;.</strong>
                <span>Try another spelling, or click a district on the map.</span>
                <button type="button" className="btn ghost" onClick={() => { setQuery(""); setSel(0); document.getElementById("q")?.focus(); }}>Clear search</button>
              </div>
            )}
            <p className="hint">Or click a district on the map.</p>
          </fieldset>
        )}

        {tab === "box" && (
          <fieldset>
            <legend className="sr-only">Box in decimal degrees</legend>
            <div className="row">
              <label>West<input type="number" step="0.01" value={box.w} onChange={(e) => setBox({ ...box, w: e.target.value })} data-testid="box-w" /></label>
              <label>East<input type="number" step="0.01" value={box.e} onChange={(e) => setBox({ ...box, e: e.target.value })} data-testid="box-e" /></label>
            </div>
            <div className="row">
              <label>South<input type="number" step="0.01" value={box.s} onChange={(e) => setBox({ ...box, s: e.target.value })} data-testid="box-s" /></label>
              <label>North<input type="number" step="0.01" value={box.n} onChange={(e) => setBox({ ...box, n: e.target.value })} data-testid="box-n" /></label>
            </div>
            <div className="toolbar">
              <button type="button" className="btn" onClick={() => applyBox()} data-testid="box-apply">Use this box</button>
              <button type="button" className="btn ghost" aria-pressed={drawing} onClick={() => setDrawing((d) => !d)} data-testid="box-draw">{drawing ? "Cancel drawing" : "Draw on map"}</button>
            </div>
            <p className="hint">{drawing ? "Drag on the map to draw the box (mouse or touch only; type the edges above for keyboard use)." : "Type the edges, or draw the box on the map."}</p>
          </fieldset>
        )}

        {tab === "radius" && (
          <fieldset>
            <legend className="sr-only">Point and radius</legend>
            <div className="row">
              <label>Latitude<input type="number" step="0.01" value={pt.lat} onChange={(e) => setPt({ ...pt, lat: e.target.value })} data-testid="pt-lat" /></label>
              <label>Longitude<input type="number" step="0.01" value={pt.lon} onChange={(e) => setPt({ ...pt, lon: e.target.value })} data-testid="pt-lon" /></label>
            </div>
            <label>Radius, km<input type="number" step="1" min="1" value={pt.km} onChange={(e) => setPt({ ...pt, km: e.target.value })} data-testid="pt-km" /></label>
            <div className="toolbar"><button type="button" className="btn" onClick={applyRadius} data-testid="pt-apply">Use this circle</button></div>
          </fieldset>
        )}

        <MapView aoiShape={aoiShape} fitBbox={fitBbox} coverage={covBbox} drawing={drawing} onBox={(b) => applyBox(b)} onDistrict={(id) => { const p = allPresets.find((x) => x.id === id); if (p) { setTab("district"); pickPreset(p); } }} />
        <p className={`status${status.warn ? " warn" : ""}`} role="status" data-testid="status">{busy ? "Working… " : ""}{status.text}</p>

        {index && (
          <fieldset>
            <legend><span className="step" aria-hidden="true">2</span>Period</legend>
            <div className="row">
              <label>From<input type="month" min={index.period.first} max={range[1]} value={range[0]} onChange={(e) => e.target.value && setRange([e.target.value, range[1]])} data-testid="from" /></label>
              <label>To<input type="month" min={range[0]} max={index.period.last} value={range[1]} onChange={(e) => e.target.value && setRange([range[0], e.target.value])} data-testid="to" /></label>
            </div>
            <p className="hint">Months outside the period are faded. The period also limits the hotspot CSV.</p>
          </fieldset>
        )}
      </section>

      <section className="stage" aria-label="Burning calendar">
        {!doc && (
          <section className="empty-state" aria-labelledby="empty-title" data-testid="empty-state">
            <h2 id="empty-title">{busy || !index ? "Loading the area" : "No area chosen yet"}</h2>
            <p>{busy || !index ? "Reading the series for this area." : "Pick a district, draw a box or enter a point and radius to see its burning calendar and whether the latest month is unusual there."}</p>
            {!busy && index && <button type="button" className="btn" onClick={() => { setTab("district"); if (isPhone()) openPicker(); else setTimeout(() => document.getElementById("q")?.focus(), 0); }}>Choose a district</button>}
          </section>
        )}
        {doc && story && aoi?.kind === "district" && aoi.id === story.region && (
          <section className="story" aria-labelledby="story-title" data-testid="story">
            <h2 id="story-title">Start here: the {story.year} jump</h2>
            <p data-testid="story-text">
              {view === "raw"
                ? `Raw record, ${doc.name}: the ${story.window} fire count jumps ${story.raw} in ${story.year}, when MODIS gives way to VIIRS. The sensors changed, not the burning.`
                : `Harmonized, the same ${story.year} step is ${story.harmonized} (raw: ${story.raw}). Years we can no longer check are flagged in the calendar.`}
            </p>
            <div className="toolbar">
              <button type="button" className="btn" data-testid="story-toggle"
                onClick={() => { setView(view === "raw" ? "harmonized" : "raw"); document.getElementById("calendar-plate")?.scrollIntoView({ block: "nearest" }); }}>
                {view === "raw" ? "Harmonize the record" : "Show the raw record again"}
              </button>
              <a className="btn ghost story-jump" href="#calendar-plate">Go to the calendar</a>
            </div>
          </section>
        )}
        {doc && index && <p className="eyebrow" data-testid="eyebrow">Is this month unusual here?</p>}
        {doc && index && <MonthCard ref={cardRef} doc={doc as AreaDoc} latest={index.period.last} nrt={nrt} />}
        {doc && <CriticalPanel doc={doc as AreaDoc} />}

        {series && doc && (
          <div className="plate" id="calendar-plate">
            <div className="plate-head">
              <h2>Burning by month, {range[0].slice(0, 4)}–{range[1].slice(0, 4)}</h2>
              <div className="toolbar">
                <div className="seg" role="group" aria-label="Series">
                  <button type="button" aria-pressed={view === "harmonized"} onClick={() => setView("harmonized")} data-testid="toggle-harmonized">Harmonized</button>
                  <button type="button" aria-pressed={view === "raw"} onClick={() => setView("raw")} data-testid="toggle-raw">Raw</button>
                </div>
                {view === "raw" && (
                  <label className="sr-only" htmlFor="rawmode">Raw series</label>
                )}
                {view === "raw" && (
                  <select id="rawmode" value={rawMode} onChange={(e) => setRawMode(e.target.value as Exclude<Mode, "harmonized">)} style={{ width: "auto" }} data-testid="raw-mode">
                    {(["recorded", "Terra", "Aqua", "SNPP", "NOAA20"] as const).map((m) => <option key={m} value={m}>{MODE_LABEL[m]}</option>)}
                  </select>
                )}
                <label className="key"><input type="checkbox" checked={showValues} onChange={(e) => setShowValues(e.target.checked)} data-testid="show-values" /> Show values</label>
              </div>
            </div>
            <div ref={calRef} style={{ background: "var(--sheet)", padding: 4 }}>
              <p className="hint" style={{ marginBottom: 8 }} data-testid="series-label">
                {series.label}. {view === "harmonized"
                  ? "Before the switch, Aqua MODIS counts are scaled to the S-NPP VIIRS level with per-region, per-month factors; from the switch on, S-NPP is shown as observed."
                  : rawMode === "recorded"
                    ? "Each month shows the one platform the record used then, with no scaling. The jump at the sensor switch is an artefact of the instruments, not of burning."
                    : "One platform alone, unscaled. Platforms are never added together."}
                {" "}{doc.name}{range[0] !== index?.period.first || range[1] !== index?.period.last ? `, ${ymLabel(range[0])} to ${ymLabel(range[1])}` : ""}.
              </p>
              {(() => {
                const inRange = flaggedInRange(flags, range[0], range[1]);
                if (!inRange.length || !flags) return null;
                const codes = [...new Set(inRange.flatMap((fy) => fy.reasons.map((r) => r.code)))];
                const ys = inRange.map((fy) => fy.year);
                return (
                  <div className="banner" role="note" data-testid="flag-banner">
                    <FlagIcon size={16} />
                    <p style={{ margin: 0 }}><strong>Caution:</strong> {ys.length === 1 ? `${ys[0]} is` : `${ys.length} years (${ys.join(", ")}) are`} flagged in this period. {codes.map((c) => plainReason(c, flags.codeText)).join(". ")}. Details below the calendar.</p>
                  </div>
                );
              })()}
              <Calendar series={series} eras={doc.eras} range={range} showValues={showValues} flags={flags} />
            </div>
            <div className="toolbar" style={{ marginTop: 14 }}>
              <button type="button" className="btn ghost" onClick={exportCalendar} data-testid="csv-calendar">Download calendar CSV</button>
              <button type="button" className="btn ghost" onClick={() => void exportHotspots()} data-testid="csv-hotspots">Download hotspots CSV</button>
              <button type="button" className="btn ghost" onClick={() => void exportPng(calRef.current, "calendar")} data-testid="png-calendar">Save calendar PNG</button>
              <button type="button" className="btn ghost" onClick={() => void exportPng(cardRef.current, "card")} data-testid="png-card">Save card PNG</button>
            </div>
            <p className={`status${exportMsg.warn ? " warn" : ""}`} role="status" data-testid="export-status">{exportMsg.text}</p>
          </div>
        )}
        <p className="hint">Data: <a href="/attribution/">NASA FIRMS and geoBoundaries</a>. Counts are masked, filtered hotspots; see <a href="/methods/">Methods</a>.</p>
      </section>
    </main>
  );
}
