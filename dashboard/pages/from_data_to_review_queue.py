"""From Data to Review Queue — the governed methodology story.

A read-only, top-to-bottom narrative of how official public trade data becomes
the human-review queue: official sources, source-to-output flow, time-safe
feature construction, and train/validation/test evaluation. It adds NO new
analytics — every number is derived live from the existing loaders, and every
diagram is an existing report figure. The story deliberately STOPS at the review
queue and its recomputable evidence; the downstream analyst-brief step is out of
scope for this dashboard.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.boundary_banner import boundary_banner
from dashboard.components.empty_states import missing_figure
from dashboard.components.kpi_cards import kpi_row
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

content = load.load_content()
copy = content["pages"]["from_data_to_review_queue"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
boundary_banner()

st.markdown(
    "This page traces the governed path from official public data to the review "
    "queue. Each stage below pairs a short explanation with the pipeline diagram "
    "that documents it. The path ends where the dashboard ends: a ranked list of "
    "**official observations** for **human review**, each backed by recomputable "
    "evidence. It does not decide anything about any party."
)

# ---- The pipeline in real numbers (all derived from the loaders) -------------
panel = load.load_panel(columns=("obs_id", "year", "model_eligible"))
queue = load.load_review_queue()
evidence = load.load_evidence()

section_title(
    "The pipeline in real numbers",
    "Derived live from the loaded artefacts — the funnel from every official row "
    "to the evidence rows that support the queue.",
)
kpi_row([
    {"label": "Official observations",
     "value": f"{len(panel):,}",
     "detail": f"{fm.year_span(panel['year'].unique())}, one row per corridor-product-year (clean panel)"},
    {"label": "Model-eligible observations",
     "value": f"{int(panel['model_eligible'].sum()):,}",
     "detail": "rows with a valid unit value and usable quality status"},
    {"label": "Review candidates",
     "value": f"{len(queue):,}",
     "detail": "top-ranked official observations placed on the queue"},
    {"label": "Evidence rows",
     "value": f"{len(evidence):,}",
     "detail": f"recomputable evidence across {evidence['obs_id'].nunique()} candidates"},
])
ledger("panel", "review_queue", "evidence")

st.divider()

# ---- Stage walkthrough -------------------------------------------------------
# Each stage: a governed heading + 1–2 sentences + the documenting figure.
STAGES = [
    {
        "heading": "Stage 1 · Official sources",
        "body": (
            "The pipeline starts from official or official-derived public data — the "
            "CEPII BACI trade panel and World Bank commodity benchmarks — with every "
            "declared input hashed and verified. These are annual, aggregate figures, "
            "not invoices, shipments, or payments."
        ),
        "figure_key": "official_data_pipeline_architecture",
        "figure_name": "official_data_pipeline_architecture.png",
        "figure_label": "The official-data pipeline architecture diagram",
    },
    {
        "heading": "Stage 2 · Source-to-output flow",
        "body": (
            "Verified sources are cleaned into a single corridor–product–year panel, "
            "one row per exporter–importer–product–year. This flow keeps a traceable "
            "line from each raw source to each analytical output, so any figure on the "
            "queue can be traced back to the file that produced it."
        ),
        "figure_key": "source_to_report_data_flow",
        "figure_name": "source_to_report_data_flow.png",
        "figure_label": "The source-to-output data-flow diagram",
    },
    {
        "heading": "Stage 3 · Time-safe features",
        "body": (
            "Each observation is compared against its own prior history, its same-year "
            "peers, and the year's benchmark to build time-safe features. Historical "
            "features use prior years only, so a row is never described using "
            "information that would not have been available at the time."
        ),
        "figure_key": "time_safe_feature_construction_flow",
        "figure_name": "time_safe_feature_construction_flow.png",
        "figure_label": "The time-safe feature-construction diagram",
    },
    {
        "heading": "Stage 4 · Train / validation / test evaluation",
        "body": (
            "A rules baseline and machine-learning challengers are evaluated on "
            "controlled synthetic scenarios — evaluation constructs, not confirmed "
            "TBML — split by year so evaluation never sees the future. The selected, "
            "rules-anchored blend is then applied to the real official observations to "
            "rank them for review."
        ),
        "figure_key": "train_validation_test_ml_workflow",
        "figure_name": "train_validation_test_ml_workflow.png",
        "figure_label": "The train / validation / test workflow diagram",
    },
]

for stage in STAGES:
    section_title(stage["heading"])
    st.markdown(stage["body"])
    figure = load.figure_path(stage["figure_key"])
    if figure:
        st.image(str(figure), width="stretch",
                 caption=f"Source: reports/figures/{stage['figure_name']}")
    else:
        missing_figure(f"reports/figures/{stage['figure_name']}", stage["figure_label"])
    st.write("")

st.divider()

# ---- Where the story stops ---------------------------------------------------
section_title(
    "Where the story stops",
    "The dashboard ends at the review queue and its evidence.",
)
st.markdown(
    "The output of this pipeline is a **review queue** of unusual corridor–product "
    "patterns, each paired with **recomputable evidence** a human can check. That is "
    "the last step shown here. Deciding what any pattern means is the reviewer's job, "
    "not the model's — a high review-priority score marks an **unusual pattern** worth "
    "a look, never a probability of crime or a finding of wrongdoing."
)
ledger("review_queue", "evidence", "project_config",
       note="figures: reports/figures (pipeline-generated)")
