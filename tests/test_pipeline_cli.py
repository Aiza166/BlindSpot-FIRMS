"""End-to-end smoke test of the ingest -> mask -> qc CLIs on hand-written fixtures."""

from __future__ import annotations

import json
import shutil

from blindspot import ingest, mask, qc


def test_cli_chain(tmp_path, fixtures_dir):
    raw = tmp_path / "raw" / "modis" / "2015"
    raw.mkdir(parents=True)
    shutil.copy(fixtures_dir / "fixture_modis_country.csv", raw)
    hot = tmp_path / "processed" / "hotspots"
    proc = tmp_path / "processed"
    assert ingest.main(["--raw", str(tmp_path / "raw"), "--out", str(hot)]) == 0
    assert mask.main(["--hotspots", str(hot), "--out", str(proc)]) == 0
    assert (proc / mask.MASK_CELLS_FILE).exists()
    rep = json.loads((proc / mask.MASK_REPORT_FILE).read_text())
    assert rep["parameters"]["grid_deg"] == mask.DEFAULT_GRID_DEG
    md = tmp_path / "QC.md"
    assert (
        qc.main(
            [
                "--hotspots",
                str(hot),
                "--mask-dir",
                str(proc),
                "--json",
                str(proc / "qc.json"),
                "--md",
                str(md),
            ]
        )
        == 0
    )
    report = json.loads((proc / "qc.json").read_text())
    assert report["mask_applied"] is True
    assert all(r["after_mask"] is not None for r in report["counts"])
