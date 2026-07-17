"""The conclusion-boundary stamp shown on every page.

The sentence comes verbatim from configs/project.yml (`conclusion_boundary`) —
the dashboard cannot drift from the pipeline's approved wording.

boundary_ribbon() renders the slim fixed footer ONCE per run (from
streamlit_app.py), so the boundary is always visible on every page.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon
from dashboard.services.data_loader import conclusion_boundary, load_content


def render_boundary_footer() -> None:
    # Fixed to the viewport bottom via .boundary-ribbon in components/styles.py;
    # its DOM position inside the main block does not matter visually.
    label = load_content().get("boundary_label", "Human-review boundary")
    st.markdown(
        f'<div class="boundary-ribbon">{render_icon("shield-check", class_name="boundary-icon")}'
        f'<span class="stamp">{html.escape(label)}</span>'
        f"<span>{html.escape(conclusion_boundary())}</span></div>",
        unsafe_allow_html=True,
    )


def boundary_ribbon() -> None:
    """Compatibility alias for the application entry point."""
    render_boundary_footer()
