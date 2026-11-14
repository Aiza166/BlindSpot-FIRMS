import type { Bbox } from "./types";

type Ring = number[][];

function inRing(lon: number, lat: number, ring: Ring): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i]![0]!, yi = ring[i]![1]!;
    const xj = ring[j]![0]!, yj = ring[j]![1]!;
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function inPolygon(lon: number, lat: number, rings: Ring[]): boolean {
  if (!rings[0] || !inRing(lon, lat, rings[0])) return false;
  for (let k = 1; k < rings.length; k++) if (inRing(lon, lat, rings[k]!)) return false;
  return true;
}

/** Point-in-polygon for GeoJSON Polygon / MultiPolygon (even-odd rule, holes respected). */
export function pointInGeometry(lon: number, lat: number, g: GeoJSON.Geometry): boolean {
  if (g.type === "Polygon") return inPolygon(lon, lat, g.coordinates as Ring[]);
  if (g.type === "MultiPolygon") return (g.coordinates as Ring[][]).some((p) => inPolygon(lon, lat, p));
  return false;
}

export function geometryBbox(g: GeoJSON.Geometry): Bbox {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const walk = (c: unknown): void => {
    if (Array.isArray(c) && typeof c[0] === "number") {
      const [x, y] = c as number[];
      x0 = Math.min(x0, x!); x1 = Math.max(x1, x!); y0 = Math.min(y0, y!); y1 = Math.max(y1, y!);
    } else if (Array.isArray(c)) c.forEach(walk);
  };
  if ("coordinates" in g) walk(g.coordinates);
  return [x0, y0, x1, y1];
}

export function bboxIntersects(a: Bbox, b: Bbox): boolean {
  return a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
}

const KM_PER_DEG_LAT = 111.32;

/** Bounding box that contains a circle of km radius around (lat, lon). */
export function radiusBbox(lat: number, lon: number, km: number): Bbox {
  const dLat = km / KM_PER_DEG_LAT;
  const dLon = km / (KM_PER_DEG_LAT * Math.cos((lat * Math.PI) / 180));
  return [lon - dLon, lat - dLat, lon + dLon, lat + dLat];
}

export function circlePolygon(lat: number, lon: number, km: number, n = 64): GeoJSON.Polygon {
  const dLat = km / KM_PER_DEG_LAT;
  const dLon = km / (KM_PER_DEG_LAT * Math.cos((lat * Math.PI) / 180));
  const ring: number[][] = [];
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * 2 * Math.PI;
    ring.push([lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)]);
  }
  return { type: "Polygon", coordinates: [ring] };
}

export function bboxPolygon(b: Bbox): GeoJSON.Polygon {
  return { type: "Polygon", coordinates: [[[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]], [b[0], b[1]]]] };
}

/** 1-degree tile keys (floor lat, floor lon) touching a bbox, clipped to the coverage box. */
export function tileKeys(b: Bbox, cov: { lon_min: number; lon_max: number; lat_min: number; lat_max: number }, deg: number): { lat: number; lon: number }[] {
  const lon0 = Math.max(b[0], cov.lon_min), lon1 = Math.min(b[2], cov.lon_max);
  const lat0 = Math.max(b[1], cov.lat_min), lat1 = Math.min(b[3], cov.lat_max);
  const out: { lat: number; lon: number }[] = [];
  if (lon0 > lon1 || lat0 > lat1) return out;
  for (let la = Math.floor(lat0 / deg) * deg; la <= lat1; la += deg)
    for (let lo = Math.floor(lon0 / deg) * deg; lo <= lon1; lo += deg) out.push({ lat: la, lon: lo });
  return out;
}
