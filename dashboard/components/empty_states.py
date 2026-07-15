"""Transparent empty states — a missing output is stated, never papered over."""

from __future__ import annotations

import streamlit as st

from dashboard.services.data_loader import load_content, regenerate_hint
from dashboard.services import path_resolver as paths


def missing_output(name: str) -> None:
    # The standard notice, plus exactly which file is absent and what to run.
    st.warning(
        f"{load_content()['empty_state']}\n\n"
        f"Missing file: `{paths.relpath(name)}`  \n"
        f"Regenerate with: `{regenerate_hint(name)}`",
        icon="🗂️",
    )


def no_rows(message: str = "No records match the current filters.") -> None:
    st.info(message, icon="🔍")


def missing_figure(figure_relpath: str, label: str) -> None:
    # A referenced report figure is absent: state which file and what it shows,
    # so a missing diagram degrades to a labelled notice instead of crashing.
    st.warning(
        f"{label} is not available in this build.\n\n"
        f"Missing figure: `{figure_relpath}`  \n"
        "Regenerate the reporting figures and reload the dashboard.",
        icon="🖼️",
    )
