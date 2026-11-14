# Security review: Blind Spot

Date: 2026-10-31. Scope: git history and tree, `web/` (static Next.js export), `pipeline/blindspot/`. Read-only review; no code changed.

## Verdict

No secrets in the repo or its history. The MAP_KEY is handled carefully. DuckDB queries are parameterized. The real risks are known CVEs in two dependencies. Nothing is HIGH for the current local-only static deployment.

## Findings

### 1. maplibre-gl 5.16.0 has a known XSS sanitizer bypass. MEDIUM
- `web/package.json:17` (`"maplibre-gl": "5.16.0"`). `npm audit --omit=dev` rates GHSA-jrc7-96c5-q579 (DOM.sanitize bypass, <=6.4.0) as critical.
- Exploit: needs attacker HTML passing through MapLibre's sanitizer (for example popups or attribution set from untrusted data). The app uses a keyless inline style and same-origin `districts.geojson`, so it is not reachable today. It becomes reachable if popups ever show feature properties from third-party data.
- Fix: upgrade to maplibre-gl >= 6.5 (6.16.0 is the audit's suggestion; it is a major bump, so retest the map).

### 2. next 15.5.28 bundles a vulnerable postcss. LOW (build-time only)
- `web/package.json:19`. GHSA-qx2v-qp2m-jg93 and GHSA-6g55-p6wh-862q / -fxqj-rqcc-2cmp / -r28c-9q8g-f849 (postcss <=8.5.22: `</style>` XSS in stringify output, `.map` file read via sourceMappingURL).
- Exploit: only triggers when attacker-controlled CSS is processed at build time. All CSS here is first-party and from pinned @fontsource packages. The output is a static export, so no runtime Next server is exposed.
- Fix: upgrade Next once a patched 15.x line exists, or use an npm `overrides` entry for `postcss` >= 8.5.23. Rerun `npm audit --omit=dev`.

### 3. ATTRIBUTION.md rendered as raw HTML. LOW
- `web/app/attribution/page.tsx:9-10`: `marked.parse(...)` goes into `dangerouslySetInnerHTML`. marked does not sanitize, so any raw HTML or `javascript:` link in the markdown becomes live.
- Exploit: someone changes the pipeline output (`make appdata` writes `web/public/data/ATTRIBUTION.md`) or opens a PR that edits it. Rendering happens at build time from a committed file, so the attacker needs commit access.
- Fix: escape HTML in a marked renderer (`renderer.html = () => ""`), or run the output through a sanitizer (e.g. isomorphic-dompurify) at build time.

### 4. The inline theme script blocks a strict CSP. INFO
- `web/app/layout.tsx:16,23`: a constant string, so it carries no injection risk. Any future `script-src` CSP will need a hash for it. No CSP or security headers are set. A static host should add `Content-Security-Policy`, `X-Content-Type-Options: nosniff` and `Referrer-Policy`. DuckDB-WASM needs `'wasm-unsafe-eval'` and `worker-src 'self'`.

### 5. DuckDB-WASM 1.28.0. INFO
- `web/package.json:13`. npm audit reports no advisory. 1.28.0 is old (it ships an older DuckDB core). The engine runs inside the user's own browser on same-origin Parquet, so the impact of a bug is limited to that tab. Upgrade during routine maintenance.

### 6. Local static server. INFO
- `web/scripts/serve.mjs:12-14`: `normalize(join(root, url))` plus a `startsWith(root)` check blocks `../` traversal. One weakness: a sibling directory such as `.../web/out-evil` would pass a plain `startsWith`. Use `startsWith(root + sep)` instead. An unvalidated Range header (`end` beyond `size`, or `start > end`) can make createReadStream throw. This is a local-only tool, so impact is negligible.

## Checks that passed

- **Secrets in git:** `git log -p | grep -iE "map_key|api[_-]?key|token|secret|password"` returns only documentation, `.claude/` agent prose and test fixtures (`FAKE_KEY`, `"test-key"`). No real key appears. `.env` is ignored (`.gitignore` lines 1-4) and untracked; only `.env.example` is tracked. No `.map` files are tracked.
- **MAP_KEY in client code:** no `process.env` or `NEXT_PUBLIC_*` in `web/app|components|lib`. `web/lib/nrt.ts` holds no key and `NRT_ENDPOINT = null`. `out/` contains no key and no 32-hex strings. Its "FIRMS" mentions are attribution text only.
- **MAP_KEY in the pipeline:** `pipeline/blindspot/download.py:368-380` reads the key from the environment only. Logs use `label` (line 460), never the URL. Errors keep only the exception type name (line 253) and pass through `redact()` (line 472). The NRT manifest leaves out URLs and keys (lines 450, 497). Only https URLs are fetched (line 102).
- **SQL injection (web):** `web/lib/duck.ts:77-86`: all AOI and date values are bound `?` parameters. `EARTH_KM` is a constant. Table names come from the manifest with `'` stripped (line 95). Dates go through `CAST(? AS DATE)`. No injection path.
- **SQL f-strings (pipeline):** `mask.py:221,246,288,350` and `calibrate.py:373` interpolate only allow-listed view names and module constants (`PK_PUNJAB`). Values are bound. Inputs come from the CLI and config, not the network.
- **Download paths:** `download.py:331` builds paths from `--products`/`--countries`/years supplied by the operator. Country names are URL-quoted in URLs. Area output names use `choices=` sources and ISO dates. Nothing derives a path from a server response.
- **Third-party scripts and CDNs:** none. DuckDB bundles are self-hosted (`duck.ts:1-2`, `scripts/copy-duckdb.mjs`). Fonts come from @fontsource. The map has no tile or style CDN.
- **Static export leakage:** `next.config.mjs` uses default production settings, so no browser source maps are emitted and none exist in `out/`. `out/data` holds only the generated public data (JSON, GeoJSON, Parquet tiles, ATTRIBUTION.md). Nothing private is in it.

## Python dependencies
Not audited live (`pip-audit` is not installed). Pin versions and run `pip-audit` against `pyproject.toml` in CI.

## Resolution (31 Oct, D-038)
- **#1 fixed:** maplibre-gl 6.16.0, with the worker self-hosted. Map retested with `make web-test` 56/56.
- **#2 fixed:** npm `overrides` postcss 8.5.32. `npm ls postcss` shows 8.5.32 as overridden. `npm audit --omit=dev` reports **0 vulnerabilities**.
- **#3 fixed:** the Attribution page renders through a `Marked` instance that escapes raw HTML and images and drops unsafe link schemes.
- **#6 fixed:** `startsWith(root + sep)`. A bad Range returns 416.
- **Deferred (INFO):** #4 CSP and headers, to be set at the static host on deploy. #5 DuckDB-WASM upgrade (D-037 pin).
