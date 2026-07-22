"""Business Problem and Value — narrative-first landing page.

Answers five questions in reading order: what problem are we solving, what
does the project do, what does it produce, why is it useful, and what does it
not claim. Every number is derived live from pipeline outputs; every sentence
template lives in dashboard_content.yml. Like every dashboard page it carries the
fixed human-review boundary ribbon (rendered once in streamlit_app.py); the
sections reveal one block at a time on scroll via the .bv-reveal scroll-timeline
in components/styles.py.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.cards import commodity_card_markup, kpi_card_markup
from dashboard.components.icons import render_icon
from dashboard.components.page_header import ledger
from dashboard.components.page_shell import render_page_header, story_section_heading_markup
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.services import data_loader as load
from dashboard.services.formatting import label_from_key

content = load.load_content()
copy = content["pages"]["executive_overview"]

# ---- Derived facts (never typed in; the ledger names the backing files) ----
panel = load.load_panel(columns=("obs_id", "year", "family_id", "product_name"))
queue = load.load_review_queue()
evidence = load.load_evidence()
briefs = load.load_analyst_briefs()  # count/existence only — text never rendered

observations = f"{len(panel):,}"
year_start = int(panel["year"].min())
year_end = int(panel["year"].max())
n_commodities = int(panel["family_id"].nunique())
queue_size = len(queue)

per_case = evidence.groupby("obs_id").size()
evidence_per_case = (
    f"{int(per_case.iloc[0])}" if per_case.nunique() == 1 else f"{per_case.mean():.1f}"
)

# Evidence checks actually present in the evidence table, most frequent first,
# shown with approved display names (fallback: humanised key).
type_labels = content.get("evidence_type_labels", {})
evidence_types = [
    type_labels.get(kind, label_from_key(kind))
    for kind in evidence["evidence_type"].value_counts().index
]

# family_id -> official product name straight from the panel.
family_names = dict(
    panel[["family_id", "product_name"]].drop_duplicates().itertuples(index=False)
)


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _tip(term: str, tip: str) -> str:
    # CSS-only tooltip (styles.py .tip): opens on hover and keyboard focus.
    return f'<span class="tip" tabindex="0" data-tip="{_e(tip)}">{_e(term)}</span>'


def _twin_card(card: dict, kind: str) -> str:
    bullets = "".join(f"<li>{_e(item)}</li>" for item in card["bullets"])
    return (
        f'<div class="twin-card {kind}">'
        f'<div class="twin-label">{_e(card["label"])}</div>'
        f"<ul>{bullets}</ul></div>"
    )


what_1 = _e(copy["what_body"].format(
    observations=observations, year_start=year_start, year_end=year_end,
    n_commodities=n_commodities,
))
# Inject the corridor-definition tooltip around the {corridor_term} placeholder.
term_html = _tip(copy["corridor_term"], copy["tooltip_corridor"])
what_2 = term_html.join(_e(part) for part in copy["what_body_2"].split("{corridor_term}"))
commodity_icons = {
    "crude_palm_oil": "droplet",
    "refined_copper_cathodes": "layers",
    "gold_unwrought": "package",
}
commodity_cards = "".join(
    commodity_card_markup(
        title=family_names[fid],
        family_id=fid,
        icon=commodity_icons[fid],
        info=copy["commodity_info"][fid],
    )
    for fid in content["family_short_labels"] if fid in family_names
)

deliverables = copy["deliverables"]
tip_evidence = copy["tooltip_evidence"].format(
    evidence_per_case=evidence_per_case,
    n_types=len(evidence_types),
    evidence_types=" · ".join(evidence_types),
)
tiles = [
    (observations, _e(deliverables["observations"]["label"]),
     deliverables["observations"]["detail"]),
    (f"Top {queue_size}", _e(deliverables["queue"]["label"]),
     deliverables["queue"]["detail"]),
    (evidence_per_case, _tip(deliverables["evidence"]["label"], tip_evidence),
     deliverables["evidence"]["detail"]),
    (f"{len(briefs)}" if briefs else "—", _e(deliverables["briefs"]["label"]),
     deliverables["briefs"]["detail"]),
]
KPI_ICONS = ["database", "checklist", "shield-check", "file-text"]
KPI_CLASSES = ["outcome-teal", "outcome-blue", "outcome-amber", "outcome-navy"]
tiles_html = "".join(
    kpi_card_markup(value, label, detail, icon, extra_classes=accent)
    for (value, label, detail), icon, accent in zip(tiles, KPI_ICONS, KPI_CLASSES)
)

process_icons = ["database", "line-chart", "file-text", "shield-check"]
process_flow = "".join(
    f'<div class="story-process-stage process-stage-{index}">'
    f'<div class="process-stage-meta"><span class="process-stage-number">{index}</span>'
    f'{render_icon(icon, class_name="process-stage-icon")}</div>'
    f'<div class="process-stage-title">{_e(step)}</div></div>'
    for index, (step, icon) in enumerate(zip(copy["pipeline_steps"], process_icons), start=1)
)

STORY_TAB_KEY = "business_value_story_tab"
story_tabs = [copy["what_heading"], copy["why_heading"], copy["pipeline_heading"]]
if st.session_state.get(STORY_TAB_KEY) not in story_tabs:
    st.session_state[STORY_TAB_KEY] = story_tabs[0]


def _restore_story_tab() -> None:
    if st.session_state.get(STORY_TAB_KEY) is None:
        st.session_state[STORY_TAB_KEY] = story_tabs[0]


bottom_line = copy["bottom_line"].format(observations=observations, queue_size=queue_size)
value_chips = "".join(f'<span class="value-chip">{_e(chip)}</span>'
                      for chip in copy["value_chips"])


with st.container(key="business_value_page"):
    st.markdown('<span class="business-value-page" aria-hidden="true"></span>',
                unsafe_allow_html=True)

    # ---- 1 · Hero -----------------------------------------------------------
    render_page_header(copy["title"], copy["subtitle"], copy["eyebrow"],
                       "hero-block bv-entry")

    # ---- 2–3 · Business problem + challenge/response -----------------------
    st.markdown(
        f'<section class="bv-section bv-problem reveal">'
        f'{story_section_heading_markup(copy["problem_heading"])}'
        f'<div class="bv-readable">'
        f'<p class="landing-prose">{_e(copy["problem_body"])}</p>'
        f'<p class="landing-prose">{_e(copy["problem_body_2"])}</p></div>'
        f'<div class="twin-grid">'
        f'{_twin_card(copy["challenge_card"], "challenge")}'
        f'{_twin_card(copy["response_card"], "response")}'
        f'</div></section>',
        unsafe_allow_html=True,
    )

    # ---- 4 · Stakeholder outcomes ------------------------------------------
    with st.container(key="business_value_stakeholders"):
        st.markdown(
            f'<section class="bv-section">'
            f'{story_section_heading_markup(copy["deliverables_heading"])}'
            f'<div class="stat-band">{tiles_html}</div></section>',
            unsafe_allow_html=True,
        )
        st.page_link("app_pages/review_queue.py", label=f"{copy['queue_cta']} →",
                     icon=":material/checklist:")
        ledger("panel", "review_queue", "evidence",
               *(["analyst_briefs"] if briefs else []))

    # ---- 5 · Manual project story ------------------------------------------
    st.markdown(
        f'<section class="bv-section bv-explore reveal">'
        f'{story_section_heading_markup("Explore the project")}</section>',
        unsafe_allow_html=True,
    )
    with st.container(key="business_value_story"):
        selected_story = st.segmented_control(
            "Explore the project",
            story_tabs,
            key=STORY_TAB_KEY,
            on_change=_restore_story_tab,
            label_visibility="collapsed",
        ) or story_tabs[0]

        if selected_story == story_tabs[0]:
            st.markdown(
                f'<section class="story-panel story-panel-what">'
                f'<div class="story-panel-heading">{_e(copy["what_heading"])}</div>'
                f'<p class="landing-prose">{what_1}</p>'
                f'<div class="commodity-grid">{commodity_cards}</div>'
                f'<p class="landing-prose">{what_2}</p></section>',
                unsafe_allow_html=True,
            )
        elif selected_story == story_tabs[1]:
            st.markdown(
                f'<section class="story-panel story-panel-why">'
                f'<div class="story-panel-heading">{_e(copy["why_heading"])}</div>'
                f'<div class="quote-grid">'
                f'<div class="quote-card before"><div class="quote-label">'
                f'{_e(copy["quote_before_label"])}</div>'
                f'<div class="quote-text">“{_e(copy["quote_before"])}”</div></div>'
                f'<div class="quote-card after"><div class="quote-label">'
                f'{_e(copy["quote_after_label"])}</div>'
                f'<div class="quote-text">“{_e(copy["quote_after"])}”</div></div>'
                f'</div><p class="landing-prose">{_e(copy["why_body"])}</p></section>',
                unsafe_allow_html=True,
            )
        else:
            with st.container(key="business_value_process_panel"):
                st.markdown(
                    f'<section class="story-panel story-panel-process">'
                    f'<div class="story-panel-heading">{_e(copy["pipeline_heading"])}</div>'
                    f'<div class="story-process-flow">{process_flow}</div></section>',
                    unsafe_allow_html=True,
                )
                st.page_link(
                    "app_pages/from_data_to_review_queue.py",
                    label=f"{copy['pipeline_cta']} →",
                    icon=":material/account_tree:",
                )

    # ---- 6 · Final value statement -----------------------------------------
    st.markdown(
        f'<section class="bv-section bv-final reveal">'
        f'<div class="bottom-line"><div class="bottom-line-text">{_e(bottom_line)}</div>'
        f'<div class="value-chip-row">{value_chips}</div></div></section>',
        unsafe_allow_html=True,
    )

# Reveal each section as it scrolls into view. The two widget-backed sections
# (stakeholder tiles + CTA, and the story tabs) are keyed containers, so they
# join the markdown `.reveal` sections by their st-key selectors.
render_scroll_reveal(
    ".st-key-business_value_page .reveal, "
    ".st-key-business_value_stakeholders, .st-key-business_value_story"
)
