// Self-host DuckDB-WASM bundles so the static export needs no CDN at runtime.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "node_modules/@duckdb/duckdb-wasm/dist");
const dst = join(root, "public/duckdb");
mkdirSync(dst, { recursive: true });
for (const f of ["duckdb-mvp.wasm", "duckdb-eh.wasm", "duckdb-browser-mvp.worker.js", "duckdb-browser-eh.worker.js"]) {
  copyFileSync(join(src, f), join(dst, f));
}
console.log("duckdb-wasm bundles copied to public/duckdb");

// MapLibre 6 loads its worker from a separate module file next to the bundle; self-host it (D-038).
const mlDst = join(root, "public/maplibre");
mkdirSync(mlDst, { recursive: true });
copyFileSync(join(root, "node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs"), join(mlDst, "maplibre-gl-worker.mjs"));
console.log("maplibre-gl worker copied to public/maplibre");
