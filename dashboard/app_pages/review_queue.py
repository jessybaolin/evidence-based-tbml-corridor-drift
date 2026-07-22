"""Review Queue — the ranked official observations, filterable and selectable."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from dashboard.components.empty_states import no_rows
from dashboard.components.filters import queue_filters, render_active_filter_chips
from dashboard.components.controls import render_filter_panel
from dashboard.components.icons import render_icon
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.components.tables import queue_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import session_state as state


def _selection_rows(pending) -> list[int]:
    # The grid stores its selection under the widget key as an attribute-dict
    # ({"selection": {"rows": [...]}}); read it defensively either way.
    if pending is None:
        return []
    selection = getattr(pending, "selection", None)
    if selection is None and isinstance(pending, dict):
        selection = pending.get("selection")
    if selection is None:
        return []
    rows = getattr(selection, "rows", None)
    if rows is None and isinstance(selection, dict):
        rows = selection.get("rows")
    if rows:
        return list(rows)
    cells = getattr(selection, "cells", None)
    if cells is None and isinstance(selection, dict):
        cells = selection.get("cells")
    return [int(cells[0][0])] if cells else []


def _country(row: pd.Series, name_column: str, iso_column: str) -> str:
    value = row.get(name_column)
    return str(value) if pd.notna(value) else str(row[iso_column])


content = load.load_content()
copy = content["pages"]["review_queue"]
with st.container(key="queue_header"):
    page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
    st.markdown(
        f'<div class="queue-interpretation-boundary" role="note">'
        f'{render_icon("info")}<span>{html.escape(copy["caveat"])}</span></div>',
        unsafe_allow_html=True,
    )

queue = load.load_review_queue()
features = load.load_features(columns=(
    "obs_id", "exporter_name", "importer_name", "benchmark_residual", "robust_historical_z",
))
enriched = metrics.enrich_queue(queue, features, content["family_short_labels"])

with render_filter_panel():
    filter_title, filter_action = st.columns(
        [4.6, 1], vertical_alignment="center", gap="medium",
    )
    with filter_title:
        section_title(copy["filters_heading"], icon="sliders")
    with filter_action:
        st.button(
            copy["reset_label"], key="queue_reset_filters",
            icon=":material/restart_alt:", on_click=state.reset_queue_filters,
            width="stretch",
        )
    filters = queue_filters(
        metrics.queue_filter_options(enriched), metrics.family_hs6_map(enriched)
    )
    filtered = metrics.apply_queue_filters(enriched, filters)

if filtered.empty:
    section_title(copy["results_heading"], icon="list-ordered")
    no_rows(copy["empty_message"])
else:
    # Key the table by the filtered rows and current case. This clears the
    # temporary cell focus after a pick while preserving the governed case.
    table_identity = f"queue_table_{pd.util.hash_pandas_object(filtered['obs_id'], index=False).sum():x}"
    selection_owner = state.selected_obs_id() or "default"
    table_key = f"{table_identity}_{selection_owner}"

    # Resolve this rerun's cell pick before rendering so the banner, checked
    # marker and amber row all update together.
    picked = _selection_rows(st.session_state.get(table_key))
    if picked and 0 <= picked[0] < len(filtered):
        state.select_obs(str(filtered.iloc[picked[0]]["obs_id"]))
        st.session_state.pop(table_key, None)

    # Current case: the sticky selection while it still points at a queue row,
    # otherwise the default that Selected Case Review opens with (rank 1). The
    # emptiness check keeps an orphaned id (e.g. after a pipeline rerun) harmless.
    current = pd.DataFrame()
    if state.selected_obs_id():
        current = enriched.loc[enriched["obs_id"] == state.selected_obs_id()]
    if current.empty:
        case_row = metrics.default_case(enriched)
        template = copy["banner_default"]
    else:
        case_row = current.iloc[0]
        template = copy["banner_current"]

    mappings = " · ".join(
        f"{family} = HS6 {code}" for family, code in metrics.family_hs6_map(enriched).items()
    )

    # ---- Results header: interpretation left, export note + button right. ----
    with st.container(key="queue_results_header"):
        heading_col, info_col, export_col = st.columns(
            [4.0, 0.3, 1.3], vertical_alignment="center", gap="small",
        )
        with heading_col:
            section_title(
                copy["results_heading"],
                copy["results_caption"],
                icon="list-ordered",
            )
        with info_col:
            # The rounding / full-precision-export note lives here as an info
            # icon beside the button (was a footer caption).
            st.markdown(
                f'<div class="queue-export-info">'
                f'<span class="tip queue-export-tip" tabindex="0" role="note" '
                f'data-tip="{html.escape(copy["table_caption_precision"], quote=True)}">'
                f'{render_icon("info")}</span></div>',
                unsafe_allow_html=True,
            )
        with export_col:
            st.download_button(
                copy["export_label"],
                data=metrics.queue_export_frame(filtered).to_csv(index=False).encode("utf-8"),
                file_name="review_queue_current_view.csv",
                mime="text/csv",
                help=copy["export_help"],
                icon=":material/download:",
                width="stretch",
            )

    # ---- Current-case control: a pinned representation of the selected row. ----
    line = template.format(
        rank=int(case_row["rank"]),
        year=int(case_row["year"]),
        exporter=_country(case_row, "exporter_name", "exporter_iso3"),
        importer=_country(case_row, "importer_name", "importer_iso3"),
        product=case_row["family_label"],
    )
    lead, _, rest = line.partition(": ")
    with st.container(key="queue_case_banner"):
        text_col, cta_col = st.columns([3.4, 1], vertical_alignment="center", gap="medium")
        with text_col:
            st.markdown(
                f'<div class="current-case-label">Current case</div>'
                f'<div class="case-banner-text"><strong>{html.escape(lead)}:</strong> '
                f"{html.escape(rest)}</div>",
                unsafe_allow_html=True,
            )
        with cta_col:
            st.page_link(
                "app_pages/case_investigation.py", label=copy["open_case_label"],
                icon=":material/folder_open:", width="stretch",
            )

    # ---- One-filter-at-a-time clear actions. ----
    render_active_filter_chips(filters)

    # ---- The queue itself: cell selection avoids Streamlit's faded row wash. ----
    display = metrics.queue_display_frame(filtered)
    displayed_rows = filtered.reset_index(drop=True)
    positions = displayed_rows.index[displayed_rows["obs_id"] == case_row["obs_id"]]
    highlight = int(positions[0]) if len(positions) else None
    table_key = f"{table_identity}_{state.selected_obs_id() or 'default'}"
    with st.container(key="queue_table_region"):
        queue_table(
            display,
            key=table_key,
            highlight_row=highlight,
            mappings=mappings,
        )

    # "How to read this queue" — the score explainer plus the unit-value
    # definition, both as footer notes (the in-grid column tooltip is dropped
    # because the dataframe positions it far from the header).
    unit_value_note = copy["columns"]["unit_value_usd_per_metric_ton"]["help"]
    with st.container(key="queue_score_guidance"):
        st.markdown(
            f'<div class="queue-guidance-content">'
            f'<div class="queue-guidance-icon">{render_icon("info")}</div>'
            f'<div><div class="queue-guidance-label">How to read the score</div>'
            f'<div class="queue-guidance-text">{html.escape(copy["score_note"])}</div></div>'
            f'</div>'
            f'<div class="queue-guidance-content">'
            f'<div class="queue-guidance-icon">{render_icon("info")}</div>'
            f'<div><div class="queue-guidance-label">How unit value is calculated</div>'
            f'<div class="queue-guidance-text">{html.escape(unit_value_note)}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

ledger("review_queue", "features", note="scores ranked on real official observations only")

# Reveal the queue's sections (banner, table, guidance) as they scroll in.
render_scroll_reveal(
    ".st-key-queue_header, .st-key-queue_case_banner, .st-key-queue_table_region, "
    ".st-key-queue_score_guidance"
)
