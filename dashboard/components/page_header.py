"""Page header (eyebrow / title / subtitle) + section titles + provenance ledger."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.services import path_resolver as paths


def page_header(title: str, subtitle: str, eyebrow: str = "Stakeholder analytics") -> None:
    st.markdown(
        f"""
        <div class="page-eyebrow">{html.escape(eyebrow)}</div>
        <h1 class="page-title">{html.escape(title)}</h1>
        <div class="page-subtitle">{html.escape(subtitle)}</div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: str | None = None) -> None:
    st.markdown(f'<div class="section-label">{html.escape(title)}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="section-caption">{html.escape(caption)}</div>', unsafe_allow_html=True)


def ledger(*file_keys: str, note: str = "") -> None:
    # The provenance ledger line: which repository files back this panel.
    parts = [paths.relpath(key) for key in file_keys]
    if note:
        parts.append(note)
    st.markdown(f'<div class="ledger">{html.escape(" · ".join(parts))}</div>', unsafe_allow_html=True)
