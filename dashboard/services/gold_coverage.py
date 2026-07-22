"""Gold quantity-coverage metrics — which official gold records sit outside
unit-value scoring, and whether the gaps are one-off or repeated.

Everything is derived live from the official panel (25,844 rows — the group-bys
are trivial), matching the analysis notebook data-profiling/
gold_nan_quantity_analysis.ipynb, which remains the verified specification.
Definitions:

  - Coverage gap: declared value is valid but quantity is NOT usable
    (value_valid_flag & ~quantity_valid_flag) — implied unit value, and so the
    rule/model scores, cannot be computed for the row.
  - Persistence is defined over the FULL panel history: a corridor active in
    all panel years whose every year lacks usable quantity. Filters must never
    redefine it.

Nothing here alters analytical values, and no function writes anything.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

GOLD = "gold_unwrought"

# Panel columns this module needs (pages pass them to load.load_panel).
PANEL_COLUMNS = (
    "obs_id", "source_row_id", "year", "exporter_iso3", "importer_iso3",
    "exporter_name", "importer_name", "corridor_id", "family_id",
    "trade_value_usd", "value_valid_flag", "quantity_valid_flag",
    "model_eligible", "source_version",
)


def with_gap_flag(panel: pd.DataFrame) -> pd.DataFrame:
    # A row is outside unit-value coverage when declared value is valid but
    # quantity is not usable — the same rule the pipeline applies before scoring.
    frame = panel.copy()
    frame["coverage_gap"] = (
        frame["value_valid_flag"].fillna(False).astype(bool)
        & ~frame["quantity_valid_flag"].fillna(False).astype(bool)
    )
    frame["route"] = (
        frame["exporter_iso3"].astype(str) + " → " + frame["importer_iso3"].astype(str)
    )
    return frame


def product_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    """Row-rate and value-share of the coverage gap per product family."""
    frame = panel if "coverage_gap" in panel.columns else with_gap_flag(panel)
    summary = frame.groupby("family_id", as_index=False).agg(
        rows=("obs_id", "size"),
        gap_rows=("coverage_gap", "sum"),
        total_value_usd=("trade_value_usd", "sum"),
    )
    gap_value = frame[frame["coverage_gap"]].groupby("family_id")["trade_value_usd"].sum()
    summary["gap_value_usd"] = summary["family_id"].map(gap_value).fillna(0.0)
    summary["gap_row_rate"] = summary["gap_rows"] / summary["rows"]
    summary["gap_value_share"] = summary["gap_value_usd"] / summary["total_value_usd"]
    return summary.sort_values("gap_row_rate", ascending=False).reset_index(drop=True)


def gold_summary(panel: pd.DataFrame) -> dict:
    """Headline gold coverage metrics plus the largest single gap observation."""
    frame = panel if "coverage_gap" in panel.columns else with_gap_flag(panel)
    gold = frame[frame["family_id"].eq(GOLD)]
    gap = gold[gold["coverage_gap"]]
    gold_value = float(gold["trade_value_usd"].sum())
    gap_value = float(gap["trade_value_usd"].sum())
    assessable = (
        gold["value_valid_flag"].fillna(False).astype(bool)
        & gold["quantity_valid_flag"].fillna(False).astype(bool)
    )
    assessable_value = float(gold.loc[assessable, "trade_value_usd"].sum())
    ordered = gap.sort_values(
        ["trade_value_usd", "obs_id"], ascending=[False, True], kind="mergesort"
    )
    largest = ordered.iloc[0]
    top10_share = float(ordered.head(10)["trade_value_usd"].sum() / gap_value)
    return {
        "gold_rows": int(len(gold)),
        "gap_rows": int(len(gap)),
        "gap_row_rate": float(len(gap) / len(gold)),
        "gap_value_usd": gap_value,
        "gap_value_share": gap_value / gold_value,
        "assessable_value_share": assessable_value / gold_value,
        "gap_model_eligible": int(gap["model_eligible"].sum()),
        "largest": {
            "obs_id": str(largest["obs_id"]),
            "year": int(largest["year"]),
            "route": str(largest["route"]),
            "exporter_name": str(largest["exporter_name"]),
            "importer_name": str(largest["importer_name"]),
            "value_usd": float(largest["trade_value_usd"]),
            "share_of_gap_value": float(largest["trade_value_usd"] / gap_value),
            "share_of_gold_value": float(largest["trade_value_usd"] / gold_value),
        },
        "top10_cumulative_share": top10_share,
        "years": sorted(int(y) for y in frame["year"].unique()),
    }


def corridor_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    """Gold corridors with their active years, gap years and gap value.

    `pattern` classifies each AFFECTED corridor for the persistence scatter:
    persistent (gap in every year of a full-history corridor) wins over the
    top-15-by-value group, mirroring the notebook.
    """
    frame = panel if "coverage_gap" in panel.columns else with_gap_flag(panel)
    gold = frame[frame["family_id"].eq(GOLD)]
    corridors = gold.groupby(
        ["corridor_id", "exporter_iso3", "importer_iso3",
         "exporter_name", "importer_name"], as_index=False,
    ).agg(
        active_years=("year", "nunique"),
        gap_years=("coverage_gap", "sum"),
        total_value_usd=("trade_value_usd", "sum"),
    )
    n_years = int(gold["year"].nunique())
    gap_value = (
        gold[gold["coverage_gap"]].groupby("corridor_id")["trade_value_usd"].sum()
    )
    corridors["gap_value_usd"] = corridors["corridor_id"].map(gap_value).fillna(0.0)
    corridors["gap_years"] = corridors["gap_years"].astype(int)
    corridors["full_history"] = corridors["active_years"].eq(n_years)
    corridors["persistent"] = corridors["full_history"] & corridors["gap_years"].eq(n_years)

    affected = corridors["gap_years"].gt(0)
    top15 = set(
        corridors[affected].nlargest(15, "gap_value_usd")["corridor_id"]
    )
    corridors["pattern"] = np.select(
        [corridors["persistent"], corridors["corridor_id"].isin(top15)],
        ["persistent", "top_value"],
        default="other",
    )
    corridors.loc[~affected, "pattern"] = "none"
    return corridors


def persistence_summary(corridors: pd.DataFrame) -> dict:
    affected = corridors[corridors["gap_years"].gt(0)]
    always = corridors[corridors["persistent"]]
    top15 = set(affected.nlargest(15, "gap_value_usd")["corridor_id"])
    return {
        "corridors": int(len(corridors)),
        "affected": int(len(affected)),
        "four_plus": int(affected["gap_years"].ge(4).sum()),
        "full_history": int(corridors["full_history"].sum()),
        "persistent": int(len(always)),
        "top15_overlap": int(len(top15 & set(always["corridor_id"]))),
        "persistent_value_usd": float(always["gap_value_usd"].sum()),
    }


def persistent_network(corridors: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Node and edge frames for the persistent-gap network.

    Nodes carry fixed radial positions (the highest-degree hub centred, others
    on a ring) so filtered views never move countries around. Positions are
    layout only — they carry no geographic or risk meaning.
    """
    edges = corridors[corridors["persistent"]].sort_values(
        ["exporter_iso3", "importer_iso3"], kind="mergesort"
    ).reset_index(drop=True).copy()

    directed = set(zip(edges["exporter_iso3"], edges["importer_iso3"]))
    edges["reciprocal"] = [
        (imp, exp) in directed
        for exp, imp in zip(edges["exporter_iso3"], edges["importer_iso3"])
    ]
    edges["category"] = np.select(
        [edges["exporter_iso3"].eq("NLD"), edges["importer_iso3"].eq("NLD")],
        ["nld_outbound", "nld_inbound"],
        default="other",
    )

    countries = sorted(set(edges["exporter_iso3"]) | set(edges["importer_iso3"]))
    names = {}
    for _, row in edges.iterrows():
        names[row["exporter_iso3"]] = row["exporter_name"]
        names[row["importer_iso3"]] = row["importer_name"]

    # The hub (most persistent connections) sits at the centre; the non-hub
    # routes' countries lead the ring so those edges stay visually separate.
    degree = pd.concat(
        [edges["exporter_iso3"], edges["importer_iso3"]]
    ).value_counts()
    hub = str(degree.index[0])
    other_first = [
        iso for pair in zip(edges["exporter_iso3"], edges["importer_iso3"])
        if hub not in pair for iso in pair
    ]
    ring = list(dict.fromkeys(other_first))
    ring += [c for c in countries if c != hub and c not in ring]
    angles = np.linspace(0.0, 2.0 * math.pi, len(ring), endpoint=False)
    positions = {hub: (0.0, 0.0)}
    positions.update({
        country: (math.cos(a), math.sin(a)) for country, a in zip(ring, angles)
    })

    nodes = pd.DataFrame({
        "iso3": countries,
        "country": [names[c] for c in countries],
        "outbound": [int((edges["exporter_iso3"] == c).sum()) for c in countries],
        "inbound": [int((edges["importer_iso3"] == c).sum()) for c in countries],
        "x": [positions[c][0] for c in countries],
        "y": [positions[c][1] for c in countries],
    })
    nodes["connections"] = nodes["outbound"] + nodes["inbound"]
    edges["x0"] = edges["exporter_iso3"].map(lambda c: positions[c][0])
    edges["y0"] = edges["exporter_iso3"].map(lambda c: positions[c][1])
    edges["x1"] = edges["importer_iso3"].map(lambda c: positions[c][0])
    edges["y1"] = edges["importer_iso3"].map(lambda c: positions[c][1])
    return nodes, edges


def network_findings(edges: pd.DataFrame) -> dict:
    nld = edges["category"].ne("other")
    reciprocal_partners = sorted(
        set(edges.loc[edges["reciprocal"] & edges["exporter_iso3"].eq("NLD"), "importer_name"])
        | set(edges.loc[edges["reciprocal"] & edges["importer_iso3"].eq("NLD"), "exporter_name"])
    )
    other_routes = [
        f'{row["exporter_name"]} → {row["importer_name"]}'
        for _, row in edges[~nld].iterrows()
    ]
    return {
        "persistent": int(len(edges)),
        "nld_linked": int(nld.sum()),
        "nld_outbound": int(edges["category"].eq("nld_outbound").sum()),
        "nld_inbound": int(edges["category"].eq("nld_inbound").sum()),
        "reciprocal_partners": reciprocal_partners,
        "other_routes": other_routes,
        "value_usd": float(edges["gap_value_usd"].sum()),
    }


def annual_trend(panel: pd.DataFrame) -> pd.DataFrame:
    frame = panel if "coverage_gap" in panel.columns else with_gap_flag(panel)
    gold = frame[frame["family_id"].eq(GOLD)]
    trend = gold.groupby("year", as_index=False).agg(
        rows=("obs_id", "size"),
        gap_rows=("coverage_gap", "sum"),
    )
    gap_value = gold[gold["coverage_gap"]].groupby("year")["trade_value_usd"].sum()
    trend["gap_value_usd"] = trend["year"].map(gap_value).fillna(0.0)
    trend["gap_row_rate"] = trend["gap_rows"] / trend["rows"]
    return trend


def concentration_table(panel: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Top gap observations by declared value with the cumulative share that
    backs the concentration statement (the Pareto detail)."""
    frame = panel if "coverage_gap" in panel.columns else with_gap_flag(panel)
    gap = frame[frame["family_id"].eq(GOLD) & frame["coverage_gap"]]
    ordered = gap.sort_values(
        ["trade_value_usd", "obs_id"], ascending=[False, True], kind="mergesort"
    ).copy()
    ordered["cumulative_share"] = (
        ordered["trade_value_usd"].cumsum() / ordered["trade_value_usd"].sum()
    )
    return ordered.head(top)[[
        "obs_id", "source_row_id", "year", "route",
        "trade_value_usd", "cumulative_share",
    ]].reset_index(drop=True)


def persistence_queue(corridors: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Corridors ranked for the repeated-gap follow-up (most gap years first)."""
    affected = corridors[corridors["gap_years"].gt(0)]
    return affected.sort_values(
        ["gap_years", "active_years", "gap_value_usd", "corridor_id"],
        ascending=[False, False, False, True], kind="mergesort",
    ).head(top)[[
        "corridor_id", "exporter_name", "importer_name",
        "active_years", "gap_years", "gap_value_usd",
    ]].reset_index(drop=True)


def followup_export(panel: pd.DataFrame) -> pd.DataFrame:
    """Every gold gap observation with its lineage, for the follow-up download."""
    frame = panel if "coverage_gap" in panel.columns else with_gap_flag(panel)
    gap = frame[frame["family_id"].eq(GOLD) & frame["coverage_gap"]]
    return gap.sort_values(
        ["trade_value_usd", "obs_id"], ascending=[False, True], kind="mergesort"
    )[[
        "obs_id", "source_row_id", "year", "exporter_iso3", "importer_iso3",
        "route", "trade_value_usd", "source_version",
    ]].reset_index(drop=True)
