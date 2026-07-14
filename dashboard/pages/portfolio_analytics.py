"""Portfolio Analytics — patterns across the official review population."""

from __future__ import annotations

import streamlit as st

from dashboard.components.boundary_banner import boundary_banner
from dashboard.components.charts import (
    bar_by_family, bar_single, histogram_emphasis, severity_stack, score_strip, show,
)
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load

content = load.load_content()
copy = content["pages"]["portfolio_analytics"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
boundary_banner()

queue = load.load_review_queue()
features = load.load_features(columns=(
    "obs_id", "exporter_name", "importer_name", "benchmark_residual", "robust_historical_z",
))
enriched = metrics.enrich_queue(queue, features, content["family_short_labels"])
evidence = load.load_evidence()
panel = load.load_panel(columns=("obs_id", "benchmark_residual", "quality_status", "year", "family_id"))

# ---- Queue composition ----
left, right = st.columns(2, gap="large")
with left:
    # The caption derives its claim from the same frame the chart plots, so a
    # pipeline rerun can never leave a stale analytic statement on screen.
    by_year = metrics.candidates_by_year(enriched)
    top_year = by_year.loc[by_year["candidates"].idxmax()]
    section_title(
        "Review candidates by year",
        f"Where the top-{len(enriched)} queue concentrates in time. "
        f"{int(top_year['year'])} leads the current run "
        f"({int(top_year['candidates'])} of {int(by_year['candidates'].sum())} candidates).",
    )
    show(bar_single(by_year, x="year", y="candidates", y_title="Review candidates"),
         key="pa_candidates_by_year")
with right:
    section_title("Review candidates by product family",
                  "Candidate counts across the three selected HS6 families.")
    show(bar_by_family(metrics.candidates_by_family(enriched), x="family_label",
                       y="candidates", y_title="Review candidates"),
         key="pa_candidates_by_family")
ledger("review_queue")

# ---- Scores in context ----
section_title("Review-priority scores by year and product",
              "Each mark is one review candidate; colour is the product family.")
show(score_strip(enriched), height=400, key="pa_score_strip")
ledger("review_queue")

section_title(
    "Benchmark residuals: queue vs full official population",
    "Log gap to the World Bank benchmark. Gray: all official observations; "
    "blue: the review queue. Review candidates sit in the tails.",
)
population, selected = metrics.residual_context(panel, enriched)
show(histogram_emphasis(population, selected, "Log gap to benchmark",
                        "All official observations", "Review queue"),
     height=400, key="pa_residual_hist")
ledger("panel", "review_queue")

# ---- Concentration ----
section_title("Corridor concentration in the review queue",
              "Countries and corridors appearing most often among the top-ranked candidates.")
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    st.markdown("**By exporter**")
    show(bar_single(metrics.concentration(enriched, "exporter_iso3"), x="exporter_iso3",
                    y="candidates", y_title="Candidates", horizontal=True),
         height=320, key="pa_conc_exporter")
with c2:
    st.markdown("**By importer**")
    show(bar_single(metrics.concentration(enriched, "importer_iso3"), x="importer_iso3",
                    y="candidates", y_title="Candidates", horizontal=True),
         height=320, key="pa_conc_importer")
with c3:
    st.markdown("**By corridor**")
    show(bar_single(metrics.concentration(enriched, "corridor"), x="corridor",
                    y="candidates", y_title="Candidates", horizontal=True),
         height=320, key="pa_conc_corridor")
st.caption("Counts describe the top-ranked queue, not the full trade population; "
           "small counts should not be read as country risk ratings.")
ledger("review_queue")

# ---- Evidence severity ----
section_title("Evidence by type and severity",
              f"How the {len(evidence):,} evidence rows distribute across metrics and severity bands.")
show(severity_stack(metrics.severity_distribution(evidence)), height=380, key="pa_severity_stack")
ledger("evidence")
