"""Business Problem & Value — narrative-first landing page.

Answers five questions in reading order: what problem are we solving, what
does the project do, what does it produce, why is it useful, and what does it
not claim. Every number is derived live from pipeline outputs; every sentence
template lives in dashboard_content.yml. The human-review boundary rides on
this page (like every page) as the fixed footer ribbon rendered by
streamlit_app.py.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.page_header import ledger
from dashboard.services import data_loader as load
from dashboard.services.formatting import label_from_key

content = load.load_content()
copy = content["pages"]["executive_overview"]
theme = load.load_theme()

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


# ---- 1 · Hero ---------------------------------------------------------------
st.markdown(
    f'<div class="hero-block anim">'
    f'<div class="page-eyebrow">{_e(copy["eyebrow"])}</div>'
    f'<h1 class="page-title">{_e(copy["title"])}</h1>'
    f'<div class="page-subtitle">{_e(copy["subtitle"])}</div>'
    f"</div>",
    unsafe_allow_html=True,
)


# ---- 2 · The business problem + challenge/response twin cards ----------------
def _twin_card(card: dict, kind: str) -> str:
    bullets = "".join(f"<li>{_e(item)}</li>" for item in card["bullets"])
    return (
        f'<div class="twin-card {kind}">'
        f'<div class="twin-label">{_e(card["label"])}</div>'
        f"<ul>{bullets}</ul></div>"
    )


st.markdown(
    f'<div class="landing-section anim d1">'
    f'<div class="landing-heading">{_e(copy["problem_heading"])}</div>'
    f'<p class="landing-prose">{_e(copy["problem_body"])}</p>'
    f'<p class="landing-prose">{_e(copy["problem_body_2"])}</p>'
    f'<div class="twin-grid">'
    f'{_twin_card(copy["challenge_card"], "challenge")}'
    f'{_twin_card(copy["response_card"], "response")}'
    f"</div></div>",
    unsafe_allow_html=True,
)

# ---- 3 · What this project does + commodity chips -----------------------------
what_1 = _e(copy["what_body"].format(
    observations=observations, year_start=year_start, year_end=year_end,
    n_commodities=n_commodities,
))
# Inject the corridor-definition tooltip around the {corridor_term} placeholder.
term_html = _tip(copy["corridor_term"], copy["tooltip_corridor"])
what_2 = term_html.join(_e(part) for part in copy["what_body_2"].split("{corridor_term}"))
chips = "".join(
    f'<span class="chip"><span class="chip-dot" style="background:{theme["families"][fid]};">'
    f"</span>{_e(family_names[fid])}</span>"
    for fid in theme["families"] if fid in family_names
)
st.markdown(
    f'<div class="landing-section anim d2">'
    f'<div class="landing-heading">{_e(copy["what_heading"])}</div>'
    f'<p class="landing-prose">{what_1}</p>'
    f'<div class="chip-row">{chips}</div>'
    f'<p class="landing-prose">{what_2}</p>'
    f"</div>",
    unsafe_allow_html=True,
)

# ---- 4 · What stakeholders receive (stat band) --------------------------------
deliverables = copy["deliverables"]
tip_evidence = copy["tooltip_evidence"].format(
    evidence_per_case=evidence_per_case,
    n_types=len(evidence_types),
    evidence_types=" · ".join(evidence_types),
)
tiles = [
    (_e(observations), _e(deliverables["observations"]["label"]),
     _e(deliverables["observations"]["detail"])),
    (_e(f"Top {queue_size}"), _e(deliverables["queue"]["label"]),
     _e(deliverables["queue"]["detail"])),
    (_e(evidence_per_case), _tip(deliverables["evidence"]["label"], tip_evidence),
     _e(deliverables["evidence"]["detail"])),
    (_e(f"{len(briefs)}") if briefs else "—", _e(deliverables["briefs"]["label"]),
     _e(deliverables["briefs"]["detail"])),
]
tiles_html = "".join(
    f'<div class="stat-tile"><div class="stat-value">{value}</div>'
    f'<div class="stat-label">{label}</div>'
    f'<div class="stat-detail">{detail}</div></div>'
    for value, label, detail in tiles
)
st.markdown(
    f'<div class="landing-section anim d3">'
    f'<div class="landing-heading">{_e(copy["deliverables_heading"])}</div>'
    f'<div class="stat-band">{tiles_html}</div>'
    f"</div>",
    unsafe_allow_html=True,
)
st.page_link("app_pages/review_queue.py", label=f"{copy['queue_cta']} →",
             icon=":material/checklist:")
ledger("panel", "review_queue", "evidence",
       *(["analyst_briefs"] if briefs else []))

# ---- 5 · Pipeline flow strip ---------------------------------------------------
flow = '<span class="flow-arrow" aria-hidden="true">→</span>'.join(
    f'<span class="flow-step">{_e(step)}</span>' for step in copy["pipeline_steps"]
)
st.markdown(
    f'<div class="landing-section anim d4">'
    f'<div class="landing-heading">{_e(copy["pipeline_heading"])}</div>'
    f'<div class="flow-strip">{flow}</div>'
    f"</div>",
    unsafe_allow_html=True,
)
st.page_link("app_pages/from_data_to_review_queue.py", label=f"{copy['pipeline_cta']} →",
             icon=":material/account_tree:")

# ---- 6 · Why it matters --------------------------------------------------------
st.markdown(
    f'<div class="landing-section anim d5">'
    f'<div class="landing-heading">{_e(copy["why_heading"])}</div>'
    f'<div class="quote-grid">'
    f'<div class="quote-card before"><div class="quote-label">{_e(copy["quote_before_label"])}</div>'
    f'<div class="quote-text">“{_e(copy["quote_before"])}”</div></div>'
    f'<div class="quote-card after"><div class="quote-label">{_e(copy["quote_after_label"])}</div>'
    f'<div class="quote-text">“{_e(copy["quote_after"])}”</div></div>'
    f"</div>"
    f'<p class="landing-prose">{_e(copy["why_body"])}</p>'
    f"</div>",
    unsafe_allow_html=True,
)

# ---- 7 · Bottom line -------------------------------------------------------------
bottom_line = copy["bottom_line"].format(observations=observations, queue_size=queue_size)
value_chips = "".join(f'<span class="value-chip">{_e(chip)}</span>'
                      for chip in copy["value_chips"])
st.markdown(
    f'<div class="landing-section anim d6">'
    f'<div class="bottom-line"><div class="bottom-line-text">{_e(bottom_line)}</div>'
    f'<div class="value-chip-row">{value_chips}</div></div>'
    f"</div>",
    unsafe_allow_html=True,
)
