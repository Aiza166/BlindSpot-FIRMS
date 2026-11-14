"""FIRMS column lists and value codes, as verified in docs/DATA_SCHEMA.md.

Everything here is a fact about the FIRMS file format, not an analysis choice.
Sources are listed in docs/DATA_SCHEMA.md; keep the two in sync.
"""

from __future__ import annotations

# Expected header of a FIRMS standard-processing CSV (yearly country file / archive).
# Attribute names are verified from the FIRMS layer descriptions; the exact lower-case,
# comma-separated header order is the one FIRMS CSV/API files use (see DATA_SCHEMA.md
# for what is verified and what is not). Matching is case-insensitive and order-free.
MODIS_COLUMNS: tuple[str, ...] = (
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "bright_t31",
    "frp",
    "daynight",
    "type",
)

VIIRS_COLUMNS: tuple[str, ...] = (
    "latitude",
    "longitude",
    "bright_ti4",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "bright_ti5",
    "frp",
    "daynight",
    "type",
)

# Columns the normaliser cannot work without.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "satellite",
    "confidence",
    "version",
    "frp",
    "daynight",
    "scan",
    "track",
)

# Columns that are documented as optional: `type` exists only in standard-processing data
# (FIRMS layer descriptions, "Type*"), `instrument` is not in every distribution.
OPTIONAL_COLUMNS: tuple[str, ...] = ("type", "instrument")

# Web-services aliases for VIIRS brightness (FIRMS VIIRS description: "Bright_ti4 /
# Brightness (in web services)", "Bright_ti5 / Brightness_2 (in web services)").
VIIRS_ALIASES: dict[str, str] = {"brightness": "bright_ti4", "brightness_2": "bright_ti5"}

# Satellite codes. Documented: MODIS A/T; VIIRS N, N20, N21.
# The extra aliases are defensive (spelled-out names, JPSS ids) and are not documented codes.
SATELLITE_TO_PLATFORM: dict[str, str] = {
    "T": "Terra",
    "TERRA": "Terra",
    "A": "Aqua",
    "AQUA": "Aqua",
    "N": "SNPP",
    "NPP": "SNPP",
    "SNPP": "SNPP",
    "S-NPP": "SNPP",
    "SUOMI NPP": "SNPP",
    "N20": "NOAA20",
    "NOAA-20": "NOAA20",
    "NOAA20": "NOAA20",
    "J1": "NOAA20",
    "N21": "NOAA21",
    "NOAA-21": "NOAA21",
    "NOAA21": "NOAA21",
    "J2": "NOAA21",
}

PLATFORM_INSTRUMENT: dict[str, str] = {
    "Terra": "MODIS",
    "Aqua": "MODIS",
    "SNPP": "VIIRS",
    "NOAA20": "VIIRS",
    "NOAA21": "VIIRS",
}

PLATFORMS: tuple[str, ...] = tuple(PLATFORM_INSTRUMENT)

# Filename hints from the FIRMS country product slugs, used only when a VIIRS file's
# `satellite` values are missing.
PRODUCT_TO_PLATFORM: dict[str, str] = {
    "viirs-snpp": "SNPP",
    "viirs-jpss1": "NOAA20",
    "viirs-jpss2": "NOAA21",
}

# VIIRS confidence codes: l/n/h in files and the area API; spelled out in some NRT files.
VIIRS_CONFIDENCE: dict[str, str] = {
    "l": "low",
    "low": "low",
    "n": "nominal",
    "nominal": "nominal",
    "h": "high",
    "high": "high",
}

# FIRMS `type` codes (layer descriptions): 0 presumed vegetation fire, 1 active volcano,
# 2 other static land source, 3 offshore.
TYPE_VEGETATION_FIRE = 0
