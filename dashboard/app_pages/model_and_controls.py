"""Model Evaluation & Controls — can you trust the ranking, and what are its limits?

A single stakeholder narrative, top to bottom: how the ranking is tested, whether
it works (in plain terms), why this method was chosen, what makes the flagged
cases different, and the controls that keep it honest. The technical layer — full
metric tables, SHAP, model parameters, source hashes — sits in one collapsed
drawer at the end. Every number is derived from the pipeline artefacts; all copy
lives in dashboard_content.yml. No Plotly or colour is built in this page.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    driver_dumbbell, headline_bar, model_metric_bar, shap_importance_bar, show,
)
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.tables import plain_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_contracts as contracts
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

content = load.load_content()
copy = content["pages"]["model_and_controls"]
short_labels = content["family_short_labels"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

comparison = load.load_model_comparison()
selection = load.load_model_selection()
project = load.load_project_config()


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _takeaway(text: str) -> None:
    st.markdown(f'<div class="case-takeaway">{_e(text)}</div>', unsafe_allow_html=True)


def _family(family_id: str | None) -> str:
    return short_labels.get(family_id, family_id or "—")


# ---- Objective (skimmable: says what the page is for) ------------------------
st.markdown(f'<div class="why-summary">{_e(copy["objective"])}</div>',
            unsafe_allow_html=True)

# ---- 1. How the ranking is tested -------------------------------------------
tested = copy["tested"]
section_title(tested["heading"])
st.markdown(tested["body"])
st.markdown(tested["split_line"].format(
    train=fm.year_span(project["train_years"]),
    validation=fm.year_span(project["validation_years"]),
    test=fm.year_span(project["test_years"]),
))
st.info(tested["caveat"], icon=":material/science:")

# ---- 2. Does it work? -------------------------------------------------------
works = copy["works"]
section_title(works["heading"])
headline = metrics.headline_eval(comparison, selection)
if headline is None:
    st.info("Evaluation results are unavailable for this run.")
else:
    _takeaway(works["takeaway"].format(
        selected_pct=round(headline["selected_pct"]), lift=round(headline["lift"])))
    bars = pd.DataFrame({
        "method": [works["bar_selected"], works["bar_rule"], works["bar_random"]],
        "found": [headline["selected_pct"], headline["rule_pct"] or 0.0,
                  headline["random_pct"]],
    })
    show(headline_bar(bars, "method", "found", works["bar_selected"], works["bar_x"]),
         height=240, key="mc_headline")
    if headline["hard_negative_fpr"] == 0.0:
        st.caption(works["guardrail"])
    st.caption(works["family_limit"].format(
        best=_family(headline["best_family_id"]),
        worst=_family(headline["worst_family_id"])))
ledger("model_comparison")

# ---- 3. Why this method was chosen ------------------------------------------
method = copy["method"]
section_title(method["heading"])
st.markdown(method["body"])
st.caption(method["score_note"])
ledger("model_selection")

# ---- 4. What makes the flagged cases different ------------------------------
drivers = copy["drivers"]
section_title(drivers["heading"])
features = load.load_features(columns=(
    "obs_id", "model_eligible", "robust_historical_z", "benchmark_residual",
    "same_family_year_peer_percentile", "unit_value_yoy_change",
))
queue = load.load_review_queue()
separation = metrics.driver_separation(features, set(queue["obs_id"]))
_takeaway(drivers["takeaway"])
show(driver_dumbbell(separation, drivers["queue_label"], drivers["population_label"],
                     drivers["x_title"]), height=300, key="mc_drivers")
st.caption(drivers["caption"])
ledger("features", "review_queue")

# ---- 5. What keeps it honest ------------------------------------------------
honest = copy["honest"]
section_title(honest["heading"])
panel_small = load.load_panel(columns=(
    "obs_id", "trade_value_usd", "quantity_metric_ton", "year", "hs6",
    "exporter_iso3", "importer_iso3", "corridor_id", "family_id", "product_name",
    "unit_value_usd_per_metric_ton", "benchmark_price_usd_per_metric_ton",
    "benchmark_residual", "quality_status", "data_quality_score", "model_eligible",
))
report = contracts.run_integrity_report(
    queue, load.load_evidence(), panel_small, load.load_features(), comparison,
)
failures = {name: problems for name, problems in report.items() if problems}
if not failures:
    st.success(honest["integrity_pass"].format(n=len(report)),
               icon=":material/check_circle:")
else:
    st.error(honest["integrity_fail_intro"], icon=":material/error:")
    for name, problems in failures.items():
        st.error(f"**{name}** — " + "; ".join(problems))

allowed_col, not_col = st.columns(2)
with allowed_col:
    st.markdown(f"**{_e(honest['allowed_label'])}**")
    for line in content["interpretation_language"]["allowed"]:
        st.success(f"“{line}”")
with not_col:
    st.markdown(f"**{_e(honest['not_allowed_label'])}**")
    for line in content["interpretation_language"]["not_allowed"]:
        st.error(f"“{line}”")
st.caption(honest["boundary_note"])

# ---- Technical details (one collapsed drawer; nothing above depends on it) ---
drawer = copy["drawer"]
with st.expander(drawer["label"]):
    st.caption(drawer["intro"])

    # Full metric table, with the evaluation-split and family selectors that used
    # to sit on the main page. mc_split stays the page's FIRST selectbox.
    d1, d2 = st.columns(2)
    with d1:
        split = st.selectbox(drawer["split_label"], ["test", "validation"], key="mc_split")
    with d2:
        family_options = ["all"] + sorted(set(comparison["family_id"]) - {"all"})
        family = st.selectbox(drawer["family_label"], family_options, key="mc_family")
    st.markdown(f"**{_e(drawer['metrics_heading'])}**")
    view = metrics.comparison_view(comparison, split, family)
    if not view.empty:
        show(model_metric_bar(view, "precision_at_k", "Precision at k",
                              {headline["selected_model"] if headline else "hybrid"}),
             height=320, key="mc_metric_bar")
        plain_table(view[[
            "model", "n", "positives", "k", "precision_at_k", "recall_at_k",
            "lift_at_k", "average_precision", "hard_negative_false_positive_rate",
            "ordinary_false_positive_rate",
        ]])

    hybrid = load.load_hybrid_candidates()
    if hybrid is not None:
        st.markdown(f"**{_e(drawer['hybrid_heading'])}**")
        plain_table(hybrid, column_labels={"challenger_weight": "Challenger weight"})

    manifest = load.load_scenario_split_manifest()
    if manifest:
        st.markdown(f"**{_e(drawer['splits_heading'])}**")
        counts = pd.DataFrame([
            {"split": name,
             "rows": manifest["counts_by_split"].get(name, 0),
             "synthetic positives": manifest["positive_counts_by_split"].get(name, 0),
             "hard negatives": manifest["hard_negative_counts_by_split"].get(name, 0)}
            for name in ["train", "validation", "test"]
        ])
        plain_table(counts)
        st.caption(drawer["splits_note"])

    shap_values = load.load_shap_summary_values()
    if shap_values is not None:
        st.markdown(f"**{_e(drawer['shap_heading'])}**")
        st.caption(drawer["shap_caveat"])
        show(shap_importance_bar(shap_values), height=420, key="mc_shap")

    xgb = load.load_xgboost_parameters()
    if xgb:
        st.markdown(f"**{_e(drawer['params_heading'])}**")
        st.json(xgb)

    coefficients = load.load_logistic_coefficients()
    if coefficients is not None:
        st.markdown(f"**{_e(drawer['coeffs_heading'])}**")
        plain_table(coefficients)

    inventory = load.load_source_file_inventory()
    if inventory is not None:
        st.markdown(f"**{_e(drawer['sources_heading'])}**")
        plain_table(inventory)
    ledger("model_comparison", "model_selection", "shap_summary_values")
