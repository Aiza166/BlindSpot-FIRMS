// DuckDB-WASM over the static Parquet tiles (D-009, D-035). Bundles are self-hosted in
// public/duckdb (scripts/copy-duckdb.mjs), so nothing is fetched from a CDN at runtime.
import type { AsyncDuckDB, AsyncDuckDBConnection } from "@duckdb/duckdb-wasm";
import { DATA, loadConstants, loadManifest } from "./data";
import { tileKeys } from "./geo";
import type { Aoi, Bbox } from "./types";
import { radiusBbox } from "./geo";

let dbPromise: Promise<{ db: AsyncDuckDB; conn: AsyncDuckDBConnection }> | null = null;
const registered = new Set<string>();

async function init() {
  const duckdb = await import("@duckdb/duckdb-wasm");
  const base = `${window.location.origin}/duckdb`;
  const bundle = await duckdb.selectBundle({
    mvp: { mainModule: `${base}/duckdb-mvp.wasm`, mainWorker: `${base}/duckdb-browser-mvp.worker.js` },
    eh: { mainModule: `${base}/duckdb-eh.wasm`, mainWorker: `${base}/duckdb-browser-eh.worker.js` },
  });
  const worker = new Worker(bundle.mainWorker!);
  const db = new duckdb.AsyncDuckDB(new duckdb.VoidLogger(), worker);
  await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
  const conn = await db.connect();
  return { db, conn };
}

export function getDuck() {
  if (!dbPromise) dbPromise = init();
  return dbPromise;
}

/** Earth mean radius (IUGG), km. */
const EARTH_KM = 6371.0088;

export function aoiBbox(aoi: Aoi): Bbox {
  if (aoi.kind === "radius") return radiusBbox(aoi.lat, aoi.lon, aoi.km);
  return aoi.bbox;
}

/** Tiles listed in the manifest that overlap the AOI bbox for the given years. */
export async function tilesFor(bbox: Bbox, years: [number, number]): Promise<{ year: number; name: string; path: string; rows: number }[]> {
  const [man, cons] = await Promise.all([loadManifest(), loadConstants()]);
  const keys = tileKeys(bbox, cons.coverage_box, man.tile_deg);
  const out: { year: number; name: string; path: string; rows: number }[] = [];
  for (let y = years[0]; y <= years[1]; y++) {
    const rows = man.rows[String(y)];
    if (!rows) continue;
    for (const k of keys) {
      const f = `tile_${k.lat}_${k.lon}.parquet`;
      const n = rows[f];
      if (n === undefined) continue;
      const path = man.path_template.replace("{year}", String(y)).replace("{lat}", String(k.lat)).replace("{lon}", String(k.lon));
      out.push({ year: y, name: `y${y}_${f}`, path, rows: n });
    }
  }
  return out;
}

async function register(tiles: { name: string; path: string }[], onProgress?: (done: number, total: number) => void) {
  const { db } = await getDuck();
  let done = 0;
  const todo = tiles.filter((t) => !registered.has(t.name));
  const queue = [...todo];
  const workers = Array.from({ length: 8 }, async () => {
    for (let t = queue.shift(); t; t = queue.shift()) {
      const r = await fetch(`${DATA}/${t.path}`);
      if (!r.ok) throw new Error(`Tile ${t.path} missing (HTTP ${r.status}).`);
      await db.registerFileBuffer(t.name, new Uint8Array(await r.arrayBuffer()));
      registered.add(t.name);
      done += 1;
      onProgress?.(done, todo.length);
    }
  });
  await Promise.all(workers);
}

/** WHERE clause + params for an AOI and a date range. Only placeholders carry user values. */
function where(aoi: Aoi, from: string, to: string, adm2?: string): { sql: string; params: (number | string)[] } {
  const b = aoiBbox(aoi);
  let sql = "lon BETWEEN ? AND ? AND lat BETWEEN ? AND ? AND acq_date BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)";
  const params: (number | string)[] = [b[0], b[2], b[1], b[3], from, to];
  if (aoi.kind === "radius") {
    sql += ` AND 2 * ${EARTH_KM} * asin(sqrt(pow(sin(radians(lat - ?) / 2), 2) + cos(radians(?)) * cos(radians(lat)) * pow(sin(radians(lon - ?) / 2), 2))) <= ?`;
    params.push(aoi.lat, aoi.lat, aoi.lon, aoi.km);
  }
  if (adm2 !== undefined) {
    sql += " AND adm2_id = ?";
    params.push(adm2);
  }
  return { sql, params };
}

// Arrow rows: StructRow proxies; toJSON() gives a plain object.
function rows(t: { toArray(): unknown[] }): Record<string, unknown>[] {
  return t.toArray().map((r) => (r as { toJSON(): Record<string, unknown> }).toJSON());
}

function fromClause(names: string[]): string {
  // File names are generated from the manifest (never user input); quote defensively.
  return `read_parquet([${names.map((n) => `'${n.replace(/'/g, "")}'`).join(", ")}])`;
}

export interface HotspotRow {
  lat: number;
  lon: number;
  acq_date: string;
  local_time: string;
  platform: string;
  instrument: string;
  confidence: string;
  frp: number;
  daynight: string;
}

export interface QueryOpts {
  aoi: Aoi;
  from: string; // YYYY-MM-DD
  to: string;
  /** Exact geoBoundaries ADM2 shape_id (tile column adm2_id, D-038). */
  adm2?: string;
  onProgress?: (done: number, total: number) => void;
}

async function prepared(opts: QueryOpts) {
  const years: [number, number] = [Number(opts.from.slice(0, 4)), Number(opts.to.slice(0, 4))];
  const tiles = await tilesFor(aoiBbox(opts.aoi), years);
  if (tiles.length === 0) return null;
  await register(tiles, opts.onProgress);
  const { conn } = await getDuck();
  return { conn, src: fromClause(tiles.map((t) => t.name)), w: where(opts.aoi, opts.from, opts.to, opts.adm2) };
}

export async function countHotspots(opts: QueryOpts): Promise<number> {
  const p = await prepared(opts);
  if (!p) return 0;
  const st = await p.conn.prepare(`SELECT count(*) AS n FROM ${p.src} WHERE ${p.w.sql}`);
  const t = await st.query(...p.w.params);
  await st.close();
  return Number(rows(t)[0]?.n ?? 0);
}

export async function queryHotspots(opts: QueryOpts, limit: number): Promise<HotspotRow[]> {
  const p = await prepared(opts);
  if (!p) return [];
  const st = await p.conn.prepare(
    `SELECT lat, lon, strftime(acq_date, '%Y-%m-%d') AS acq_date, local_time, platform, instrument, confidence, frp, daynight
     FROM ${p.src} WHERE ${p.w.sql} ORDER BY acq_date, local_time, lat, lon, platform LIMIT ?`,
  );
  const t = await st.query(...p.w.params, limit);
  await st.close();
  return rows(t) as unknown as HotspotRow[];
}

/** Monthly counts per platform (never summed across platforms). */
export async function monthlyByPlatform(opts: QueryOpts): Promise<{ platform: string; ym: string; n: number }[]> {
  const p = await prepared(opts);
  if (!p) return [];
  const st = await p.conn.prepare(
    `SELECT platform, strftime(acq_date, '%Y-%m') AS ym, count(*) AS n FROM ${p.src} WHERE ${p.w.sql} GROUP BY ALL`,
  );
  const t = await st.query(...p.w.params);
  await st.close();
  return rows(t).map((r) => ({ platform: String(r.platform), ym: String(r.ym), n: Number(r.n) }));
}

/** Aqua detections (lat, lon, month) for per-detection calibration-region assignment. */
export async function aquaPoints(opts: QueryOpts): Promise<{ lat: number; lon: number; ym: string }[]> {
  const p = await prepared(opts);
  if (!p) return [];
  const st = await p.conn.prepare(
    `SELECT lat, lon, strftime(acq_date, '%Y-%m') AS ym FROM ${p.src} WHERE ${p.w.sql} AND platform = 'Aqua'`,
  );
  const t = await st.query(...p.w.params);
  await st.close();
  return rows(t).map((r) => ({ lat: Number(r.lat), lon: Number(r.lon), ym: String(r.ym) }));
}
