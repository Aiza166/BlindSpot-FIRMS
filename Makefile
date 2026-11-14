# Blind Spot pipeline. Run from the repo root.
# `make data` needs network access to firms.modaps.eosdis.nasa.gov (run it on your own computer).

PY      ?= .venv/bin/python
VENV    ?= .venv
COUNTRIES ?= Pakistan India
YEARS     ?= 2003-2025
PRODUCTS  ?= modis viirs-snpp viirs-jpss1
RAW       ?= data/raw/firms
PROCESSED ?= data/processed
BOUNDARIES ?= data/raw/boundaries

.PHONY: story install data download ingest mask mask-compare qc boundaries regions calibrate t1 t2 t3 appdata web web-test deploy-rehearsal \
	test lint format clean-processed

install:
	python3.11 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e '.[dev]'

data: download ingest mask qc boundaries regions calibrate t1 t2 t3 appdata

download:
	$(PY) -m blindspot.download --countries $(COUNTRIES) --years $(YEARS) \
		--products $(PRODUCTS) --out $(RAW)

ingest:
	$(PY) -m blindspot.ingest --raw $(RAW) --out $(PROCESSED)/hotspots

mask:
	$(PY) -m blindspot.mask --hotspots $(PROCESSED)/hotspots --out $(PROCESSED)

mask-compare:
	$(PY) -m blindspot.mask_compare --hotspots $(PROCESSED)/hotspots \
		--json $(PROCESSED)/mask_comparison.json --md docs/MASK_COMPARISON.md

qc:
	$(PY) -m blindspot.qc --hotspots $(PROCESSED)/hotspots --mask-dir $(PROCESSED) \
		--json $(PROCESSED)/qc_report.json --md docs/QC_REPORT.md

boundaries:
	$(PY) -m blindspot.boundaries --out $(BOUNDARIES)

regions:
	$(PY) -m blindspot.regions --hotspots $(PROCESSED)/hotspots --boundaries $(BOUNDARIES) \
		--out $(PROCESSED)/regions

calibrate:
	$(PY) -m blindspot.calibrate --hotspots $(PROCESSED)/hotspots --mask-dir $(PROCESSED) \
		--regions $(PROCESSED)/regions --out $(PROCESSED)/harmonized

t1:
	$(PY) -m blindspot.t1 --hotspots $(PROCESSED)/hotspots --mask-dir $(PROCESSED) \
		--regions $(PROCESSED)/regions --boundaries $(BOUNDARIES) \
		--harmonized $(PROCESSED)/harmonized --out $(PROCESSED)/results/t1.json
	$(PY) -m blindspot.report_t1 --json $(PROCESSED)/results/t1.json --md docs/RESULTS_T1.md \
		--t2 $(PROCESSED)/results/t2.json

t2:
	$(PY) -m blindspot.t2 --hotspots $(PROCESSED)/hotspots --mask-dir $(PROCESSED) \
		--regions $(PROCESSED)/regions --harmonized $(PROCESSED)/harmonized \
		--t1 $(PROCESSED)/results/t1.json --out $(PROCESSED)/results/t2.json
	$(PY) -m blindspot.report_t2 --json $(PROCESSED)/results/t2.json --md docs/RESULTS_T2.md
	$(PY) -m blindspot.report_t1 --json $(PROCESSED)/results/t1.json --md docs/RESULTS_T1.md \
		--t2 $(PROCESSED)/results/t2.json

t3:
	$(PY) -m blindspot.t3 --hotspots $(PROCESSED)/hotspots --mask-dir $(PROCESSED) \
		--regions $(PROCESSED)/regions --harmonized $(PROCESSED)/harmonized \
		--t1 $(PROCESSED)/results/t1.json --out $(PROCESSED)/results/t3.json --md docs/RESULTS_T3.md
	$(PY) -m blindspot.pitch --t1 $(PROCESSED)/results/t1.json \
		--t2 $(PROCESSED)/results/t2.json --t3 $(PROCESSED)/results/t3.json --plan docs/PLAN.md

appdata:
	$(PY) -m blindspot.appdata --processed $(PROCESSED) --boundaries $(BOUNDARIES) \
		--out web/public/data

test: lint
	$(PY) -m pytest

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

format:
	$(VENV)/bin/ruff format .
	$(VENV)/bin/ruff check --fix .

clean-processed:
	rm -rf $(PROCESSED)/hotspots $(PROCESSED)/persistent_mask_cells.parquet \
		$(PROCESSED)/mask_report.json $(PROCESSED)/qc_report.json \
		$(PROCESSED)/mask_comparison.json $(PROCESSED)/regions $(PROCESSED)/harmonized \
		$(PROCESSED)/results/t1.json $(PROCESSED)/results/t2.json

# Web app (D-036, D-037). web: install + build the static export and serve it locally.
web:
	cd web && npm install --no-audit --no-fund && npm run build && npm run serve

# Build, serve on :4173, run the Playwright e2e checks (screenshots -> docs/screenshots/),
# then cross-check the browser's custom-AOI series against Python.
web-test:
	cd web && npm install --no-audit --no-fund && npm run lint && npm run typecheck && npm test && npm run build
	cd web && (PORT=4173 node scripts/serve.mjs --headers & echo $$! > .serve.pid); sleep 1; \
	  node e2e/run.mjs; st=$$?; kill $$(cat .serve.pid); rm -f .serve.pid; exit $$st
	$(PY) web/e2e/check_custom_aoi.py

# Deploy rehearsal (D-041, docs/DEPLOY.md): build the export (writes out/_headers + CSP meta and
# checks Cloudflare limits), serve it on :4173 with those headers, check headers, run e2e. Local only.
deploy-rehearsal:
	cd web && npm run build
	cd web && (PORT=4173 node scripts/serve.mjs --headers & echo $$! > .serve.pid); sleep 1; \
	  curl -sI http://localhost:4173/ | grep -iE 'content-security|x-content-type|referrer-policy|permissions-policy|x-frame'; \
	  BASE=http://localhost:4173 node e2e/run.mjs; st=$$?; kill $$(cat .serve.pid); rm -f .serve.pid; exit $$st

# Submission text and video script from results JSON (no hand-typed numbers).
story:
	$(PY) -m blindspot.story
