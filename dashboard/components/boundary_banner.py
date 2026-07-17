"""The conclusion-boundary stamp shown on every page.

The sentence comes verbatim from configs/project.yml (`conclusion_boundary`) —
the dashboard cannot drift from the pipeline's approved wording.

boundary_ribbon() renders the slim fixed footer ONCE per run (from
streamlit_app.py), so the boundary is always visible on every page.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.services.data_loader import conclusion_boundary, load_content


def boundary_ribbon() -> None:
    # Fixed to the viewport bottom via .boundary-ribbon in components/styles.py;
    # its DOM position inside the main block does not matter visually.
    label = load_content().get("boundary_label", "Human-review boundary")
    st.markdown(
        f'<div class="boundary-ribbon"><span class="stamp">{html.escape(label)}</span>'
        f"<span>{html.escape(conclusion_boundary())}</span></div>",
        unsafe_allow_html=True,
    )
