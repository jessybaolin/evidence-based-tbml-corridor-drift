"""Validation for the Trade Landscape and Patterns page.

The landscape half must reproduce the profiling notebook's stakeholder-relevant
Section 4 facts from the live panel: gold ~81% of value and benchmarks that moved
sharply. Numbers are recomputed here independently.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.components.charts import small_multiples_by_family
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

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
    assert scale["quantity_metric_ton"].notna().all()
    assert set(scale["family_label"]) == {"Gold", "Copper", "Palm oil"}


def test_trade_value_hover_uses_business_billions_not_si_giga(panel, short_labels):
    scale = metrics.trade_scale_by_family_year(panel, short_labels)
    fig = small_multiples_by_family(
        scale,
        "trade_value_usd",
        hover_label="Trade value (USD)",
        hover_values=scale["trade_value_usd"].map(fm.compact_usd),
    )
    display_values = [str(row[0]) for trace in fig.data for row in trace.customdata]
    assert "$16.0B" in display_values
    assert not any(value.endswith("G") for value in display_values)
    assert all("%{customdata[0]}" in trace.hovertemplate for trace in fig.data)


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
    # Skimmable objective + the two-part structure. The "The trade landscape"
    # divider was dropped — the page title (with its landmark icon) names that
    # half — so the landscape sections start straight away.
    assert "builds the context for the review queue" in text
    for heading in ("Scale: where the money is",
                    "Market context: prices can move across the whole market",
                    "Profile of the Top 50 Review Queue"):
        assert heading in text, heading
    assert "Structure: a steady base" not in text
    assert "Top-10 share of value" not in text
    # The value/quantity toggle exists.
    assert len(at.segmented_control) == 1


def test_scale_has_collapsed_table_twin_with_both_measures():
    at = _run()
    assert not at.exception
    assert any(expander.label == "View annual scale data" for expander in at.expander)
    assert len(at.dataframe) == 0
    markup = " ".join(str(block.value) for block in at.markdown)
    assert '<table class="data-table zebra">' in markup
    for heading in (
        "Year", "Product family", "Trade value (USD)", "Quantity (metric tons)"
    ):
        assert heading in markup
    assert "$458,401,226,764.00" in markup
    assert "7,641.714" in markup
    assert any(button.label == "Download scale data (.csv)"
               for button in at.get("download_button"))


def test_scale_toggle_switches_to_quantity():
    at = _run()
    at2 = at.segmented_control[0].set_value("Quantity").run()
    assert not at2.exception
    assert "By physical volume" in _text(at2)


def test_landscape_guardrails_present():
    text = _text(_run())
    for guardrail in (
        "heights are not comparable across panels",
        "It is not an invoice price",
        "rather than treating every price increase as unusual",
        "not the whole market",
    ):
        assert guardrail in text, guardrail


def test_no_wrongdoing_language_in_page_copy():
    # Scope to THIS page's copy — the global boundary ribbon legitimately negates
    # "money laundering / criminal intent" on every page and is tested elsewhere.
    import json

    copy = load.load_content()["pages"]["portfolio_analytics"]
    lowered = json.dumps(copy).lower()
    assert "flagged cases" not in lowered
    for phrase in ("probability of crime", "suspicious", "laundering", "criminal",
                   "fraudulent", "proven", "wrongdoing"):
        assert phrase not in lowered, phrase
