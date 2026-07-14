"""Repository-root resolution, file discovery, and data contracts on real outputs."""

from __future__ import annotations

import pandas as pd

from dashboard.services import data_contracts as contracts
from dashboard.services import data_loader as load
from dashboard.services import path_resolver as paths


def test_repo_root_has_anchor_files():
    root = paths.repo_root()
    assert (root / "configs" / "project.yml").exists()
    assert (root / "src" / "tbml_common.py").exists()


def test_every_required_file_exists():
    missing = [
        name for name, spec in paths.DATA_FILES.items()
        if spec["required"] and not spec["path"].exists()
    ]
    assert missing == [], f"required outputs missing: {missing}"


def test_queue_contract(queue, panel):
    assert contracts.validate_queue(queue) == []
    assert contracts.check_queue_is_official(queue, panel) == []


def test_queue_hs6_stays_six_character_string(queue):
    assert queue["hs6"].map(lambda v: isinstance(v, str) and len(v) == 6).all()


def test_evidence_contract_and_joins(evidence, queue):
    assert contracts.validate_evidence(evidence, queue) == []
    # Every queue row's key_evidence_count matches the actual evidence rows.
    counts = evidence.groupby("obs_id").size()
    for _, row in queue.iterrows():
        assert int(row["key_evidence_count"]) == int(counts.get(row["obs_id"], 0))


def test_panel_and_features_contracts(panel, features):
    assert contracts.validate_panel(panel) == []
    assert contracts.validate_features(features) == []


def test_model_comparison_contract(comparison):
    assert contracts.validate_model_comparison(comparison) == []


def test_official_queue_never_carries_injected_values(queue, panel):
    # Even where an obs_id was also chosen for scenario injection (legitimate —
    # injections mutate a COPY), the queue must carry the clean panel's values.
    injections_path = paths.ROOT / "data" / "processed" / "scenario_injections.csv"
    if not injections_path.exists():
        return
    injections = pd.read_csv(injections_path)
    overlap = queue.merge(injections, on="obs_id", suffixes=("", "_inj"))
    clean = panel.set_index("obs_id")["trade_value_usd"]
    for _, row in overlap.iterrows():
        assert abs(row["trade_value_usd"] - clean[row["obs_id"]]) < 1e-9


def test_boundary_sentence_comes_from_project_config():
    boundary = load.conclusion_boundary()
    assert "does not establish money laundering" in boundary
    assert boundary == load.load_project_config()["conclusion_boundary"]


def test_feature_explanations_parse():
    explanations = load.load_feature_explanations()
    assert explanations is not None
    assert "feature_name" in explanations.columns
    assert "plain_english_interpretation" in explanations.columns
    assert len(explanations) >= 10
