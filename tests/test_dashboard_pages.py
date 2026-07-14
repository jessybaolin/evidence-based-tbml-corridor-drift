"""Render every dashboard page headlessly with Streamlit's AppTest.

Each page file runs as its own script (conftest puts the repo root on
sys.path, so `dashboard.*` imports resolve). A page passes when it renders
without an exception and shows the conclusion boundary.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "executive_overview.py",
    "review_queue.py",
    "case_investigation.py",
    "portfolio_analytics.py",
    "model_and_controls.py",
    "appendix.py",
]


def _run_page(page: str, **session_state) -> AppTest:
    at = AppTest.from_file(str(REPO_ROOT / "dashboard" / "pages" / page), default_timeout=120)
    for key, value in session_state.items():
        at.session_state[key] = value
    return at.run()


def _rendered_text(at: AppTest) -> str:
    chunks = [str(getattr(block, "value", "")) for block in at.markdown]
    chunks += [str(getattr(block, "body", "")) for block in getattr(at, "caption", [])]
    return " ".join(chunks)


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    at = _run_page(page)
    assert not at.exception, f"{page} raised: {at.exception}"


@pytest.mark.parametrize("page", PAGES)
def test_boundary_banner_visible(page):
    at = _run_page(page)
    assert "does not establish money laundering" in _rendered_text(at), page


def test_entry_point_renders_default_page():
    at = AppTest.from_file(str(REPO_ROOT / "dashboard" / "streamlit_app.py"), default_timeout=120)
    at.run()
    assert not at.exception


def test_review_queue_filters_and_empty_state():
    at = _run_page("review_queue.py")
    # Narrow the score slider to an impossible band -> transparent empty state.
    slider = next(s for s in at.slider if s.key == "queue_score_range")
    low = slider.value[0]
    at = slider.set_value((low, low)).run()
    assert not at.exception
    assert any("No review candidates match" in str(block.value) for block in at.info)


def test_case_investigation_selectbox_changes_case():
    # AppTest exposes FORMATTED labels via .options; select by index and check
    # the raw obs_id landed in session state.
    from dashboard.services.data_loader import load_review_queue

    queue = load_review_queue()
    expected = queue.sort_values("rank").iloc[4]["obs_id"]
    at = _run_page("case_investigation.py")
    selector = at.selectbox[0]
    assert len(selector.options) == len(queue)
    at = selector.select_index(4).run()
    assert not at.exception
    assert at.session_state["tbml_selected_obs_id"] == expected


def test_case_investigation_respects_queue_selection():
    from dashboard.services.data_loader import load_review_queue

    carried = load_review_queue().sort_values("rank").iloc[7]["obs_id"]
    at = _run_page("case_investigation.py", tbml_selected_obs_id=carried)
    assert not at.exception
    assert at.selectbox[0].value == carried


def test_model_controls_split_switch():
    at = _run_page("model_and_controls.py")
    split_box = at.selectbox[0]
    at = split_box.select("validation").run()
    assert not at.exception


def test_appendix_dictionary_search():
    at = _run_page("appendix.py")
    search = next(t for t in at.text_input if t.key == "dict_search")
    at = search.set_value("residual").run()
    assert not at.exception
