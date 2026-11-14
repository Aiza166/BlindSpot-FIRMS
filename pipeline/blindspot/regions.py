"""Assign detections to geoBoundaries ADM1/ADM2 and to the calibration regions (D-025).

Output is a derived table keyed by the exact (lat, lon) of each filtered detection; the raw
hotspot partitions are not touched. Long format, one row per (point, level, shape):

    level  = "ADM1" | "ADM2" | "CALIB"
    CALIB  shape_id in {"PK_Punjab", "IN_Punjab", "rest_of_box"}

A point inside polygons of both countries (geoBoundaries draws each country as it represents
itself) gets one row for each.

    python -m blindspot.regions --hotspots data/processed/hotspots \
        --boundaries data/raw/boundaries --out data/processed/regions
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import box as make_box

from blindspot.boundaries import DEFAULT_SETS, Shape, find_shape, load_shapes

PK_PUNJAB = "PK_Punjab"
IN_PUNJAB = "IN_Punjab"
REST = "rest_of_box"
CALIB_REGIONS = (PK_PUNJAB, IN_PUNJAB, REST)
PUNJAB_NAME = "Punjab"
POINT_REGIONS_FILE = "point_regions.parquet"
SHAPES_FILE = "shapes.parquet"
REGIONS_JSON = "regions.json"
_CHUNK = 1_000_000


def _query(lat: np.ndarray, lon: np.ndarray, shapes: list[Shape]) -> tuple[np.ndarray, np.ndarray]:
    """(point index, shape index) pairs where the point intersects the shape."""
    if not shapes or len(lat) == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
    tree = shapely.STRtree([s.geometry for s in shapes])
    pi, si = [], []
    for start in range(0, len(lat), _CHUNK):
        pts = shapely.points(lon[start : start + _CHUNK], lat[start : start + _CHUNK])
        p, s = tree.query(pts, predicate="intersects")
        pi.append(p + start)
        si.append(s)
    return np.concatenate(pi), np.concatenate(si)


def assign_points(points: pd.DataFrame, shapes: list[Shape]) -> tuple[pd.DataFrame, dict]:
    """Long table (lat, lon, level, shape_iso, shape_id) and a summary dict."""
    pts = points[["lat", "lon"]].drop_duplicates().reset_index(drop=True)
    lat = pts["lat"].to_numpy(dtype=float)
    lon = pts["lon"].to_numpy(dtype=float)
    pk = find_shape(shapes, "PAK", "ADM1", PUNJAB_NAME)
    ind = find_shape(shapes, "IND", "ADM1", PUNJAB_NAME)

    parts = []
    for level in ("ADM1", "ADM2"):
        sub = [s for s in shapes if s.level == level]
        p, s = _query(lat, lon, sub)
        parts.append(
            pd.DataFrame(
                {
                    "lat": lat[p],
                    "lon": lon[p],
                    "level": level,
                    "shape_iso": [sub[i].iso for i in s],
                    "shape_id": [sub[i].shape_id for i in s],
                }
            )
        )
    adm1 = parts[0]
    in_pk = set(map(tuple, adm1.loc[adm1.shape_id == pk.shape_id, ["lat", "lon"]].to_numpy()))
    in_in = set(map(tuple, adm1.loc[adm1.shape_id == ind.shape_id, ["lat", "lon"]].to_numpy()))
    keys = list(zip(lat, lon, strict=True))
    f_pk = np.fromiter((k in in_pk for k in keys), dtype=bool, count=len(keys))
    f_in = np.fromiter((k in in_in for k in keys), dtype=bool, count=len(keys))
    calib = [
        pd.DataFrame(
            {"lat": lat[f_pk], "lon": lon[f_pk], "shape_iso": "PAK", "shape_id": PK_PUNJAB}
        ),
        pd.DataFrame(
            {"lat": lat[f_in], "lon": lon[f_in], "shape_iso": "IND", "shape_id": IN_PUNJAB}
        ),
    ]
    rest = ~(f_pk | f_in)
    calib.append(
        pd.DataFrame({"lat": lat[rest], "lon": lon[rest], "shape_iso": "", "shape_id": REST})
    )
    c = pd.concat(calib, ignore_index=True)
    c["level"] = "CALIB"
    out = pd.concat([*parts, c], ignore_index=True)[
        ["lat", "lon", "level", "shape_iso", "shape_id"]
    ]
    meta = {
        "pk_punjab_shape_id": pk.shape_id,
        "pk_punjab_shape_name": pk.name,
        "in_punjab_shape_id": ind.shape_id,
        "in_punjab_shape_name": ind.name,
        "n_points": int(len(pts)),
        "n_points_pk_punjab": int(f_pk.sum()),
        "n_points_in_punjab": int(f_in.sum()),
        "n_points_in_both_punjabs": int((f_pk & f_in).sum()),
        "n_points_rest_of_box": int(rest.sum()),
        "n_points_no_adm1": int(len(pts) - adm1[["lat", "lon"]].drop_duplicates().shape[0]),
    }
    return out, meta


def shapes_table(shapes: list[Shape], box: tuple[float, float, float, float]) -> pd.DataFrame:
    """One row per shape with the share of its area inside the coverage box (lon/lat degrees)."""
    b = make_box(*box)
    rows = []
    for s in shapes:
        area = s.geometry.area
        rows.append(
            {
                "level": s.level,
                "shape_iso": s.iso,
                "shape_id": s.shape_id,
                "shape_name": s.name,
                "share_area_in_box": float(s.geometry.intersection(b).area / area) if area else 0.0,
            }
        )
    return pd.DataFrame(rows)


def run(hotspots_dir: Path, boundaries_dir: Path, out_dir: Path) -> dict:
    from blindspot import ingest
    from blindspot.ingest import COVERAGE_BOX

    con = ingest.connect(hotspots_dir)
    con.execute("SET enable_progress_bar = false")
    pts = con.execute(
        "SELECT DISTINCT lat, lon FROM ("
        " SELECT lat, lon FROM hotspots_filtered UNION ALL"
        " SELECT lat, lon FROM hotspots_filtered_nrt)"
    ).df()
    shapes = load_shapes(boundaries_dir, DEFAULT_SETS)
    table, meta = assign_points(pts, shapes)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out_dir / POINT_REGIONS_FILE, index=False)
    b = COVERAGE_BOX
    box = (b.lon_min, b.lat_min, b.lon_max, b.lat_max)
    st = shapes_table(shapes, box)
    st.to_parquet(out_dir / SHAPES_FILE, index=False)
    meta["n_shapes"] = {lvl: int((st.level == lvl).sum()) for lvl in ("ADM1", "ADM2")}
    (out_dir / REGIONS_JSON).write_text(json.dumps(meta, indent=2))
    return meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--hotspots", type=Path, default=Path("data/processed/hotspots"))
    p.add_argument("--boundaries", type=Path, default=Path("data/raw/boundaries"))
    p.add_argument("--out", type=Path, default=Path("data/processed/regions"))
    args = p.parse_args(argv)
    meta = run(args.hotspots, args.boundaries, args.out)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
