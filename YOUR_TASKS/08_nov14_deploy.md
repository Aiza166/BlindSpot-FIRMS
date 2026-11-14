# 08. Sat 14 Nov: deploy and test (only after 09:00 PKT)

**When:** after **09:00 PKT, Sat 14 Nov**. **Time:** 1-2 h. Source of truth: `docs/DEPLOY.md` (decision D-041); this file mirrors it for Windows. Not tested on Windows.

## What it is
Build the site locally and upload it to Cloudflare Pages with Wrangler, set the FIRMS key as a secret, and run smoke tests including the live near-real-time card.

## Why it matters
No public link means no submission. The live month card closes the gap named in `docs/ARENA_CONCLUSION.md` fix 2, and a phone test closes checkpoint H26.

## Steps (PowerShell, from the repo folder, after tasks 02, 03, 04)
1. **Check the clock.** It must be 14 Nov 09:00 PKT or later.
2. `git pull`, then `git status` should be clean.
3. Tests (in `web`): `npm install --no-audit --no-fund`, then `npm run lint`, `npm run typecheck`, `npm test`. You do not need Python for deploy.
4. **Build with the live-card endpoint:** `cd web`, then
   ```
   $env:NEXT_PUBLIC_NRT_ENDPOINT="/api/nrt"
   npm run build
   ```
   The last lines must say `gen-headers: ... files (limit 20000)` and `wrote out/_headers`. (DEPLOY.md writes the Bash form `NEXT_PUBLIC_NRT_ENDPOINT=/api/nrt npm run build`; the PowerShell form is a translation.)
5. **Key check:** search the output for the first 8 characters of your key; it must find nothing: `Select-String -Path out\*,functions\* -Pattern "<first 8 chars>" -Recurse` (translation; ask Claude if unsure).
6. **Create the project (first time):** `npx wrangler@3 pages project create blindspot --production-branch main`. **On 14 Nov `https://blindspot.pages.dev` already served another team's site ("Smart Navigation for the Blind"), so expect the name to be taken:** use `blindspot-firms` (or another free name) everywhere below, including `web/wrangler.toml` and the curl tests. The URL will be `https://<name>.pages.dev`.
7. **Secret:** `npx wrangler@3 pages secret put FIRMS_MAP_KEY --project-name blindspot`, paste the key when asked (it does not echo). Never put it in a file.
8. **Deploy (from `web\`):** `npx wrangler@3 pages deploy out --project-name blindspot --branch main --commit-dirty=true`. Note the printed URL.
9. **Test the live card:** in PowerShell use `curl.exe` (not the `curl` alias):
   ```
   curl.exe -s "https://blindspot.pages.dev/api/nrt?bbox=75.33,29.73,76.24,30.48&area=76128533B82601690264832" -H "Origin: https://blindspot.pages.dev"
   ```
   Expect `"status": "ok"` and `"provisional": true`. With `-H "Origin: https://evil.test"` expect 403. With `bbox=50,30,55,32` expect 400.
10. **Smoke tests**, in a private window, logged out, and on your phone over mobile data (DEPLOY.md section F): home page loads with Punjab; raw/harmonized toggle changes the calendar; Sangrur month card shows a third figure "NOAA-20 VIIRS, November 2026 · near-real-time, provisional"; draw a custom box; download a CSV; open /results/, /use-case/, /methods/, /about/, /attribution/; console shows no errors (F12).
11. **Repo public or not:** on 14 Nov the GitHub repo was already public. Run the secret scan in DEPLOY.md section G anyway. The 2026 guide does not require a code link; "Link to Final Project" can be the live app.
12. **Optional:** request a FortiGuard Web Filter classification for the new URL (https://www.fortiguard.com/faq/wfratingsubmit, Company Name "N/A") so school or office filters do not block judges.

## Record the result
Write the production URL and date in `docs/CHECKPOINTS.md` (H1, H26) and tell Claude. Tick the box.

## Common problems
- **Rollback:** Cloudflare dashboard, Workers & Pages, blindspot, Deployments, pick the last good one, **Rollback**.
- **Key leaked or quota abused:** `npx wrangler@3 pages secret delete FIRMS_MAP_KEY --project-name blindspot`; the card falls back to the archive snapshot; request a new key.
- **Build fails the size check:** see DEPLOY.md ("If the build ever fails the size check").
- **NRT returns 503:** secret missing or misspelt; set it again.
- **Whole site must go down:** dashboard, blindspot, Settings, Delete project.
