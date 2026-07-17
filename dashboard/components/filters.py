"""The Review Queue filter row — one place above everything it scopes."""

from __future__ import annotations

import streamlit as st

from dashboard.services import session_state as state


def queue_filters(options: dict, copy: dict) -> dict:
    # Four primary filters. Empty multiselects mean "no restriction" so a
    # cleared filter can never blank the queue by accident.
    row1 = st.columns(4)
    with row1[0]:
        years = st.multiselect("Year", options["years"], key="queue_years")
    with row1[1]:
        families = st.multiselect("Product family", options["families"], key="queue_families")
    with row1[2]:
        exporters = st.multiselect("Exporter", options["exporters"], key="queue_exporters")
    with row1[3]:
        importers = st.multiselect("Importer", options["importers"], key="queue_importers")

    size_options = [str(option) for option in copy["queue_size_options"]]
    row2 = st.columns([2.4, 1.6, 1], vertical_alignment="bottom")
    with row2[0]:
        choice = st.segmented_control(
            copy["queue_size_label"], size_options,
            default=size_options[0], key="queue_size",
        )
    with row2[2]:
        st.button(copy["reset_label"], on_click=state.reset_queue_filters, width="stretch")

    # Each option label carries its own size ("Top 50" -> 50) so the governed
    # copy and the behaviour cannot drift. Deselecting the control (clicking
    # the active segment) falls back to the first option.
    top_n = int(str(choice or size_options[0]).rsplit(" ", 1)[-1])
    published = int(options.get("published", 0))
    largest = max(int(option.rsplit(" ", 1)[-1]) for option in size_options)
    if 0 < published < largest:
        # The pipeline publishes fewer rows than the largest option: say so
        # plainly instead of pretending a bigger queue exists.
        st.caption(copy["queue_size_note"].format(published=published))

    with st.expander(copy["advanced_label"]):
        low = float(options["score_min"])
        high = float(options["score_max"])
        pad = max((high - low) * 0.05, 0.0005)  # keep endpoints selectable
        score_range = st.slider(
            "Review-priority score range",
            min_value=round(low - pad, 4), max_value=round(high + pad, 4),
            value=(round(low - pad, 4), round(high + pad, 4)),
            step=0.001, key="queue_score_range",
        )

    return {
        "years": years,
        "families": families,
        "exporters": exporters,
        "importers": importers,
        "score_range": score_range,
        "top_n": top_n,
    }
