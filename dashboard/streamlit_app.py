"""
Evidence-First TBML Corridor Drift Lab — multipage Streamlit dashboard entry point.

WHAT IT DOES:
    Boots the app: puts the repository root on sys.path (so `dashboard.*`
    imports work no matter where the terminal was opened), applies the global
    theme, and registers the six pages with st.navigation.

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

# Material Symbol icons (icon=":material/<name>:") render as monochrome glyphs
# in the theme colour — frost on the navy sidebar — matching the blue palette.
pages = {
    "Business & Review": [
        st.Page("pages/executive_overview.py", title="Business Problem & Value", icon=":material/account_balance:", default=True),
        st.Page("pages/review_queue.py", title="Official Review Queue", icon=":material/checklist:"),
        st.Page("pages/case_investigation.py", title="Selected Case Review", icon=":material/search:"),
        st.Page("pages/portfolio_analytics.py", title="Queue Patterns", icon=":material/trending_up:"),
    ],
    "Trust & Methodology": [
        st.Page("pages/from_data_to_review_queue.py", title="From Data to Review Queue", icon=":material/account_tree:"),
        st.Page("pages/model_and_controls.py", title="Model Validation & Controls", icon=":material/verified_user:"),
        st.Page("pages/appendix.py", title="Appendix", icon=":material/menu_book:"),
    ],
}

with st.sidebar:
    st.markdown(f"## {content['app']['title']}")
    st.caption(content["app"]["subtitle"])
    st.markdown("---")

navigation = st.navigation(pages, expanded=True)

try:
    navigation.run()
except MissingOutputError as error:
    # A required pipeline output is absent: state it plainly, never substitute.
    st.error(str(error), icon="🗂️")
    st.stop()
