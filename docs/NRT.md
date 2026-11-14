# Near-real-time card: deploy and test (D-010, D-040)

The static export (`web/out/`) stays static. The NRT card uses one Cloudflare Pages Function,
`web/functions/api/nrt.ts`, with the logic in `web/functions/_lib/nrt-core.ts`.

## What the function does

`GET /api/nrt?bbox=W,S,E,N[&area=<district or region id>][&month=YYYY-MM]`

1. Reads `FIRMS_MAP_KEY` from the server environment (a Pages secret). The key is never sent to the browser, never logged and never returned. Error text has the key replaced by `[MAP_KEY]`.
2. Calls the FIRMS area API `VIIRS_NOAA20_NRT` for the bbox in windows of at most 5 days. The windows run from the UTC day before the month starts up to today (local solar time is ahead of UTC).
3. Keeps VIIRS confidence n/h (`nominal`/`high` also accepted). Converts each detection to its local solar date (UTC + lon/15 h) and keeps the requested month. With `area`, it also clips to the district polygon (`districts.geojson`) or the Punjab outline (`results/calibration.json`).
4. Drops the persistent-hotspot mask cells in `data/nrt/mask_cells.json`, written by `make appdata` from `persistent_mask_cells.parquet` with the same cell formula as `mask.py`.
5. D-010: returns the NOAA-20 standard-archive median for the same calendar month, taken from the area JSON. Custom boxes have no median from the server, so the client uses its own NOAA-20 median. The card shows the ratio only once the month is complete. Before that it shows "d of D days so far".
6. FIRMS results are cached for 3 h per **snapped** bbox (outward to a 0.25° grid) and month, in memory (LRU, 500 entries) and in `caches.default` when present. Shared-cache entries carry a format version and `fetchedAt`; stale or old-format entries are refetched. Counting then uses the exact bbox (and polygon). The response sends `Cache-Control: s-maxage=10800`.

## Quota protection and errors (review fixes, docs/review/TS_REACT_REVIEW.md)

- **Origin:** no `*` CORS. A request whose `Origin` is not the site's own origin (or `ALLOWED_ORIGIN`, an optional Pages variable) gets 403 `forbidden_origin`.
- **Rate limit:** per-IP token bucket (`CF-Connecting-IP`), burst 20, then one request per 6 s, per isolate → 429 `rate_limited`. A Cloudflare rate-limiting rule on `/api/nrt` can be added in front.
- **Areas:** `area` must be a district id or region id listed in `index.json` (own keys only); otherwise 404 `unknown_area` before any FIRMS call. Known areas are counted on their server-side bbox.
- **Months:** only the current and the previous UTC month; anything else is 400 `month_out_of_window`. The client also refuses to label any other month as near-real-time.
- **FIRMS calls:** at most 7 per request; each has a 10 s timeout and the request has a 25 s budget → 504 `timeout`.
- **Bbox:** clamped to the coverage box (400 only when nothing is left); the client rounds outward.
- **Data files:** a missing or non-JSON asset (e.g. an HTML fallback) is 500 `missing_data` naming the file; 5xx errors are logged with the key redacted.
- `daysCovered` uses the local solar date at the bbox centre, the same clock as counting.

Every error body is `{ "status": "unavailable", "code": "...", "reason": "..." }`.
7. Every response is labelled `provisional: true` and carries `label` = constants.json `nrt_label` ("near-real-time, provisional").

The client (`web/lib/nrt.ts`) calls the function only when `NEXT_PUBLIC_NRT_ENDPOINT` is set at build time. This variable holds a URL, never a key. When it is unset, or the call fails, the card shows the cached archive snapshot and says why.

## Unit tests (no network, no key)

```
cd web && npm test        # vitest: functions/nrt.test.ts, mocked FIRMS CSV
```

The tests cover: day windows, CSV parsing and confidence filter, local solar date, mask, polygon clip, median, 3 h cache, input validation, the missing-key 503, grid snapping, unknown/prototype area ids, month window, timeout 504, bbox clamp, missing-data 500, shared-cache freshness, local daysCovered, origin 403, rate-limit 429, key redaction, and the Pages handler's headers and body. `make web-test` runs them too.

## Deploy (Cloudflare Pages)

1. Create a Pages project with root directory `web`, build command `NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt npm run build` and output directory `out`. Pages picks up `web/functions/` automatically.
2. Settings → Variables and Secrets → add `FIRMS_MAP_KEY` as an **encrypted secret** for Production (and Preview if wanted). Do not put it in `wrangler.toml`, `.env` committed files or any `NEXT_PUBLIC_*` variable.
3. Deploy. The static data files are served as assets; the function reads them through `env.ASSETS`.

Local run with your own key (for the test on 14 Nov). The key stays in your shell or in an untracked `web/.dev.vars`:

```
cd web
NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt npm run build
echo "FIRMS_MAP_KEY=<your key>" > .dev.vars      # .dev.vars must stay untracked (.gitignore)
npx wrangler@3 pages dev out --compatibility-date=2024-11-01
# then, in another terminal (Sangrur district id from public/data/index.json):
curl -s "http://localhost:8788/api/nrt?bbox=75.33,29.73,76.24,30.48&area=76128533B82601690264832" | python3 -m json.tool
```

Expected: `"status": "ok"`, `"provisional": true`, `noaa20` ≥ 0, `daysCovered` = today's day of the month, and `median.value` equal to `median.NOAA20.values[10]` in the district JSON (for November). Open http://localhost:8788/ and choose Sangrur. The card shows a third figure, "NOAA-20 VIIRS, November 2026 · near-real-time, provisional".

Checks: `curl ...?bbox=50,30,55,32` (outside the box) and `...&month=2005-03` give 400; `-H "Origin: https://evil.test"` gives 403. With no secret set, the answer is 503 "not configured", and the app falls back to the snapshot. Run `grep -r "<your key>" web/out` and confirm it finds nothing.

## Limits

- The FIRMS transaction limit (DATA_SCHEMA §4): one uncached request costs up to 7 transactions (5-day windows). The 3 h cache keeps this low.
- Boxes and circles are counted on their bounding box (the card says so). Districts and the two Punjab regions are counted on their polygons.
- NRT has no `type` field, so static-source filtering relies on the persistent mask alone (D-010).
