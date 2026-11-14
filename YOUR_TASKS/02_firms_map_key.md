# 02. Get a FIRMS MAP_KEY and save it in `.env`

**When:** by 3 Nov (checkpoint P3). **Time:** 15 min.

## What it is
A free key from NASA FIRMS. It is used only for the live "this month" card (near-real-time data). The historical archive needs no key.

## Why it matters
It decides whether the month card shows the live current month (Impact, Presentation) or only the last archive month, labelled "not live". `docs/GRADE.md` item 2.

## Steps (Windows)
1. Open https://firms.modaps.eosdis.nasa.gov/api/map_key/ in your browser.
2. Click **Get MAP_KEY**, enter your email, submit.
3. Check your inbox and spam for the email from NASA FIRMS. It contains a 32-character key.
4. Back on that page, click **Check status**, paste the key. It should show your transaction limit. (Do not paste the key anywhere else.)
5. In the project folder (after task 03), copy `.env.example` to `.env`: in PowerShell `Copy-Item .env.example .env`.
6. Open `.env` in Notepad and put the key after `FIRMS_MAP_KEY=` with no quotes or spaces. Leave `OPENAQ_API_KEY=` empty. Save.

## Where to record the result
Tick P3 in `docs/CHECKPOINTS.md` ("key works on website"). Never write the key in any file except `.env`.

## Hard rules
- `.env` is in `.gitignore`; never commit it, paste it in chat, screenshot it or email it.
- If the key leaks, request a new one on the same page and replace it.
- A new Claude account or person must create their own `.env`; the key is not in the repo.

## Common problems
- **No email:** check spam; try again with another address.
- **Page says invalid key later:** copy again from the email, without trailing spaces.
- **Earthdata login:** P3 also mentions an Earthdata login; it is only needed for the website, not for our code. (Unverified whether required.)
