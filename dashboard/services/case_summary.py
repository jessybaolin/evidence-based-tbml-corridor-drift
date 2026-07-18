"""
Case Summary analytics — pure functions behind the Selected Case Review page.

WHAT IT DOES:
    Prepares the corridor series and the three comparison-view frames (market
    comparison, own history, peer position) plus the runtime validation that
    guards the page. The analytical rules mirror notebook section 6.2 of
    data-profiling/business_Review_Data_profiling_revamped.ipynb exactly:

    - peer population = clean-panel rows with the same family_id and year whose
      unit-value / benchmark ratio is finite and > 0 (the selected case is IN
      the population);
    - percentile = inclusive at-or-below share, (ratio <= case_ratio).mean();
    - the histogram draws log10 ratios inside 0.01x..100x only, but every peer
      (including those outside the drawn window) stays in the percentile maths;
    - shifted_corridor_history_median is stored in NATURAL-LOG space and must
      be exponentiated before display; it uses prior years only, and missing
      years/medians are never filled, interpolated or defaulted to zero.

    No Streamlit, no file I/O — everything here is unit-testable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Columns the page loads from the clean panel for peer context + validation.
PEER_PANEL_COLUMNS = (
    "obs_id", "year", "exporter_iso3", "importer_iso3", "hs6", "family_id",
    "trade_value_usd", "quantity_metric_ton", "unit_value_usd_per_metric_ton",
    "benchmark_price_usd_per_metric_ton", "quality_status",
)

# Histogram display window (log10 of the benchmark multiple), as in the
# notebook: 0.01x .. 100x is drawn; everything outside stays in the maths.
HIST_LOG_LO = -2.0
HIST_LOG_HI = 2.0
HIST_BINS = 48

# The identity fields that must agree across queue / features / panel.
IDENTITY_FIELDS = ("year", "exporter_iso3", "importer_iso3", "hs6", "family_id")


def corridor_series(features: pd.DataFrame, exporter_iso3: str,
                    importer_iso3: str, hs6: str) -> pd.DataFrame:
    """All observed years for one exporter–importer–HS6 corridor, year-sorted.

    Straight from the features table (which carries the stored prior-year log
    median) — no interpolation and no synthetic rows.
    """
    rows = features[
        (features["exporter_iso3"] == exporter_iso3)
        & (features["importer_iso3"] == importer_iso3)
        & (features["hs6"].astype(str) == str(hs6))
    ]
    return rows.sort_values("year").reset_index(drop=True)


def _full_year_index(series: pd.DataFrame) -> pd.DataFrame:
    # One row per calendar year across the corridor's observed span. Years the
    # corridor did not trade/report stay as all-NaN rows so chart lines GAP —
    # they are never zero-filled or interpolated.
    years = series["year"].astype(int)
    span = list(range(int(years.min()), int(years.max()) + 1))
    frame = pd.DataFrame({"year": span})
    frame["observed"] = frame["year"].isin(set(years))
    return frame


def market_comparison_frame(series: pd.DataFrame, case_year: int) -> pd.DataFrame:
    """View 1: corridor implied unit value vs the World Bank benchmark."""
    base = pd.DataFrame({
        "year": series["year"].astype(int),
        "trade_value_usd": series["trade_value_usd"].astype(float),
        "quantity_metric_ton": series["quantity_metric_ton"].astype(float),
        "unit_value": series["unit_value_usd_per_metric_ton"].astype(float),
        "benchmark": series["benchmark_price_usd_per_metric_ton"].astype(float),
        "quality_status": series["quality_status"].astype(str),
    })
    ratio = base["unit_value"] / base["benchmark"]
    base["multiple"] = ratio.where(np.isfinite(ratio) & (ratio > 0))
    frame = _full_year_index(series).merge(base, on="year", how="left")
    frame["is_case_year"] = frame["year"].eq(int(case_year))
    return frame


def own_history_frame(series: pd.DataFrame, case_year: int) -> pd.DataFrame:
    """View 2: corridor implied unit value vs its own prior-year median.

    The stored shifted_corridor_history_median is a NATURAL-LOG value — it is
    exponentiated here, once, so no caller can ever plot the raw log number.
    prior_years_used counts the strictly-earlier observed years with a
    computable unit value (the values the median is actually built from).
    """
    uv = series["unit_value_usd_per_metric_ton"].astype(float)
    used: list[int] = []
    seen = 0
    for value in uv:  # series is year-sorted; count priors BEFORE this year
        used.append(seen)
        if np.isfinite(value) and value > 0:
            seen += 1
    log_median = series["shifted_corridor_history_median"].astype(float)
    prior_median = np.exp(log_median)
    base = pd.DataFrame({
        "year": series["year"].astype(int),
        "unit_value": uv,
        "prior_median": prior_median.where(np.isfinite(prior_median)),
        "prior_years_used": pd.Series(used, index=series.index, dtype=float),
        "quality_status": series["quality_status"].astype(str),
    })
    multiple = base["unit_value"] / base["prior_median"]
    base["multiple_vs_prior"] = multiple.where(np.isfinite(multiple) & (multiple > 0))
    frame = _full_year_index(series).merge(base, on="year", how="left")
    frame["is_case_year"] = frame["year"].eq(int(case_year))
    return frame


def peer_position(panel: pd.DataFrame, family_id: str, year: int,
                  obs_id: str) -> dict | None:
    """View 3: where the case sits among same-family, same-year peers.

    Population rule (notebook 6.2b): clean-panel rows of the same family and
    year whose unit-value/benchmark ratio is finite and strictly positive.
    The selected case is part of the population; returns None if it is not
    present exactly once (the page then shows an unavailable state).
    """
    population = panel[
        panel["family_id"].eq(family_id) & panel["year"].eq(int(year))
    ].copy()
    ratio = (
        population["unit_value_usd_per_metric_ton"]
        / population["benchmark_price_usd_per_metric_ton"]
    )
    population["multiple"] = ratio
    population = population[
        np.isfinite(population["multiple"]) & population["multiple"].gt(0)
    ]
    mine = population.loc[population["obs_id"].astype(str).eq(str(obs_id)), "multiple"]
    if len(mine) != 1:
        return None
    case_ratio = float(mine.iloc[0])

    ratios = population["multiple"].to_numpy(dtype=float)
    percentile = float((ratios <= case_ratio).mean())  # inclusive, case included

    log_ratio = np.log10(ratios)
    in_window = (log_ratio >= HIST_LOG_LO) & (log_ratio <= HIST_LOG_HI)
    counts, edges = np.histogram(
        log_ratio[in_window], bins=HIST_BINS, range=(HIST_LOG_LO, HIST_LOG_HI)
    )
    bins = pd.DataFrame({
        "log_left": edges[:-1],
        "log_right": edges[1:],
        "log_center": (edges[:-1] + edges[1:]) / 2.0,
        "ratio_low": np.power(10.0, edges[:-1]),
        "ratio_high": np.power(10.0, edges[1:]),
        "count": counts.astype(int),
    })
    return {
        "case_ratio": case_ratio,
        "case_log_ratio": float(np.log10(case_ratio)),
        "percentile": percentile,
        "peer_count": int(len(population)),
        "peers_strictly_below": int((ratios < case_ratio).sum()),
        "median_multiple": float(np.median(ratios)),
        "p95_multiple": float(np.percentile(ratios, 95)),
        "peers_at_or_above_3x": int((ratios >= 3.0).sum()),
        "bins": bins,
        "n_outside": int(len(population) - int(in_window.sum())),
        "max_count": int(counts.max()) if len(counts) else 0,
    }


# ---- Runtime validation ------------------------------------------------------

def _close(a, b, rel: float = 1e-6, absolute: float = 1e-9) -> bool:
    a_na, b_na = pd.isna(a), pd.isna(b)
    if a_na or b_na:
        return bool(a_na and b_na)
    return bool(np.isclose(float(a), float(b), rtol=rel, atol=absolute))


def validate_case_view(obs_id: str, queue: pd.DataFrame, features: pd.DataFrame,
                       panel: pd.DataFrame) -> list[str]:
    """Recompute every displayed identity/value; return the list of violations.

    An empty list means every check passed. The page must render a governed
    error state (and no numbers) if any violation fires.
    """
    violations: list[str] = []
    obs_id = str(obs_id)

    q_rows = queue.loc[queue["obs_id"].astype(str) == obs_id]
    if len(q_rows) != 1:
        return [
            f"observation appears {len(q_rows)} times in the review queue "
            "(expected exactly once)"
        ]
    q = q_rows.iloc[0]

    f_rows = features.loc[features["obs_id"].astype(str) == obs_id]
    p_rows = panel.loc[panel["obs_id"].astype(str) == obs_id]
    if len(f_rows) != 1:
        violations.append(
            f"observation appears {len(f_rows)} times in the features table "
            "(expected exactly once)"
        )
    if len(p_rows) != 1:
        violations.append(
            f"observation appears {len(p_rows)} times in the official clean panel "
            "(expected exactly once) — only official panel rows may be shown"
        )
    if violations:
        return violations
    f, p = f_rows.iloc[0], p_rows.iloc[0]

    # Identity agreement across the three artefacts.
    for field in IDENTITY_FIELDS:
        values = {str(q[field]), str(f[field]), str(p[field])}
        if len(values) > 1:
            violations.append(
                f"{field} disagrees across queue/features/panel: {sorted(values)}"
            )

    # Implied unit value = trade value / quantity, in every table storing it.
    for label, row in (("queue", q), ("features", f), ("panel", p)):
        quantity = row["quantity_metric_ton"]
        if pd.notna(quantity) and float(quantity) != 0.0:
            recomputed = float(row["trade_value_usd"]) / float(quantity)
            if not _close(row["unit_value_usd_per_metric_ton"], recomputed):
                violations.append(
                    f"implied unit value in the {label} row does not equal "
                    "trade value / quantity"
                )
    if not _close(q["unit_value_usd_per_metric_ton"], f["unit_value_usd_per_metric_ton"]):
        violations.append("implied unit value disagrees between queue and features")

    # Benchmark multiple = implied unit value / benchmark price.
    benchmark = q["benchmark_price_usd_per_metric_ton"]
    if pd.isna(benchmark) or float(benchmark) <= 0:
        violations.append("World Bank benchmark price is missing for the selected case")
        return violations
    case_multiple = float(q["unit_value_usd_per_metric_ton"]) / float(benchmark)
    if not np.isfinite(case_multiple) or case_multiple <= 0:
        violations.append("benchmark multiple is not computable for the selected case")

    # Corridor series and the market frame.
    series = corridor_series(features, q["exporter_iso3"], q["importer_iso3"], q["hs6"])
    if series.empty or int(q["year"]) not in set(series["year"].astype(int)):
        violations.append("the selected case year is missing from its own corridor series")
        return violations
    market = market_comparison_frame(series, int(q["year"]))
    observed = market[market["observed"]]
    computable = observed.dropna(subset=["unit_value", "benchmark", "multiple"])
    for _, row in computable.iterrows():
        if not _close(row["multiple"], row["unit_value"] / row["benchmark"]):
            violations.append(
                f"market-view multiple for {int(row['year'])} does not equal "
                "implied unit value / benchmark"
            )
    gap_rows = market[~market["observed"]]
    if not gap_rows[["trade_value_usd", "quantity_metric_ton", "unit_value",
                     "benchmark", "multiple"]].isna().all().all():
        violations.append("an unobserved year carries fabricated values in the market view")

    # Prior-year median: prior years only, log-space storage, exp display.
    own = own_history_frame(series, int(q["year"]))
    case_own = own.loc[own["year"] == int(q["year"])].iloc[0]
    stored_log = f["shifted_corridor_history_median"]
    prior = series.loc[
        series["year"].astype(int) < int(q["year"]), "unit_value_usd_per_metric_ton"
    ].astype(float)
    prior = prior[np.isfinite(prior) & (prior > 0)]
    if len(prior) == 0:
        if pd.notna(stored_log):
            violations.append(
                "a prior-year median is stored although no prior year has a "
                "computable unit value"
            )
        if pd.notna(case_own["prior_median"]):
            violations.append(
                "a prior baseline is displayed although none can be computed "
                "from prior years"
            )
    else:
        recomputed_log = float(np.median(np.log(prior)))
        if not _close(stored_log, recomputed_log, rel=1e-9):
            violations.append(
                "stored prior-year median does not match a recomputation from "
                "prior years only"
            )
        if not _close(case_own["prior_median"], float(np.exp(float(stored_log))), rel=1e-9):
            violations.append(
                "displayed prior-year median is not the exponentiated stored log median"
            )

    # Peer population, membership, percentile and histogram conservation.
    position = peer_position(panel, q["family_id"], int(q["year"]), obs_id)
    if position is None:
        violations.append(
            "the selected case does not appear exactly once in its peer population"
        )
        return violations
    family = panel[panel["family_id"].eq(q["family_id"]) & panel["year"].eq(int(q["year"]))]
    ratio = (
        family["unit_value_usd_per_metric_ton"]
        / family["benchmark_price_usd_per_metric_ton"]
    )
    ratio = ratio[np.isfinite(ratio) & (ratio > 0)]
    recomputed_pct = float((ratio <= position["case_ratio"]).mean())
    if not _close(position["percentile"], recomputed_pct, rel=0.0, absolute=1e-12):
        violations.append("peer percentile does not match an independent recomputation")
    if int(position["bins"]["count"].sum()) + position["n_outside"] != position["peer_count"]:
        violations.append(
            "histogram clipping would drop peers from the percentile calculation"
        )
    if not _close(position["case_ratio"], case_multiple):
        violations.append(
            "peer-view benchmark multiple disagrees with the case-facts multiple"
        )
    return violations
