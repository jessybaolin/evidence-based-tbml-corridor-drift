"""Evidence cards: the recomputable facts behind a case, with caveats attached."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from dashboard.components.status_badges import severity_pill
from dashboard.services import formatting as fm


def evidence_cards(rows: pd.DataFrame) -> None:
    # One card per evidence row: approved plain-English summary up front,
    # recomputable numbers and the caveat underneath. Nothing is generated.
    for _, row in rows.iterrows():
        summary = html.escape(str(row["plain_english_summary"]))
        meta = (
            f"{html.escape(str(row['evidence_id']))} · metric {html.escape(str(row['metric_name']))} · "
            f"observed {fm.fmt(row['observed_value'])} vs {fm.fmt(row['comparison_value'])} "
            f"({html.escape(str(row['comparison_group']))}) · threshold {fm.fmt(row['threshold'])}"
        )
        caveat = html.escape(str(row["caveat"]))
        st.markdown(
            f"""
            <div class="evidence-card">
            {severity_pill(row["severity"])}
            <div style="margin-top:0.4rem;">{summary}</div>
            <div class="evidence-meta">{meta}</div>
            <div class="evidence-meta">Caveat: {caveat}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
