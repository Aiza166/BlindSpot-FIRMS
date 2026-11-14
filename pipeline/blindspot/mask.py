"""Persistent-hotspot mask (PLAN.md §4, docs/DECISIONS.md D-022 and D-024).

Default rule, `year-round` (D-024): a cell-year is year-round when the cell has filtered
detections in at least `min_months` distinct calendar months of that year and those months
cannot be covered by `max_seasons` windows of `season_len` consecutive months (windows wrap
Dec -> Jan). A cell is masked when it has at least `min_years` year-round years. Kilns, steel
plants and flares burn across the calendar; forest fires and crop-residue burning come in one
or two seasons, so they are kept.

Old rule, `seasonal-offseason` (D-022, superseded): a cell is masked when it has a detection
in at least `min_years` years during `months` (Jan–Mar, Jul–Sep). Kept only for
docs/MASK_COMPARISON.md; it removes real forest-fire and early paddy-burning detections.

Under both rules one static mask is built from all platforms and applied to every series and
year (NRT included); all detections in a masked cell are removed. Months and years are taken
from local solar time.

The share of detections removed is reported per platform, never pooled across platforms
(CLAUDE.md rule 1).

    python -m blindspot.mask --hotspots data/processed/hotspots --out data/processed
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd

DEFAULT_GRID_DEG = 0.01
DEFAULT_MIN_YEARS = 3
DEFAULT_MONTHS: tuple[int, ...] = (1, 2, 3, 7, 8, 9)  # seasonal-offseason rule only
DEFAULT_MIN_MONTHS = 4
DEFAULT_SEASON_LEN = 3
DEFAULT_MAX_SEASONS = 2
RULE_YEAR_ROUND = "year-round"
RULE_SEASONAL_OFFSEASON = "seasonal-offseason"
RULES = (RULE_YEAR_ROUND, RULE_SEASONAL_OFFSEASON)
DEFAULT_RULE = RULE_YEAR_ROUND
# Views mask.py may read from. Identifiers cannot be bound as SQL parameters, so the
# view name is checked against this allow-list instead.
ALLOWED_SOURCE_VIEWS = frozenset({"hotspots_filtered", "hotspots_filtered_nrt"})
# Guards floor() against x/grid landing a hair below an integer (31.5/0.01 = 3149.99...).
_EPS = 1e-9

MASK_CELLS_FILE = "persistent_mask_cells.parquet"
MASK_REPORT_FILE = "mask_report.json"


def cell_index(coord: float, grid_deg: float) -> int:
    """Integer grid index of a coordinate (same formula as the SQL below)."""
    return math.floor(coord / grid_deg + _EPS)


def _month_bits(months: Iterable[int]) -> int:
    return sum(1 << (int(m) - 1) for m in set(months))


def _season_unions(season_len: int, max_seasons: int) -> set[int]:
    """Bitmasks of every union of `max_seasons` circular windows of `season_len` months."""
    windows = [
        _month_bits(((start + k) % 12) + 1 for k in range(season_len)) for start in range(12)
    ]
    unions = set()
    for combo in itertools.combinations_with_replacement(windows, max_seasons):
        u = 0
        for w in combo:
            u |= w
        unions.add(u)
    return unions


def _is_year_round_bits(bits: int, min_months: int, unions: set[int]) -> bool:
    if bin(bits).count("1") < min_months:
        return False
    return not any(bits & ~u == 0 for u in unions)


def is_year_round(
    months: Iterable[int],
    min_months: int = DEFAULT_MIN_MONTHS,
    season_len: int = DEFAULT_SEASON_LEN,
    max_seasons: int = DEFAULT_MAX_SEASONS,
) -> bool:
    """True when `months` (one cell-year) has >= min_months distinct months that no
    `max_seasons` windows of `season_len` consecutive months (wrapping Dec -> Jan) can cover."""
    unions = _season_unions(season_len, max_seasons)
    return _is_year_round_bits(_month_bits(months), min_months, unions)


def year_round_bitmasks(
    min_months: int = DEFAULT_MIN_MONTHS,
    season_len: int = DEFAULT_SEASON_LEN,
    max_seasons: int = DEFAULT_MAX_SEASONS,
) -> list[int]:
    """Every 12-bit month mask (bit m-1 = month m) that counts as a year-round cell-year."""
    unions = _season_unions(season_len, max_seasons)
    return [b for b in range(1, 1 << 12) if _is_year_round_bits(b, min_months, unions)]


@dataclass
class MaskResult:
    cells: pd.DataFrame
    grid_deg: float
    min_years: int
    months: tuple[int, ...]
    source_view: str
    rule: str = DEFAULT_RULE
    min_months: int = DEFAULT_MIN_MONTHS
    season_len: int = DEFAULT_SEASON_LEN
    max_seasons: int = DEFAULT_MAX_SEASONS
    removed: dict[str, int] = field(default_factory=dict)
    total: dict[str, int] = field(default_factory=dict)

    @property
    def share_removed(self) -> dict[str, float]:
        return {p: (self.removed.get(p, 0) / n if n else 0.0) for p, n in self.total.items()}

    def parameters(self) -> dict:
        prm: dict = {"rule": self.rule, "grid_deg": self.grid_deg, "min_years": self.min_years}
        if self.rule == RULE_YEAR_ROUND:
            prm.update(
                min_months=self.min_months,
                season_len=self.season_len,
                max_seasons=self.max_seasons,
            )
        else:
            prm["months"] = list(self.months)
        prm.update(time_basis="local_solar_datetime", source_view=self.source_view)
        return prm

    def to_report(self) -> dict:
        return {
            "parameters": self.parameters(),
            "n_masked_cells": int(len(self.cells)),
            "detections_total_by_platform": self.total,
            "detections_removed_by_platform": self.removed,
            "share_removed_by_platform": self.share_removed,
        }


def _validate(
    grid_deg: float,
    min_years: int,
    months: tuple[int, ...],
    source_view: str,
    rule: str = DEFAULT_RULE,
    min_months: int = DEFAULT_MIN_MONTHS,
    season_len: int = DEFAULT_SEASON_LEN,
    max_seasons: int = DEFAULT_MAX_SEASONS,
) -> None:
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}")
    if not 1 <= min_months <= 12:
        raise ValueError("min_months must be in 1..12")
    if not 1 <= season_len <= 12 or max_seasons < 1:
        raise ValueError("season_len must be in 1..12 and max_seasons >= 1")
    if not grid_deg > 0:
        raise ValueError("grid_deg must be > 0")
    if min_years < 1:
        raise ValueError("min_years must be >= 1")
    if not months or any(m not in range(1, 13) for m in months):
        raise ValueError("months must be a non-empty subset of 1..12")
    if source_view not in ALLOWED_SOURCE_VIEWS:
        raise ValueError(f"source_view must be one of {sorted(ALLOWED_SOURCE_VIEWS)}")


_CELL_SQL = """
CAST(floor(lat / $grid + $eps) AS BIGINT) AS cell_lat,
CAST(floor(lon / $grid + $eps) AS BIGINT) AS cell_lon
"""


def build_mask(
    con: duckdb.DuckDBPyConnection,
    grid_deg: float = DEFAULT_GRID_DEG,
    min_years: int = DEFAULT_MIN_YEARS,
    months: tuple[int, ...] = DEFAULT_MONTHS,
    source_view: str = "hotspots_filtered",
    rule: str = DEFAULT_RULE,
    min_months: int = DEFAULT_MIN_MONTHS,
    season_len: int = DEFAULT_SEASON_LEN,
    max_seasons: int = DEFAULT_MAX_SEASONS,
) -> MaskResult:
    """Find persistent cells in `source_view` and count detections they remove per platform.

    `rule="year-round"` (default, D-024) uses min_years, min_months, season_len, max_seasons;
    `rule="seasonal-offseason"` (old D-022 rule, comparison only) uses min_years and months.
    """
    months = tuple(int(m) for m in months)
    _validate(grid_deg, min_years, months, source_view, rule, min_months, season_len, max_seasons)
    if rule == RULE_YEAR_ROUND:
        cells = _year_round_cells(
            con, grid_deg, min_years, source_view, min_months, season_len, max_seasons
        )
    else:
        cells = _offseason_cells(con, grid_deg, min_years, months, source_view)
    cells["lat_min"] = cells["cell_lat"] * grid_deg
    cells["lon_min"] = cells["cell_lon"] * grid_deg

    result = MaskResult(
        cells,
        float(grid_deg),
        int(min_years),
        months,
        source_view,
        rule,
        int(min_months),
        int(season_len),
        int(max_seasons),
    )
    _register_cells(con, result)
    counts = con.execute(
        f"""
        WITH c AS (SELECT platform, {_CELL_SQL} FROM {source_view})
        SELECT c.platform,
               count(*) AS total,
               count(m.cell_lat) AS removed
        FROM c LEFT JOIN persistent_mask_cells m USING (cell_lat, cell_lon)
        GROUP BY c.platform
        ORDER BY c.platform
        """,  # noqa: S608 - source_view is allow-listed; values are bound parameters
        {"grid": float(grid_deg), "eps": _EPS},
    ).fetchall()
    result.total = {p: int(t) for p, t, _ in counts}
    result.removed = {p: int(r) for p, _, r in counts}
    return result


def _offseason_cells(
    con: duckdb.DuckDBPyConnection,
    grid_deg: float,
    min_years: int,
    months: tuple[int, ...],
    source_view: str,
) -> pd.DataFrame:
    params = {"grid": float(grid_deg), "eps": _EPS, "months": list(months), "min_years": min_years}
    return con.execute(
        f"""
        WITH c AS (
            SELECT {_CELL_SQL},
                   year(local_solar_datetime) AS y,
                   month(local_solar_datetime) AS m
            FROM {source_view}
        )
        SELECT cell_lat, cell_lon,
               count(DISTINCT y) AS n_years,
               list(DISTINCT y ORDER BY y) AS years,
               count(*) AS n_offseason_detections
        FROM c
        WHERE list_contains($months, m)
        GROUP BY cell_lat, cell_lon
        HAVING count(DISTINCT y) >= $min_years
        ORDER BY cell_lat, cell_lon
        """,  # noqa: S608 - source_view is allow-listed; values are bound parameters
        params,
    ).df()


def _year_round_cells(
    con: duckdb.DuckDBPyConnection,
    grid_deg: float,
    min_years: int,
    source_view: str,
    min_months: int,
    season_len: int,
    max_seasons: int,
) -> pd.DataFrame:
    """Cells with >= min_years year-round years.

    Columns: n_years / years (year-round years only), n_detections (all years, all
    platforms), months_active (distinct months over the year-round years).
    """
    params = {
        "grid": float(grid_deg),
        "eps": _EPS,
        "min_years": min_years,
        "qualifying": year_round_bitmasks(min_months, season_len, max_seasons),
    }
    return con.execute(
        f"""
        WITH c AS (
            SELECT {_CELL_SQL},
                   year(local_solar_datetime) AS y,
                   month(local_solar_datetime) AS m
            FROM {source_view}
        ),
        cy AS (
            SELECT cell_lat, cell_lon, y,
                   bit_or(CAST(1 AS BIGINT) << (m - 1)) AS bits,
                   list(DISTINCT m) AS ms
            FROM c GROUP BY cell_lat, cell_lon, y
        ),
        q AS (
            SELECT cell_lat, cell_lon,
                   count(*) AS n_years,
                   list(y ORDER BY y) AS years,
                   list_sort(list_distinct(flatten(list(ms)))) AS months_active
            FROM cy
            WHERE list_contains($qualifying, bits)
            GROUP BY cell_lat, cell_lon
            HAVING count(*) >= $min_years
        ),
        n AS (SELECT cell_lat, cell_lon, count(*) AS n_detections FROM c GROUP BY ALL)
        SELECT q.cell_lat, q.cell_lon, q.n_years, q.years, q.months_active, n.n_detections
        FROM q JOIN n USING (cell_lat, cell_lon)
        ORDER BY q.cell_lat, q.cell_lon
        """,  # noqa: S608 - source_view is allow-listed; values are bound parameters
        params,
    ).df()


def _register_cells(con: duckdb.DuckDBPyConnection, result: MaskResult) -> None:
    cells = result.cells[["cell_lat", "cell_lon"]].astype("int64")
    con.register("_mask_cells_df", cells)
    con.execute("CREATE OR REPLACE TABLE persistent_mask_cells AS SELECT * FROM _mask_cells_df")
    con.unregister("_mask_cells_df")


def apply_mask(
    con: duckdb.DuckDBPyConnection, result: MaskResult, source_view: str = "hotspots_filtered"
) -> None:
    """Create views hotspots_masked_flags (all rows + in_persistent_mask) and hotspots_masked.

    The grid used here is the one stored in `result`, so build and apply always agree.
    """
    _validate(
        result.grid_deg,
        result.min_years,
        result.months,
        source_view,
        result.rule,
        result.min_months,
        result.season_len,
        result.max_seasons,
    )
    _register_cells(con, result)
    # DuckDB views cannot hold bound parameters; the grid is a float from MaskResult,
    # formatted with repr(), never user text.
    grid = repr(float(result.grid_deg))
    eps = repr(_EPS)
    con.execute(
        f"""
        CREATE OR REPLACE VIEW hotspots_masked_flags AS
        SELECT s.*, (m.cell_lat IS NOT NULL) AS in_persistent_mask
        FROM {source_view} s
        LEFT JOIN persistent_mask_cells m
          ON m.cell_lat = CAST(floor(s.lat / {grid} + {eps}) AS BIGINT)
         AND m.cell_lon = CAST(floor(s.lon / {grid} + {eps}) AS BIGINT);
        CREATE OR REPLACE VIEW hotspots_masked AS
        SELECT * EXCLUDE (in_persistent_mask) FROM hotspots_masked_flags
        WHERE NOT in_persistent_mask;
        """  # noqa: S608 - allow-listed view name and float literals only
    )


def write_outputs(result: MaskResult, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cells_path = out_dir / MASK_CELLS_FILE
    report_path = out_dir / MASK_REPORT_FILE
    result.cells.to_parquet(cells_path, index=False)
    report_path.write_text(json.dumps(result.to_report(), indent=2))
    return cells_path, report_path


def load_mask(cells_path: Path, report_path: Path) -> MaskResult:
    rep = json.loads(Path(report_path).read_text())
    prm = rep["parameters"]
    # Reports written before D-024 have no "rule" key: they used the off-season rule.
    rule = prm.get("rule", RULE_SEASONAL_OFFSEASON)
    result = MaskResult(
        pd.read_parquet(cells_path),
        prm["grid_deg"],
        prm["min_years"],
        tuple(prm.get("months", DEFAULT_MONTHS)),
        prm["source_view"],
        rule,
        prm.get("min_months", DEFAULT_MIN_MONTHS),
        prm.get("season_len", DEFAULT_SEASON_LEN),
        prm.get("max_seasons", DEFAULT_MAX_SEASONS),
    )
    result.total = rep["detections_total_by_platform"]
    result.removed = rep["detections_removed_by_platform"]
    return result


def main(argv: list[str] | None = None) -> int:
    from blindspot import ingest

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument("--out", type=Path, default=Path("data/processed"))
    p.add_argument("--grid", type=float, default=DEFAULT_GRID_DEG, help="cell size in degrees")
    p.add_argument("--min-years", type=int, default=DEFAULT_MIN_YEARS)
    p.add_argument(
        "--rule",
        choices=RULES,
        default=DEFAULT_RULE,
        help="year-round (D-024, default); seasonal-offseason (old D-022 rule, comparison only)",
    )
    p.add_argument("--min-months", type=int, default=DEFAULT_MIN_MONTHS, help="year-round rule")
    p.add_argument("--season-len", type=int, default=DEFAULT_SEASON_LEN, help="year-round rule")
    p.add_argument("--max-seasons", type=int, default=DEFAULT_MAX_SEASONS, help="year-round rule")
    p.add_argument(
        "--months",
        type=int,
        nargs="+",
        default=list(DEFAULT_MONTHS),
        help="seasonal-offseason rule only",
    )
    args = p.parse_args(argv)
    con = ingest.connect(args.hotspots)
    result = build_mask(
        con,
        args.grid,
        args.min_years,
        tuple(args.months),
        rule=args.rule,
        min_months=args.min_months,
        season_len=args.season_len,
        max_seasons=args.max_seasons,
    )
    cells_path, report_path = write_outputs(result, args.out)
    print(
        f"rule {result.rule}: {len(result.cells)} persistent cells -> {cells_path}; "
        f"report -> {report_path}"
    )
    for platform, share in result.share_removed.items():
        print(f"  {platform}: {share:.4%} of filtered detections removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
