"""Queue and generic tables — stakeholder labels outside, raw fields preserved inside."""

from __future__ import annotations

import pandas as pd
import streamlit as st

# Raw column -> stakeholder-facing label for the review queue. Internal names
# stay untouched in the dataframe; only st.column_config renames them.
QUEUE_COLUMN_LABELS = {
    "rank": "Rank",
    "year": "Year",
    "exporter_iso3": "Exporter",
    "importer_iso3": "Importer",
    "hs6": "HS6",
    "family_label": "Product",
    "selected_review_priority_score": "Review-priority score",
    "quality_status_label": "Data quality",
    "key_evidence_count": "Evidence",
}
QUEUE_DISPLAY_COLUMNS = list(QUEUE_COLUMN_LABELS)


def queue_table(frame: pd.DataFrame, key: str, height: int = 460):
    # Single-row selection feeds the Case Investigation page via session state.
    shown = frame[QUEUE_DISPLAY_COLUMNS]
    return st.dataframe(
        shown,
        hide_index=True,
        width="stretch",
        height=height,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
        column_config={
            "rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
            "year": st.column_config.NumberColumn("Year", format="%d", width="small"),
            "exporter_iso3": st.column_config.TextColumn("Exporter", width="small"),
            "importer_iso3": st.column_config.TextColumn("Importer", width="small"),
            "hs6": st.column_config.TextColumn("HS6", width="small"),
            "family_label": st.column_config.TextColumn("Product"),
            "selected_review_priority_score": st.column_config.ProgressColumn(
                "Review-priority score", min_value=0.0, max_value=1.0, format="%.3f",
            ),
            "quality_status_label": st.column_config.TextColumn("Data quality"),
            "key_evidence_count": st.column_config.NumberColumn("Evidence", format="%d", width="small"),
        },
    )


def plain_table(frame: pd.DataFrame, column_labels: dict[str, str] | None = None,
                height: int | None = None) -> None:
    # Short reference tables grow with their content; long ones pass a pixel cap.
    config = {raw: st.column_config.Column(label) for raw, label in (column_labels or {}).items()}
    st.dataframe(frame, hide_index=True, width="stretch",
                 height=height if height is not None else "content",
                 column_config=config or None)
