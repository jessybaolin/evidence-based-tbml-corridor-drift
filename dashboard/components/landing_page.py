"""The full-screen welcome (landing) screen shown before the dashboard shell.

Rendered only on the root route. The product description comes verbatim from
the existing `app` block of dashboard_content.yml; the hero title, eyebrow and
call-to-action are the landing-only copy in the `landing` block. Nothing is
reworded in code — every string lives in content.yml.

The CTA is a real Streamlit button: clicking it records the session flag via
services.session_state and switches to Business Problem and Value. No timers, no
automatic redirects — the user always chooses to enter.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.services import session_state as state
from dashboard.services.data_loader import load_content

DASHBOARD_ENTRY_PAGE = "app_pages/executive_overview.py"


def _title_markup(title_lines: list[str]) -> str:
    # Each configured phrase is its own hero line (a block span); a phrase still
    # wraps within itself on a narrow viewport, so nothing overflows.
    return " ".join(
        f'<span class="welcome-title-line">{html.escape(str(line))}</span>'
        for line in title_lines
    )


def render_landing() -> None:
    # The landing sheet (styles.apply_landing_styles) is injected once by the
    # entry point, which owns route styling — never a second time here.
    state.init_landing()
    content = load_content()
    app = content["app"]
    landing = content["landing"]

    st.markdown(
        f'<div class="welcome-hero">'
        f'<div class="welcome-accent" aria-hidden="true"></div>'
        f'<div class="welcome-eyebrow">{html.escape(landing["eyebrow"])}</div>'
        f'<h1 class="welcome-title">{_title_markup(landing["title_lines"])}</h1>'
        f'<p class="welcome-sub">{html.escape(app["subtitle"])}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.container(key="welcome_cta"):
        if st.button(
            landing["cta"],
            key="landing_enter",
            type="primary",
            icon=":material/arrow_forward:",
        ):
            state.complete_landing()
            st.switch_page(DASHBOARD_ENTRY_PAGE)
