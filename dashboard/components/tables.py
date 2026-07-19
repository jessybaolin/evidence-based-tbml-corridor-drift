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

from dashboard.services.data_loader import load_content, load_theme


def queue_table(display: pd.DataFrame, key: str, highlight_row: int | None = None,
                mappings: str = "", height: int = 520):
    # Renders the frame produced by dashboard_metrics.queue_display_frame
    # (nine columns, fixed order). Single-row selection is Streamlit's row-pick
    # affordance and feeds Selected Case Review via session state; the current
    # case row is tinted amber through a pandas Styler (per-row CSS cannot
    # reach st.dataframe's canvas grid, but Styler backgrounds can). Numbers
    # are rounded by st.column_config only — the underlying values stay exact.
    theme = load_theme()
    palette = theme["palette"]
    content = load_content()
    columns_copy = content["pages"]["review_queue"]["columns"]
    stripe = theme["components"]["table"]["stripe_bg"]
    selected_bg = theme["selection"]["background"]
    selected_border = theme["selection"]["border"]
    family_styles = {
        content["family_short_labels"][family_id]: color
        for family_id, color in theme["families"].items()
    }

    frame = display.reset_index(drop=True)
    style_frame = pd.DataFrame("", index=frame.index, columns=frame.columns)
    for row_index, row in frame.iterrows():
        selected = highlight_row is not None and row_index == highlight_row
        if selected:
            selected_style = (
                f"background-color: color-mix(in srgb, {selected_bg} 58%, white); "
                f"color: {theme['selection']['text']}"
            )
            style_frame.loc[row_index, :] = selected_style
            style_frame.loc[row_index, "rank"] += (
                f"; border-left: 3px solid {selected_border}; font-weight: 800"
            )
        elif row_index % 2 == 1:
            style_frame.loc[row_index, :] = f"background-color: {stripe}"

        rank = int(row["rank"])
        if rank == 1:
            style_frame.loc[row_index, "rank"] += f"; color: {palette['ink']}; font-weight: 800"
        elif rank <= 3:
            style_frame.loc[row_index, "rank"] += "; font-weight: 700"

        if not selected:
            family_color = family_styles.get(str(row["product"]))
            if family_color:
                style_frame.loc[row_index, "product"] += (
                    f"; background-color: color-mix(in srgb, {family_color} 10%, white); "
                    f"color: {family_color}; font-weight: 700"
                )

    def _copy(column: str, **fmt) -> dict:
        entry = columns_copy[column]
        help_text = entry["help"].format(**fmt) if fmt else entry["help"]
        return {"label": entry["label"], "help": help_text}

    rank_copy = _copy("rank")
    corridor_copy = _copy("corridor")
    product_copy = _copy("product", mappings=mappings)
    score_copy = _copy("selected_review_priority_score")
    return st.dataframe(
        frame.style.apply(lambda _: style_frame, axis=None),
        hide_index=True,
        width="stretch",
        height=height,
        row_height=42,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
        column_config={
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
                product_copy["label"], width=112, help=product_copy["help"],
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
                _copy("unit_value_usd_per_metric_ton")["label"], format="dollar", width=130,
                help=_copy("unit_value_usd_per_metric_ton")["help"],
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
