"""Fill the pitch sentence in docs/PLAN.md §2 from t1.json and t2.json (CLAUDE.md rule 7).
The text between the pitch markers is replaced; every number is read from the JSON. The
"moved later" clause is used only when T3 (D-039) finds T = supported for IN Punjab; without
t3.json, or otherwise, the default clause states the correction and the comparability flags.
The D-034 `moved_later` evidence is still computed and listed, but no longer gates a clause.

    python -m blindspot.pitch --t1 data/processed/results/t1.json \
        --t2 data/processed/results/t2.json --t3 data/processed/results/t3.json --plan docs/PLAN.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

START, END = "<!-- pitch:start -->", "<!-- pitch:end -->"
MAX_WORDS = 55  # D-047 (was 45): room for the season and the harmonized numbers
PK, IN, CTRL = "PK_Punjab", "IN_Punjab", "rest_of_box"
CALIB = [str(y) for y in range(2012, 2022)]
TEST = [str(y) for y in range(2022, 2026)]


def _p(x: float) -> str:
    return f"{x * 100:+.0f}%"


def _p1(x: float) -> str:
    return f"{x * 100:+.1f}%"


def moved_later(t2: dict) -> dict:
    """Evidence for 'IN Punjab burning moved later' (D-034). All three must hold."""
    ns = t2["t2b"][IN]["night_share"]["SNPP"]
    pre = [ns[y]["share"] for y in CALIB if y in ns and ns[y]["share"] is not None]
    post = [ns[y]["share"] for y in TEST if y in ns and ns[y]["share"] is not None]
    night = bool(pre and post and sum(post) / len(post) > max(pre))

    def close(era: str) -> float:
        b = [
            x
            for x in t2["t2"][IN]["delta_bins"]
            if x["era"] == era
            and x["bin_lo_h"] is not None
            and x["bin_hi_h"] is not None
            and x["bin_lo_h"] >= -0.5
            and x["bin_hi_h"] <= 0.5
        ]
        return sum(x["ratio"] * x["n_days"] for x in b) / sum(x["n_days"] for x in b)

    close_rise = bool(close("2022-2025") > close("2012-2021"))
    control_flat = not t2["t2"][CTRL]["all_common_days"]["pi_test"]["outside"]
    return {
        "night_share_rise": night,
        "close_bin_ratio_rise": close_rise,
        "control_flat": control_flat,
        "supported": night and close_rise and control_flat,
    }


def t3_clause(t3: dict | None) -> dict:
    """Which middle clause the T3 verdicts allow (D-039)."""
    if not t3:
        return {"T": None, "D": None, "clause": "default"}
    ev = t3["t3"][IN]["evidence"]
    t, d = ev["T"]["verdict"], ev["D"]["verdict"]
    return {"T": t, "D": d, "clause": "later" if t == "supported" else "default"}


def sentence(t1: dict, t2: dict, t3: dict | None = None) -> str:
    def step(r: str) -> float:
        return t1["results"]["hotspots"][r]["step_2012"]["raw_step"]

    ev = moved_later(t2)
    removed = all(t2["t1_reevaluated"][r]["step_pass"] for r in (PK, IN))
    lead = "Blind Spot shows when this month's burning is unusual for any district."

    def harmonized(r: str) -> float | None:
        return t1["results"]["hotspots"][r]["step_2012"].get("harmonized_step")

    h_pk, h_in = harmonized(PK), harmonized(IN)
    first = (
        "In Punjab's October–November season the raw fire record jumps "
        f"{_p(step(PK))} (Pakistan) and {_p(step(IN))} (India) in 2012, "
        "when MODIS gives way to VIIRS"
        + (
            f"; harmonized, {_p1(h_pk)} and {_p1(h_in)}."
            if removed and h_pk is not None and h_in is not None
            else "."
        )
    )
    g = t3_clause(t3)
    if g["clause"] == "later":
        mid = (
            "Since 2022, some Indian Punjab burning moved past afternoon satellites; those "
            "years are flagged."
            if g["D"] != "supported"
            else "Since 2022, Indian Punjab burning fell and moved later; those years are flagged."
        )
    else:
        mid = "It also flags the years where the record stops being comparable."
    s = f"{lead} {first} {mid}"
    n = len(s.split())
    if n > MAX_WORDS:
        raise ValueError(f"pitch has {n} words > {MAX_WORDS}")
    keys = (
        "<sub>Numbers: `t1.json` results.hotspots.{PK,IN}_Punjab.step_2012."
        "{raw_step,harmonized_step}. "
        "'Removes that jump': `t2.json` t1_reevaluated.{PK,IN}_Punjab.step_pass. "
        "'Moved later' clause needs `t3.json` t3.IN_Punjab.evidence.T.verdict == supported "
        "(D-039); this run: "
        + ", ".join(f"{k}={v}" for k, v in g.items())
        + ". D-034 evidence (no longer a gate): "
        + ", ".join(f"{k}={v}" for k, v in ev.items())
        + f". {n} words. Filled by `python -m blindspot.pitch` (`make t3`).</sub>"
    )
    return f'> "{s}"\n\n{keys}'


def fill(plan: str, text: str) -> str:
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pat.search(plan):
        raise ValueError("pitch markers not found")
    return pat.sub(lambda _m: f"{START}\n{text}\n{END}", plan)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--t1", type=Path, default=Path("data/processed/results/t1.json"))
    p.add_argument("--t2", type=Path, default=Path("data/processed/results/t2.json"))
    p.add_argument("--t3", type=Path, default=None)
    p.add_argument("--plan", type=Path, default=Path("docs/PLAN.md"))
    a = p.parse_args(argv)
    t3 = json.loads(a.t3.read_text()) if a.t3 else None
    t = sentence(json.loads(a.t1.read_text()), json.loads(a.t2.read_text()), t3)
    a.plan.write_text(fill(a.plan.read_text(), t))
    print(t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
