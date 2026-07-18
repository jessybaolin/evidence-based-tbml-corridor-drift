"""Case Summary analytics are recomputed independently for every queue case.

Every check re-derives the expectation from the published artefacts (or from
hand-built synthetic frames), never from the functions under test, so a wrong
displayed number cannot be self-confirmed. Rules mirror notebook §6.2 of
data-profiling/business_Review_Data_profiling_revamped.ipynb.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dashboard.services import case_summary as cs

IDENTITY = ("year", "exporter_iso3", "importer_iso3", "hs6", "family_id")


def _series(features, q):
    return cs.corridor_series(
        features, q["exporter_iso3"], q["importer_iso3"], q["hs6"]
    )


def test_every_queue_case_passes_the_runtime_validation(queue, features, panel):
    # The same gate the page runs before showing any number.
    for obs_id in queue["obs_id"]:
        assert cs.validate_case_view(obs_id, queue, features, panel) == [], obs_id


def test_queue_cases_are_official_panel_rows_exactly_once(queue, panel):
    # No synthetic scenario row can enter the selector: every selectable obs_id
    # exists exactly once in the official clean panel.
    counts = panel["obs_id"].value_counts()
    for obs_id in queue["obs_id"]:
        assert counts.get(obs_id, 0) == 1, obs_id


def test_identity_and_arithmetic_recomputed_independently(queue, features, panel):
    f = features.set_index("obs_id")
    p = panel.set_index("obs_id")
    for _, q in queue.iterrows():
        fr, pr = f.loc[q["obs_id"]], p.loc[q["obs_id"]]
        for field in IDENTITY:
            assert str(q[field]) == str(fr[field]) == str(pr[field]), (q["obs_id"], field)
        # Implied unit value = trade value / quantity (tight tolerance).
        assert np.isclose(
            float(q["unit_value_usd_per_metric_ton"]),
            float(q["trade_value_usd"]) / float(q["quantity_metric_ton"]),
            rtol=1e-9,
        ), q["obs_id"]
        # Benchmark multiple = implied unit value / benchmark price.
        multiple = float(q["unit_value_usd_per_metric_ton"]) / float(
            q["benchmark_price_usd_per_metric_ton"]
        )
        assert np.isfinite(multiple) and multiple > 0, q["obs_id"]
        market = cs.market_comparison_frame(_series(features, q), int(q["year"]))
        row = market.loc[market["year"] == int(q["year"])].iloc[0]
        assert np.isclose(float(row["multiple"]), multiple, rtol=1e-9), q["obs_id"]


def test_prior_median_uses_prior_years_only_and_is_exponentiated(queue, features):
    for _, q in queue.iterrows():
        series = _series(features, q)
        own = cs.own_history_frame(series, int(q["year"]))
        for _, row in own[own["observed"]].iterrows():
            prior = series.loc[
                series["year"].astype(int) < int(row["year"]),
                "unit_value_usd_per_metric_ton",
            ].astype(float)
            prior = prior[np.isfinite(prior) & (prior > 0)]
            if len(prior) == 0:
                # No baseline -> unavailable, never zero or fabricated.
                assert pd.isna(row["prior_median"]), (q["obs_id"], row["year"])
                assert pd.isna(row["multiple_vs_prior"]), (q["obs_id"], row["year"])
            else:
                # Median of prior-year LOG unit values, exponentiated for
                # display — recomputed here from the raw series.
                expected = float(np.exp(np.median(np.log(prior))))
                assert np.isclose(float(row["prior_median"]), expected, rtol=1e-9), \
                    (q["obs_id"], row["year"])
                assert int(row["prior_years_used"]) == len(prior), \
                    (q["obs_id"], row["year"])
        # The displayed case-year median equals exp(stored log median).
        stored = features.loc[
            features["obs_id"] == q["obs_id"], "shifted_corridor_history_median"
        ].iloc[0]
        case_row = own.loc[own["year"] == int(q["year"])].iloc[0]
        if pd.isna(stored):
            assert pd.isna(case_row["prior_median"])
        else:
            assert np.isclose(
                float(case_row["prior_median"]), float(np.exp(float(stored))),
                rtol=1e-12,
            ), q["obs_id"]


def test_unobserved_years_stay_gaps_never_filled(queue, features):
    # Years absent from the official series are all-NaN rows (chart gaps);
    # nothing is interpolated, forward-filled or zeroed.
    for _, q in queue.iterrows():
        series = _series(features, q)
        market = cs.market_comparison_frame(series, int(q["year"]))
        own = cs.own_history_frame(series, int(q["year"]))
        market_gaps = market[~market["observed"]]
        own_gaps = own[~own["observed"]]
        assert market_gaps[
            ["trade_value_usd", "quantity_metric_ton", "unit_value",
             "benchmark", "multiple"]
        ].isna().all().all(), q["obs_id"]
        assert own_gaps[
            ["unit_value", "prior_median", "multiple_vs_prior"]
        ].isna().all().all(), q["obs_id"]


def test_peer_population_membership_and_percentile(queue, panel, features):
    for _, q in queue.iterrows():
        position = cs.peer_position(
            panel, q["family_id"], int(q["year"]), q["obs_id"]
        )
        assert position is not None, q["obs_id"]
        # Independent recomputation of the notebook §6.2b population rule:
        # same family, same year, finite and strictly positive ratio.
        fam = panel[
            panel["family_id"].eq(q["family_id"]) & panel["year"].eq(int(q["year"]))
        ].copy()
        ratio = (
            fam["unit_value_usd_per_metric_ton"]
            / fam["benchmark_price_usd_per_metric_ton"]
        )
        fam["ratio"] = ratio
        fam = fam[np.isfinite(fam["ratio"]) & fam["ratio"].gt(0)]
        assert position["peer_count"] == len(fam), q["obs_id"]
        # The selected case is IN its peer population exactly once.
        assert int(fam["obs_id"].astype(str).eq(str(q["obs_id"])).sum()) == 1, q["obs_id"]
        case_ratio = float(q["unit_value_usd_per_metric_ton"]) / float(
            q["benchmark_price_usd_per_metric_ton"]
        )
        assert np.isclose(position["case_ratio"], case_ratio, rtol=1e-9), q["obs_id"]
        # Inclusive at-or-below share over the FULL population (case included).
        expected_pct = float((fam["ratio"] <= position["case_ratio"]).mean())
        assert position["percentile"] == expected_pct, q["obs_id"]
        # Histogram clipping conserves the population: drawn + outside = all.
        assert int(position["bins"]["count"].sum()) + position["n_outside"] \
            == position["peer_count"], q["obs_id"]
        # Sanity crosscheck against the stored model feature: same population,
        # but the feature uses average-rank tie handling (rank pct of the log
        # ratio) while the notebook §6.2 display formula is the inclusive
        # at-or-below share — under ties they differ by at most half the tied
        # count over n. Assert closeness, not equality (display follows §6.2).
        stored_pct = features.loc[
            features["obs_id"] == q["obs_id"], "same_family_year_peer_percentile"
        ].iloc[0]
        assert abs(position["percentile"] - float(stored_pct)) < 0.01, q["obs_id"]


def test_extreme_ratios_stay_in_percentile_maths_when_clipped():
    # A peer with a ratio outside the drawn 0.01x–100x window is excluded from
    # the histogram bars but MUST stay in the percentile denominator.
    frame = pd.DataFrame({
        "obs_id": ["a", "b", "c", "extreme", "case"],
        "year": [2022] * 5,
        "family_id": ["fam"] * 5,
        "unit_value_usd_per_metric_ton": [50.0, 200.0, 90.0, 1e7, 500.0],
        "benchmark_price_usd_per_metric_ton": [100.0] * 5,
    })
    position = cs.peer_position(frame, "fam", 2022, "case")
    assert position is not None
    assert position["peer_count"] == 5
    assert position["n_outside"] == 1                      # the 1e5x ratio
    assert int(position["bins"]["count"].sum()) == 4       # drawn bars only
    # Percentile over ALL five ratios: case ratio 5.0 sits above 0.5/2/0.9,
    # below 1e5 -> 4/5 inclusive.
    assert position["percentile"] == 0.8
    assert position["peers_strictly_below"] == 3
    assert position["peers_at_or_above_3x"] == 2           # case + extreme


def test_no_prior_baseline_is_unavailable_not_zero():
    # A first-year corridor has no prior median: the frame must carry NaN
    # (rendered as the unavailable state), never zero or a fabricated level.
    series = pd.DataFrame({
        "year": [2022],
        "trade_value_usd": [1000.0],
        "quantity_metric_ton": [2.0],
        "unit_value_usd_per_metric_ton": [500.0],
        "benchmark_price_usd_per_metric_ton": [100.0],
        "shifted_corridor_history_median": [np.nan],
        "quality_status": ["fully_usable"],
    })
    own = cs.own_history_frame(series, 2022)
    row = own.iloc[0]
    assert pd.isna(row["prior_median"])
    assert pd.isna(row["multiple_vs_prior"])
    assert int(row["prior_years_used"]) == 0


def test_case_missing_from_peer_population_returns_none():
    # A case whose own ratio is not computable cannot claim a peer position.
    frame = pd.DataFrame({
        "obs_id": ["a", "case"],
        "year": [2022, 2022],
        "family_id": ["fam", "fam"],
        "unit_value_usd_per_metric_ton": [50.0, np.nan],
        "benchmark_price_usd_per_metric_ton": [100.0, 100.0],
    })
    assert cs.peer_position(frame, "fam", 2022, "case") is None


def test_validation_flags_a_tampered_unit_value(queue, features, panel):
    # The runtime gate must actually fire when a displayed identity breaks.
    tampered = queue.copy()
    target = tampered.index[0]
    tampered.loc[target, "unit_value_usd_per_metric_ton"] *= 1.5
    violations = cs.validate_case_view(
        tampered.loc[target, "obs_id"], tampered, features, panel
    )
    assert violations, "tampered unit value must be caught"


def test_validation_rejects_an_unknown_observation(queue, features, panel):
    violations = cs.validate_case_view("obs_does_not_exist", queue, features, panel)
    assert violations and "review queue" in violations[0]
