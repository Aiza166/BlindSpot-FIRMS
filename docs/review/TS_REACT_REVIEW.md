# TypeScript + React review: commit e452edc (web/) and web/functions/

Reviewers: typescript-reviewer, react-reviewer (agent definitions in .claude/agents). Read-only review; no code changed.
Scope: web/ excluding node_modules, .next, out, public/data. Focus: web/functions (Cloudflare Pages NRT function).

Verdict: no CRITICAL findings. The key stays on the server, the FIRMS URL is built only from validated numbers and constants (no SSRF), and the memo cache has a size bound. The main risks are abuse of the key's quota and wrong zero counts for months that NRT does not cover.

## Findings

### HIGH-1: Anyone can drain the FIRMS transaction quota (open CORS, cache can be bypassed)
- File: web/functions/api/nrt.ts:228, web/functions/_lib/nrt-core.ts:76,159,171
- Scenario: `access-control-allow-origin: *` with no rate limit. Each request that misses the cache makes up to 7 FIRMS calls (one per 5-day window). The cache key rounds the bbox to 1e-4 degrees, so an attacker can shift the bbox by 0.0001 on each request, miss the cache every time, and use up the MAP_KEY transaction limit. After that the service fails for everyone with "FIRMS did not return a CSV".
- Fix: restrict CORS to the site's own origin, or drop the header because the call is same-origin. Add a per-IP rate limit (Cloudflare rate-limiting rule or a KV/DO counter). Snap the bbox to a coarse grid, e.g. 0.05 degrees, before building the cache key and the FIRMS URL, then filter to the exact bbox when counting.

### HIGH-2: Months outside the NRT window return a confident zero
- File: web/functions/_lib/nrt-core.ts:71-72,158
- Scenario: `month=2005-03` or `month=0001-01` passes validation. Date.UTC maps years 0-99 to 1900-1999. FIRMS NRT keeps only about the last 2 months, so the response is `status:"ok", noaa20:0` for a complete month. MonthCard then shows "0 vs median N, far below". Each such request also spends up to 7 FIRMS transactions.
- Fix: accept only the current month and the previous month (or the window that FIRMS NRT actually serves). Reject anything else with 400 "month outside the near-real-time window". Reject years below 2012 explicitly.

### MEDIUM-1: The outbound FIRMS fetch has no timeout
- File: web/functions/api/nrt.ts:236; nrt-core.ts:174
- Scenario: FIRMS hangs. Up to 7 calls run one after another, so the function waits until the platform's wall-clock limit. The client gets a platform error page, not the JSON `unavailable` body.
- Fix: `fetch(u, { signal: AbortSignal.timeout(8000) })`, and set an overall time budget. The existing catch already redacts the key from the message.

### MEDIUM-2: The client's rounding can push an edge district outside the coverage box
- File: web/lib/nrt.ts:38 vs nrt-core.ts:69
- Scenario: the client sends `toFixed(4)`. A district bbox at lon_max = 77.84999 becomes 77.8500 > lon_max, and the server returns 400 "bbox is outside the coverage box" for a valid district.
- Fix: on the server, clamp the bbox to the coverage box (with a small tolerance) instead of rejecting it. Or on the client, round west/south down and east/north up, then clamp.

### MEDIUM-3: `area` lookup uses prototype keys
- File: web/functions/_lib/nrt-core.ts:142
- Scenario: `area=__proto__` or `area=constructor` passes `/^[A-Za-z0-9_]{1,64}$/`. `index.regions["constructor"]` is a function and is truthy, so the code reads `data/function Object() {...}`. The result is a 404 or a JSON SyntaxError, which becomes a 500. There is no exploit, but it is a wrong code path.
- Fix: `Object.hasOwn(index.regions, id)`, and validate the area id against index.json district/region ids before touching any asset.

### MEDIUM-4: A missing asset can turn into a 500 or a wrong 404 reason
- File: web/functions/api/nrt.ts:238-240
- Scenario: Pages can serve a 200 HTML fallback (404.html or SPA routing) for an unknown path. `r.json()` then throws a SyntaxError, the response is a 500 "internal error", and nothing is logged. The 404 message also says "unknown area" when the missing file is a core file such as constants.json or mask_cells.json, which hides a deployment fault.
- Fix: check that `content-type` is JSON before parsing. Give core files a 500 with a distinct reason. Log unexpected errors (`console.error` of the error with the key redacted) so failures are visible in observability.

### LOW-1: Shared-cache hits skip the memo and freshness checks
- File: nrt-core.ts:162-163
- Scenario: an edge-cache hit is returned without being put in the memo, and its `fetchedAt` age is never checked. Expiry relies only on the edge max-age. A body from an older format version could also be served after a deploy.
- Fix: check `now - Date.parse(shared.fetchedAt) < CACHE_SECONDS*1000`, add a schema version to the cache key, and memoize the hit.

### LOW-2: The memo evicts in FIFO order, not LRU, and expired entries are never pruned
- File: nrt-core.ts:211
- Impact: memory stays bounded at 500 entries, which is fine. Hot entries can be evicted before cold ones. This matters little per isolate. Optional fix: delete the key and set it again on a hit (LRU), and skip expired entries.

### LOW-3: `daysCovered` uses the UTC day, while counting uses local solar days
- File: nrt-core.ts:194
- Scenario: shortly after local midnight (up to 5.4 h ahead of UTC), detections for local day D+1 are counted but `daysCovered` still says D. The copy saying how much of the month has passed is off by one day.
- Fix: compute the current local date with the bbox centre longitude (`now + lonC/15 h`).

### LOW-4: The past-month check compares strings before the year is constrained
- File: nrt-core.ts:158
- Note: `q.month > now.slice(0,7)` works because the format is fixed to YYYY-MM. Keep the regex and this check together. Covered by the fix for HIGH-2.

### LOW-5 (React): The Explorer fetches the region file at an empty path when a region is unknown
- File: web/components/Explorer.tsx (overlappedRegions block, `getJson(index.regions[r] ?? "")`)
- Scenario: if a calibration region has no entry in index.json, the code fetches `data/`, gets HTML, and throws a JSON error. Flags for the custom area are then lost without any notice.
- Fix: filter out regions without an index entry before `Promise.all`, or use `Promise.allSettled`.

### LOW-6 (React): The NRT fetch in the Explorer passes no AbortSignal
- File: web/components/Explorer.tsx (`fetchNrt(nrtBbox, ...)`)
- Scenario: `reqId` prevents stale state updates, but switching areas quickly leaves requests running, and each one costs FIRMS transactions on a cache miss (see HIGH-1).
- Fix: create an AbortController for each selection and abort it in the effect cleanup or when a new request starts. fetchNrt already rethrows AbortError.

### LOW-7 (React): The client shows the server's `reason` text as is
- File: web/lib/nrt.ts:44-45, MonthCard.tsx
- Note: React escapes the text, so there is no XSS. Server reasons are fixed strings, and the FIRMS error path is redacted. If upstream text is ever passed through, keep reason strings fixed on the server.

## Verified OK
- The key is used only in the outbound URL. `redact()` is applied to fetch exception messages. The HTTP-status error carries no URL. The 503 for a missing key reveals nothing.
- SSRF: the host is the constant FIRMS_AREA. The path parts are a validated finite number bbox, a fixed SOURCE, an integer day count and an ISO date. readAsset paths come from validated ids and index.json.
- Bbox validation: finite, ordered, inside the coverage box, at most 50 square degrees. Month: regex. Area: charset and length.
- React: hook dependencies in Calendar `useMemo` are correct. Keys are stable (year, code). Flag icons are `aria-hidden` with sr-only text. Deep-link params are checked against the period.

## Resolution (1 Nov)

All HIGH and MEDIUM findings and the cheap LOWs are fixed in web/functions/, web/lib/nrt.ts, web/lib/reliability.ts and web/components/Explorer.tsx. Tests: functions/nrt.test.ts, 24 vitest tests (15 new). `make web-test` green: eslint 0, tsc 0, vitest 24/24, Playwright 127/127.

- HIGH-1: CORS `*` removed; foreign `Origin` → 403 (`ALLOWED_ORIGIN` env optional). Area ids must be in index.json; known areas use their server bbox. FIRMS bbox snapped outward to 0.25°, cache keyed on the snapped box, exact bbox used for counting. Per-IP token bucket (20 burst, 1/6 s) → 429. Hard cap of 7 FIRMS calls.
- HIGH-2 / LOW-4: only current and previous UTC month, else 400 `month_out_of_window`; client drops any other month.
- MEDIUM-1: 10 s AbortSignal timeout per call, 25 s budget → 504 `timeout`.
- MEDIUM-2: bbox clamped to the coverage box; client rounds outward.
- MEDIUM-3: `Object.hasOwn` for region and polygon lookup; districts checked against index.json.
- MEDIUM-4: non-JSON or missing asset → `AssetMissing` → 500 `missing_data` naming the file; error bodies carry a `code`; 5xx logged with key redacted.
- LOW-1: shared-cache hits checked for age and format version, then memoized. LOW-2: LRU touch and expiry pruning.
- LOW-3: `daysCovered` from the local solar date at the bbox centre.
- LOW-5: regions without an index entry are filtered (`knownRegions`). LOW-6: one AbortController per selection, aborted on a new selection and on unmount.
- LOW-7: unchanged; server reasons remain fixed strings.
