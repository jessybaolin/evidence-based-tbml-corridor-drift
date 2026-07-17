"""Review Queue — the ranked official observations, filterable and selectable."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.empty_states import no_rows
from dashboard.components.filters import queue_filters
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.status_badges import quality_label
from dashboard.components.tables import queue_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import session_state as state

content = load.load_content()
copy = content["pages"]["review_queue"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
st.caption(copy["caveat"])

queue = load.load_review_queue()
features = load.load_features(columns=(
    "obs_id", "exporter_name", "importer_name", "benchmark_residual", "robust_historical_z",
))
enriched = metrics.enrich_queue(queue, features, content["family_short_labels"])
enriched["quality_status_label"] = enriched["quality_status"].map(quality_label)

section_title("Filters", "Every control refreshes the queue below; empty filters mean no restriction.")
filters = queue_filters(metrics.queue_filter_options(enriched))
filtered = metrics.apply_queue_filters(enriched, filters)

section_title(
    "Ranked official observations",
    f"{len(filtered):,} of {len(enriched):,} review candidates match the current filters. "
    "Select a row to open it in Case Investigation.",
)

if filtered.empty:
    no_rows("No review candidates match the current filters. Reset the filters or widen the score range.")
else:
    # Key the table by the filtered row set: Streamlit keeps a row selection
    # bound to the widget key across reruns, so after a filter change a stale
    # positional selection would crash (index out of bounds) or silently point
    # at a different observation. A content-derived key drops it instead.
    table_key = f"queue_table_{pd.util.hash_pandas_object(filtered['obs_id'], index=False).sum():x}"
    event = queue_table(filtered, key=table_key)
    selected_rows = getattr(getattr(event, "selection", None), "rows", [])
    if selected_rows and selected_rows[0] < len(filtered):
        selected = filtered.iloc[selected_rows[0]]
        state.select_obs(selected["obs_id"])
        st.success(
            f"Selected #{int(selected['rank'])}: {int(selected['year'])} {selected['corridor']} — "
            f"{selected['product_name']} (score {selected['selected_review_priority_score']:.3f}). "
            "Open **Case Investigation** in the navigation to explore it.",
            icon="🗂️",
        )
    elif state.selected_obs_id():
        current = enriched.loc[enriched["obs_id"] == state.selected_obs_id()]
        if not current.empty:
            row = current.iloc[0]
            st.info(
                f"Current case: #{int(row['rank'])} · {int(row['year'])} {row['corridor']} — "
                f"{row['product_name']}. Select another row to change it.",
                icon="📌",
            )
    else:
        st.info("Select a row to carry that observation into Case Investigation.", icon="📌")

    # Download exactly what is filtered, with raw analytical columns intact.
    csv_bytes = filtered.drop(columns=["quality_status_label"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download the filtered queue (CSV)",
        data=csv_bytes,
        file_name="filtered_review_queue.csv",
        mime="text/csv",
    )

ledger("review_queue", "features", note="scores ranked on real official observations only")
