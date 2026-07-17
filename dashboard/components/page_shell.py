"""Canonical page-shell interfaces; compatibility wrappers live in page_header."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon


def render_page_header(title: str, subtitle: str, eyebrow: str = "Stakeholder analytics",
                       class_name: str = "") -> None:
    classes = "page-header" + (f" {class_name}" if class_name else "")
    st.markdown(
        f'<header class="{html.escape(classes, quote=True)}">'
        f'<div class="page-eyebrow">{html.escape(eyebrow)}</div>'
        f'<h1 class="page-title">{html.escape(title)}</h1>'
        f'<div class="page-subtitle">{html.escape(subtitle)}</div>'
        f'</header>',
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, caption: str | None = None,
                           icon: str = "layers") -> None:
    caption_html = (
        f'<div class="section-caption">{html.escape(caption)}</div>' if caption else ""
    )
    st.markdown(
        f'<div class="section-heading">{render_icon(icon, class_name="section-icon")}'
        f'<div><div class="section-label">{html.escape(title)}</div>{caption_html}</div></div>',
        unsafe_allow_html=True,
    )
