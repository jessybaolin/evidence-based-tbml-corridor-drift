"""Data Dictionary — analytical definitions and official data sources."""

from __future__ import annotations

import streamlit as st

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

dictionary_tab, sources_tab = st.tabs(["Key Data Fields", "Official Data Sources"])

# ---- Tab 1: Key Data Fields ----
with dictionary_tab:
    section_title("Fields used in analysis and review", icon="file-search")

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

    sections = {
        "Derived financial metrics": ("Trade and benchmark measures", "line-chart"),
        "Time-safe features": ("Historical and peer comparison signals", "calendar"),
        "Model scores": ("Review-priority outputs", "list-ordered"),
    }
    table = _dictionary_table()
    table = table[table["category"].astype(str).isin(sections)].copy()
    # A field can occur in several output files. Stakeholders need one definition,
    # not a repeated schema row for every artefact that carries it.
    table = (
        table.sort_values(["category", "field", "dataset"])
        .drop_duplicates(subset="field", keep="first")
        .reset_index(drop=True)
    )

    search = st.text_input(
        "Search key fields",
        key="dict_search",
        placeholder="e.g. unit value, benchmark, historical change",
        icon=":material/search:",
    )

    filtered = table
    if search:
        needle = search.strip().lower()
        haystack = (filtered["field"].str.lower() + " " + filtered["definition"].str.lower()
                    + " " + filtered["derivation"].str.lower())
        filtered = filtered[haystack.str.contains(needle, regex=False)]

    st.caption(f"{len(filtered):,} key fields shown.")
    if filtered.empty:
        st.info("No key fields match. Try a broader search.")
    else:
        for category, (title, icon) in sections.items():
            block = filtered[filtered["category"] == category]
            if block.empty:
                continue
            section_title(title, icon=icon)
            plain_table(
                block[["field", "definition", "derivation", "unit", "time_safety_rule",
                       "quality_caveat"]],
                column_labels={
                    "field": "Field", "definition": "What it means",
                    "derivation": "How it is calculated", "unit": "Unit",
                    "time_safety_rule": "Time-safety rule",
                    "quality_caveat": "Why it matters / caveat",
                },
                # Field names are long single tokens, so auto-layout gave them
                # the widest column and squeezed the four prose columns into
                # four- and five-line cells. These shares put the width where
                # the reading is.
                column_widths={
                    "field": "17%", "definition": "19%", "derivation": "20%",
                    "unit": "8%", "time_safety_rule": "17%", "quality_caveat": "19%",
                },
                height=min(96 + 72 * len(block), 640),
            )
    ledger("feature_explanations", "data_dictionary_md")

# ---- Tab 2: Official Data Sources ----
with sources_tab:
    section_title("Official source datasets", icon="database")
    notes = load.load_data_source_notes()
    manifest = load.load_source_manifest()
    if notes is None and manifest is None:
        missing_output("data_source_notes")
    else:
        for card in build_source_cards(notes, manifest):
            source_card(card)
    ledger("data_source_notes", "source_manifest")
