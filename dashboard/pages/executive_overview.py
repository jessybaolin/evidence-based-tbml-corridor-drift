"""Executive Overview — the ten-second read: scope, headline KPIs, where to go next."""

from __future__ import annotations

import streamlit as st

from dashboard.components.boundary_banner import boundary_banner
from dashboard.components.charts import bar_by_family, show
from dashboard.components.kpi_cards import kpi_row
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.status_badges import quality_label
from dashboard.components.tables import plain_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load

content = load.load_content()
copy = content["pages"]["executive_overview"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
boundary_banner()
st.markdown(copy["explanation"])

# ---- KPI cards (all derived; the ledger below names the backing files) ----
panel = load.load_panel(columns=("obs_id", "year", "family_id", "product_name",
                                 "quality_status", "model_eligible", "hs6"))
queue = load.load_review_queue()
evidence = load.load_evidence()
comparison = load.load_model_comparison()
selection = load.load_model_selection()
manifest = load.load_source_manifest()

kpis = metrics.overview_kpis(panel, queue, evidence, comparison, selection, manifest)
labels = content["overview_kpis"]
kpi_row([
    {"label": labels["observations"], "value": kpis["observations"]["value"],
     "detail": kpis["observations"]["detail"]},
    {"label": labels["model_eligible"], "value": kpis["model_eligible"]["value"],
     "detail": kpis["model_eligible"]["detail"]},
    {"label": labels["queue"], "value": kpis["queue"]["value"],
     "detail": kpis["queue"]["detail"]},
    {"label": labels["evidence"], "value": kpis["evidence"]["value"],
     "detail": kpis["evidence"]["detail"]},
])
kpi_row([
    {"label": labels["families"], "value": kpis["families"]["value"],
     "detail": kpis["families"]["detail"]},
    {"label": labels["models"], "value": kpis["models"]["value"],
     "detail": kpis["models"]["detail"]},
    {"label": labels["validation"], "value": kpis["validation"]["value"],
     "detail": kpis["validation"]["detail"]},
    {"label": labels["selected_method"], "value": kpis["selected_method"]["value"],
     "detail": kpis["selected_method"]["detail"]},
])
ledger("panel", "review_queue", "evidence", "model_comparison", "model_selection")

st.write("")
left, right = st.columns([1.35, 1], gap="large")

with left:
    section_title("Top five review candidates",
                  "Open the Review Queue for filters, search, and row selection.")
    short_labels = content["family_short_labels"]
    preview = queue.nsmallest(5, "rank").copy()
    preview["corridor"] = preview["exporter_iso3"] + " → " + preview["importer_iso3"]
    preview["family_label"] = preview["family_id"].map(short_labels).fillna(preview["product_name"])
    preview["quality_status_label"] = preview["quality_status"].map(quality_label)
    plain_table(
        preview[["rank", "year", "corridor", "family_label",
                 "selected_review_priority_score", "quality_status_label"]],
        column_labels={
            "rank": "Rank", "year": "Year", "corridor": "Corridor",
            "family_label": "Product", "selected_review_priority_score": "Review-priority score",
            "quality_status_label": "Data quality",
        },
    )
    ledger("review_queue", note=f"score = {metrics.selected_method_label(selection)}")

with right:
    section_title("Official-data coverage by product family",
                  "Filtered official BACI rows per selected HS6 family.")
    coverage = metrics.family_coverage(panel, content["family_short_labels"])
    show(bar_by_family(coverage, x="family_label", y="panel_rows",
                       y_title="Official panel rows", hover=["hs6", "model_eligible"]),
         key="exec_family_coverage")
    ledger("panel")

# ---- Data quality + limitations ----
quality_col, limits_col = st.columns(2, gap="large")
with quality_col:
    section_title("Data-quality summary",
                  "Quality is a usability signal, kept separate from suspiciousness.")
    quality = metrics.quality_summary(panel)
    quality["label"] = quality["quality_status"].map(quality_label)
    for _, row in quality.iterrows():
        st.markdown(f"- **{row['label']}** — {row['rows']:,} rows ({row['share']:.0%})")
    ledger("panel")
with limits_col:
    section_title("Key limitations")
    for bullet in content["limitations"]:
        st.markdown(f"- {bullet}")

# ---- Navigation guidance ----
section_title("How to use this dashboard")
step_cols = st.columns(len(content["navigation_steps"]))
for index, (column, (title, text)) in enumerate(zip(step_cols, content["navigation_steps"]), start=1):
    with column:
        st.markdown(
            f'<div class="info-card"><span class="step-pill">STEP {index}</span>'
            f"<h4>{title}</h4><p>{text}</p></div>",
            unsafe_allow_html=True,
        )
