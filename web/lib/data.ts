import type { AreaDoc, CalibrationDoc, Constants, IndexDoc, TileManifest } from "./types";

/** Base path of the static data (public/data). */
export const DATA = "/data";

const cache = new Map<string, Promise<unknown>>();

export function getJson<T>(path: string): Promise<T> {
  const url = `${DATA}/${path}`;
  let p = cache.get(url);
  if (!p) {
    p = fetch(url).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${path} (HTTP ${r.status}). Run make appdata.`);
      return r.json();
    });
    cache.set(url, p);
  }
  return p as Promise<T>;
}

export const loadIndex = () => getJson<IndexDoc>("index.json");
export const loadConstants = () => getJson<Constants>("constants.json");
export const loadManifest = () => getJson<TileManifest>("tiles/manifest.json");
export const loadCalibration = () => getJson<CalibrationDoc>("results/calibration.json");
export const loadDistrict = (id: string) => getJson<AreaDoc>(`districts/${id}.json`);
