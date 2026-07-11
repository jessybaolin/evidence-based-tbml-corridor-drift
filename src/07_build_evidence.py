"""
WHAT IT DOES:
  A score alone is not "evidence-first". For every top-ranked official observation this
  script extracts the handful of feature metrics that actually drove it (e.g. robust
  historical z, benchmark residual, year-over-year unit-value change), and records each as
  one structured, recomputable evidence row: the observed value, the comparison it was
  measured against, the threshold, a severity, a plain-English summary, and a caveat. These
  rows are what the analyst briefs (step 08) cite — so no claim is made without a fact behind it.

READS (inputs):
  - data/processed/corridor_features.parquet — the time-safe feature values
  - data/outputs/top_ranked_corridors.csv — the review queue (which observations to explain)

WRITES (outputs):
  - data/outputs/evidence_table.csv — one row per (observation, firing metric)
  - evidence_table.csv (repo root) — a convenience copy
  - data/outputs/top_ranked_corridors.csv — re-written with a key_evidence_count column added

"""

from __future__ import annotations

import hashlib
import pandas as pd

from tbml_common import DATA_OUTPUTS, DATA_PROCESSED, ROOT, ensure_dirs, fmt


# Specification for every metric that can become evidence. Each entry says how to describe
# the metric: its evidence_type, what it is compared against, the threshold that counts as
# notable, the direction (absolute / high / high_or_low), which raw fields support it, and a
# required caveat. This is config/reference data — the logic that uses it is in build_evidence().
METRIC_SPECS = {
    "robust_historical_z": {
        "evidence_type": "history_deviation",
        "comparison_field": "shifted_corridor_history_median",
        "comparison_group": "same exporter-importer-HS6 corridor, prior years only",
        "threshold": 4.0,
        "direction": "absolute",
        "source_fields": "log_unit_value;shifted_corridor_history_median;shifted_corridor_history_mad",
        "caveat": "Short or low-dispersion history can make this metric less stable.",
    },
    "benchmark_residual": {
        "evidence_type": "benchmark_gap",
        "comparison_field": "benchmark_price_usd_per_metric_ton",
        "comparison_group": "same-family World Bank annual commodity benchmark",
        "threshold": 0.70,
        "direction": "absolute",
        "source_fields": "unit_value_usd_per_metric_ton;benchmark_price_usd_per_metric_ton;benchmark_residual",
        "caveat": "The benchmark is broad market context, not invoice-level fair value.",
    },
    "benchmark_adjusted_drift": {
        "evidence_type": "benchmark_adjusted_drift",
        "comparison_field": "benchmark_residual",
        "comparison_group": "previous observed same-corridor benchmark residual",
        "threshold": 0.70,
        "direction": "absolute",
        "source_fields": "benchmark_residual;benchmark_adjusted_drift",
        "caveat": "Annual residual movement can reflect contract timing, quality, freight, insurance, or reporting differences.",
    },
    "unit_value_yoy_change": {
        "evidence_type": "annual_unit_value_change",
        "comparison_field": None,
        "comparison_group": "previous observed same-corridor-HS6 year",
        "threshold": 0.80,
        "direction": "absolute",
        "source_fields": "unit_value_usd_per_metric_ton;unit_value_yoy_change",
        "caveat": "Aggregate annual unit values are not invoice prices.",
    },
    "value_quantity_divergence": {
        "evidence_type": "value_quantity_divergence",
        "comparison_field": "quantity_yoy_change",
        "comparison_group": "same corridor-HS6 value growth versus quantity growth",
        "threshold": 0.80,
        "direction": "absolute",
        "source_fields": "trade_value_yoy_change;quantity_yoy_change;value_quantity_divergence",
        "caveat": "Value and quantity can diverge for benign commercial reasons.",
    },
    "same_family_year_peer_percentile": {
        "evidence_type": "peer_position",
        "comparison_field": None,
        "comparison_group": "same HS6/family and year peer corridors",
        "threshold": 0.95,
        "direction": "high_or_low",
        "source_fields": "benchmark_residual;same_family_year_peer_percentile",
        "caveat": "Peer comparison is at HS6 aggregate level and can hide product-quality differences.",
    },
    "corridor_novelty_flag": {
        "evidence_type": "corridor_activity",
        "comparison_field": "corridor_activity_history",
        "comparison_group": "prior active years for same corridor-HS6",
        "threshold": 1.0,
        "direction": "high",
        "source_fields": "corridor_activity_history;corridor_novelty_flag",
        "caveat": "New corridors can be entirely legitimate and require context.",
    },
    "corridor_reactivation_flag": {
        "evidence_type": "corridor_activity",
        "comparison_field": "corridor_activity_history",
        "comparison_group": "prior active years and gap pattern for same corridor-HS6",
        "threshold": 1.0,
        "direction": "high",
        "source_fields": "corridor_activity_history;corridor_reactivation_flag",
        "caveat": "Reactivation can be driven by commodity cycles, policy changes, or reporting changes.",
    },
}


def evidence_id(obs_id: str, metric_name: str, observed_value: float) -> str:
    # Deterministic, content-based ID: the same (observation, metric, value) always hashes to
    # the same "ev_..." id, so evidence rows are stable and reproducible across runs.
    payload = f"{obs_id}|{metric_name}|{observed_value:.12g}"
    return "ev_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:18]


def severity(magnitude: float, threshold: float) -> str:
    # Map "how far past the threshold" to a label. >=2x threshold = high, >=1x = medium, else low.
    if threshold <= 0:
        return "low"
    ratio = magnitude / threshold
    if ratio >= 2.0:
        return "high"
    if ratio >= 1.0:
        return "medium"
    return "low"


def metric_magnitude(metric_name: str, value: float) -> float:
    # Normalize a metric to a non-negative "strength". Most metrics use absolute value;
    # the peer percentile is special — strength = distance from the middle (0.5), scaled to 0..1,
    # so both very-high and very-low percentiles count as notable.
    if pd.isna(value):
        return 0.0
    if metric_name == "same_family_year_peer_percentile":
        return abs(float(value) - 0.5) * 2.0
    return abs(float(value))


def plain_summary(row: pd.Series, metric_name: str, observed: float, comparison: float | None, threshold: float, sev: str) -> str:
    # Produce a one-sentence, human-readable description of the evidence. Wording is fixed per
    # metric (no free-form generation) so summaries stay factual and recomputable.
    base = f"{row['year']} {row['exporter_iso3']} to {row['importer_iso3']} {row['hs6']} ({row['product_name']})"
    if metric_name == "benchmark_residual":
        return f"{base} has a log benchmark residual of {fmt(observed, 3)} against the World Bank annual benchmark. Severity: {sev}."
    if metric_name == "robust_historical_z":
        return f"{base} differs from its prior corridor history with robust historical z of {fmt(observed, 3)}. Severity: {sev}."
    if metric_name == "benchmark_adjusted_drift":
        return f"{base} moved by {fmt(observed, 3)} in benchmark-adjusted residual versus the previous observed corridor year. Severity: {sev}."
    if metric_name == "unit_value_yoy_change":
        return f"{base} has a year-over-year log unit-value change of {fmt(observed, 3)}. Severity: {sev}."
    if metric_name == "value_quantity_divergence":
        return f"{base} shows value-quantity divergence of {fmt(observed, 3)}. Severity: {sev}."
    if metric_name == "same_family_year_peer_percentile":
        return f"{base} sits at peer percentile {fmt(observed, 3)} within the same family and year. Severity: {sev}."
    if metric_name == "corridor_novelty_flag":
        return f"{base} appears as a new corridor-HS6 observation with no prior active year in the panel. Severity: {sev}."
    if metric_name == "corridor_reactivation_flag":
        return f"{base} appears after a prior gap in observed activity. Severity: {sev}."
    return f"{base} triggered {metric_name} = {fmt(observed, 3)}. Severity: {sev}."


def build_evidence() -> pd.DataFrame:
    ensure_dirs()

    # ---- Join features to the review queue ----
    # We only build evidence for the observations that made the top-ranked list.
    # Take only the top-ranked obs_ids, and attach their full feature values.
    features = pd.read_parquet(DATA_PROCESSED / "corridor_features.parquet")
    top = pd.read_csv(DATA_OUTPUTS / "top_ranked_corridors.csv")
    scores = top[["obs_id", "selected_review_priority_score", "rank"]]
    source = features.merge(scores, on="obs_id", how="inner", validate="one_to_one")
    source = source.sort_values(["rank", "obs_id"], kind="mergesort")

    # ---- For each observation, pick its strongest metrics and emit evidence rows ----
    rows: list[dict[str, object]] = []
    for _, obs in source.iterrows():
        # Score each available metric by how far it exceeds its threshold.
        candidates = []
        for metric_name, spec in METRIC_SPECS.items():
            if metric_name not in obs or pd.isna(obs[metric_name]):
                continue
            observed = float(obs[metric_name])
            threshold = float(spec["threshold"])
            magnitude = metric_magnitude(metric_name, observed)
            # Keep evidence compact: include indicators that cross threshold or are the strongest observed facts.
            candidates.append((magnitude / max(threshold, 1e-9), metric_name))
        # Keep only the top 4 strongest metrics for this observation (ties broken by name).
        selected = sorted(candidates, key=lambda item: (-item[0], item[1]))[:4]

        # Build one fully-described evidence row per selected metric.
        for _, metric_name in selected:
            spec = METRIC_SPECS[metric_name]
            observed = float(obs[metric_name])
            # Pull the comparison value (e.g. the historical median) when the spec names one.
            comparison_field = spec["comparison_field"]
            comparison = None
            if comparison_field and comparison_field in obs and pd.notna(obs[comparison_field]):
                comparison = float(obs[comparison_field])
            threshold = float(spec["threshold"])
            mag = metric_magnitude(metric_name, observed)
            sev = severity(mag, threshold)
            eid = evidence_id(str(obs["obs_id"]), metric_name, observed)
            rows.append({
                "evidence_id": eid,
                "obs_id": obs["obs_id"],
                "source_table": "data/processed/corridor_features.parquet",
                "source_row_id": obs.get("source_row_id", obs["obs_id"]),
                "evidence_type": spec["evidence_type"],
                "metric_name": metric_name,
                "observed_value": observed,
                "comparison_value": comparison,
                "comparison_group": spec["comparison_group"],
                "threshold": threshold,
                "direction": spec["direction"],
                "severity": sev,
                "source_fields": spec["source_fields"],
                "source_version": obs.get("source_version", "CEPII_BACI_HS17_V202601_filtered_official_derived"),
                "plain_english_summary": plain_summary(obs, metric_name, observed, comparison, threshold, sev),
                "caveat": spec["caveat"],
            })

    # ---- Persist evidence + back-fill an evidence count onto the review queue ----
    evidence = pd.DataFrame(rows)
    if evidence.empty:
        raise ValueError("No evidence rows were built for top-ranked official observations")
    evidence.to_csv(DATA_OUTPUTS / "evidence_table.csv", index=False)
    evidence.to_csv(ROOT / "evidence_table.csv", index=False)  # convenience copy at repo root

    # Count evidence rows per observation and write it back into top_ranked_corridors.csv so
    # the queue shows how much support each ranked row has.
    counts = evidence.groupby("obs_id").size().rename("key_evidence_count").reset_index()
    top_updated = top.drop(columns=["key_evidence_count"], errors="ignore").merge(counts, on="obs_id", how="left", validate="one_to_one")
    top_updated["key_evidence_count"] = top_updated["key_evidence_count"].fillna(0).astype(int)
    top_updated.to_csv(DATA_OUTPUTS / "top_ranked_corridors.csv", index=False)
    print(f"Wrote {len(evidence):,} evidence rows")
    return evidence


if __name__ == "__main__":
    build_evidence()
