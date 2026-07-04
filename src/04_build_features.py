"""
04_build_features.py — Engineer the time-safe features used for scoring + write their data dictionary.

PIPELINE STEP: 5 of 12  (runs after 03_build_panel.py, before 05_build_scenarios.py)

WHAT IT DOES:
  Computes the model/rule input features from the clean panel — drift vs. the corridor's
  own history, benchmark residuals, year-over-year changes, novelty/reactivation flags,
  etc. The actual math lives in tbml_common.build_features(); the key property it enforces
  is TIME SAFETY: a feature for year Y may only use data from year Y or earlier (prior
  years / same-year peers), never future years and never any downstream label. This script
  also emits a human-readable "feature dictionary" markdown table from FEATURE_EXPLANATIONS
  so reviewers can see, per feature, how it is derived and why it is safe.

READS (inputs):
  - data/processed/corridor_product_year_panel.parquet — the clean panel

WRITES (outputs):
  - data/processed/corridor_features.parquet — one time-safe feature row per official observation
  - reports/feature_explanation_table.md — the feature data dictionary (rendered from the table below)

"""

from __future__ import annotations

import pandas as pd
import numpy as np

# build_features() is the workhorse (in tbml_common.py); this script wraps it and
# writes the documentation table.
from tbml_common import DATA_PROCESSED, REPORTS, ensure_dirs, _log_change, feature_columns, identity_columns

# feature dictionary, with columns:
#   (feature_name, derivation, why_created, significance_for_review,
#    time_safety_rule, plain_english_interpretation)
# This is reference text only — it does NOT compute anything; the matching calculations
# live in tbml_common.build_features(). Note how every "time_safety_rule" entry restricts
# the feature to prior-years / same-year information so no future data can leak in.
FEATURE_EXPLANATIONS = [
    ("log_unit_value", "log(unit_value_usd_per_metric_ton)", "Stabilizes skewed unit values.", "Shows unusually high or low implied prices within a product family.", "Uses only the current row's official value and quantity.", "The aggregate implied price on a log scale."),
    ("shifted_corridor_history_median", "Median of prior-year log_unit_value for the same exporter-importer-HS6 corridor.", "Builds the corridor's own baseline.", "Shows whether the row differs from its own past.", "Prior years only; current/future years excluded.", "What this route-product normally looked like before this year."),
    ("shifted_corridor_history_mad", "Median absolute deviation of prior prior-year log_unit_value.", "Gives robust historical spread.", "Large current deviations matter more when history is stable.", "Prior years only.", "How much this route-product used to vary."),
    ("robust_historical_z", "(log_unit_value - shifted median) / shifted MAD with a safe denominator.", "Measures distance from prior corridor behavior.", "Core drift signal.", "Median and MAD are shifted prior-year values.", "How far this row is from its own historical pattern."),
    ("same_family_year_peer_percentile", "Percentile rank of benchmark_residual within the same HS6/family and year.", "Compares against contemporaneous peers.", "Finds rows unusual relative to other corridors in the same market year.", "Same-year only; no future-year peer distributions.", "Where this row sits among same-product peers that year."),
    ("trade_value_yoy_change", "log(current trade value / previous observed trade value) for same corridor-HS6.", "Captures sudden value movement.", "Highlights sharp trade value jumps or falls.", "Previous observation only.", "How much aggregate value changed since the previous active year."),
    ("quantity_yoy_change", "log(current quantity / previous observed quantity) for same corridor-HS6.", "Separates value growth from physical quantity growth.", "Shows whether value changes are volume-driven.", "Previous observation only.", "How much physical quantity changed."),
    ("unit_value_yoy_change", "log(current unit value / previous observed unit value).", "Captures implied price movement.", "Important for valuation-style review.", "Previous observation only.", "How much the implied price changed."),
    ("benchmark_residual", "log_unit_value - log(World Bank benchmark USD per metric ton).", "Adds macro commodity context.", "Separates corridor-specific gaps from broad commodity levels.", "Uses benchmark for the same year only.", "The gap between observed aggregate unit value and broad market context."),
    ("benchmark_adjusted_drift", "benchmark_residual - previous observed benchmark_residual.", "Looks at movement after broad benchmark changes.", "Reduces false positives when commodity markets move broadly.", "Previous residual only.", "Whether the gap to benchmark changed compared with this route's prior gap."),
    ("corridor_activity_history", "Count of prior active years for exporter-importer-HS6.", "Captures history depth.", "Short-history rows need caveats.", "Prior years only.", "How many earlier years this route-product appeared."),
    ("corridor_novelty_flag", "1 if no prior active year exists; else 0.", "Flags new corridors.", "New corridors can matter when paired with extreme values.", "Prior activity only.", "This route-product is new in the observed panel."),
    ("corridor_reactivation_flag", "1 if prior activity exists and the previous active year is not the immediately preceding year.", "Captures reappearing routes.", "Reactivation can matter with large valuation changes.", "Prior activity pattern only.", "The route-product disappeared and came back."),
    ("value_quantity_divergence", "trade_value_yoy_change - quantity_yoy_change.", "Identifies value moving faster than quantity.", "Useful for valuation-style review patterns.", "Based on previous-observation changes only.", "Value changed more than physical volume."),
    ("missingness_flags", "Binary flags for missing quantity, benchmark, history, or country mapping.", "Makes data limits explicit.", "Prevents data-quality issues from being mistaken for suspiciousness.", "Missingness reflects available data at the row time.", "What key information is missing."),
    ("data_quality_flags", "Flags and additive score for quantity, benchmark, history, and provenance completeness.", "Separates confidence from anomaly strength.", "Low quality caveats a case; it should not automatically raise suspiciousness.", "Uses source/provenance and prior history only where relevant.", "How usable and well-supported the row is."),
]

def _prior_median_mad(values: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    # For each position, compute the median + MAD of ALL PRIOR values only (the current value is
    # appended AFTER its baseline is recorded). This is what makes "shifted history" time-safe:
    # a row can never see its own or any future value when forming its baseline.
    medians = np.full(len(values), np.nan)
    mads = np.full(len(values), np.nan)
    history: list[float] = []
    for idx, value in enumerate(values.to_numpy(dtype=float, na_value=np.nan)):
        if history:
            arr = np.asarray(history, dtype=float)
            med = float(np.median(arr))
            medians[idx] = med
            mads[idx] = float(np.median(np.abs(arr - med)))  # median absolute deviation
        if np.isfinite(value):
            history.append(float(value))
    return medians, mads


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    # Derive every time-safe features from the clean panel dataset. Time-safe means only use information that already existed at the time of analysis
    # example: a 2020 row is judged purely on earlier facts. This is to prevent leakage

    required = {
        "obs_id", "source_row_id", "year", "exporter_iso3", "importer_iso3", "corridor_id", "hs6", "family_id",
        "product_name", "trade_value_usd", "quantity_metric_ton", "unit_value_usd_per_metric_ton", "log_unit_value",
        "benchmark_price_usd_per_metric_ton", "benchmark_yoy_change", "benchmark_residual", "benchmark_join_status",
        "valid_extreme_flag", "data_quality_score", "quality_status", "model_eligible", "source_version"
    }

    missing = required - set(panel.columns) #c heck whether there are any missing requried fields

    if missing:
        raise ValueError(f"Panel missing fields required for feature engineering: {sorted(missing)}")
    
    # Sort by corridor + HS6 + year so "prior years" means the rows above within each group.
    features = panel.copy().sort_values(["corridor_id", "hs6", "year"], kind="mergesort")
    group_keys = ["corridor_id", "hs6"]

    # ---- Shifted (prior-only) history median + MAD per corridor ----
    med = pd.Series(np.nan, index=features.index, dtype=float)
    mad = pd.Series(np.nan, index=features.index, dtype=float) #median absolute deviation

    # When you iterate a pandas groupby, each item is a tuple of two things: (the group's key, the group's rows)
    # Compute median and median absolute deviation of prior log_unit_value per route (corridor + produt)
    for _, group in features.groupby(group_keys, sort=False, dropna=False):   # one iteration per route (corridor + hs6)
        m, d = _prior_median_mad(group["log_unit_value"]) #one iteration per row within that route
        med.loc[group.index] = m
        mad.loc[group.index] = d
    features["shifted_corridor_history_median"] = med
    features["shifted_corridor_history_mad"] = mad

    # use a small postiive fallback
    safe_mad = features["shifted_corridor_history_mad"].where(features["shifted_corridor_history_mad"] > 1e-9, 0.05) # keep current value if > 0 else replace with 0.05

    # Robust z = how many MADs the current value sits from the prior median (the core drift signal).
    features["robust_historical_z"] = (features["log_unit_value"] - features["shifted_corridor_history_median"]) / safe_mad
    features.loc[features["shifted_corridor_history_median"].isna(), "robust_historical_z"] = np.nan  #overwrites robust_historical_z if median is 0

    # Same-year peer comparison is allowed because it does not use future years.
    features["same_family_year_peer_percentile"] = features.groupby(["family_id", "year"], sort=False)["benchmark_residual"].rank(method="average", pct=True)

    # ---- Previous-observation (lagged) values for year-over-year changes ----
    grouped = features.groupby(group_keys, sort=False, dropna=False)
    prev_trade = grouped["trade_value_usd"].shift(1)
    prev_qty = grouped["quantity_metric_ton"].shift(1)
    prev_uv = grouped["unit_value_usd_per_metric_ton"].shift(1)
    prev_resid = grouped["benchmark_residual"].shift(1)
    prev_year = grouped["year"].shift(1)
    features["trade_value_yoy_change"] = _log_change(features["trade_value_usd"], prev_trade)
    features["quantity_yoy_change"] = _log_change(features["quantity_metric_ton"], prev_qty)
    features["unit_value_yoy_change"] = _log_change(features["unit_value_usd_per_metric_ton"], prev_uv)
    features["benchmark_adjusted_drift"] = features["benchmark_residual"] - prev_resid

    # Activity history / novelty / reactivation (new corridor, or one that reappeared after a gap).
    features["corridor_activity_history"] = grouped.cumcount().astype(float) # how many earlier appearances did this route have before this row.
    features["corridor_novelty_flag"] = (features["corridor_activity_history"] == 0).astype(int) # 1 when the count is 0. It is the route's first-ever appearance (brand new).
    features["corridor_reactivation_flag"] = ((features["corridor_activity_history"] > 0) & ((features["year"] - prev_year) > 1)).astype(int) # it vanished and came back.

    # Value moving faster than quantity
    features["value_quantity_divergence"] = features["trade_value_yoy_change"] - features["quantity_yoy_change"]

    # Did this route move differently from the whole market?
    # unit_value_yoy_change = how much this route's price moved.
    # benchmark_yoy_change = how much the world market price for that commodity moved.
    # A near-zero gap = the price change is explained by the market; a big gap = it isn't.
    features["benchmark_consistency_gap"] = (features["unit_value_yoy_change"] - features["benchmark_yoy_change"]).abs()

    # ---- Explicit missingness flags (data limits, NOT suspiciousness) ----
    features["missing_quantity_flag"] = features["quantity_metric_ton"].isna().astype(int)
    features["missing_benchmark_flag"] = (features["benchmark_join_status"] != "matched").astype(int)
    features["missing_history_flag"] = features["shifted_corridor_history_median"].isna().astype(int)
    features["missing_country_mapping_flag"] = (features["exporter_iso3"].isna() | features["importer_iso3"].isna()).astype(int)
    features["data_quality_flags"] = (
        "quantity_missing=" + features["missing_quantity_flag"].astype(str)
        + ";benchmark_missing=" + features["missing_benchmark_flag"].astype(str)
        + ";history_missing=" + features["missing_history_flag"].astype(str)
        + ";country_missing=" + features["missing_country_mapping_flag"].astype(str)
    )

    # ---- Safety guards: no infinities, and NO labels/scenario/crime columns may leak in ----
    numeric_cols = feature_columns()
    if np.isinf(features[numeric_cols].to_numpy(dtype=float, na_value=np.nan)).any():  # check for infinite values for features
        raise ValueError("Feature construction produced infinite values")
    forbidden = {"synthetic_review_priority", "scenario_id", "money_laundering", "fraud", "criminal", "tbml_confirmed"}
    present = forbidden.intersection(features.columns)
    if present:
        raise ValueError(f"Forbidden fields entered features: {sorted(present)}")
    

    # ---- Keep identity + context + features, de-duplicated, in a stable order ----
    # list(dict.fromkeys(["year", "hs6", "year", "value"])) -> ['year', 'hs6', 'value']
    # dict.fromkeys(iterable) creates a dictionary key from the iterable and sets every value to None. dic key is unique!
    keep = identity_columns() + [
        "exporter_code", "importer_code", "exporter_name", "importer_name", "trade_value_usd", "quantity_metric_ton",
        "unit_value_usd_per_metric_ton", "benchmark_price_usd_per_metric_ton", "benchmark_yoy_change",
    ] + feature_columns() + [
        "quality_status", "model_eligible", "source_version", "source_row_id", "data_quality_flags", "benchmark_caveat"
    ]
    return features[list(dict.fromkeys(keep))].sort_values(["year", "family_id", "corridor_id", "hs6"], kind="mergesort").reset_index(drop=True)



def main() -> None:
    ensure_dirs()

    # ---- Render the feature dictionary to markdown ----
    # Turn FEATURE_EXPLANATIONS into a DataFrame and write it as a markdown table so the
    # governance docs (and the final report) can show exactly how each feature is built.
    explanation = pd.DataFrame(FEATURE_EXPLANATIONS, columns=[
        "feature_name", "derivation", "why_created", "significance_for_review", "time_safety_rule", "plain_english_interpretation"
    ])
    (REPORTS / "feature_explanation_table.md").write_text(
        "# Time-safe feature explanation table\n\n" + explanation.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    # ---- Compute the time-safe features ----
    panel = pd.read_parquet(DATA_PROCESSED / "corridor_product_year_panel.parquet")
    features = build_features(panel)
    features.to_parquet(DATA_PROCESSED / "corridor_features.parquet", index=False)

    print(f"features rows={len(features):,}; feature table written")



if __name__ == "__main__":
    main()
