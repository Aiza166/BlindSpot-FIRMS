"""Tests for blindspot.download. HTTP is mocked: no network, no real FIRMS data."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging

import pytest

from blindspot import download
from blindspot.download import HttpResponse

CSV = (
    b"latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,"
    b"confidence,version,bright_ti5,frp,daynight,type\n"
    b"30.1,75.0,340.5,0.4,0.37,2016-10-20,0815,N,VIIRS,n,2,295.1,5.2,D,0\n"
)
FAKE_KEY = "0123456789abcdef0123456789abcdef"  # test value, not a real key


class FakeTransport:
    """Replays queued responses per URL and records every request."""

    def __init__(self, script: dict[str, list]):
        self.script = {k: list(v) for k, v in script.items()}
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url, headers, timeout):
        self.calls.append((url, dict(headers)))
        queue = self.script.get(url)
        if not queue:
            return HttpResponse(404, {}, iter([b"not found"]))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(body: bytes = CSV, status: int = 200, headers=None) -> HttpResponse:
    return HttpResponse(
        status, headers or {}, iter([body[: len(body) // 2], body[len(body) // 2 :]])
    )


def no_sleep(_s: float) -> None:
    return None


URL = "https://example.test/data/country/viirs-snpp/2016/viirs-snpp_2016_Pakistan.csv"


# ---------- URL building ----------


def test_country_url_default_template():
    assert download.country_url("modis", 2010, "Pakistan") == (
        "https://firms.modaps.eosdis.nasa.gov/data/country/modis/2010/modis_2010_Pakistan.csv"
    )


def test_country_url_custom_template_and_quoting():
    t = "https://mirror.test/{product}/{year}/{product}_{year}_{country}.csv"
    assert download.country_url("viirs-snpp", 2020, "Sri Lanka", t) == (
        "https://mirror.test/viirs-snpp/2020/viirs-snpp_2020_Sri%20Lanka.csv"
    )


def test_bad_template_rejected():
    with pytest.raises(ValueError, match="placeholder"):
        download.country_url("modis", 2010, "Pakistan", "https://x.test/{product}.csv")


def test_parse_years():
    assert download.parse_years(["2003-2005", "2010"]) == [2003, 2004, 2005, 2010]
    with pytest.raises(ValueError):
        download.parse_years(["2005-2003"])


# ---------- single file ----------


def test_download_writes_file_and_hash(tmp_path):
    t = FakeTransport({URL: [ok()]})
    dest = tmp_path / "f.csv"
    e = download.download_file(URL, dest, transport=t, sleep=no_sleep)
    assert e["status"] == "downloaded"
    assert dest.read_bytes() == CSV
    assert e["size"] == len(CSV)
    assert e["sha256"] == hashlib.sha256(CSV).hexdigest()
    assert not (tmp_path / "f.csv.part").exists()


def test_existing_file_is_skipped_without_request(tmp_path):
    dest = tmp_path / "f.csv"
    dest.write_bytes(CSV)
    t = FakeTransport({URL: [ok()]})
    e = download.download_file(URL, dest, transport=t, sleep=no_sleep)
    assert e["status"] == "skipped_existing"
    assert t.calls == []
    assert e["sha256"] == hashlib.sha256(CSV).hexdigest()


def test_partial_file_is_resumed_with_range(tmp_path):
    dest = tmp_path / "f.csv"
    part = tmp_path / "f.csv.part"
    part.write_bytes(CSV[:40])
    t = FakeTransport({URL: [HttpResponse(206, {}, iter([CSV[40:]]))]})
    e = download.download_file(URL, dest, transport=t, sleep=no_sleep)
    assert t.calls[0][1]["Range"] == "bytes=40-"
    assert e["status"] == "downloaded"
    assert dest.read_bytes() == CSV


def test_partial_file_restarted_when_server_ignores_range(tmp_path):
    dest = tmp_path / "f.csv"
    (tmp_path / "f.csv.part").write_bytes(b"garbage-old-bytes")
    t = FakeTransport({URL: [ok()]})  # 200 = full body, not a continuation
    download.download_file(URL, dest, transport=t, sleep=no_sleep)
    assert dest.read_bytes() == CSV


def test_retries_with_backoff_then_succeeds(tmp_path):
    slept: list[float] = []
    t = FakeTransport({URL: [HttpResponse(503, {}, iter([b""])), ConnectionError("reset"), ok()]})
    e = download.download_file(
        URL, tmp_path / "f.csv", transport=t, sleep=slept.append, backoff_s=2.0
    )
    assert e["status"] == "downloaded"
    assert e["attempts"] == 3
    assert slept == [2.0, 4.0]


def test_retry_after_header_respected(tmp_path):
    slept: list[float] = []
    t = FakeTransport({URL: [HttpResponse(429, {"Retry-After": "7"}, iter([b""])), ok()]})
    download.download_file(URL, tmp_path / "f.csv", transport=t, sleep=slept.append)
    assert slept == [7.0]


def test_gives_up_after_max_retries(tmp_path):
    t = FakeTransport({URL: [HttpResponse(500, {}, iter([b""]))] * 10})
    e = download.download_file(URL, tmp_path / "f.csv", transport=t, sleep=no_sleep, retries=3)
    assert e["status"] == "failed"
    assert len(t.calls) == 3
    assert not (tmp_path / "f.csv").exists()


def test_404_is_not_found_and_not_retried(tmp_path):
    t = FakeTransport({})
    e = download.download_file(URL, tmp_path / "f.csv", transport=t, sleep=no_sleep)
    assert e["status"] == "not_found"
    assert len(t.calls) == 1


def test_html_instead_of_csv_is_rejected(tmp_path):
    t = FakeTransport({URL: [ok(b"<!DOCTYPE html><html>Error</html>")]})
    e = download.download_file(URL, tmp_path / "f.csv", transport=t, sleep=no_sleep)
    assert e["status"] == "invalid_content"
    assert "not a FIRMS CSV" in e["error"]
    assert not (tmp_path / "f.csv").exists()


# ---------- batch + manifest ----------


def test_download_country_years_and_manifest(tmp_path):
    tmpl = "https://example.test/data/country/{product}/{year}/{product}_{year}_{country}.csv"
    good = tmpl.format(product="viirs-snpp", year=2016, country="Pakistan")
    t = FakeTransport({good: [ok()]})
    entries = download.download_country_years(
        countries=["Pakistan"],
        years=[2011, 2016, 2017],
        products=["viirs-snpp"],
        out_dir=tmp_path,
        url_template=tmpl,
        transport=t,
        sleep=no_sleep,
    )
    by_year = {e["year"]: e["status"] for e in entries}
    # 2011 precedes S-NPP's first FIRMS year: skipped without a request.
    assert by_year == {2011: "skipped_unavailable", 2016: "downloaded", 2017: "not_found"}
    assert [c[0] for c in t.calls] == [
        good,
        tmpl.format(product="viirs-snpp", year=2017, country="Pakistan"),
    ]
    assert (tmp_path / "viirs-snpp" / "2016" / "viirs-snpp_2016_Pakistan.csv").exists()
    manifest = json.loads((tmp_path / download.MANIFEST).read_text())
    rec = manifest["entries"]["viirs-snpp/2016/viirs-snpp_2016_Pakistan.csv"]
    assert rec["url"] == good
    assert rec["status"] == "downloaded"
    assert rec["sha256"] == hashlib.sha256(CSV).hexdigest()
    assert manifest["url_template"] == tmpl

    # Second run: the file exists, so nothing is fetched again.
    t2 = FakeTransport({})
    entries2 = download.download_country_years(
        ["Pakistan"], [2016], ["viirs-snpp"], tmp_path, tmpl, transport=t2, sleep=no_sleep
    )
    assert entries2[0]["status"] == "skipped_existing"
    assert t2.calls == []


def test_unknown_product_rejected(tmp_path):
    with pytest.raises(ValueError, match="product"):
        download.download_country_years(["Pakistan"], [2016], ["modis-c5"], tmp_path)


def test_cli_returns_2_when_everything_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(download, "urllib_transport", FakeTransport({}))
    monkeypatch.setattr(download.time, "sleep", no_sleep)
    rc = download.main(
        [
            "--countries",
            "Pakistan",
            "--years",
            "2016",
            "--products",
            "viirs-snpp",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 2
    assert "--url-template" in capsys.readouterr().err


# ---------- area API (NRT) ----------


def test_map_key_read_from_env_only():
    with pytest.raises(download.MapKeyMissing):
        download.get_map_key({})
    assert download.get_map_key({"FIRMS_MAP_KEY": f" {FAKE_KEY} "}) == FAKE_KEY


def test_area_day_range_and_source_validated(tmp_path):
    env = {"FIRMS_MAP_KEY": FAKE_KEY}
    with pytest.raises(ValueError, match="day_range"):
        download.fetch_area("VIIRS_NOAA20_NRT", day_range=6, out_path=tmp_path / "a.csv", env=env)
    with pytest.raises(ValueError, match="source"):
        download.fetch_area("VIIRS_X", out_path=tmp_path / "a.csv", env=env)


def test_area_url_and_key_never_logged(tmp_path, caplog):
    env = {"FIRMS_MAP_KEY": FAKE_KEY}
    expected = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FAKE_KEY}/VIIRS_NOAA20_NRT/"
        "60,23,80,37/5/2026-10-25"
    )
    t = FakeTransport({expected: [ok()]})
    with caplog.at_level(logging.DEBUG):
        res = download.fetch_area(
            "VIIRS_NOAA20_NRT",
            day_range=5,
            date=dt.date(2026, 10, 25),
            out_path=tmp_path / "a.csv",
            env=env,
            transport=t,
            sleep=no_sleep,
            limiter=download.RateLimiter(clock=lambda: 0.0, sleep=no_sleep),
        )
    assert t.calls[0][0] == expected
    assert res["status"] == "downloaded"
    assert FAKE_KEY not in caplog.text
    assert FAKE_KEY not in json.dumps(res)
    assert "provisional" in res["note"]


def test_area_error_text_is_redacted(tmp_path):
    env = {"FIRMS_MAP_KEY": FAKE_KEY}
    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FAKE_KEY}/VIIRS_NOAA20_NRT/"
        "60,23,80,37/1"
    )
    t = FakeTransport({url: [ok(f"Invalid MAP_KEY {FAKE_KEY}.".encode())]})
    with pytest.raises(download.AreaApiError) as err:
        download.fetch_area(
            "VIIRS_NOAA20_NRT",
            day_range=1,
            out_path=tmp_path / "a.csv",
            env=env,
            transport=t,
            sleep=no_sleep,
            limiter=download.RateLimiter(clock=lambda: 0.0, sleep=no_sleep),
        )
    assert FAKE_KEY not in str(err.value)
    assert "[MAP_KEY]" in str(err.value)


def test_date_windows_never_exceed_five_days():
    w = download.date_windows(dt.date(2026, 10, 1), dt.date(2026, 10, 12))
    assert w == [
        (dt.date(2026, 10, 1), 5),
        (dt.date(2026, 10, 6), 5),
        (dt.date(2026, 10, 11), 2),
    ]
    with pytest.raises(ValueError):
        download.date_windows(dt.date(2026, 10, 2), dt.date(2026, 10, 1))


def test_rate_limiter_waits_when_budget_spent():
    now = [0.0]
    slept: list[float] = []

    def sleep(s):
        slept.append(s)
        now[0] += s

    lim = download.RateLimiter(
        max_cost=10, window_s=600, min_interval_s=0, clock=lambda: now[0], sleep=sleep
    )
    lim.acquire(5)
    lim.acquire(5)
    assert slept == []
    lim.acquire(5)  # budget of 10 spent at t=0 -> wait until t=600
    assert slept == [600.0]
    with pytest.raises(ValueError):
        lim.acquire(11)


def test_rate_limiter_min_interval():
    now = [0.0]
    slept: list[float] = []

    def sleep(s):
        slept.append(s)
        now[0] += s

    lim = download.RateLimiter(min_interval_s=1.5, clock=lambda: now[0], sleep=sleep)
    lim.acquire(1)
    lim.acquire(1)
    assert slept == [1.5]
