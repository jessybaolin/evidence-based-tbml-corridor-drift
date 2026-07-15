"""
Builds the Appendix data dictionary from authoritative project material.

WHAT IT DOES:
    Merges three layers, in decreasing authority, into one searchable table:
      1. reports/feature_explanation_table.md  — approved feature definitions
         (derivation, time-safety rule, plain-English interpretation);
      2. reports/data_dictionary.md            — the pipeline's field dictionary;
      3. actual dataframe schemas               — column name, dtype, dataset
         (schema-inferred; clearly labelled, never invented definitions).
    A small curated map adds category, unit, and which dashboard page uses the
    field — presentation metadata that exists nowhere in the pipeline.
"""

from __future__ import annotations

import pandas as pd

# Presentation-only metadata (category / unit / dashboard page). Definitions are
# NOT invented here — they come from the two markdown documents; fields without
# documented definitions show as schema-inferred.
CURATED: dict[str, dict[str, str]] = {
    "obs_id": {"category": "Identifiers", "pages": "Official Review Queue, Selected Case Review"},
    "source_row_id": {"category": "Identifiers"},
    "evidence_id": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "corridor_id": {"category": "Identifiers", "pages": "Selected Case Review"},
    "year": {"category": "Identifiers", "pages": "All pages"},
    "hs6": {"category": "Identifiers", "pages": "All pages"},
    "family_id": {"category": "Identifiers", "pages": "All pages"},
    "product_name": {"category": "Identifiers", "pages": "All pages"},
    "exporter_iso3": {"category": "Identifiers", "pages": "Official Review Queue, Selected Case Review"},
    "importer_iso3": {"category": "Identifiers", "pages": "Official Review Queue, Selected Case Review"},
    "exporter_name": {"category": "Identifiers"},
    "importer_name": {"category": "Identifiers"},
    "t": {"category": "Source values"},
    "k / hs6": {"category": "Source values"},
    "i / exporter_code": {"category": "Source values"},
    "j / importer_code": {"category": "Source values"},
    "v": {"category": "Source values", "unit": "thousands of current USD"},
    "q": {"category": "Source values", "unit": "metric tons"},
    "trade_value_usd": {"category": "Derived financial metrics", "unit": "USD",
                        "pages": "Official Review Queue, Selected Case Review"},
    "quantity_metric_ton": {"category": "Derived financial metrics", "unit": "metric tons",
                            "pages": "Selected Case Review"},
    "unit_value_usd_per_metric_ton": {"category": "Derived financial metrics", "unit": "USD per metric ton",
                                      "pages": "Selected Case Review"},
    "benchmark_price_usd_per_metric_ton": {"category": "Derived financial metrics", "unit": "USD per metric ton",
                                           "pages": "Selected Case Review"},
    "log_unit_value": {"category": "Time-safe features"},
    "benchmark_residual": {"category": "Time-safe features", "unit": "log difference",
                           "pages": "Selected Case Review, Queue Patterns"},
    "shifted_corridor_history_median": {"category": "Time-safe features"},
    "shifted_corridor_history_mad": {"category": "Time-safe features"},
    "robust_historical_z": {"category": "Time-safe features", "pages": "Selected Case Review"},
    "same_family_year_peer_percentile": {"category": "Time-safe features", "unit": "percentile (0–1)",
                                         "pages": "Selected Case Review"},
    "trade_value_yoy_change": {"category": "Time-safe features", "unit": "log change"},
    "quantity_yoy_change": {"category": "Time-safe features", "unit": "log change"},
    "unit_value_yoy_change": {"category": "Time-safe features", "unit": "log change",
                              "pages": "Selected Case Review"},
    "benchmark_adjusted_drift": {"category": "Time-safe features", "unit": "log change",
                                 "pages": "Selected Case Review"},
    "benchmark_consistency_gap": {"category": "Time-safe features", "unit": "absolute log change"},
    "benchmark_yoy_change": {"category": "Time-safe features", "unit": "log change"},
    "value_quantity_divergence": {"category": "Time-safe features", "unit": "log change",
                                  "pages": "Selected Case Review"},
    "corridor_activity_history": {"category": "Time-safe features", "unit": "count of prior years"},
    "corridor_novelty_flag": {"category": "Time-safe features", "pages": "Selected Case Review"},
    "corridor_reactivation_flag": {"category": "Time-safe features", "pages": "Selected Case Review"},
    "missing_quantity_flag": {"category": "Quality fields"},
    "missing_benchmark_flag": {"category": "Quality fields"},
    "missing_history_flag": {"category": "Quality fields"},
    "missing_country_mapping_flag": {"category": "Quality fields"},
    "missingness_flags": {"category": "Quality fields"},
    "data_quality_flags": {"category": "Quality fields", "pages": "Selected Case Review"},
    "data_quality_score": {"category": "Quality fields", "unit": "additive score 0–6",
                           "pages": "Official Review Queue, Selected Case Review"},
    "quality_status": {"category": "Quality fields", "pages": "Official Review Queue, Selected Case Review"},
    "model_eligible": {"category": "Quality fields", "pages": "Business Problem & Value"},
    "valid_extreme_flag": {"category": "Quality fields", "pages": "Selected Case Review"},
    "exclusion_reason": {"category": "Quality fields"},
    "rank": {"category": "Model scores", "pages": "Official Review Queue, Selected Case Review"},
    "selected_review_priority_score": {"category": "Model scores", "unit": "0–1 ranking score",
                                       "pages": "Official Review Queue, Selected Case Review"},
    "rule_score": {"category": "Model scores", "unit": "0–1 ranking score",
                   "pages": "Model Validation & Controls"},
    "selected_challenger_score": {"category": "Model scores", "unit": "0–1 ranking score",
                                  "pages": "Model Validation & Controls"},
    # Scenario label: must never be attributed to the official BACI extract.
    "synthetic_review_priority": {
        "category": "Model scores",
        "dataset": "data/processed/scenario_labels.parquet (scenario evaluation only)",
    },
    "key_evidence_count": {"category": "Evidence fields", "pages": "Official Review Queue, Selected Case Review"},
    "evidence_type": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "metric_name": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "observed_value": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "comparison_value": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "comparison_group": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "threshold": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "direction": {"category": "Evidence fields"},
    "severity": {"category": "Evidence fields", "pages": "Selected Case Review, Queue Patterns"},
    "source_fields": {"category": "Evidence fields"},
    "plain_english_summary": {"category": "Evidence fields", "pages": "Selected Case Review"},
    "caveat": {"category": "Evidence fields", "pages": "Selected Case Review"},
}

# Which datasets are introspected for schema-inferred rows.
DICTIONARY_DATASETS = ["panel", "features", "review_queue", "evidence", "model_comparison"]

_COLUMNS = [
    "field", "dataset", "category", "data_type", "definition", "derivation",
    "unit", "time_safety_rule", "quality_caveat", "definition_source", "dashboard_pages",
]


def build_dictionary(
    schemas: dict[str, pd.DataFrame],
    feature_explanations: pd.DataFrame | None,
    dictionary_md: pd.DataFrame | None,
) -> pd.DataFrame:
    # Layer 1: approved feature explanations (highest authority for features).
    features_doc: dict[str, dict] = {}
    if feature_explanations is not None and "feature_name" in feature_explanations.columns:
        features_doc = feature_explanations.set_index("feature_name").to_dict(orient="index")

    # Layer 2: the pipeline data dictionary (field | meaning | type | caveat).
    md_doc: dict[str, dict] = {}
    if dictionary_md is not None and "field" in dictionary_md.columns:
        md_doc = dictionary_md.set_index("field").to_dict(orient="index")

    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for dataset_name, frame in schemas.items():
        for column in frame.columns:
            key = (column, dataset_name)
            if key in seen:
                continue
            seen.add(key)
            rows.append(_build_row(column, dataset_name, str(frame[column].dtype), features_doc, md_doc))

    # Documented fields that exist only outside the loaded dataframes (raw BACI
    # t/k/i/j, scenario labels, ...) still deserve a dictionary row. The
    # dataset attribution comes from CURATED where set — a scenario label must
    # never be attributed to the official raw extract.
    schema_fields = {r["field"] for r in rows}
    for field_name, entry in md_doc.items():
        if field_name not in schema_fields and not any(field_name.startswith(f) for f in schema_fields):
            rows.append({
                "field": field_name,
                "dataset": CURATED.get(field_name, {}).get("dataset", "data/raw (BACI extract)"),
                "category": CURATED.get(field_name, {}).get("category", "Source values"),
                "data_type": entry.get("type", ""),
                "definition": entry.get("meaning", ""),
                "derivation": "",
                "unit": CURATED.get(field_name, {}).get("unit", ""),
                "time_safety_rule": "",
                "quality_caveat": entry.get("caveat", ""),
                "definition_source": "reports/data_dictionary.md",
                "dashboard_pages": CURATED.get(field_name, {}).get("pages", ""),
            })

    dictionary = pd.DataFrame(rows, columns=_COLUMNS)
    category_order = [
        "Identifiers", "Source values", "Derived financial metrics",
        "Time-safe features", "Quality fields", "Model scores", "Evidence fields", "Other",
    ]
    dictionary["category"] = pd.Categorical(
        dictionary["category"], categories=category_order, ordered=True
    )
    return dictionary.sort_values(["category", "field", "dataset"]).reset_index(drop=True)


# Definitions quoted from the feature-engineering code (src/tbml_common.py)
# for fields the markdown documents do not cover — labelled code-derived.
CODE_DERIVED: dict[str, dict[str, str]] = {
    "benchmark_consistency_gap": {
        "definition": ("Did this route move differently from the whole market? A near-zero gap "
                       "means the price change is explained by the market; a big gap means it is not."),
        "derivation": "abs(unit_value_yoy_change - benchmark_yoy_change)",
        "time_safety": "Compares this row's year-over-year change with the same year's benchmark change.",
    },
    "benchmark_yoy_change": {
        "definition": "Year-over-year log change of the benchmark price itself.",
        "derivation": "log(benchmark price / prior-year benchmark price) per family",
        "time_safety": "Uses the prior year's benchmark only.",
    },
}


def _build_row(column: str, dataset_name: str, dtype: str,
               features_doc: dict, md_doc: dict) -> dict:
    curated = CURATED.get(column, {})
    definition, derivation, time_safety, caveat, source = "", "", "", "", "schema-inferred"

    if column in features_doc:
        entry = features_doc[column]
        definition = entry.get("plain_english_interpretation", "")
        derivation = entry.get("derivation", "")
        time_safety = entry.get("time_safety_rule", "")
        caveat = entry.get("significance_for_review", "")
        source = "reports/feature_explanation_table.md"
    elif column in CODE_DERIVED:
        entry = CODE_DERIVED[column]
        definition = entry["definition"]
        derivation = entry["derivation"]
        time_safety = entry["time_safety"]
        source = "src/tbml_common.py (feature-engineering code)"
    elif column in md_doc:
        entry = md_doc[column]
        definition = entry.get("meaning", "")
        caveat = entry.get("caveat", "")
        source = "reports/data_dictionary.md"
    else:
        # Some dictionary rows document raw/derived pairs like "k / hs6".
        for md_field, entry in md_doc.items():
            aliases = [part.strip() for part in md_field.split("/")]
            if column in aliases:
                definition = entry.get("meaning", "")
                caveat = entry.get("caveat", "")
                source = "reports/data_dictionary.md"
                break

    return {
        "field": column,
        "dataset": dataset_name,
        "category": curated.get("category", "Other"),
        "data_type": dtype,
        "definition": definition,
        "derivation": derivation,
        "unit": curated.get("unit", ""),
        "time_safety_rule": time_safety,
        "quality_caveat": caveat,
        "definition_source": source,
        "dashboard_pages": curated.get("pages", ""),
    }
