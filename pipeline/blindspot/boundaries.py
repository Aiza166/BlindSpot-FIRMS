"""geoBoundaries ADM1/ADM2 for PAK and IND: download and load (docs/DECISIONS.md D-025).

The official index `releaseData/geoBoundariesOpen-meta.csv` (not stored in Git LFS) gives, for
each boundary set, the licence, source and a static download link pinned to one repo commit.
We take the GeoJSON from that same commit. The geometry files are Git LFS objects: a response
that is an LFS pointer instead of GeoJSON is refused, never saved.

    python -m blindspot.boundaries --out data/raw/boundaries
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
from dataclasses import dataclass
from pathlib import Path

from shapely.geometry import shape as to_geometry
from shapely.geometry.base import BaseGeometry

from blindspot.download import Transport, sha256_file, urllib_transport

INDEX_URL = (
    "https://raw.githubusercontent.com/wmgeolab/geoBoundaries/main/releaseData/"
    "geoBoundariesOpen-meta.csv"
)
INDEX_FILE = "geoBoundariesOpen-meta.csv"
MANIFEST = "manifest.json"
DEFAULT_SETS: tuple[tuple[str, str], ...] = (
    ("PAK", "ADM1"),
    ("IND", "ADM1"),
    ("PAK", "ADM2"),
    ("IND", "ADM2"),
)
_LFS_MAGIC = b"version https://git-lfs.github.com/spec/v1"


def geojson_name(iso: str, adm: str) -> str:
    return f"geoBoundaries-{iso}-{adm}.geojson"


def is_lfs_pointer(head: bytes) -> bool:
    return head.lstrip().startswith(_LFS_MAGIC)


def index_row(index_path: Path, iso: str, adm: str) -> dict[str, str]:
    """The index row for one boundary set, chosen by its boundaryID prefix `{ISO}-{ADM}-`.

    The index also contains rows whose boundaryType disagrees with their ID (e.g. an
    `IND-ADM0-…` row typed ADM1); matching on the ID prefix skips those.
    """
    text = Path(index_path).read_text(encoding="utf-8")
    prefix = f"{iso}-{adm}-"
    rows = [r for r in csv.DictReader(io.StringIO(text)) if r["boundaryID"].startswith(prefix)]
    if len(rows) != 1:
        raise LookupError(f"expected one index row for {prefix}, found {len(rows)}")
    return rows[0]


def geojson_url(row: dict[str, str]) -> str:
    link = row["staticDownloadLink"]
    if not link.endswith("-all.zip"):
        raise ValueError(f"unexpected staticDownloadLink: {link}")
    url = link[: -len("-all.zip")] + ".geojson"
    # Geometry lives in Git LFS; github.com/.../raw/... redirects to the LFS media host.
    # Request the media host directly (same official repo and pinned commit).
    prefix = "https://github.com/wmgeolab/geoBoundaries/raw/"
    if url.startswith(prefix):
        url = (
            "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/" + url[len(prefix) :]
        )
    return url


def _fetch(url: str, transport: Transport, timeout: float = 120.0) -> tuple[int, bytes]:
    resp = transport(url, {"User-Agent": "blindspot-pipeline"}, timeout)
    return resp.status, b"".join(resp.body)


def download_all(
    out_dir: Path,
    sets: tuple[tuple[str, str], ...] | list[tuple[str, str]] = DEFAULT_SETS,
    index_path: Path | None = None,
    transport: Transport | None = None,
) -> dict:
    """Download each boundary set; write manifest.json with URL, licence, source, sha256."""
    transport = transport or urllib_transport
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if index_path is None:
        status, body = _fetch(INDEX_URL, transport)
        if status != 200:
            raise RuntimeError(f"geoBoundaries index: HTTP {status} from {INDEX_URL}")
        index_path = out_dir / INDEX_FILE
        index_path.write_bytes(body)
    manifest: dict = {
        "index_url": INDEX_URL,
        "index_sha256": sha256_file(index_path),
        "retrieved": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "files": {},
    }
    for iso, adm in sets:
        row = index_row(index_path, iso, adm)
        url = geojson_url(row)
        rec = {
            "url": url,
            "boundary_id": row["boundaryID"],
            "year_represented": row.get("boundaryYearRepresented", ""),
            "source": row.get("boundarySource", ""),
            "licence": row.get("boundaryLicense", ""),
            "licence_detail": row.get("licenseDetail", ""),
            "licence_source": row.get("licenseSource", ""),
        }
        target = out_dir / geojson_name(iso, adm)
        try:
            status, body = _fetch(url, transport)
        except OSError as e:
            rec["status"] = f"network_error: {e}"
        else:
            if status != 200:
                rec["status"] = f"http_{status}"
            elif is_lfs_pointer(body[:200]):
                rec["status"] = "lfs_pointer"
            else:
                json.loads(body)  # must parse as JSON before it is kept
                target.write_bytes(body)
                rec.update(status="ok", sha256=sha256_file(target), bytes=len(body))
        manifest["files"][f"{iso}-{adm}"] = rec
    (out_dir / MANIFEST).write_text(json.dumps(manifest, indent=2))
    return manifest


@dataclass(frozen=True)
class Shape:
    iso: str
    level: str
    shape_id: str
    name: str
    geometry: BaseGeometry


def load_shapes(
    boundaries_dir: Path, sets: tuple[tuple[str, str], ...] | list[tuple[str, str]] = DEFAULT_SETS
) -> list[Shape]:
    out: list[Shape] = []
    for iso, adm in sets:
        path = Path(boundaries_dir) / geojson_name(iso, adm)
        head = path.read_bytes()[:200]
        if is_lfs_pointer(head):
            raise ValueError(f"{path} is a Git LFS pointer, not GeoJSON; re-run make boundaries")
        fc = json.loads(path.read_text(encoding="utf-8"))
        for f in fc["features"]:
            p = f["properties"]
            out.append(
                Shape(iso, adm, str(p["shapeID"]), str(p["shapeName"]), to_geometry(f["geometry"]))
            )
    return out


def _norm(name: str) -> str:
    return " ".join(name.split()).casefold()


def find_shape(shapes: list[Shape], iso: str, level: str, name: str) -> Shape:
    hits = [s for s in shapes if s.iso == iso and s.level == level and _norm(s.name) == _norm(name)]
    if len(hits) != 1:
        raise LookupError(f"expected one {iso} {level} shape named {name!r}, found {len(hits)}")
    return hits[0]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--out", type=Path, default=Path("data/raw/boundaries"))
    args = p.parse_args(argv)
    manifest = download_all(args.out)
    bad = {k: v["status"] for k, v in manifest["files"].items() if v.get("status") != "ok"}
    for k, v in manifest["files"].items():
        print(f"{k}: {v.get('status')}  licence: {v['licence']}  {v['url']}")
    if bad:
        print(
            "Some boundary files did not download. geoBoundaries geometry is stored in Git LFS; "
            "the host media.githubusercontent.com must be reachable."
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
