"""The Review Queue filter row — one place above everything it scopes."""

from __future__ import annotations

import streamlit as st

from dashboard.services import session_state as state


def queue_filters(options: dict):
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

    filters = {
        "years": years,
        "families": families,
        "exporters": exporters,
        "importers": importers,
    }
    return filters


def render_active_filter_chips(filters: dict) -> None:
    """Render one keyboard-accessible clear action for every active filter."""
    specs: list[tuple[str, str, str]] = []
    for key, label, values in (
        ("queue_years", "Year", filters.get("years")),
        ("queue_families", "Product", filters.get("families")),
        ("queue_exporters", "Exporter", filters.get("exporters")),
        ("queue_importers", "Importer", filters.get("importers")),
    ):
        if values:
            specs.append((key, label, ", ".join(str(value) for value in values)))

    if not specs:
        return

    with st.container(key="queue_filter_chips"):
        columns = st.columns(len(specs))
        for column, (key, label, value) in zip(columns, specs):
            with column:
                st.button(
                    f"{label}: {value}", key=f"queue_clear_{key}",
                    icon=":material/close:", on_click=state.clear_queue_filter,
                    args=(key,), width="stretch",
                )
