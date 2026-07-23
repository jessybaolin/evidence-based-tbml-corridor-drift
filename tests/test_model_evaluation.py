"""Model Evaluation & Controls — the stakeholder revamp.

Confirms the plain-language translations are correct (share/lift derived from the
real comparison table), that model-selection criteria and blend evidence remain
auditable, that the narrative renders, and that technical machinery stays collapsed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

from dashboard.components.charts import (
    headline_bar, model_metric_bar, review_capacity_tradeoff, shap_importance_bar,
)
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"
PAGE_SOURCE = (REPO_ROOT / "dashboard" / "app_pages" / "model_and_controls.py").read_text(
    encoding="utf-8")


@pytest.fixture(scope="module")
def artefacts():
    return load.load_model_comparison(), load.load_model_selection()


@pytest.fixture(scope="module")
def model_scores(artefacts):
    _, selection = artefacts
    score_col = str(selection["selected_score_column"])
    return load.load_model_scores(columns=(
        "obs_id", "split", "synthetic_review_priority", "hard_negative", score_col,
    ))


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


def test_row_level_top50_evidence_reconciles_with_published_metrics(artefacts, model_scores):
    comparison, selection = artefacts
    evidence = metrics.ranking_evidence(model_scores, selection, split="test", k=50)
    published = comparison[
        comparison["split"].eq("test")
        & comparison["family_id"].eq("all")
        & comparison["model"].eq("hybrid")
    ].iloc[0]

    assert evidence["n"] == 6033 == int(published["n"])
    assert evidence["positives"] == 108 == int(published["positives"])
    assert evidence["found"] == 24
    assert evidence["precision"] == pytest.approx(0.48)
    assert evidence["precision"] == pytest.approx(float(published["precision_at_k"]))
    assert evidence["recall"] == pytest.approx(24 / 108)
    assert evidence["recall"] == pytest.approx(float(published["recall_at_k"]))
    assert evidence["random_expected"] == pytest.approx(50 * 108 / 6033)
    assert evidence["lift"] == pytest.approx(float(published["lift_at_k"]))
    assert evidence["hard_negative_total"] == 72
    assert evidence["hard_negative_top"] == 0


def test_review_capacity_curve_is_auditable(artefacts, model_scores):
    _, selection = artefacts
    curve = metrics.review_capacity_curve(model_scores, selection).set_index("capacity")
    expected = {
        10: (6, 60.0, 100 * 6 / 108),
        25: (14, 56.0, 100 * 14 / 108),
        50: (24, 48.0, 100 * 24 / 108),
        100: (40, 40.0, 100 * 40 / 108),
        200: (54, 27.0, 50.0),
    }
    for capacity, (found, precision, recall) in expected.items():
        assert int(curve.loc[capacity, "found"]) == found
        assert float(curve.loc[capacity, "precision_pct"]) == pytest.approx(precision)
        assert float(curve.loc[capacity, "recall_pct"]) == pytest.approx(recall)

    fig = review_capacity_tradeoff(
        curve.reset_index(), 50, "Precision", "Recall", "Rows reviewed", "Share (%)",
    )
    assert [trace.name for trace in fig.data] == ["Precision", "Recall"]
    assert fig.data[0].line.color == "#A62E4E"
    assert any(int(shape.x0) == 50 == int(shape.x1) for shape in fig.layout.shapes)
    assert fig.layout.yaxis.range == (0, 100)


def test_model_bar_charts_accept_the_page_red_emphasis():
    import pandas as pd

    red = load.load_theme()["chart"]["case_corridor"]
    frame = pd.DataFrame({"method": ["Selected", "Baseline"], "value": [48.0, 14.0]})
    fig = headline_bar(
        frame, "method", "value", "Selected", "Share (%)", emphasis_color=red,
    )
    colors = dict(zip(
        fig.data[0].y,
        fig.data[0].marker.color,
    ))
    assert colors["Selected"] == red
    assert colors["Baseline"] != red

    metric_view = pd.DataFrame({
        "model": ["Hybrid blend", "XGBoost"],
        "precision_pct": [0.48, 0.50],
    })
    metric_fig = model_metric_bar(
        metric_view, "precision_pct", "Precision", {"Hybrid blend"},
        emphasis_color=red,
    )
    metric_colors = dict(zip(metric_fig.data[0].y, metric_fig.data[0].marker.color))
    assert metric_colors["Hybrid blend"] == red
    assert metric_colors["XGBoost"] != red
    assert metric_fig.layout.xaxis.tickformat == ".0%"

    shap_fig = shap_importance_bar(pd.DataFrame({
        "feature_name": ["Feature A", "Feature B"],
        "mean_abs_shap": [0.5, 0.25],
    }), emphasis_color=red)
    assert shap_fig.data[0].marker.color == red

    assert "emphasis_color=model_emphasis" in PAGE_SOURCE
    styles = (REPO_ROOT / "dashboard" / "components" / "styles.py").read_text("utf-8")
    assert ".blend-challenger {{ background: {case_maroon}; }}" in styles


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
    # The queue-build flow anchors the page, followed by evaluation, method
    # selection and the interpretation controls.
    for heading in ("How the ranking queue is built",
                    "How the ranking is tested", "How well does it rank the test patterns?",
                    "Why this method was chosen", "What keeps it honest"):
        assert heading in text, heading
    assert "What makes the flagged cases different" not in text
    # Precision and recall are stated as distinct counts, with the random
    # expectation and lift translated into plain language.
    assert "24 of the 50 highest-ranked rows" in text
    assert "random 50-row review" in text
    assert "27x more concentrated than random selection" in text
    assert "24 of all 108 planted patterns" in text
    assert "not real-world detection rates" in text
    assert "What changes when review capacity changes?" in text
    assert "How these results are calculated" in text
    assert "48.0%" in text
    assert "22.2%" in text
    assert "26.8x" in text
    assert "None of the 72 planted benign look-alikes" not in text
    # The evaluation-copy visual explains planted patterns without carrying the
    # year-split controls, which belong beside the held-out performance results.
    assert "Planted unusual patterns" in text
    assert "Benign look-alikes" in text
    assert "planted rows never enter the official review queue" in text
    assert "How to read this test" not in text
    assert "Only the chosen method returns to score the real records" not in text
    assert "Time-based test design" in text
    assert "Fit the model" in text
    assert "Select the method" in text
    assert "Final test" in text
    assert "The final test years are used only for evaluation" in text
    assert "It learns on 2017–2020" not in text
    assert "The performance figures below show how well the selected method ranks" in text
    assert "held-out 2023–2024 public-data test copy" in text
    assert "Public trade data has no confirmed cases to learn from, so the method is measured" not in text
    # Why-this-method: the methods compared, the honest hybrid-vs-XGBoost trade,
    # the two score sources, and the blend formula with its validation evidence.
    assert "XGBoost" in text
    assert "documented weighted-sum score" in text
    assert "Start with fixed weights" in text
    assert any(
        "How the weighted-sum score and 75/25 blend are calculated" in str(e.label)
        for e in at.expander
    )
    assert "23 of 50 (46%)" in text
    assert "formula weight" in text
    assert "governance choice" in text
    assert "transparent fixed-rule score" not in text
    assert "documented points" not in text
    assert "The retained ranking formula" in text
    assert "The score sets review order" not in text
    assert "Market-explanation adjustment" in text
    assert "Data-reliability adjustment" in text
    assert "Both adjustments are penalties in the calculation" in text
    assert "0.08 × (6 − quality score) ÷ 6" in text
    assert "a weighted-signal subtotal of 0.70 becomes 0.55" in text
    assert "Each missing quality point subtracts about 0.013" in text
    assert "maximum additions total 1.18" in text
    weight = float(selection["selected_hybrid_challenger_weight"])
    assert f"{round(weight * 100)}%" in text          # challenger share, e.g. 75%
    assert f"{round((1 - weight) * 100)}%" in text     # rule share, e.g. 25%
    assert "which official gold records never reached that assessment" in text
    assert any("View Unscored Gold Records" in str(link.label)
               for link in at.get("page_link"))
    assert "Scores are review-priority signals, not probabilities" not in text
    assert "challenger model" not in text.lower()


def test_method_comparison_matches_table(artefacts):
    comparison, _ = artefacts
    mc = metrics.method_comparison(comparison, "test")
    test_all = comparison[(comparison["split"] == "test") & (comparison["family_id"] == "all")]
    assert len(mc) == len(test_all)
    for _, row in test_all.iterrows():
        got = mc[mc["model"] == row["model"]].iloc[0]
        assert got["precision_pct"] == pytest.approx(100 * float(row["precision_at_k"]))
    assert "XGBoost" in set(mc["method"])
    assert mc.loc[mc["model"] == "hybrid", "method"].iloc[0] == "Hybrid blend"


def test_model_selection_metrics_and_rule_weights_are_explicit():
    settings = yaml.safe_load((REPO_ROOT / "configs" / "thresholds.yml").read_text("utf-8"))
    selection = settings["model_selection"]
    assert "selected_metric" not in selection
    assert selection["challenger_metric"] == "average_precision"
    assert selection["hybrid_metric"] == "precision_at_k"

    rules = settings["rules"]
    expected_weights = {
        "history_weight": 0.20,
        "benchmark_residual_weight": 0.18,
        "benchmark_drift_weight": 0.18,
        "yoy_weight": 0.12,
        "divergence_weight": 0.12,
        "peer_weight": 0.10,
        "novelty_weight": 0.06,
        "reactivation_weight": 0.08,
        "valid_extreme_weight": 0.14,
    }
    for key, value in expected_weights.items():
        assert float(rules[key]) == pytest.approx(value)
    assert float(rules["benchmark_consistency_reference"]) == pytest.approx(0.35)

    pipeline = (REPO_ROOT / "src" / "06_train_evaluate_models.py").read_text("utf-8")
    for key in expected_weights:
        assert f'settings["{key}"]' in pipeline
    assert 'selection_settings["challenger_metric"]' in pipeline
    assert 'selection_settings["hybrid_metric"]' in pipeline


def test_configured_selection_metrics_reproduce_the_published_choice(artefacts):
    comparison, published = artefacts
    settings = yaml.safe_load(
        (REPO_ROOT / "configs" / "thresholds.yml").read_text("utf-8")
    )["model_selection"]

    validation = comparison[
        comparison["split"].eq("validation") & comparison["family_id"].eq("all")
    ]
    supervised = validation[validation["model"].isin(["logistic", "xgboost"])]
    challenger = supervised.sort_values(
        [settings["challenger_metric"], "hard_negative_false_positive_rate"],
        ascending=[False, True], kind="mergesort",
    ).iloc[0]
    assert challenger["model"] == published["selected_challenger"] == "xgboost"

    candidates = load.load_hybrid_candidates()
    selected = candidates.sort_values(
        [settings["hybrid_metric"], "hard_negative_false_positive_rate",
         "average_precision", "challenger_weight"],
        ascending=[False, True, False, True], kind="mergesort",
    ).iloc[0]
    assert float(selected["challenger_weight"]) == pytest.approx(
        float(published["selected_hybrid_challenger_weight"])
    )


def test_technical_machinery_lives_in_the_drawer():
    # The drawer exists, and the raw model builders / params are only used inside
    # the expander block — never in the main narrative above it.
    at = _run()
    assert any("Technical details" in str(e.label) for e in at.expander)
    drawer_start = PAGE_SOURCE.index("with st.expander(drawer[")
    for technical in ("shap_importance_bar(", "model_metric_bar("):
        assert PAGE_SOURCE.index(technical) > drawer_start, technical
    text = _text(at)
    for expected in (
        "Evaluation protocol and scope", "Scenario rows and scoring eligibility",
        "How to read the metrics", "Rows in test copy", "Eligible rows scored",
        "ROC-AUC is not reported", "Selected XGBoost settings",
    ):
        assert expected in text
    assert "6,658" in text
    assert "6,033" in text
    assert "625" in text
    assert "Transparent-baseline coefficients" not in text
    assert "transformed_feature" not in text
    assert "st.json(" not in PAGE_SOURCE
    assert "Source files and checksums" not in text
    assert "load_source_file_inventory" not in PAGE_SOURCE


def test_no_wrongdoing_language_in_page_copy():
    import json
    copy = load.load_content()["pages"]["model_and_controls"]
    lowered = json.dumps(copy).lower()
    for phrase in ("probability of crime", "suspicious", "laundering", "criminal",
                   "fraudulent", "proven", "wrongdoing"):
        assert phrase not in lowered, phrase
