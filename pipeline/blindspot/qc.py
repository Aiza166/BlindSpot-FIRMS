"""QC report for the ingested hotspot table.

Reports, per platform × year: rows raw and after each filter (applied in order: standard
processing, type == 0, confidence, coverage box, duplicate removal, persistent-hotspot mask),
days with zero rows, duplicate rows, and schema drift across raw files.

Writes data/processed/qc_report.json and docs/QC_REPORT.md. Every number in both comes
from the data on disk at run time.

    python -m blindspot.qc --hotspots data/processed/hotspots --mask-dir data/processed
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import duckdb

STAGES = (
    "raw",
    "after_standard",
    "after_type",
    "after_confidence",
    "after_box",
    "after_dedup",
    "after_mask",
)

_COUNTS_SQL = """
SELECT platform, CAST(year AS INTEGER) AS year,
       count(*) AS raw,
       count(*) FILTER (WHERE passes_standard) AS after_standard,
       count(*) FILTER (WHERE passes_standard AND passes_type) AS after_type,
       count(*) FILTER (WHERE passes_standard AND passes_type AND passes_conf)
           AS after_confidence,
       count(*) FILTER (WHERE passes_standard AND passes_type AND passes_conf AND in_box)
           AS after_box,
       count(*) FILTER (WHERE passes_standard AND passes_type AND passes_conf AND in_box
                        AND NOT is_duplicate) AS after_dedup,
       count(*) FILTER (WHERE is_duplicate) AS n_duplicates
FROM hotspots
GROUP BY platform, year
ORDER BY platform, year
"""

_MASKED_SQL = """
SELECT platform, CAST(year AS INTEGER) AS year, count(*) AS n
FROM hotspots_masked GROUP BY platform, year
"""


def _has_view(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = con.execute("SELECT count(*) FROM duckdb_views() WHERE view_name = ?", [name]).fetchone()
    return bool(row and row[0])


def stage_counts(con: duckdb.DuckDBPyConnection) -> tuple[list[dict], list[dict]]:
    rows = con.execute(_COUNTS_SQL).fetchall()
    masked: dict[tuple[str, int], int] | None = None
    if _has_view(con, "hotspots_masked"):
        masked = {(p, y): n for p, y, n in con.execute(_MASKED_SQL).fetchall()}
    counts, dups = [], []
    for platform, year, *vals, n_dup in rows:
        rec = {"platform": platform, "year": int(year)}
        rec.update({s: int(v) for s, v in zip(STAGES[:-1], vals, strict=True)})
        rec["after_mask"] = None if masked is None else int(masked.get((platform, year), 0))
        counts.append(rec)
        dups.append({"platform": platform, "year": int(year), "n_duplicates": int(n_dup)})
    return counts, dups


def _ranges(days: list[dt.date]) -> list[list[str]]:
    out: list[list[str]] = []
    for d in days:
        if out and dt.date.fromisoformat(out[-1][1]) + dt.timedelta(days=1) == d:
            out[-1][1] = d.isoformat()
        else:
            out.append([d.isoformat(), d.isoformat()])
    return out


def coverage_gaps(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Days with zero raw rows per platform × year, within the platform's observed span.

    A zero day can be real (no fires anywhere in the file's country) or a data gap; check it
    against FIRMS /api/missing_data/ before treating it as either.
    """
    rows = con.execute(
        "SELECT platform, acq_date, count(*) FROM hotspots GROUP BY platform, acq_date"
    ).fetchall()
    by_platform: dict[str, set[dt.date]] = {}
    for platform, day, _ in rows:
        by_platform.setdefault(platform, set()).add(day)
    out = []
    for platform in sorted(by_platform):
        days = by_platform[platform]
        first, last = min(days), max(days)
        for year in range(first.year, last.year + 1):
            start = max(dt.date(year, 1, 1), first)
            end = min(dt.date(year, 12, 31), last)
            expected = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
            zero = [d for d in expected if d not in days]
            out.append(
                {
                    "platform": platform,
                    "year": year,
                    "expected_days": len(expected),
                    "days_with_data": len(expected) - len(zero),
                    "zero_days": len(zero),
                    "zero_day_ranges": _ranges(zero),
                }
            )
    return out


def schema_drift(ingest_log: dict) -> dict:
    """Compare each raw file's header with the expected schema and with its peers."""
    missing, extra = {}, {}
    signatures: dict[str, dict[tuple[str, ...], list[str]]] = {}
    for f in ingest_log.get("files", []):
        if f["missing_expected"]:
            missing[f["source_file"]] = f["missing_expected"]
        if f["extra"]:
            extra[f["source_file"]] = f["extra"]
        sig = tuple(sorted(f["columns"]))
        signatures.setdefault(f["instrument"], {}).setdefault(sig, []).append(f["source_file"])
    return {
        "files_with_missing_columns": missing,
        "files_with_extra_columns": extra,
        "column_signatures": {
            inst: [{"columns": list(sig), "files": files} for sig, files in sigs.items()]
            for inst, sigs in signatures.items()
        },
        "drift_detected": {inst: len(sigs) > 1 for inst, sigs in sorted(signatures.items())},
    }


def build_report(con: duckdb.DuckDBPyConnection, ingest_log: dict) -> dict:
    counts, dups = stage_counts(con)
    return {
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "stages": list(STAGES),
        "mask_applied": _has_view(con, "hotspots_masked"),
        "n_raw_files": len(ingest_log.get("files", [])),
        "counts": counts,
        "duplicates": dups,
        "coverage_gaps": coverage_gaps(con),
        "schema_drift": schema_drift(ingest_log),
    }


def _fmt(v: object) -> str:
    return "–" if v is None else str(v)


def render_markdown(report: dict) -> str:
    lines = [
        "# QC report",
        "",
        f"Generated by `python -m blindspot.qc` at {report['generated_at_utc']} from "
        f"{report['n_raw_files']} raw file(s). Do not edit by hand; rerun `make data`.",
        "",
        "Filters are applied in order, each column counting rows that pass it and every "
        "filter to its left. Platforms are never summed.",
        "",
        "## Rows per platform × year",
        "",
        "| Platform | Year | " + " | ".join(STAGES) + " |",
        "|---|---|" + "---|" * len(STAGES),
    ]
    for r in report["counts"]:
        lines.append(
            f"| {r['platform']} | {r['year']} | " + " | ".join(_fmt(r[s]) for s in STAGES) + " |"
        )
    if not report["mask_applied"]:
        lines += ["", "Mask not applied in this run (after_mask shown as –)."]
    lines += [
        "",
        "## Days with zero rows",
        "",
        "Within each platform's observed date span. A zero day may be real or a gap; check "
        "FIRMS `/api/missing_data/`.",
        "",
        "| Platform | Year | Expected days | Days with data | Zero days | Zero-day ranges |",
        "|---|---|---|---|---|---|",
    ]
    for g in report["coverage_gaps"]:
        ranges = g["zero_day_ranges"]
        shown = ", ".join(a if a == b else f"{a}…{b}" for a, b in ranges[:8])
        if len(ranges) > 8:
            shown += f" (+{len(ranges) - 8} more in qc_report.json)"
        lines.append(
            f"| {g['platform']} | {g['year']} | {g['expected_days']} | "
            f"{g['days_with_data']} | {g['zero_days']} | {shown or '–'} |"
        )
    lines += [
        "",
        "## Duplicates",
        "",
        "Same platform, UTC time, lat and lon. Flagged in `hotspots.is_duplicate`, "
        "excluded from `hotspots_filtered`.",
        "",
        "| Platform | Year | Duplicate rows |",
        "|---|---|---|",
    ]
    lines += [
        f"| {d['platform']} | {d['year']} | {d['n_duplicates']} |" for d in report["duplicates"]
    ]
    drift = report["schema_drift"]
    lines += ["", "## Schema drift", ""]
    for inst, flag in drift["drift_detected"].items():
        n = len(drift["column_signatures"][inst])
        lines.append(f"- {inst}: {'DRIFT' if flag else 'consistent'} ({n} column set(s))")
    for name, cols in drift["files_with_missing_columns"].items():
        lines.append(f"- `{name}` is missing expected column(s): {', '.join(cols)}")
    for name, cols in drift["files_with_extra_columns"].items():
        lines.append(f"- `{name}` has unexpected column(s): {', '.join(cols)}")
    return "\n".join(lines) + "\n"


def write_outputs(report: dict, json_path: Path, md_path: Path) -> tuple[Path, Path]:
    json_path, md_path = Path(json_path), Path(md_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2))
    md_path.write_text(render_markdown(report))
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    from blindspot import ingest, mask

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument(
        "--mask-dir",
        type=Path,
        default=Path("data/processed"),
        help="folder holding persistent_mask_cells.parquet + mask_report.json",
    )
    p.add_argument("--json", type=Path, default=Path("data/processed/qc_report.json"))
    p.add_argument("--md", type=Path, default=Path("docs/QC_REPORT.md"))
    args = p.parse_args(argv)
    con = ingest.connect(args.hotspots)
    cells = args.mask_dir / mask.MASK_CELLS_FILE
    report_file = args.mask_dir / mask.MASK_REPORT_FILE
    if cells.exists() and report_file.exists():
        mask.apply_mask(con, mask.load_mask(cells, report_file))
    log = json.loads((args.hotspots / ingest.INGEST_LOG).read_text())
    j, m = write_outputs(build_report(con, log), args.json, args.md)
    print(f"QC report -> {j} and {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
