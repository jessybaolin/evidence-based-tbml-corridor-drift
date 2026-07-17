"""
Evidence-First TBML Corridor Drift Lab — multipage Streamlit dashboard entry point.

WHAT IT DOES:
    Boots the app: puts the repository root on sys.path (so `dashboard.*`
    imports work no matter where the terminal was opened), applies the global
    theme, registers the pages with st.navigation, and renders the fixed
    human-review boundary ribbon that rides on every page.

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
from dashboard.components.styles import apply_global_styles
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
         "icon": ":material/account_balance:", "default": True},
        {"path": "app_pages/from_data_to_review_queue.py", "title": "From Data to Review Queue",
         "icon": ":material/account_tree:"},
        {"path": "app_pages/portfolio_analytics.py", "title": "Trade Landscape and Patterns",
         "icon": ":material/trending_up:"},
        {"path": "app_pages/review_queue.py", "title": "Top 50 Review Queue",
         "icon": ":material/checklist:"},
        {"path": "app_pages/case_investigation.py", "title": "Selected Case Review",
         "icon": ":material/search:"},
    ],
    "Trust & Methodology": [
        {"path": "app_pages/model_and_controls.py", "title": "Model Validation & Controls",
         "icon": ":material/verified_user:"},
        {"path": "app_pages/appendix.py", "title": "Appendix",
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

navigation = st.navigation(nav_groups, position="hidden")

with st.sidebar:
    st.markdown(f'<div class="brand-title">{content["app"]["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">{content["app"]["subtitle"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-rule"></div>', unsafe_allow_html=True)
    for group_name, entries in PAGE_GROUPS.items():
        st.markdown(f'<div class="nav-group">{group_name}</div>', unsafe_allow_html=True)
        for entry in entries:
            st.page_link(page_by_path[entry["path"]], label=entry["title"], icon=entry["icon"])

# The human-review boundary rides on EVERY page as a fixed footer ribbon,
# rendered once here so no page can drop it. Text comes verbatim from
# configs/project.yml via data_loader.conclusion_boundary().
render_boundary_footer()

try:
    navigation.run()
except MissingOutputError as error:
    # A required pipeline output is absent: state it plainly, never substitute.
    st.error(str(error), icon=":material/folder_off:")
    st.stop()
