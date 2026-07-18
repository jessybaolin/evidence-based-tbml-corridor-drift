"""Future-state wholesale-bank implementation pathway.

This page is conceptual and deliberately has no data-loader dependency beyond
the governed copy. It explains how the current public-data triage outputs could
sit inside a bank workflow without presenting any proposed integration as built.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.banners import render_dataset_strip, render_info_banner
from dashboard.components.icons import render_icon, render_icon_badge
from dashboard.components.page_shell import render_page_header
from dashboard.services.data_loader import load_content

copy = load_content()["pages"]["bank_implementation_pathway"]


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _section_heading(title: str, caption: str | None = None) -> str:
    caption_html = f'<div class="bank-section-caption">{_e(caption)}</div>' if caption else ""
    return (
        '<div class="bank-section-heading">'
        f'<div class="bank-section-title">{_e(title)}</div>{caption_html}</div>'
    )


def _architecture_nodes(nodes: list[dict[str, str]]) -> str:
    rendered = []
    for index, node in enumerate(nodes, start=1):
        rendered.append(
            '<div class="bank-flow-node">'
            f'<span class="bank-node-index">{index}</span>'
            '<div class="bank-node-copy">'
            f'<div class="bank-node-title">{_e(node["title"])}</div>'
            f'<div class="bank-node-detail">{_e(node["detail"])}</div>'
            '</div></div>'
        )
    return '<span class="bank-flow-arrow" aria-hidden="true">&darr;</span>'.join(rendered)


def _icon_cards(items: list[dict[str, str]], class_name: str) -> str:
    cards = []
    for item in items:
        cards.append(
            f'<article class="bank-icon-card {class_name}">'
            f'{render_icon_badge(item["icon"], class_name="bank-card-icon")}'
            '<div class="bank-card-copy">'
            f'<div class="bank-card-title">{_e(item["title"])}</div>'
            f'<div class="bank-card-detail">{_e(item["detail"])}</div>'
            '</div></article>'
        )
    return "".join(cards)


render_page_header(copy["title"], copy["subtitle"], copy["eyebrow"], "hero-block anim")
render_info_banner(
    copy["boundary"]["label"],
    copy["boundary"]["body"],
    icon="shield-check",
    class_name="future-boundary",
)

role = copy["role"]
st.markdown(
    '<section class="landing-section bank-role anim d1">'
    f'{_section_heading(role["heading"])}'
    f'<p class="landing-prose">{_e(role["body"])}</p>'
    f'<p class="landing-prose">{_e(role["body_2"])}</p>'
    '</section>',
    unsafe_allow_html=True,
)

architecture = copy["architecture"]
today = architecture["today"]
future = architecture["future"]
st.markdown(
    '<section class="landing-section anim d2">'
    f'{_section_heading(architecture["heading"], architecture["caption"])}'
    '<div class="bank-architecture" role="figure" '
    f'aria-label="{_e(architecture["heading"])}">'
    '<div class="bank-state bank-state-today">'
    f'<div class="bank-state-kicker">{_e(today["kicker"])}</div>'
    f'<div class="bank-state-title">{_e(today["title"])}</div>'
    f'<div class="bank-flow">{_architecture_nodes(today["nodes"])}</div>'
    '</div>'
    '<div class="bank-bridge" aria-hidden="true">'
    f'{render_icon("line-chart")}<span>{_e(architecture["bridge"])}</span></div>'
    '<div class="bank-state bank-state-future">'
    f'<div class="bank-state-kicker">{_e(future["kicker"])}</div>'
    f'<div class="bank-state-title">{_e(future["title"])}</div>'
    f'<div class="bank-flow">{_architecture_nodes(future["nodes"])}</div>'
    '</div></div>'
    f'<div class="bank-feedback-note">{render_icon("info")}'
    f'<span>{_e(architecture["feedback_note"])}</span></div>'
    '</section>',
    unsafe_allow_html=True,
)

domains = copy["data_domains"]
st.markdown(
    '<section class="landing-section anim d3">'
    f'{_section_heading(domains["heading"], domains["caption"])}'
    f'<div class="bank-domain-grid">{_icon_cards(domains["items"], "domain")}</div>'
    '</section>',
    unsafe_allow_html=True,
)

value = copy["value"]
st.markdown(
    '<section class="landing-section anim d4">'
    f'{_section_heading(value["heading"], value["caption"])}'
    f'<div class="bank-value-grid">{_icon_cards(value["items"], "value")}</div>'
    '</section>',
    unsafe_allow_html=True,
)

adoption = copy["adoption"]
stages = []
for stage in adoption["stages"]:
    stages.append(
        '<article class="bank-stage">'
        f'<div class="bank-stage-number">{_e(stage["number"])}</div>'
        f'<div class="bank-stage-title">{_e(stage["title"])}</div>'
        f'<div class="bank-stage-detail">{_e(stage["detail"])}</div>'
        '</article>'
    )
st.markdown(
    '<section class="landing-section anim d5">'
    f'{_section_heading(adoption["heading"], adoption["caption"])}'
    f'<div class="bank-adoption">{"".join(stages)}</div>'
    '</section>',
    unsafe_allow_html=True,
)

controls = copy["controls"]
control_items = "".join(
    '<div class="bank-control-item">'
    f'{render_icon("shield-check")}<div><div class="bank-control-title">{_e(item["title"])}</div>'
    f'<div class="bank-control-detail">{_e(item["detail"])}</div></div></div>'
    for item in controls["items"]
)
st.markdown(
    '<section class="landing-section anim d6">'
    f'{_section_heading(controls["heading"])}'
    f'<div class="bank-controls">{control_items}</div>'
    '</section>',
    unsafe_allow_html=True,
)

closing = copy["closing"]
chips = "".join(f'<span class="value-chip">{_e(chip)}</span>' for chip in closing["chips"])
st.markdown(
    '<section class="landing-section anim d6">'
    '<div class="bottom-line">'
    f'<div class="bottom-line-text">{_e(closing["statement"])}</div>'
    f'<div class="value-chip-row">{chips}</div>'
    '</div></section>',
    unsafe_allow_html=True,
)
render_dataset_strip(copy["design_basis"])
