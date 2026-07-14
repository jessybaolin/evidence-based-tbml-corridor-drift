"""The conclusion-boundary stamp shown on every page.

The sentence comes verbatim from configs/project.yml (`conclusion_boundary`) —
the dashboard cannot drift from the pipeline's approved wording.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.services.data_loader import conclusion_boundary, load_content


def boundary_banner() -> None:
    label = load_content().get("boundary_label", "Human-review boundary")
    st.markdown(
        f"""
        <div class="boundary-banner">
        <span class="stamp">{html.escape(label)}</span>
        {html.escape(conclusion_boundary())}
        </div>
        """,
        unsafe_allow_html=True,
    )
