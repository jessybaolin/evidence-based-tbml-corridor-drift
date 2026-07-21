"""
Evidence-First TBML Corridor Drift Lab — multipage Streamlit dashboard entry point.

WHAT IT DOES:
    Boots the app: puts the repository root on sys.path (so `dashboard.*`
    imports work no matter where the terminal was opened), applies the global
    theme, registers the pages with st.navigation, and renders the fixed
    human-review boundary ribbon that rides on every dashboard page. The
    root/default route is the full-screen welcome landing, which renders
    WITHOUT the shell (no sidebar, no ribbon); its CTA enters the dashboard.

RUN (from the repository root):
    python -m streamlit run dashboard/streamlit_app.py

READS (inputs): generated pipeline outputs via dashboard.services.data_loader.
WRITES (outputs): nothing — this is a read-only presentation layer.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repo root on sys.path BEFORE any dashboard.* import. st.navigation re-runs
# this script on every interaction, so the pages always execute after this.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from dashboard.components.boundary_banner import render_boundary_footer
from dashboard.components.styles import (
    apply_dashboard_entry_styles,
    apply_global_styles,
    apply_landing_styles,
)
from dashboard.services import session_state as state
from dashboard.services.data_loader import MissingOutputError, load_content

content = load_content()

st.set_page_config(
    page_title=content["app"]["short_title"],
    page_icon=content["app"]["icon"],
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()

# Page metadata in one place. Material Symbol icons (":material/<name>:") render
# as monochrome glyphs in the theme colour — frost on the navy sidebar.
# NOTE: page files live in app_pages/ (NOT pages/) on purpose: a directory
# literally named "pages" next to the entry point triggers Streamlit's MPA-v1
# compatibility path, under which a cold-session deep link executes the page
# file alone — without the global styles, sidebar, or boundary ribbon.
PAGE_GROUPS = {
    "Business & Review": [
        {"path": "app_pages/executive_overview.py", "title": "Business Problem & Value",
         "icon": ":material/account_balance:"},
        {"path": "app_pages/from_data_to_review_queue.py", "title": "From Data to Review Queue",
         "icon": ":material/account_tree:"},
        {"path": "app_pages/portfolio_analytics.py", "title": "Trade Landscape and Patterns",
         "icon": ":material/trending_up:"},
        {"path": "app_pages/review_queue.py", "title": "Top 50 Review Queue",
         "icon": ":material/checklist:"},
        {"path": "app_pages/case_investigation.py", "title": "Selected Case Review",
         "icon": ":material/search:"},
    ],
    "Methodology": [
        {"path": "app_pages/model_and_controls.py", "title": "Model Evaluation & Controls",
         "icon": ":material/verified_user:"},
    ],
    "Future State": [
        {"path": "app_pages/bank_implementation_pathway.py", "title": "Bank Implementation Pathway",
         "icon": ":material/hub:"},
    ],
    "Appendix": [
        {"path": "app_pages/appendix.py", "title": "Data Dictionary",
         "icon": ":material/menu_book:"},
    ],
}

# Build the st.Page objects and register them for routing, but HIDE Streamlit's
# built-in sidebar menu (position="hidden"). Its auto-nav injects fixed vertical
# spacing we cannot fully override; instead we render our own navigation with
# st.page_link below, so the whole sidebar is one container we style top-to-bottom.
nav_groups: dict[str, list] = {}
page_by_path: dict[str, "st.Page"] = {}
for group_name, entries in PAGE_GROUPS.items():
    built = []
    for entry in entries:
        page = st.Page(entry["path"], title=entry["title"], icon=entry["icon"],
                       default=entry.get("default", False))
        built.append(page)
        page_by_path[entry["path"]] = page
    nav_groups[group_name] = built

# The full-screen welcome is the root/default route. It is registered for
# routing but deliberately absent from PAGE_GROUPS, so the hand-built sidebar
# below never lists it and in-session navigation can never return to it; deep
# links to dashboard pages resolve directly and never pass through it.
landing_page = st.Page("app_pages/landing.py", title="Welcome", default=True)

navigation = st.navigation({"Welcome": [landing_page], **nav_groups}, position="hidden")
on_landing = navigation is landing_page

if on_landing:
    # Welcome route: no sidebar content is rendered, and the landing sheet
    # hides the remaining chrome (sidebar space, collapse control, clearance).
    apply_landing_styles()
else:
    with st.sidebar:
        st.markdown(f'<div class="brand-title">{content["app"]["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="brand-sub">{content["app"]["tagline"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-rule"></div>', unsafe_allow_html=True)
        for group_name, entries in PAGE_GROUPS.items():
            st.markdown(f'<div class="nav-group">{group_name}</div>', unsafe_allow_html=True)
            for entry in entries:
                st.page_link(page_by_path[entry["path"]], label=entry["title"], icon=entry["icon"])
        # Return path to the main (welcome) page at the FOOT of the nav: the
        # landing is hidden from the groups above, so this quiet link is the one
        # in-session way back to it (a browser deep link to "/" also works).
        with st.container(key="sidebar_home"):
            st.page_link(landing_page, label="Main Page", icon=":material/home:")

    # The human-review boundary rides on the dashboard pages as a fixed footer
    # ribbon, rendered once here. It is intentionally omitted from the Business
    # Problem & Value narrative intro (stakeholder preference); every other page
    # keeps it, verbatim from configs/project.yml.
    if navigation is not page_by_path["app_pages/executive_overview.py"]:
        render_boundary_footer()

    # One-shot entrance on the first dashboard render after the landing CTA;
    # the flag is consumed, so widget reruns never replay it.
    if state.consume_dashboard_entry():
        apply_dashboard_entry_styles()

try:
    navigation.run()
except MissingOutputError as error:
    # A required pipeline output is absent: state it plainly, never substitute.
    st.error(str(error), icon=":material/folder_off:")
    st.stop()
