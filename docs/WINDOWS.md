# Running the science pipeline on Windows (PowerShell)

**You usually do not need this.** To build and deploy the website you only need Git and Node (`YOUR_TASKS/03_set_up_windows_pc.md`): the website data is already in the repo. Use this file only to re-run the analysis from the raw NASA data. It takes about an hour and about 2 GB of disk. These commands are translated from the `Makefile` and have **not been run on Windows**; on Linux/Mac use `make install && make data && make test`. Run everything from the folder that contains `pyproject.toml`.

## One-time setup
1. Install **Python 3.11** from python.org and tick "Add python.exe to PATH".
2. In PowerShell:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
```
`pytest` should end with about 192 passed and 1 skipped (Linux count). If PowerShell blocks scripts, you do not need to activate the venv: every command calls `.venv\Scripts\python` directly.

## Download and process the data (no key needed)
```powershell
.\.venv\Scripts\python -m blindspot.download --countries Pakistan India --years 2003-2025 --products modis viirs-snpp viirs-jpss1 --out data/raw/firms
.\.venv\Scripts\python -m blindspot.ingest --raw data/raw/firms --out data/processed/hotspots
.\.venv\Scripts\python -m blindspot.mask --hotspots data/processed/hotspots --out data/processed
.\.venv\Scripts\python -m blindspot.qc --hotspots data/processed/hotspots --mask-dir data/processed --json data/processed/qc_report.json --md docs/QC_REPORT.md
.\.venv\Scripts\python -m blindspot.boundaries --out data/raw/boundaries
.\.venv\Scripts\python -m blindspot.regions --hotspots data/processed/hotspots --boundaries data/raw/boundaries --out data/processed/regions
.\.venv\Scripts\python -m blindspot.calibrate --hotspots data/processed/hotspots --mask-dir data/processed --regions data/processed/regions --out data/processed/harmonized
```
If the download exits with code 2 ("no file arrived"), the yearly-country URL pattern changed: open https://firms.modaps.eosdis.nasa.gov/country/ , copy one file link and send it to Claude.

## The three tests and the reports
```powershell
.\.venv\Scripts\python -m blindspot.t1 --hotspots data/processed/hotspots --mask-dir data/processed --regions data/processed/regions --boundaries data/raw/boundaries --harmonized data/processed/harmonized --out data/processed/results/t1.json
.\.venv\Scripts\python -m blindspot.report_t1 --json data/processed/results/t1.json --md docs/RESULTS_T1.md --t2 data/processed/results/t2.json
.\.venv\Scripts\python -m blindspot.t2 --hotspots data/processed/hotspots --mask-dir data/processed --regions data/processed/regions --harmonized data/processed/harmonized --t1 data/processed/results/t1.json --out data/processed/results/t2.json
.\.venv\Scripts\python -m blindspot.report_t2 --json data/processed/results/t2.json --md docs/RESULTS_T2.md
.\.venv\Scripts\python -m blindspot.report_t1 --json data/processed/results/t1.json --md docs/RESULTS_T1.md --t2 data/processed/results/t2.json
.\.venv\Scripts\python -m blindspot.t3 --hotspots data/processed/hotspots --mask-dir data/processed --regions data/processed/regions --harmonized data/processed/harmonized --t1 data/processed/results/t1.json --out data/processed/results/t3.json --md docs/RESULTS_T3.md
.\.venv\Scripts\python -m blindspot.pitch --t1 data/processed/results/t1.json --t2 data/processed/results/t2.json --t3 data/processed/results/t3.json --plan docs/PLAN.md
```
The first `report_t1` line is only a first pass; the last `report_t1` line after `t2` is the final one (this mirrors the Makefile).

## Rebuild the website data (changes tracked files)
```powershell
.\.venv\Scripts\python -m blindspot.appdata --processed data/processed --boundaries data/raw/boundaries --out web/public/data
```
This overwrites the tracked files in `web/public/data`. Only run it if you intend to change the site's data, then rebuild the site (`cd web; npm run build`).

## Near-real-time data (needs your MAP_KEY)
Copy `.env.example` to `.env`, put your key after `FIRMS_MAP_KEY=` (never paste it into chat or commit it), then:
```powershell
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object { $k,$v = $_ -split '=',2; Set-Item -Path "env:$($k.Trim())" -Value $v.Trim() }
.\.venv\Scripts\python -m blindspot.download --area-source VIIRS_NOAA20_NRT --area-start 2026-11-01 --area-end 2026-11-10 --out data/raw/firms_nrt
```
