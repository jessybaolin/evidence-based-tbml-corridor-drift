"""The Review Queue filter row — one place above everything it scopes."""

from __future__ import annotations

import streamlit as st

from dashboard.components.icons import render_icon
from dashboard.services import session_state as state


def queue_filters(options: dict, copy: dict):
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

    all_size_options = [str(option) for option in copy["queue_size_options"]]
    published = int(options.get("published", 0))
    size_options = [
        option for option in all_size_options
        if int(option.rsplit(" ", 1)[-1]) <= published
    ] or all_size_options[:1]

    row2 = st.columns([2.4, 2.2, 1.4], vertical_alignment="center")
    with row2[0]:
        choice = st.segmented_control(
            copy["queue_size_label"], size_options,
            default=size_options[0], key="queue_size",
        )

    # Each option label carries its own size ("Top 50" -> 50) so the governed
    # copy and the behaviour cannot drift. Deselecting the control (clicking
    # the active segment) falls back to the first option.
    top_n = int(str(choice or size_options[0]).rsplit(" ", 1)[-1])
    largest = max(int(option.rsplit(" ", 1)[-1]) for option in all_size_options)
    if 0 < published < largest:
        note = copy["queue_size_note"].format(published=published)
        with row2[1]:
            st.markdown(
                f'<div class="queue-size-helper" role="note">{render_icon("info")}'
                f'<span class="tip" tabindex="0" data-tip="{note}">'
                f"Top {published} currently available</span></div>",
                unsafe_allow_html=True,
            )
    with row2[2]:
        result_slot = st.empty()

    with st.expander(copy["advanced_label"]):
        low = float(options["score_min"])
        high = float(options["score_max"])
        pad = max((high - low) * 0.05, 0.0005)  # keep endpoints selectable
        score_default = (round(low - pad, 4), round(high + pad, 4))
        score_range = st.slider(
            "Review-priority score range",
            min_value=round(low - pad, 4), max_value=round(high + pad, 4),
            value=score_default,
            step=0.001, key="queue_score_range",
        )
        st.button(
            "Clear advanced filters", key="queue_clear_advanced",
            icon=":material/close:", on_click=state.clear_queue_filter,
            args=("queue_score_range",),
        )

    filters = {
        "years": years,
        "families": families,
        "exporters": exporters,
        "importers": importers,
        "score_range": score_range,
        "score_default": score_default,
        "top_n": top_n,
    }
    return filters, result_slot


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

    score_range = tuple(filters.get("score_range") or ())
    score_default = tuple(filters.get("score_default") or ())
    if score_range and score_range != score_default:
        specs.append((
            "queue_score_range", "Score",
            f"{float(score_range[0]):.3f}-{float(score_range[1]):.3f}",
        ))

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
