# Deploy on 14 Nov (Cloudflare Pages)

Rule: nothing public before **14 Nov 09:00 PKT**. Everything below happens on or after that time. Decision: D-041.

## How it is set up

| Item | Value |
|---|---|
| Host | Cloudflare Pages, free plan |
| Method | **Direct Upload with Wrangler** from any computer with Git and Node (the app data is in the repo, D-045). Git integration is also possible but untested. |
| Project root | `web/` |
| Build command (local) | `NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt npm run build` |
| Output directory | `web/out` (`pages_build_output_dir` in `web/wrangler.toml`) |
| Functions | `web/functions/` (one function, `/api/nrt`), uploaded with the output |
| Headers | `web/out/_headers`, written by `web/scripts/gen-headers.mjs` at the end of every build |
| Redirects | none needed (`trailingSlash: true` export; Pages serves `/about` → `/about/`) |
| Secret | `FIRMS_MAP_KEY` (encrypted secret, Production) |
| Variable | `ALLOWED_ORIGIN` (optional, plain; set only if a second origin such as a custom domain must call `/api/nrt`) |

### Why Direct Upload, and what changed (D-045)

Originally the 116 MB of app data (`web/public/data`) was gitignored, so a build had to run on a computer that had rebuilt it with `make data` (about an hour). On 1 Nov 2026 the data was committed to the private repo, and a clean clone was tested: `npm install` (24 s) and `npm run build` produced the full site (4,028 files, 161 MB). So any computer with Git and Node can build and upload. We still use Direct Upload because it is the tested path. Cloudflare's Git integration (build command `cd web && npm install && npm run build`, output `web/out`, variable `NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt`) should now also work but has not been tried.

### Size against Cloudflare Pages limits (checked by `gen-headers.mjs` on every build)

| Limit | Ours (1 Nov build) |
|---|---|
| ≤ 20,000 files per deployment | 4,023 (incl. `_headers`) |
| ≤ 25 MiB per file | largest `duckdb/duckdb-mvp.wasm` 21.1 MiB; largest data tile far smaller |
| `_headers` ≤ 100 rules, line ≤ 2,000 chars | 2 rules |

No R2 or GitHub Releases needed. **If** the build ever fails the size check (for example more years or countries): put `web/public/data/tiles/` in an R2 bucket with a public custom domain or `r2.dev` URL, point the tile base URL at it, and add that origin to `connect-src` in `gen-headers.mjs`. GitHub Releases is not suitable for tiles (no CORS, no Range requests).

### Security headers

All paths (`/*` in `_headers`): `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` (camera, microphone, geolocation, payment, usb off), `X-Frame-Options: DENY`, `Cross-Origin-Opener-Policy: same-origin`, `Strict-Transport-Security`, and a header CSP `frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'`.

Each HTML page also gets a `<meta http-equiv="Content-Security-Policy">` with: `default-src 'self'`; `script-src 'self' 'wasm-unsafe-eval'` + sha256 hashes of that page's inline Next.js scripts (no `'unsafe-inline'` for scripts); `worker-src 'self' blob:`; `connect-src 'self' blob: data:`; `img-src 'self' data: blob:`; `style-src 'self' 'unsafe-inline'` (React style attributes and MapLibre need it); `font-src 'self' data:`. Why a meta tag: the results page has 185 inline scripts and its hash list is longer than the 2,000-character `_headers` line limit. Browsers enforce both policies. No third-party origins: fonts, MapLibre and DuckDB-WASM are self-hosted, and there is no external basemap.

Rehearsed locally: `make deploy-rehearsal` builds, serves `web/out` with `_headers` applied, prints the headers and runs the full Playwright e2e (which fails on any console error, including CSP violations). `make web-test` now also serves with the headers.

## Steps on 14 Nov (after 09:00 PKT)

### A. Build (any computer with Git and Node, about 5 min)

1. `git pull` and confirm `git status` is clean.
2. In `web/`: `npm install --no-audit --no-fund`, then `npm run lint`, `npm run typecheck` and `npm test` (Windows-friendly). The full `make test` and `make web-test` need Python and `sh`; they are optional on Windows and were run on Linux (see `docs/MORNING_SUMMARY.md`).
3. `cd web && NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt npm run build`. **In Git Bash on Windows, prefix `MSYS_NO_PATHCONV=1`**: without it Git Bash rewrites `/api/nrt` to `C:/Program Files/Git/api/nrt`, the CSP blocks that request and the card falls back to the archive (seen on 15 Nov). Check with `grep -rl "Program Files" out/_next` (must find nothing). PowerShell is not affected. The last lines must say `gen-headers: ... files (limit 20000)` and `wrote out/_headers`.
4. `grep -rl "<first 8 characters of your key>" out functions` must find nothing.

### B. Cloudflare account and project (first time only, about 10 min)

1. Go to https://dash.cloudflare.com/sign-up and create an account with the team email. Turn on two-factor authentication (My Profile → Authentication).
2. On the laptop: `cd web && npx wrangler@3 login` (opens the browser; click **Allow**).
3. `npx wrangler@3 pages project create blindspot --production-branch main`. If the name is taken, use `blindspot-firms` and use that name below. The site URL is `https://<name>.pages.dev`.

### C. Secret

1. `npx wrangler@3 pages secret put FIRMS_MAP_KEY --project-name blindspot` and paste the key when asked. (Or dashboard: Workers & Pages → blindspot → Settings → Variables and Secrets → Add → Type **Secret** → name `FIRMS_MAP_KEY` → Save.)
2. Leave `ALLOWED_ORIGIN` empty unless you add a custom domain.
3. Never put the key in `wrangler.toml`, `.env` in git, a `NEXT_PUBLIC_*` variable, chat or screenshots.

### D. Deploy

1. `cd web && npx wrangler@3 pages deploy out --project-name blindspot --branch main --commit-dirty=true`. Run it from `web/` so `functions/` is uploaded.
2. Note the deployment URL printed (`https://<hash>.blindspot.pages.dev`) and the production URL `https://blindspot.pages.dev`.

### E. Test NRT with the key

1. `curl -s "https://blindspot.pages.dev/api/nrt?bbox=75.33,29.73,76.24,30.48&area=76128533B82601690264832" -H "Origin: https://blindspot.pages.dev" | python3 -m json.tool` → `"status": "ok"`, `"provisional": true`, `daysCovered` = today's day of month.
2. Same with `-H "Origin: https://evil.test"` → 403 `forbidden_origin`. `bbox=50,30,55,32` → 400.
3. `curl -s https://blindspot.pages.dev/ | grep -c "<first 8 characters of your key>"` → 0.

### F. Smoke tests (phone and laptop, logged out / private window)

1. `curl -sI https://blindspot.pages.dev/` shows `content-security-policy`, `x-content-type-options: nosniff`, `referrer-policy`, `permissions-policy`, `x-frame-options: DENY`.
2. Home page loads; map shows Punjab; no errors in the browser console (laptop: F12 → Console).
3. Pick PK Punjab: raw → harmonized toggle changes the calendar; 2012 step numbers match `docs/SUBMISSION.md`.
4. Pick Sangrur: month card shows a third figure "NOAA-20 VIIRS, November 2026 · near-real-time, provisional".
5. Draw a custom box: series appears (DuckDB-WASM works under the CSP).
6. Download CSV: file opens; NRT rows labelled provisional.
7. Open /results/, /use-case/, /methods/, /about/, /attribution/: all load.
8. On a phone (4G): home page usable, calendar readable, toggle works. Closes H26.
9. Optional: https://securityheaders.com and https://observatory.mozilla.org on the URL.

### G. Repo public or not

The app does not need the repo to be public. Make it public only if the 2026 submission guide asks for a code link (re-check on 13 Nov). Before making it public: `git log -p | grep -i "map_key=\|FIRMS_MAP_KEY=[a-f0-9]"` finds no real key; `.dev.vars` and `.env` are not tracked (`git ls-files | grep -E "\.env$|dev.vars"` is empty). Then GitHub → Settings → General → Danger Zone → Change visibility → Public.

### H. Rollback

- Bad deploy: dashboard → Workers & Pages → blindspot → Deployments → pick the last good one → **⋯ → Rollback to this deployment**. Or redeploy an older build: `git checkout <good commit> && make appdata && cd web && npm run build && npx wrangler@3 pages deploy out ...`.
- Key leaked or quota abused: delete the secret (`npx wrangler@3 pages secret delete FIRMS_MAP_KEY --project-name blindspot`); the card falls back to the archive snapshot (503 "not configured"). Ask FIRMS for a new key, then set it again.
- Whole site must go down: dashboard → blindspot → Settings → **Delete project** (the URL stops working).
