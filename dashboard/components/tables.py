"""Queue and generic tables — stakeholder labels outside, raw fields preserved inside.

The interactive review queue stays an st.dataframe (it needs single-row
selection, pinning, and the ProgressColumn score bar). The static reference
tables render as a themed HTML table (components/styles .data-table) so they get
real borders, a tinted header, refined zebra striping, and row hover — none of
which st.dataframe's canvas grid (glide-data-grid) can style. Cell values are
HTML-escaped and numeric columns are right-aligned with tabular figures; floats
are shown to 4 decimals (display only — the underlying values are unchanged).
"""

from __future__ import annotations

import html

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
        row_height=38,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
        column_config={
            "rank": st.column_config.NumberColumn(
                "Rank", format="%d", width="small", pinned=True,
                help="Queue position — 1 is the most unusual official observation. Not a severity score.",
            ),
            "year": st.column_config.NumberColumn("Year", format="%d", width="small"),
            "exporter_iso3": st.column_config.TextColumn(
                "Exporter", width="small", help="Reporter (exporter) ISO3 country code.",
            ),
            "importer_iso3": st.column_config.TextColumn(
                "Importer", width="small", help="Partner (importer) ISO3 country code.",
            ),
            "hs6": st.column_config.TextColumn(
                "HS6", width="small", help="Six-digit Harmonised System product code.",
            ),
            "family_label": st.column_config.TextColumn("Product"),
            "selected_review_priority_score": st.column_config.ProgressColumn(
                "Review-priority score", min_value=0.0, max_value=1.0, format="%.3f",
                help="Relative ranking signal (0–1) for how unusual the pattern is. "
                     "Not a probability of wrongdoing.",
            ),
            "quality_status_label": st.column_config.TextColumn(
                "Data quality", width="medium",
                help="Data-quality status of the underlying official observation.",
            ),
            "key_evidence_count": st.column_config.NumberColumn(
                "Evidence", format="%d", width="small",
                help="Count of recomputable evidence rows backing this candidate.",
            ),
        },
    )


# ---- Styled HTML reference table -------------------------------------------

def _column_kind(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "bool"
    if pd.api.types.is_integer_dtype(series):
        return "int"
    if pd.api.types.is_float_dtype(series):
        return "float"
    return "other"


def _cell(value, kind: str) -> str:
    # Format for display and HTML-escape. Values are never altered analytically;
    # floats are shown to 4 dp (trailing zeros trimmed) purely for presentation.
    if pd.isna(value):
        return ""
    if kind == "int":
        return f"{int(value):,}"
    if kind == "float":
        number = float(value)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.4f}".rstrip("0").rstrip(".")
    if kind == "bool":
        return "Yes" if bool(value) else "No"
    return html.escape(str(value))


def plain_table(frame: pd.DataFrame, column_labels: dict[str, str] | None = None,
                height: int | None = None, zebra: bool = True) -> None:
    # Render a static reference table as themed HTML (see styles .data-table).
    # `height` caps the scroll height in px (sticky header stays visible);
    # `zebra` toggles alternating-row tint.
    columns = list(frame.columns)
    labels = column_labels or {}
    kinds = {col: _column_kind(frame[col]) for col in columns}
    numeric = {col: kinds[col] in ("int", "float") for col in columns}

    head_cells = "".join(
        f'<th class="num">{html.escape(str(labels.get(col, col)))}</th>' if numeric[col]
        else f"<th>{html.escape(str(labels.get(col, col)))}</th>"
        for col in columns
    )
    body_rows = []
    for _, row in frame.iterrows():
        cells = "".join(
            f'<td class="num">{_cell(row[col], kinds[col])}</td>' if numeric[col]
            else f"<td>{_cell(row[col], kinds[col])}</td>"
            for col in columns
        )
        body_rows.append(f"<tr>{cells}</tr>")

    table_class = "data-table zebra" if zebra else "data-table"
    wrap_style = (
        f' style="max-height:{int(height)}px; overflow-y:auto;"' if height else ""
    )
    markup = (
        f'<div class="data-table-wrap"{wrap_style}>'
        f'<table class="{table_class}">'
        f"<thead><tr>{head_cells}</tr></thead>"
        f'<tbody>{"".join(body_rows)}</tbody>'
        f"</table></div>"
    )
    st.markdown(markup, unsafe_allow_html=True)
