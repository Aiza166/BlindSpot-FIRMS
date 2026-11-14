# 04. Cloudflare account and wrangler login (no deploy)

**When:** before 13 Nov. **Time:** 20 min. **Allowed now:** creating an account and logging in is not publishing. Do **not** run `wrangler pages deploy`.

## What it is
The site is hosted on Cloudflare Pages (free plan), deployed with the Wrangler command-line tool (`docs/DEPLOY.md`, section B).

## Why it matters
A dead or missing link is scored very low (`docs/GRADE.md` item 2). Doing the account setup now saves time on 14 Nov.

## Steps
1. Go to https://dash.cloudflare.com/sign-up and sign up with the team email.
2. Verify the email. Turn on two-factor authentication: profile icon, **My Profile**, **Authentication**.
3. (Needs task 03 done.) In PowerShell: `cd nasa-hackathon\web` then `npx wrangler@3 login`. A browser tab opens; click **Allow**. Return to PowerShell; it should say you are logged in. Check with `npx wrangler@3 whoami`.
4. Stop here. Do **not** create the Pages project or deploy until 14 Nov 09:00 PKT (task 08 does that).

## Record the result
Tick the box. Do not write the Cloudflare password anywhere in the repo.

## Common problems
- **Browser does not open:** copy the URL printed by wrangler into the browser.
- **`npx` not found:** install Node (task 03).
- **Project name taken (later):** `docs/DEPLOY.md` says use `blindspot-firms`.
- Wrangler login on Windows is untested by the AI.
