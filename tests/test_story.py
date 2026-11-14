"""Tests for blindspot.story: placeholders, voice-over limits, and number traceability."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from blindspot import story

ROOT = Path(__file__).resolve().parents[1]
NUM = re.compile(r"(?<![\w.])[-+−]?\d(?:[\d,]*\d)?(?:\.\d+)?%?(?![\w])")
# Literal numbers allowed in the templates: fixed rule text (PLAN §4 filters, licence and product
# versions, 375 m pixels, deadlines, the 30 s / 70-word video limits, the pre-registered window).
FIXED = {
    "0",
    "30",
    "375",
    "6.1",
    "2.5",
    "1.0",
    "13",
    "14",
    "15",
    "70",
    "30.0",
    "6.5",  # Vadrevu & Lasko (2018) Aqua->VIIRS multiple, quoted in docs/REFERENCES.md
    "55",  # video voice-over word limit
}
STRIP = [
    re.compile(r"## Number sources.*", re.S),
    re.compile(r"## References.*?(?=\n## |\Z)", re.S),
    # hand-copied run log (command timings, test counts); not a result of the study
    re.compile(r"## Final check.*?(?=\n## |\Z)", re.S),
    re.compile(r"^\s*\d+\. ", re.M),  # list numbers
    re.compile(r"\d+ words, \d+ s\."),  # computed by add_voice_over
    re.compile(r"https?://\S+"),
    re.compile(r"\]\([^)]*\)"),  # image and link targets (file names such as usecase-sangrur-2.png)
    re.compile(r"\bBSD-\d-Clause\b|\bApache-\d\.\d\b"),  # licence identifiers
    re.compile(r"doi:\S+"),
    re.compile(r"`[^`]*`"),
    re.compile(r"\d+:\d\d(?:–\d+:\d\d)?"),  # shot times
    re.compile(
        r"\bD-\d{3}\b|\bADM\d\b|§\d+|\bT\d\b|\bP\d\b|^\| \d+ \||\bH\d+\b|NOAA-20|S-NPP", re.M
    ),
]


def _numbers(text: str) -> list[str]:
    for pat in STRIP:
        text = pat.sub(" ", text)
    return NUM.findall(text)


def _is_year(tok: str) -> bool:
    return tok.isdigit() and 1990 <= int(tok) <= 2030


def test_render_fills_and_logs():
    data = {"t1": {"a": {"b": [0.5, 6.13]}}, "index": {"ds": [1, 2, 3]}}
    out, log = story.render("x {{t1:a.b.1|pct}} y {{index:ds|len}} {{pitch}}", data, "P")
    assert out == "x +613% y 3 P"
    assert ("t1:a.b.1|pct", "+613%") in log


def test_month_format_names_the_month():
    out, _ = story.render(
        "to {{index:period.last|month}}", {"index": {"period": {"last": "2026-10"}}}, ""
    )
    assert out == "to October 2026"


@pytest.mark.parametrize("tmpl", ["{{t9:a}}", "{{t1:nope}}", "{{t1:a|bogus}}"])
def test_render_rejects_bad_placeholders(tmpl):
    with pytest.raises(KeyError):
        story.render(tmpl, {"t1": {"a": 1}}, "")


def test_render_rejects_leftover_braces():
    with pytest.raises(ValueError):
        story.render("{{t1:a}} and {{ broken", {"t1": {"a": 1}}, "")


def test_voice_over_limit_and_srt():
    row = "| 0:00–0:04 | p | t | <!--vo-->One two. Three.<!--/vo--> |\n<!--vo-full-->"
    text, sub = story.add_voice_over(row)
    assert "> One two. Three." in text and "3 words, 4 s." in text
    assert sub.startswith("1\n00:00:00,000 --> 00:00:02,667\nOne two.")
    long = "| 0:00–0:30 | p | t | <!--vo-->" + "word " * 56 + "<!--/vo--> |"
    with pytest.raises(ValueError):
        story.add_voice_over(long)


@pytest.fixture
def built(tmp_path):
    for p in [*story.SOURCES.values(), *(t for t, _ in story.JOBS), story.CHECKPOINTS]:
        src = ROOT / p
        if not src.exists():
            pytest.skip(f"{p} missing (run make web-test / make appdata first)")
        (tmp_path / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, tmp_path / p)
    index = json.loads((ROOT / story.SOURCES["index"]).read_text())
    ddir = story.SOURCES["index"].parent / "districts"
    (tmp_path / ddir).mkdir(parents=True, exist_ok=True)
    for _, name, country in story.USECASES:
        d = next(x for x in index["districts"] if x["name"] == name and x["country"] == country)
        shutil.copy(ROOT / ddir / f"{d['id']}.json", tmp_path / ddir / f"{d['id']}.json")
    story.build(tmp_path)
    data = story.load({k: tmp_path / p for k, p in story.SOURCES.items()})
    logs = {}
    for tmpl, out in story.JOBS:
        cps = (tmp_path / story.CHECKPOINTS).read_text()
        _, logs[out] = story.render(
            (tmp_path / tmpl).read_text(), data, story.pitch_quote(data), cps
        )
    return tmp_path, logs, story.pitch_quote(data)


def test_outputs_have_no_placeholders(built):
    root, _, _ = built
    for _, out in story.JOBS:
        text = (root / out).read_text()
        assert "{{" not in text and "}}" not in text and "<!--vo" not in text
    assert (root / story.SRT_OUT).read_text().startswith("1\n00:00:00,000")


def test_every_number_traces_to_a_json_key(built):
    root, logs, pq = built
    for _, out in story.JOBS:
        text = (root / out).read_text().replace(pq, " ")
        allowed = {n for _, v in logs[out] for n in NUM.findall(v)}
        stray = [
            n for n in _numbers(text) if n not in allowed and n not in FIXED and not _is_year(n)
        ]
        assert not stray, f"{out}: numbers not from JSON: {stray}"


def test_number_sources_table_lists_each_placeholder(built):
    root, logs, _ = built
    for _, out in story.JOBS:
        text = (root / story.SOURCES_OUT.get(out, out)).read_text()
        for expr, val in logs[out]:
            if expr not in ("pitch", "checkpoints"):
                assert f"| {val} |" in text


def test_checkpoint_table_reads_rows():
    md = "| CP | By | Gate | Status | Score | Notes |\n|---|---|---|---|---|---|\n"
    md += "| H6 | x | Rows | ✅ | 8 | n |"
    assert story.checkpoint_table(md).splitlines()[-1] == "| H6 | Rows | ✅ | 8 |"


def test_t3_reliability_formats():
    rel = {
        "2021": {"harmonization_reliable": "yes"},
        "2022": {"harmonization_reliable": "caution"},
        "2023": {"harmonization_reliable": "caution"},
        "2025": {"harmonization_reliable": "caution"},
    }
    data = {"t3": {"r": rel, "ys": [2022, 2023, 2024]}}
    out, _ = story.render(
        "{{t3:r|caution}} / {{t3:r|first_caution}} / {{t3:ys|years}} / {{t3:x|x2}}",
        {**data, "t3": {**data["t3"], "x": 0.0537}},
        "",
    )
    assert out == "2022, 2023, 2025 / 2022 / 2022–2024 / 0.05×"


def test_month_check_matches_usecase_rules():
    doc = {
        "period": {"first": "2003-11"},
        "harmonized": {
            "value": [
                10.0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                30.0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                5.0,
            ],
            "partial": [False] * 25,
        },
        "median": {
            "harmonized": {"values": [0] * 10 + [10.0, 0], "baseline_years": [2003, 2005]},
            "NOAA20": {"values": [0] * 10 + [4.0, 0], "baseline_years": [2019, 2025]},
        },
        "median_excl_flagged": {
            "values": [0] * 10 + [20.0, 0],
            "excluded_years": [2005],
        },
        "raw": {"NOAA20": {"n": [None] * 24 + [2]}},
        "reliability": {
            "calib_region": "IN_Punjab",
            "caution_years": {"2005": ["burning_time_shift"]},
        },
    }
    k = story.month_check(doc, "2005-11")
    assert k["value"] == 5.0 and k["ratio"] == 0.5
    assert k["rank_from_lowest"] == 1 and k["n_compared"] == 3
    assert k["min_earlier"] == 10.0 and k["min_earlier_year"] == 2003
    assert k["noaa20_ratio"] == 0.5
    assert k["caution"] == "caution" and k["reasons"] == "burning_time_shift"
    assert k["median_excl"] == 20.0 and k["ratio_excl"] == 0.25 and k["excluded_years"] == [2005]


def test_load_adds_usecase(built):
    root, _, _ = built
    data = story.load({k: root / p for k, p in story.SOURCES.items()})
    assert {"sangrur", "kasur", "sangrur25", "kasur25"} <= set(data["usecase"])


def _nov_doc(vals: dict[int, float], caution: list[int], partial: tuple[int, ...] = ()):
    """Harmonized series, first month 2010-11, so every 12th entry is a November."""
    years = sorted(vals)
    n = (years[-1] - 2010) * 12 + 1
    v: list[float | None] = [None] * n
    p: list[bool | None] = [None] * n
    for y in years:
        v[(y - 2010) * 12] = vals[y]
        p[(y - 2010) * 12] = y in partial
    return {
        "period": {"first": "2010-11"},
        "harmonized": {"value": v, "partial": p},
        "reliability": {"caution_years": {str(y): ["aqua_overpass_drift"] for y in caution}},
    }


def test_flagship_month_is_highest_unflagged_november_since_2012():
    # 2011 is before 2012; 2014 is highest but flagged; 2016 partial; 2013 wins
    doc = _nov_doc(
        {2011: 900, 2012: 50, 2013: 70, 2014: 500, 2015: 60, 2016: 300, 2017: 40},
        caution=[2014],
        partial=(2016,),
    )
    # month index: first=2010-11 so every 12th entry is a November
    assert story.flagship_month(doc) == ("2013-11", 4)  # 2012, 2013, 2015, 2017 eligible


def test_flagship_tie_goes_to_later_year_and_empty_raises():
    doc = _nov_doc({2012: 80, 2013: 80, 2014: 10}, caution=[])
    assert story.flagship_month(doc)[0] == "2013-11"
    with pytest.raises(ValueError):
        story.flagship_month(_nov_doc({2012: 80}, caution=[2012]))


def test_headline_examples_are_unflagged_and_contrast_flagged(built):
    root, _, _ = built
    data = story.load({k: root / p for k, p in story.SOURCES.items()})
    uc = data["usecase"]
    for key in ("sangrur", "kasur"):
        assert uc[key]["caution"] == "reliable", key  # headline: not on the caution list
        assert uc[f"{key}25"]["caution"] == "caution" and uc[f"{key}25"]["ym"] == "2025-11"
        assert uc[key]["ym"][:4] != "2025" and int(uc[key]["ym"][:4]) >= 2012


def test_lead_sentence_first_in_submission_and_video(built):
    root, _, _ = built
    sub = (root / "docs/SUBMISSION.md").read_text()
    lines = [x for x in sub.splitlines() if x.strip()]
    assert lines[0].startswith("# ")
    lead = lines[1]  # first content line under the title
    # W5 (decisions.md W-06): the page opens on a person and a problem, then the 2012 jump.
    assert lead.startswith("**A district officer in Punjab") and "jump" in lead
    assert "flags the years" in lead
    srt = (root / story.SRT_OUT).read_text()
    assert "Pakistani Punjab's October–November fire record jumps" in srt.split("\n\n")[0]
