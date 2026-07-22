"""Model Evaluation & Controls — can you trust the ranking, and what are its limits?

A single stakeholder narrative, top to bottom: how the ranking is tested, whether
it works (in plain terms), why this method was chosen, and the controls that keep
it honest. The technical layer — full
metric tables, SHAP, model parameters, source hashes — sits in one collapsed
drawer at the end. Every number is derived from the pipeline artefacts; all copy
lives in dashboard_content.yml. No Plotly or colour is built in this page.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    case_emphasis_color, headline_bar, model_metric_bar, review_capacity_tradeoff,
    shap_importance_bar, show,
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
threshold_config = load.load_thresholds_config()
hybrid = load.load_hybrid_candidates()
queue = load.load_review_queue()
queue_size = len(queue)
selected_score_col = str(selection.get("selected_score_column", "hybrid_score"))
model_emphasis = case_emphasis_color()
model_scores = load.load_model_scores(columns=(
    "obs_id", "split", "synthetic_review_priority", "hard_negative", selected_score_col,
))


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

# ---- 2. How well does it rank the test patterns? ---------------------------
works = copy["works"]
section_title(works["heading"], icon="chart-pie")
headline = metrics.headline_eval(comparison, selection)
if headline is None:
    st.info("Evaluation results are unavailable for this run.")
else:
    evidence = metrics.ranking_evidence(
        model_scores, selection, split="test", k=int(headline["k"]),
    )
    _takeaway(works["takeaway"].format(
        found=evidence["found"], k=evidence["k"],
        random_expected=f"{float(evidence['random_expected']):.1f}",
        lift=f"{float(evidence['lift']):.0f}",
    ))
    bars = pd.DataFrame({
        "method": [works["bar_selected"], works["bar_rule"], works["bar_random"]],
        "found": [100.0 * float(evidence["precision"]), headline["rule_pct"] or 0.0,
                  100.0 * float(evidence["prevalence"])],
    })
    show(headline_bar(
        bars, "method", "found", works["bar_selected"], works["bar_x"],
        emphasis_color=model_emphasis,
    ),
         height=240, key="mc_headline")
    if int(evidence["hard_negative_top"]) == 0:
        st.caption(works["guardrail"].format(
            hard_total=evidence["hard_negative_total"], k=evidence["k"],
        ))
    st.caption(works["family_limit"].format(
        best=_family(headline["best_family_id"]),
        worst=_family(headline["worst_family_id"])))

    st.markdown(f'<div class="chart-subhead">{_e(works["capacity_heading"])}</div>',
                unsafe_allow_html=True)
    st.markdown(works["capacity_body"])
    capacity = metrics.review_capacity_curve(model_scores, selection)
    show(review_capacity_tradeoff(
        capacity, int(evidence["k"]), works["capacity_precision"],
        works["capacity_recall"], works["capacity_x"], works["capacity_y"],
    ), height=330, key="mc_capacity_tradeoff")
    st.caption(works["capacity_caption"].format(
        k=evidence["k"], found=evidence["found"],
        precision=f"{100.0 * float(evidence['precision']):.0f}",
        positives=evidence["positives"],
        recall=f"{100.0 * float(evidence['recall']):.0f}",
    ))

    math = works["math"]
    with st.expander(math["label"]):
        st.caption(math["intro"])
        fact_values = (
            (math["facts"]["rows"], f"{int(evidence['n']):,}"),
            (math["facts"]["patterns"], f"{int(evidence['positives']):,}"),
            (math["facts"]["reviewed"], f"{int(evidence['k']):,}"),
            (math["facts"]["found"], f"{int(evidence['found']):,}"),
        )
        facts_html = "".join(
            f'<div class="mc-eval-fact"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'
            for label, value in fact_values
        )
        st.markdown(f'<div class="mc-eval-facts">{facts_html}</div>',
                    unsafe_allow_html=True)

        precision_pct = 100.0 * float(evidence["precision"])
        recall_pct = 100.0 * float(evidence["recall"])
        prevalence_pct = 100.0 * float(evidence["prevalence"])
        metric_copy = math["metrics"]
        columns = math["columns"]
        calculation_table = pd.DataFrame([
            {
                columns["metric"]: metric_copy["precision"][0],
                columns["calculation"]: f"{evidence['found']} / {evidence['k']}",
                columns["result"]: f"{precision_pct:.1f}%",
                columns["meaning"]: metric_copy["precision"][1],
            },
            {
                columns["metric"]: metric_copy["recall"][0],
                columns["calculation"]: f"{evidence['found']} / {evidence['positives']}",
                columns["result"]: f"{recall_pct:.1f}%",
                columns["meaning"]: metric_copy["recall"][1],
            },
            {
                columns["metric"]: metric_copy["random"][0],
                columns["calculation"]: f"{evidence['positives']} / {evidence['n']:,}",
                columns["result"]: (
                    f"{prevalence_pct:.2f}% ({float(evidence['random_expected']):.2f} rows)"
                ),
                columns["meaning"]: metric_copy["random"][1],
            },
            {
                columns["metric"]: metric_copy["lift"][0],
                columns["calculation"]: f"{precision_pct:.1f}% / {prevalence_pct:.2f}%",
                columns["result"]: f"{float(evidence['lift']):.1f}x",
                columns["meaning"]: metric_copy["lift"][1],
            },
        ])
        plain_table(calculation_table)
        st.caption(math["caveat"])
ledger("model_comparison", "model_scores")

# ---- 3. Why this method was chosen ------------------------------------------
method = copy["method"]
section_title(method["heading"], icon="sliders")
st.markdown(method["body"])

# Three plain decisions explain where the two scores and the blend come from.
_method_steps = []
for _step in method["story_steps"]:
    _method_steps.append(
        f'<div class="method-step">'
        f'<div class="method-step-icon">{render_icon(_step["icon"])}</div>'
        f'<div class="method-step-title">{_e(_step["title"])}</div>'
        f'<div class="method-step-detail">{_e(_step["detail"])}</div></div>'
    )
st.markdown(f'<div class="method-path anim">{"".join(_method_steps)}</div>',
            unsafe_allow_html=True)

# Formula + split bar, derived from the validation-selected weight.
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
st.markdown(method["selection_summary"].format(
    challenger_pct=challenger_pct,
    rule_pct=rule_pct,
    validation_years=fm.year_span(project["validation_years"]),
))

# The mechanics are evidence, but not required reading for the main story.
weighted = method["weighted_sum"]
with st.expander(weighted["label"]):
    st.markdown(weighted["intro"])
    st.markdown(f'<div class="blend-eq method-rule-eq">{_e(weighted["formula"])}</div>',
                unsafe_allow_html=True)
    st.markdown(f"**{weighted['components_heading']}**")
    rule_settings = threshold_config["rules"]
    component_columns = weighted["columns"]
    component_rows = pd.DataFrame([
        {
            component_columns["signal"]: item["signal"],
            component_columns["weight"]: f"{float(rule_settings[item['key']]):.2f}",
            component_columns["meaning"]: item["meaning"],
        }
        for item in weighted["components"]
    ])
    plain_table(component_rows)
    st.markdown(f"**{weighted['reductions_heading']}**")
    st.markdown("- " + weighted["consistency_reduction"].format(
        value=f"{float(rule_settings['benchmark_consistency_credit']):.2f}"))
    st.markdown("- " + weighted["quality_reduction"].format(
        value=f"{float(rule_settings['quality_penalty_weight']):.2f}"))
    st.caption(weighted["clipping_note"])

    st.markdown(f"**{weighted['validation_heading']}**")
    st.markdown(weighted["validation_intro"])
    if hybrid is not None:
        validation_columns = weighted["validation_columns"]
        validation_rows = []
        for _, candidate in hybrid.sort_values("challenger_weight", ascending=False).iterrows():
            challenger_weight = float(candidate["challenger_weight"])
            found = round(float(candidate["precision_at_k"]) * int(candidate["k"]))
            selected_label = "Selected" if abs(challenger_weight - _weight) < 1e-9 else "Compared"
            validation_rows.append({
                validation_columns["blend"]: selected_label,
                validation_columns["xgboost"]: f"{challenger_weight:.0%}",
                validation_columns["weighted_sum"]: f"{1.0 - challenger_weight:.0%}",
                validation_columns["result"]: (
                    f"{found} of {int(candidate['k'])} "
                    f"({float(candidate['precision_at_k']):.0%})"
                ),
            })
        plain_table(pd.DataFrame(validation_rows))
    st.caption(weighted["validation_caveat"])

# The five-method chart is the held-out check, not the blend-selection step.
st.markdown(f'<div class="chart-subhead">{_e(method["test_heading"])}</div>',
            unsafe_allow_html=True)
_mc = metrics.method_comparison(comparison, "test")
_xgb_pct = float(_mc.loc[_mc["model"] == "xgboost", "precision_pct"].iloc[0])
_hyb_pct = float(_mc.loc[_mc["model"] == "hybrid", "precision_pct"].iloc[0])
show(headline_bar(_mc, "method", "precision_pct",
                  metrics.METHOD_LABELS["hybrid"], method["comparison_x"],
                  emphasis_color=model_emphasis),
     height=270, key="mc_method_compare")
st.caption(method["comparison_caption"].format(
    test_years=fm.year_span(project["test_years"])))

st.markdown(
    f'<div class="method-tradeoff">{_e(method["tradeoff"].format(
        xgb_pct=round(_xgb_pct), hyb_pct=round(_hyb_pct)))}</div>',
    unsafe_allow_html=True,
)
st.caption(method["explainability_note"])
st.caption(method["score_note"])
ledger("model_selection", "hybrid_candidates")

# ---- 4. What keeps it honest ------------------------------------------------
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

    ledger("model_comparison", "model_selection", "shap_summary_values")

# ---- Hand-off: what the queue could NOT assess (gold quantity coverage) ------
# The queue is built only from observations with usable value and quantity; the
# coverage page answers what happened to the gold records outside that boundary.
next_page = copy["next_page"]
with st.container(key="mc_next_page"):
    st.markdown(f'<div class="case-takeaway">{_e(next_page["body"])}</div>',
                unsafe_allow_html=True)
    st.page_link("app_pages/gold_quantity_coverage.py",
                 label=f'{next_page["cta"]} →', icon=":material/rule:")

# Reveal the narrative sections and the remaining stakeholder charts as
# they scroll into view. The drawer's own bold sub-headings are not .section-
# heading, so they stay unaffected.
render_scroll_reveal(
    ".section-heading, .st-key-mc_headline, .st-key-mc_capacity_tradeoff, "
    ".st-key-mc_method_compare"
)
