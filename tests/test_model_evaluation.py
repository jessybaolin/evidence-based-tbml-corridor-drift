"""Model Evaluation & Controls — the stakeholder revamp.

Confirms the plain-language translations are correct (share/lift derived from the
real comparison table), that the driver separation is computed honestly, that the
narrative renders, and that the technical machinery stays in the collapsed drawer.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"
PAGE_SOURCE = (REPO_ROOT / "dashboard" / "app_pages" / "model_and_controls.py").read_text(
    encoding="utf-8")


@pytest.fixture(scope="module")
def artefacts():
    return load.load_model_comparison(), load.load_model_selection()


# ---- headline_eval: the plain "does it work?" numbers ------------------------

def test_headline_eval_matches_comparison_table(artefacts):
    comparison, selection = artefacts
    h = metrics.headline_eval(comparison, selection, split="test")
    assert h is not None
    test_all = comparison[(comparison["split"] == "test") & (comparison["family_id"] == "all")]
    hybrid = test_all[test_all["model"] == "hybrid"].iloc[0]
    rule = test_all[test_all["model"] == "rule"].iloc[0]
    # The share is precision@k as a percentage, straight from the table.
    assert h["selected_pct"] == pytest.approx(100 * float(hybrid["precision_at_k"]))
    assert h["rule_pct"] == pytest.approx(100 * float(rule["precision_at_k"]))
    # Random-review baseline = positives / n.
    assert h["random_pct"] == pytest.approx(100 * int(hybrid["positives"]) / int(hybrid["n"]))
    assert h["lift"] == pytest.approx(float(hybrid["lift_at_k"]))
    # The over-alerting guardrail: zero hard-negative false positives on test.
    assert h["hard_negative_fpr"] == 0.0
    # Selected method reads from the selection file, not hardcoded.
    assert h["selected_model"] == selection["selected_score_column"].replace("_score", "")


def test_headline_family_best_and_worst(artefacts):
    comparison, selection = artefacts
    h = metrics.headline_eval(comparison, selection, split="test")
    fam = comparison[(comparison["split"] == "test") & (comparison["model"] == "hybrid")
                     & (comparison["family_id"] != "all")]
    assert h["best_family_id"] == fam.loc[fam["average_precision"].idxmax(), "family_id"]
    assert h["worst_family_id"] == fam.loc[fam["average_precision"].idxmin(), "family_id"]
    # On the current data the method is strongest on gold, weakest on palm oil.
    assert h["best_family_id"] == "gold_unwrought"
    assert h["worst_family_id"] == "crude_palm_oil"


def test_selected_beats_rule_beats_random(artefacts):
    comparison, selection = artefacts
    h = metrics.headline_eval(comparison, selection, split="test")
    assert h["selected_pct"] > h["rule_pct"] > h["random_pct"]
    assert h["lift"] > 1.0


# ---- driver_separation: queue extreme on every lens -------------------------

def test_driver_separation_queue_is_extreme_on_all_lenses():
    features = load.load_features(columns=(
        "obs_id", "model_eligible", "robust_historical_z", "benchmark_residual",
        "same_family_year_peer_percentile", "unit_value_yoy_change",
    ))
    queue = load.load_review_queue()
    sep = metrics.driver_separation(features, set(queue["obs_id"]))
    assert len(sep) == 4
    for _, row in sep.iterrows():
        # Every lens: the queue's typical value sits well above a typical route.
        assert row["queue_pct"] > row["population_pct"], row["lens"]
        assert row["queue_pct"] >= 85.0, row["lens"]
        assert row["queue_median"] > row["rest_median"], row["lens"]


def test_driver_separation_medians_recomputed_independently():
    features = load.load_features(columns=(
        "obs_id", "model_eligible", "robust_historical_z", "benchmark_residual",
        "same_family_year_peer_percentile", "unit_value_yoy_change",
    ))
    queue = load.load_review_queue()
    ids = set(queue["obs_id"].astype(str))
    scored = features[features["model_eligible"].astype(bool)]
    sep = metrics.driver_separation(features, set(queue["obs_id"])).set_index("lens")
    for lens in ("robust_historical_z", "same_family_year_peer_percentile"):
        expected = scored[scored["obs_id"].astype(str).isin(ids)][lens].median()
        assert sep.loc[lens, "queue_median"] == pytest.approx(float(expected))


# ---- Page render + structure -------------------------------------------------

def _run() -> AppTest:
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page("app_pages/model_and_controls.py")
    return at.run()


def _text(at: AppTest) -> str:
    chunks = []
    for kind in ("markdown", "caption", "info", "success", "error", "warning"):
        for block in getattr(at, kind, []):
            chunks.append(str(getattr(block, "value", getattr(block, "body", ""))))
    return " ".join(chunks)


def test_page_renders_the_plain_narrative(artefacts):
    comparison, selection = artefacts
    h = metrics.headline_eval(comparison, selection, split="test")
    at = _run()
    assert not at.exception
    text = _text(at)
    for heading in ("How the ranking is tested", "Does it work?",
                    "Why this method was chosen", "What makes the flagged cases different",
                    "What keeps it honest"):
        assert heading in text, heading
    # The precision metric is translated to a plain share + lift in the takeaway.
    assert f"{round(h['selected_pct'])}%" in text
    assert f"{round(h['lift'])} times" in text
    # The pinned evaluation caveat is present.
    assert "not real-world detection rates" in text


def test_technical_machinery_lives_in_the_drawer():
    # The drawer exists, and the raw model builders / params are only used inside
    # the expander block — never in the main narrative above it.
    at = _run()
    assert any("Technical details" in str(e.label) for e in at.expander)
    drawer_start = PAGE_SOURCE.index("with st.expander(drawer[")
    for technical in ("shap_importance_bar(", "model_metric_bar(", "st.json("):
        assert PAGE_SOURCE.index(technical) > drawer_start, technical


def test_no_wrongdoing_language_in_page_copy():
    import json
    copy = load.load_content()["pages"]["model_and_controls"]
    lowered = json.dumps(copy).lower()
    for phrase in ("probability of crime", "suspicious", "laundering", "criminal",
                   "fraudulent", "proven", "wrongdoing"):
        assert phrase not in lowered, phrase
