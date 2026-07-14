"""Case Investigation — one selected official observation, in depth."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.boundary_banner import boundary_banner
from dashboard.components.charts import (
    history_line, residual_line, show, unit_value_vs_benchmark,
)
from dashboard.components.empty_states import missing_output
from dashboard.components.evidence_panel import evidence_cards
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.status_badges import quality_pill
from dashboard.components.tables import plain_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm
from dashboard.services import session_state as state

content = load.load_content()
copy = content["pages"]["case_investigation"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
boundary_banner()

queue = load.load_review_queue().sort_values("rank")
features = load.load_features()
evidence = load.load_evidence()
short_labels = content["family_short_labels"]

# ---- Case selector: works with or without a Review Queue selection ----
labels = {
    row.obs_id: (
        f"#{int(row.rank)} · {int(row.year)} · {row.exporter_iso3} → {row.importer_iso3} · "
        f"{short_labels.get(row.family_id, row.product_name)}"
    )
    for row in queue.itertuples()
}
ids = list(labels)
carried = state.selected_obs_id()
initial_index = ids.index(carried) if carried in ids else 0
selected_id = st.selectbox(
    "Selected observation", ids, index=initial_index,
    format_func=lambda obs: labels[obs],
    help="Pick a case here, or select a row on the Review Queue page.",
)
state.select_obs(selected_id)

record = metrics.case_record(selected_id, queue, features)
if record is None:
    st.error("The selected observation is not in the review queue. Choose another case.")
    st.stop()

case_evidence = metrics.case_evidence(evidence, selected_id)

# ---- Case header ----
m1, m2, m3, m4 = st.columns(4)
m1.metric("Review rank", f"#{int(record['rank'])}")
m2.metric("Review-priority score", fm.score(record["selected_review_priority_score"]),
          help=load.load_model_selection().get("score_language"))
m3.metric("Evidence rows", int(record["key_evidence_count"]))
with m4:
    st.markdown("**Data quality**", help="Quality is a usability signal, separate from suspiciousness.")
    st.markdown(quality_pill(record["quality_status"]), unsafe_allow_html=True)
    if record.get("valid_extreme_flag"):
        st.caption("Valid extreme retained (>5× or <0.2× benchmark)")

summary_tab, trend_tab, why_tab, evidence_tab, limits_tab = st.tabs(
    ["Case Summary", "Trade & Benchmark Trend", "Why It Ranked High", "Evidence", "Limitations"]
)

# ---- Tab 1: Case Summary ----
with summary_tab:
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        section_title("Observation")
        st.markdown(
            f"""
            **Observation ID:** `{record['obs_id']}`  \n
            **Year:** {int(record['year'])}  \n
            **Corridor:** {record.get('exporter_name', record['exporter_iso3'])} ({record['exporter_iso3']})
            → {record.get('importer_name', record['importer_iso3'])} ({record['importer_iso3']})  \n
            **HS6:** `{record['hs6']}` — {record['product_name']}  \n
            **Ranking method:** {metrics.selected_method_label(load.load_model_selection())}
            """
        )
    with right:
        section_title("Reported values", "Annual official aggregates — not invoices or shipments.")
        values = pd.DataFrame([
            {"measure": "Trade value", "value": fm.money(record["trade_value_usd"])},
            {"measure": "Quantity", "value": fm.quantity_mt(record["quantity_metric_ton"])},
            {"measure": "Aggregate unit value", "value": fm.money(record["unit_value_usd_per_metric_ton"]) + " / mt"},
            {"measure": "World Bank benchmark", "value": fm.money(record["benchmark_price_usd_per_metric_ton"]) + " / mt"},
            {"measure": "Benchmark residual (log gap)", "value": fm.fmt(record.get("benchmark_residual"))},
            {"measure": "Rule score", "value": fm.score(record["rule_score"])},
            {"measure": "Challenger score", "value": fm.score(record["selected_challenger_score"])},
        ])
        plain_table(values, column_labels={"measure": "Measure", "value": "Value"})
    if record.get("benchmark_caveat") and pd.notna(record.get("benchmark_caveat")):
        st.caption(f"Benchmark caveat: {record['benchmark_caveat']}")
    ledger("review_queue", "features")

# ---- Tab 2: Trade & Benchmark Trend (actual corridor history, no indexing) ----
with trend_tab:
    history_columns = (
        "obs_id", "year", "exporter_iso3", "importer_iso3", "hs6",
        "trade_value_usd", "quantity_metric_ton", "unit_value_usd_per_metric_ton",
        "benchmark_price_usd_per_metric_ton", "benchmark_residual", "quality_status",
    )
    panel = load.load_panel(columns=history_columns)
    history = metrics.case_history(panel, record["exporter_iso3"], record["importer_iso3"], record["hs6"])
    if history.empty:
        st.info("No corridor history is available in the clean panel for this exporter–importer–HS6.")
    else:
        section_title(
            "Aggregate unit value vs World Bank benchmark",
            "Both series in USD per metric ton. The benchmark is broad market context, not invoice-level fair value.",
        )
        log_scale = st.toggle(
            "Log scale", value=False,
            help="Useful when the unit value sits orders of magnitude from the benchmark.",
        )
        show(unit_value_vs_benchmark(history, int(record["year"]), log_scale),
             height=420, key="case_unit_value_trend")

        left, right = st.columns(2, gap="large")
        with left:
            section_title("Trade value over time", "Annual aggregate trade value (USD).")
            show(history_line(history, "trade_value_usd", "USD", int(record["year"])),
                 key="case_trade_value")
        with right:
            section_title("Quantity over time", "Annual aggregate quantity (metric tons).")
            show(history_line(history, "quantity_metric_ton", "Metric tons", int(record["year"]), ",.3f"),
                 key="case_quantity")

        section_title("Benchmark residual over time",
                      "Log gap between the corridor's unit value and the benchmark; 0 means at benchmark.")
        show(residual_line(history, int(record["year"])), key="case_residual")

        observed_years = ", ".join(str(int(y)) for y in history["year"])
        st.caption(f"Observed years for this corridor-product: {observed_years}. Missing years were not traded or not reported.")
    ledger("panel")

# ---- Tab 3: Why It Ranked High (actual features + approved interpretations) ----
with why_tab:
    section_title(
        "Ranking signals for this observation",
        "Actual feature values with the project's approved plain-English interpretations. "
        "No generated explanations.",
    )
    signals = metrics.case_signals(record, load.load_feature_explanations())
    if signals.empty:
        st.info("No feature values are available for this observation.")
    else:
        display = signals.copy()
        display["value"] = display["value"].map(lambda v: fm.fmt(v, 3))
        plain_table(
            display,
            column_labels={
                "signal": "Signal", "value": "Value",
                "interpretation": "What it means (approved wording)",
                "time_safety": "Time-safety rule",
            },
            height=430,
        )
    if record.get("data_quality_flags") and pd.notna(record.get("data_quality_flags")):
        st.caption(f"Data-quality flags: `{record['data_quality_flags']}`")

    section_title("Model-contribution context (global)",
                  "Global model contribution context; not a row-specific explanation.")
    # Row-level SHAP values are not produced by the pipeline — only the global
    # summary exists, and it is labelled as such rather than presented per-case.
    shap_figure = load.figure_path("shap_summary")
    if shap_figure:
        st.image(str(shap_figure), width="stretch")
        st.caption("SHAP explains model behaviour; it is not factual or legal evidence. "
                   f"Source: reports/figures/{shap_figure.name}")
    else:
        missing_output("shap_summary_values")
    ledger("features", "feature_explanations")

# ---- Tab 4: Evidence ----
with evidence_tab:
    section_title(
        "Recomputable evidence",
        "Each card restates a metric that can be recomputed from the official data. "
        "Severity reflects distance from the metric's review threshold.",
    )
    if case_evidence.empty:
        st.info("No evidence rows exist for this observation in the evidence table.")
    else:
        evidence_cards(case_evidence)
        with st.expander("Evidence as a table"):
            plain_table(case_evidence[[
                "evidence_id", "evidence_type", "metric_name", "observed_value",
                "comparison_value", "comparison_group", "threshold", "severity",
                "plain_english_summary", "caveat",
            ]])
    ledger("evidence")

# ---- Tab 5: Limitations ----
with limits_tab:
    section_title("Case-specific caveats")
    case_caveats = case_evidence["caveat"].dropna().unique().tolist() if not case_evidence.empty else []
    if record.get("benchmark_caveat") and pd.notna(record.get("benchmark_caveat")):
        case_caveats.append(str(record["benchmark_caveat"]))
    if case_caveats:
        for caveat in dict.fromkeys(case_caveats):
            st.markdown(f"- {caveat}")
    else:
        st.markdown("- No evidence-specific caveats recorded for this case.")
    section_title("Project-wide limitations")
    for bullet in content["limitations"]:
        st.markdown(f"- {bullet}")
    st.markdown(f"- {copy['caveat']} Human review remains necessary before any conclusion.")
