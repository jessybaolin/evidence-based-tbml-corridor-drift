"""Official data-source cards for the Appendix."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.cards import source_card_markup
from dashboard.services.source_registry import SourceCard, is_valid_https_url


def source_card(card: SourceCard) -> None:
    rows = [
        ("Publisher", card.publisher),
        ("Project use", card.project_use),
        ("Release / version", card.release),
        ("Years used", card.years_used),
        ("Fields / series used", card.fields_used),
        ("Original unit", card.original_unit),
        ("Project transformation", card.transformation),
        ("Provenance", card.provenance),
        ("Important caveat", card.caveat),
    ]
    body = "".join(
        f'<div class="source-row"><b>{html.escape(label)}:</b> {html.escape(value)}</div>'
        for label, value in rows if value
    )
    if is_valid_https_url(card.url):
        link = (
            f'<div class="source-row"><b>Official URL:</b> '
            f'<a href="{html.escape(card.url)}" target="_blank">{html.escape(card.url)}</a> '
            f'<span class="source-origin">({html.escape(card.url_origin)})</span></div>'
        )
    else:
        link = '<div class="source-row"><b>Official URL:</b> not recorded in project metadata</div>'
    role = (
        "official" if card.key == "cepii_baci"
        else "benchmark" if card.key == "worldbank_cmo"
        else "typology"
    )
    icon = {"official": "landmark", "benchmark": "line-chart", "typology": "file-search"}[role]
    st.markdown(source_card_markup(
        role=role,
        icon=icon,
        eyebrow=card.publisher,
        title=card.name,
        sections_html=body + link,
        extra_classes="appendix-source-card",
    ), unsafe_allow_html=True)
