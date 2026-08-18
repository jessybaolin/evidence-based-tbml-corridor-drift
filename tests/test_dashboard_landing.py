"""Landing (welcome) screen contract: root/default route, shell suppression,
session-state completion flag, and CTA navigation into the dashboard shell.

The landing renders through the real entry point (streamlit_app.py +
st.navigation), exactly like the page tests: the root run must show the hero
without the sidebar or the boundary ribbon, and the CTA must hand over to
Business Problem and Value with the full shell restored.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"
CONTENT = REPO_ROOT / "dashboard" / "config" / "dashboard_content.yml"

CTA_LABEL = "Enter the dashboard"
# Session keys owned by dashboard/services/session_state.py; asserted as
# literals so an accidental rename fails loudly here.
LANDING_FLAG = "tbml_landing_complete"
ENTRY_PENDING = "tbml_dashboard_entry_pending"


def _run_root() -> AppTest:
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    return at.run()


def _run_page(page: str) -> AppTest:
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page(f"app_pages/{page}")
    return at.run()


def _text(at: AppTest) -> str:
    return " ".join(str(getattr(block, "value", "")) for block in at.markdown)


def _app_copy() -> dict:
    return yaml.safe_load(CONTENT.read_text(encoding="utf-8"))["app"]


def _boundary() -> str:
    config = yaml.safe_load(
        (REPO_ROOT / "configs" / "project.yml").read_text(encoding="utf-8")
    )
    return str(config["conclusion_boundary"])


def _state(at: AppTest, key: str, default=None):
    try:
        return at.session_state[key]
    except KeyError:
        return default


def test_landing_is_the_default_page_with_title_and_cta():
    at = _run_root()
    assert not at.exception
    text = _text(at)
    # Hero title = the configured landing.title_lines rendered as three lines
    # (acronym spelled out in full), + the product description verbatim from
    # the existing app block of dashboard_content.yml.
    landing = yaml.safe_load(CONTENT.read_text(encoding="utf-8"))["landing"]
    for line in landing["title_lines"]:
        assert line in text
    assert "Trade-Based Money Laundering (TBML)" in text
    assert _app_copy()["subtitle"] in text
    assert any(button.label == landing["cta"] for button in at.button)
    # A root visit initialises the flag without completing it.
    assert _state(at, LANDING_FLAG) is False


def test_landing_renders_without_sidebar_or_ribbon():
    at = _run_root()
    assert not at.exception
    assert len(at.sidebar.markdown) == 0, "landing must not render the sidebar"
    assert _boundary() not in _text(at), "landing must not render the ribbon"


def test_cta_completes_landing_and_enters_business_page():
    at = _run_root()
    cta = next(button for button in at.button if button.label == CTA_LABEL)
    cta.click()
    at.run()
    assert not at.exception
    assert _state(at, LANDING_FLAG) is True
    # st.switch_page landed on Business Problem and Value with the sidebar shell
    # restored (that page carries the boundary footer like every dashboard page),
    # and the one-shot entry flag was consumed.
    assert "Evidence-First Trade Pattern Triage" in _text(at)
    assert len(at.sidebar.markdown) > 0
    assert _state(at, ENTRY_PENDING, default="consumed") == "consumed"


def test_dashboard_pages_keep_shell_and_single_ribbon():
    at = _run_page("review_queue.py")
    assert not at.exception
    assert len(at.sidebar.markdown) > 0
    assert _text(at).count(_boundary()) == 1
    assert all(button.label != CTA_LABEL for button in at.button)


def test_dashboard_sidebar_offers_a_return_to_main_page():
    # The landing is hidden from the nav groups. Its accessible page-link label
    # remains available, while CSS presents it as the first, icon-only home
    # control in the brand area rather than as a footer navigation row.
    at = _run_page("review_queue.py")
    assert not at.exception
    labels = [str(getattr(link, "label", "")) for link in at.sidebar.get("page_link")]
    assert "Main Page" in labels, "sidebar return-to-main-page link missing"
    assert labels[0] == "Main Page", "home control should precede content navigation"

    styles = (REPO_ROOT / "dashboard" / "components" / "styles.py").read_text("utf-8")
    assert ".st-key-sidebar_home" in styles
    assert "align-items: center !important" in styles
    assert "clip: rect(0, 0, 0, 0)" in styles


def test_dashboard_sidebar_links_directly_to_project_walkthrough():
    at = _run_page("executive_overview.py")
    assert not at.exception
    sidebar_html = "\n".join(str(block.value) for block in at.sidebar.markdown)
    assert "Review Priority Triage System" in sidebar_html
    assert "Review-priority analytics" not in sidebar_html
    assert "Project walkthrough" in sidebar_html
    assert "https://www.youtube.com/watch?v=s-p0yXFv6fQ" in sidebar_html
    assert 'target="_blank"' in sidebar_html
    assert 'rel="noopener noreferrer"' in sidebar_html
    assert "sidebar-walkthrough-icon" in sidebar_html


def test_direct_deep_navigation_bypasses_the_landing():
    # AppTest.switch_page mirrors a deep link: the landing never executes, so
    # its session flag is never initialised and no CTA appears. Use a page that
    # keeps the boundary footer to confirm the full shell renders.
    at = _run_page("review_queue.py")
    assert not at.exception
    assert _boundary() in _text(at)
    assert _state(at, LANDING_FLAG, default="untouched") == "untouched"


def test_page_directory_contract_still_holds():
    assert (REPO_ROOT / "dashboard" / "app_pages" / "landing.py").is_file()
    assert not (REPO_ROOT / "dashboard" / "pages").exists()
