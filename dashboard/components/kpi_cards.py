"""KPI card rows built on st.metric (styled globally in components/styles.py)."""

from __future__ import annotations

import streamlit as st


def kpi_row(cards: list[dict], per_row: int = 4) -> None:
    # cards: [{"label": ..., "value": ..., "detail": ...}, ...] — values arrive
    # pre-formatted from services.dashboard_metrics; nothing is computed here.
    for start in range(0, len(cards), per_row):
        chunk = cards[start:start + per_row]
        columns = st.columns(per_row)
        for column, card in zip(columns, chunk):
            column.metric(
                label=card["label"],
                value=card["value"],
                help=card.get("detail") or None,
            )
