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

def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")



# ===== Config loaders (thin readers for configs/*.yml) =====
# def project_config() -> dict[str, Any]:
#     # Years, seeds, train/val/test split, top_k, the boundary sentence, etc.
#     return load_yaml(CONFIGS / "project.yml")


def families() -> list[dict[str, Any]]:
    # The three HS6 commodity families and their metadata.
    return load_yaml(CONFIGS / "hs_families.yml")["families"]


def benchmarks_config() -> list[dict[str, Any]]:
    # World Bank benchmark series mapping + unit/conversion info.
    return load_yaml(CONFIGS / "benchmark_series.yml")["benchmarks"]


# def thresholds() -> dict[str, Any]:
#     # Rule weights/reference values, model-selection settings, evidence limits.
#     return load_yaml(CONFIGS / "thresholds.yml")


def benchmark_lookup_by_label() -> dict[str, dict[str, Any]]:
    # Index the benchmark config by its workbook "source_label" (lowercased) so the World Bank
    # parser can find the Palm oil / Copper / Gold columns by name.
    return {str(item["source_label"]).strip().casefold(): item for item in benchmarks_config()}


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
    frame["v"] = pd.to_numeric(frame["v"], errors="coerce") # not triggered
    frame["q"] = pd.to_numeric(frame["q"], errors="coerce") # turn NA values into NaN
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


# ===== World Bank benchmark extraction =====
def extract_worldbank_benchmarks(workbook_path: Path | None = None) -> pd.DataFrame:
    # Parse the World Bank "Pink Sheet" annual workbook into one tidy benchmark row per
    # (commodity, year). The sheet layout is discovered (not hard-coded by cell) so it is robust.
    workbook_path = workbook_path or get_raw_path(WORLD_BANK_FILE)
    workbook = pd.ExcelFile(workbook_path)
    if "Annual Prices (Nominal)" not in workbook.sheet_names:
        raise ValueError(f"Expected Annual Prices (Nominal) sheet; available={workbook.sheet_names}")
    sheet = pd.read_excel(workbook_path, sheet_name="Annual Prices (Nominal)", header=None, engine="openpyxl")
    # Discover commodity names and units rather than hard-coding cell coordinates.
    # Scan the first ~20 rows for the one that contains all three commodity labels (Palm oil/Copper/Gold).
    label_map = benchmark_lookup_by_label()
    commodity_row = None
    commodity_cols: dict[str, int] = {}
    for r in range(min(20, len(sheet))):
        row_values = [str(x).strip().casefold() for x in sheet.iloc[r].tolist()]
        found = {}
        for label in label_map:
            if label in row_values:
                found[label] = row_values.index(label)
        if len(found) == len(label_map):
            commodity_row = r
            commodity_cols = found
            break
    if commodity_row is None:
        raise ValueError("Could not locate Palm oil, Copper, and Gold columns in World Bank annual sheet")
    # The unit string sits directly under the commodity header row.
    unit_row = commodity_row + 1
    # Find the column that holds the years (it must contain all of 2017..2024).
    year_col = None
    for c in range(min(5, sheet.shape[1])):
        years = pd.to_numeric(sheet.iloc[:, c], errors="coerce")
        if set(EXPECTED_YEARS).issubset(set(years.dropna().astype(int).tolist())):
            year_col = c
            break
    if year_col is None:
        raise ValueError("Could not locate year column in World Bank annual sheet")
    # Walk each data row; for years in scope, read each commodity's price and normalize units.
    rows: list[dict[str, Any]] = []
    for row_idx in range(unit_row + 1, len(sheet)):
        year_val = pd.to_numeric(pd.Series([sheet.iat[row_idx, year_col]]), errors="coerce").iat[0]
        if pd.isna(year_val):
            continue
        year = int(year_val)
        if year not in EXPECTED_YEARS:
            continue
        for label, col in commodity_cols.items():
            meta = label_map[label]
            value = pd.to_numeric(pd.Series([sheet.iat[row_idx, col]]), errors="coerce").iat[0]
            if pd.isna(value):
                continue
            # Guard: the workbook's compact unit must match what the config expects for this series.
            unit_compact = str(sheet.iat[unit_row, col]).strip()
            expected_compact = str(meta.get("workbook_unit"))
            if unit_compact != expected_compact:
                raise ValueError(f"World Bank unit mismatch for {meta['source_label']}: {unit_compact} != {expected_compact}")
            price_original = float(value)
            # Only gold needs converting (troy-ounce -> metric-ton); palm oil/copper are already per-ton.
            if str(meta["family_id"]) == "gold_unwrought":
                price_per_mt = price_original * GOLD_TROY_OUNCE_TO_METRIC_TON_FACTOR
            else:
                price_per_mt = price_original
            rows.append({
                "family_id": meta["family_id"],
                "hs6": str(meta["hs6"]),
                "benchmark_series_id": meta["benchmark_series_id"],
                "benchmark_price_original": price_original,     # keep the raw value
                "benchmark_unit_original": meta["original_unit"],
                "benchmark_price_usd_per_metric_ton": float(price_per_mt),  # normalized value
                "benchmark_year": year,
                "benchmark_conversion_method": meta["conversion_method"],
                "benchmark_caveat": meta["caveat"],
                "source_filename": workbook_path.name,
                "source_sheet": "Annual Prices (Nominal)",
                "source_compact_unit": unit_compact,
            })
    result = pd.DataFrame(rows).sort_values(["family_id", "benchmark_year"], kind="mergesort").reset_index(drop=True)
    # Year-over-year log change of the benchmark itself (used later for benchmark-consistency checks).
    result["benchmark_yoy_change"] = result.groupby("family_id", sort=False)["benchmark_price_usd_per_metric_ton"].transform(lambda s: np.log(s / s.shift(1)))
    result["benchmark_yoy_change"] = result["benchmark_yoy_change"].replace([np.inf, -np.inf], np.nan)
    # Sanity check: exactly 3 commodities x 8 years = 24 rows.
    expected_rows = len(EXPECTED_YEARS) * len(EXPECTED_HS6)
    if len(result) != expected_rows:
        raise ValueError(f"Expected {expected_rows} annual benchmark rows; parsed {len(result)}")
    return result


def load_country_codes():
    # Load the BACI numeric -> country code for mapping
    frame = pd.read_csv(get_raw_path(COUNTRY_FILE), dtype={"country_code": "int64", "country_iso3": "string", "country_name": "string"})
    required = ["country_code", "country_name", "country_iso3"]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Country code file missing columns: {sorted(missing)}")
    if frame["country_code"].duplicated().any(): # this column is used for join key. it has to be unique
        raise ValueError("Country code file has duplicate numeric country codes")
    return frame[required] 


def load_product_codes() -> pd.DataFrame:
    # Load the HS code -> description lookup, keeping the code as a zero-padded 6-char string.
    frame = pd.read_csv(get_raw_path(PRODUCT_FILE), dtype={"code": "string", "description": "string"})
    frame["code"] = frame["code"].astype("string").str.zfill(6)
    return frame 


# ===== Stable IDs =====
# Hash each row records for traceability
def stable_id(prefix: str, *parts: Any, length: int = 20) -> str:
    # Deterministic ID from the joined parts (NaNs become ""), so the same inputs always map to the
    # same id across runs. Used for obs_id (the analytical key) and the BACI source-row id.
    payload = "|".join("" if pd.isna(p) else str(p) for p in parts)
    return prefix + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def baci_source_row_id(row: pd.Series) -> str:
    # A provenance id for a raw BACI row (year, HS6, exporter, importer, value, quantity).
    return stable_id("baci_", row["t"], row["k"], row["i"], row["j"], row["v"], row["q"], length=24)



# ===== Panel construction (the canonical year+exporter+importer+HS6 table) =====
def build_panel(raw: pd.DataFrame, benchmarks: pd.DataFrame, source_hash: str):
    # Turn raw BACI rows + benchmarks into the clean panel + an exclusion audit. Returns
    # (retained_panel, audit). This is the single most important table in the project.
    country = load_country_codes()
    product_desc = load_product_codes().rename(columns={"code": "hs6", "description": "hs6_product_code_description"})
    family_ref = pd.DataFrame(families())[["family_id", "hs6", "product_name", "benchmark_series_id", "project_role"]] # convery .yml to df

    # Rename raw columns to friendly name
    panel = raw.copy()
    panel["source_row_id"] = panel.apply(baci_source_row_id, axis=1) # hash each row
    panel = panel.rename(columns={"t": "year", "k": "hs6", "i": "exporter_code", "j": "importer_code"})
    panel["hs6"] = panel["hs6"].astype("string").str.zfill(6)
    panel["trade_value_usd"] = panel["v"] * 1000.0 # column v is thousands of current USD
    panel["quantity_metric_ton"] = panel["q"] # already reported in metric tons.
    panel["quantity_unit_raw"] = "metric_ton"

    # ---- Join reference tables: family, product description, exporter/importer names, benchmark ----
    panel = panel.merge(family_ref, on="hs6", how="left", validate="many_to_one")
    panel = panel.merge(product_desc[["hs6", "hs6_product_code_description"]], on="hs6", how="left", validate="many_to_one")
    panel = panel.merge(country.rename(columns={"country_code": "exporter_code", "country_iso3": "exporter_iso3", "country_name": "exporter_name"}), on="exporter_code", how="left", validate="many_to_one")
    panel = panel.merge(country.rename(columns={"country_code": "importer_code", "country_iso3": "importer_iso3", "country_name": "importer_name"}), on="importer_code", how="left", validate="many_to_one")
    
    # Benchmark join is many-to-many on (family, hs6) then narrowed to the matching year.
    panel = panel.merge(benchmarks, on=["family_id", "hs6"], how="left", validate="many_to_many", suffixes=("", "_benchmark"))
    panel = panel[panel["year"] == panel["benchmark_year"]].copy()
    if "benchmark_series_id_benchmark" in panel.columns:
        panel["benchmark_series_id"] = panel["benchmark_series_id_benchmark"].combine_first(panel.get("benchmark_series_id"))
        panel = panel.drop(columns=["benchmark_series_id_benchmark"])

    # ---- Validity flags + the core derived measurements ----
    panel["benchmark_join_status"] = np.where(panel["benchmark_price_usd_per_metric_ton"], "matched", "missing")
    panel["value_valid_flag"] = panel["trade_value_usd"].notna() & (panel["trade_value_usd"] > 0)
    panel["quantity_valid_flag"] = panel["quantity_metric_ton"].notna() & (panel["quantity_metric_ton"] > 0)
    panel["unit_value_valid_flag"] = panel["value_valid_flag"] & panel["quantity_valid_flag"]

    # Implied aggregate unit value = USD / metric ton (only where both value and quantity are valid).
    panel["unit_value_usd_per_metric_ton"] = np.where(panel["unit_value_valid_flag"], panel["trade_value_usd"] / panel["quantity_metric_ton"], np.nan)
    panel["log_unit_value"] = np.where(panel["unit_value_valid_flag"], np.log(panel["unit_value_usd_per_metric_ton"]), np.nan)

    # Benchmark residual = how far the implied unit value sits from the World Bank price (log scale).
    panel["benchmark_residual"] = np.where(
        panel["unit_value_valid_flag"] & panel["benchmark_price_usd_per_metric_ton"].notna(),
        panel["log_unit_value"] - np.log(panel["benchmark_price_usd_per_metric_ton"]),
        np.nan,
    )

    # Flag "valid extremes": real values that are >5x or <0.2x the benchmark. ratio of unit_value_usd_per_metric_ton / benchmark_proce_usd_per_metric_ton
    ratio = panel["unit_value_usd_per_metric_ton"] / panel["benchmark_price_usd_per_metric_ton"]
    panel["valid_extreme_flag"] = panel["unit_value_valid_flag"] & ((ratio > 5.0) | (ratio < 0.20))

    # Corridor id = "EXP->IMP"; obs_id = the deterministic analytical key for this year+route+HS6.
    panel["corridor_id"] = panel["exporter_iso3"].fillna("UNK") + "->" + panel["importer_iso3"].fillna("UNK")
    panel["obs_id"] = [stable_id("obs_", y, e, i, h) for y, e, i, h in zip(panel["year"], panel["exporter_code"], panel["importer_code"], panel["hs6"], strict=True)]

    # Compute number of combination of each corridor_id and hs6
    panel = panel.sort_values(["corridor_id", "hs6", "year"], kind="mergesort")
    panel["history_years_available"] = panel.groupby(["corridor_id", "hs6"], sort=False).cumcount()

    # ---- Assign a quality status (separates DATA QUALITY from suspiciousness) ----
    def status_and_reason(row: pd.Series) -> tuple[str, str]:
        # Unmapped country or non-positive value => excluded entirely.
        if pd.isna(row["exporter_iso3"]) or pd.isna(row["importer_iso3"]):
            return "excluded_entirely", "unmapped_country_code"
        if not bool(row["value_valid_flag"]):
            return "excluded_entirely", "non_positive_or_missing_trade_value"
        
        # Missing quantity blocks unit-value modeling but is kept for audit (not suspicious).
        if not bool(row["quantity_valid_flag"]):
            return "excluded_from_modeling_retained_for_audit", "missing_or_non_positive_quantity"
        
        # Otherwise usable; attach caveats for missing benchmark / short history / valid extreme.
        caveats: list[str] = []
        if row["benchmark_join_status"] != "matched":
            caveats.append("missing_benchmark")
        if int(row["history_years_available"]) < 2:
            caveats.append("short_history")
        if bool(row["valid_extreme_flag"]):
            caveats.append("valid_extreme_retained")
        if caveats:
            return "usable_with_caveat", ";".join(caveats)
        return "fully_usable", ""

    # Status
    status_pairs = panel.apply(status_and_reason, axis=1)
    panel["quality_status"] = [s for s, _ in status_pairs]
    panel["exclusion_reason"] = [r for _, r in status_pairs]

    # ---- Additive data-quality score (a CONFIDENCE signal, not an anomaly score) ----
    panel["quantity_score"] = panel["quantity_valid_flag"].astype(int)
    panel["benchmark_score"] = np.where(panel["benchmark_join_status"] == "matched", 2, 0)
    panel["history_score"] = np.select([panel["history_years_available"] >= 5, panel["history_years_available"] >= 3], [2, 1], default=0)
    panel["completeness_score"] = panel[["source_row_id", "hs6", "year", "exporter_code", "importer_code"]].notna().all(axis=1).astype(int)
    panel["data_quality_score"] = panel["quantity_score"] + panel["benchmark_score"] + panel["history_score"] + panel["completeness_score"]

    # Data quality is a usability/confidence signal, not an anomaly score.
    # A row is model-eligible only if it has a valid unit value and is usable (with or without caveats).
    panel["model_eligible"] = panel["unit_value_valid_flag"] & panel["quality_status"].isin(["fully_usable", "usable_with_caveat"])

    # Provenance stamps carried on every panel row.
    panel["source_filename"] = BACI_FILE
    panel["source_version"] = "CEPII_BACI_HS17_V202601_filtered_official_derived"
    panel["source_file_hash"] = source_hash
    panel["hs_revision"] = "HS17"

    # ---- Enforce canonical-key uniqueness on the retained rows ----
    # The whole project assumes one row = one (year, exporter, importer, product). just a defensive insurance although
    # BACI dataset is already one-per-key
    key = ["year", "exporter_iso3", "importer_iso3", "hs6"]
    retained = panel[panel["quality_status"] != "excluded_entirely"].copy()
    if retained.duplicated(key).any():
        dups = retained.loc[retained.duplicated(key, keep=False), key].head(10).to_dict(orient="records")
        raise ValueError(f"Canonical key is not unique; examples={dups}")
    
    # ---- Select the published panel columns + build the exclusion audit ----
    output_cols = [
        "obs_id", "source_row_id", "year", "exporter_code", "exporter_iso3", "exporter_name",
        "importer_code", "importer_iso3", "importer_name", "corridor_id", "hs6", "family_id",
        "product_name", "hs6_product_code_description", "project_role", "v", "q", "trade_value_usd",
        "quantity_metric_ton", "quantity_unit_raw", "unit_value_usd_per_metric_ton", "log_unit_value",
        "benchmark_series_id", "benchmark_price_original", "benchmark_unit_original", "benchmark_price_usd_per_metric_ton",
        "benchmark_year", "benchmark_yoy_change", "benchmark_join_status", "benchmark_conversion_method",
        "benchmark_residual", "benchmark_caveat", "source_sheet", "history_years_available", "value_valid_flag",
        "quantity_valid_flag", "unit_value_valid_flag", "valid_extreme_flag", "quantity_score", "benchmark_score",
        "history_score", "completeness_score", "data_quality_score", "quality_status", "exclusion_reason",
        "model_eligible", "source_filename", "source_version", "source_file_hash", "hs_revision"
    ]

    # Include fully usable, excluded_from_modeling_retained_for_audit, and usable_with_caveat
    retained = retained[output_cols].sort_values(key, kind="mergesort").reset_index(drop=True)

    # Audit = anything that is not "fully_usable" (caveated, modeling-excluded, or fully excluded),
    # so no row is ever silently lost.
    audit = panel[panel["quality_status"] != "fully_usable"][[
        "obs_id", "source_row_id", "year", "exporter_code", "importer_code", "hs6", "family_id",
        "quality_status", "exclusion_reason", "value_valid_flag", "quantity_valid_flag", "benchmark_join_status",
        "source_filename", "source_version"
    ]].sort_values(["quality_status", "year", "hs6", "exporter_code", "importer_code"], kind="mergesort").reset_index(drop=True)
    return retained, audit



    return panel


