"""Render docs/RESULTS_T2.md from data/processed/results/t2.json. Every figure is read from
the JSON (CLAUDE.md rule 7).

    python -m blindspot.report_t2 --json data/processed/results/t2.json --md docs/RESULTS_T2.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from blindspot.report_t1 import LABEL

PLATS = ("Aqua", "Terra", "SNPP", "NOAA20")


def _bin_label(lo: float | None, hi: float | None) -> str:
    """Δ bin label; None edges are open-ended (t2.json writes null, D-038)."""
    a = "(−∞" if lo is None else f"({lo:g}"
    b = "∞)" if hi is None else f"{hi:g}]"
    return f"{a}, {b}"


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:+.1f}%"


def _f(x: float | None, nd: int = 3) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def _hm(h: float | None) -> str:
    if h is None:
        return "n/a"
    m = round(h * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def _region(r: str, t: dict, b: dict, control: bool = False) -> list[str]:
    m, a, e = t["matched"], t["all_common_days"], t["aqua_drift_effect"]
    pi, ts, md = m["pi_test"], m["theil_sen"], t["min_detectable_drift"]
    adj = t["overpass_adjusted_pi_test_descriptive"]
    rv, ev = t["verdict_revised"], t["evaluable_test_years"]
    head = "control, post hoc (D-034); no pre-registered verdict" if control else ""
    rvt = ""
    if rv["pi_test"]:
        rp, rt = rv["pi_test"], rv["theil_sen"]
        rvt = (
            f" Evaluable test years {', '.join(map(str, rv['evaluable_test_years']))}: "
            f"interval {_f(rp['pi_ratio'][0])}–{_f(rp['pi_ratio'][1])}, observed mean "
            f"{_f(rp['test_mean_ratio'])} ({'outside' if rp['outside'] else 'inside'}); "
            f"Theil–Sen {_pct(rt['slope_pct_per_year'])}/yr, 95% CI "
            f"{_pct(rt['ci95_pct_per_year'][0])} to {_pct(rt['ci95_pct_per_year'][1])}."
        )
    out = [
        f"## {LABEL.get(r, r)}" + (f" ({head})" if control else ""),
        "",
        f"**T2 verdict, revised (D-034): {rv['label']}.**{rvt}",
        "",
        f"T2 verdict, original (D-033): {t['verdict']['label']} (prediction-interval rule: "
        f"{'outside' if pi['outside'] else 'inside'}; Theil–Sen CI "
        f"{'excludes' if ts['excludes_zero'] else 'includes'} 0).",
        "",
        "Test-year evaluability (D-034): "
        + "; ".join(
            f"{y} {'ok' if v['evaluable'] else 'insufficient (' + v['reason'] + ')'}"
            for y, v in ev.items()
        )
        + ".",
        "",
        f"- Matched days (|Δ| ≤ {m['tolerance_h'] * 60:.0f} min): 2012–2021 95% prediction "
        f"interval for the 2022–2025 mean ratio {_f(pi['pi_ratio'][0])}–{_f(pi['pi_ratio'][1])}; "
        f"observed mean {_f(pi['test_mean_ratio'])} ({_pct(pi['test_vs_base_pct'])} vs "
        "2012–2021).",
        f"- Theil–Sen slope 2012–2025 (matched): {_pct(ts['slope_pct_per_year'])}/yr, 95% CI "
        f"{_pct(ts['ci95_pct_per_year'][0])} to {_pct(ts['ci95_pct_per_year'][1])}.",
        "- All common days (not a verdict): 2022–2025 mean "
        f"{_pct(a['pi_test']['test_vs_base_pct'])}"
        f" vs 2012–2021, {'outside' if a['pi_test']['outside'] else 'inside'} the interval; "
        f"Theil–Sen {_pct(a['theil_sen']['slope_pct_per_year'])}/yr "
        f"({_pct(a['theil_sen']['ci95_pct_per_year'][0])} to "
        f"{_pct(a['theil_sen']['ci95_pct_per_year'][1])}).",
        f"- **Aqua-drift effect:** {_pct(e['effect_pct_per_hour'])} per hour of Δ(Aqua − S-NPP), "
        f"95% CI {_pct(e['effect_ci95_pct_per_hour'][0])} to "
        f"{_pct(e['effect_ci95_pct_per_hour'][1])} (p = {e['slope_p']:.2g}).",
        f"- Overpass-adjusted ratio (descriptive only; circular because b is fit on all years "
        f"and absorbs any post-2022 change, D-034): 2022–2025 mean "
        f"{_pct(adj['test_vs_base_pct'])} vs 2012–2021. Not used in any verdict.",
        f"- Minimum detectable drift (α = {md['alpha']}, power {md['power']}, "
        f"{md['k']} test years): {_pct(md['pct'])}.",
        "",
        "| Year | Matched days | Aqua/S-NPP matched | Δ median, matched days (h) | "
        "All-days ratio | Δ median, all days (h) | Implied drift effect |",
        "|---|---|---|---|---|---|---|",
    ]
    for y, v in a["by_year"].items():
        mv = m["by_year"].get(y)
        flag = " (insufficient)" if y in ev and not ev[y]["evaluable"] else ""
        out.append(
            f"| {y}{flag} | {mv['n_days'] if mv else 0} | {_f(mv['ratio']) if mv else 'n/a'} | "
            f"{_f(mv['delta_sample_median_h'], 2) if mv else 'n/a'} | "
            f"{_f(v['ratio'])} | {_f(v['delta_h'], 2)} | "
            f"{_pct(e['implied_effect_by_year'].get(y))} |"
        )
    out += [
        "",
        "Ratio Aqua/S-NPP by Δ(Aqua − S-NPP) bin, days on which both see daytime fire:",
        "",
        "| Δ bin (h) | 2012–2021 ratio (days) | 2022–2025 ratio (days) |",
        "|---|---|---|",
    ]
    bins: dict = {}
    for x in t["delta_bins"]:
        bins.setdefault((x["bin_lo_h"], x["bin_hi_h"]), {})[x["era"]] = x
    for (lo, hi), d in sorted(
        bins.items(), key=lambda kv: -math.inf if kv[0][0] is None else kv[0][0]
    ):
        cells = [
            f"{_f(d[k]['ratio'])} ({d[k]['n_days']})" if k in d else "n/a"
            for k in ("2012-2021", "2022-2025")
        ]
        out.append(f"| {_bin_label(lo, hi)} | {cells[0]} | {cells[1]} |")
    out += [
        "",
        "### T2b (consistency only, never proof)",
        "",
        "Median local solar time of daytime detections (empirical overpass, D-033):",
        "",
        "| Year | " + " | ".join(PLATS) + " | S-NPP night share | NOAA-20 night share | "
        "Terra/Aqua | Terra/Aqua corrected |",
        "|---|" + "---|" * (len(PLATS) + 4),
    ]
    ns, op, ta = b["night_share"], b["overpass_h"], b["terra_aqua"]
    for y in sorted(ta, key=int):
        cells = [_hm(op[p].get(y, {}).get("median_h")) for p in PLATS]

        def share(p: str, yy: str = y) -> str:
            v = ns[p].get(yy)
            return _pct(v["share"])[1:] if v and v["share"] is not None else "n/a"

        corr = _f(ta[y]["ratio_corrected"]) if ta[y]["corrected"] else "—"
        if ta[y]["corrected"] and int(y) >= 2023:
            corr = f"_({corr})_"
        out.append(
            f"| {y} | " + " | ".join(cells) + f" | {share('SNPP')} | {share('NOAA20')} | "
            f"{_f(ta[y]['ratio'])} | {corr} |"
        )
    out += [
        "",
        f"Correction: {b['correction']}. Terra drifts earlier while Aqua drifts later, so "
        "Terra/Aqua cannot separate orbit from burning behaviour; corrected values from 2023 "
        "(in parentheses) are not interpretable.",
        "",
    ]
    return out


def render(j: dict) -> str:
    prov = j["provenance"]
    src = j["crossing_time_source"]
    out = [
        "# T2 / T2b results",
        "",
        f"Generated by `python -m blindspot.report_t2` from `data/processed/results/t2.json` "
        f"({j['generated']}). Do not edit by hand. Definitions: `docs/DECISIONS.md` D-033. "
        "Which explanation fits (orbit, timing, decline): `docs/RESULTS_T3.md` (D-039).",
        "",
        f"- Window {j['window']['start']} to {j['window']['end']} ({j['window']['time_basis']}); "
        f"daytime detections; regions {', '.join(LABEL.get(r, r) for r in j['regions'])}.",
        f"- Crossing times: official per-year table found: "
        f"{'yes' if src['official_per_year_table'] else 'no'}; used {src['used']}. "
        f"NASA milestones: {', '.join(src['official_milestones'])}.",
        f"- Code commit `{prov['code']['commit']}`"
        + (" (pipeline code had uncommitted changes)" if prov["code"]["code_dirty"] else "")
        + ".",
        "",
        "## Verdicts",
        "",
        f"Revised verdict (D-034, post-data): a test year needs ≥ "
        f"{j['parameters']['min_matched_days_d034']} matched days and an all-days median Δ "
        f"within tolerance; fewer than {j['parameters']['min_evaluable_test_years_d034']} "
        "such years → inconclusive. The original D-033 verdict is shown beside it.",
        "",
        "| Region | T2 original (D-033) | T2 revised (D-034) | T1 (revised) | T1 under D-033 |",
        "|---|---|---|---|---|",
    ]
    for r in j["regions"]:
        t1, t0 = j["t1_reevaluated"][r], j["t1_reevaluated_d033"][r]
        out.append(
            f"| {LABEL.get(r, r)} | {j['verdict_t2'][r]['label']} | "
            f"{j['verdict_t2_revised'][r]['label']} | {t1['label']} | {t0['label']} |"
        )
    c = j["control_region"]
    out.append(
        f"| {LABEL.get(c, c)} (control) | {j['t2'][c]['verdict']['label']} | "
        f"{j['t2'][c]['verdict_revised']['label']} | — | — |"
    )
    out += ["", f"_{j['control_note']}._", ""]
    for r in j["regions"]:
        out += _region(r, j["t2"][r], j["t2b"][r])
    out += _region(c, j["t2"][c], j["t2b"][c], control=True)
    mr = j["mask_report"]
    out += [
        "## Mask report",
        "",
        f"{mr['n_masked_cells']} masked cells. Share removed, all detections: "
        + ", ".join(f"{k} {_pct(v)[1:]}" for k, v in mr["share_removed_by_platform_all"].items())
        + ".",
        "",
        "| Region | Platform | Window detections | Removed | Share |",
        "|---|---|---|---|---|",
    ]
    for r, by in mr["window_by_region"].items():
        for p in sorted(by):
            v = by[p]
            out.append(
                f"| {LABEL.get(r, r)} | {p} | {v['detections']:,} | {v['removed']:,} | "
                f"{v['share_removed'] * 100:.2f}% |"
            )
    out += ["", "## Inputs", "", "| Input | sha256 | Files |", "|---|---|---|"]
    for k, v in prov["inputs"].items():
        out.append(f"| {k} | `{(v.get('sha256') or 'missing')[:16]}` | {v.get('n_files', 0)} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--json", type=Path, default=Path("data/processed/results/t2.json"))
    p.add_argument("--md", type=Path, default=Path("docs/RESULTS_T2.md"))
    a = p.parse_args(argv)
    a.md.write_text(render(json.loads(a.json.read_text())))
    print(f"-> {a.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
