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
    assert s["assessable_value_share"] == pytest.approx(0.9995851242)
    assert s["gap_model_eligible"] == 0, "no gap row may be model-eligible"
    largest = s["largest"]
    assert largest["year"] == 2024
    assert largest["route"] == "ARE → THA"
    assert largest["value_usd"] == pytest.approx(838370797, abs=1.0)
    assert largest["share_of_gap_value"] == pytest.approx(0.709, abs=1e-3)
    assert largest["share_of_gold_value"] == pytest.approx(0.0002940381)


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
    assert nodes["connections"].value_counts().sort_index().to_dict() == {
        1: 10, 2: 3, 12: 1,
    }
    assert int(edges["reciprocal"].sum()) == 6  # three pairs, two directions each
    assert edges["active_years"].eq(8).all()
    assert edges["gap_years"].eq(8).all()


def test_network_node_area_is_proportional(panel):
    from dashboard.components.charts import persistent_gap_network

    corridors = gc.corridor_coverage(panel)
    nodes, edges = gc.persistent_network(corridors)
    copy = load.load_content()["pages"]["gold_quantity_coverage"]["charts"]["network"]
    fig = persistent_gap_network(nodes, edges, "all", copy)
    node_trace = next(trace for trace in fig.data if trace.mode == "markers+text")

    sizes_by_count = {
        int(custom[1]): float(size)
        for custom, size in zip(node_trace.customdata, node_trace.marker.size)
    }
    base_area = sizes_by_count[1] ** 2
    assert sizes_by_count[2] ** 2 / base_area == pytest.approx(2.0)
    assert sizes_by_count[12] ** 2 / base_area == pytest.approx(12.0)


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
    assert "The Gold Records the Queue Cannot Assess" in text
    assert "Why inspect just 0.0415% of gold value?" in text
    assert "coverage blind spot" in text
    assert "does not indicate hidden risk or a missed case" in text
    for heading in ("Why the small value share still matters",
                    "Is the coverage gap isolated or repeated?",
                    "Where is the repeated gap concentrated?",
                    "What should stakeholders conclude?"):
        assert heading in text, heading
    # Derived headline figures appear (never typed in).
    assert "1,877" in text and "12,205" in text
    assert "15.38%" in text
    assert "$1.183B" in text and "0.0415%" in text
    assert "99.9585%" in text
    # The one-off vs repeated split with its verified anchors.
    assert "70.9%" in text
    assert "0.0294%" in text
    assert "0.000035%" in text
    assert "United Arab Emirates → Thailand" in text
    assert "14" in text and "702" in text
    # Network summary card + guardrail.
    assert "12 of the 14 routes touch the Netherlands" in text
    assert "9 go from the Netherlands" in text and "3 go to it" in text
    assert "Greece, Ireland and Latvia" in text
    assert "does not identify the reporting party" in text
    assert "measure country risk" in text
    # The coverage-boundary framing in the single red banner.
    assert "a coverage blind spot means unavailable scoring" in text
    assert "same exporter–importer route" in text
    # The main decision is fully explained by the two cards. These old
    # drill-downs duplicated the next network section and the headline record.
    assert not any(
        expander.label.startswith(("Concentration detail", "Persistence detail"))
        for expander in at.expander
    )
    assert [expander.label for expander in at.expander] == [
        "Route details behind the network"
    ]
    assert "Each row is one exporter–importer route drawn in the network" in text
    assert "reverse route also appears in the table" in text
    assert "sum of the eight annual trade values from 2017 to 2024" in text
    assert "years present in the panel = 8 AND years without usable quantity = 8" not in text
    assert "Circle area = routes touching country" in text
    assert "1 route · 10 countries" in text
    assert "2 routes · Greece, Ireland, Latvia" in text
    assert "12 routes · Netherlands" in text
    assert "Direction group" in text
    assert "Part of a two-way pair" in text
    assert "Strong value coverage, with one narrow data-quality follow-up" in text
    assert "Missing quantity should never be converted into an anomaly signal" in text
    page_link_labels = [str(getattr(link, "label", "")) for link in at.get("page_link")]
    assert "Continue to Bank Implementation Pathway" in page_link_labels
    # The 'What happens next' comparison band was removed from the page.
    assert "Unit-value review pathway" not in text


def test_page_offers_network_views():
    at = _run_page()
    assert not at.exception
    # The network view filter exists with the all-routes default selected.
    seg = [c for c in at.segmented_control if c.key == "gc_network_view"]
    assert len(seg) == 1
    assert seg[0].value == "All routes (14)"
    # Switching a view re-renders without error (positions stay fixed by design).
    at2 = seg[0].set_value("Two-way pairs (6 routes)").run()
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
