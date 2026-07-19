"""
Predictable session-state handling — the only module that names state keys.

WHAT IT DOES:
    Wraps every st.session_state key the app uses behind typed helpers so pages
    never invent ad-hoc keys. Case selection survives navigation; queue filters
    reset through one function.
"""

from __future__ import annotations

import streamlit as st

# All session-state keys in one place. Widget-owned keys (the ones passed as
# `key=` to widgets) are listed so reset_queue_filters can clear them safely.
SELECTED_OBS = "tbml_selected_obs_id"
QUEUE_FILTER_KEYS = [
    "queue_years", "queue_families", "queue_exporters", "queue_importers",
    "queue_score_range", "queue_size",
]
APPENDIX_KEYS = ["dict_search", "dict_categories", "dict_datasets", "dict_sources"]


def selected_obs_id() -> str | None:
    return st.session_state.get(SELECTED_OBS)


def select_obs(obs_id: str) -> None:
    st.session_state[SELECTED_OBS] = str(obs_id)


def clear_selection() -> None:
    st.session_state.pop(SELECTED_OBS, None)


def reset_queue_filters() -> None:
    # Deleting widget keys resets each widget to its declared default on rerun.
    for key in QUEUE_FILTER_KEYS:
        st.session_state.pop(key, None)


def clear_queue_filter(key: str) -> None:
    """Clear one governed queue widget without disturbing the other filters."""
    if key not in QUEUE_FILTER_KEYS:
        raise ValueError(f"Unknown queue filter key: {key}")
    st.session_state.pop(key, None)
