# 03. Set up the project on your Windows 11 PC

**When:** before 10 Nov (so launch day is not spent installing). **Time:** about 30 minutes (Git, Node, a 165 MB clone and a 5 minute build). No data rebuild needed.

## What it is
Install Git and Node, clone the private repo, build the website locally and look at it.

## Why it matters
The deploy on 14 Nov builds the site on a computer and uploads it. Since 1 Nov 2026 the website's data (`web/public/data`, 116 MB) is stored in the repo (decision D-045), so you do not need Python, the 1.2 GB NASA download or the hour-long data rebuild. A clean clone was tested on Linux: `npm install` took 24 seconds and `npm run build` produced the full site.

## Not tested on Windows
The steps below use only Git, Node and npm, which behave the same on Windows, but nobody has run them on Windows yet. The Linux test used Node v22.22.0. Use the current Node LTS (22 or newer); other versions are unverified. If something fails, send Claude the error text.

## Steps
1. **Install tools.**
   - Git: https://git-scm.com/download/win (defaults are fine).
   - Node.js LTS from https://nodejs.org/ . Then in PowerShell run `node -v` and `npm -v` and note the versions.
2. **Clone the private repo.** Open PowerShell, go somewhere short like `C:\work`:
   ```
   git clone https://github.com/Aiza166/BlindSpot-FIRMS.git
   cd BlindSpot-FIRMS
   ```
   Git asks you to sign in to GitHub (browser popup). A different GitHub account must be added as a collaborator first (`docs/CONTINUE.md`).
3. **Build and view the site:**
   ```
   cd web
   npm install --no-audit --no-fund
   npm run build
   npm run serve
   ```
   The build must end with lines starting `gen-headers:` and `wrote out/_headers`. Open http://localhost:4173 and check: the explorer opens on a district, the calendar shows, the month card says "Latest available month, not live". Stop the server with Ctrl+C.
4. **Run the quick checks:** in `web`: `npm run lint`, `npm run typecheck`, `npm test`. All should pass (vitest: 33 tests on Linux).

## Optional: re-run the science (only if you change the analysis)
This needs Python 3.11 and takes about an hour. Follow `docs/WINDOWS.md`. Running the last step (`appdata`) rewrites tracked files under `web/public/data`, so do not run it unless you mean to change the site's data.

## Record the result
Tick the box in `YOUR_TASKS/README.md`. Add a line to `docs/CHECKPOINTS.md` ("Windows setup done, Node version X"). If you hit Windows errors, tell Claude so this file can be fixed.

## Common problems
- **`git` or `node` not found:** close and reopen PowerShell after installing.
- **`npm install` is slow or fails:** retry; check `node -v`.
- **Long paths error:** clone close to the drive root, for example `C:\work\`.
- **Port 4173 in use:** close the other window running the server.
- **Clone asks for a password:** use the browser sign-in, not your GitHub password; or create a personal access token (GitHub, Settings, Developer settings).
