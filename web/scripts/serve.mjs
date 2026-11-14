// Minimal static server for the export in out/ (local testing only; supports Range).
import { createServer } from "node:http";
import { createReadStream, existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";
const root = join(fileURLToPath(new URL("..", import.meta.url)), "out");
const port = Number(process.env.PORT ?? 4173);
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json", ".geojson": "application/geo+json", ".wasm": "application/wasm", ".parquet": "application/octet-stream", ".md": "text/markdown; charset=utf-8", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".png": "image/png", ".txt": "text/plain" };
// --headers flag: apply out/_headers like Cloudflare Pages (exact paths and trailing "*" splats;
// repeated headers are comma-joined) for the local deploy rehearsal (D-041).
const rules = [];
if (process.argv.includes("--headers") || process.env.HEADERS === "1") {
  let cur = null;
  for (const line of readFileSync(join(root, "_headers"), "utf8").split("\n")) {
    if (line.startsWith("/")) { cur = { path: line.trim(), headers: [] }; rules.push(cur); }
    else if (cur && line.trim()) { const i = line.indexOf(":"); cur.headers.push([line.slice(0, i).trim().toLowerCase(), line.slice(i + 1).trim()]); }
  }
  console.log(`applying ${rules.length} _headers rules`);
}
function extra(url) {
  const h = {};
  for (const r of rules) {
    const hit = r.path.endsWith("*") ? url.startsWith(r.path.slice(0, -1)) : url === r.path;
    if (hit) for (const [k, v] of r.headers) h[k] = h[k] ? `${h[k]}, ${v}` : v;
  }
  return h;
}
createServer((req, res) => {
  const url = decodeURIComponent((req.url ?? "/").split("?")[0]);
  for (const [k, v] of Object.entries(extra(url))) res.setHeader(k, v);
  let p = normalize(join(root, url));
  if (p !== root && !p.startsWith(root + sep)) { res.writeHead(403).end(); return; }
  if (existsSync(p) && statSync(p).isDirectory()) p = join(p, "index.html");
  if (!existsSync(p)) { res.writeHead(404, { "content-type": "text/plain" }).end("not found"); return; }
  const size = statSync(p).size;
  const type = types[extname(p)] ?? "application/octet-stream";
  const range = req.headers.range?.match(/bytes=(\d*)-(\d*)/);
  if (range) {
    const start = range[1] ? Number(range[1]) : 0;
    const end = Math.min(range[2] ? Number(range[2]) : size - 1, size - 1);
    if (start > end || start >= size) { res.writeHead(416, { "content-range": `bytes */${size}` }).end(); return; }
    res.writeHead(206, { "content-type": type, "content-range": `bytes ${start}-${end}/${size}`, "accept-ranges": "bytes", "content-length": end - start + 1 });
    createReadStream(p, { start, end }).pipe(res);
    return;
  }
  res.writeHead(200, { "content-type": type, "content-length": size, "accept-ranges": "bytes" });
  createReadStream(p).pipe(res);
}).listen(port, () => console.log(`serving ${root} on http://localhost:${port}`));
