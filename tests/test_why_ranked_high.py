"""Validation for the Selected Case Review 'Why It Ranked High' tab.

The user's overriding requirement is correctness: no displayed ratio, percentile
or direction may be wrong. These tests recompute every card multiple, the peer
percentile scaling and the signal formatting independently from the published
artefacts, across ALL 50 queue cases, and assert the page's pure functions agree.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import why_ranked_high as wrh

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"

LOG_FIELDS = [
    "unit_value_yoy_change", "benchmark_residual", "benchmark_adjusted_drift",
    "trade_value_yoy_change", "quantity_yoy_change", "value_quantity_divergence",
]
CARD_FEATURE = {"A": "unit_value_yoy_change", "B": "benchmark_residual",
                "D": "benchmark_adjusted_drift"}  # C is the z-score, handled apart


@pytest.fixture(scope="module")
def artefacts():
    queue = load.load_review_queue().sort_values("rank")
    features = load.load_features()
    evidence = load.load_evidence()
    content = load.load_content()
    return queue, features, evidence, content


@pytest.fixture(scope="module")
def records(artefacts):
    queue, features, _, _ = artefacts
    return [metrics.case_record(o, queue, features) for o in queue["obs_id"]]


# ---- signal_number: the single log-space -> multiple conversion --------------

def test_log_fields_are_exponentiated_all_cases(records):
    for rec in records:
        for field in LOG_FIELDS:
            raw = rec.get(field)
            got = wrh.signal_number(field, raw)
            if raw is None or pd.isna(raw):
                assert got is None
            else:
                assert got == pytest.approx(float(np.exp(float(raw))), rel=1e-9)


def test_percentile_is_scaled_by_100(records):
    for rec in records:
        raw = rec.get("same_family_year_peer_percentile")
        got = wrh.signal_number("same_family_year_peer_percentile", raw)
        assert got == pytest.approx(float(raw) * 100.0, rel=1e-9)


def test_zscore_is_never_exponentiated(records):
    for rec in records:
        raw = float(rec["robust_historical_z"])
        assert wrh.signal_number("robust_historical_z", raw) == pytest.approx(raw)
        card_c = next(c for c in wrh.card_metrics(rec) if c["slot"] == "C")
        assert card_c["magnitude"] == pytest.approx(abs(raw))
        # exp(z) would be a wildly different (nonsense) number.
        if 1 < abs(raw) < 300:
            assert card_c["magnitude"] != pytest.approx(float(np.exp(raw)))


def test_count_and_flag_and_magnitude_kept_raw(records):
    for rec in records:
        for field in ("corridor_activity_history", "corridor_novelty_flag",
                      "corridor_reactivation_flag", "benchmark_consistency_gap"):
            raw = rec.get(field)
            if raw is not None and pd.notna(raw):
                assert wrh.signal_number(field, raw) == pytest.approx(float(raw))


# ---- Card metrics: multiples match the features across every case ------------

def test_card_multiples_match_features_all_cases(records):
    for rec in records:
        cards = {c["slot"]: c for c in wrh.card_metrics(rec)}
        for slot, field in CARD_FEATURE.items():
            raw = rec.get(field)
            card = cards[slot]
            if raw is None or pd.isna(raw):
                assert not card["available"]
            else:
                assert card["available"]
                assert card["magnitude"] == pytest.approx(
                    float(np.exp(float(raw))), rel=1e-9)


def test_top_case_reference_numbers(records):
    # Anchors the audited reference values for the rank-1 case.
    top = records[0]
    cards = {c["slot"]: c for c in wrh.card_metrics(top)}
    assert cards["A"]["magnitude"] == pytest.approx(6.416, abs=0.01)
    assert cards["B"]["magnitude"] == pytest.approx(6.363, abs=0.01)
    assert cards["D"]["magnitude"] == pytest.approx(6.413, abs=0.01)
    assert cards["C"]["magnitude"] == pytest.approx(18.83, abs=0.01)
    pct = wrh.signal_number("same_family_year_peer_percentile",
                            top["same_family_year_peer_percentile"])
    assert wrh.percentile_ordinal(pct) == "99.4th"


def test_all_four_cards_available_for_published_queue(records):
    # Every published queue case carries all four card features.
    for rec in records:
        for card in wrh.card_metrics(rec):
            assert card["available"], (rec["obs_id"], card["slot"])


def test_card_unavailable_only_on_missing_feature():
    rec = {"unit_value_yoy_change": float("nan"), "benchmark_residual": 1.0,
           "robust_historical_z": 3.0, "benchmark_adjusted_drift": 0.5}
    cards = {c["slot"]: c for c in wrh.card_metrics(rec)}
    assert not cards["A"]["available"]
    assert cards["A"]["magnitude"] is None
    assert cards["B"]["available"] and cards["C"]["available"] and cards["D"]["available"]


def test_direction_positive_and_negative_synthetic():
    up = {"unit_value_yoy_change": 1.8, "benchmark_residual": 1.8,
          "robust_historical_z": 5.0, "benchmark_adjusted_drift": 1.8}
    down = {"unit_value_yoy_change": -1.2, "benchmark_residual": -1.2,
            "robust_historical_z": -5.0, "benchmark_adjusted_drift": -1.2}
    cu = {c["slot"]: c for c in wrh.card_metrics(up)}
    cd = {c["slot"]: c for c in wrh.card_metrics(down)}
    assert (cu["A"]["direction"], cd["A"]["direction"]) == ("increase", "decrease")
    assert (cu["B"]["direction"], cd["B"]["direction"]) == ("above", "below")
    assert (cu["C"]["direction"], cd["C"]["direction"]) == ("above", "below")
    assert (cu["D"]["direction"], cd["D"]["direction"]) == ("increase", "decrease")
    # A downward log change is a multiple below 1 (a fall), never a fabricated 0.
    assert cd["A"]["magnitude"] == pytest.approx(float(np.exp(-1.2)))
    assert cd["A"]["magnitude"] < 1.0


def test_real_negative_direction_case(records):
    # quantity_yoy_change carries real negatives -> exp() < 1 (a genuine fall).
    neg = [r for r in records
           if pd.notna(r.get("quantity_yoy_change")) and float(r["quantity_yoy_change"]) < 0]
    assert neg, "expected a real negative quantity_yoy_change case in the queue"
    assert wrh.signal_number("quantity_yoy_change", neg[0]["quantity_yoy_change"]) < 1.0


# ---- Dynamic summary: grounded only in the case's evidence rows --------------

def test_summary_only_names_present_evidence_types(artefacts, records):
    _, _, evidence, _ = artefacts
    for rec in records:
        case_ev = metrics.case_evidence(evidence, rec["obs_id"])
        present = set(case_ev["evidence_type"].astype(str))
        for key in wrh.summary_clause_keys(rec, case_ev):
            etype = key.rsplit(".", 1)[0]
            assert etype in present, (rec["obs_id"], key)


def test_missing_evidence_type_is_not_claimed_but_card_still_shows(artefacts, records):
    # A case can lack a benchmark_gap evidence row while its residual is present:
    # the summary must not claim the benchmark reason, yet card B still shows the
    # real, recomputable multiple (never hidden).
    _, _, evidence, _ = artefacts
    checked = False
    for rec in records:
        case_ev = metrics.case_evidence(evidence, rec["obs_id"])
        if "benchmark_gap" in set(case_ev["evidence_type"].astype(str)):
            continue
        keys = wrh.summary_clause_keys(rec, case_ev)
        assert not any(k.startswith("benchmark_gap") for k in keys)
        card_b = next(c for c in wrh.card_metrics(rec) if c["slot"] == "B")
        assert card_b["available"]
        checked = True
    assert checked, "expected at least one benchmark_gap-missing case (17 exist)"


# ---- Signal profile + complete display-label mapping -------------------------

def test_signal_profile_fields_all_have_content(artefacts, records):
    _, _, _, content = artefacts
    labels = content["pages"]["case_investigation"]["why"]["signals"]
    for rec in records:
        for row in wrh.signal_profile(rec):
            assert row["field"] in labels, row["field"]


def test_signal_order_content_is_complete(artefacts):
    _, _, _, content = artefacts
    labels = content["pages"]["case_investigation"]["why"]["signals"]
    for field in wrh.SIGNAL_ORDER:
        assert field in labels
        for key in ("label", "tooltip", "interpretation", "derived", "time_safety"):
            assert labels[field].get(key), (field, key)


# ---- Page-level behaviour ----------------------------------------------------

def _run_case(**session_state) -> AppTest:
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page("app_pages/case_investigation.py")
    for key, value in session_state.items():
        at.session_state[key] = value
    return at.run()


def _text(at: AppTest) -> str:
    chunks = [str(getattr(b, "value", "")) for b in at.markdown]
    chunks += [str(getattr(b, "body", "")) for b in getattr(at, "caption", [])]
    return " ".join(chunks)


def test_case_page_has_three_tabs_no_evidence_tab(artefacts):
    _, _, _, content = artefacts
    tabs = content["pages"]["case_investigation"]["tabs"]
    assert tabs == ["Case Summary", "Why It Ranked High", "Caveats"]
    at = _run_case()
    assert not at.exception
    assert len(at.tabs) == 3


def test_why_tab_shows_summary_cards_and_removed_content():
    at = _run_case()
    text = _text(at)
    # Dynamic summary + the governed note that now rides inside the banner.
    assert "This observation ranked highly because" in text
    assert ("These are reasons to review this pattern more closely — "
            "not a finding of wrongdoing.") in text
    # Real per-case figures rendered (rank-1 audited values).
    assert "99.4th percentile" in text
    # Signals section still renders (assert on its description — expander labels
    # are not part of AppTest markdown/caption text). The raw-evidence Audit table
    # was removed as too technical for the stakeholder view.
    assert "The complete analytical profile supporting the selected observation" in text
    assert "raw evidence records behind the comparisons above" not in text
    # Removed: global SHAP context and the raw data-quality flag string.
    assert "Model-contribution context" not in text
    assert "quantity_missing=" not in text
    assert "Evidence as a table" not in text


def test_changing_case_refreshes_the_why_tab(artefacts):
    queue, _, _, _ = artefacts
    other = queue.sort_values("rank").iloc[7]["obs_id"]
    at = _run_case(tbml_selected_obs_id=other)
    assert not at.exception
    assert "This observation ranked highly" in _text(at)


def test_no_wrongdoing_language_in_why_tab():
    banned = ["probability of crime", "suspicious entity", "detected laundering",
              "confirmed tbml", "fraudulent trade", "proven overvaluation",
              "proof of mispricing"]
    lowered = _text(_run_case()).lower()
    for phrase in banned:
        assert phrase not in lowered, phrase
