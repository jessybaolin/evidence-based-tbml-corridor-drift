"""
Shared library: every helper, constant, and core algorithm used by the pipeline.

ROLE: This file is imported by all the numbered scripts (00-11, 99). It is NOT run on its own
      and writes no files itself — the calling scripts persist whatever these functions return.

"""

from __future__ import annotations

import hashlib
import html
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

# ===== Paths & constants =====
# Project root = the folder that contains src/ (this file lives in src/).
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"          # original official inputs
DATA_INTERIM = ROOT / "data" / "interim"  # staged copies (step 02)
DATA_PROCESSED = ROOT / "data" / "processed"  # panel/features/scenarios
DATA_OUTPUTS = ROOT / "data" / "outputs"  # scores/evidence/validation
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
PROMPTS = ROOT / "prompts"
CONFIGS = ROOT / "configs"

# The exact official input file names expected under data/raw/.
BACI_FILE = "baci_hs17_v202601_selected_2017_2024_151110_740311_710812.parquet"
NOTES_FILE = "data_source_notes.json"
WORLD_BANK_FILE = "CMO-Historical-Data-Annual.xlsx"
FATF_2020_FILE = "Trade-Based-Money-Laundering-Trends-and-Developments_2020.pdf"
FATF_2021_FILE = "Trade-Based-Money-Laundering-Risk-Indicators_2021.pdf"
COUNTRY_FILE = "country_codes_V202601.csv"
PRODUCT_FILE = "product_codes_HS17_V202601.csv"
README_SOURCE_FILE = "baci-readme.txt"

# Schema/scope expectations that the validation steps assert against.
BACI_REQUIRED_COLUMNS = ["t", "k", "i", "j", "v", "q"]  # year, HS6, exporter, importer, value, quantity
EXPECTED_YEARS = list(range(2017, 2025))                # 2017..2024 inclusive
EXPECTED_HS6 = ["151110", "740311", "710812"]           # palm oil, copper, gold
# The single non-overclaiming sentence repeated across every output (briefs, reports, dashboard).
BOUNDARY = (
    "This output prioritises an unusual corridor-product pattern for human review. "
    "It does not establish money laundering, misinvoicing, or criminal intent."
)
# Gold benchmark is quoted in USD/troy-ounce; convert to USD/metric-ton to match BACI quantities.
# 1 metric ton = 1,000,000 g; 1 troy ounce = 31.1034768 g.
TROY_OUNCE_GRAMS = 31.1034768
GOLD_TROY_OUNCE_TO_METRIC_TON_FACTOR = 1_000_000.0 / TROY_OUNCE_GRAMS


# ===== Generic I/O helpers =====
def ensure_dirs() -> None:
    # Create all project folders up front so scripts can write freely.
    for path in [DATA_RAW, DATA_INTERIM, DATA_PROCESSED, DATA_OUTPUTS, REPORTS, FIGURES, PROMPTS, CONFIGS]:
        path.mkdir(parents=True, exist_ok=True)

def utc_now() -> str:
    # Whole-second UTC ISO timestamp (used in JSON reports).
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_file(path: Path) -> str:
    # Stream a file in 1 MB chunks and return its SHA-256 hex digest (for provenance/integrity).
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _json_default(obj: Any) -> Any:
    # Fallback for json.dumps: convert types the stdlib encoder can't handle on its own.
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if obj is pd.NaT:
        return None
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return sorted(obj)
    # Last resort: stringify so report writing never crashes on an unexpected type.
    return str(obj)

def write_json(path: Path, payload: Any) -> None:
    # Write pretty, key-sorted JSON (deterministic output), creating parent dirs as needed.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# ===== Source loading & validation =====
def get_raw_path(filename: str) -> Path:
    # Resolve a file under data/raw/. If it isn't there but a copy exists in /mnt/data (the
    # original upload location), copy it in. Raise a clear error if it is genuinely missing.
    path = DATA_RAW / filename
    if not path.exists():
        fallback = Path("/mnt/data") / filename
        if fallback.exists():
            DATA_RAW.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fallback, path)
    if not path.exists():
        raise FileNotFoundError(f"Required input file is missing: {path}")
    return path


def input_inventory() -> pd.DataFrame:
    # Build a table of every declared input file with its size and SHA-256 hash (the chain of
    # custody used by 01_verify_sources.py).
    names = [
        BACI_FILE, NOTES_FILE, WORLD_BANK_FILE, FATF_2020_FILE, FATF_2021_FILE,
        COUNTRY_FILE, PRODUCT_FILE, README_SOURCE_FILE,
    ]
    rows = []
    for name in names:
        path = get_raw_path(name)
        rows.append({
            "file_name": name,
            "relpath": str(path.relative_to(ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return pd.DataFrame(rows)


def read_baci_raw(path: Path | None = None) -> pd.DataFrame:
    # Load the BACI parquet, enforce the 6 official columns, and normalize types.
    path = path or get_raw_path(BACI_FILE)
    frame = pd.read_parquet(path)
    missing = set(BACI_REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"BACI Parquet is missing official columns: {sorted(missing)}")
    frame = frame[BACI_REQUIRED_COLUMNS].copy()
    # Keep HS6 as text. If a reader turned k into a number, zero-fill restores six-character codes.
    frame["k"] = frame["k"].astype("string").str.strip().str.zfill(6)
    # year/exporter/importer are integer codes; value/quantity are numeric (coerce bad cells to NaN).
    for col in ["t", "i", "j"]:
        frame[col] = pd.to_numeric(frame[col], errors="raise").astype("int64")
    frame["v"] = pd.to_numeric(frame["v"], errors="coerce")
    frame["q"] = pd.to_numeric(frame["q"], errors="coerce")
    return frame


def validate_baci_against_notes(frame: pd.DataFrame, notes: dict[str, Any]) -> dict[str, Any]:
    # Cross-check the actual BACI rows against the provenance notes: columns present, exact
    # years/HS6, and that the per-HS6 / per-year / total row counts all match what the notes claim.
    actual_by_hs6 = {k: int(v) for k, v in frame["k"].value_counts().sort_index().items()}
    actual_by_year = {str(int(k)): int(v) for k, v in frame["t"].value_counts().sort_index().items()}
    notes_counts = notes.get("record_counts", {})
    return {
        "required_columns_present": all(c in frame.columns for c in BACI_REQUIRED_COLUMNS),
        "k_dtype_after_normalization": str(frame["k"].dtype),
        "years_exact": sorted(frame["t"].unique().tolist()) == EXPECTED_YEARS,
        "hs6_exact": sorted(frame["k"].unique().tolist()) == sorted(EXPECTED_HS6),
        "row_count_nonzero": len(frame) > 0,
        "row_count": int(len(frame)),
        "notes_total_records": int(notes_counts.get("total_records", -1)),
        "row_count_matches_notes": int(len(frame)) == int(notes_counts.get("total_records", -1)),
        "by_hs6_matches_notes": actual_by_hs6 == notes_counts.get("by_hs6_code", {}),
        "by_year_matches_notes": actual_by_year == notes_counts.get("by_year", {}),
        "actual_by_hs6": actual_by_hs6,
        "actual_by_year": actual_by_year,
        "preview": frame.head(8).astype({"k": "string"}).to_dict(orient="records"),
    }


def source_notes_check(notes: dict[str, Any]) -> dict[str, Any]:
    # Confirm the notes themselves assert the right provenance facts (official-derived CEPII BACI,
    # HS17, release 202601, the right years/HS6, no derived fields, not synthetic).
    text = json.dumps(notes, sort_keys=True).casefold()
    return {
        "official_derived_cepii_baci": "official-derived" in text and "cepii baci" in text,
        "hs17": notes.get("hs_revision") == "HS17",
        "release_202601": str(notes.get("baci_release")) == "202601",
        "years_2017_2024": notes.get("years_included") == EXPECTED_YEARS,
        "selected_hs6_families": sorted(notes.get("hs6_codes_included", [])) == sorted(EXPECTED_HS6),
        "retained_fields": notes.get("columns_retained") == BACI_REQUIRED_COLUMNS,
        "no_derived_fields_added": "no derived fields" in text,
        "not_synthetic": bool(notes.get("not_synthetic")) is True,
    }

def extract_worldbank_benchmarks():

    return 0

