"""The Review Queue filter row — one place above everything it scopes."""

from __future__ import annotations

import streamlit as st

from dashboard.services import session_state as state


def queue_filters(options: dict) -> dict:
    # Empty multiselects mean "no restriction" so a cleared filter can never
    # blank the queue by accident; the score slider spans the observed range.
    row1 = st.columns([1, 1, 1, 1])
    with row1[0]:
        years = st.multiselect("Year", options["years"], key="queue_years")
    with row1[1]:
        families = st.multiselect("Product family", options["families"], key="queue_families")
    with row1[2]:
        exporters = st.multiselect("Exporter", options["exporters"], key="queue_exporters")
    with row1[3]:
        importers = st.multiselect("Importer", options["importers"], key="queue_importers")

    row2 = st.columns([1.2, 1.4, 1, 1])
    with row2[0]:
        statuses = st.multiselect("Data-quality status", options["statuses"], key="queue_statuses")
    with row2[1]:
        low = float(options["score_min"])
        high = float(options["score_max"])
        pad = max((high - low) * 0.05, 0.0005)  # keep endpoints selectable
        score_range = st.slider(
            "Review-priority score range",
            min_value=round(low - pad, 4), max_value=round(high + pad, 4),
            value=(round(low - pad, 4), round(high + pad, 4)),
            step=0.001, key="queue_score_range",
        )
    with row2[2]:
        min_evidence = st.number_input("Min evidence rows", min_value=0, max_value=20,
                                       value=0, step=1, key="queue_min_evidence")
    with row2[3]:
        top_n = st.number_input("Show top N by rank (0 = all)", min_value=0, max_value=500,
                                value=0, step=10, key="queue_top_n")

    row3 = st.columns([3, 1])
    with row3[0]:
        search = st.text_input(
            "Search (obs_id, corridor, country name, HS6)",
            key="queue_search", placeholder="e.g. ESP, Nepal, 710812, obs_c1178…",
        )
    with row3[1]:
        st.write("")  # aligns the button with the input's baseline
        st.button("Reset filters", on_click=state.reset_queue_filters, width="stretch")

    return {
        "years": years,
        "families": families,
        "exporters": exporters,
        "importers": importers,
        "statuses": statuses,
        "score_range": score_range,
        "min_evidence": int(min_evidence) or None,
        "search": search,
        "top_n": int(top_n) or None,
    }
