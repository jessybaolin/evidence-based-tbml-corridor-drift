"""From Data to Review Queue — the interactive "Data Coverage & Trust" story.

One page, two scenes, one mental model kept in view throughout:
official trade data is verified, standardised and converted into time-safe
analytical signals; synthetic scenarios only test and select the model; only
real official observations enter the review queue.

Scene 1 — the three institutional sources and the unit of analysis.
Scene 2 — how official records become comparable analytical observations.

How the ranking is then tested and chosen is a model-validation story; it lives
on the Model Evaluation & Controls page, linked from the end of this one.

Every number is derived live from the loaded artefacts (never typed in), and all
stakeholder copy lives in dashboard_content.yml. The human-review boundary
rides on this page as the fixed footer ribbon rendered by streamlit_app.py.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.banners import render_info_banner
from dashboard.components.cards import kpi_card_markup, source_card_markup
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.components.page_header import ledger, page_header
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

content = load.load_content()
copy = content["pages"]["from_data_to_review_queue"]

# ---- Derived facts (never typed in; the ledger names the backing files) ------
panel = load.load_panel(columns=(
    "obs_id", "year", "family_id", "product_name", "hs6",
    "exporter_name", "importer_name", "trade_value_usd", "quantity_metric_ton",
    "model_eligible", "benchmark_price_original", "benchmark_unit_original",
))
queue = load.load_review_queue()
benchmark_series = load.load_benchmark_series_config() or []

total_rows = len(panel)
years = sorted(int(y) for y in panel["year"].unique())
n_years = len(years)
year_span = fm.year_span(years)
n_families = int(panel["family_id"].nunique())

eligible_mask = panel["model_eligible"].astype(bool)
eligible_rows = int(eligible_mask.sum())
eligible_pct = 100.0 * eligible_rows / total_rows
value_share = (
    100.0 * float(panel.loc[eligible_mask, "trade_value_usd"].sum())
    / float(panel["trade_value_usd"].sum())
)

short_labels = content.get("family_short_labels", {})
family_names = " · ".join(
    short_labels.get(fid, fid) for fid in short_labels if fid in set(panel["family_id"])
)
family_hs6 = dict(panel[["family_id", "hs6"]].drop_duplicates().itertuples(index=False))
family_product = dict(
    panel[["family_id", "product_name"]].drop_duplicates().itertuples(index=False)
)
family_bench_unit = {row["family_id"]: row["original_unit"] for row in benchmark_series}

# Neutral, deterministic sample observation: the largest-trade-value official
# row that is NOT on the review queue — a big, ordinary flow, never a case.
_non_queue = panel[~panel["obs_id"].isin(set(queue["obs_id"]))]
sample = _non_queue.loc[_non_queue["trade_value_usd"].idxmax()]

# Real benchmark sample: the latest gold year (gold carries the unit conversion).
_gold = panel[
    (panel["family_id"] == "gold_unwrought") & panel["benchmark_price_original"].notna()
]
gold_bench = _gold.loc[_gold["year"].idxmax()] if not _gold.empty else None


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _tip(term: str, tip: str) -> str:
    # CSS-only tooltip (styles.py .tip): opens on hover and keyboard focus.
    return f'<span class="tip" tabindex="0" data-tip="{_e(tip)}">{_e(term)}</span>'


# ---- Page frame: header · sticky mental model · trust KPI strip --------------
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

render_info_banner(copy["mental_model_stamp"], copy["mental_model"], icon="shield-check")

kpis = copy["kpis"]
tiles = [
    (f"{total_rows:,}",
     _tip(kpis["observations"]["label"], kpis["observations"]["tip"]),
     kpis["observations"]["detail"]),
    (year_span,
     _e(kpis["period"]["label"]),
     kpis["period"]["detail"].format(n_years=n_years)),
    (f"{n_families}",
     _e(kpis["families"]["label"]),
     kpis["families"]["detail"].format(family_names=family_names)),
    (f"{eligible_pct:.1f}%",
     _tip(kpis["eligible"]["label"], kpis["eligible"]["tip"]),
     kpis["eligible"]["detail"].format(eligible_count=f"{eligible_rows:,}")),
    (f"{value_share:.1f}%",
     _tip(kpis["value_coverage"]["label"], kpis["value_coverage"]["tip"]),
     kpis["value_coverage"]["detail"].format(
         excluded_share=f"{100.0 - value_share:.1f}")),
]
KPI_ICONS = ["database", "calendar", "package", "shield-check", "chart-pie"]
tiles_html = "".join(
    kpi_card_markup(value, label, detail, icon)
    for (value, label, detail), icon in zip(tiles, KPI_ICONS)
)
st.markdown(f'<div class="stat-band five anim">{tiles_html}</div>', unsafe_allow_html=True)
ledger("panel", "review_queue", "evidence")

# ---- Scene mechanics ----------------------------------------------------------
SCENE_LABELS = [str(label) for label in copy["scene_labels"]]
_SCENE = "dtrq_scene"
_BAR = "dtrq_stage_bar"
_REPLAY = "dtrq_replay"

if _SCENE not in st.session_state:
    st.session_state[_SCENE] = 0
if _REPLAY not in st.session_state:
    st.session_state[_REPLAY] = 0
st.session_state.setdefault(_BAR, SCENE_LABELS[st.session_state[_SCENE]])


def _go(delta: int) -> None:
    idx = max(0, min(len(SCENE_LABELS) - 1, st.session_state[_SCENE] + delta))
    if idx != st.session_state[_SCENE]:
        st.session_state[_SCENE] = idx
        st.session_state[_REPLAY] += 1  # remount -> the scene's entrance replays
    st.session_state[_BAR] = SCENE_LABELS[idx]


def _on_bar() -> None:
    label = st.session_state.get(_BAR)
    if label is None:
        # segmented_control allows deselection; keep the current scene selected.
        st.session_state[_BAR] = SCENE_LABELS[st.session_state[_SCENE]]
        return
    idx = SCENE_LABELS.index(label)
    if idx != st.session_state[_SCENE]:
        st.session_state[_SCENE] = idx
        st.session_state[_REPLAY] += 1


bar_col, prev_col, next_col = st.columns(
    [5.5, 1.2, 1.05], vertical_alignment="center"
)
with bar_col:
    st.segmented_control(
        "Story scene", SCENE_LABELS, key=_BAR, on_change=_on_bar,
        label_visibility="collapsed",
    )
scene_idx = int(st.session_state[_SCENE])
with prev_col:
    st.button(copy["prev_label"], key="dtrq_prev", on_click=_go, args=(-1,),
              type="secondary", disabled=scene_idx == 0, width="stretch")
with next_col:
    # Primary action = teal fill (styles.py stBaseButton-primary).
    st.button(copy["next_label"], key="dtrq_next", on_click=_go, args=(1,),
              type="primary", disabled=scene_idx == len(SCENE_LABELS) - 1,
              width="stretch")

_replay_stamp = int(st.session_state[_REPLAY])


def _block(inner: str) -> None:
    # Scene HTML is wrapped with the replay counter as a data attribute:
    # changing it changes the markdown payload, Streamlit remounts the DOM
    # node, and the CSS entrance storyboard replays. No JS, no loops.
    st.markdown(
        f'<div data-scene="{scene_idx}" data-replay="{_replay_stamp}">{inner}</div>',
        unsafe_allow_html=True,
    )


def _pv_rows(pairs: list[tuple[str, str]]) -> str:
    return "".join(
        f'<div class="pv-row"><span class="pv-k">{_e(k)}</span>'
        f'<span class="pv-v">{_e(v)}</span></div>'
        for k, v in pairs
    )


# ---- Scene 1 · Sources & scope -------------------------------------------------
def _scene_sources() -> None:
    s1 = copy["scene1"]
    cards = s1["cards"]
    # The "hover for a sample" prompt was removed; source cards keep the reveal
    # on hover/focus but no longer advertise it.
    hint = ""

    baci = cards["baci"]
    baci_preview = (
        f'<div class="src-preview"><div class="pv-title">{_e(baci["preview_title"])}</div>'
        + _pv_rows([
            ("Year", f"{int(sample['year'])}"),
            ("Exporter", str(sample["exporter_name"])),
            ("Importer", str(sample["importer_name"])),
            ("Product", f"HS6 {sample['hs6']} — {sample['product_name']}"),
            ("Value", fm.money(sample["trade_value_usd"])),
            ("Quantity", fm.quantity_mt(sample["quantity_metric_ton"])),
        ])
        + f'<div class="pv-cap">{_e(baci["preview_caption"])}</div></div>'
    )
    card_1_body = (
        f'<span class="src-lab">{_e(s1["supplies_label"])}</span>'
        f'<div class="src-row">{_e(baci["supplies"])}</div>'
        f'<span class="src-lab">{_e(s1["credible_label"])}</span>'
        f'<div class="src-row">{_e(baci["credible"])}</div>'
        f'<div class="src-row src-boundary"><span class="src-lab">'
        f'{_e(s1["boundary_label"])}</span>{_e(baci["boundary"])}</div>'
        f"{hint}{baci_preview}"
    )
    card_1 = source_card_markup(
        role="official", icon="landmark", eyebrow=baci["kicker"], title=baci["name"],
        sections_html=card_1_body, extra_classes="src-baci sb b2", tabindex=True,
    )

    bench = cards["benchmark"]
    bench_pairs = [
        ("Product", short_labels.get("gold_unwrought", "Gold")),
        ("Original unit", family_bench_unit.get("gold_unwrought", "USD per troy ounce")),
        ("Analysis unit", "USD per metric ton"),
        ("Role", str(bench["preview_role"])),
    ]
    bench_cap = ""
    if gold_bench is not None:
        bench_pairs.insert(1, ("Year", f"{int(gold_bench['year'])}"))
        bench_cap = (
            f"{int(gold_bench['year'])} reported price: "
            f"{fm.money(gold_bench['benchmark_price_original'], 2)} per troy ounce, "
            f"converted for comparison with metric-ton quantities."
        )
    bench_preview = (
        f'<div class="src-preview"><div class="pv-title">{_e(bench["preview_title"])}</div>'
        + _pv_rows(bench_pairs)
        + (f'<div class="pv-cap">{_e(bench_cap)}</div>' if bench_cap else "")
        + "</div>"
    )
    card_2_body = (
        f'<span class="src-lab">{_e(s1["supplies_label"])}</span>'
        f'<div class="src-row">{_e(bench["supplies"])}</div>'
        f'<span class="src-lab">{_e(s1["use_label"])}</span>'
        f'<div class="src-row">{_e(bench["use"])}</div>'
        f'<div class="src-row src-boundary"><span class="src-lab">'
        f'{_e(s1["boundary_label"])}</span>{_e(bench["boundary"])}</div>'
        f"{hint}{bench_preview}"
    )
    card_2 = source_card_markup(
        role="benchmark", icon="line-chart", eyebrow=bench["kicker"], title=bench["name"],
        sections_html=card_2_body, extra_classes="src-worldbank sb b3", tabindex=True,
    )

    fatf = cards["fatf"]
    never_items = "".join(f"<li>{_e(item)}</li>" for item in fatf["never"])
    card_3_body = (
        f'<span class="src-lab">{_e(s1["supplies_label"])}</span>'
        f'<div class="src-row">{_e(fatf["supplies"])}</div>'
        f'<span class="src-lab">{_e(s1["use_label"])}</span>'
        f'<div class="src-row">{_e(fatf["use"])}</div>'
        f'<div class="src-row src-boundary src-never"><span class="src-lab">'
        f'{_e(fatf["never_intro"])}</span><ul>{never_items}</ul></div>'
    )
    card_3 = source_card_markup(
        role="typology", icon="file-search", eyebrow=fatf["kicker"], title=fatf["name"],
        sections_html=card_3_body, extra_classes="src-fatf sb b4",
    )

    _block(
        f'<div class="landing-section sb reveal b1">'
        f'<div class="landing-heading">{_e(s1["heading"])}</div></div>'
        f'<div class="src-grid">{card_1}{card_2}{card_3}</div>'
    )

    # Unit of analysis: one real record shown as a plain table, plus the twin
    # It-is / It-is-not cards.
    unit = s1["unit"]
    rf = unit["record_fields"]
    record_rows = [
        (rf["year"], str(int(sample["year"]))),
        (rf["exporter"], _e(sample["exporter_name"])),
        (rf["importer"], _e(sample["importer_name"])),
        (rf["product"], f'HS6 {_e(sample["hs6"])} · {_e(sample["product_name"])}'),
        (rf["value"], _e(fm.money(sample["trade_value_usd"]))),
        (rf["quantity"], _e(fm.quantity_mt(sample["quantity_metric_ton"]))),
    ]
    record_body = "".join(
        f'<tr><td class="rec-k">{_e(label)}</td><td>{value}</td></tr>'
        for label, value in record_rows
    )
    corridor = (
        f'<div class="data-table-wrap"><table class="data-table"><tbody>'
        f"{record_body}</tbody></table></div>"
        f'<div class="mini-note">{_e(unit["record_caption"])}</div>'
    )
    twin = (
        f'<div class="twin-grid">'
        f'<div class="twin-card response"><div class="twin-label">{_e(unit["is_label"])}</div>'
        f"<p>{_e(unit['is_text'])}</p></div>"
        f'<div class="twin-card"><div class="twin-label">{_e(unit["is_not_label"])}</div>'
        f"<p>{_e(unit['is_not_text'])}</p></div>"
        f"</div>"
    )
    _block(
        f'<div class="landing-section sb reveal b5">'
        f'<div class="landing-heading">{_e(unit["heading"])}</div>'
        f'<div class="unit-eq">{_e(unit["equation"])}</div>'
        f"{corridor}{twin}"
        f'<p class="landing-prose">{_e(unit["closing"])}</p>'
        f"</div>"
    )

    # Why these three product families: each card carries its family colour, and
    # the copy is shown directly (no hover reveal).
    fams = s1["families"]
    order = ["gold_unwrought", "refined_copper_cathodes", "crude_palm_oil"]
    fam_cards = []
    for beat, fid in zip(("b6", "b7", "b7"), order):
        if fid not in family_hs6:
            continue
        role = fams["roles"][fid]
        fam_cards.append(
            f'<div class="fam-card sb {beat} fam-{fid}">'
            f'<div class="fam-head"><span class="chip-dot"></span>'
            f'<span class="fam-name">{_e(short_labels.get(fid, fid))}</span></div>'
            f'<div class="fam-role">{_e(role["role"])}</div>'
            f'<div class="fam-body">{_e(role["body"])}</div>'
            f"</div>"
        )
    tags = "".join(f'<span class="tag">{_e(tag)}</span>' for tag in fams["tags"])
    _block(
        f'<div class="landing-section sb reveal b6">'
        f'<div class="landing-heading">{_e(fams["heading"])}</div></div>'
        f'<div class="fam-grid">{"".join(fam_cards)}</div>'
        f'<div class="sb b8"><div class="tag-row">{tags}</div>'
        f'<p class="landing-prose">{_e(fams["statement"])}</p></div>'
    )
    ledger("panel", "hs_families", "benchmark_series")


# ---- Scene 2 · Prepare the data -------------------------------------------------
def _scene_prepare() -> None:
    s2 = copy["scene2"]

    stage_cards = []
    for i, stage in enumerate(s2["stages"], start=1):
        stage_cards.append(
            f'<div class="pipe-stage sb b{min(i + 1, 8)}">'
            f'<span class="pipe-num">{i}</span>'
            f'<div class="pipe-title">{_e(stage["title"])}</div>'
            f'<div class="pipe-body">{_e(stage["body"])}</div></div>'
        )
        if i < len(s2["stages"]):
            stage_cards.append(
                f'<span class="pipe-arrow sb b{min(i + 1, 8)}" aria-hidden="true">→</span>'
            )
    _block(
        f'<div class="landing-section sb reveal b1">'
        f'<div class="landing-heading">{_e(s2["heading"])}</div></div>'
        f'<div class="pipe-strip">{"".join(stage_cards)}</div>'
    )

    row_panel = s2["row_panel"]
    row_fields = row_panel["record_fields"]
    record_cells = [
        (row_fields["observation_id"], sample["obs_id"], "mono"),
        (row_fields["year"], str(int(sample["year"])), "num"),
        (row_fields["corridor"],
         f'{sample["exporter_name"]} → {sample["importer_name"]}', ""),
        (row_fields["product"],
         f'HS6 {sample["hs6"]} · {sample["product_name"]}', ""),
        (row_fields["trade_value"], fm.money(sample["trade_value_usd"]), "num"),
        (row_fields["quantity"], fm.quantity_mt(sample["quantity_metric_ton"]), "num"),
    ]
    record_headers = "".join(f"<th>{_e(label)}</th>" for label, _, _ in record_cells)
    record_values = "".join(
        f'<td class="{css_class}">{_e(value)}</td>'
        for _, value, css_class in record_cells
    )
    _block(
        f'<div class="prep-panel prep-record-panel sb b5">'
        f'<div class="prep-kicker">3 · {_e(s2["stages"][2]["title"])}</div>'
        f'<div class="data-table-wrap prep-record-table"><table class="data-table">'
        f'<thead><tr>{record_headers}</tr></thead>'
        f'<tbody><tr>{record_values}</tr></tbody></table></div>'
        f'<div class="mini-note">{_e(row_panel["record_caption"])}</div>'
        f"</div>"
    )

    timesafe = s2["timesafe_panel"]
    chips = "".join(
        f'<div class="sig-chip"><div class="sig-name">{_e(chip["name"])}</div>'
        f'<div class="sig-q">{_e(chip["question"])}</div></div>'
        for chip in timesafe["chips"]
    )
    focus_year = 2022 if 2022 in years else years[max(0, len(years) - 3)]
    history_years = [y for y in years if y < focus_year]
    hidden_years = [y for y in years if y > focus_year]
    year_chips = []
    for i, y in enumerate(history_years):
        year_chips.append(f'<span class="yr lit yl{min(i + 1, 5)}">{y}</span>')
    year_chips.append(
        f'<span class="yr focus ylf">{focus_year}'
        f"<small>{_e(timesafe['year_compare_label'])}</small></span>"
    )
    for y in hidden_years:
        year_chips.append(
            f'<span class="yr hid">{y}<small>✕ {_e(timesafe["year_hidden_label"])}</small></span>'
        )
    year_caption = timesafe["year_caption"].format(
        focus_year=focus_year,
        history_span=fm.year_span(history_years) if history_years else "—",
        hidden_span=fm.year_span(hidden_years) if hidden_years else "—",
    )
    _block(
        f'<div class="prep-panel sb b7">'
        f'<div class="prep-kicker">5 · {_e(s2["stages"][4]["title"])}</div>'
        f'<p class="prep-body">{_e(timesafe["definition"])}</p>'
        f'<div class="sig-chip-row">{chips}</div>'
        f'<div class="mini-note year-section-heading">'
        f'{_e(timesafe["year_heading"].format(focus_year=focus_year))}</div>'
        f'<div class="year-strip">{"".join(year_chips)}</div>'
        f'<div class="mini-note">{_e(year_caption)}</div>'
        f"</div>"
    )
    ledger("panel", "source_manifest", "features")


if scene_idx == 0:
    _scene_sources()
else:
    _scene_prepare()

# ---- Closing statement + validation deep-dive link: only on the final scene ----
if scene_idx == len(SCENE_LABELS) - 1:
    closing = copy["closing"]
    # One navy wrap-up panel holds the bottom line AND the on-demand link to the
    # model-validation deep dive, so the close reads as a single block. How the
    # ranking is tested is a separate story — a link here, not a mandatory scene.
    with st.container(key="dtrq_closing"):
        st.markdown(
            f'<div class="bottom-line-text">{_e(closing["statement"])}</div>'
            f'<div class="bl-reminder">{_e(closing["reminder"])}</div>',
            unsafe_allow_html=True,
        )
        st.page_link("app_pages/model_and_controls.py",
                     label=f'{copy["model_eval_cta"]} →', icon=":material/verified_user:")

# Reveal the story sections (and the closing panel) as they scroll into view.
render_scroll_reveal(".reveal, .st-key-dtrq_closing")
