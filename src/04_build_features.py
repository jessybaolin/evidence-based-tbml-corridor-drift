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
from tbml_common import DATA_PROCESSED, REPORTS, ensure_dirs, build_features

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
