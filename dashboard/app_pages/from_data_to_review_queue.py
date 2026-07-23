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
from dashboard.services import data_dictionary as ddict
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

content = load.load_content()
copy = content["pages"]["from_data_to_review_queue"]

# ---- Derived facts (never typed in; the ledger names the backing files) ------
panel = load.load_panel(columns=(
    "obs_id", "year", "family_id", "product_name", "hs6",
    "exporter_name", "importer_name", "trade_value_usd", "quantity_metric_ton",
    "model_eligible", "benchmark_price_original", "benchmark_unit_original",
    "benchmark_price_usd_per_metric_ton", "unit_value_usd_per_metric_ton",
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

# Time-safe signals for the sample obs, read from the features table — the same
# columns that feed the ranking — so the demonstration table below traces the
# metrics straight back to one auditable row. Values are formatted on the page.
_feat = load.load_features(columns=(
    "obs_id", "robust_historical_z", "same_family_year_peer_percentile",
    "unit_value_usd_per_metric_ton", "benchmark_price_usd_per_metric_ton",
    "unit_value_yoy_change", "benchmark_residual",
    "value_quantity_divergence", "corridor_activity_history",
    "corridor_novelty_flag", "corridor_reactivation_flag",
))
_sf = _feat[_feat["obs_id"] == sample["obs_id"]]
sample_signals = _sf.iloc[0] if not _sf.empty else None

# Authoritative field definitions for the in-table info icons, read from the
# same sources the Appendix data dictionary uses (feature-explanation table,
# then the code-derived definitions) so the tooltips can never drift from it.
_feat_expl = load.load_feature_explanations()
_TIPS = {
    field: ddict.field_tooltip(field, _feat_expl)
    for field in (
        "unit_value_usd_per_metric_ton", "unit_value_yoy_change",
        "same_family_year_peer_percentile", "benchmark_residual",
    )
}


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _tip(term: str, tip: str) -> str:
    # CSS-only tooltip (styles.py .tip): opens on hover and keyboard focus.
    return f'<span class="tip" tabindex="0" data-tip="{_e(tip)}">{_e(term)}</span>'


def _year_list_phrase(yrs: list[int]) -> str:
    # "2022, 2023 or 2024" / "2024" / "later years" — a natural spoken list.
    labels = [str(y) for y in yrs]
    if not labels:
        return "later years"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + " or " + labels[-1]


def _th(label: str, tip: str | None = None) -> str:
    # A table header cell. When a definition is supplied it carries a native
    # `title` tooltip (browser-rendered, so — unlike a CSS tooltip — it is never
    # clipped by the table's horizontal-scroll wrapper) plus a small ⓘ cue.
    # Each line of the definition is escaped, then joined with a newline entity
    # so the derivation drops onto its own line in the tooltip (a raw "\n" can be
    # collapsed by the markdown pipeline; "&#10;" renders reliably).
    if tip:
        tip_attr = "&#10;".join(_e(line) for line in tip.split("\n"))
        return (f'<th title="{tip_attr}">{_e(label)} '
                f'<span class="th-info" aria-hidden="true">ⓘ</span></th>')
    return f"<th>{_e(label)}</th>"


def _row_panel_cells() -> list[tuple[str, str, str, str | None]]:
    """The one clean annual row, as (label, value, css, tooltip) cells.

    Shared by the "build one clean annual row" table and the signals table so
    both show the identical prepared row; only the signals table appends the
    derived columns. Values come from the real sample observation.
    """
    fields = copy["scene2"]["row_panel"]["record_fields"]
    bench_mt = sample["benchmark_price_usd_per_metric_ton"]
    uv_mt = sample["unit_value_usd_per_metric_ton"]
    return [
        (fields["observation_id"], str(sample["obs_id"]), "mono", None),
        (fields["year"], str(int(sample["year"])), "num", None),
        (fields["corridor"],
         f'{sample["exporter_name"]} → {sample["importer_name"]}', "", None),
        (fields["product"],
         f'{short_labels.get(sample["family_id"], sample["product_name"])} · HS6 {sample["hs6"]}',
         "", None),
        (fields["trade_value"], fm.money(sample["trade_value_usd"]), "num", None),
        (fields["quantity"], fm.quantity_mt(sample["quantity_metric_ton"]), "num", None),
        # Implied unit value, beside its world-market benchmark; the info icon
        # carries the data-dictionary definition of why it is an "implied
        # aggregate unit value for one metric ton".
        (fields["unit_value"], fm.money(uv_mt) if uv_mt == uv_mt else "—", "num",
         _TIPS["unit_value_usd_per_metric_ton"]),
        (fields["benchmark"],
         fm.money(bench_mt) if bench_mt == bench_mt else "—", "num", None),
    ]


def _signals_table_html(timesafe: dict, focus_year: int) -> str:
    """The same prepared row, replicated, then extended with three derived,
    time-safe signals read from the features table (the same columns that feed
    the ranking) so a reader can trace each signal back to one auditable row.
    Each derived column carries its data-dictionary definition as an info icon.
    """
    if sample_signals is None:
        return ""
    table_copy = timesafe["signal_table"]
    sig_labels = table_copy["signal_columns"]
    s = sample_signals

    def _n(value):
        return value if value == value else None  # NaN → None

    yoy = _n(s["unit_value_yoy_change"])
    peer = _n(s["same_family_year_peer_percentile"])
    resid = _n(s["benchmark_residual"])

    cells = _row_panel_cells() + [
        (sig_labels["unit_value_yoy"],
         f"{yoy * 100:+.1f}%" if yoy is not None else "—", "num",
         _TIPS["unit_value_yoy_change"]),
        (sig_labels["peer_percentile"],
         f"{round(peer * 100)}th pct" if peer is not None else "—", "num",
         _TIPS["same_family_year_peer_percentile"]),
        (sig_labels["benchmark_residual"],
         f"{resid:+.3f}" if resid is not None else "—", "num",
         _TIPS["benchmark_residual"]),
    ]
    head_html = "".join(_th(label, tip) for label, _, _, tip in cells)
    val_html = "".join(f'<td class="{css}">{_e(v)}</td>' for _, v, css, _ in cells)

    # The table shows three signals as an example; note how many are derived in
    # total, counted live from the feature-explanation table (the Data Dictionary
    # source) so the number never drifts. Omit the note if that file is absent.
    intro_text = table_copy["intro"].format(focus_year=focus_year)
    total_signals = len(_feat_expl) if _feat_expl is not None else 0
    if total_signals:
        intro_text += " " + table_copy["scope_note"].format(total_signals=total_signals)
    # The provenance note reads as an explanation OF the table, so it follows it.
    return (
        f'<div class="data-table-wrap prep-record-table prep-signals-table">'
        f'<table class="data-table"><thead><tr>{head_html}</tr></thead>'
        f'<tbody><tr>{val_html}</tr></tbody></table></div>'
        f'<p class="prep-body sig-table-intro">{_e(intro_text)}</p>'
        f'<div class="mini-note">{_e(table_copy["caption"])}</div>'
    )


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
        f'<div class="landing-heading">{_e(s1["heading"])}</div>'
        f'<div class="src-grid">{card_1}{card_2}{card_3}</div>'
        f'</div>'
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
        f'<div class="data-table-wrap"><table class="data-table grid-lines"><tbody>'
        f"{record_body}</tbody></table></div>"
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
        f'<div class="landing-heading">{_e(fams["heading"])}</div>'
        f'<div class="fam-grid">{"".join(fam_cards)}</div>'
        f'<div class="sb b8"><div class="tag-row">{tags}</div>'
        f'<p class="landing-prose">{_e(fams["statement"])}</p></div>'
        f'</div>'
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
        f'<div class="landing-heading">{_e(s2["heading"])}</div>'
        f'<div class="pipe-strip">{"".join(stage_cards)}</div>'
        f'</div>'
    )

    row_panel = s2["row_panel"]
    # The prepared row, carrying the implied unit value beside its benchmark; the
    # signals table below replicates these exact cells and extends them.
    record_cells = _row_panel_cells()
    record_headers = "".join(_th(label, tip) for label, _, _, tip in record_cells)
    record_values = "".join(
        f'<td class="{css_class}">{_e(value)}</td>'
        for _, value, css_class, _ in record_cells
    )
    _block(
        f'<div class="prep-panel prep-record-panel reveal sb b5">'
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
    # The time-safe illustration uses the SAME real observation shown above, so
    # the whole scene is one coherent example (its year drives the strip).
    focus_year = int(sample["year"])
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
    history_span = fm.year_span(history_years) if history_years else "—"
    definition_text = timesafe["definition"].format(
        focus_year=focus_year,
        history_span=history_span,
        hidden_phrase=_year_list_phrase(hidden_years),
    )
    year_caption = timesafe["year_caption"].format(
        focus_year=focus_year,
        history_span=history_span,
        hidden_span=fm.year_span(hidden_years) if hidden_years else "—",
    )
    signals_table_html = _signals_table_html(timesafe, focus_year)
    _block(
        f'<div class="prep-panel reveal sb b7">'
        f'<div class="prep-kicker">5 · {_e(s2["stages"][4]["title"])}</div>'
        f'<p class="prep-body">{_e(definition_text)}</p>'
        f'<div class="sig-chip-row">{chips}</div>'
        f'<div class="year-block">'
        f'<div class="mini-note year-section-heading">'
        f'{_e(timesafe["year_heading"].format(focus_year=focus_year))}</div>'
        f'<div class="year-strip">{"".join(year_chips)}</div>'
        f'<div class="mini-note year-caption">{_e(year_caption)}</div>'
        f'</div>'
        f'{signals_table_html}'
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
        statement_html = "".join(
            f'<p class="bottom-line-text">{_e(para)}</p>'
            for para in closing["statement"]
        )
        st.markdown(statement_html, unsafe_allow_html=True)
        st.page_link("app_pages/model_and_controls.py",
                     label=f'{copy["model_eval_cta"]} →', icon=":material/verified_user:")

# Reveal the story sections (and the closing panel) as they scroll into view.
render_scroll_reveal(".reveal, .st-key-dtrq_closing")
