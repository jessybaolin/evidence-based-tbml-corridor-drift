"""
Presentation formatting only — analytical values are never altered on load.

WHAT IT DOES:
    NA-safe number/label formatters shared by every page, matching the
    conventions of src/tbml_common.py (fmt/money) so dashboard figures read the
    same as the evidence table and reports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def money(value, digits: int = 0) -> str:
    # USD with thousands separators; mirrors tbml_common.money.
    if value is None or pd.isna(value):
        return "NA"
    return f"${float(value):,.{digits}f}"


def fmt(value, digits: int = 3) -> str:
    # General NA-safe formatter; integers get separators, floats fixed decimals.
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def score(value) -> str:
    # Review-priority scores always shown to 3 decimals.
    return fmt(value, 3)


def compact_usd(value) -> str:
    # Axis/KPI-friendly USD: $1.2M, $3.4B. Full precision stays in tooltips.
    if value is None or pd.isna(value):
        return "NA"
    v = float(value)
    for cut, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= cut:
            return f"${v / cut:,.1f}{suffix}"
    return f"${v:,.0f}"


def quantity_mt(value) -> str:
    # Metric tons; small quantities (gold) need decimals to stay meaningful.
    if value is None or pd.isna(value):
        return "NA"
    v = float(value)
    return f"{v:,.3f} mt" if abs(v) < 10 else f"{v:,.0f} mt"


def label_from_key(raw: str) -> str:
    # 'usable_with_caveat' -> 'Usable with caveat' (fallback when no mapping).
    return str(raw).replace("_", " ").strip().capitalize()


def corridor(exporter_iso3, importer_iso3) -> str:
    return f"{exporter_iso3} → {importer_iso3}"


def year_span(years) -> str:
    ys = sorted(int(y) for y in years)
    return f"{ys[0]}–{ys[-1]}" if ys else "NA"
