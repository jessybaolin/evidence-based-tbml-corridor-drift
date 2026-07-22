"""Canonical page-shell interfaces; compatibility wrappers live in page_header."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon


def render_page_header(title: str, subtitle: str, eyebrow: str = "Stakeholder analytics",
                       class_name: str = "", icon: str | None = None) -> None:
    classes = "page-header" + (f" {class_name}" if class_name else "")
    eyebrow_html = (
        f'<div class="page-eyebrow">{html.escape(eyebrow)}</div>' if eyebrow else ""
    )
    subtitle_html = (
        f'<div class="page-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    )
    icon_html = render_icon(icon, class_name="page-title-icon") if icon else ""
    st.markdown(
        f'<header class="{html.escape(classes, quote=True)}">'
        f'{eyebrow_html}'
        f'<h1 class="page-title">{icon_html}{html.escape(title)}</h1>'
        f'{subtitle_html}'
        f'</header>',
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, caption: str | None = None,
                           icon: str = "layers", info: str | None = None) -> None:
    caption_html = (
        f'<div class="section-caption">{html.escape(caption)}</div>' if caption else ""
    )
    # Optional hover/focus tooltip beside the title (the shared .tip mechanism).
    info_html = (
        '<span class="section-info tip" tabindex="0" role="note" '
        f'aria-label="More information about {html.escape(title, quote=True)}" '
        f'data-tip="{html.escape(info, quote=True)}">{render_icon("info")}</span>'
        if info else ""
    )
    st.markdown(
        f'<div class="section-heading">{render_icon(icon, class_name="section-icon")}'
        f'<div><div class="section-label">{html.escape(title)}{info_html}</div>'
        f'{caption_html}</div></div>',
        unsafe_allow_html=True,
    )


def story_section_heading_markup(title: str) -> str:
    """Full-width divider heading for narrative stakeholder pages."""
    return (
        '<div class="story-section-header">'
        f'<div class="story-section-title">{html.escape(title)}</div>'
        '<div class="story-section-rule" aria-hidden="true"></div></div>'
    )
