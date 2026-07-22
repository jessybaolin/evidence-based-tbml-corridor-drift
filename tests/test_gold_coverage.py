"""Gold Quantity Coverage: the metrics reproduce the verified notebook snapshot
(data-profiling/gold_nan_quantity_analysis.ipynb), the page tells the
three-question story, and missing quantity is never framed as a signal.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard.services import data_loader as load
from dashboard.services import gold_coverage as gc

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    frame = pd.read_parquet(
        REPO_ROOT / "data" / "processed" / "corridor_product_year_panel.parquet",
        columns=list(gc.PANEL_COLUMNS),
    )
    return gc.with_gap_flag(frame)


def _run_page() -> AppTest:
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page("app_pages/gold_quantity_coverage.py")
    return at.run()


def _text(at: AppTest) -> str:
    parts = [str(getattr(block, "value", "")) for block in at.markdown]
    parts += [str(getattr(block, "value", "")) for block in at.caption]
    return " ".join(parts)


# ---- Metrics reproduce the notebook's verified snapshot ----------------------

def test_gold_summary_matches_verified_snapshot(panel):
    s = gc.gold_summary(panel)
    assert s["gold_rows"] == 12205
    assert s["gap_rows"] == 1877
    assert s["gap_row_rate"] == pytest.approx(1877 / 12205)
    assert s["gap_value_usd"] == pytest.approx(1182907098, abs=1.0)
    assert s["gap_value_share"] == pytest.approx(0.000415, abs=5e-6)
    assert s["gap_model_eligible"] == 0, "no gap row may be model-eligible"
    largest = s["largest"]
    assert largest["year"] == 2024
    assert largest["route"] == "ARE → THA"
    assert largest["value_usd"] == pytest.approx(838370797, abs=1.0)
    assert largest["share_of_gap_value"] == pytest.approx(0.709, abs=1e-3)


def test_corridor_persistence_matches_verified_snapshot(panel):
    corridors = gc.corridor_coverage(panel)
    p = gc.persistence_summary(corridors)
    assert p["corridors"] == 3068
    assert p["affected"] == 1047
    assert p["four_plus"] == 104
    assert p["full_history"] == 702
    assert p["persistent"] == 14
    assert p["top15_overlap"] == 0
    assert p["persistent_value_usd"] == pytest.approx(1000119, abs=1.0)


def test_network_findings_match_verified_snapshot(panel):
    corridors = gc.corridor_coverage(panel)
    nodes, edges = gc.persistent_network(corridors)
    f = gc.network_findings(edges)
    assert f["persistent"] == 14
    assert f["nld_linked"] == 12
    assert f["nld_outbound"] == 9
    assert f["nld_inbound"] == 3
    assert f["reciprocal_partners"] == ["Greece", "Ireland", "Latvia"]
    assert sorted(f["other_routes"]) == [
        "Australia → Brazil", "Slovenia → North Macedonia",
    ]
    # Node positions are fixed layout: the hub is centred, others on a ring.
    hub = nodes.loc[nodes["connections"].idxmax()]
    assert hub["iso3"] == "NLD" and hub["x"] == 0.0 and hub["y"] == 0.0
    assert len(nodes) == 14


def test_gap_definition_and_export_lineage(panel):
    # The gap rule is exactly "valid value, unusable quantity", and the export
    # keeps the lineage identifiers a reviewer needs to trace any row.
    gold = panel[panel["family_id"].eq(gc.GOLD)]
    manual = (gold["value_valid_flag"].fillna(False)
              & ~gold["quantity_valid_flag"].fillna(False))
    assert int(manual.sum()) == 1877
    export = gc.followup_export(panel)
    assert len(export) == 1877
    assert {"obs_id", "source_row_id", "source_version"} <= set(export.columns)
    assert float(export["trade_value_usd"].iloc[0]) == pytest.approx(838370797, abs=1.0)
    # The official queue itself never contains a missing-quantity row.
    queue = load.load_review_queue()
    assert queue["quantity_metric_ton"].notna().all()


# ---- The page tells the three-question story ---------------------------------

def test_page_renders_three_question_story():
    at = _run_page()
    assert not at.exception
    text = _text(at)
    assert "Gold Trade Without Usable Quantity" in text
    for heading in ("How much cannot be assessed?",
                    "Large one-offs or repeated gaps?",
                    "Where do the repeated gaps occur?"):
        assert heading in text, heading
    # Derived headline figures appear (never typed in).
    assert "1,877" in text and "12,205" in text
    assert "15.38%" in text
    assert "$1.183B" in text and "0.0415%" in text
    # The one-off vs repeated split with its verified anchors.
    assert "70.9%" in text
    assert "United Arab Emirates → Thailand" in text
    assert "14" in text and "702" in text
    # Network finding strip + guardrail.
    assert "12 of 14 Netherlands-linked" in text
    assert "9 outbound" in text and "3 inbound" in text
    assert "Greece, Ireland, Latvia" in text
    assert "not reporter attribution" in text
    assert "not country risk" in text
    # The coverage-boundary framing in the single red banner.
    assert "not an anomaly signal" in text
    # The 'What happens next' comparison band was removed from the page.
    assert "Unit-value review pathway" not in text


def test_page_offers_network_views():
    at = _run_page()
    assert not at.exception
    # The network view filter exists with the all-routes default selected.
    seg = [c for c in at.segmented_control if c.key == "gc_network_view"]
    assert len(seg) == 1
    assert seg[0].value == "All persistent routes"
    # Switching a view re-renders without error (positions stay fixed by design).
    at2 = seg[0].set_value("Reciprocal routes").run()
    assert not at2.exception


def test_model_page_hands_over_to_coverage_page():
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page("app_pages/model_and_controls.py")
    at.run()
    assert not at.exception
    cta = load.load_content()["pages"]["model_and_controls"]["next_page"]["cta"]
    labels = [str(getattr(pl, "label", "")) for pl in at.get("page_link")]
    assert any(cta in label for label in labels), "coverage hand-off link missing"


def test_no_wrongdoing_language_in_page_copy():
    import json

    copy = load.load_content()["pages"]["gold_quantity_coverage"]
    lowered = json.dumps(copy).lower()
    for phrase in ("probability of crime", "suspicious", "laundering", "criminal",
                   "fraudulent", "proven", "wrongdoing"):
        assert phrase not in lowered, phrase
