"""Appendix — data dictionary and official data sources."""

from __future__ import annotations

import streamlit as st

from dashboard.components.boundary_banner import boundary_banner
from dashboard.components.empty_states import missing_output
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.source_cards import source_card
from dashboard.components.tables import plain_table
from dashboard.services import data_dictionary as dictionary
from dashboard.services import data_loader as load
from dashboard.services.source_registry import build_source_cards

content = load.load_content()
copy = content["pages"]["appendix"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
boundary_banner()

dictionary_tab, sources_tab = st.tabs(["Data Dictionary", "Official Data Sources"])

# ---- Tab 1: Data Dictionary ----
with dictionary_tab:
    section_title(
        "Project data dictionary",
        "Documented definitions come from reports/feature_explanation_table.md and "
        "reports/data_dictionary.md; rows marked schema-inferred describe the column "
        "as stored without inventing a definition.",
    )

    @st.cache_data(show_spinner=False)
    def _dictionary_table():
        schemas = {
            "corridor_product_year_panel.parquet": load.load_panel(),
            "corridor_features.parquet": load.load_features(),
            "top_ranked_corridors.csv": load.load_review_queue(),
            "evidence_table.csv": load.load_evidence(),
            "model_comparison.csv": load.load_model_comparison(),
        }
        return dictionary.build_dictionary(
            schemas, load.load_feature_explanations(), load.load_data_dictionary_md(),
        )

    table = _dictionary_table()

    f1, f2, f3, f4 = st.columns([1.4, 1.4, 1.2, 2])
    with f1:
        categories = st.multiselect("Field category", [str(c) for c in table["category"].cat.categories],
                                    key="dict_categories")
    with f2:
        datasets = st.multiselect("Dataset", sorted(table["dataset"].unique()), key="dict_datasets")
    with f3:
        sources = st.multiselect("Definition source",
                                 sorted(table["definition_source"].unique()), key="dict_sources")
    with f4:
        search = st.text_input("Search field name or definition", key="dict_search",
                               placeholder="e.g. residual, unit value, severity")

    filtered = table
    if categories:
        filtered = filtered[filtered["category"].astype(str).isin(categories)]
    if datasets:
        filtered = filtered[filtered["dataset"].isin(datasets)]
    if sources:
        filtered = filtered[filtered["definition_source"].isin(sources)]
    if search:
        needle = search.strip().lower()
        haystack = (filtered["field"].str.lower() + " " + filtered["definition"].str.lower()
                    + " " + filtered["derivation"].str.lower())
        filtered = filtered[haystack.str.contains(needle, regex=False)]

    st.caption(f"{len(filtered):,} of {len(table):,} dictionary rows match.")
    if filtered.empty:
        st.info("No dictionary rows match. Clear a filter or broaden the search.")
    else:
        # Thematic sections instead of one very wide table.
        for category in filtered["category"].cat.categories:
            block = filtered[filtered["category"] == category]
            if block.empty:
                continue
            section_title(str(category))
            plain_table(
                block[["field", "dataset", "data_type", "definition", "derivation",
                       "unit", "time_safety_rule", "quality_caveat", "definition_source",
                       "dashboard_pages"]],
                column_labels={
                    "field": "Field", "dataset": "Dataset", "data_type": "Type",
                    "definition": "Definition", "derivation": "Derivation", "unit": "Unit",
                    "time_safety_rule": "Time-safety rule", "quality_caveat": "Caveat / significance",
                    "definition_source": "Definition source", "dashboard_pages": "Used on",
                },
                height=min(72 + 35 * len(block), 420),
            )
    ledger("feature_explanations", "data_dictionary_md",
           note="plus schemas of the five loaded artefacts")

# ---- Tab 2: Official Data Sources ----
with sources_tab:
    section_title(
        "Official source datasets",
        "Publisher, release, units, transformations, and provenance for every source the lab uses.",
    )
    notes = load.load_data_source_notes()
    manifest = load.load_source_manifest()
    if notes is None and manifest is None:
        missing_output("data_source_notes")
    else:
        for card in build_source_cards(notes, manifest):
            source_card(card)
    st.markdown(f"> {content['provenance_note']}")
    ledger("data_source_notes", "source_manifest",
           note="World Bank + FATF URLs from the dashboard registry (services/source_registry.py)")
