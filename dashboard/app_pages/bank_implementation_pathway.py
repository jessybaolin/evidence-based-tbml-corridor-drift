"""Future-state wholesale-bank implementation pathway.

A scrolling product-showcase page that closes the project. It is conceptual and
has no data-loader dependency beyond the governed copy and one committed
screenshot; it explains how the current public-data triage outputs could sit
inside a bank workflow without presenting any proposed integration as built. The
AI evidence-assistant panel is an explicitly labelled concept mockup — no model
runs here. Every visible string comes from content.yml; this module owns only
layout + the decorative (currentColor) inline SVGs styled by
styles.apply_global_styles().
"""

from __future__ import annotations

import base64
import html

import streamlit as st

from dashboard.components.icons import render_icon
from dashboard.components.page_shell import render_page_header
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.services.data_loader import load_content
from dashboard.services.path_resolver import DATA_OUTPUTS

copy = load_content()["pages"]["bank_implementation_pathway"]

# Journey / AI-story accent classes, in section order.
_JOURNEY_ACCENTS = ("acc-blue", "acc-amber", "acc-teal")
_AI_ACCENTS = ("acc-blue", "acc-violet", "acc-amber")
# Verdict label -> (badge modifier class, icon) for the evidence-assistant mockup.
_VERDICT = {
    "Match": ("v-match", "check"),
    "Conflict": ("v-conflict", "x"),
    "Gap": ("v-gap", "minus"),
    "Review": ("v-review", "alert-triangle"),
}
# Records-grid render order + cell classes (Beneficial ownership leads, full
# width). Content order is [KYC, Trade, Shipment, Payments, Sanctions, Benef.].
_REC_ORDER = (
    (5, "wide center bip-rec-lead"),
    (0, "wide bip-rec-kyc"),
    (1, "wide bip-rec-trade"),
    (2, "tall bip-rec-ship"),
    (3, "tall bip-rec-pay"),
    (4, "tall bip-rec-sanc"),
)
# Icons for the four "rules the AI would follow" chips (content has text only).
_RULE_ICONS = ("shield-check", "link", "info", "checklist")


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


@st.cache_data(show_spinner=False)
def _screenshot_uri() -> str:
    """The Top-50 queue screenshot as an inline data URI for the product frame.

    A committed project output; inlining keeps the browser chrome in one CSS
    block. Cached so the base64 is computed once per session.
    """
    path = DATA_OUTPUTS / "top_50_review_queue_hero.png"
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _heading(title: str, lead: str | None = None, rule_class: str = "") -> str:
    rule = f'<div class="bip-rule {rule_class}"></div>' if rule_class else '<div class="bip-rule"></div>'
    lead_html = f'<p class="bip-lead">{_e(lead)}</p>' if lead else ""
    return f'{rule}<h2 class="bip-h2">{_e(title)}</h2>{lead_html}'


def _journey_flow(steps: list[dict[str, str]]) -> str:
    parts = []
    for index, step in enumerate(steps):
        if index:
            parts.append(
                f'<div class="bip-arrow" aria-hidden="true">{render_icon("arrow-right")}</div>'
            )
        parts.append(
            f'<div class="bip-stage {_JOURNEY_ACCENTS[index]}">'
            f'<span class="bip-node">{render_icon(step["icon"])}</span>'
            f'<div class="bip-stage-kicker">{_e(step["label"])}</div>'
            f'<div class="bip-stage-q">{_e(step["question"])}</div>'
            '</div>'
        )
    return f'<div class="bip-flow">{"".join(parts)}</div>'


def _ai_flow(steps: list[dict[str, str]]) -> str:
    parts = []
    for index, step in enumerate(steps):
        if index:
            parts.append(
                f'<div class="bip-arrow" aria-hidden="true">{render_icon("arrow-right")}</div>'
            )
        parts.append(
            f'<div class="bip-stage {_AI_ACCENTS[index]}">'
            f'<span class="bip-node">{render_icon(step["icon"])}</span>'
            f'<div class="bip-stage-kicker">{_e(step["kicker"])}</div>'
            f'<div class="bip-stage-h">{_e(step["title"])}</div>'
            f'<div class="bip-stage-d">{_e(step["detail"])}</div>'
            '</div>'
        )
    return f'<div class="bip-flow">{"".join(parts)}</div>'


def _tf_steps(nodes: list[dict[str, str]]) -> str:
    steps = []
    for index, node in enumerate(nodes, start=1):
        steps.append(
            '<div class="bip-tf-step">'
            f'<span class="bip-tf-num">{index}</span>'
            '<div>'
            f'<div class="bip-tf-step-title">{_e(node["title"])}</div>'
            f'<div class="bip-tf-step-detail">{_e(node["detail"])}</div>'
            '</div></div>'
        )
    return "".join(steps)


def _today_future(today: dict, future: dict, bridge: str) -> str:
    return (
        '<div class="bip-tf">'
        '<div class="bip-tf-col bip-tf-today">'
        f'<div class="bip-tf-kicker">{_e(today["kicker"])}</div>'
        f'<div class="bip-tf-title">{_e(today["title"])}</div>'
        f'<div class="bip-tf-steps">{_tf_steps(today["nodes"])}</div>'
        '</div>'
        '<div class="bip-tf-connector" aria-hidden="true">'
        f'<span class="bip-tf-connector-node">{render_icon("line-chart")}</span>'
        f'<div class="bip-tf-connector-label">{_e(bridge)}</div>'
        '</div>'
        '<div class="bip-tf-col bip-tf-future">'
        f'<div class="bip-tf-kicker">{_e(future["kicker"])}</div>'
        f'<div class="bip-tf-title">{_e(future["title"])}</div>'
        f'<div class="bip-tf-steps">{_tf_steps(future["nodes"])}</div>'
        '</div></div>'
    )


def _product_frame(product: dict) -> str:
    chrome = (
        '<div class="bip-frame-chrome">'
        '<span class="bip-tl r"></span><span class="bip-tl y"></span>'
        '<span class="bip-tl g"></span>'
        '<div class="bip-omni">'
        f'{render_icon("shield-check")}<span>{_e(product["url"])}</span></div>'
        '</div>'
    )
    uri = _screenshot_uri()
    screen = (
        '<div class="bip-frame-screen">'
        f'<img src="{uri}" alt="{_e(product["alt"])}" loading="lazy">'
        '<div class="bip-scan" aria-hidden="true"></div>'
        '<div class="bip-frame-fade" aria-hidden="true"></div>'
        f'<div class="bip-frame-caption">{_e(product["caption"])}</div>'
        '</div>'
    ) if uri else f'<div class="bip-frame-caption">{_e(product["caption"])}</div>'
    return f'<div class="bip-frame">{chrome}{screen}</div>'


def _records(items: list[dict[str, str]]) -> str:
    cards = []
    for item_index, cell_class in _REC_ORDER:
        item = items[item_index]
        cards.append(
            f'<div class="bip-rec {cell_class}">'
            f'<span class="bip-rec-tile">{render_icon(item["icon"])}</span>'
            '<div>'
            f'<div class="bip-rec-title">{_e(item["title"])}</div>'
            f'<div class="bip-rec-body">{_e(item["detail"])}</div>'
            '</div></div>'
        )
    return f'<div class="bip-records">{"".join(cards)}</div>'


def _mockup(mockup: dict) -> str:
    case = mockup["case"]
    assistant = mockup["assistant"]
    linked = mockup["linked"]

    metrics = "".join(
        f'<div class="bip-mock-metric{" alert" if row.get("tone") == "alert" else ""}">'
        f'<span class="bip-mock-metric-label">{_e(row["label"])}</span>'
        f'<span class="bip-mock-metric-value">{_e(row["value"])}</span></div>'
        for row in case["rows"]
    )
    case_html = (
        '<div class="bip-mock-case">'
        f'<div class="bip-mock-kicker">{_e(case["kicker"])}</div>'
        '<div class="bip-mock-route">'
        f'<span class="bip-mock-route-name">{_e(case["route"])}</span>'
        f'<span class="bip-mock-tag">{_e(case["tag"])}</span></div>'
        '<div class="bip-mock-score">'
        f'<span class="bip-mock-score-value">{_e(case["score"])}</span>'
        f'<span class="bip-mock-score-label">{_e(case["score_label"])}</span></div>'
        f'<div class="bip-mock-metrics">{metrics}</div>'
        '</div>'
    )

    records = []
    for record in assistant["records"]:
        cls, icon = _VERDICT.get(record["verdict"], ("v-gap", "minus"))
        records.append(
            '<div class="bip-mock-record">'
            f'<span class="bip-mock-verdict {cls}">{render_icon(icon)}{_e(record["verdict"])}</span>'
            f'<span class="bip-mock-record-text">{_e(record["text"])}</span>'
            f'<span class="bip-mock-record-src">{_e(record["source"])} ↗</span>'
            '</div>'
        )
    chips = "".join(
        f'<span class="bip-mock-chip {"ok" if index == 0 else "warn"}">{_e(chip)}</span>'
        for index, chip in enumerate(assistant["answer_chips"])
    )
    assist_html = (
        '<div class="bip-mock-assist">'
        '<div class="bip-mock-assist-head"><div class="bip-mock-assist-id">'
        f'<span class="bip-mock-avatar">{render_icon("sparkles")}</span>'
        f'<div><div class="bip-mock-assist-name">{_e(assistant["name"])}</div>'
        f'<div class="bip-mock-assist-sub">{_e(assistant["tagline"])}</div></div></div>'
        f'<span class="bip-mock-ai-pill">{render_icon("sparkles")}{_e(assistant["badge"])}</span>'
        '</div>'
        f'<div class="bip-mock-subhead">{_e(assistant["records_heading"])}</div>'
        f'<div class="bip-mock-records">{"".join(records)}</div>'
        f'<div class="bip-mock-subhead">{_e(assistant["ask_heading"])}</div>'
        '<div class="bip-mock-chat">'
        f'<div class="bip-mock-q">{_e(assistant["question"])}</div>'
        '<div class="bip-mock-a">'
        f'<span class="bip-mock-a-avatar">{render_icon("sparkles")}</span>'
        '<div class="bip-mock-a-bubble">'
        f'<div class="bip-mock-a-chips">{chips}</div>'
        f'<div class="bip-mock-a-text">{_e(assistant["answer"])}</div>'
        f'<div class="bip-mock-a-src">{_e(assistant["answer_source"])}</div>'
        '</div></div></div>'
        '<div class="bip-mock-input">'
        f'<span>{_e(assistant["input_placeholder"])}</span>'
        f'<span class="bip-mock-send">{render_icon("arrow-right")}</span></div>'
        f'<div class="bip-mock-note">{_e(assistant["note"])}</div>'
        '</div>'
    )

    files = []
    for index, item in enumerate(linked["items"], start=1):
        files.append(
            f'<div class="bip-mock-file bip-mock-file-{index}">'
            '<div class="bip-mock-file-top">'
            f'<span class="bip-mock-file-tile">{render_icon(item["icon"])}</span>'
            f'<span class="bip-mock-file-chev">{render_icon("chevron-right")}</span></div>'
            f'<div class="bip-mock-file-title">{_e(item["title"])}</div>'
            f'<div class="bip-mock-file-meta">{_e(item["meta"])}</div>'
            '</div>'
        )
    linked_html = (
        '<div class="bip-mock-linked">'
        '<div class="bip-mock-linked-head">'
        f'<span class="bip-mock-linked-title">{_e(linked["heading"])}</span>'
        f'<span class="bip-mock-linked-badge">{_e(linked["badge"])}</span></div>'
        f'<div class="bip-mock-linked-caption">{_e(linked["caption"])}</div>'
        f'<div class="bip-mock-files">{"".join(files)}</div>'
        '<div class="bip-mock-foot">'
        f'{render_icon("shield-check")}<span>{_e(linked["footnote"])}</span></div>'
        '</div>'
    )

    return (
        '<div class="bip-mock-head">'
        f'<span class="bip-mock-head-title">{_e(mockup["title"])}</span>'
        f'<span class="bip-mock-badge">{render_icon("sparkles")}{_e(mockup["badge"])}</span>'
        '</div>'
        '<div class="bip-mock">'
        '<div class="bip-mock-chrome">'
        '<span class="bip-mock-tl r"></span><span class="bip-mock-tl y"></span>'
        '<span class="bip-mock-tl g"></span>'
        f'<span class="bip-mock-chrome-label">{_e(mockup["chrome"])}</span></div>'
        f'<div class="bip-mock-body">{case_html}{assist_html}</div>'
        f'{linked_html}'
        '</div>'
    )


def _outputs(items: list[dict[str, str]]) -> str:
    cells = []
    for index, item in enumerate(items, start=1):
        cells.append(
            f'<div class="bip-output bip-output-{index}">'
            f'<span class="bip-output-icon">{render_icon(item["icon"])}</span>'
            '<div>'
            f'<div class="bip-output-title">{_e(item["title"])}</div>'
            f'<div class="bip-output-detail">{_e(item["detail"])}</div>'
            '</div></div>'
        )
    return f'<div class="bip-outputs">{"".join(cells)}</div>'


def _rules(guardrails: list[str]) -> str:
    chips = []
    for index, text in enumerate(guardrails):
        icon = _RULE_ICONS[index] if index < len(_RULE_ICONS) else "shield-check"
        chips.append(f'<span class="bip-chip">{render_icon(icon)}{_e(text)}</span>')
    return f'<div class="bip-rules">{"".join(chips)}</div>'


def _value_band(items: list[dict[str, str]]) -> str:
    cells = []
    for index, item in enumerate(items, start=1):
        cells.append(
            f'<div class="bip-value-cell bip-value-cell-{index}">'
            f'<div class="bip-value-num">{index:02d}</div>'
            f'<span class="bip-value-tile">{render_icon(item["icon"])}</span>'
            f'<div class="bip-value-title">{_e(item["title"])}</div>'
            f'<div class="bip-value-detail">{_e(item["detail"])}</div>'
            '</div>'
        )
    return f'<div class="bip-value-band">{"".join(cells)}</div>'


def _closing(closing: dict) -> str:
    chips = "".join(
        f'<span class="bip-closing-chip{" final" if index == len(closing["chips"]) - 1 else ""}">'
        f'{_e(chip)}</span>'
        for index, chip in enumerate(closing["chips"])
    )
    return (
        '<div class="bip-closing-panel">'
        f'<p class="bip-closing-text">{_e(closing["statement"])}</p>'
        f'<div class="bip-closing-chips">{chips}</div>'
        '</div>'
    )


# ---- Render ----------------------------------------------------------------

render_page_header(
    copy["title"],
    copy["subtitle"],
    copy["eyebrow"],
    "hero-block bank-pathway-hero anim",
)

# Future-state boundary banner (fixed wording; label stacked over the sentence).
st.markdown(
    '<div class="bip-boundary reveal">'
    f'<span class="bip-boundary-icon">{render_icon("shield-check")}</span>'
    '<div>'
    f'<div class="bip-boundary-label">{_e(copy["boundary"]["label"])}</div>'
    f'<div class="bip-boundary-body">{_e(copy["boundary"]["body"])}</div>'
    '</div></div>',
    unsafe_allow_html=True,
)

# 1. Where the prototype could fit — journey flow + today/future model.
fit = copy["fit"]
st.markdown(
    '<section class="bip-section reveal">'
    f'{_heading(fit["heading"], fit["caption"])}'
    f'{_journey_flow(fit["steps"])}'
    f'{_today_future(fit["today"], fit["future"], fit["bridge"])}'
    '</section>',
    unsafe_allow_html=True,
)

# 2. The product — full-bleed navy band with the live Top 50 Review Queue.
product = copy["product"]
st.markdown(
    '<section class="bip-band bip-product reveal">'
    '<div class="bip-product-glow" aria-hidden="true"></div>'
    '<div class="bip-product-head">'
    '<div class="bip-rule"></div>'
    f'<div class="bip-product-eyebrow">{_e(product["kicker"])}</div>'
    f'<div class="bip-product-title">{_e(product["title"])}</div>'
    '</div>'
    f'{_product_frame(product)}'
    '</section>',
    unsafe_allow_html=True,
)

# 3. What bank records add — varied records grid (Beneficial ownership leads).
domains = copy["data_domains"]
st.markdown(
    '<section class="bip-section reveal">'
    f'{_heading(domains["heading"], domains["caption"])}'
    f'{_records(domains["items"])}'
    '</section>',
    unsafe_allow_html=True,
)

# 4. Where AI could help — full-bleed cool-tint band: callout, record-linking
#    flow, the concept mockup, what the analyst receives, and the hard rules.
ai = copy["ai_extension"]
st.markdown(
    '<section class="bip-band bip-ai reveal">'
    f'{_heading(ai["heading"], None)}'
    f'<p class="bip-ai-lead">{_e(ai["caption"])}</p>'
    '<div class="bip-ai-callout">'
    f'<span class="bip-ai-callout-icon">{render_icon("brain")}</span>'
    f'<p>{_e(ai["value_statement"])}</p></div>'
    f'{_ai_flow(ai["steps"])}'
    f'{_mockup(ai["mockup"])}'
    f'<div class="bip-outputs-title">{_e(ai["outputs_heading"])}</div>'
    f'{_outputs(ai["outputs"])}'
    f'<div class="bip-rules-title">{_e(ai["guardrail_heading"])}</div>'
    f'{_rules(ai["guardrails"])}'
    '</section>',
    unsafe_allow_html=True,
)

# 5. How this could help a wholesale-banking AFC team — numbered value band.
value = copy["value"]
st.markdown(
    '<section class="bip-section reveal">'
    f'{_heading(value["heading"], None)}'
    f'{_value_band(value["items"])}'
    '</section>',
    unsafe_allow_html=True,
)

# 6. Closing statement + design-basis footnote.
st.markdown(
    '<section class="bip-closing reveal">'
    f'{_closing(copy["closing"])}'
    '</section>'
    '<div class="bip-footnote">'
    f'{render_icon("file-text")}<span>{_e(copy["design_basis"])}</span>'
    '</div>',
    unsafe_allow_html=True,
)

# Reveal each section as it scrolls into view (fail-safe: visible if blocked).
render_scroll_reveal(".reveal")
