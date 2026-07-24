"""Shared card renderers. Callers provide content; the theme owns appearance."""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.icons import render_icon, render_icon_badge

SOURCE_ROLES = frozenset({"official", "benchmark", "typology"})


def kpi_card_markup(
    value: str,
    label_html: str,
    detail: str,
    icon: str,
    *,
    extra_classes: str = "",
) -> str:
    classes = "stat-tile kpi-card" + (f" {extra_classes}" if extra_classes else "")
    return (
        f'<div class="{html.escape(classes, quote=True)}">'
        f'{render_icon_badge(icon, class_name="kpi-icon")}'
        f'<div class="kpi-copy"><div class="stat-value">{html.escape(str(value))}</div>'
        f'<div class="stat-label">{label_html}</div>'
        f'<div class="stat-detail">{html.escape(str(detail))}</div></div></div>'
    )


def render_kpi_card(value: str, label: str, detail: str, icon: str) -> None:
    st.markdown(kpi_card_markup(value, html.escape(label), detail, icon), unsafe_allow_html=True)


def commodity_card_markup(*, title: str, family_id: str, icon: str, info: str,
                          role: str = "", body: str = "") -> str:
    """Compact editorial product-family card for narrative scope panels.

    With `role`/`body`, the card also shows why the family was chosen (the
    selection rationale) as visible text; the physical-commodity description
    stays on the info tooltip either way.
    """
    safe_family = html.escape(family_id.replace("_", "-"), quote=True)
    safe_title = html.escape(title)
    safe_info = html.escape(info, quote=True)
    detail = " commodity-card-detail" if (role or body) else ""
    rationale = ""
    if role or body:
        rationale = (
            f'<div class="commodity-role">{html.escape(role)}</div>'
            f'<div class="commodity-body">{html.escape(body)}</div>'
        )
    return (
        f'<article class="commodity-card family-{safe_family}{detail}" data-tip="{safe_info}">'
        '<div class="commodity-card-head">'
        f'{render_icon_badge(icon, class_name="commodity-icon")}'
        '<div class="commodity-title-row">'
        f'<div class="commodity-title">{safe_title}</div>'
        '<span class="commodity-info tip" tabindex="0" role="note" '
        f'aria-label="About {html.escape(title, quote=True)}" '
        f'data-tip="{safe_info}">{render_icon("info")}</span>'
        '</div></div>'
        f'{rationale}</article>'
    )


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


def fact_list_markup(rows: list[tuple[str, str]]) -> str:
    """Label/value fact rows (Case facts panel). Both cells are HTML fragments:
    callers embed .tip tooltips in labels and status pills in values, so they
    escape their own plain strings (same contract as kpi_card_markup)."""
    body = "".join(
        f'<div class="fact-row"><span class="fact-k">{label_html}</span>'
        f'<span class="fact-v">{value_html}</span></div>'
        for label_html, value_html in rows
    )
    return f'<div class="fact-list">{body}</div>'


def render_fact_list(rows: list[tuple[str, str]]) -> None:
    st.markdown(fact_list_markup(rows), unsafe_allow_html=True)


def comparison_card_markup(*, title: str, value_html: str, support: str,
                           caveat_tip_html: str, secondary_html: str = "",
                           available: bool = True, extra_classes: str = "") -> str:
    """A stakeholder comparison card (Why It Ranked High, 2x2 grid).

    title/support are plain strings (escaped here); value_html, secondary_html
    and caveat_tip_html are pre-built fragments (the caller embeds the info-icon
    .tip and any emphasis). An unavailable card is muted and carries no support.
    extra_classes lets the caller add a per-card accent and entrance-animation.
    """
    klass = "compare-card" if available else "compare-card compare-card-muted"
    if extra_classes:
        klass = f"{klass} {extra_classes}"
    secondary = (
        f'<div class="compare-secondary">{secondary_html}</div>' if secondary_html else ""
    )
    support_html = (
        f'<div class="compare-support">{html.escape(support)}</div>'
        if support and available else ""
    )
    return (
        f'<div class="{klass}">'
        f'<div class="compare-head"><span class="compare-title">{html.escape(title)}</span>'
        f'{caveat_tip_html}</div>'
        f'<div class="compare-value">{value_html}</div>'
        f'{secondary}{support_html}</div>'
    )


def render_chart_card(title: str, caption: str | None = None) -> None:
    caption_html = f'<div class="section-caption">{html.escape(caption)}</div>' if caption else ""
    st.markdown(
        f'<div class="chart-card-heading">{render_icon("line-chart")}'
        f'<div><div class="section-label">{html.escape(title)}</div>{caption_html}</div></div>',
        unsafe_allow_html=True,
    )
