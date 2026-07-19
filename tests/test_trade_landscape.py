"""Validation for the Trade Landscape and Patterns page.

The landscape half must reproduce the profiling notebook's Section 4 facts from
the live panel: gold ~81% of value, benchmarks that moved sharply, and a stable,
unevenly concentrated corridor base. Numbers are recomputed here independently.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"
PANEL_COLS = (
    "obs_id", "year", "family_id", "exporter_iso3", "importer_iso3", "hs6",
    "trade_value_usd", "quantity_metric_ton",
    "benchmark_price_usd_per_metric_ton", "benchmark_residual",
)


@pytest.fixture(scope="module")
def panel():
    return load.load_panel(columns=PANEL_COLS)


@pytest.fixture(scope="module")
def short_labels():
    return load.load_content()["family_short_labels"]


def test_landscape_summary_matches_section4(panel, short_labels):
    s = metrics.landscape_summary(panel, short_labels)
    assert s["dominant_family_id"] == "gold_unwrought"
    assert s["dominant_share"] == pytest.approx(81.0, abs=0.5)  # notebook ~81%
    assert s["n_families"] == 3
    assert (s["year_start"], s["year_end"], s["n_years"]) == (2017, 2024, 8)
    assert s["total_value"] == pytest.approx(3.5e12, rel=0.1)  # ~$3.5tn
    assert s["n_corridors"] > 0


def test_trade_scale_frame_is_complete_and_conserves_value(panel, short_labels):
    scale = metrics.trade_scale_by_family_year(panel, short_labels)
    assert len(scale) == 3 * 8  # family x year, no gaps
    assert scale["trade_value_usd"].sum() == pytest.approx(
        float(panel["trade_value_usd"].sum()), rel=1e-9)
    assert (scale["active_corridors"] > 0).all()
    assert set(scale["family_label"]) == {"Gold", "Copper", "Palm oil"}


def test_top10_concentration_palm_heavy_gold_long_tailed(panel, short_labels):
    top = metrics.top_corridor_share_by_family(panel, short_labels).set_index("family_label")
    # Notebook: palm ~60%, copper ~36%, gold ~27%.
    assert top.loc["Palm oil", "top_share_pct"] == pytest.approx(60.0, abs=3)
    assert top.loc["Gold", "top_share_pct"] == pytest.approx(27.0, abs=3)
    assert (top.loc["Palm oil", "top_share_pct"]
            > top.loc["Copper", "top_share_pct"]
            > top.loc["Gold", "top_share_pct"])
    assert top["top_share_pct"].between(0, 100).all()


def test_benchmarks_moved_sharply(panel, short_labels):
    bm = metrics.benchmark_by_family_year(panel, short_labels)
    gold = bm[bm["family_id"] == "gold_unwrought"].sort_values("year")["benchmark"]
    copper = bm[bm["family_id"] == "refined_copper_cathodes"].set_index("year")["benchmark"]
    palm = bm[bm["family_id"] == "crude_palm_oil"].set_index("year")["benchmark"]
    assert gold.iloc[-1] / gold.iloc[0] == pytest.approx(1.9, abs=0.15)   # nearly doubled
    assert copper[2021] / copper[2020] == pytest.approx(1.5, abs=0.1)     # +~50% in 2021
    assert palm.idxmax() == 2022                                          # peak into 2022


# ---- Page behaviour ----------------------------------------------------------

def _run() -> AppTest:
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page("app_pages/portfolio_analytics.py")
    return at.run()


def _text(at: AppTest) -> str:
    chunks = [str(getattr(b, "value", "")) for b in at.markdown]
    chunks += [str(getattr(b, "body", "")) for b in getattr(at, "caption", [])]
    return " ".join(chunks)


def test_page_shows_landscape_then_patterns_with_objective():
    at = _run()
    assert not at.exception
    text = _text(at)
    # Skimmable objective + the two-part structure.
    assert "Read this page before the queue" in text
    for heading in ("The trade landscape", "Scale: where the money is",
                    "Structure: a steady base", "Market context: prices moved on their own",
                    "How the flagged cases fall out"):
        assert heading in text, heading
    # The value/quantity toggle exists.
    assert len(at.segmented_control) == 1


def test_scale_toggle_switches_to_quantity():
    at = _run()
    at2 = at.segmented_control[0].set_value("Quantity").run()
    assert not at2.exception
    assert "By physical volume" in _text(at2)


def test_landscape_guardrails_present():
    text = _text(_run())
    for guardrail in (
        "heights are not comparable across panels",
        "not a control weakness",
        "It is not an invoice price",
        "not simply the largest",
    ):
        assert guardrail in text, guardrail


def test_no_wrongdoing_language_in_page_copy():
    # Scope to THIS page's copy — the global boundary ribbon legitimately negates
    # "money laundering / criminal intent" on every page and is tested elsewhere.
    import json

    copy = load.load_content()["pages"]["portfolio_analytics"]
    lowered = json.dumps(copy).lower()
    for phrase in ("probability of crime", "suspicious", "laundering", "criminal",
                   "fraudulent", "proven", "wrongdoing"):
        assert phrase not in lowered, phrase
