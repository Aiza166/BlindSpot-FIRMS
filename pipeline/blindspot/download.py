"""Download FIRMS data: yearly country CSVs (history) and the area API (near-real-time).

Runs on the lead's own computer (this cloud workspace cannot reach FIRMS, D-014).

Yearly country CSVs (standard processing, no key needed):

    python -m blindspot.download --countries Pakistan India --years 2003-2025 \\
        --products modis viirs-snpp viirs-jpss1 --out data/raw/firms

The URL pattern is not documented on a FIRMS page we could read; see docs/DATA_SCHEMA.md.
Override it with --url-template or BLINDSPOT_FIRMS_COUNTRY_URL_TEMPLATE, using the
placeholders {product}, {year}, {country}.

Area API (NRT, needs FIRMS_MAP_KEY in the environment; the key is never logged):

    python -m blindspot.download --area-source VIIRS_NOAA20_NRT \\
        --area-start 2026-11-01 --area-end 2026-11-10 --out data/raw/firms_nrt

Downloads are resumable (HTTP Range on a .part file), skip files that already exist, retry
with exponential backoff, and record URL, size, sha256 and status in manifest.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# ---------------------------------------------------------------- constants

# Best-guess pattern, confirmed only by secondary sources (docs/DATA_SCHEMA.md §3).
DEFAULT_COUNTRY_URL_TEMPLATE = (
    "https://firms.modaps.eosdis.nasa.gov/data/country/{product}/{year}/"
    "{product}_{year}_{country}.csv"
)
URL_TEMPLATE_ENV = "BLINDSPOT_FIRMS_COUNTRY_URL_TEMPLATE"

# Product slugs from https://firms.modaps.eosdis.nasa.gov/country/ (modis, viirs-snpp,
# viirs-jpss1). Years before these are not requested (the satellite had no FIRMS data);
# they are lower bounds, and a 404 for a later year is recorded, not fatal.
PRODUCT_FIRST_YEAR: dict[str, int] = {
    "modis": 2000,  # Terra from Nov 2000
    "viirs-snpp": 2012,  # S-NPP from 20 Jan 2012
    "viirs-jpss1": 2018,  # NOAA-20 standard data; FIRMS FAQ lists 2020, D-015 April 2018
}

# Area API, verified at https://firms.modaps.eosdis.nasa.gov/api/area/
AREA_URL_TEMPLATE = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/{area}/{day_range}"
)
AREA_SOURCES: tuple[str, ...] = (
    "LANDSAT_NRT",
    "MODIS_NRT",
    "MODIS_SP",
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA20_SP",
    "VIIRS_NOAA21_NRT",
    "VIIRS_NOAA21_SP",
    "VIIRS_SNPP_NRT",
    "VIIRS_SNPP_SP",
)
MAX_DAY_RANGE = 5
COVERAGE_AREA = "60,23,80,37"  # west,south,east,north (PLAN.md §3)
MAP_KEY_ENV = "FIRMS_MAP_KEY"
NRT_NOTE = "near-real-time data: provisional"

MANIFEST = "manifest.json"
RETRY_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
NOT_FOUND_STATUSES = frozenset({404, 410})


# ---------------------------------------------------------------- HTTP transport


@dataclass
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: Iterable[bytes] = field(default_factory=list)


Transport = Callable[[str, Mapping[str, str], float], HttpResponse]


def urllib_transport(url: str, headers: Mapping[str, str], timeout: float) -> HttpResponse:
    """Default transport (stdlib). HTTP errors become statuses; network errors raise OSError."""
    if not url.startswith("https://"):
        raise ValueError("only https:// URLs are fetched")
    req = urllib.request.Request(url, headers=dict(headers))  # noqa: S310 - https enforced
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 - https enforced
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp else b""
        return HttpResponse(e.code, dict(e.headers or {}), [body])

    def chunks() -> Iterator[bytes]:
        with resp:
            while chunk := resp.read(1 << 16):
                yield chunk

    return HttpResponse(resp.status, dict(resp.headers), chunks())


# ---------------------------------------------------------------- helpers


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def looks_like_firms_csv(path: Path) -> tuple[bool, str]:
    """True if the first line is a CSV header with latitude and longitude."""
    with Path(path).open("rb") as f:
        head = f.read(4096)
    first = head.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    cols = {c.strip().strip('"').lower() for c in first.split(",")}
    return ({"latitude", "longitude"} <= cols, first[:120])


def _retry_after(headers: Mapping[str, str]) -> float | None:
    for k, v in headers.items():
        if k.lower() == "retry-after":
            try:
                return max(0.0, float(v))
            except ValueError:
                return None
    return None


def parse_years(specs: Iterable[str]) -> list[int]:
    """'2003-2025' and '2010' style specs → sorted unique years."""
    years: set[int] = set()
    for spec in specs:
        if "-" in spec:
            a, b = (int(x) for x in spec.split("-", 1))
            if b < a:
                raise ValueError(f"bad year range {spec!r}")
            years.update(range(a, b + 1))
        else:
            years.add(int(spec))
    return sorted(years)


def country_url(
    product: str, year: int, country: str, template: str = DEFAULT_COUNTRY_URL_TEMPLATE
) -> str:
    for ph in ("{product}", "{year}", "{country}"):
        if ph not in template:
            raise ValueError(f"URL template is missing the {ph} placeholder: {template}")
    return template.format(product=product, year=year, country=urllib.parse.quote(country, safe=""))


# ---------------------------------------------------------------- one file


def download_file(
    url: str,
    dest: Path,
    *,
    transport: Transport | None = None,
    sleep: Callable[[float], None] | None = None,
    retries: int = 5,
    backoff_s: float = 2.0,
    timeout: float = 120.0,
    overwrite: bool = False,
    label: str | None = None,
) -> dict:
    """Fetch url → dest. Returns a manifest entry. `label` replaces url in logs and errors."""
    transport = transport or urllib_transport
    sleep = sleep or time.sleep
    label = label or url
    dest = Path(dest)
    part = dest.with_name(dest.name + ".part")
    entry: dict = {
        "url": url,
        "path": str(dest),
        "status": None,
        "http_status": None,
        "size": None,
        "sha256": None,
        "attempts": 0,
        "error": None,
        "retrieved_at": _now(),
    }

    if dest.exists() and not overwrite:
        valid, _ = looks_like_firms_csv(dest)
        if valid:
            entry.update(
                status="skipped_existing", size=dest.stat().st_size, sha256=sha256_file(dest)
            )
            log.info("skip (exists) %s", label)
            return entry
        log.warning("existing file is not a FIRMS CSV, fetching again: %s", dest)
        dest.unlink()
    elif dest.exists():
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, retries + 1):
        entry["attempts"] = attempt
        headers = {"User-Agent": "blindspot-pipeline/0.1"}
        offset = part.stat().st_size if part.exists() else 0
        if offset:
            headers["Range"] = f"bytes={offset}-"
        wait: float | None = None
        try:
            resp = transport(url, headers, timeout)
            entry["http_status"] = resp.status
            if resp.status in (200, 206):
                mode = "ab" if (resp.status == 206 and offset) else "wb"
                with part.open(mode) as f:
                    for chunk in resp.body:
                        f.write(chunk)
                break
            if resp.status == 416:  # our .part is stale or complete: start again
                part.unlink(missing_ok=True)
                entry["error"] = "HTTP 416, restarting"
            elif resp.status in NOT_FOUND_STATUSES:
                entry.update(status="not_found", error=f"HTTP {resp.status}")
                log.info("not found (HTTP %s): %s", resp.status, label)
                return entry
            elif resp.status in RETRY_STATUSES:
                entry["error"] = f"HTTP {resp.status}"
                wait = _retry_after(resp.headers)
            else:
                entry.update(status="http_error", error=f"HTTP {resp.status}")
                log.error("HTTP %s, not retrying: %s", resp.status, label)
                return entry
        except (OSError, ConnectionError, TimeoutError) as e:  # keep .part for resume
            entry["error"] = f"{type(e).__name__}"
        if attempt < retries:
            delay = wait if wait is not None else backoff_s * 2 ** (attempt - 1)
            log.warning(
                "attempt %d failed (%s), retrying in %.1fs: %s",
                attempt,
                entry["error"],
                delay,
                label,
            )
            sleep(delay)
    else:
        entry["status"] = "failed"
        log.error("giving up after %d attempts (%s): %s", retries, entry["error"], label)
        return entry

    valid, first = looks_like_firms_csv(part)
    if not valid:
        part.unlink(missing_ok=True)
        entry.update(
            status="invalid_content", error=f"response is not a FIRMS CSV (first line: {first!r})"
        )
        log.error("not a FIRMS CSV: %s", label)
        return entry
    part.replace(dest)
    entry.update(
        status="downloaded", error=None, size=dest.stat().st_size, sha256=sha256_file(dest)
    )
    log.info("downloaded %s (%d bytes)", label, entry["size"])
    return entry


# ---------------------------------------------------------------- manifest


def _load_manifest(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"entries": {}}


def _save_manifest(path: Path, manifest: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    tmp.replace(path)


# ---------------------------------------------------------------- country CSVs


def download_country_years(
    countries: Iterable[str],
    years: Iterable[int],
    products: Iterable[str],
    out_dir: Path,
    url_template: str = DEFAULT_COUNTRY_URL_TEMPLATE,
    *,
    transport: Transport | None = None,
    sleep: Callable[[float], None] | None = None,
    retries: int = 5,
    backoff_s: float = 2.0,
) -> list[dict]:
    """Fetch every product × year × country file into out_dir/{product}/{year}/."""
    products, countries, years = list(products), list(countries), list(years)
    unknown = [p for p in products if p not in PRODUCT_FIRST_YEAR]
    if unknown:
        raise ValueError(f"unknown product(s) {unknown}; known: {sorted(PRODUCT_FIRST_YEAR)}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / MANIFEST
    manifest = _load_manifest(manifest_path)
    manifest["url_template"] = url_template
    this_year = dt.date.today().year
    entries: list[dict] = []
    for product in products:
        for year in years:
            for country in countries:
                url = country_url(product, year, country, url_template)
                rel = Path(product) / str(year) / f"{product}_{year}_{country}.csv"
                if year < PRODUCT_FIRST_YEAR[product] or year > this_year:
                    entry = {
                        "url": url,
                        "path": str(out_dir / rel),
                        "status": "skipped_unavailable",
                        "retrieved_at": _now(),
                        "error": f"{product} has no FIRMS data for {year}",
                    }
                else:
                    entry = download_file(
                        url,
                        out_dir / rel,
                        transport=transport,
                        sleep=sleep,
                        retries=retries,
                        backoff_s=backoff_s,
                    )
                entry.update(product=product, year=year, country=country)
                entries.append(entry)
                manifest["entries"][rel.as_posix()] = entry
                manifest["updated_at"] = _now()
                _save_manifest(manifest_path, manifest)
    return entries


# ---------------------------------------------------------------- area API (NRT)


class MapKeyMissing(RuntimeError):
    pass


class AreaApiError(RuntimeError):
    pass


def get_map_key(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    key = (env.get(MAP_KEY_ENV) or "").strip()
    if not key:
        raise MapKeyMissing(
            f"{MAP_KEY_ENV} is not set. Put it in .env (never in git) and export it, "
            "e.g. `set -a; . ./.env; set +a`."
        )
    return key


def redact(text: str, key: str) -> str:
    return text.replace(key, "[MAP_KEY]") if key else text


class RateLimiter:
    """Sliding-window budget of area-API transactions plus a minimum gap between calls.

    FIRMS documents a per-key transaction budget per 10 minutes (DATA_SCHEMA.md §4);
    the default stays below it. Cost of a call = its day_range.
    """

    def __init__(
        self,
        max_cost: int = 4000,
        window_s: float = 600.0,
        min_interval_s: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.max_cost, self.window_s, self.min_interval_s = max_cost, window_s, min_interval_s
        self.clock, self.sleep = clock, sleep
        self._spent: deque[tuple[float, int]] = deque()
        self._last: float | None = None

    def _expire(self, now: float) -> None:
        while self._spent and self._spent[0][0] <= now - self.window_s:
            self._spent.popleft()

    def acquire(self, cost: int = 1) -> None:
        if cost > self.max_cost:
            raise ValueError("cost exceeds the whole budget")
        now = self.clock()
        if self._last is not None and now - self._last < self.min_interval_s:
            self.sleep(self.min_interval_s - (now - self._last))
            now = self.clock()
        self._expire(now)
        while sum(c for _, c in self._spent) + cost > self.max_cost:
            self.sleep(self._spent[0][0] + self.window_s - now)
            now = self.clock()
            self._expire(now)
        self._spent.append((now, cost))
        self._last = now


def date_windows(start: dt.date, end: dt.date) -> list[tuple[dt.date, int]]:
    """Split [start, end] (inclusive) into (first_day, day_range ≤ 5) windows."""
    if end < start:
        raise ValueError("end before start")
    out, d = [], start
    while d <= end:
        n = min(MAX_DAY_RANGE, (end - d).days + 1)
        out.append((d, n))
        d += dt.timedelta(days=n)
    return out


def fetch_area(
    source: str,
    *,
    out_path: Path,
    area: str = COVERAGE_AREA,
    day_range: int = 1,
    date: dt.date | None = None,
    env: Mapping[str, str] | None = None,
    transport: Transport | None = None,
    sleep: Callable[[float], None] | None = None,
    limiter: RateLimiter | None = None,
    retries: int = 4,
) -> dict:
    """One area-API call: data for [date, date + day_range - 1], or the latest days if no date.

    The returned record never contains the key or the URL.
    """
    if source not in AREA_SOURCES:
        raise ValueError(f"unknown source {source!r}; known: {AREA_SOURCES}")
    if not 1 <= int(day_range) <= MAX_DAY_RANGE:
        raise ValueError(f"day_range must be 1..{MAX_DAY_RANGE} (FIRMS limit)")
    key = get_map_key(env)
    url = AREA_URL_TEMPLATE.format(key=key, source=source, area=area, day_range=int(day_range))
    if date is not None:
        url += f"/{date.isoformat()}"
    label = f"area {source} {area} {day_range}d {date or 'latest'}"
    (limiter or RateLimiter()).acquire(int(day_range))
    entry = download_file(
        url,
        Path(out_path),
        transport=transport,
        sleep=sleep,
        retries=retries,
        overwrite=True,
        label=label,
    )
    if entry["status"] != "downloaded":
        raise AreaApiError(redact(f"{label}: {entry['status']} ({entry['error']})", key))
    with Path(out_path).open("rb") as f:
        n_rows = max(0, sum(1 for _ in f) - 1)
    return {
        "source": source,
        "area": area,
        "day_range": int(day_range),
        "date": date.isoformat() if date else None,
        "path": str(out_path),
        "status": entry["status"],
        "n_rows": n_rows,
        "size": entry["size"],
        "sha256": entry["sha256"],
        "retrieved_at": entry["retrieved_at"],
        "note": NRT_NOTE,
    }


def fetch_area_range(
    source: str,
    start: dt.date,
    end: dt.date,
    out_dir: Path,
    **kwargs,
) -> list[dict]:
    """Fetch [start, end] in ≤5-day windows; writes a manifest without URLs or keys."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    limiter = kwargs.pop("limiter", None) or RateLimiter()
    results = []
    for first, n in date_windows(start, end):
        path = out_dir / f"{source}_{first.isoformat()}_{n}d.csv"
        results.append(
            fetch_area(source, out_path=path, day_range=n, date=first, limiter=limiter, **kwargs)
        )
    _save_manifest(
        out_dir / MANIFEST,
        {
            "note": NRT_NOTE,
            "updated_at": _now(),
            "entries": {Path(r["path"]).name: r for r in results},
        },
    )
    return results


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--countries", nargs="+", help="FIRMS country names, e.g. Pakistan India")
    p.add_argument("--years", nargs="+", default=["2003-2025"], help="e.g. 2003-2025 2026")
    p.add_argument(
        "--products",
        nargs="+",
        default=["modis", "viirs-snpp", "viirs-jpss1"],
        choices=sorted(PRODUCT_FIRST_YEAR),
    )
    p.add_argument("--out", type=Path, default=Path("data/raw/firms"))
    p.add_argument(
        "--url-template", default=os.environ.get(URL_TEMPLATE_ENV, DEFAULT_COUNTRY_URL_TEMPLATE)
    )
    p.add_argument("--retries", type=int, default=5)
    p.add_argument("--area-source", choices=AREA_SOURCES, help="area API mode (needs MAP_KEY)")
    p.add_argument("--area-start", type=dt.date.fromisoformat)
    p.add_argument("--area-end", type=dt.date.fromisoformat)
    p.add_argument("--area", default=COVERAGE_AREA, help="west,south,east,north")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s"
    )

    if args.area_source:
        if not (args.area_start and args.area_end):
            p.error("--area-source needs --area-start and --area-end")
        try:
            res = fetch_area_range(
                args.area_source,
                args.area_start,
                args.area_end,
                args.out,
                area=args.area,
                retries=args.retries,
            )
        except (MapKeyMissing, AreaApiError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"{len(res)} area file(s) -> {args.out} ({NRT_NOTE})")
        return 0

    if not args.countries:
        p.error("--countries is required (or use --area-source)")
    entries = download_country_years(
        args.countries,
        parse_years(args.years),
        args.products,
        args.out,
        args.url_template,
        retries=args.retries,
        sleep=time.sleep,
    )
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["status"]] = counts.get(e["status"], 0) + 1
    print("download summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"manifest: {args.out / MANIFEST}")
    got = counts.get("downloaded", 0) + counts.get("skipped_existing", 0)
    if got == 0:
        print(
            "error: no file was downloaded. The yearly country CSV URL pattern is not "
            "officially documented and may have changed. Open "
            "https://firms.modaps.eosdis.nasa.gov/country/, copy one file link, and pass "
            "the pattern with --url-template (placeholders {product}, {year}, {country}) "
            f"or set {URL_TEMPLATE_ENV}.",
            file=sys.stderr,
        )
        return 2
    return (
        1
        if (counts.get("failed") or counts.get("invalid_content") or counts.get("http_error"))
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
