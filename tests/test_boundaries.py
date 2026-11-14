"""Tests for blindspot.boundaries and blindspot.regions.

TEST FIXTURES ONLY: the index rows and polygons below are hand-written squares and invented
IDs, not geoBoundaries data.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from blindspot import boundaries, regions
from blindspot.download import HttpResponse

INDEX = (
    "boundaryID,boundaryName,boundaryISO,boundaryYearRepresented,boundaryType,"
    "boundarySource,boundaryLicense,licenseDetail,licenseSource,staticDownloadLink\n"
    '"IND-ADM0-1","India","IND","2011","ADM1","Src0","Lic0","","ls0",'
    '"https://github.com/o/r/raw/abc1234/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1-all.zip"\n'
    '"IND-ADM1-2","India","IND","2011","ADM1","SrcIN","CC BY 2.5 IN","","ls1",'
    '"https://github.com/o/r/raw/abc1234/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1-all.zip"\n'
    '"PAK-ADM1-3","Pakistan","PAK","2019","ADM1","SrcPK","Public Domain","","ls2",'
    '"https://github.com/o/r/raw/abc1234/releaseData/gbOpen/PAK/ADM1/geoBoundaries-PAK-ADM1-all.zip"\n'
)


def _square(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def _fc(features):
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": p, "geometry": g} for p, g in features],
    }


def test_index_row_skips_mislabelled_adm0_row(tmp_path):
    p = tmp_path / "index.csv"
    p.write_text(INDEX)
    row = boundaries.index_row(p, "IND", "ADM1")
    assert row["boundaryID"] == "IND-ADM1-2"
    assert row["boundaryLicense"] == "CC BY 2.5 IN"
    url = boundaries.geojson_url(row)
    assert url.endswith("/raw/abc1234/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1.geojson")
    with pytest.raises(LookupError):
        boundaries.index_row(p, "PAK", "ADM2")


def test_lfs_pointer_is_rejected():
    assert boundaries.is_lfs_pointer(b"version https://git-lfs.github.com/spec/v1\noid sha256:ab")
    assert not boundaries.is_lfs_pointer(b'{"type": "FeatureCollection"}')


def test_download_records_licence_and_refuses_lfs_pointer(tmp_path):
    index = tmp_path / "index.csv"
    index.write_text(INDEX)
    good = json.dumps(_fc([({"shapeName": "Punjab", "shapeID": "X"}, _square(0, 0, 1, 1))]))
    row_pk = boundaries.index_row(index, "PAK", "ADM1")
    row_in = boundaries.index_row(index, "IND", "ADM1")

    def transport(url, headers, timeout):
        if url == boundaries.geojson_url(row_pk):
            return HttpResponse(200, {}, [good.encode()])
        if url == boundaries.geojson_url(row_in):
            return HttpResponse(200, {}, [b"version https://git-lfs.github.com/spec/v1\n"])
        return HttpResponse(404, {}, [b""])

    manifest = boundaries.download_all(
        tmp_path / "out", [("PAK", "ADM1"), ("IND", "ADM1")], index, transport=transport
    )
    pk = manifest["files"]["PAK-ADM1"]
    assert pk["status"] == "ok"
    assert pk["licence"] == "Public Domain"
    assert pk["boundary_id"] == "PAK-ADM1-3"
    assert len(pk["sha256"]) == 64
    assert manifest["files"]["IND-ADM1"]["status"] == "lfs_pointer"
    assert not (tmp_path / "out" / "geoBoundaries-IND-ADM1.geojson").exists()


@pytest.fixture
def bdir(tmp_path):
    """Two 'countries'. PAK: Punjab [0,1]x[0,1], Sindh [0,1]x[-1,0].
    IND: Punjab [1,2]x[0,1] (shares the edge x=1 with PK Punjab), Haryana [1,2]x[-1,0].
    ADM2: one district per province, same squares, plus an overlapping IND district."""
    d = tmp_path / "b"
    d.mkdir()
    feats = {
        ("PAK", "ADM1"): [
            ({"shapeName": "Punjab", "shapeID": "PK1"}, _square(0, 0, 1, 1)),
            ({"shapeName": "Sindh", "shapeID": "PK2"}, _square(0, -1, 1, 0)),
        ],
        ("IND", "ADM1"): [
            ({"shapeName": " punjab ", "shapeID": "IN1"}, _square(1, 0, 2, 1)),
            ({"shapeName": "Haryana", "shapeID": "IN2"}, _square(1, -1, 2, 0)),
        ],
        ("PAK", "ADM2"): [
            ({"shapeName": "Lahore", "shapeID": "PKD1"}, _square(0, 0, 1, 1)),
        ],
        ("IND", "ADM2"): [
            ({"shapeName": "Amritsar", "shapeID": "IND1"}, _square(1, 0, 2, 1)),
            ({"shapeName": "Overlap", "shapeID": "IND9"}, _square(0.5, 0, 1.5, 1)),
        ],
    }
    for (iso, adm), f in feats.items():
        (d / boundaries.geojson_name(iso, adm)).write_text(json.dumps(_fc(f)))
    return d


def test_find_punjab_by_name(bdir):
    shapes = boundaries.load_shapes(bdir, [("PAK", "ADM1"), ("IND", "ADM1")])
    assert boundaries.find_shape(shapes, "PAK", "ADM1", "Punjab").shape_id == "PK1"
    assert boundaries.find_shape(shapes, "IND", "ADM1", "Punjab").shape_id == "IN1"
    with pytest.raises(LookupError):
        boundaries.find_shape(shapes, "PAK", "ADM1", "Balochistan")


def test_assign_points_long_table_and_calibration_regions(bdir):
    shapes = boundaries.load_shapes(bdir, boundaries.DEFAULT_SETS)
    pts = pd.DataFrame(
        {
            "lat": [0.5, 0.5, -0.5, 0.5, 5.0],
            "lon": [0.25, 1.75, 0.5, 1.0, 5.0],  # PK Punjab, IN Punjab, Sindh, on the edge, none
        }
    )
    out, meta = regions.assign_points(pts, shapes)
    calib = out[out.level == "CALIB"]

    def ids(lat, lon, level):
        sel = out[(out.lat == lat) & (out.lon == lon) & (out.level == level)]
        return sorted(sel.shape_id)

    assert ids(0.5, 0.25, "CALIB") == ["PK_Punjab"]
    assert ids(0.5, 1.75, "CALIB") == ["IN_Punjab"]
    assert ids(-0.5, 0.5, "CALIB") == ["rest_of_box"]
    assert ids(0.5, 1.0, "CALIB") == ["IN_Punjab", "PK_Punjab"]  # on the shared edge: both
    assert ids(5.0, 5.0, "CALIB") == ["rest_of_box"]
    assert ids(0.5, 0.25, "ADM2") == ["PKD1"]
    assert ids(0.5, 1.75, "ADM2") == ["IND1"]
    assert ids(0.5, 1.0, "ADM2") == ["IND1", "IND9", "PKD1"]
    assert ids(-0.5, 0.5, "ADM1") == ["PK2"]
    assert meta["pk_punjab_shape_id"] == "PK1"
    assert meta["in_punjab_shape_id"] == "IN1"
    assert meta["n_points_in_both_punjabs"] == 1
    assert set(calib.shape_id) <= set(regions.CALIB_REGIONS)
