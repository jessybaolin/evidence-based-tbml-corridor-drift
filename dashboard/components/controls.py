"""Presentation wrappers for control groups without changing widget semantics."""

from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


@contextmanager
def render_filter_panel():
    """Provide a stable keyed container for centrally styled filter controls."""
    with st.container(key="dashboard_filter_panel"):
        yield

