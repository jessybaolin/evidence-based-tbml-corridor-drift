"""Model & Controls — how the ranking was evaluated, selected, controlled, caveated."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.charts import model_metric_bar, shap_importance_bar, show
from dashboard.components.empty_states import missing_output
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.tables import plain_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_contracts as contracts
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

content = load.load_content()
copy = content["pages"]["model_and_controls"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

comparison = load.load_model_comparison()
selection = load.load_model_selection()
project = load.load_project_config()

# The page's core honesty device: scenario evaluation vs real scoring, side by side.
st.info(
    f"**Scenario-based model evaluation** (below) is separate from **scoring of real "
    f"official observations** (the Review Queue). {copy['scenario_note']}",
    icon="🧪",
)

performance_tab, negatives_tab, selection_tab, splits_tab, controls_tab, boundaries_tab = st.tabs([
    "Performance", "Hard Negatives", "Model Selection", "Data Splits",
    "Integrity Controls", "Interpretation Boundaries",
])

METRIC_LABELS = {
    "average_precision": "Average precision",
    "precision_at_k": "Precision at k",
    "recall_at_k": "Recall at k",
    "lift_at_k": "Lift at k",
}
EMPHASIS_MODELS = {"hybrid", str(selection.get("selected_challenger", ""))}

with performance_tab:
    section_title(
        "Scenario-based model comparison",
        "Metrics evaluate controlled synthetic review-priority scenarios — not real crime labels.",
    )
    f1, f2, f3 = st.columns(3)
    with f1:
        split = st.selectbox("Split", ["test", "validation"], index=0)
    with f2:
        family_options = ["all"] + sorted(set(comparison["family_id"]) - {"all"})
        family = st.selectbox("Product family", family_options, index=0)
    with f3:
        metric = st.selectbox("Metric", list(METRIC_LABELS), format_func=METRIC_LABELS.get)
    view = metrics.comparison_view(comparison, split, family)
    if view.empty:
        st.info("No comparison rows exist for this split/family combination.")
    else:
        show(model_metric_bar(view, metric, METRIC_LABELS[metric], EMPHASIS_MODELS),
             height=380, key="mc_metric_bar")
        st.caption("Accent bars: the selected challenger and the hybrid actually used for ranking. "
                   f"k = {int(view['k'].iloc[0])} (top-k evaluation window).")
        plain_table(view[["model", "n", "positives", "k", "precision_at_k", "recall_at_k",
                          "lift_at_k", "average_precision",
                          "hard_negative_false_positive_rate", "ordinary_false_positive_rate"]])
    figure = load.figure_path("model_comparison")
    if figure:
        with st.expander("Pipeline-generated comparison figure (reports/figures)"):
            st.image(str(figure), width="stretch")
    ledger("model_comparison")

with negatives_tab:
    section_title(
        "Hard-negative false-positive rates",
        "Hard negatives are deliberately unusual but benign scenarios (benchmark-consistent moves, "
        "proportional value-and-quantity growth). Lower is better: it means the method does not "
        "over-alert on market-consistent behaviour.",
    )
    split_hn = st.selectbox("Split", ["test", "validation"], index=0, key="hn_split")
    view_hn = metrics.comparison_view(comparison, split_hn, "all")
    if view_hn.empty:
        st.info("No comparison rows for this split.")
    else:
        show(model_metric_bar(view_hn, "hard_negative_false_positive_rate",
                              "Hard-negative false-positive rate", EMPHASIS_MODELS),
             height=360, key="mc_hn_fpr")
        show(model_metric_bar(view_hn, "ordinary_false_positive_rate",
                              "Ordinary false-positive rate", EMPHASIS_MODELS),
             height=360, key="mc_ord_fpr")
    figure_hn = load.figure_path("hard_negative_comparison")
    if figure_hn:
        with st.expander("Pipeline-generated hard-negative figure (reports/figures)"):
            st.image(str(figure_hn), width="stretch")
    ledger("model_comparison")

with selection_tab:
    section_title("Selected ranking method", "Chosen on the validation split only, before the test split was touched.")
    s1, s2, s3 = st.columns(3)
    s1.metric("Selected challenger", str(selection.get("selected_challenger", "—")))
    s2.metric("Hybrid challenger weight", fm.fmt(selection.get("selected_hybrid_challenger_weight"), 2))
    s3.metric("Selection split", str(selection.get("selection_split", "—")))
    st.markdown(f"**Score column used for the queue:** `{selection.get('selected_score_column', 'hybrid_score')}` — "
                f"{metrics.selected_method_label(selection)}")
    st.caption(selection.get("score_language", ""))
    st.caption(
        "Governance note: the hybrid is a rules-anchored blend chosen for stable, explainable ranking; "
        "on some scenario metrics the pure challenger scores higher."
    )

    hybrid = load.load_hybrid_candidates()
    if hybrid is not None:
        section_title("Hybrid-weight candidates on validation",
                      "The tested blend weights; the top row was selected.")
        plain_table(hybrid, column_labels={"challenger_weight": "Challenger weight"})
    else:
        missing_output("hybrid_candidates")

    xgb = load.load_xgboost_parameters()
    if xgb:
        with st.expander("Selected XGBoost parameters and tuning trials"):
            st.json(xgb)
    coefficients = load.load_logistic_coefficients()
    if coefficients is not None:
        with st.expander("Logistic baseline coefficients"):
            plain_table(coefficients)

    shap_values = load.load_shap_summary_values()
    if shap_values is not None:
        section_title("Global model-contribution summary (SHAP)",
                      "Global model contribution context; not a row-specific explanation and not evidence.")
        show(shap_importance_bar(shap_values), height=420, key="mc_shap")
    else:
        missing_output("shap_summary_values")
    ledger("model_selection", "hybrid_candidates", "shap_summary_values")

with splits_tab:
    section_title("Time-based train / validation / test design",
                  "Splits are frozen by year so evaluation never sees the future.")
    plain_table(metrics.split_years_table(project))
    manifest = load.load_scenario_split_manifest()
    if manifest:
        counts = pd.DataFrame([
            {"split": split_name,
             "rows": manifest["counts_by_split"].get(split_name, 0),
             "synthetic positives": manifest["positive_counts_by_split"].get(split_name, 0),
             "hard negatives": manifest["hard_negative_counts_by_split"].get(split_name, 0)}
            for split_name in ["train", "validation", "test"]
        ])
        plain_table(counts)
        st.caption(f"Label separation (verbatim from the manifest): {manifest.get('label_separation', '')}")
    else:
        missing_output("scenario_split_manifest")
    st.markdown(
        "- Historical features use **prior years only** (shifted median/MAD).\n"
        "- Scenario IDs and labels live in a **separate labels file**, never in features.\n"
        "- The test split was evaluated **once**, after the design freeze."
    )
    ledger("scenario_split_manifest", "project_config")

with controls_tab:
    section_title(
        "Live integrity checks",
        "Contracts the dashboard re-runs on the loaded artefacts, including the control that the "
        "queue carries clean-panel values (no scenario-injected rows).",
    )
    panel_small = load.load_panel(columns=("obs_id", "trade_value_usd", "quantity_metric_ton",
                                           "year", "hs6", "exporter_iso3", "importer_iso3",
                                           "corridor_id", "family_id", "product_name",
                                           "unit_value_usd_per_metric_ton",
                                           "benchmark_price_usd_per_metric_ton",
                                           "benchmark_residual", "quality_status",
                                           "data_quality_score", "model_eligible"))
    report = contracts.run_integrity_report(
        load.load_review_queue(), load.load_evidence(), panel_small,
        load.load_features(), comparison,
    )
    for check_name, problems in report.items():
        if problems:
            st.error(f"**{check_name}** — " + "; ".join(problems), icon="❌")
        else:
            st.success(f"**{check_name}** — pass", icon="✅")

    manifest_sources = load.load_source_manifest()
    verified, total = metrics.source_verification_counts(manifest_sources)
    if total:
        section_title("Source verification (recorded by the pipeline)")
        st.markdown(f"- **{verified} of {total}** recorded source checks are true "
                    "(file hashes, row counts, provenance claims).")
        inventory = load.load_source_file_inventory()
        if inventory is not None:
            with st.expander("Raw-input inventory (SHA-256)"):
                plain_table(inventory)
    else:
        missing_output("source_manifest")
    ledger("source_manifest", "source_file_inventory")

with boundaries_tab:
    section_title("What this dashboard may and may not say")
    allowed_col, not_col = st.columns(2)
    with allowed_col:
        for line in content["interpretation_language"]["allowed"]:
            st.success(f"**Allowed:** “{line}”")
    with not_col:
        for line in content["interpretation_language"]["not_allowed"]:
            st.error(f"**Not allowed:** “{line}”")
    st.markdown(
        "- Scores are **review-priority ranking scores**, not calibrated probabilities of crime.\n"
        "- Scenario labels are **controlled evaluation constructs**, not confirmed TBML.\n"
        "- SHAP is model-contribution context, **not factual or legal evidence**.\n"
        "- FATF–Egmont material is typology context only, **never row-level evidence**.\n"
        "- World Bank benchmarks are market context, **not invoice-level fair value**."
    )
