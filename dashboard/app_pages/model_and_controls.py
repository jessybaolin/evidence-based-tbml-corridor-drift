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
from dashboard.components.icons import render_icon
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.scroll_reveal import render_scroll_reveal
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
queue_size = len(load.load_review_queue())


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _takeaway(text: str) -> None:
    st.markdown(f'<div class="case-takeaway">{_e(text)}</div>', unsafe_allow_html=True)


def _family(family_id: str | None) -> str:
    return short_labels.get(family_id, family_id or "—")


# ---- Objective (skimmable: says what the page is for) ------------------------
st.markdown(f'<div class="why-summary anim">{_e(copy["objective"])}</div>',
            unsafe_allow_html=True)

# ---- How the ranking queue is built (top-of-page pipeline overview) ----------
# The blend split (challenger vs rules %) is derived from the selection artefact,
# never typed in — it drives the flow step, the formula and the split bar below.
_weight = float(selection.get("selected_hybrid_challenger_weight") or 0.75)
challenger_pct = round(_weight * 100)
rule_pct = round((1.0 - _weight) * 100)
challenger_name = metrics.METHOD_LABELS.get(
    str(selection.get("selected_challenger", "xgboost")), "XGBoost")
blend = f"{challenger_pct}% {challenger_name} + {rule_pct}% rules"

qb = copy["queue_build"]
section_title(qb["heading"], qb["caption"], icon="list-ordered")
_flow_parts: list[str] = []
for _i, _s in enumerate(qb["steps"], start=1):
    if _i > 1:
        _flow_parts.append('<span class="mc-flow-arrow" aria-hidden="true">→</span>')
    _flow_parts.append(
        f'<div class="mc-flow-step"><span class="mc-flow-num">{_i}</span>'
        f'<div class="mc-flow-title">'
        f'{_e(str(_s["title"]).format(queue_size=queue_size, blend=blend))}</div>'
        f'<div class="mc-flow-detail">'
        f'{_e(str(_s["detail"]).format(queue_size=queue_size, blend=blend))}</div></div>'
    )
st.markdown(f'<div class="mc-flow anim">{"".join(_flow_parts)}</div>',
            unsafe_allow_html=True)

# ---- 1. How the ranking is tested -------------------------------------------
tested = copy["tested"]
section_title(tested["heading"], icon="file-search")
st.markdown(tested["body"])

# "Tested on a copy" visual: the planted patterns the method must catch vs the
# benign look-alikes it must leave alone (replaces the old two-lane wall).
sc = copy["scenarios"]


def _scenario_items(items: list) -> str:
    return "".join(
        f'<div class="scenario-item">'
        f'<div class="scenario-item-title">{_e(it["title"])}</div>'
        f'<div class="scenario-item-detail">{_e(it["detail"])}</div></div>'
        for it in items
    )


st.markdown(
    f'<div class="chart-subhead">{_e(sc["subhead"])}</div>'
    f'<div class="scenario anim">'
    f'<div class="scenario-copy">'
    f'<span class="scenario-copy-real">{_e(sc["copy_from"])}</span>'
    f'<span class="scenario-copy-arrow" aria-hidden="true">→</span>'
    f'<span class="scenario-copy-test">{_e(sc["copy_to"])}</span>'
    f'<span class="scenario-copy-note">{_e(sc["copy_note"])}</span></div>'
    f'<div class="scenario-groups">'
    f'<div class="scenario-group catch">'
    f'<div class="scenario-group-head">{render_icon("checklist", class_name="scenario-ic")}'
    f'<span>{_e(sc["catch_heading"])}</span></div>'
    f'{_scenario_items(sc["catch_items"])}</div>'
    f'<div class="scenario-group ignore">'
    f'<div class="scenario-group-head">{render_icon("line-chart", class_name="scenario-ic")}'
    f'<span>{_e(sc["ignore_heading"])}</span></div>'
    f'{_scenario_items(sc["ignore_items"])}</div></div>'
    f'<div class="scenario-note">{_e(sc["separation_note"])}</div></div>',
    unsafe_allow_html=True,
)

st.markdown(tested["split_line"].format(
    train=fm.year_span(project["train_years"]),
    validation=fm.year_span(project["validation_years"]),
    test=fm.year_span(project["test_years"]),
))
st.info(tested["caveat"], icon=":material/science:")

# ---- 2. Does it work? -------------------------------------------------------
works = copy["works"]
section_title(works["heading"], icon="chart-pie")
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
section_title(method["heading"], icon="sliders")
st.markdown(method["body"])

# The five methods compared on precision@50 (held-out test years). headline_bar
# (NOT model_metric_bar, which is drawer-only) keeps the % framing on the page.
_mc = metrics.method_comparison(comparison, "test")
_xgb_pct = float(_mc.loc[_mc["model"] == "xgboost", "precision_pct"].iloc[0])
_hyb_pct = float(_mc.loc[_mc["model"] == "hybrid", "precision_pct"].iloc[0])
show(headline_bar(_mc, "method", "precision_pct",
                  metrics.METHOD_LABELS["hybrid"], method["comparison_x"]),
     height=270, key="mc_method_compare")
st.caption(method["comparison_caption"])

# The honest trade: XGBoost scored a little higher, but the blend is kept — the
# choice was frozen on validation (no leakage) and 25% rules stay auditable.
st.markdown(method["tradeoff"].format(xgb_pct=round(_xgb_pct), hyb_pct=round(_hyb_pct)))
for _reason in method["tradeoff_reasons"]:
    st.markdown(f"- {_reason.format(rule_pct=rule_pct)}")

# Formula + the challenger/rules split bar, derived from the selection weight.
st.markdown(f'<div class="chart-subhead">{_e(method["formula_heading"])}</div>',
            unsafe_allow_html=True)
st.markdown(
    f'<div class="blend anim">'
    f'<div class="blend-eq">'
    f'{_e(method["formula"].format(challenger_pct=challenger_pct, rule_pct=rule_pct))}</div>'
    f'<div class="blend-bar">'
    f'<div class="blend-seg blend-challenger" style="width:{challenger_pct}%">'
    f'{_e(method["blend_challenger_label"].format(challenger_pct=challenger_pct))}</div>'
    f'<div class="blend-seg blend-rule" style="width:{rule_pct}%">'
    f'{_e(method["blend_rule_label"].format(rule_pct=rule_pct))}</div>'
    f'</div></div>',
    unsafe_allow_html=True,
)
st.caption(method["score_note"])
ledger("model_selection")

# ---- 4. What makes the flagged cases different ------------------------------
drivers = copy["drivers"]
section_title(drivers["heading"], icon="search")
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
section_title(honest["heading"], icon="shield-check")
panel_small = load.load_panel(columns=(
    "obs_id", "trade_value_usd", "quantity_metric_ton", "year", "hs6",
    "exporter_iso3", "importer_iso3", "corridor_id", "family_id", "product_name",
    "unit_value_usd_per_metric_ton", "benchmark_price_usd_per_metric_ton",
    "benchmark_residual", "quality_status", "data_quality_score", "model_eligible",
))
report = contracts.run_integrity_report(
    queue, load.load_evidence(), panel_small, load.load_features(), comparison,
)
# Live integrity checks still run; only a FAILURE surfaces. The reassuring green
# "all checks pass" banner was removed to keep the page calmer and less green.
failures = {name: problems for name, problems in report.items() if problems}
if failures:
    st.error(honest["integrity_fail_intro"], icon=":material/error:")
    for name, problems in failures.items():
        st.error(f"**{name}** — " + "; ".join(problems))

# Allowed vs not-allowed language, as two equal-height cards (grid stretch),
# coloured blue / rose rather than two more green success boxes.
_allowed = "".join(
    f'<li>“{_e(line)}”</li>' for line in content["interpretation_language"]["allowed"])
_not_allowed = "".join(
    f'<li>“{_e(line)}”</li>' for line in content["interpretation_language"]["not_allowed"])
st.markdown(
    f'<div class="say-grid">'
    f'<div class="say-card say-allowed">'
    f'<div class="say-head"><span class="say-mark" aria-hidden="true">✓</span>'
    f'{_e(honest["allowed_label"])}</div>'
    f'<ul class="say-list">{_allowed}</ul></div>'
    f'<div class="say-card say-notallowed">'
    f'<div class="say-head"><span class="say-mark" aria-hidden="true">✕</span>'
    f'{_e(honest["not_allowed_label"])}</div>'
    f'<ul class="say-list">{_not_allowed}</ul></div></div>',
    unsafe_allow_html=True,
)
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

# Reveal the six narrative sections (their headings) and the three charts as
# they scroll into view. The drawer's own bold sub-headings are not .section-
# heading, so they stay unaffected.
render_scroll_reveal(
    ".section-heading, .st-key-mc_headline, "
    ".st-key-mc_method_compare, .st-key-mc_drivers"
)
