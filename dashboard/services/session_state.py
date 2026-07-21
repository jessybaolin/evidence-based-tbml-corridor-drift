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
]
APPENDIX_KEYS = ["dict_search"]
LANDING_COMPLETE = "tbml_landing_complete"
DASHBOARD_ENTRY_PENDING = "tbml_dashboard_entry_pending"


def init_landing() -> None:
    """Root visit: make the completion flag exist before the CTA reads it."""
    st.session_state.setdefault(LANDING_COMPLETE, False)


def landing_complete() -> bool:
    return bool(st.session_state.get(LANDING_COMPLETE, False))


def complete_landing() -> None:
    # CTA click: the flag survives every rerun and page switch this session,
    # and the next dashboard render plays its one-shot entrance exactly once.
    st.session_state[LANDING_COMPLETE] = True
    st.session_state[DASHBOARD_ENTRY_PENDING] = True


def consume_dashboard_entry() -> bool:
    """True exactly once — on the first dashboard render after the CTA."""
    return bool(st.session_state.pop(DASHBOARD_ENTRY_PENDING, False))


def selected_obs_id() -> str | None:
    return st.session_state.get(SELECTED_OBS)


def select_obs(obs_id: str) -> None:
    st.session_state[SELECTED_OBS] = str(obs_id)


def clear_selection() -> None:
    st.session_state.pop(SELECTED_OBS, None)


def reset_queue_filters() -> None:
    # Explicit empty values also clear mounted multiselect chips on the rerun.
    for key in QUEUE_FILTER_KEYS:
        st.session_state[key] = []


def clear_queue_filter(key: str) -> None:
    """Clear one governed queue widget without disturbing the other filters."""
    if key not in QUEUE_FILTER_KEYS:
        raise ValueError(f"Unknown queue filter key: {key}")
    st.session_state[key] = []
