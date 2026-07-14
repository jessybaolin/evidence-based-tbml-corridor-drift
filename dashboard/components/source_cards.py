"""Official data-source cards for the Appendix."""

from __future__ import annotations

import html

import streamlit as st

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
            f'<span style="opacity:0.7;">({html.escape(card.url_origin)})</span></div>'
        )
    else:
        link = '<div class="source-row"><b>Official URL:</b> not recorded in project metadata</div>'
    st.markdown(
        f'<div class="source-card"><h4>{html.escape(card.name)}</h4>{body}{link}</div>',
        unsafe_allow_html=True,
    )
