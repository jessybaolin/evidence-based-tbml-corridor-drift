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
    assert options["published"] == len(enriched)
    assert options["exporter_labels"]["ESP"] == "Spain (ESP)"
    assert options["importer_labels"]["NPL"] == "Nepal (NPL)"
    all_rows = metrics.apply_queue_filters(enriched, {})
    assert len(all_rows) == len(enriched)
    year = options["years"][0]
    by_year = metrics.apply_queue_filters(enriched, {"years": [year]})
    assert (by_year["year"] == year).all()
    none = metrics.apply_queue_filters(enriched, {"score_range": (0.0, 0.0)})
    assert none.empty  # empty-filter results must not error
    top = metrics.apply_queue_filters(enriched, {"top_n": 10})
    assert list(top["rank"]) == sorted(enriched["rank"])[:10]
    # top_n larger than the published queue is inert, never an error.
    capped = metrics.apply_queue_filters(enriched, {"top_n": 500})
    assert len(capped) == len(enriched)


def test_queue_display_frame_columns_corridor_and_rank_stability(queue, features, content):
    enriched = _enriched(queue, features, content)
    display = metrics.queue_display_frame(enriched)
    assert list(display.columns) == metrics.QUEUE_DISPLAY_COLUMNS
    assert len(display) == len(enriched)
    # Three-character source codes with the arrow separator. Alongside ISO3
    # the official data uses special partner codes (e.g. S19 = Other Asia,
    # nes), which the queue must show as published, never hide or rewrite.
    assert display["corridor"].str.fullmatch(r"[A-Z0-9]{3} → [A-Z0-9]{3}").all()
    # Values pass through untouched — formatting happens in column_config only.
    assert (display["trade_value_usd"].to_numpy()
            == enriched.reset_index(drop=True)["trade_value_usd"].to_numpy()).all()
    # Ranks travel with their rows: re-sorting the view cannot reassign them.
    resorted = display.sort_values("quantity_metric_ton", ascending=False)
    assert set(zip(resorted["rank"], resorted["corridor"])) \
        == set(zip(display["rank"], display["corridor"]))


def test_queue_display_frame_product_is_clean_family_label(queue, features, content):
    # The product column carries the plain family label — no caveat glyph.
    enriched = _enriched(queue, features, content)
    display = metrics.queue_display_frame(enriched)
    frame = enriched.reset_index(drop=True)
    assert display["product"].tolist() == frame["family_label"].tolist()
    assert not display["product"].str.startswith("⚠").any()


def test_queue_export_frame_traceability_and_rank_order(queue, features, content):
    enriched = _enriched(queue, features, content)
    shuffled = enriched.sample(frac=1, random_state=7)
    export = metrics.queue_export_frame(shuffled)
    assert list(export.columns) == metrics.QUEUE_EXPORT_COLUMNS
    assert export["rank"].is_monotonic_increasing  # export is always rank order
    assert not export["product"].str.startswith("⚠").any()
    assert export["quality_status"].notna().all()
    # Full precision: exported values equal the published artefact exactly.
    merged = export.merge(queue[["obs_id", "trade_value_usd"]], on="obs_id", suffixes=("", "_src"))
    assert len(merged) == len(export)
    assert (merged["trade_value_usd"] == merged["trade_value_usd_src"]).all()


def test_default_case_and_family_hs6_map(queue, features, content):
    enriched = _enriched(queue, features, content)
    assert int(metrics.default_case(enriched)["rank"]) == int(enriched["rank"].min())
    mapping = metrics.family_hs6_map(enriched)
    assert set(mapping) == set(enriched["family_label"].unique())
    assert all(len(code) == 6 for code in mapping.values())


def test_case_record_and_evidence(queue, features, evidence):
    # Corridor time-series logic lives in services/case_summary.py now
    # (tests/test_case_summary.py); this covers the record join + evidence sort.
    obs_id = queue.iloc[0]["obs_id"]
    record = metrics.case_record(obs_id, queue, features)
    assert record is not None and record["obs_id"] == obs_id
    assert "robust_historical_z" in record  # feature join worked
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
