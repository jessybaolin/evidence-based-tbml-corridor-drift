"""
Why-It-Ranked-High analytics — pure functions behind the Selected Case Review
"Why It Ranked High" tab. No Streamlit, no file I/O; everything here is unit
tested against the published artefacts.

Two independent layers, deliberately kept separate:

1. The dynamic ranking SUMMARY is grounded ONLY in the case's evidence rows
   (data/outputs/evidence_table.csv) — it names a comparison as a reason the
   observation ranked highly only when that evidence_type is actually one of the
   case's rows. summary_clause_keys() returns the ordered (type, direction)
   keys; the page maps them to approved copy.

2. The four comparison CARDS show the real, recomputable feature value for the
   selected case. A queue case always carries these features, so a card renders
   its number whenever the feature is finite and shows a data-absence message
   only when it is genuinely NaN (e.g. a corridor with no prior year). This
   never hides a real signal and never fabricates one.

Log-space discipline (verified against reports/feature_explanation_table.md and
the values themselves): unit_value_yoy_change, benchmark_residual,
benchmark_adjusted_drift, trade_value_yoy_change, quantity_yoy_change and
value_quantity_divergence are natural-log ratios/residuals — exp() gives the
multiple. robust_historical_z is a z-score (never exp'd). The peer percentile is
a 0-1 share (x100). Flags are binary; corridor_activity_history is a count;
benchmark_consistency_gap is a magnitude shown as-is.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---- Field taxonomy ----------------------------------------------------------
# Natural-log ratio/residual features: exp() -> a multiplicative comparison.
LOG_MULTIPLE_FIELDS = frozenset({
    "unit_value_yoy_change", "benchmark_residual", "benchmark_adjusted_drift",
    "trade_value_yoy_change", "quantity_yoy_change", "value_quantity_divergence",
})
PERCENTILE_FIELDS = frozenset({"same_family_year_peer_percentile"})  # 0-1 share
ZSCORE_FIELDS = frozenset({"robust_historical_z"})                   # never exp'd
FLAG_FIELDS = frozenset({"corridor_novelty_flag", "corridor_reactivation_flag"})
COUNT_FIELDS = frozenset({"corridor_activity_history"})
# Anything else (e.g. benchmark_consistency_gap) is shown as a plain magnitude.

# The signal profile order (spec section 7 — by analytical importance).
SIGNAL_ORDER: tuple[str, ...] = (
    "robust_historical_z",
    "benchmark_residual",
    "benchmark_adjusted_drift",
    "same_family_year_peer_percentile",
    "unit_value_yoy_change",
    "trade_value_yoy_change",
    "quantity_yoy_change",
    "value_quantity_divergence",
    "corridor_activity_history",
    "corridor_novelty_flag",
    "corridor_reactivation_flag",
    "benchmark_consistency_gap",
)


def signal_kind(field: str) -> str:
    if field in LOG_MULTIPLE_FIELDS:
        return "log_multiple"
    if field in PERCENTILE_FIELDS:
        return "percentile"
    if field in ZSCORE_FIELDS:
        return "zscore"
    if field in FLAG_FIELDS:
        return "flag"
    if field in COUNT_FIELDS:
        return "count"
    return "magnitude"


def percentile_ordinal(number: float) -> str:
    """A 0-100 percentile as an ordinal string, e.g. 99.36 -> '99.4th'.

    The suffix follows the last displayed digit (spec: 90.2 -> 'nd',
    99.4 -> 'th'); tenths never hit the 11/12/13 exception.
    """
    text = f"{float(number):.1f}"
    suffix = {"1": "st", "2": "nd", "3": "rd"}.get(text[-1], "th")
    return f"{text}{suffix}"


def signal_number(field: str, value) -> float | None:
    """The displayed numeric magnitude for a field, or None when missing.

    log_multiple -> exp(value) (the multiple); percentile -> value*100;
    everything else -> the value itself (z, count, flag, magnitude). This is the
    single place log space is turned into a multiple, so nothing else can plot or
    print a raw log value as a price/ratio.
    """
    if value is None or pd.isna(value):
        return None
    v = float(value)
    kind = signal_kind(field)
    if kind == "log_multiple":
        return float(np.exp(v))
    if kind == "percentile":
        return v * 100.0
    return v


# ---- The four comparison cards -----------------------------------------------
# slot -> the feature it converts, its evidence_type, and how direction reads.
CARD_SLOTS: tuple[dict, ...] = (
    {"slot": "A", "feature": "unit_value_yoy_change",
     "evidence_type": "annual_unit_value_change", "direction": "change"},
    {"slot": "B", "feature": "benchmark_residual",
     "evidence_type": "benchmark_gap", "direction": "level"},
    {"slot": "C", "feature": "robust_historical_z",
     "evidence_type": "history_deviation", "direction": "signed"},
    {"slot": "D", "feature": "benchmark_adjusted_drift",
     "evidence_type": "benchmark_adjusted_drift", "direction": "change"},
)


def _direction(mode: str, number: float) -> str:
    # number is the displayed magnitude (multiple for change/level, z for signed).
    if mode == "signed":
        return "above" if number >= 0 else "below"
    # change: >=1 rose, <1 fell; level: >=1 above benchmark, <1 below.
    if mode == "level":
        return "above" if number >= 1.0 else "below"
    return "increase" if number >= 1.0 else "decrease"


def card_metrics(record: dict) -> list[dict]:
    """One dict per card slot (A-D) with the numbers the page renders.

    available=True means the feature is finite for this case and the card shows
    its value; available=False means the feature is genuinely missing and the
    page shows that card's data-absence message. `magnitude` is the multiple for
    slots A/B/D and the (unsigned) z for slot C; `raw` is the stored feature
    value; `direction` is a copy key ('increase'/'decrease'/'above'/'below').
    """
    cards = []
    for spec in CARD_SLOTS:
        field = spec["feature"]
        raw = record.get(field)
        number = signal_number(field, raw)
        available = number is not None
        if not available:
            cards.append({**spec, "available": False, "raw": None,
                          "magnitude": None, "direction": None})
            continue
        direction = _direction(spec["direction"], number)
        magnitude = abs(number) if spec["direction"] == "signed" else number
        cards.append({**spec, "available": True, "raw": float(raw),
                      "magnitude": float(magnitude), "direction": direction})
    return cards


# ---- Dynamic ranking summary (evidence-row-driven) ---------------------------
# Summary clause order: strongest/most-intuitive reasons first.
SUMMARY_TYPE_ORDER: tuple[str, ...] = (
    "annual_unit_value_change", "benchmark_gap", "history_deviation",
    "benchmark_adjusted_drift", "value_quantity_divergence",
)
# For a present evidence_type, the feature whose sign sets the clause direction.
_SUMMARY_DIRECTION_FIELD = {
    "annual_unit_value_change": ("unit_value_yoy_change", "change"),
    "benchmark_gap": ("benchmark_residual", "level"),
    "history_deviation": ("robust_historical_z", "signed"),
    "benchmark_adjusted_drift": ("benchmark_adjusted_drift", "change"),
    "value_quantity_divergence": ("value_quantity_divergence", "change"),
}


def present_evidence_types(case_evidence: pd.DataFrame) -> set[str]:
    if case_evidence is None or case_evidence.empty:
        return set()
    return set(case_evidence["evidence_type"].astype(str))


def summary_clause_keys(record: dict, case_evidence: pd.DataFrame) -> list[str]:
    """Ordered '<evidence_type>.<direction>' keys for the case's flagged reasons.

    Only evidence types actually present among the case's rows appear, so the
    summary never claims a comparison the evidence does not support.
    """
    present = present_evidence_types(case_evidence)
    keys: list[str] = []
    for etype in SUMMARY_TYPE_ORDER:
        if etype not in present:
            continue
        field, mode = _SUMMARY_DIRECTION_FIELD[etype]
        number = signal_number(field, record.get(field))
        direction = _direction(mode, number) if number is not None else "change"
        keys.append(f"{etype}.{direction}")
    return keys


# ---- The full analytical signal profile --------------------------------------
def signal_profile(record: dict) -> list[dict]:
    """Ordered rows for the 'Signals for this observation' table.

    Each row: field (exact dataset name), kind, raw value, and number (the
    displayed magnitude from signal_number). The page joins the display label,
    tooltip, how-derived and time-safety copy by `field`; the case-result string
    is formatted from (kind, number, raw) so no raw log value is ever primary.
    Only fields actually present on the record are returned.
    """
    rows = []
    for field in SIGNAL_ORDER:
        if field not in record:
            continue
        raw = record.get(field)
        rows.append({
            "field": field,
            "kind": signal_kind(field),
            "raw": None if raw is None or pd.isna(raw) else float(raw),
            "number": signal_number(field, raw),
        })
    return rows
