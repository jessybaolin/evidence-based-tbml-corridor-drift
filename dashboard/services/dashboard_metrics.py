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
            # Eligibility hinges on the reported QUANTITY: without a valid
            # quantity no implied unit value exists (value ÷ quantity). Rows
            # missing it are retained for audit, never silently removed.
            "value": f"{int(panel['model_eligible'].sum()):,}",
            "detail": "rows with the valid reported quantity that unit-value signals require",
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
        "exporters": sorted(queue["exporter_iso3"].unique()),
        "importers": sorted(queue["importer_iso3"].unique()),
        "score_min": float(scores.min()),
        "score_max": float(scores.max()),
        "published": len(queue),
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
    if filters.get("score_range"):
        low, high = filters["score_range"]
        scores = result["selected_review_priority_score"]
        result = result[(scores >= low) & (scores <= high)]
    if filters.get("top_n"):
        result = result.nsmallest(int(filters["top_n"]), "rank")
    return result.sort_values("rank").reset_index(drop=True)


# The Review Queue grid, exactly as displayed: nine columns in this order.
# Values come straight from the published queue; the only presentation-derived
# field is the corridor string.
QUEUE_DISPLAY_COLUMNS = [
    "rank", "year", "corridor", "product", "trade_value_usd",
    "quantity_metric_ton", "unit_value_usd_per_metric_ton",
    "benchmark_price_usd_per_metric_ton", "selected_review_priority_score",
]

# The CSV export: the displayed view plus the traceability fields the old
# export guaranteed (obs_id joins evidence/features; quality_status carries the
# data-quality caveat; source_* pin the exact pipeline inputs).
QUEUE_EXPORT_COLUMNS = [
    "obs_id", *QUEUE_DISPLAY_COLUMNS,
    "quality_status", "source_row_id", "source_version",
]


def queue_display_frame(enriched: pd.DataFrame) -> pd.DataFrame:
    # Pure display projection: row order is preserved (positional selection in
    # the grid maps back to the input frame), numbers keep full precision —
    # rounding happens in st.column_config, never here. Ranks travel with their
    # rows, so user re-sorting in the grid can never reassign a rank.
    frame = enriched.reset_index(drop=True)
    display = frame.reindex(columns=[c for c in QUEUE_DISPLAY_COLUMNS if c != "product"])
    display["product"] = frame["family_label"]
    return display[QUEUE_DISPLAY_COLUMNS]


def queue_export_frame(enriched: pd.DataFrame) -> pd.DataFrame:
    # Full-precision export of the current view, always rank-ascending.
    # quality_status carries the data-quality caveat for each row.
    frame = enriched.reset_index(drop=True).sort_values("rank")
    export = frame.reindex(columns=[c for c in QUEUE_EXPORT_COLUMNS if c != "product"])
    export["product"] = frame["family_label"]
    return export[QUEUE_EXPORT_COLUMNS].reset_index(drop=True)


def family_hs6_map(queue: pd.DataFrame) -> dict[str, str]:
    # Family display name -> HS6 code, derived live from the queue rows (the
    # HS6 column left the grid; this feeds the Product column help + caption).
    pairs = queue[["family_label", "hs6"]].drop_duplicates().sort_values("family_label")
    return {str(label): str(code) for label, code in zip(pairs["family_label"], pairs["hs6"])}


def default_case(enriched: pd.DataFrame) -> pd.Series:
    # The case Selected Case Review opens when nothing was picked yet: the
    # top-ranked row of the full queue.
    return enriched.loc[enriched["rank"].idxmin()]


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


# ---- Trade landscape (the full official panel, not the 50-row queue) -----------
# These describe the whole official population — the reading frame a reviewer
# needs before the queue: how large the trade is and how the wider market
# benchmark changed over time.

def _with_corridor(panel: pd.DataFrame) -> pd.DataFrame:
    frame = panel.copy()
    frame["corridor"] = (frame["exporter_iso3"].astype(str) + "→"
                         + frame["importer_iso3"].astype(str))
    return frame


def trade_scale_by_family_year(panel: pd.DataFrame, short_labels: dict) -> pd.DataFrame:
    # Value and quantity per family per year. The same frame feeds the scale
    # small multiples and their exact-value table twin.
    grouped = panel.groupby(["family_id", "year"], as_index=False).agg(
        trade_value_usd=("trade_value_usd", "sum"),
        quantity_metric_ton=("quantity_metric_ton", "sum"),
    )
    grouped["family_label"] = grouped["family_id"].map(short_labels).fillna(
        grouped["family_id"])
    return grouped.sort_values(["family_label", "year"]).reset_index(drop=True)


def benchmark_by_family_year(panel: pd.DataFrame, short_labels: dict) -> pd.DataFrame:
    # The World Bank benchmark per family per year (constant within a family-year;
    # max ignores any missing row). Columns: family_id, family_label, year, benchmark.
    grouped = panel.groupby(["family_id", "year"], as_index=False).agg(
        benchmark=("benchmark_price_usd_per_metric_ton", "max"))
    grouped["family_label"] = grouped["family_id"].map(short_labels).fillna(
        grouped["family_id"])
    return grouped.sort_values(["family_label", "year"]).reset_index(drop=True)


def landscape_summary(panel: pd.DataFrame, short_labels: dict) -> dict:
    # Headline context figures for the landscape strip — all derived, never typed.
    total_value = float(panel["trade_value_usd"].sum())
    by_family = panel.groupby("family_id")["trade_value_usd"].sum()
    dominant = str(by_family.idxmax())
    years = sorted(int(y) for y in panel["year"].unique())
    return {
        "total_value": total_value,
        "dominant_family_id": dominant,
        "dominant_family_label": short_labels.get(dominant, dominant),
        "dominant_share": 100.0 * float(by_family.max()) / total_value,
        "n_families": int(panel["family_id"].nunique()),
        "year_start": years[0],
        "year_end": years[-1],
        "n_years": len(years),
        "n_corridors": int(_with_corridor(panel)["corridor"].nunique()),
    }


# ---- Model & controls ----------------------------------------------------------

def comparison_view(comparison: pd.DataFrame, split: str, family_id: str = "all") -> pd.DataFrame:
    view = comparison[(comparison["split"] == split) & (comparison["family_id"] == family_id)]
    return view.sort_values("average_precision", ascending=False).reset_index(drop=True)


# Display names for the five scoring methods compared during model selection.
# Technical identifiers → readable labels (like family_short_labels for models).
METHOD_LABELS: dict[str, str] = {
    "rule": "Fixed rules",
    "logistic": "Logistic regression",
    "xgboost": "XGBoost",
    "isolation": "Isolation forest",
    "hybrid": "Hybrid blend",
}


def method_comparison(comparison: pd.DataFrame, split: str = "test") -> pd.DataFrame:
    """The five scoring methods and their precision@k on one split (all families),
    as a percentage — the share of the top-k that were genuinely planted patterns.
    Read straight from model_comparison.csv; friendly labels for display. Returns
    columns model / method / precision_pct (one row per method present)."""
    view = comparison[(comparison["split"] == split) & (comparison["family_id"] == "all")]
    rows = [
        {
            "model": str(row["model"]),
            "method": METHOD_LABELS.get(str(row["model"]), str(row["model"])),
            "precision_pct": 100.0 * float(row["precision_at_k"]),
        }
        for _, row in view.iterrows()
    ]
    return pd.DataFrame(rows)


def split_years_table(project_config: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {"split": "Train", "years": fm.year_span(project_config["train_years"]),
         "purpose": "Fit model parameters"},
        {"split": "Validation", "years": fm.year_span(project_config["validation_years"]),
         "purpose": "Select challenger and hybrid weight"},
        {"split": "Test", "years": fm.year_span(project_config["test_years"]),
         "purpose": "Final evaluation after design freeze"},
    ])


# ---- Model evaluation, in plain-language stakeholder terms ----------------------
def headline_eval(comparison: pd.DataFrame, selection: dict, split: str = "test") -> dict | None:
    """The plain "does it work?" numbers for the selected method vs simple rules.

    Translates precision@k into a share (what fraction of the top-k were the
    planted patterns), against the transparent rule baseline and a random-review
    baseline (positives / n). Every value is read from model_comparison.csv, never
    typed in. `split` defaults to the held-out test years.
    """
    selected_model = str(selection.get("selected_score_column", "hybrid_score")).replace("_score", "")
    view = comparison[(comparison["split"] == split) & (comparison["family_id"] == "all")]

    def _row(model: str):
        rows = view[view["model"] == model]
        return rows.iloc[0] if not rows.empty else None

    selected = _row(selected_model)
    rule = _row("rule")
    if selected is None:
        return None
    n = int(selected["n"])
    positives = int(selected["positives"])
    random_pct = 100.0 * positives / n if n else 0.0
    family_rows = comparison[
        (comparison["split"] == split) & (comparison["model"] == selected_model)
        & (comparison["family_id"] != "all")
    ]
    best_family = worst_family = None
    if not family_rows.empty:
        best_family = str(family_rows.loc[family_rows["average_precision"].idxmax(), "family_id"])
        worst_family = str(family_rows.loc[family_rows["average_precision"].idxmin(), "family_id"])
    return {
        "selected_model": selected_model,
        "k": int(selected["k"]),
        "n": n,
        "positives": positives,
        "selected_pct": 100.0 * float(selected["precision_at_k"]),
        "rule_pct": 100.0 * float(rule["precision_at_k"]) if rule is not None else None,
        "random_pct": random_pct,
        "lift": float(selected["lift_at_k"]),
        "hard_negative_fpr": float(selected["hard_negative_false_positive_rate"]),
        "best_family_id": best_family,
        "worst_family_id": worst_family,
    }


def ranking_evidence(
    scores: pd.DataFrame,
    selection: dict,
    split: str = "test",
    k: int = 50,
) -> dict[str, float | int | str]:
    """Recompute Top-k evidence from row-level synthetic-scenario scores.

    Sorting mirrors src/06_train_evaluate_models.metric_at_k exactly: score
    descending, then observation ID ascending with a stable mergesort. The
    counts make precision, recall and lift auditable without treating planted
    labels as real-world outcomes.
    """
    score_col = str(selection.get("selected_score_column", "hybrid_score"))
    required = {"obs_id", "split", "synthetic_review_priority", "hard_negative", score_col}
    missing = required - set(scores.columns)
    if missing:
        raise ValueError(f"Model scores are missing required columns: {sorted(missing)}")

    ranked = (
        scores[scores["split"].eq(split)]
        .sort_values([score_col, "obs_id"], ascending=[False, True], kind="mergesort")
        .reset_index(drop=True)
    )
    k_eff = min(max(int(k), 0), len(ranked))
    top = ranked.head(k_eff)
    positives = int(ranked["synthetic_review_priority"].sum())
    found = int(top["synthetic_review_priority"].sum())
    precision = found / k_eff if k_eff else 0.0
    recall = found / positives if positives else 0.0
    prevalence = positives / len(ranked) if len(ranked) else 0.0
    hard_total = int(ranked["hard_negative"].astype(bool).sum())
    hard_top = int(top["hard_negative"].astype(bool).sum())
    return {
        "score_col": score_col,
        "n": int(len(ranked)),
        "positives": positives,
        "k": k_eff,
        "found": found,
        "precision": precision,
        "recall": recall,
        "prevalence": prevalence,
        "random_expected": k_eff * prevalence,
        "lift": precision / prevalence if prevalence else 0.0,
        "hard_negative_total": hard_total,
        "hard_negative_top": hard_top,
    }


def review_capacity_curve(
    scores: pd.DataFrame,
    selection: dict,
    capacities: tuple[int, ...] = (10, 25, 50, 100, 200),
    split: str = "test",
) -> pd.DataFrame:
    """Precision/recall trade-off as analyst review capacity changes."""
    rows = []
    for capacity in sorted(set(int(value) for value in capacities if int(value) > 0)):
        evidence = ranking_evidence(scores, selection, split=split, k=capacity)
        rows.append({
            "capacity": int(evidence["k"]),
            "found": int(evidence["found"]),
            "positives": int(evidence["positives"]),
            "precision_pct": 100.0 * float(evidence["precision"]),
            "recall_pct": 100.0 * float(evidence["recall"]),
        })
    return pd.DataFrame(rows).drop_duplicates("capacity").reset_index(drop=True)
