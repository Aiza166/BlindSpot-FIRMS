// Write out/_headers (Cloudflare Pages) after `next build` (D-041).
// Security headers on every path, including a short header CSP (frame-ancestors, object-src,
// base-uri, form-action). The full CSP goes in a <meta http-equiv> tag injected into each HTML
// page, with sha256 hashes of that page's inline scripts (Next.js RSC payload), so script-src
// needs no 'unsafe-inline'. A meta tag is used because the hash list for some pages is longer
// than the 2,000-character limit of a Cloudflare _headers line. Both policies are enforced.
// Also checks the export against Cloudflare Pages limits (20,000 files, 25 MiB per file).
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const out = join(fileURLToPath(new URL("..", import.meta.url)), "out");
const MAX_FILES = 20000;
const MAX_BYTES = 25 * 1024 * 1024;

const files = [];
(function walk(d) {
  for (const n of readdirSync(d)) {
    const p = join(d, n);
    if (statSync(p).isDirectory()) walk(p);
    else files.push(p);
  }
})(out);

const big = files.filter((f) => statSync(f).size > MAX_BYTES);
const largest = files.reduce((a, f) => (statSync(f).size > statSync(a).size ? f : a), files[0]);
console.log(`gen-headers: ${files.length} files (limit ${MAX_FILES}); largest ${relative(out, largest)} ${(statSync(largest).size / 2 ** 20).toFixed(1)} MiB (limit 25 MiB)`);
if (files.length + 1 > MAX_FILES || big.length) {
  console.error(`gen-headers: over Cloudflare Pages limits: ${big.map((f) => relative(out, f)).join(", ")}`);
  process.exit(1);
}

const common = [
  "X-Content-Type-Options: nosniff",
  "Referrer-Policy: strict-origin-when-cross-origin",
  "Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()",
  "X-Frame-Options: DENY",
  "Cross-Origin-Opener-Policy: same-origin",
  "Strict-Transport-Security: max-age=31536000",
  "Content-Security-Policy: frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'",
];
function csp(hashes) {
  return [
    "default-src 'self'",
    `script-src 'self' 'wasm-unsafe-eval' ${hashes.map((h) => `'sha256-${h}'`).join(" ")}`.trim(),
    "worker-src 'self' blob:",
    "connect-src 'self' blob: data:",
    "img-src 'self' data: blob:",
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self' data:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

const lines = ["/*", ...common.map((h) => `  ${h}`), ""];
let pages = 0;
const INLINE = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;
for (const f of files.filter((x) => x.endsWith(".html")).sort()) {
  const html = readFileSync(f, "utf8");
  const hashes = [...new Set([...html.matchAll(INLINE)].map((m) => createHash("sha256").update(m[1], "utf8").digest("base64")))];
  if (html.includes('http-equiv="Content-Security-Policy"')) continue; // already injected
  const tag = `<meta http-equiv="Content-Security-Policy" content="${csp(hashes)}"/>`;
  const anchor = '<meta charSet="utf-8"/>'; // keep charset in the first 1,024 bytes
  const at = html.indexOf(anchor);
  if (at < 0) { console.error(`gen-headers: no charset meta in ${relative(out, f)}`); process.exit(1); }
  const cut = at + anchor.length;
  writeFileSync(f, html.slice(0, cut) + tag + html.slice(cut));
  pages += 1;
}
// Long cache for content-hashed Next.js chunks.
lines.push("/_next/static/*", "  Cache-Control: public, max-age=31536000, immutable", "");
const rules = lines.filter((l) => l.startsWith("/")).length;
if (rules > 100) { console.error(`gen-headers: ${rules} rules (Cloudflare limit 100)`); process.exit(1); }
writeFileSync(join(out, "_headers"), lines.join("\n"));
console.log(`gen-headers: wrote out/_headers (${rules} rules); CSP meta tag in ${pages} pages`);
