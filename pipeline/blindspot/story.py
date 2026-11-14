"""Fill the submission and video templates from results JSON (CLAUDE.md rule 7).

A placeholder is ``{{source:dotted.path|format}}``; ``{{pitch}}`` inserts the pitch sentence
from blindspot.pitch. Every filled value is logged and, for Markdown outputs, listed in a
"Number sources" table at the end, so each number traces back to one JSON key.

    python -m blindspot.story          # same as `make story`
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from blindspot import pitch as pitch_mod

DATA = Path("web/public/data")
SOURCES: dict[str, Path] = {
    "t1": DATA / "results/t1.json",
    "t2": DATA / "results/t2.json",
    "t3": DATA / "results/t3.json",
    "mask": DATA / "results/mask_report.json",
    "calib": DATA / "results/calibration.json",
    "constants": DATA / "constants.json",
    "index": DATA / "index.json",
    "aoi": Path("web/e2e/artifacts/custom_aoi_check.json"),
    "axe": Path("docs/review/axe-after.json"),
}
USECASES: list[tuple[str, str, str]] = [  # (key, district name, country); web/app/use-case
    ("sangrur", "Sangrur", "IND"),
    ("kasur", "Kasur", "PAK"),
]
USECASE_MONTH = "2025-11"  # contrast example: a flagged year (D-042)
FLAGSHIP_CALENDAR_MONTH = 11  # November
FLAGSHIP_FROM_YEAR = 2012  # S-NPP era
TEAM_NAMES = "Aiza Gazyani and Kissa Zehra"  # replaces {NAMES} in templates
JOBS: list[tuple[Path, Path]] = [
    (Path("docs/templates/SUBMISSION.tmpl.md"), Path("docs/SUBMISSION.md")),
    (Path("docs/templates/VIDEO_SCRIPT.tmpl.md"), Path("docs/VIDEO_SCRIPT.md")),
    (Path("docs/templates/MORNING_SUMMARY.tmpl.md"), Path("docs/MORNING_SUMMARY.md")),
]
# Outputs whose "Number sources" table goes to a separate file (keeps the submission readable).
SOURCES_OUT: dict[Path, Path] = {Path("docs/SUBMISSION.md"): Path("docs/SUBMISSION_SOURCES.md")}
CHECKPOINTS = Path("docs/CHECKPOINTS.md")
SRT_OUT = Path("docs/video/subtitles.srt")
VO = re.compile(r"\|\s*(\d+):(\d\d)–(\d+):(\d\d)\s*\|.*?<!--vo-->(.*?)<!--/vo-->")
VO_FULL = "<!--vo-full-->"
MAX_VO_WORDS = 55
PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
SOURCES_HEADING = "## Number sources"


def _signed_pct(x: float) -> str:
    return f"{x * 100:+.0f}%"


FORMATS: dict[str, Callable[[Any], str]] = {
    "raw": str,
    "int": lambda x: f"{round(float(x)):,}",
    "f3": lambda x: f"{float(x):.3f}",
    "f2": lambda x: f"{float(x):.2f}",
    "pct": _signed_pct,  # fraction -> signed percent, 0 dp
    "pct1": lambda x: f"{float(x) * 100:+.1f}%",
    "upct": lambda x: f"{float(x) * 100:.0f}%",  # fraction -> unsigned percent
    "upct1": lambda x: f"{float(x) * 100:.1f}%",
    "upct3": lambda x: f"{float(x) * 100:.3f}%",
    "cut": lambda x: f"{(1 - float(x)) * 100:.0f}%",  # share removed: 1 - ratio
    "len": lambda x: str(len(x)),
    "nviol": lambda x: str(sum(len(r["violations"]) for r in x)),  # axe runs -> total violations
    "year": lambda x: str(x)[:4],
    "month": lambda x: dt.datetime.strptime(str(x)[:7], "%Y-%m").strftime("%B %Y"),  # 2026-10
    "min": lambda x: f"{round(float(x) * 60)} minutes",
    "x2": lambda x: f"{float(x):.2f}×",
    "years": lambda x: _years(x),  # list, or dict keyed by year -> "2022–2025" or "2022, 2024"
    "caution": lambda x: _years(  # t3 reliability dict -> caution years
        [y for y, v in x.items() if v.get("harmonization_reliable") == "caution"]
    ),
    "first_caution": lambda x: min(
        y for y, v in x.items() if v.get("harmonization_reliable") == "caution"
    ),
}


def _years(x: Any) -> str:
    ys = sorted(int(y) for y in x)
    if not ys:
        return "none"
    if ys == list(range(ys[0], ys[-1] + 1)) and len(ys) > 2:
        return f"{ys[0]}–{ys[-1]}"
    return ", ".join(str(y) for y in ys)


def lookup(data: dict[str, Any], key: str) -> Any:
    """Resolve ``source:a.b.0.c``; integer parts index lists."""
    src, _, path = key.partition(":")
    if src not in data:
        raise KeyError(f"unknown source {src!r} in {key!r}")
    cur: Any = data[src]
    for part in path.split(".") if path else []:
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(f"{key!r}: no {part!r}")
    return cur


def checkpoint_table(md: str) -> str:
    """CP, gate, status and score columns of every checkpoint row in CHECKPOINTS.md."""
    rows = ["| CP | Gate | Status | Score |", "|---|---|---|---|"]
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"[A-Z]\d+", cells[0]):
            rows.append(f"| {cells[0]} | {cells[2]} | {cells[3]} | {cells[4] or '–'} |")
    return "\n".join(rows)


def render(
    template: str, data: dict[str, Any], pitch_text: str, checkpoints: str = ""
) -> tuple[str, list[tuple]]:
    """Return (filled text, log of (placeholder, value)). Raises on a bad placeholder."""
    log: list[tuple[str, str]] = []

    def sub(m: re.Match[str]) -> str:
        expr = m.group(1)
        if expr == "pitch":
            log.append(("pitch", "blindspot.pitch.sentence(t1, t2, t3)"))
            return pitch_text
        if expr == "checkpoints":
            table = checkpoint_table(checkpoints)
            log.append(("checkpoints", table))
            return table
        key, _, fmt = expr.partition("|")
        fmt = fmt or "raw"
        if fmt not in FORMATS:
            raise KeyError(f"unknown format {fmt!r} in {expr!r}")
        val = FORMATS[fmt](lookup(data, key))
        log.append((expr, val))
        return val

    out = PLACEHOLDER.sub(sub, template)
    if "{{" in out or "}}" in out:
        raise ValueError("unfilled placeholder left in output")
    return out, log


def sources_table(log: list[tuple[str, str]]) -> str:
    rows = ["| Placeholder (`source:json.path\\|format`) | Value |", "|---|---|"]
    seen: set[str] = set()
    for expr, val in log:
        if expr in seen or expr in ("pitch", "checkpoints"):
            continue
        seen.add(expr)
        rows.append(f"| `{expr.replace('|', chr(92) + '|')}` | {val} |")
    files = ", ".join(f"`{k}` = `{v.as_posix()}`" for k, v in SOURCES.items())
    return (
        f"\n\n{SOURCES_HEADING}\n\nGenerated by `make story` (pipeline/blindspot/story.py). "
        f"Do not edit by hand; edit the template. Sources: {files}. The pitch quote comes "
        "from `blindspot.pitch` (its own key list is in docs/PLAN.md §2).\n\n" + "\n".join(rows)
    )


def voice_over(text: str) -> list[tuple[int, int, str]]:
    """(start s, end s, line) for each shot-list row with a <!--vo--> cell."""
    return [
        (int(a) * 60 + int(b), int(c) * 60 + int(d), line.strip())
        for a, b, c, d, line in VO.findall(text)
    ]


def srt(lines: list[tuple[int, int, str]]) -> str:
    """One cue per sentence; a shot's time is split by word count (subtitle cues stay short)."""

    def ts(ms: int) -> str:
        return f"00:{ms // 60000:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    cues: list[tuple[int, int, str]] = []
    for a, b, line in lines:
        parts = [x for x in re.split(r"(?<=[.!?])\s+", line) if x]
        words = sum(len(x.split()) for x in parts)
        t = a * 1000
        for x in parts:
            end = t + round((b - a) * 1000 * len(x.split()) / words)
            cues.append((t, end, x))
            t = end
    return "\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{x}\n" for i, (a, b, x) in enumerate(cues, 1))


def add_voice_over(text: str) -> tuple[str, str | None]:
    """Fill <!--vo-full--> with the joined voice-over; return (text, srt or None)."""
    lines = voice_over(text)
    if not lines:
        return text, None
    full = " ".join(line for _, _, line in lines)
    n = len(full.split())
    if n > MAX_VO_WORDS:
        raise ValueError(f"voice-over has {n} words > {MAX_VO_WORDS}")
    text = text.replace(VO_FULL, f"> {full}\n\n{n} words, {lines[-1][1]} s.")
    return text.replace("<!--vo-->", "").replace("<!--/vo-->", ""), srt(lines)


def pitch_quote(data: dict[str, Any]) -> str:
    block = pitch_mod.sentence(data["t1"], data["t2"], data.get("t3"))
    return block.split("\n", 1)[0].removeprefix("> ").strip('"')


def _months_of(doc: dict[str, Any]) -> list[str]:
    first = doc["period"]["first"]
    y0, m0 = int(first[:4]), int(first[5:7])
    n = len(doc["harmonized"]["value"])
    return [f"{y0 + (m0 - 1 + k) // 12}-{(m0 - 1 + k) % 12 + 1:02d}" for k in range(n)]


def flagship_month(
    doc: dict[str, Any],
    cal_month: int = FLAGSHIP_CALENDAR_MONTH,
    from_year: int = FLAGSHIP_FROM_YEAR,
) -> tuple[str, int]:
    """D-042 rule: highest complete harmonized value of the calendar month since from_year, in a
    year not in the district's caution years. Ties: later year. Returns (ym, n)."""
    caution = {int(y) for y in (doc.get("reliability") or {}).get("caution_years", {})}
    h = doc["harmonized"]
    cands = [
        (h["value"][k], int(ym[:4]), ym)
        for k, ym in enumerate(_months_of(doc))
        if int(ym[5:7]) == cal_month
        and int(ym[:4]) >= from_year
        and int(ym[:4]) not in caution
        and h["partial"][k] is False
        and h["value"][k] is not None
    ]
    if not cands:
        raise ValueError("no eligible month")
    return max(cands)[2], len(cands)


def month_check(doc: dict[str, Any], ym: str) -> dict[str, Any]:
    """Same numbers as web/lib/usecase.ts checkMonth: one month of one district vs earlier years."""
    first = doc["period"]["first"]
    y0, m0 = int(first[:4]), int(first[5:7])
    n = len(doc["harmonized"]["value"])
    months = [f"{y0 + (m0 - 1 + k) // 12}-{(m0 - 1 + k) % 12 + 1:02d}" for k in range(n)]
    i = months.index(ym)
    y, m = int(ym[:4]), int(ym[5:7])
    h = doc["harmonized"]
    earlier = [
        (int(mm[:4]), h["value"][k])
        for k, mm in enumerate(months)
        if int(mm[5:7]) == m
        and int(mm[:4]) < y
        and h["partial"][k] is not True
        and h["value"][k] is not None
    ]
    v = h["value"][i]
    allv = sorted([e[1] for e in earlier] + [v])
    med = doc["median"]["harmonized"]["values"][m - 1]
    n20 = doc["raw"]["NOAA20"]["n"][i]
    n20med = doc["median"]["NOAA20"]["values"][m - 1]
    rel = doc.get("reliability") or {}
    reasons = rel.get("caution_years", {}).get(str(y), [])
    return {
        "ym": ym,
        "value": v,
        "median": med,
        "median_years": doc["median"]["harmonized"]["baseline_years"],
        "ratio": v / med if med else None,
        "rank_from_lowest": allv.index(v) + 1,
        "n_compared": len(allv),
        "min_earlier": min(earlier, key=lambda e: e[1])[1] if earlier else None,
        "min_earlier_year": min(earlier, key=lambda e: e[1])[0] if earlier else None,
        "noaa20": n20,
        "noaa20_median": n20med,
        "noaa20_years": doc["median"]["NOAA20"]["baseline_years"],
        "noaa20_ratio": n20 / n20med if n20 and n20med else None,
        "median_excl": doc["median_excl_flagged"]["values"][m - 1],
        "excluded_years": doc["median_excl_flagged"]["excluded_years"],
        "ratio_excl": v / doc["median_excl_flagged"]["values"][m - 1]
        if doc["median_excl_flagged"]["values"][m - 1]
        else None,
        "calib_region": rel.get("calib_region"),
        "caution": "caution" if reasons else "reliable",
        "reasons": ", ".join(reasons) or "none",
    }


def usecases(data_dir: Path, index: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"month": USECASE_MONTH}
    for key, name, country in USECASES:
        d = next(x for x in index["districts"] if x["name"] == name and x["country"] == country)
        doc = json.loads((data_dir / "districts" / f"{d['id']}.json").read_text())
        ym, n_eligible = flagship_month(doc)
        out[key] = {**month_check(doc, ym), "n_eligible": n_eligible}  # flagship, unflagged year
        out[f"{key}25"] = month_check(doc, USECASE_MONTH)  # contrast: flagged year
    return out


def load(sources: dict[str, Path] = SOURCES) -> dict[str, Any]:
    data = {k: json.loads(p.read_text()) for k, p in sources.items()}
    if "index" in data:
        data_dir = sources["index"].parent
        if (data_dir / "districts").is_dir():
            data["usecase"] = usecases(data_dir, data["index"])
    return data


def build(root: Path = Path("."), jobs: list[tuple[Path, Path]] = JOBS) -> list[Path]:
    data = load({k: root / p for k, p in SOURCES.items()})
    pq = pitch_quote(data)
    cps = (root / CHECKPOINTS).read_text()
    written = []
    for tmpl, out in jobs:
        text, log = render((root / tmpl).read_text().replace("{NAMES}", TEAM_NAMES), data, pq, cps)
        text, sub = add_voice_over(text)
        if sub is not None:
            (root / SRT_OUT).parent.mkdir(parents=True, exist_ok=True)
            (root / SRT_OUT).write_text(sub)
            written.append(SRT_OUT)
        table = sources_table(log)
        if out in SOURCES_OUT:
            side = SOURCES_OUT[out]
            (root / side).write_text(
                f"# Number sources for {out.name}\n\nEvery number in `{out.as_posix()}` traces to "
                f"one row below.{table.split(SOURCES_HEADING, 1)[1]}\n"
            )
            written.append(side)
            table = (
                "\n\nEach number above traces to a results file; "
                f"the list is {side.name} in the repository."
            )
        text = text.rstrip() + table + "\n"
        (root / out).parent.mkdir(parents=True, exist_ok=True)
        (root / out).write_text(text)
        written.append(out)
    return written


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--root", type=Path, default=Path("."))
    a = p.parse_args(argv)
    for out in build(a.root):
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
