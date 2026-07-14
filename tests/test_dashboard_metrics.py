"""Dashboard KPI calculations and case lookups match the source outputs."""

from __future__ import annotations

from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load


def _enriched(queue, features, content):
    return metrics.enrich_queue(queue, features, content["family_short_labels"])


def test_overview_kpis_match_sources(panel, queue, evidence, comparison, content):
    # Expectations derive from the same artefacts the KPIs read, so a
    # legitimate pipeline rerun cannot break this test spuriously.
    manifest = load.load_source_manifest()
    kpis = metrics.overview_kpis(
        panel, queue, evidence, comparison, load.load_model_selection(), manifest,
    )
    assert kpis["observations"]["value"] == f"{len(panel):,}"
    assert kpis["queue"]["value"] == f"{len(queue):,}"
    assert kpis["evidence"]["value"] == f"{len(evidence):,}"
    assert kpis["model_eligible"]["value"] == f"{int(panel['model_eligible'].sum()):,}"
    assert kpis["models"]["value"] == str(comparison["model"].nunique())
    verified, total = metrics.source_verification_counts(manifest)
    expected = "Verified" if verified == total else f"{verified}/{total} checks"
    assert kpis["validation"]["value"] == (expected if total else "Not verified")


def test_selected_method_label_formatting():
    # Formatter behaviour tested with a synthetic selection (artefact-independent);
    # the live label just needs to exist.
    label = metrics.selected_method_label(
        {"selected_challenger": "xgboost", "selected_hybrid_challenger_weight": 0.75}
    )
    assert label == "Hybrid: 75% xgboost + 25% rules"
    assert metrics.selected_method_label(load.load_model_selection())


def test_enrich_queue_joins_names_and_residuals(queue, features, content):
    enriched = _enriched(queue, features, content)
    assert len(enriched) == len(queue)
    assert enriched["exporter_name"].notna().all()
    assert enriched["benchmark_residual"].notna().all()
    assert (enriched["corridor"].str.contains("→")).all()


def test_queue_filters_and_empty_result(queue, features, content):
    enriched = _enriched(queue, features, content)
    options = metrics.queue_filter_options(enriched)
    all_rows = metrics.apply_queue_filters(enriched, {})
    assert len(all_rows) == len(enriched)
    year = options["years"][0]
    by_year = metrics.apply_queue_filters(enriched, {"years": [year]})
    assert (by_year["year"] == year).all()
    none = metrics.apply_queue_filters(enriched, {"score_range": (0.0, 0.0)})
    assert none.empty  # empty-filter results must not error
    searched = metrics.apply_queue_filters(enriched, {"search": enriched["obs_id"].iloc[0]})
    assert len(searched) == 1


def test_case_record_history_and_evidence(queue, features, evidence, panel):
    obs_id = queue.iloc[0]["obs_id"]
    record = metrics.case_record(obs_id, queue, features)
    assert record is not None and record["obs_id"] == obs_id
    assert "robust_historical_z" in record  # feature join worked
    history = metrics.case_history(
        panel, record["exporter_iso3"], record["importer_iso3"], record["hs6"]
    )
    assert not history.empty
    assert int(record["year"]) in set(history["year"])
    case_rows = metrics.case_evidence(evidence, obs_id)
    assert len(case_rows) == int(record["key_evidence_count"])
    assert (case_rows["obs_id"] == obs_id).all()


def test_case_signals_use_approved_interpretations(queue, features):
    record = metrics.case_record(queue.iloc[0]["obs_id"], queue, features)
    signals = metrics.case_signals(record, load.load_feature_explanations())
    assert not signals.empty
    z_row = signals.loc[signals["signal"] == "robust_historical_z"].iloc[0]
    assert "historical pattern" in z_row["interpretation"]


def test_unknown_case_returns_none(queue, features):
    assert metrics.case_record("obs_does_not_exist", queue, features) is None


def test_comparison_view_test_split(comparison):
    view = metrics.comparison_view(comparison, "test", "all")
    assert set(view["model"]) == {"rule", "logistic", "xgboost", "isolation", "hybrid"}
    # The view is exactly the split/family slice of the artefact, sorted by AP.
    expected = comparison[(comparison["split"] == "test") & (comparison["family_id"] == "all")]
    assert view.set_index("model")["average_precision"].to_dict() == \
        expected.set_index("model")["average_precision"].to_dict()
    assert view["average_precision"].is_monotonic_decreasing
