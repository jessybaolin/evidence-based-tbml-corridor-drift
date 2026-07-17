"""Shared information-banner and dataset-strip presentation."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon, render_icon_badge


def render_info_banner(label: str, body: str, *, icon: str = "brain") -> None:
    st.markdown(
        f'<div class="mental-model" role="note">{render_icon_badge(icon, class_name="banner-icon")}'
        f'<div><span class="mm-stamp">{html.escape(label)}</span>{html.escape(body)}</div></div>',
        unsafe_allow_html=True,
    )


def render_dataset_strip(text: str) -> None:
    st.markdown(
        f'<div class="ledger dataset-strip">{render_icon("file-text")}'
        f'<span>{html.escape(text)}</span></div>',
        unsafe_allow_html=True,
    )

