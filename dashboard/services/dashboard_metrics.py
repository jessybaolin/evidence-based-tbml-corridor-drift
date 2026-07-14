"""
Dashboard metric calculations — pure functions over the loaded artefacts.

WHAT IT DOES:
    Every KPI, aggregation, and case assembly the pages show. Functions take
    dataframes/dicts as arguments (no Streamlit, no file I/O) so the same code
    is unit-testable and page-independent. Values are derived, never typed in.
"""

from __future__ import annotations

import pandas as pd

from dashboard.services import formatting as fm

# ---- Executive overview ------------------------------------------------------

def overview_kpis(
    panel: pd.DataFrame,
    queue: pd.DataFrame,
    evidence: pd.DataFrame,
    comparison: pd.DataFrame,
    selection: dict,
    source_manifest: dict | None,
) -> dict[str, dict]:
    # Each KPI carries its value plus the artefact it was derived from, so the
    # overview can print an honest provenance line under the cards.
    verified, total_checks = source_verification_counts(source_manifest)
    validation_value = "Not verified"
    if total_checks:
        validation_value = "Verified" if verified == total_checks else f"{verified}/{total_checks} checks"
    return {
        "observations": {
            "value": f"{len(panel):,}",
            "detail": f"{fm.year_span(panel['year'].unique())}, one row per corridor-product-year",
            "source": "panel",
        },
        "model_eligible": {
            "value": f"{int(panel['model_eligible'].sum()):,}",
            "detail": "valid unit value and usable quality status",
            "source": "panel",
        },
        "families": {
            "value": f"{panel['family_id'].nunique()}",
            "detail": ", ".join(sorted(panel["product_name"].dropna().unique())),
            "source": "panel",
        },
        "queue": {
            "value": f"{len(queue):,}",
            "detail": f"top-ranked official observations ({fm.year_span(queue['year'].unique())})",
            "source": "review_queue",
        },
        "models": {
            "value": f"{comparison['model'].nunique()}",
            "detail": ", ".join(sorted(comparison["model"].unique())),
            "source": "model_comparison",
        },
        "evidence": {
            "value": f"{len(evidence):,}",
            "detail": f"{evidence['obs_id'].nunique()} candidates with recomputable evidence",
            "source": "evidence",
        },
        "validation": {
            "value": validation_value,
            "detail": "source hashes, counts, and provenance checks",
            "source": "source_manifest",
        },
        "selected_method": {
            "value": selected_method_label(selection),
            "detail": selection.get("score_language", ""),
            "source": "model_selection",
        },
    }


def selected_method_label(selection: dict) -> str:
    challenger = selection.get("selected_challenger", "challenger")
    weight = selection.get("selected_hybrid_challenger_weight")
    if weight is None:
        return str(selection.get("selected_score_column", "hybrid"))
    rule_share = round((1.0 - float(weight)) * 100)
    return f"Hybrid: {round(float(weight) * 100)}% {challenger} + {rule_share}% rules"


def source_verification_counts(source_manifest: dict | None) -> tuple[int, int]:
    # Count the boolean checks recorded by 01_verify_sources.py.
    if not source_manifest:
        return 0, 0
    booleans: list[bool] = []
    for block in ("baci_source_confirmed", "data_source_notes_checks"):
        for value in (source_manifest.get(block) or {}).values():
            if isinstance(value, bool):
                booleans.append(value)
    return sum(booleans), len(booleans)


def family_coverage(panel: pd.DataFrame, short_labels: dict[str, str]) -> pd.DataFrame:
    coverage = (
        panel.groupby(["family_id", "hs6", "product_name"], as_index=False)
        .agg(panel_rows=("obs_id", "count"), model_eligible=("model_eligible", "sum"))
    )
    coverage["family_label"] = coverage["family_id"].map(short_labels).fillna(coverage["product_name"])
    return coverage.sort_values("panel_rows", ascending=False).reset_index(drop=True)


def quality_summary(panel: pd.DataFrame) -> pd.DataFrame:
    summary = panel["quality_status"].value_counts().rename_axis("quality_status").reset_index(name="rows")
    summary["share"] = summary["rows"] / summary["rows"].sum()
    return summary


# ---- Review queue --------------------------------------------------------------

def enrich_queue(queue: pd.DataFrame, features: pd.DataFrame, short_labels: dict[str, str]) -> pd.DataFrame:
    # Presentation-only enrichment: corridor label, family short name, country
    # names and benchmark residual joined from the feature table. Raw analytical
    # columns are preserved untouched for the CSV download.
    extra_cols = ["obs_id", "exporter_name", "importer_name", "benchmark_residual", "robust_historical_z"]
    enriched = queue.merge(features[extra_cols], on="obs_id", how="left", validate="one_to_one")
    enriched["corridor"] = [
        fm.corridor(e, i) for e, i in zip(enriched["exporter_iso3"], enriched["importer_iso3"])
    ]
    enriched["family_label"] = enriched["family_id"].map(short_labels).fillna(enriched["product_name"])
    enriched["caveat_flag"] = enriched["quality_status"].ne("fully_usable")
    return enriched


def queue_filter_options(queue: pd.DataFrame) -> dict:
    scores = queue["selected_review_priority_score"]
    return {
        "years": sorted(int(y) for y in queue["year"].unique()),
        "families": sorted(queue["family_label"].unique()),
        "hs6": sorted(queue["hs6"].unique()),
        "exporters": sorted(queue["exporter_iso3"].unique()),
        "importers": sorted(queue["importer_iso3"].unique()),
        "statuses": sorted(queue["quality_status"].unique()),
        "score_min": float(scores.min()),
        "score_max": float(scores.max()),
    }


def apply_queue_filters(queue: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = queue
    if filters.get("years"):
        result = result[result["year"].isin(filters["years"])]
    if filters.get("families"):
        result = result[result["family_label"].isin(filters["families"])]
    if filters.get("exporters"):
        result = result[result["exporter_iso3"].isin(filters["exporters"])]
    if filters.get("importers"):
        result = result[result["importer_iso3"].isin(filters["importers"])]
    if filters.get("statuses"):
        result = result[result["quality_status"].isin(filters["statuses"])]
    if filters.get("score_range"):
        low, high = filters["score_range"]
        scores = result["selected_review_priority_score"]
        result = result[(scores >= low) & (scores <= high)]
    if filters.get("min_evidence") is not None:
        result = result[result["key_evidence_count"] >= filters["min_evidence"]]
    if filters.get("search"):
        needle = str(filters["search"]).strip().lower()
        haystack = (
            result["obs_id"].astype(str).str.lower()
            + " " + result["corridor"].astype(str).str.lower()
            + " " + result["exporter_name"].fillna("").astype(str).str.lower()
            + " " + result["importer_name"].fillna("").astype(str).str.lower()
            + " " + result["hs6"].astype(str)
        )
        result = result[haystack.str.contains(needle, regex=False)]
    if filters.get("top_n"):
        result = result.nsmallest(int(filters["top_n"]), "rank")
    return result.sort_values("rank").reset_index(drop=True)


# ---- Case investigation ----------------------------------------------------------

def case_record(obs_id: str, queue: pd.DataFrame, features: pd.DataFrame) -> dict | None:
    # One flat dict for the case header: queue row + feature row (feature values
    # win nothing — they are disjoint apart from the join key).
    queue_rows = queue.loc[queue["obs_id"] == obs_id]
    if queue_rows.empty:
        return None
    record = queue_rows.iloc[0].to_dict()
    feature_rows = features.loc[features["obs_id"] == obs_id]
    if not feature_rows.empty:
        for key, value in feature_rows.iloc[0].to_dict().items():
            record.setdefault(key, value)
    return record


def case_history(panel: pd.DataFrame, exporter_iso3: str, importer_iso3: str, hs6: str) -> pd.DataFrame:
    # All observed years for the same exporter–importer–HS6 corridor, straight
    # from the clean panel — no interpolation, no indexing, no synthetic points.
    history = panel[
        (panel["exporter_iso3"] == exporter_iso3)
        & (panel["importer_iso3"] == importer_iso3)
        & (panel["hs6"] == hs6)
    ]
    return history.sort_values("year").reset_index(drop=True)


def case_evidence(evidence: pd.DataFrame, obs_id: str) -> pd.DataFrame:
    severity_order = {"high": 0, "medium": 1, "low": 2}
    rows = evidence.loc[evidence["obs_id"] == obs_id].copy()
    rows["severity_rank"] = rows["severity"].map(severity_order).fillna(9)
    return rows.sort_values(["severity_rank", "evidence_id"]).drop(columns="severity_rank")


# The feature values shown on "Why it ranked high", in display order.
SIGNAL_FIELDS = [
    "robust_historical_z", "benchmark_residual", "benchmark_adjusted_drift",
    "same_family_year_peer_percentile", "unit_value_yoy_change",
    "trade_value_yoy_change", "quantity_yoy_change", "value_quantity_divergence",
    "benchmark_consistency_gap", "corridor_novelty_flag", "corridor_reactivation_flag",
]


# Features absent from reports/feature_explanation_table.md whose meaning is
# documented in the feature-engineering code (src/tbml_common.py) — quoted from
# there and labelled with that source, never invented.
CODE_DOCUMENTED_SIGNALS: dict[str, dict[str, str]] = {
    "benchmark_consistency_gap": {
        "interpretation": (
            "Did this route move differently from the whole market? A near-zero gap "
            "means the price change is explained by the market; a big gap means it "
            "is not. (Documented in src/tbml_common.py.)"
        ),
        "time_safety": "Compares this row's year-over-year change with the same year's benchmark change.",
    },
}


def case_signals(record: dict, explanations: pd.DataFrame | None) -> pd.DataFrame:
    # Pair each available feature value with its approved plain-English
    # interpretation from reports/feature_explanation_table.md (or, where that
    # table has no entry, the code documentation above). No free-form generated
    # text — anything else undocumented shows as an em dash.
    doc: dict[str, dict] = {}
    if explanations is not None and "feature_name" in explanations.columns:
        doc = explanations.set_index("feature_name").to_dict(orient="index")
    rows = []
    for field in SIGNAL_FIELDS:
        if field not in record:
            continue
        entry = doc.get(field, {})
        code_entry = CODE_DOCUMENTED_SIGNALS.get(field, {})
        rows.append({
            "signal": field,
            "value": record.get(field),
            "interpretation": entry.get("plain_english_interpretation")
            or code_entry.get("interpretation", "—"),
            "time_safety": entry.get("time_safety_rule")
            or code_entry.get("time_safety", "—"),
        })
    return pd.DataFrame(rows)


# ---- Portfolio analytics ----------------------------------------------------------

def candidates_by_year(queue: pd.DataFrame) -> pd.DataFrame:
    return queue.groupby("year", as_index=False).agg(candidates=("obs_id", "count"))


def candidates_by_family(queue: pd.DataFrame) -> pd.DataFrame:
    return (
        queue.groupby(["family_id", "family_label"], as_index=False)
        .agg(candidates=("obs_id", "count"), mean_score=("selected_review_priority_score", "mean"))
        .sort_values("candidates", ascending=False)
    )


def concentration(queue: pd.DataFrame, by: str, top_n: int = 10) -> pd.DataFrame:
    return (
        queue.groupby(by, as_index=False)
        .agg(candidates=("obs_id", "count"), mean_score=("selected_review_priority_score", "mean"))
        .sort_values(["candidates", "mean_score"], ascending=[False, False])
        .head(top_n)
    )


def severity_distribution(evidence: pd.DataFrame) -> pd.DataFrame:
    return (
        evidence.groupby(["evidence_type", "severity"], as_index=False)
        .agg(rows=("evidence_id", "count"))
    )


def residual_context(panel: pd.DataFrame, queue: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    # Benchmark residuals: full official population (context) vs queue (emphasis).
    population = panel["benchmark_residual"].dropna()
    queue_ids = set(queue["obs_id"])
    selected = panel.loc[panel["obs_id"].isin(queue_ids), "benchmark_residual"].dropna()
    return population, selected


# ---- Model & controls ----------------------------------------------------------

def comparison_view(comparison: pd.DataFrame, split: str, family_id: str = "all") -> pd.DataFrame:
    view = comparison[(comparison["split"] == split) & (comparison["family_id"] == family_id)]
    return view.sort_values("average_precision", ascending=False).reset_index(drop=True)


def split_years_table(project_config: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {"split": "Train", "years": fm.year_span(project_config["train_years"]),
         "purpose": "Fit model parameters"},
        {"split": "Validation", "years": fm.year_span(project_config["validation_years"]),
         "purpose": "Select challenger and hybrid weight"},
        {"split": "Test", "years": fm.year_span(project_config["test_years"]),
         "purpose": "Final evaluation after design freeze"},
    ])
