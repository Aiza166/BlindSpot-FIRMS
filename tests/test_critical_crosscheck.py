"""D-043: the browser's drawn-area critical-period code (web/lib/criticalCalc.ts) must equal the
pipeline reference (appdata.critical_periods) on the same series.

The fixture holds the harmonized series (1-decimal, as shipped), baseline and caution years of two
real districts plus a synthetic wrap-around case, and the Python output for them. The vitest file
web/lib/criticalCalc.test.ts feeds the same inputs to the TypeScript function.
Tolerance: months/onset/peak/end/other_months/n_years/excluded_years exactly; typical values and
threshold within 0.1 (one-decimal rounding: Python round() is half-to-even, JS Math.round half-up).

Regenerate (needs `make appdata` output):
    BLINDSPOT_REGEN_FIXTURE=1 pytest tests/test_critical_crosscheck.py
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from blindspot import appdata as ad

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/critical_crosscheck.json"
DATA = ROOT / "web/public/data"
DISTRICTS = {"Sangrur": "76128533B82601690264832", "Kasur": "60131773B44072502651200"}


def _frame(case: dict) -> pd.DataFrame:
    rows = []
    for k, v, p in zip(case["months"], case["value"], case["partial"], strict=True):
        if v is None:
            continue
        y, m = k.split("-")
        rows.append({"year": int(y), "month": int(m), "value": v, "partial": bool(p)})
    return pd.DataFrame(rows)


def python_output(case: dict) -> dict:
    last = tuple(int(x) for x in case["months"][-1].split("-"))
    first_year = case["baseline"][0]
    med, crit = ad.critical_periods(_frame(case), case["caution_years"], last, first_year)
    return {"median_excl_flagged": med, "critical": crit}


def _district_case(name: str, doc: dict) -> dict:
    return {
        "name": name,
        "months": ad_months(doc),
        "value": doc["harmonized"]["value"],
        "partial": doc["harmonized"]["partial"],
        "baseline": doc["median"]["harmonized"]["baseline_years"],
        "caution_years": sorted(int(y) for y in doc["reliability"]["caution_years"]),
    }


def ad_months(doc: dict) -> list[str]:
    fy, fm = (int(x) for x in doc["period"]["first"].split("-"))
    ly, lm = (int(x) for x in doc["period"]["last"].split("-"))
    return [ad.ym(y, m) for y, m in ad.month_range((fy, fm), (ly, lm))]


def _synthetic() -> dict:
    months, value = [], []
    for y in range(2003, 2011):
        for m in range(1, 13):
            months.append(ad.ym(y, m))
            value.append({12: 80.0, 1: 70.0, 5: 60.0}.get(m, 1.0) * (10.0 if y == 2007 else 1.0))
    return {
        "name": "synthetic_wrap",
        "months": months,
        "value": value,
        "partial": [False] * len(months),
        "baseline": [2003, 2010],
        "caution_years": [2007],
    }


def test_regenerate_fixture_when_asked():
    if not os.environ.get("BLINDSPOT_REGEN_FIXTURE"):
        pytest.skip("set BLINDSPOT_REGEN_FIXTURE=1 to rebuild from web/public/data")
    cases = [
        _district_case(n, json.loads((DATA / "districts" / f"{i}.json").read_text()))
        for n, i in DISTRICTS.items()
    ] + [_synthetic()]
    for c in cases:
        c["expected"] = python_output(c)
    FIXTURE.write_text(json.dumps({"tolerance": 0.1, "cases": cases}, separators=(",", ":")))


def test_fixture_equals_python_reference():
    fx = json.loads(FIXTURE.read_text())
    assert [c["name"] for c in fx["cases"]][:2] == list(DISTRICTS)
    for c in fx["cases"]:
        assert python_output(c) == c["expected"], c["name"]


def test_fixture_cases_are_nontrivial():
    fx = json.loads(FIXTURE.read_text())
    for c in fx["cases"]:
        assert c["expected"]["critical"]["months"], c["name"]
        assert c["caution_years"], c["name"]
        assert c["expected"]["critical"]["this_year"] is not None, c["name"]


@pytest.mark.skipif(not (DATA / "districts").exists(), reason="needs make appdata output")
def test_recomputing_from_shipped_rounded_series_matches_shipped_block():
    """Shipped blocks use unrounded series; from the rounded series they agree within 0.1."""
    fx = json.loads(FIXTURE.read_text())
    for c in fx["cases"][:2]:
        shipped = json.loads((DATA / "districts" / f"{DISTRICTS[c['name']]}.json").read_text())
        a, b = shipped["critical"], c["expected"]["critical"]
        assert a["months"] == b["months"] and (a["onset"], a["peak"], a["end"]) == (
            b["onset"],
            b["peak"],
            b["end"],
        )
        for x, y in zip(
            shipped["median_excl_flagged"]["values"],
            c["expected"]["median_excl_flagged"]["values"],
            strict=True,
        ):
            assert (x is None and y is None) or abs(x - y) <= 0.1
