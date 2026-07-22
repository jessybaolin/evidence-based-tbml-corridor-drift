"""Future-state wholesale-bank implementation pathway.

This page is conceptual and deliberately has no data-loader dependency beyond
the governed copy and one committed screenshot. It explains how the current
public-data triage outputs could sit inside a bank workflow without presenting
any proposed integration as built. The AI evidence-assistant panel is an
explicitly labelled concept mockup — no model runs here.
"""

from __future__ import annotations

import base64
import html

import streamlit as st

from dashboard.components.banners import render_dataset_strip, render_info_banner
from dashboard.components.icons import render_icon, render_icon_badge
from dashboard.components.page_shell import render_page_header
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.services.data_loader import load_content
from dashboard.services.path_resolver import DATA_OUTPUTS

copy = load_content()["pages"]["bank_implementation_pathway"]

# Verdict label -> (badge modifier class, icon) for the evidence-assistant mockup.
_VERDICT = {
    "Match": ("v-match", "check"),
    "Conflict": ("v-conflict", "x"),
    "Gap": ("v-gap", "minus"),
    "Review": ("v-review", "alert-triangle"),
}


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


@st.cache_data(show_spinner=False)
def _screenshot_uri() -> str:
    """Return the Top-50 queue hero screenshot as an inline data URI.

    The image is a committed project output; encoding it inline keeps the
    browser-frame chrome in one HTML block (Streamlit cannot wrap st.image in
    custom markup). Cached so the base64 is computed once per session.
    """
    path = DATA_OUTPUTS / "top_50_review_queue_hero.png"
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _section_heading(title: str, caption: str | None = None) -> str:
    caption_html = (
        f'<div class="bank-section-caption">{_e(caption)}</div>' if caption else ""
    )
    return (
        '<div class="bank-section-heading">'
        f'<div class="bank-section-title">{_e(title)}</div>'
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


def _product_frame(product: dict) -> str:
    """The Top-50 Review Queue shown inside a browser-window frame."""
    bar = (
        '<div class="bank-browser-bar">'
        '<span class="bank-browser-dot d1"></span>'
        '<span class="bank-browser-dot d2"></span>'
        '<span class="bank-browser-dot d3"></span>'
        '<div class="bank-browser-omni">'
        f'{render_icon("shield-check")}<span>{_e(product["url"])}</span></div>'
        '</div>'
    )
    uri = _screenshot_uri()
    if uri:
        shot = (
            '<div class="bank-browser-shot">'
            f'<img src="{uri}" alt="{_e(product["alt"])}" loading="lazy">'
            '<div class="bank-browser-fade" aria-hidden="true"></div>'
            f'<div class="bank-browser-caption">{_e(product["caption"])}</div>'
            '</div>'
        )
    else:  # Defensive: the screenshot is a committed output, so this is unused.
        shot = f'<div class="bank-mock-note">{_e(product["caption"])}</div>'
    return f'<div class="bank-browser">{bar}{shot}</div>'


def _mockup(mockup: dict) -> str:
    """The concept mockup: a flagged case beside a record-linking AI assistant."""
    case = mockup["case"]
    assistant = mockup["assistant"]
    linked = mockup["linked"]

    metrics = "".join(
        f'<div class="bank-mock-metric{" alert" if row.get("tone") == "alert" else ""}">'
        f'<span class="bank-mock-metric-label">{_e(row["label"])}</span>'
        f'<span class="bank-mock-metric-value">{_e(row["value"])}</span></div>'
        for row in case["rows"]
    )
    case_html = (
        '<div class="bank-mock-case">'
        f'<div class="bank-mock-kicker">{_e(case["kicker"])}</div>'
        '<div class="bank-mock-route">'
        f'<span class="bank-mock-route-name">{_e(case["route"])}</span>'
        f'<span class="bank-mock-tag">{_e(case["tag"])}</span></div>'
        '<div class="bank-mock-score">'
        f'<span class="bank-mock-score-value">{_e(case["score"])}</span>'
        f'<span class="bank-mock-score-label">{_e(case["score_label"])}</span></div>'
        f'<div class="bank-mock-metrics">{metrics}</div>'
        '</div>'
    )

    records = []
    for record in assistant["records"]:
        cls, icon = _VERDICT.get(record["verdict"], ("v-gap", "minus"))
        records.append(
            '<div class="bank-mock-record">'
            f'<span class="bank-mock-verdict {cls}">{render_icon(icon)}{_e(record["verdict"])}</span>'
            f'<span class="bank-mock-record-text">{_e(record["text"])}</span>'
            f'<span class="bank-mock-record-src">{_e(record["source"])} ↗</span>'
            '</div>'
        )
    chips = "".join(
        f'<span class="bank-mock-chip {"ok" if index == 0 else "warn"}">{_e(chip)}</span>'
        for index, chip in enumerate(assistant["answer_chips"])
    )
    assistant_html = (
        '<div class="bank-mock-assist">'
        '<div class="bank-mock-assist-head"><div class="bank-mock-assist-id">'
        f'<span class="bank-mock-assist-avatar">{render_icon("sparkles")}</span>'
        f'<div><div class="bank-mock-assist-name">{_e(assistant["name"])}</div>'
        f'<div class="bank-mock-assist-sub">{_e(assistant["tagline"])}</div></div></div>'
        f'<span class="bank-mock-badge">{render_icon("sparkles")}{_e(assistant["badge"])}</span>'
        '</div>'
        f'<div class="bank-mock-subhead">{_e(assistant["records_heading"])}</div>'
        f'<div class="bank-mock-records">{"".join(records)}</div>'
        f'<div class="bank-mock-subhead">{_e(assistant["ask_heading"])}</div>'
        '<div class="bank-mock-chat">'
        f'<div class="bank-mock-q">{_e(assistant["question"])}</div>'
        '<div class="bank-mock-a">'
        f'<span class="bank-mock-a-avatar">{render_icon("sparkles")}</span>'
        '<div class="bank-mock-a-bubble">'
        f'<div class="bank-mock-a-chips">{chips}</div>'
        f'<div class="bank-mock-a-text">{_e(assistant["answer"])}</div>'
        f'<div class="bank-mock-a-src">{_e(assistant["answer_source"])}</div>'
        '</div></div></div>'
        '<div class="bank-mock-input">'
        f'<span>{_e(assistant["input_placeholder"])}</span>'
        f'<span class="bank-mock-send">{render_icon("arrow-right")}</span></div>'
        f'<div class="bank-mock-note">{_e(assistant["note"])}</div>'
        '</div>'
    )

    files = []
    for index, item in enumerate(linked["items"], start=1):
        files.append(
            f'<div class="bank-mock-file bank-mock-file-{index}">'
            '<div class="bank-mock-file-top">'
            f'<span class="bank-mock-file-icon">{render_icon(item["icon"])}</span>'
            f'{render_icon("chevron-right")}</div>'
            f'<div class="bank-mock-file-title">{_e(item["title"])}</div>'
            f'<div class="bank-mock-file-meta">{_e(item["meta"])}</div>'
            '</div>'
        )
    linked_html = (
        '<div class="bank-mock-linked">'
        '<div class="bank-mock-linked-head">'
        f'<span class="bank-mock-linked-title">{_e(linked["heading"])}</span>'
        f'<span class="bank-mock-linked-badge">{_e(linked["badge"])}</span></div>'
        f'<div class="bank-mock-linked-caption">{_e(linked["caption"])}</div>'
        f'<div class="bank-mock-files">{"".join(files)}</div>'
        '<div class="bank-mock-foot">'
        f'{render_icon("shield-check")}<span>{_e(linked["footnote"])}</span></div>'
        '</div>'
    )

    return (
        '<div class="bank-mock-head">'
        f'<span class="bank-mock-head-title">{_e(mockup["title"])}</span>'
        f'<span class="bank-mock-badge">{render_icon("sparkles")}{_e(mockup["badge"])}</span>'
        '</div>'
        '<div class="bank-mock">'
        '<div class="bank-mock-chrome">'
        '<span class="bank-browser-dot d1"></span>'
        '<span class="bank-browser-dot d2"></span>'
        '<span class="bank-browser-dot d3"></span>'
        f'<span class="bank-mock-chrome-label">{_e(mockup["chrome"])}</span></div>'
        f'<div class="bank-mock-body">{case_html}{assistant_html}</div>'
        f'{linked_html}'
        '</div>'
    )


def _value_band(items: list[dict[str, str]]) -> str:
    cells = []
    for index, item in enumerate(items, start=1):
        cells.append(
            f'<div class="bank-band-cell bank-band-cell-{index}">'
            f'<div class="bank-band-num">{index:02d}</div>'
            f'{render_icon_badge(item["icon"], class_name="bank-band-icon")}'
            f'<div class="bank-band-title">{_e(item["title"])}</div>'
            f'<div class="bank-band-detail">{_e(item["detail"])}</div>'
            '</div>'
        )
    return f'<div class="bank-value-band">{"".join(cells)}</div>'


# ---- Render ----------------------------------------------------------------

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
# Page marker: scopes the generous inter-section spacing (matching Business
# Problem & Value) to this page only.
st.markdown('<span class="bank-page-marker" aria-hidden="true"></span>',
            unsafe_allow_html=True)

# 1. Where the prototype could fit — public signal to human decision, then the
#    today -> future operating model.
fit = copy["fit"]
today = fit["today"]
future = fit["future"]
st.markdown(
    '<section class="landing-section reveal">'
    f'{_section_heading(fit["heading"], fit["caption"])}'
    f'<div class="bank-fit-rail">{_fit_steps(fit["steps"])}</div>'
    '<div class="bank-architecture" role="figure" '
    f'aria-label="{_e(fit["heading"])}">'
    '<div class="bank-state bank-state-today">'
    f'<div class="bank-state-kicker">{_e(today["kicker"])}</div>'
    f'<div class="bank-state-title">{_e(today["title"])}</div>'
    f'<div class="bank-flow">{_architecture_nodes(today["nodes"])}</div>'
    '</div>'
    '<div class="bank-bridge" aria-hidden="true">'
    f'{render_icon("line-chart")}<span>{_e(fit["bridge"])}</span></div>'
    '<div class="bank-state bank-state-future">'
    f'<div class="bank-state-kicker">{_e(future["kicker"])}</div>'
    f'<div class="bank-state-title">{_e(future["title"])}</div>'
    f'<div class="bank-flow">{_architecture_nodes(future["nodes"])}</div>'
    '</div></div>'
    '</section>',
    unsafe_allow_html=True,
)

# 2. The product — the live Top 50 Review Queue in a browser frame.
product = copy["product"]
st.markdown(
    '<section class="landing-section reveal">'
    '<div class="bank-product-head">'
    f'<div class="bank-product-kicker">{_e(product["kicker"])}</div>'
    f'<div class="bank-product-title">{_e(product["title"])}</div>'
    '</div>'
    f'{_product_frame(product)}'
    '</section>',
    unsafe_allow_html=True,
)

# 3. What bank records add — the varied domain grid.
domains = copy["data_domains"]
st.markdown(
    '<section class="landing-section reveal">'
    f'{_section_heading(domains["heading"], domains["caption"])}'
    f'<div class="bank-domain-grid">{_icon_cards(domains["items"], "domain")}</div>'
    '</section>',
    unsafe_allow_html=True,
)

# 4. Where AI could help — governed value statement, the record-linking flow, a
#    labelled concept mockup, then what the analyst receives and the hard rules.
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
    f'{_mockup(ai["mockup"])}'
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

# 5. How this could help a wholesale-banking AFC team — numbered value band.
value = copy["value"]
st.markdown(
    '<section class="landing-section reveal">'
    f'{_section_heading(value["heading"])}'
    f'{_value_band(value["items"])}'
    '</section>',
    unsafe_allow_html=True,
)

# 6. Closing statement.
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

# Reveal each pathway section as it scrolls into view.
render_scroll_reveal(".reveal")
