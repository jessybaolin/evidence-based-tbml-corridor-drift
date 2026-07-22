"""The full-screen welcome (landing) screen shown before the dashboard shell.

Rendered only on the root route. Every copy string lives in content.yml
(`landing` block + `app.subtitle`); nothing is reworded in code. The two CTAs
are real Streamlit buttons — clicking either records the session flag via
services.session_state and switches into the dashboard. No timers, no automatic
redirects: the user always chooses to enter.

Layout mirrors the design handoff (references/design_handoff_landing_and_showcase):
a top-bar, a centred hero, a three-node "how it works" pipeline, a scroll cue,
and a browser-framed screenshot of the live Top 50 Review Queue. All colour,
size, spacing and motion live in styles.apply_landing_styles(); this module owns
only structure + the (decorative, currentColor) inline SVGs.
"""

from __future__ import annotations

import base64
import html

import streamlit as st

from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.services import session_state as state
from dashboard.services.data_loader import load_content
from dashboard.services.path_resolver import DATA_OUTPUTS

# The CTA hands over to Business Problem and Value (executive_overview.py). This
# route and the session flow are intentionally unchanged from the prior landing.
DASHBOARD_ENTRY_PAGE = "app_pages/executive_overview.py"

# Top-bar nav targets, in the same order as landing.nav (content.yml). Home
# returns to this landing (root); Methodology and Review queue deep-link into
# their dashboard pages via Streamlit's per-page URL paths (the script-file
# stems). Routing is unchanged — these just link to routes that already exist.
_NAV_HREFS = ("/", "/model_and_controls", "/review_queue")

_SVG_OPEN = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-linecap="round" stroke-linejoin="round"'
)
# Exact glyphs from the design reference (Lucide-style). Coloured via CSS.
_HOME_SVG = (
    f'{_SVG_OPEN} width="15" height="15" stroke-width="2">'
    '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/></svg>'
)
_LINE_CHART_SVG = (
    f'{_SVG_OPEN} width="22" height="22" stroke-width="1.9">'
    '<path d="M4 18l4-5 3 3 5-7 4 5"/><path d="M4 21h16"/></svg>'
)
_RANKED_SVG = (
    f'{_SVG_OPEN} width="22" height="22" stroke-width="1.9">'
    '<path d="M9 6l2 2 3-3M9 12l2 2 3-3M9 18l2 2 3-3M18 6h2M18 12h2M18 18h2"/></svg>'
)
_SHIELD_SVG = (
    f'{_SVG_OPEN} width="22" height="22" stroke-width="2">'
    '<path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/>'
    '<path d="M9 12l2 2 4-4"/></svg>'
)
_CHEVRON_SVG = (
    f'{_SVG_OPEN} class="lp-chev" width="18" height="18" stroke-width="2">'
    '<path d="M6 9l6 6 6-6"/></svg>'
)
_LOCK_SVG = (
    f'{_SVG_OPEN} width="12" height="12" stroke-width="2.4">'
    '<rect x="5" y="11" width="14" height="10" rx="2"/>'
    '<path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>'
)

_NODE_SVGS = (_LINE_CHART_SVG, _RANKED_SVG, _SHIELD_SVG)
_NODE_KINDS = ("lp-node-open", "lp-node-open", "lp-node-fill")


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


@st.cache_data(show_spinner=False)
def _screenshot_uri() -> str:
    """The Top-50 queue screenshot as an inline data URI for the framed preview.

    Embedding inline keeps the browser-chrome framing as one CSS-styled block
    (Streamlit cannot wrap st.image in custom markup). Cached so the base64 is
    computed once per session.
    """
    path = DATA_OUTPUTS / "top_50_review_queue_hero.png"
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _cta(container_key: str, button_key: str, label: str) -> None:
    """One real Streamlit CTA button (routing + session flow unchanged)."""
    with st.container(key=container_key):
        if st.button(label, key=button_key, type="primary",
                     icon=":material/arrow_forward:"):
            state.complete_landing()
            st.switch_page(DASHBOARD_ENTRY_PAGE)


def render_landing() -> None:
    # The landing sheet (styles.apply_landing_styles) is injected once by the
    # entry point, which owns route styling — never a second time here.
    state.init_landing()
    content = load_content()
    app = content["app"]
    landing = content["landing"]

    nav_items = "".join(
        f'<a class="lp-nav-item{" active" if index == 0 else ""}" '
        f'href="{_NAV_HREFS[index] if index < len(_NAV_HREFS) else "/"}" target="_self">'
        f'{_HOME_SVG if index == 0 else ""}{_e(label)}</a>'
        for index, label in enumerate(landing["nav"])
    )
    title_lines = "".join(f"<span>{_e(line)}</span>" for line in landing["title_lines"])

    # --- Top bar + hero (the CTA below is a real button, so it is separate) ---
    st.markdown(
        '<div class="lp-root">'
        '<header class="lp-topbar lp-anim lp-d-nav">'
        '<div class="lp-brand" aria-hidden="true"></div>'
        f'<nav class="lp-nav">{nav_items}</nav>'
        '</header>'
        '<main class="lp-hero">'
        '<div class="lp-accent lp-anim lp-d-accent" aria-hidden="true"></div>'
        f'<div class="lp-eyebrow lp-anim lp-d-eyebrow">{_e(landing["eyebrow"])}</div>'
        f'<h1 class="lp-h1 lp-anim lp-d-h1">{title_lines}</h1>'
        f'<p class="lp-sub lp-anim lp-d-sub">{_e(app["subtitle"])}</p>'
        '</main>'
        '</div>',
        unsafe_allow_html=True,
    )
    _cta("welcome_cta", "landing_enter", landing["cta"])

    # --- How it works (pipeline) + scroll cue + product preview ---
    nodes = "".join(
        '<div class="lp-node-col">'
        f'<div class="lp-node {_NODE_KINDS[index]}">{_NODE_SVGS[index]}</div>'
        f'<div class="lp-step">{_e(step["step"])}</div>'
        f'<div class="lp-node-title">{_e(step["title"])}</div>'
        f'<div class="lp-node-body">{_e(step["body"])}</div>'
        '</div>'
        for index, step in enumerate(landing["pipeline"])
    )

    uri = _screenshot_uri()
    shot = (
        f'<img class="lp-shot" src="{uri}" alt="Top 50 review queue" loading="lazy">'
        if uri else ""
    )

    st.markdown(
        '<section class="lp-pipeline reveal">'
        '<div class="lp-track" aria-hidden="true"></div>'
        f'{nodes}'
        '</section>'
        '<div class="lp-scrollcue lp-anim lp-d-cue">'
        '<div class="lp-cue-inner">'
        f'<span class="lp-cue-label">{_e(landing["scroll_cue"])}</span>'
        '<div class="lp-mouse" aria-hidden="true"><span class="lp-dot"></span></div>'
        f'{_CHEVRON_SVG}'
        '</div></div>'
        '<section class="lp-product reveal">'
        '<div class="lp-pedestal" aria-hidden="true"></div>'
        '<div class="lp-frame">'
        '<div class="lp-chrome">'
        '<span class="lp-light r"></span>'
        '<span class="lp-light y"></span>'
        '<span class="lp-light g"></span>'
        '<div class="lp-chrome-center">'
        f'<div class="lp-url">{_LOCK_SVG}<span>{_e(landing["product_url"])}</span></div>'
        '</div></div>'
        f'<div class="lp-screen">{shot}'
        '<div class="lp-scan" aria-hidden="true"></div>'
        '<div class="lp-fade" aria-hidden="true"></div>'
        '</div></div>'
        f'<div class="lp-caption">{_e(landing["product_caption"])}</div>'
        '</section>',
        unsafe_allow_html=True,
    )
    _cta("welcome_cta_closing", "landing_enter_closing", landing["cta"])

    # Product section fades/rises as it enters view (fail-safe: visible if the
    # observer is ever blocked). Hero motion is the on-load CSS keyframes above.
    render_scroll_reveal(".reveal")
