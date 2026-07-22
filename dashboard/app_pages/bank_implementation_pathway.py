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
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.services.data_loader import load_content

copy = load_content()["pages"]["bank_implementation_pathway"]


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _section_heading(
    title: str,
    caption: str | None = None,
    info: str | None = None,
) -> str:
    caption_html = f'<div class="bank-section-caption">{_e(caption)}</div>' if caption else ""
    info_html = (
        '<span class="bank-section-info tip" tabindex="0" role="note" '
        f'aria-label="More information about {_e(title)}" data-tip="{_e(info)}">'
        f'{render_icon("info")}</span>'
        if info else ""
    )
    return (
        '<div class="bank-section-heading">'
        f'<div class="bank-section-title">{_e(title)}{info_html}</div>'
        f'{caption_html}</div>'
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
    for index, item in enumerate(items, start=1):
        cards.append(
            f'<article class="bank-icon-card {class_name} bank-card-{index}">'
            f'{render_icon_badge(item["icon"], class_name="bank-card-icon")}'
            '<div class="bank-card-copy">'
            f'<div class="bank-card-title">{_e(item["title"])}</div>'
            f'<div class="bank-card-detail">{_e(item["detail"])}</div>'
            '</div></article>'
        )
    return "".join(cards)


def _fit_steps(items: list[dict[str, str]]) -> str:
    steps = []
    for index, item in enumerate(items, start=1):
        steps.append(
            f'<article class="bank-fit-step bank-fit-step-{index}">'
            f'{render_icon_badge(item["icon"], class_name="bank-fit-icon")}'
            '<div class="bank-fit-copy">'
            f'<div class="bank-fit-label">{_e(item["label"])}</div>'
            f'<div class="bank-fit-question">{_e(item["question"])}</div>'
            '</div></article>'
        )
    return "".join(steps)


def _ai_steps(items: list[dict[str, str]]) -> str:
    steps = []
    for index, item in enumerate(items, start=1):
        if index > 1:
            steps.append('<span class="bank-ai-arrow" aria-hidden="true">&rarr;</span>')
        steps.append(
            f'<article class="bank-ai-step bank-ai-step-{index}">'
            f'{render_icon_badge(item["icon"], class_name="bank-ai-icon")}'
            '<div class="bank-ai-copy">'
            f'<div class="bank-ai-kicker">{_e(item["kicker"])}</div>'
            f'<div class="bank-ai-title">{_e(item["title"])}</div>'
            f'<div class="bank-ai-detail">{_e(item["detail"])}</div>'
            '</div></article>'
        )
    return "".join(steps)


def _ai_outputs(items: list[dict[str, str]]) -> str:
    outputs = []
    for index, item in enumerate(items, start=1):
        outputs.append(
            f'<article class="bank-ai-output bank-ai-output-{index}">'
            f'{render_icon_badge(item["icon"], class_name="bank-ai-output-icon")}'
            '<div class="bank-ai-output-copy">'
            f'<div class="bank-ai-output-title">{_e(item["title"])}</div>'
            f'<div class="bank-ai-output-detail">{_e(item["detail"])}</div>'
            '</div></article>'
        )
    return "".join(outputs)


render_page_header(
    copy["title"],
    copy["subtitle"],
    copy["eyebrow"],
    "hero-block bank-pathway-hero anim",
)
render_info_banner(
    copy["boundary"]["label"],
    copy["boundary"]["body"],
    icon="shield-check",
    class_name="future-boundary",
)

role = copy["role"]
st.markdown(
    '<section class="landing-section bank-role bank-reveal">'
    f'{_section_heading(role["heading"], info=role["info"])}'
    f'<div class="bank-fit-rail">{_fit_steps(role["steps"])}</div>'
    '</section>',
    unsafe_allow_html=True,
)

architecture = copy["architecture"]
today = architecture["today"]
future = architecture["future"]
st.markdown(
    '<section class="landing-section reveal">'
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
    '<section class="landing-section reveal">'
    f'{_section_heading(domains["heading"], domains["caption"])}'
    f'<div class="bank-domain-grid">{_icon_cards(domains["items"], "domain")}</div>'
    '</section>',
    unsafe_allow_html=True,
)

value = copy["value"]
st.markdown(
    '<section class="landing-section reveal">'
    f'{_section_heading(value["heading"], value["caption"])}'
    f'<div class="bank-value-grid">{_icon_cards(value["items"], "value")}</div>'
    '</section>',
    unsafe_allow_html=True,
)

ai = copy["ai_extension"]
outputs = _ai_outputs(ai["outputs"])
guardrails = "".join(
    f'<span class="bank-ai-guardrail">{render_icon("shield-check")}{_e(item)}</span>'
    for item in ai["guardrails"]
)
st.markdown(
    '<section class="landing-section reveal">'
    f'{_section_heading(ai["heading"], ai["caption"])}'
    '<div class="bank-ai-shell">'
    f'<div class="bank-ai-value">{render_icon("brain")}<span>{_e(ai["value_statement"])}</span></div>'
    f'<div class="bank-ai-flow">{_ai_steps(ai["steps"])}</div>'
    '<div class="bank-ai-support">'
    '<div class="bank-ai-outputs">'
    f'<div class="bank-ai-support-title">{_e(ai["outputs_heading"])}</div>'
    f'<div class="bank-ai-output-grid">{outputs}</div></div>'
    '<div class="bank-ai-guardrails">'
    f'<div class="bank-ai-support-title">{_e(ai["guardrail_heading"])}</div>'
    f'<div class="bank-ai-guardrail-grid">{guardrails}</div>'
    '</div></div></div></section>',
    unsafe_allow_html=True,
)

closing = copy["closing"]
chips = "".join(f'<span class="value-chip">{_e(chip)}</span>' for chip in closing["chips"])
st.markdown(
    '<section class="landing-section reveal bank-closing">'
    '<div class="bottom-line">'
    f'<div class="bottom-line-text">{_e(closing["statement"])}</div>'
    f'<div class="value-chip-row">{chips}</div>'
    '</div></section>',
    unsafe_allow_html=True,
)
render_dataset_strip(copy["design_basis"])

# Reveal each pathway section as it scrolls into view (replaces the old
# scroll-scrubbed .bank-reveal; that CSS is now inert).
render_scroll_reveal(".reveal")
