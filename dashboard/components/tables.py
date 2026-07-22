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
from collections.abc import Callable

import pandas as pd
import streamlit as st

from dashboard.services.data_loader import load_content, load_theme


def queue_table(display: pd.DataFrame, key: str, highlight_row: int | None = None,
                mappings: str = "", height: int = 520):
    # Renders the frame produced by dashboard_metrics.queue_display_frame
    # (nine analytical columns, fixed order). A read-only checkbox marks the
    # current case while single-cell selection lets any cell pick its row; the
    # case row is tinted amber through a pandas Styler (per-row CSS cannot
    # reach st.dataframe's canvas grid, but Styler backgrounds can). Numbers
    # are rounded by st.column_config only — the underlying values stay exact.
    theme = load_theme()
    palette = theme["palette"]
    content = load_content()
    columns_copy = content["pages"]["review_queue"]["columns"]
    stripe = theme["components"]["table"]["stripe_bg"]
    families = theme["families"]
    family_colors = {
        content["family_short_labels"]["gold_unwrought"]: families["gold_unwrought"],
        content["family_short_labels"]["crude_palm_oil"]: families["crude_palm_oil"],
        content["family_short_labels"]["refined_copper_cathodes"]: families["refined_copper_cathodes"],
    }

    frame = display.reset_index(drop=True)
    frame.insert(
        0,
        "current_case",
        [highlight_row is not None and row == highlight_row for row in frame.index],
    )
    # Flat family dot (no glossy emoji "shadow"): a plain "●" glyph coloured per
    # family through the Styler below — the whole product cell takes the colour.
    product_colors = frame["product"].map(lambda label: family_colors.get(str(label), ""))
    frame["product"] = frame["product"].map(lambda label: f"●  {label}")
    style_frame = pd.DataFrame("", index=frame.index, columns=frame.columns)
    for row_index, row in frame.iterrows():
        # The current case is marked only by its ticked "current_case" checkbox
        # (and the banner above) — no row-background highlight, so the table stays
        # calm and the zebra striping is never interrupted.
        if row_index % 2 == 1:
            style_frame.loc[row_index, :] = f"background-color: {stripe}"

        rank = int(row["rank"])
        if rank == 1:
            style_frame.loc[row_index, "rank"] += f"; color: {palette['ink']}; font-weight: 800"
        elif rank <= 3:
            style_frame.loc[row_index, "rank"] += "; font-weight: 700"

        # Flat family colour on the product cell (the "●" dot + label).
        if product_colors.iloc[row_index]:
            style_frame.loc[row_index, "product"] += (
                f"; color: {product_colors.iloc[row_index]}; font-weight: 650"
            )

    def _copy(column: str, **fmt) -> dict:
        entry = columns_copy[column]
        help_text = entry["help"].format(**fmt) if fmt else entry["help"]
        return {"label": entry["label"], "help": help_text}

    rank_copy = _copy("rank")
    corridor_copy = _copy("corridor")
    product_copy = _copy("product", mappings=mappings)
    score_copy = _copy("selected_review_priority_score")
    # Column headers match the reference tables (data dictionary): navy + frost.
    styled_frame = frame.style.apply(lambda _: style_frame, axis=None).set_table_styles([
        {
            "selector": "th",
            "props": [
                ("background-color", palette["sidebar_bg"]),
                ("color", palette["sidebar_ink"]),
                ("font-weight", "700"),
            ],
        },
    ])
    return st.dataframe(
        styled_frame,
        hide_index=True,
        width="stretch",
        height=height,
        row_height=42,
        on_select="rerun",
        selection_mode="single-cell",
        key=key,
        column_config={
            "current_case": st.column_config.CheckboxColumn("", width=38),
            "rank": st.column_config.NumberColumn(
                rank_copy["label"], format="%d", width=62, pinned=True,
                help=rank_copy["help"],
            ),
            "year": st.column_config.NumberColumn(
                _copy("year")["label"], format="%d", width=58, help=_copy("year")["help"],
            ),
            "corridor": st.column_config.TextColumn(
                corridor_copy["label"], width=108, help=corridor_copy["help"],
            ),
            "product": st.column_config.TextColumn(
                product_copy["label"], width=126, help=product_copy["help"],
            ),
            "trade_value_usd": st.column_config.NumberColumn(
                _copy("trade_value_usd")["label"], format="localized", width=128,
                help=_copy("trade_value_usd")["help"],
            ),
            "quantity_metric_ton": st.column_config.NumberColumn(
                _copy("quantity_metric_ton")["label"], format="localized", width=126,
                help=_copy("quantity_metric_ton")["help"],
            ),
            "unit_value_usd_per_metric_ton": st.column_config.NumberColumn(
                # No in-grid help: the definition lives in the footer note under
                # the table (the dataframe positioned the tooltip far from here).
                _copy("unit_value_usd_per_metric_ton")["label"], format="dollar", width=145,
            ),
            "benchmark_price_usd_per_metric_ton": st.column_config.NumberColumn(
                _copy("benchmark_price_usd_per_metric_ton")["label"], format="dollar", width=140,
                help=_copy("benchmark_price_usd_per_metric_ton")["help"],
            ),
            "selected_review_priority_score": st.column_config.ProgressColumn(
                score_copy["label"], min_value=0.0, max_value=1.0, format="%.3f",
                help=score_copy["help"], width=180,
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
                height: int | None = None, zebra: bool = True,
                formatters: dict[str, Callable[[object], str]] | None = None) -> None:
    # Render a static reference table as themed HTML (see styles .data-table).
    # `height` caps the scroll height in px (sticky header stays visible);
    # `zebra` toggles alternating-row tint.
    columns = list(frame.columns)
    labels = column_labels or {}
    display_formatters = formatters or {}
    kinds = {col: _column_kind(frame[col]) for col in columns}
    numeric = {col: kinds[col] in ("int", "float") for col in columns}

    head_cells = "".join(
        f'<th class="num">{html.escape(str(labels.get(col, col)))}</th>' if numeric[col]
        else f"<th>{html.escape(str(labels.get(col, col)))}</th>"
        for col in columns
    )
    body_rows = []
    for _, row in frame.iterrows():
        cells = []
        for col in columns:
            if col in display_formatters and not pd.isna(row[col]):
                value = html.escape(str(display_formatters[col](row[col])))
            else:
                value = _cell(row[col], kinds[col])
            cell_class = ' class="num"' if numeric[col] else ""
            cells.append(f"<td{cell_class}>{value}</td>")
        body_rows.append(f'<tr>{"".join(cells)}</tr>')

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
