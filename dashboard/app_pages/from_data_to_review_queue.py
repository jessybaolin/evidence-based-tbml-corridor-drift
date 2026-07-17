"""From Data to Review Queue — the interactive "Data Coverage & Trust" story.

One page, three scenes, one mental model kept in view throughout:
official trade data is verified, standardised and converted into time-safe
analytical signals; synthetic scenarios only test and select the model; only
real official observations enter the review queue.

Scene 1 — the three institutional sources and the unit of analysis.
Scene 2 — how official records become comparable analytical observations.
Scene 3 — the official-analysis lane vs the controlled evaluation copy, and
          how a ranked row becomes a reviewable, evidence-backed case.

Every number is derived live from the loaded artefacts (never typed in), all
copy lives in dashboard_content.yml, and the detailed material (pipeline PNGs,
raw BACI field names, checksums) sits in the technical companion expander at
the bottom. The human-review boundary rides on this page as the fixed footer
ribbon rendered by streamlit_app.py.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from dashboard.components.empty_states import missing_figure
from dashboard.components.page_header import ledger, page_header
from dashboard.components.tables import plain_table
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm
from dashboard.services.dashboard_metrics import selected_method_label

content = load.load_content()
copy = content["pages"]["from_data_to_review_queue"]
theme = load.load_theme()

# ---- Derived facts (never typed in; the ledger names the backing files) ------
panel = load.load_panel(columns=(
    "obs_id", "year", "family_id", "product_name", "hs6",
    "exporter_name", "importer_name", "trade_value_usd", "quantity_metric_ton",
    "model_eligible", "benchmark_price_original", "benchmark_unit_original",
))
queue = load.load_review_queue()
evidence = load.load_evidence()
project_config = load.load_project_config()
selection = load.load_model_selection()
manifest = load.load_source_manifest()          # optional
source_notes = load.load_data_source_notes()    # optional
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

per_case = evidence.groupby("obs_id").size()
evidence_per_case = (
    f"{int(per_case.iloc[0])}" if per_case.nunique() == 1 else f"{per_case.mean():.1f}"
)
type_labels = content.get("evidence_type_labels", {})
evidence_types = [
    type_labels.get(kind, fm.label_from_key(kind))
    for kind in evidence["evidence_type"].value_counts().index
]

train_span = fm.year_span(project_config["train_years"])
validation_span = fm.year_span(project_config["validation_years"])
test_span = fm.year_span(project_config["test_years"])
queue_size = len(queue)
selected_method = selected_method_label(selection)


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _tip(term: str, tip: str) -> str:
    # CSS-only tooltip (styles.py .tip): opens on hover and keyboard focus.
    return f'<span class="tip" tabindex="0" data-tip="{_e(tip)}">{_e(term)}</span>'


# ---- Page frame: header · sticky mental model · trust KPI strip --------------
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

st.markdown(
    f'<div class="mental-model" role="note">'
    f'<span class="mm-stamp">{_e(copy["mental_model_stamp"])}</span>'
    f'{_e(copy["mental_model"])}</div>',
    unsafe_allow_html=True,
)

kpis = copy["kpis"]
tiles = [
    (f"{total_rows:,}",
     _tip(kpis["observations"]["label"], kpis["observations"]["tip"]),
     _e(kpis["observations"]["detail"])),
    (year_span,
     _e(kpis["period"]["label"]),
     _e(kpis["period"]["detail"].format(n_years=n_years))),
    (f"{n_families}",
     _e(kpis["families"]["label"]),
     _e(kpis["families"]["detail"].format(family_names=family_names))),
    (f"{eligible_pct:.1f}%",
     _tip(kpis["eligible"]["label"], kpis["eligible"]["tip"]),
     _e(kpis["eligible"]["detail"].format(eligible_count=f"{eligible_rows:,}"))),
    (f"{value_share:.1f}%",
     _tip(kpis["value_coverage"]["label"], kpis["value_coverage"]["tip"]),
     _e(kpis["value_coverage"]["detail"].format(
         excluded_share=f"{100.0 - value_share:.1f}"))),
]
tiles_html = "".join(
    f'<div class="stat-tile"><div class="stat-value">{value}</div>'
    f'<div class="stat-label">{label}</div>'
    f'<div class="stat-detail">{detail}</div></div>'
    for value, label, detail in tiles
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


def _replay() -> None:
    st.session_state[_REPLAY] += 1


bar_col, ind_col, prev_col, next_col, replay_col = st.columns(
    [4.4, 1.25, 1.2, 1.05, 1.35], vertical_alignment="center"
)
with bar_col:
    st.segmented_control(
        "Story scene", SCENE_LABELS, key=_BAR, on_change=_on_bar,
        label_visibility="collapsed",
    )
scene_idx = int(st.session_state[_SCENE])
with ind_col:
    st.markdown(
        f'<div class="scene-indicator">'
        f'{_e(copy["scene_indicator"].format(n=scene_idx + 1, total=len(SCENE_LABELS)))}'
        f"</div>",
        unsafe_allow_html=True,
    )
with prev_col:
    st.button(copy["prev_label"], key="dtrq_prev", on_click=_go, args=(-1,),
              disabled=scene_idx == 0, width="stretch")
with next_col:
    st.button(copy["next_label"], key="dtrq_next", on_click=_go, args=(1,),
              disabled=scene_idx == len(SCENE_LABELS) - 1, width="stretch")
with replay_col:
    st.button(copy["replay_label"], key="dtrq_replay_btn", on_click=_replay,
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
    hint = f'<div class="src-hint">{_e(s1["hover_hint"])}</div>'

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
    card_1 = (
        f'<div class="src-card sb b2" tabindex="0">'
        f'<div class="src-kicker">{_e(baci["kicker"])}</div>'
        f'<div class="src-name">{_e(baci["name"])}</div>'
        f'<span class="src-lab">{_e(s1["supplies_label"])}</span>'
        f'<div class="src-row">{_e(baci["supplies"])}</div>'
        f'<span class="src-lab">{_e(s1["credible_label"])}</span>'
        f'<div class="src-row">{_e(baci["credible"])}</div>'
        f'<div class="src-row src-boundary"><span class="src-lab">'
        f'{_e(s1["boundary_label"])}</span>{_e(baci["boundary"])}</div>'
        f"{hint}{baci_preview}</div>"
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
    card_2 = (
        f'<div class="src-card sb b3" tabindex="0">'
        f'<div class="src-kicker">{_e(bench["kicker"])}</div>'
        f'<div class="src-name">{_e(bench["name"])}</div>'
        f'<span class="src-lab">{_e(s1["supplies_label"])}</span>'
        f'<div class="src-row">{_e(bench["supplies"])}</div>'
        f'<span class="src-lab">{_e(s1["use_label"])}</span>'
        f'<div class="src-row">{_e(bench["use"])}</div>'
        f'<div class="src-row src-boundary"><span class="src-lab">'
        f'{_e(s1["boundary_label"])}</span>{_e(bench["boundary"])}</div>'
        f"{hint}{bench_preview}</div>"
    )

    fatf = cards["fatf"]
    never_items = "".join(f"<li>{_e(item)}</li>" for item in fatf["never"])
    card_3 = (
        f'<div class="src-card sb b4">'
        f'<div class="src-kicker">{_e(fatf["kicker"])}</div>'
        f'<div class="src-name">{_e(fatf["name"])}</div>'
        f'<span class="src-lab">{_e(s1["supplies_label"])}</span>'
        f'<div class="src-row">{_e(fatf["supplies"])}</div>'
        f'<span class="src-lab">{_e(s1["use_label"])}</span>'
        f'<div class="src-row">{_e(fatf["use"])}</div>'
        f'<div class="src-row src-boundary src-never"><span class="src-lab">'
        f'{_e(fatf["never_intro"])}</span><ul>{never_items}</ul></div>'
        f"</div>"
    )

    _block(
        f'<div class="landing-section sb b1">'
        f'<div class="landing-heading">{_e(s1["heading"])}</div></div>'
        f'<div class="src-grid">{card_1}{card_2}{card_3}</div>'
    )

    # Unit of analysis: real corridor, twin It-is / It-is-not cards.
    unit = s1["unit"]
    corridor = (
        f'<div class="corridor-visual">'
        f'<div class="cv-lane">'
        f'<div class="cv-node"><span class="cv-role">{_e(unit["exporter_label"])}</span>'
        f'<span class="cv-name">{_e(sample["exporter_name"])}</span></div>'
        f'<div class="cv-link"><span>HS6 {_e(sample["hs6"])} · {_e(sample["product_name"])}</span></div>'
        f'<div class="cv-node"><span class="cv-role">{_e(unit["importer_label"])}</span>'
        f'<span class="cv-name">{_e(sample["importer_name"])}</span></div>'
        f"</div>"
        f'<div class="cv-year">{_e(unit["year_label"].format(year=int(sample["year"])))}</div>'
        f'<div class="cv-arrow" aria-hidden="true">↓</div>'
        f'<div class="cv-row-chip">{_e(unit["row_label"])} — '
        f'value {_e(fm.compact_usd(sample["trade_value_usd"]))} · '
        f'quantity {_e(fm.quantity_mt(sample["quantity_metric_ton"]))}</div>'
        f"</div>"
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
        f'<div class="landing-section sb b5">'
        f'<div class="landing-heading">{_e(unit["heading"])}</div>'
        f'<div class="unit-eq">{_e(unit["equation"])}</div>'
        f"{corridor}{twin}"
        f'<p class="landing-prose">{_e(unit["closing"])}</p>'
        f"</div>"
    )

    # Why these three product families.
    fams = s1["families"]
    order = ["gold_unwrought", "refined_copper_cathodes", "crude_palm_oil"]
    fam_cards = []
    for beat, fid in zip(("b6", "b7", "b7"), order):
        if fid not in family_hs6:
            continue
        role = fams["roles"][fid]
        reveal = (
            f'<div class="src-preview">'
            f'<div class="pv-title">{_e(short_labels.get(fid, fid))} · {_e(family_product.get(fid, fid))}</div>'
            + _pv_rows([
                (fams["hs6_label"], str(family_hs6[fid])),
                (fams["unit_label"], family_bench_unit.get(fid, "—")),
                (fams["tests_label"], str(role["tests"])),
            ])
            + f'<div class="pv-cap">{_e(fams["note"])}</div></div>'
        )
        fam_cards.append(
            f'<div class="fam-card sb {beat}" tabindex="0">'
            f'<div class="fam-head"><span class="chip-dot" '
            f'style="background:{theme["families"].get(fid, "#97A3B4")};"></span>'
            f'<span class="fam-name">{_e(short_labels.get(fid, fid))}</span></div>'
            f'<div class="fam-role">{_e(role["role"])}</div>'
            f'<div class="fam-body">{_e(role["body"])}</div>'
            f"{hint}{reveal}</div>"
        )
    tags = "".join(f'<span class="tag">{_e(tag)}</span>' for tag in fams["tags"])
    _block(
        f'<div class="landing-section sb b6">'
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
        f'<div class="landing-section sb b1">'
        f'<div class="landing-heading">{_e(s2["heading"])}</div></div>'
        f'<div class="pipe-strip">{"".join(stage_cards)}</div>'
    )

    verify = s2["verify_panel"]
    release = "not recorded"
    if source_notes:
        release = str(source_notes.get("baci_release", "not recorded"))
    left, right = st.columns(2)
    with left:
        _block(
            f'<div class="prep-panel sb b3">'
            f'<div class="prep-kicker">1 · {_e(s2["stages"][0]["title"])}</div>'
            f'<div class="file-card"><span class="file-doc" aria-hidden="true"></span>'
            f'<span class="file-name">{_e(verify["file_label"].format(release=release))}</span>'
            f'<span class="verify-badge">✓ {_e(verify["badge"])}</span></div>'
            f'<p class="prep-body">{_e(verify["body"])}</p>'
            f"</div>"
        )
        with st.expander(verify["provenance_cta"]):
            st.markdown(verify["provenance_note"])
            rows = []
            if manifest:
                confirmed = manifest.get("baci_source_confirmed", {})
                if confirmed.get("sha256"):
                    rows.append({"Artefact": "Filtered BACI extract (parquet)",
                                 "SHA-256": confirmed["sha256"]})
            if source_notes:
                checksums = source_notes.get("checksums", {})
                for label, key in [
                    ("BACI country codes", "country_codes_sha256"),
                    ("BACI product codes", "product_codes_sha256"),
                    ("World Bank CMO workbook", "world_bank_workbook_sha256"),
                ]:
                    if checksums.get(key):
                        rows.append({"Artefact": label, "SHA-256": checksums[key]})
            if rows:
                plain_table(pd.DataFrame(rows))
            else:
                st.markdown("Provenance records have not been generated for this run.")
            ledger("source_manifest", "data_source_notes")
    with right:
        conv_rows = "".join(
            f'<span class="conv-row">{_e(example)}</span>'
            for example in s2["standardise_panel"]["examples"]
        )
        _block(
            f'<div class="prep-panel sb b4">'
            f'<div class="prep-kicker">2 · {_e(s2["stages"][1]["title"])}</div>'
            f"{conv_rows}"
            f'<div class="mini-note">{_e(s2["stages"][1]["body"])}</div>'
            f"</div>"
        )

    build_col, controls_col = st.columns(2)
    with build_col:
        row_panel = s2["row_panel"]
        tiles = "".join(
            f'<span class="merge-tile {cls}">{_e(label)}</span>'
            for cls, label in zip(("ma", "mb", "mc"), row_panel["raw_labels"])
        )
        _block(
            f'<div class="prep-panel sb b5">'
            f'<div class="prep-kicker">3 · {_e(s2["stages"][2]["title"])}</div>'
            f'<div class="merge-tiles">{tiles}</div>'
            f'<div class="merge-arrow" aria-hidden="true">↓</div>'
            f'<div class="merge-row"><span class="lineage" aria-hidden="true">⌂</span>'
            f'{_e(row_panel["clean_label"])}</div>'
            f'<div class="mini-note">{_e(row_panel["caption"])}</div>'
            f"</div>"
        )
    with controls_col:
        controls = s2["controls_panel"]
        funnel = (
            f'<div class="funnel">'
            f'<div class="funnel-bar f1">{_e(controls["funnel_total"].format(total=f"{total_rows:,}"))}</div>'
            f'<div class="funnel-drop" aria-hidden="true">↓</div>'
            f'<div class="funnel-bar f2" style="width:{eligible_pct:.1f}%;">'
            f'{_e(controls["funnel_eligible"].format(eligible=f"{eligible_rows:,}"))}</div>'
            f'<div class="funnel-drop" aria-hidden="true">↓</div>'
            f'<div class="funnel-note">'
            f'{_e(controls["funnel_value"].format(value_share=f"{value_share:.1f}"))}</div>'
            f"</div>"
        )
        _block(
            f'<div class="prep-panel sb b6">'
            f'<div class="prep-kicker">4 · {_e(s2["stages"][3]["title"])}</div>'
            f'<p class="prep-body">{_e(controls["body"])}</p>'
            f"{funnel}"
            f'<div class="mini-note">{_tip(controls["eligibility_term"], controls["tip"])}'
            f' · {_e(controls["note"])}</div>'
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
        f'<div class="mini-note">{_e(timesafe["year_heading"].format(focus_year=focus_year))}</div>'
        f'<div class="year-strip">{"".join(year_chips)}</div>'
        f'<div class="mini-note">{_e(year_caption)}</div>'
        f"</div>"
    )
    ledger("panel", "source_manifest", "features")


# ---- Scene 3 · Test, rank & explain ----------------------------------------------
def _scene_wall() -> None:
    s3 = copy["scene3"]
    official = s3["official"]
    evaluation = s3["evaluation"]
    resolution = s3["resolution"]

    official_steps = [str(step).format(queue_size=queue_size) for step in official["steps"]]
    official_rows = (
        f'<div class="lane-step"><span class="n">1</span><span>{_e(official_steps[0])}</span></div>'
        f'<div class="lane-step"><span class="n">2</span><span>{_e(official_steps[1])}</span></div>'
        f'<div class="lane-step"><span class="n">3</span><div>'
        f'<span class="model-chip s3-chip">{_e(official_steps[2])}</span>'
        f'<div class="res-detail">{_e(resolution["model_detail"].format(selected_method=selected_method))}</div>'
        f'<div class="res-detail s3-late1">{_e(resolution["applied"])}</div>'
        f"</div></div>"
        f'<div class="lane-step"><span class="n">4</span>'
        f'<span class="queue-node s3-late2">{_e(official_steps[3])}</span></div>'
    )
    eval_steps = [
        str(step).format(train_span=train_span, validation_span=validation_span,
                         test_span=test_span)
        for step in evaluation["steps"]
    ]
    eval_rows = "".join(
        f'<div class="lane-step"><span class="n">{i}</span><span>{_e(step)}</span></div>'
        for i, step in enumerate(eval_steps, start=1)
    )
    fork = (
        f'<div class="fork">'
        f'<div class="fork-top sb b2">{_e(s3["top_node"])}</div>'
        f'<div class="fork-split sb b2"><span aria-hidden="true">▼</span><span></span>'
        f'<span aria-hidden="true">▼</span></div>'
        f'<div class="lane official sb b3">'
        f'<div class="lane-kicker">{_e(official["kicker"])}</div>'
        f'<div class="lane-sub">{_e(official["sub"])}</div>'
        f"{official_rows}</div>"
        f'<div class="wall"><span>{_e(s3["wall_label"])}</span></div>'
        f'<div class="lane eval s3-eval">'
        f'<div class="lane-kicker">{_e(evaluation["kicker"])}</div>'
        f'<div class="eval-label">{_e(evaluation["label"])}</div>'
        f"{eval_rows}"
        f'<div class="lane-note">{_e(evaluation["return_note"])}</div>'
        f"</div></div>"
    )
    _block(
        f'<div class="landing-section sb b1">'
        f'<div class="landing-heading">{_e(s3["heading"])}</div></div>'
        f"{fork}"
        f'<p class="landing-prose sb b5">{_e(s3["supporting"])}</p>'
    )

    output = s3["output"]
    evidence_step = output["step_evidence"].format(evidence_per_case=evidence_per_case)
    example_tags = "".join(f'<span class="tag">{_e(label)}</span>' for label in evidence_types)
    _block(
        f'<div class="landing-section sb b6">'
        f'<div class="landing-heading">{_e(output["heading"])}</div>'
        f'<div class="out-flow">'
        f'<div class="out-node">{_e(output["step_case"])}</div>'
        f'<div class="out-arrow" aria-hidden="true">↓</div>'
        f'<div class="out-node">{_tip(evidence_step, output["evidence_tip"])}</div>'
        f'<div class="out-arrow" aria-hidden="true">↓</div>'
        f'<div class="out-node">{_e(output["step_brief"])}</div>'
        f'<div class="out-arrow" aria-hidden="true">↓</div>'
        f'<div class="out-node review">{_e(output["step_review"])}</div>'
        f"</div>"
        f'<div class="mini-note">{_e(output["examples_intro"])}:</div>'
        f'<div class="tag-row">{example_tags}</div>'
        f"</div>"
    )

    fatf = s3["fatf"]
    brief_items = "".join(f"<li>{_e(item)}</li>" for item in fatf["brief_structure"])
    _block(
        f'<div class="landing-section sb b7">'
        f'<div class="landing-heading">{_e(fatf["heading"])}</div>'
        f'<div class="fatf-grid">'
        f'<div class="fatf-input evidence"><small>Input</small>{_e(fatf["input_evidence"])}</div>'
        f'<div class="fatf-input context"><small>Input</small>{_e(fatf["input_context"])}</div>'
        f'<div class="fatf-join" aria-hidden="true">▼</div>'
        f'<div class="fatf-out">{_e(fatf["output_node"])}</div>'
        f"</div>"
        f'<div class="mini-note">{_e(fatf["note"])}</div>'
        f'<p class="landing-prose" style="margin-bottom:0.25rem;">{_e(fatf["brief_structure_intro"])}:</p>'
        f'<ul class="landing-prose" style="margin-top:0;">{brief_items}</ul>'
        f"</div>"
    )
    layers = pd.DataFrame([list(row) for row in fatf["layers"]], columns=["Layer", "Role"])
    plain_table(layers)
    st.markdown(f'<div class="mini-note">{_e(fatf["render_note"])}</div>',
                unsafe_allow_html=True)
    ledger("review_queue", "evidence", "model_selection", "analyst_briefs")


if scene_idx == 0:
    _scene_sources()
elif scene_idx == 1:
    _scene_prepare()
else:
    _scene_wall()

# ---- Closing statement (persistent, below the scenes) --------------------------
closing = copy["closing"]
st.markdown(
    f'<div class="landing-section anim">'
    f'<div class="bottom-line"><div class="bottom-line-text">{_e(closing["statement"])}</div>'
    f'<div class="bl-reminder">{_e(closing["reminder"])}</div></div></div>',
    unsafe_allow_html=True,
)

# ---- Technical companion (everything detailed lives here, not on the canvas) ---
companion = copy["companion"]
with st.expander(companion["cta"]):
    st.markdown(companion["intro"])

    st.markdown(f"**{companion['figures_heading']}**")
    FIGURES = [
        ("official_data_pipeline_architecture", "official_data_pipeline_architecture.png",
         "The official-data pipeline architecture diagram"),
        ("source_to_report_data_flow", "source_to_report_data_flow.png",
         "The source-to-output data-flow diagram"),
        ("time_safe_feature_construction_flow", "time_safe_feature_construction_flow.png",
         "The time-safe feature-construction diagram"),
        ("train_validation_test_ml_workflow", "train_validation_test_ml_workflow.png",
         "The train / validation / test workflow diagram"),
    ]
    fig_cols = st.columns(2)
    for i, (key, name, label) in enumerate(FIGURES):
        with fig_cols[i % 2]:
            figure = load.figure_path(key)
            if figure:
                st.image(str(figure), width="stretch",
                         caption=f"Source: reports/figures/{name}")
            else:
                missing_figure(f"reports/figures/{name}", label)

    st.markdown(f"**{companion['fields_heading']}**")
    st.markdown(companion["fields_note"])
    if source_notes:
        definitions = source_notes.get("column_definitions", {})
        unit_notes = source_notes.get("important_unit_notes", {})
        fields = pd.DataFrame([
            {"Field": field, "Meaning": meaning, "Unit note": unit_notes.get(field, "")}
            for field, meaning in definitions.items()
        ])
        plain_table(fields)
    else:
        st.markdown("The BACI provenance notes file has not been generated for this run.")

    st.markdown(f"**{companion['provenance_heading']}**")
    prov_rows = []
    if manifest:
        confirmed = manifest.get("baci_source_confirmed", {})
        if confirmed.get("sha256"):
            prov_rows.append({"Artefact": "Filtered BACI extract (parquet)",
                              "SHA-256": confirmed["sha256"]})
        created = str(manifest.get("created_at", ""))[:10]
    else:
        created = ""
    if source_notes:
        checksums = source_notes.get("checksums", {})
        for label, key in [
            ("BACI country codes", "country_codes_sha256"),
            ("BACI product codes", "product_codes_sha256"),
            ("World Bank CMO workbook", "world_bank_workbook_sha256"),
        ]:
            if checksums.get(key):
                prov_rows.append({"Artefact": label, "SHA-256": checksums[key]})
    if prov_rows:
        plain_table(pd.DataFrame(prov_rows))
        if created:
            st.caption(f"Source verification recorded {created}.")
    else:
        st.markdown("Checksum records have not been generated for this run.")
    ledger("source_manifest", "data_source_notes",
           note="figures: reports/figures (pipeline-generated)")
