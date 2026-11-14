"""Old vs new persistent-hotspot mask rule (docs/DECISIONS.md D-024, CLAUDE.md rule 6).

Builds both masks on the same `hotspots_filtered` view and reports, per rule: share removed
per platform (all years; and 2012–2021 for Aqua vs S-NPP, D-022's revisit check), share of
S-NPP removed by local solar month over the whole box, share removed per platform in the
Punjab core box in Oct–Nov, the number of masked cells, and the 10 masked cells with most
detections (coordinates only, for an imagery check). A sensitivity row gives the lead's draft
rule (>= 4 months, one 3-month window) without adopting it.

Every number is computed here from the data on disk; nothing is typed in.

    python -m blindspot.mask_compare --hotspots data/processed/hotspots \\
        --json data/processed/mask_comparison.json --md docs/MASK_COMPARISON.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import duckdb

from blindspot import mask

# Punjab core box (edges inclusive), months by local solar time.
PUNJAB_CORE = {"lon_min": 71.0, "lon_max": 77.0, "lat_min": 29.5, "lat_max": 32.6}
PUNJAB_MONTHS = (10, 11)
TOP_N = 10

RULES = {
    "old": {"rule": mask.RULE_SEASONAL_OFFSEASON},
    "new": {"rule": mask.RULE_YEAR_ROUND},
}
SENSITIVITY = {"draft_one_window": {"rule": mask.RULE_YEAR_ROUND, "max_seasons": 1}}


def _share(removed: int, total: int) -> float | None:
    return removed / total if total else None


def _rule_metrics(con: duckdb.DuckDBPyConnection, kwargs: dict, full: bool) -> dict:
    result = mask.build_mask(con, **kwargs)
    mask.apply_mask(con, result)
    out: dict = {
        "parameters": result.parameters(),
        "n_masked_cells": int(len(result.cells)),
        "overall": {
            p: {"total": result.total[p], "removed": result.removed[p], "share": s}
            for p, s in result.share_removed.items()
        },
    }
    if not full:
        return out
    rows = con.execute(
        """
        SELECT platform, count(*), count(*) FILTER (WHERE in_persistent_mask)
        FROM hotspots_masked_flags
        WHERE year(local_solar_datetime) BETWEEN 2012 AND 2021
          AND platform IN ('Aqua', 'SNPP')
        GROUP BY platform ORDER BY platform
        """
    ).fetchall()
    out["calibration_years_2012_2021"] = {
        p: {"total": t, "removed": r, "share": _share(r, t)} for p, t, r in rows
    }
    rows = con.execute(
        """
        SELECT month(local_solar_datetime) AS m, count(*),
               count(*) FILTER (WHERE in_persistent_mask)
        FROM hotspots_masked_flags WHERE platform = 'SNPP'
        GROUP BY m ORDER BY m
        """
    ).fetchall()
    out["snpp_by_month"] = {
        int(m): {"total": t, "removed": r, "share": _share(r, t)} for m, t, r in rows
    }
    rows = con.execute(
        """
        SELECT platform, count(*), count(*) FILTER (WHERE in_persistent_mask)
        FROM hotspots_masked_flags
        WHERE lon BETWEEN $lon_min AND $lon_max AND lat BETWEEN $lat_min AND $lat_max
          AND list_contains($months, month(local_solar_datetime))
        GROUP BY platform ORDER BY platform
        """,
        {**PUNJAB_CORE, "months": list(PUNJAB_MONTHS)},
    ).fetchall()
    out["punjab_core_oct_nov"] = {
        p: {"total": t, "removed": r, "share": _share(r, t)} for p, t, r in rows
    }
    out["top_cells"] = _top_cells(con, result)
    return out


def _top_cells(con: duckdb.DuckDBPyConnection, result: mask.MaskResult) -> list[dict]:
    grid = float(result.grid_deg)
    qualifying = result.cells[["cell_lat", "cell_lon", "years"]].copy()
    qualifying["years"] = qualifying["years"].apply(lambda ys: [int(y) for y in ys])
    con.register("_qual_years", qualifying)
    rows = con.execute(
        """
        WITH c AS (
            SELECT CAST(floor(lat / $grid + $eps) AS BIGINT) AS cell_lat,
                   CAST(floor(lon / $grid + $eps) AS BIGINT) AS cell_lon,
                   platform, year(local_solar_datetime) AS y,
                   month(local_solar_datetime) AS m
            FROM hotspots_masked_flags WHERE in_persistent_mask
        )
        SELECT c.cell_lat, c.cell_lon, count(*) AS n,
               list_sort(list_distinct(list(c.m))) AS months_all_years,
               list_sort(list_distinct(list(c.y))) AS years_with_detections,
               any_value(q.years) AS qualifying_years,
               count(*) FILTER (WHERE platform = 'Aqua') AS n_aqua,
               count(*) FILTER (WHERE platform = 'Terra') AS n_terra,
               count(*) FILTER (WHERE platform = 'SNPP') AS n_snpp,
               count(*) FILTER (WHERE platform = 'NOAA20') AS n_noaa20
        FROM c JOIN _qual_years q USING (cell_lat, cell_lon)
        GROUP BY c.cell_lat, c.cell_lon
        ORDER BY n DESC, c.cell_lat, c.cell_lon
        LIMIT $top
        """,
        {"grid": grid, "eps": mask._EPS, "top": TOP_N},
    ).fetchall()
    con.unregister("_qual_years")
    out = []
    for cl, cn, n, months, years, qyears, na, nt, ns, n20 in rows:
        out.append(
            {
                "cell_lat": int(cl),
                "cell_lon": int(cn),
                "centre_lat": round((cl + 0.5) * grid, 4),
                "centre_lon": round((cn + 0.5) * grid, 4),
                "n_detections": int(n),
                "by_platform": {"Aqua": na, "Terra": nt, "SNPP": ns, "NOAA20": n20},
                "months_all_years": [int(m) for m in months],
                "years_with_detections": [int(y) for y in years],
                "qualifying_years": [int(y) for y in qyears],
            }
        )
    return out


def compare(con: duckdb.DuckDBPyConnection) -> dict:
    report = {
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "time_basis": "local_solar_datetime",
        "punjab_core_box": PUNJAB_CORE,
        "punjab_core_months": list(PUNJAB_MONTHS),
        "rules": {name: _rule_metrics(con, kw, full=True) for name, kw in RULES.items()},
        "sensitivity": {
            name: _rule_metrics(con, kw, full=False) for name, kw in SENSITIVITY.items()
        },
    }
    return report


def _pct(v: float | None) -> str:
    return "–" if v is None else f"{v:.2%}"


def _ranges(xs: list[int]) -> str:
    out: list[str] = []
    for x in xs:
        if out and out[-1].split("–")[-1] == str(x - 1):
            out[-1] = out[-1].split("–")[0] + f"–{x}"
        else:
            out.append(str(x))
    return ", ".join(out)


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def render_markdown(rep: dict) -> str:
    old, new = rep["rules"]["old"], rep["rules"]["new"]
    platforms = sorted(set(old["overall"]) | set(new["overall"]))
    box = rep["punjab_core_box"]
    lines = [
        "# Persistent-hotspot mask: old vs new rule",
        "",
        f"Generated by `python -m blindspot.mask_compare` at {rep['generated_at_utc']} from "
        "`hotspots_filtered` (standard data, type 0, confidence, coverage box, no duplicates). "
        "Do not edit by hand. Months and years are local solar time. Platforms are never "
        "summed. Every detection in a masked cell (all years, all platforms) counts as removed.",
        "",
        "- **Old** (`--rule seasonal-offseason`, D-022, superseded): cell has a detection in "
        "≥3 distinct years during Jan–Mar or Jul–Sep.",
        "- **New** (`--rule year-round`, default, D-024): in ≥3 distinct years the cell has "
        "detections in ≥4 distinct months that no two 3-month windows (wrapping Dec→Jan) can "
        "cover.",
        "",
        "The rule was changed after the old rule's results were seen (CLAUDE.md rule 6); "
        "both are reported here.",
        "",
        "## Masked cells (0.01° grid)",
        "",
        "| Rule | Masked cells |",
        "|---|---|",
        f"| Old | {old['n_masked_cells']} |",
        f"| New | {new['n_masked_cells']} |",
        "",
        "## Share removed per platform, whole box, all years",
        "",
        "| Platform | Detections | Old removed | Old % | New removed | New % |",
        "|---|---|---|---|---|---|",
    ]
    for p in platforms:
        o, n = old["overall"][p], new["overall"][p]
        lines.append(
            f"| {p} | {o['total']} | {o['removed']} | {_pct(o['share'])} | "
            f"{n['removed']} | {_pct(n['share'])} |"
        )
    lines += [
        "",
        "Calibration years 2012–2021 only (D-022 revisit check: Aqua vs S-NPP):",
        "",
        "| Platform | Detections | Old % | New % |",
        "|---|---|---|---|",
    ]
    for p in sorted(new["calibration_years_2012_2021"]):
        o, n = old["calibration_years_2012_2021"][p], new["calibration_years_2012_2021"][p]
        lines.append(f"| {p} | {o['total']} | {_pct(o['share'])} | {_pct(n['share'])} |")
    lines += [
        "",
        "## S-NPP share removed by month, whole box, all years",
        "",
        "| Month | Detections | Old removed | Old % | New removed | New % |",
        "|---|---|---|---|---|---|",
    ]
    for m in sorted(new["snpp_by_month"], key=int):
        o, n = old["snpp_by_month"][m], new["snpp_by_month"][m]
        lines.append(
            f"| {_MONTHS[int(m) - 1]} | {o['total']} | {o['removed']} | {_pct(o['share'])} | "
            f"{n['removed']} | {_pct(n['share'])} |"
        )
    lines += [
        "",
        f"## Punjab core ({box['lon_min']}–{box['lon_max']}°E, "
        f"{box['lat_min']}–{box['lat_max']}°N, edges inclusive), Oct–Nov, all years",
        "",
        "| Platform | Detections | Old removed | Old % | New removed | New % |",
        "|---|---|---|---|---|---|",
    ]
    for p in sorted(new["punjab_core_oct_nov"]):
        o, n = old["punjab_core_oct_nov"][p], new["punjab_core_oct_nov"][p]
        lines.append(
            f"| {p} | {o['total']} | {o['removed']} | {_pct(o['share'])} | "
            f"{n['removed']} | {_pct(n['share'])} |"
        )
    for name, label in (("new", "New"), ("old", "Old")):
        lines += [
            "",
            f"## Sanity check: 10 masked cells with most detections, {label.lower()} rule",
            "",
            "Coordinates only, for a human to check on satellite imagery. What these cells "
            "are has not been verified. Centre = cell centre; the cell spans ±0.005°. "
            "Months = distinct months with a detection in any year; qualifying years = years "
            "that meet the rule.",
            "",
            "| # | Centre lat | Centre lon | Detections | Aqua / Terra / S-NPP / NOAA-20 | "
            "Months (all years) | Years with detections | Qualifying years |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for i, c in enumerate(rep["rules"][name]["top_cells"], 1):
            bp = c["by_platform"]
            lines.append(
                f"| {i} | {c['centre_lat']:.3f} | {c['centre_lon']:.3f} | {c['n_detections']} | "
                f"{bp['Aqua']} / {bp['Terra']} / {bp['SNPP']} / {bp['NOAA20']} | "
                f"{_ranges(c['months_all_years'])} | {_ranges(c['years_with_detections'])} | "
                f"{_ranges(c['qualifying_years'])} |"
            )
    s = rep["sensitivity"]["draft_one_window"]
    lines += [
        "",
        "## Sensitivity (not adopted): draft rule",
        "",
        "The lead's draft (≥4 months in a year, not all within one 3-month window; same as "
        "`--max-seasons 1`). Shown only so the effect of the two-window refinement is visible.",
        "",
        f"Masked cells: {s['n_masked_cells']}.",
        "",
        "| Platform | Removed | % |",
        "|---|---|---|",
    ]
    for p in sorted(s["overall"]):
        lines.append(f"| {p} | {s['overall'][p]['removed']} | {_pct(s['overall'][p]['share'])} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    from blindspot import ingest

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument("--json", type=Path, default=Path("data/processed/mask_comparison.json"))
    p.add_argument("--md", type=Path, default=Path("docs/MASK_COMPARISON.md"))
    args = p.parse_args(argv)
    rep = compare(ingest.connect(args.hotspots))
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(rep, indent=2))
    args.md.write_text(render_markdown(rep))
    print(f"mask comparison -> {args.json} and {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
