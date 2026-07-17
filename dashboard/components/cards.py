"""Shared card renderers. Callers provide content; the theme owns appearance."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon, render_icon_badge

SOURCE_ROLES = frozenset({"official", "benchmark", "typology"})


def kpi_card_markup(value: str, label_html: str, detail: str, icon: str) -> str:
    return (
        f'<div class="stat-tile kpi-card">{render_icon_badge(icon, class_name="kpi-icon")}'
        f'<div class="kpi-copy"><div class="stat-value">{html.escape(str(value))}</div>'
        f'<div class="stat-label">{label_html}</div>'
        f'<div class="stat-detail">{html.escape(str(detail))}</div></div></div>'
    )


def render_kpi_card(value: str, label: str, detail: str, icon: str) -> None:
    st.markdown(kpi_card_markup(value, html.escape(label), detail, icon), unsafe_allow_html=True)


def source_card_markup(*, role: str, icon: str, eyebrow: str, title: str,
                       sections_html: str, footer_html: str = "",
                       extra_classes: str = "", tabindex: bool = False) -> str:
    if role not in SOURCE_ROLES:
        raise ValueError(f"Unknown source role: {role}")
    tab = ' tabindex="0"' if tabindex else ""
    classes = f"src-card source-role-{role} {extra_classes}".strip()
    return (
        f'<div class="{html.escape(classes, quote=True)}"{tab}>'
        f'<div class="source-card-head">{render_icon_badge(icon, class_name="source-icon")}'
        f'<div><div class="src-kicker">{html.escape(eyebrow)}</div>'
        f'<div class="src-name">{html.escape(title)}</div></div></div>'
        f'{sections_html}{footer_html}</div>'
    )


def render_source_card(**kwargs) -> None:
    st.markdown(source_card_markup(**kwargs), unsafe_allow_html=True)


def render_chart_card(title: str, caption: str | None = None) -> None:
    caption_html = f'<div class="section-caption">{html.escape(caption)}</div>' if caption else ""
    st.markdown(
        f'<div class="chart-card-heading">{render_icon("line-chart")}'
        f'<div><div class="section-label">{html.escape(title)}</div>{caption_html}</div></div>',
        unsafe_allow_html=True,
    )

