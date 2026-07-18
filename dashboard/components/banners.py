"""Shared information-banner and dataset-strip presentation."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon, render_icon_badge


def render_info_banner(
    label: str,
    body: str,
    *,
    icon: str = "brain",
    class_name: str = "",
) -> None:
    classes = "mental-model" + (f" {class_name}" if class_name else "")
    st.markdown(
        f'<div class="{html.escape(classes, quote=True)}" role="note">'
        f'{render_icon_badge(icon, class_name="banner-icon")}'
        f'<div><span class="mm-stamp">{html.escape(label)}</span>{html.escape(body)}</div></div>',
        unsafe_allow_html=True,
    )


def render_dataset_strip(text: str) -> None:
    st.markdown(
        f'<div class="ledger dataset-strip">{render_icon("file-text")}'
        f'<span>{html.escape(text)}</span></div>',
        unsafe_allow_html=True,
    )
