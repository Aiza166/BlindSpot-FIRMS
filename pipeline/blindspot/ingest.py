"""Read raw FIRMS CSVs (MODIS + VIIRS) and normalise them to one hotspot table.

Filters from PLAN.md §4 are added as separate boolean flag columns; no row is ever dropped
here. `filtered_view` (pandas) and the DuckDB view `hotspots_filtered` combine the flags.

Output: Hive-partitioned Parquet, year=YYYY/platform=NAME, under data/processed/hotspots/.

    python -m blindspot.ingest --raw data/raw/firms --out data/processed/hotspots
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

from blindspot import schema

log = logging.getLogger(__name__)

INGEST_LOG = "_ingest_log.json"
_MARKER = "_blindspot_hotspots"


class SchemaError(ValueError):
    """A raw file does not match a known FIRMS schema."""


@dataclass(frozen=True)
class Box:
    """Lon/lat box, inclusive on all edges."""

    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float


# PLAN.md §3: coverage box 60–80°E, 23–37°N.
COVERAGE_BOX = Box(lon_min=60.0, lon_max=80.0, lat_min=23.0, lat_max=37.0)

# PLAN.md §4: MODIS confidence >= 30.
MODIS_MIN_CONFIDENCE = 30
# MODIS class boundaries (low < 30 <= nominal < 80 <= high). See docs/DATA_SCHEMA.md.
MODIS_HIGH_CONFIDENCE = 80
# PLAN.md §4: VIIRS n/h; robustness run with l/n/h.
VIIRS_PASS_CLASSES = frozenset({"nominal", "high"})
VIIRS_ROBUST_CLASSES = frozenset({"low", "nominal", "high"})

NORMALIZED_COLUMNS: tuple[str, ...] = (
    "platform",
    "instrument",
    "lat",
    "lon",
    "acq_datetime_utc",
    "local_solar_datetime",
    "acq_date",
    "year",
    "daynight",
    "confidence_raw",
    "confidence_class",
    "frp",
    "scan",
    "track",
    "type",
    "version",
    "processing",
    "source_file",
    "source_row",
    "passes_standard",
    "passes_type",
    "passes_conf",
    "passes_conf_robust",
    "in_box",
)

ARROW_SCHEMA = pa.schema(
    [
        ("platform", pa.string()),
        ("instrument", pa.string()),
        ("lat", pa.float64()),
        ("lon", pa.float64()),
        ("acq_datetime_utc", pa.timestamp("us", tz="UTC")),
        ("local_solar_datetime", pa.timestamp("us")),
        ("acq_date", pa.date32()),
        ("year", pa.int32()),
        ("daynight", pa.string()),
        ("confidence_raw", pa.string()),
        ("confidence_class", pa.string()),
        ("frp", pa.float64()),
        ("scan", pa.float64()),
        ("track", pa.float64()),
        ("type", pa.int8()),
        ("version", pa.string()),
        ("processing", pa.string()),
        ("source_file", pa.string()),
        ("source_row", pa.int64()),
        ("passes_standard", pa.bool_()),
        ("passes_type", pa.bool_()),
        ("passes_conf", pa.bool_()),
        ("passes_conf_robust", pa.bool_()),
        ("in_box", pa.bool_()),
    ]
)

_VERSION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(URT|RT|NRT)?\s*$", re.IGNORECASE)


# ---------------------------------------------------------------- reading


def read_raw_csv(path: Path) -> pd.DataFrame:
    """Read a FIRMS CSV as strings with lower-cased, stripped column names."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "brightness_2" in df.columns:  # VIIRS as served by web services
        df = df.rename(columns=schema.VIIRS_ALIASES)
    return df


def detect_instrument(columns: list[str], raw: pd.DataFrame | None, filename: str) -> str:
    """Return "MODIS" or "VIIRS" from the instrument column, header, or filename."""
    cols = set(columns)
    if raw is not None and "instrument" in cols:
        values = {str(v).strip().upper() for v in raw["instrument"].dropna().unique()}
        if len(values) == 1 and values <= {"MODIS", "VIIRS"}:
            return values.pop()
        if len(values) > 1:
            raise SchemaError(f"{filename}: mixed instrument values {sorted(values)}")
    if "bright_t31" in cols:
        return "MODIS"
    if cols & {"bright_ti4", "bright_ti5", "brightness_2"}:
        return "VIIRS"
    name = filename.lower()
    if "modis" in name:
        return "MODIS"
    if "viirs" in name:
        return "VIIRS"
    raise SchemaError(
        f"{filename}: cannot tell MODIS from VIIRS (no instrument column, no "
        "bright_t31 / bright_ti4 column, no hint in the file name)"
    )


def _platform_hint(filename: str) -> str | None:
    name = filename.lower()
    for product, platform in schema.PRODUCT_TO_PLATFORM.items():
        if product in name:
            return platform
    return None


def _platforms(raw: pd.DataFrame, instrument: str, filename: str) -> pd.Series:
    codes = raw["satellite"].fillna("").astype(str).str.strip().str.upper()
    platform = codes.map(schema.SATELLITE_TO_PLATFORM)
    unknown = sorted(set(codes[platform.isna()]))
    if unknown:
        hint = _platform_hint(filename) if instrument == "VIIRS" else None
        if hint and unknown == [""]:
            platform = platform.fillna(hint)
        else:
            raise SchemaError(f"{filename}: unknown satellite code(s) {unknown}")
    wrong = sorted({p for p in platform.unique() if schema.PLATFORM_INSTRUMENT[p] != instrument})
    if wrong:
        raise SchemaError(
            f"{filename}: satellite(s) {wrong} do not belong to instrument {instrument}"
        )
    return platform.astype(str)


# ---------------------------------------------------------------- field logic


def parse_acq_datetime(acq_date: pd.Series, acq_time: pd.Series) -> pd.Series:
    """Combine acq_date (YYYY-MM-DD) and acq_time (HHMM UTC, leading zeros optional)."""
    hhmm = acq_time.astype(str).str.strip().str.replace(":", "", regex=False).str.zfill(4)
    stamp = acq_date.astype(str).str.strip() + " " + hhmm
    out = pd.to_datetime(stamp, format="%Y-%m-%d %H%M", errors="raise")
    return out.dt.tz_localize("UTC")


def local_solar_datetime(utc: pd.Series, lon: pd.Series) -> pd.Series:
    """Local solar time = UTC + lon/15 hours (naive timestamp: it is not a civil time zone)."""
    naive = utc.dt.tz_convert("UTC").dt.tz_localize(None)
    offset = pd.to_timedelta(lon.astype(float) * 240.0, unit="s")  # 3600/15 s per degree
    return (naive + offset).dt.floor("us")


def modis_confidence(raw: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MODIS 0–100 → (class, passes ≥30, robust). Robust equals primary for MODIS."""
    num = pd.to_numeric(raw, errors="coerce")
    cls = pd.Series(pd.NA, index=raw.index, dtype="object")
    cls[num < MODIS_MIN_CONFIDENCE] = "low"
    cls[(num >= MODIS_MIN_CONFIDENCE) & (num < MODIS_HIGH_CONFIDENCE)] = "nominal"
    cls[num >= MODIS_HIGH_CONFIDENCE] = "high"
    passes = (num >= MODIS_MIN_CONFIDENCE).fillna(False).astype(bool)
    return cls, passes, passes.copy()


def viirs_confidence(raw: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """VIIRS l/n/h (or low/nominal/high) → (class, passes n/h, robust l/n/h)."""
    cls = raw.astype(str).str.strip().str.lower().map(schema.VIIRS_CONFIDENCE)
    cls = cls.astype("object").where(cls.notna(), pd.NA)
    passes = cls.isin(VIIRS_PASS_CLASSES).astype(bool)
    robust = cls.isin(VIIRS_ROBUST_CLASSES).astype(bool)
    return cls, passes, robust


def processing_level(version: pd.Series) -> pd.Series:
    """'standard' for a bare collection number, else the URT/RT/NRT suffix; NA if unparsable."""

    def one(v: object) -> object:
        m = _VERSION_RE.match(str(v)) if pd.notna(v) else None
        if not m:
            return pd.NA
        return m.group(2).upper() if m.group(2) else "standard"

    return version.map(one).astype("object")


def in_box(lat: pd.Series, lon: pd.Series, box: Box = COVERAGE_BOX) -> pd.Series:
    return (lon.between(box.lon_min, box.lon_max) & lat.between(box.lat_min, box.lat_max)).astype(
        bool
    )


# ---------------------------------------------------------------- normalise


def normalize(raw: pd.DataFrame, source_file: str, box: Box = COVERAGE_BOX) -> pd.DataFrame:
    """Normalise one raw FIRMS table to NORMALIZED_COLUMNS. Never drops rows."""
    columns = list(raw.columns)
    missing = [c for c in schema.REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise SchemaError(f"{source_file}: missing required column(s) {missing}")
    instrument = detect_instrument(columns, raw, source_file)
    if raw.empty:
        return _empty()

    out = pd.DataFrame(index=raw.index)
    out["platform"] = _platforms(raw, instrument, source_file)
    out["instrument"] = instrument
    out["lat"] = pd.to_numeric(raw["latitude"], errors="raise").astype(float)
    out["lon"] = pd.to_numeric(raw["longitude"], errors="raise").astype(float)
    utc = parse_acq_datetime(raw["acq_date"], raw["acq_time"])
    out["acq_datetime_utc"] = utc.dt.as_unit("us")
    out["local_solar_datetime"] = local_solar_datetime(utc, out["lon"]).dt.as_unit("us")
    out["acq_date"] = utc.dt.date
    out["year"] = utc.dt.year.astype("int32")
    out["daynight"] = raw["daynight"].astype(str).str.strip().str.upper()
    out["confidence_raw"] = raw["confidence"].astype(str).str.strip()
    conf = modis_confidence if instrument == "MODIS" else viirs_confidence
    cls, passes, robust = conf(raw["confidence"])
    out["confidence_class"] = cls
    for col in ("frp", "scan", "track"):
        out[col] = pd.to_numeric(raw[col], errors="coerce").astype(float)
    if "type" in columns:
        out["type"] = pd.to_numeric(raw["type"], errors="coerce").astype("Int8")
    else:
        out["type"] = pd.Series(pd.NA, index=raw.index, dtype="Int8")
    out["version"] = raw["version"].astype(str).str.strip()
    out["processing"] = processing_level(out["version"])
    out["source_file"] = source_file
    out["source_row"] = range(1, len(raw) + 1)
    out["passes_standard"] = (out["processing"] == "standard").fillna(False).astype(bool)
    out["passes_type"] = (out["type"] == schema.TYPE_VEGETATION_FIRE).fillna(False).astype(bool)
    out["passes_conf"] = passes.to_numpy()
    out["passes_conf_robust"] = robust.to_numpy()
    out["in_box"] = in_box(out["lat"], out["lon"], box)
    return out[list(NORMALIZED_COLUMNS)].reset_index(drop=True)


def _empty() -> pd.DataFrame:
    return ARROW_SCHEMA.empty_table().to_pandas()


def normalize_file(path: Path, box: Box = COVERAGE_BOX) -> pd.DataFrame:
    path = Path(path)
    return normalize(read_raw_csv(path), path.name, box)


def filtered_view(
    df: pd.DataFrame,
    *,
    require_standard: bool = True,
    require_type: bool = True,
    robust_confidence: bool = False,
) -> pd.DataFrame:
    """Rows passing the PLAN §4 filters (persistent-hotspot mask is applied in mask.py)."""
    keep = df["in_box"] & (df["passes_conf_robust"] if robust_confidence else df["passes_conf"])
    if require_standard:
        keep &= df["passes_standard"]
    if require_type:
        keep &= df["passes_type"]
    if "is_duplicate" in df.columns:
        keep &= ~df["is_duplicate"]
    return df[keep]


# ---------------------------------------------------------------- write / read


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_record(path: Path, raw: pd.DataFrame, instrument: str, df: pd.DataFrame) -> dict:
    expected = schema.MODIS_COLUMNS if instrument == "MODIS" else schema.VIIRS_COLUMNS
    cols = list(raw.columns)
    return {
        "source_file": path.name,
        "path": str(path),
        "sha256": _sha256(path),
        "instrument": instrument,
        "platforms": sorted(df["platform"].unique().tolist()),
        "n_rows": int(len(df)),
        "columns": cols,
        "missing_expected": [c for c in expected if c not in cols],
        "extra": [c for c in cols if c not in expected],
    }


def _prepare_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not (out_dir / _MARKER).exists():
            raise FileExistsError(
                f"{out_dir} is not empty and was not written by blindspot.ingest; "
                "refusing to clear it. Choose another --out."
            )
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / _MARKER).write_text("written by blindspot.ingest; safe to delete\n")


def ingest_dir(raw_dir: Path, out_dir: Path, box: Box = COVERAGE_BOX) -> dict:
    """Normalise every *.csv under raw_dir and write year × platform Parquet partitions."""
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    files = sorted(p for p in raw_dir.rglob("*.csv") if p.is_file())
    if not files:
        raise FileNotFoundError(f"no .csv files under {raw_dir}")
    _prepare_out_dir(out_dir)
    records, n_rows = [], 0
    for i, path in enumerate(files):
        raw = read_raw_csv(path)
        df = normalize(raw, path.name, box)
        instrument = detect_instrument(list(raw.columns), raw, path.name)
        records.append(_file_record(path, raw, instrument, df))
        n_rows += len(df)
        log.info("ingested %s: %d rows", path.name, len(df))
        if df.empty:
            continue
        table = pa.Table.from_pandas(df, schema=ARROW_SCHEMA, preserve_index=False)
        ds.write_dataset(
            table,
            out_dir,
            format="parquet",
            partitioning=ds.partitioning(
                pa.schema([("year", pa.int32()), ("platform", pa.string())]), flavor="hive"
            ),
            basename_template=f"part-{i:05d}-{{i}}.parquet",
            existing_data_behavior="overwrite_or_ignore",
        )
    summary = {"n_files": len(files), "n_rows": n_rows, "box": box.__dict__, "files": records}
    (out_dir / INGEST_LOG).write_text(json.dumps(summary, indent=2, default=str))
    return summary


_VIEWS_SQL = """
CREATE OR REPLACE VIEW hotspots AS
SELECT *,
       row_number() OVER (
           PARTITION BY platform, acq_datetime_utc, lat, lon
           ORDER BY source_file, source_row
       ) > 1 AS is_duplicate
FROM hotspots_raw;

CREATE OR REPLACE VIEW hotspots_filtered AS
SELECT * FROM hotspots
WHERE passes_standard AND passes_type AND passes_conf AND in_box AND NOT is_duplicate;

-- NRT rows have no `type` field (D-010), so the type filter cannot apply; the
-- persistent-hotspot mask (mask.py) is what removes static sources from NRT.
CREATE OR REPLACE VIEW hotspots_filtered_nrt AS
SELECT * FROM hotspots
WHERE NOT passes_standard AND passes_conf AND in_box AND NOT is_duplicate;
"""


def connect(hotspots_dir: Path, con: duckdb.DuckDBPyConnection | None = None):
    """DuckDB connection with views: hotspots (all rows + is_duplicate), hotspots_filtered."""
    con = con or duckdb.connect()
    pattern = str(Path(hotspots_dir) / "**" / "*.parquet")
    rel = con.read_parquet(pattern, hive_partitioning=True)
    rel.create_view("hotspots_raw", replace=True)
    con.execute(_VIEWS_SQL)
    return con


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--raw", type=Path, default=Path("data/raw/firms"))
    p.add_argument("--out", type=Path, default=Path("data/processed/hotspots"))
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = ingest_dir(args.raw, args.out)
    print(f"ingested {summary['n_files']} files, {summary['n_rows']} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
