"""Review Queue — the ranked official observations, filterable and selectable."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from dashboard.components.empty_states import no_rows
from dashboard.components.filters import queue_filters
from dashboard.components.controls import render_filter_panel
from dashboard.components.page_header import ledger, page_header, section_title
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
    return list(rows or [])


def _country(row: pd.Series, name_column: str, iso_column: str) -> str:
    value = row.get(name_column)
    return str(value) if pd.notna(value) else str(row[iso_column])


content = load.load_content()
copy = content["pages"]["review_queue"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
st.caption(copy["caveat"])

queue = load.load_review_queue()
features = load.load_features(columns=(
    "obs_id", "exporter_name", "importer_name", "benchmark_residual", "robust_historical_z",
))
enriched = metrics.enrich_queue(queue, features, content["family_short_labels"])

with render_filter_panel():
    section_title(copy["filters_heading"], copy["filters_caption"])
    filters = queue_filters(metrics.queue_filter_options(enriched), copy)
filtered = metrics.apply_queue_filters(enriched, filters)

section_title(copy["results_heading"])

if filtered.empty:
    no_rows(copy["empty_message"])
else:
    # Key the table by the filtered row set: Streamlit keeps a row selection
    # bound to the widget key across reruns, so after a filter change a stale
    # positional selection would crash (index out of bounds) or silently point
    # at a different observation. A content-derived key drops it instead.
    table_key = f"queue_table_{pd.util.hash_pandas_object(filtered['obs_id'], index=False).sum():x}"

    # Resolve this rerun's row pick BEFORE anything renders: the grid stores
    # its selection in session state under the widget key, so the banner and
    # the amber row tint reflect the click that triggered this run instead of
    # lagging one interaction behind.
    picked = _selection_rows(st.session_state.get(table_key))
    if picked and 0 <= picked[0] < len(filtered):
        state.select_obs(str(filtered.iloc[picked[0]]["obs_id"]))

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

    # ---- Export row: the current view, full precision, always rank-ordered ----
    count_col, export_col = st.columns([2.8, 1], vertical_alignment="center")
    with count_col:
        st.caption(copy["results_caption"].format(
            shown=f"{len(filtered):,}", total=f"{len(enriched):,}",
        ))
    with export_col:
        st.download_button(
            copy["export_label"],
            data=metrics.queue_export_frame(filtered).to_csv(index=False).encode("utf-8"),
            file_name="review_queue_current_view.csv",
            mime="text/csv",
            help=copy["export_help"],
            width="stretch",
        )

    # ---- Current-case banner: amber = attention/caveat, never a finding ----
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
                f'<div class="case-banner-text"><strong>{html.escape(lead)}:</strong> '
                f"{html.escape(rest)}</div>",
                unsafe_allow_html=True,
            )
        with cta_col:
            st.page_link(
                "app_pages/case_investigation.py", label=copy["open_case_label"],
                icon=":material/folder_open:", width="stretch",
            )

    # ---- The queue itself ----
    display = metrics.queue_display_frame(filtered)
    positions = filtered.index[filtered["obs_id"] == case_row["obs_id"]]
    highlight = int(positions[0]) if len(positions) else None
    queue_table(display, key=table_key, highlight_row=highlight, mappings=mappings)

    st.caption(copy["score_note"])
    st.caption(copy["table_caption_products"].format(mappings=mappings))
    st.caption(copy["table_caption_precision"])

ledger("review_queue", "features", note="scores ranked on real official observations only")
