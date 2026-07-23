"""Selected Case Review — one selected official observation, in depth.

Header: one compact amber selected-case strip (facts · score · the change-case
control) instead of the old KPI cards. Case Summary: a Case facts
panel (35%) beside a three-view comparison carousel (65%) — market comparison,
own history, peer position — each with a Chart|Table mode, all driven by the
pure frames in services/case_summary.py so a chart and its table can never
disagree. A runtime consistency gate (validate_case_view) recomputes every
displayed identity and value; if anything disagrees with the published
artefacts the page shows a governed error state instead of numbers.
"""

from __future__ import annotations

import html
import re

import pandas as pd
import streamlit as st

from dashboard.components.cards import comparison_card_markup, render_fact_list
from dashboard.components.charts import (
    case_combined_view, case_peer_view, case_view_height, show,
)
from dashboard.components.empty_states import render_empty_state
from dashboard.components.icons import render_icon
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.components.status_badges import quality_pill
from dashboard.components.tables import plain_table
from dashboard.services import case_summary as case
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm
from dashboard.services import session_state as state
from dashboard.services import why_ranked_high as wrh

content = load.load_content()
copy = content["pages"]["case_investigation"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

queue = load.load_review_queue().sort_values("rank")
features = load.load_features()
evidence = load.load_evidence()
panel = load.load_panel(columns=case.PEER_PANEL_COLUMNS)
short_labels = content["family_short_labels"]


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _tip(inner_html: str, tip: str) -> str:
    # CSS-only tooltip (styles.py .tip): opens on hover and keyboard focus.
    return f'<span class="tip" tabindex="0" data-tip="{_e(tip)}">{inner_html}</span>'


def _na(value, formatter) -> str:
    # NA-safe display cell: missing analytical values show an em dash, never 0.
    return "—" if value is None or pd.isna(value) else formatter(value)


def _view_heading(title: str, icon: str) -> None:
    # Comparison-view heading with the word "corridor" highlighted and carrying
    # an on-hover definition — the corridor is the unit this page reviews.
    label = re.sub(
        r"(?i)corridors?",
        lambda m: (f'<span class="tip corridor-term" tabindex="0" '
                   f'data-tip="{_e(copy["corridor_tip"])}">{m.group(0)}</span>'),
        _e(title),
    )
    st.markdown(
        f'<div class="section-heading">{render_icon(icon, class_name="section-icon")}'
        f'<div><div class="section-label">{label}</div></div></div>',
        unsafe_allow_html=True,
    )


# ---- Selected-case strip: facts · score · quality · change case --------------
# The selectbox stays the page's FIRST (and only) selectbox and keeps writing
# the raw obs_id to session state — the shared contract with the Review Queue.
labels = {
    row.obs_id: (
        f"#{int(row.rank)} · {int(row.year)} · {row.exporter_iso3} → {row.importer_iso3} · "
        f"{short_labels.get(row.family_id, row.product_name)}"
    )
    for row in queue.itertuples()
}
ids = list(labels)
carried = state.selected_obs_id()
initial_index = ids.index(carried) if carried in ids else 0

with st.container(key="case_strip"):
    # Two cells: the case identity and the control that changes it. The
    # review-priority score moved into the Case facts list, directly under the
    # review rank it follows from.
    facts_col, change_col = st.columns(
        [4.95, 1.85], vertical_alignment="center", gap="medium"
    )
    # The selector renders in the rightmost column but must EXECUTE first so the
    # facts cell on its left describes the case picked on this rerun.
    with change_col:
        st.markdown(
            f'<div class="case-strip-label">{_e(copy["selector_label"])}</div>',
            unsafe_allow_html=True,
        )
        selected_id = st.selectbox(
            copy["selector_label"], ids, index=initial_index,
            format_func=lambda obs: labels[obs],
            help=copy["selector_help"], label_visibility="collapsed",
        )
    state.select_obs(selected_id)

    record = metrics.case_record(selected_id, queue, features)
    if record is None:
        render_empty_state(copy["not_in_queue"], level="warning")
        st.stop()

    # Consistency gate: recompute every displayed identity/value against the
    # published artefacts. Any disagreement -> governed error, no numbers.
    violations = case.validate_case_view(selected_id, queue, features, panel)
    if violations:
        render_empty_state(
            copy["validation_error"].format(reason=violations[0]), level="warning"
        )
        st.stop()

    case_year = int(record["year"])
    family_id = str(record["family_id"])
    case_multiple = float(record["unit_value_usd_per_metric_ton"]) / float(
        record["benchmark_price_usd_per_metric_ton"]
    )

    with facts_col:
        st.markdown(
            f'<div class="case-strip-facts"><strong>#{int(record["rank"])}</strong>'
            f" · {case_year} · {_e(record['exporter_iso3'])} → {_e(record['importer_iso3'])}"
            f" · {_e(short_labels.get(family_id, record['product_name']))}"
            f" · HS6 {_e(record['hs6'])}</div>",
            unsafe_allow_html=True,
        )

case_evidence = metrics.case_evidence(evidence, selected_id)

# ---- The comparison frames: one prepared source per view (charts AND tables) --
series = case.corridor_series(
    features, record["exporter_iso3"], record["importer_iso3"], record["hs6"]
)
market = case.market_comparison_frame(series, case_year)
own = case.own_history_frame(series, case_year)
position = case.peer_position(panel, family_id, case_year, selected_id)

summary_tab, why_tab, limits_tab = st.tabs([str(t) for t in copy["tabs"]])

# ---- Tab 1: Case Summary ------------------------------------------------------
with summary_tab:
    views = copy["views"]
    VIEW_LABELS = [str(v) for v in views["labels"]]
    MODE_LABELS = [str(views["mode_chart"]), str(views["mode_table"])]
    _VIEW_IDX = "case_view_idx"
    _VIEW_BAR = "case_view_bar"

    if _VIEW_IDX not in st.session_state:
        st.session_state[_VIEW_IDX] = 0
    st.session_state[_VIEW_IDX] = max(
        0, min(len(VIEW_LABELS) - 1, int(st.session_state[_VIEW_IDX]))
    )
    st.session_state.setdefault(_VIEW_BAR, VIEW_LABELS[st.session_state[_VIEW_IDX]])

    def _on_view_bar() -> None:
        label = st.session_state.get(_VIEW_BAR)
        if label is None:
            # segmented_control allows deselection; keep the current view.
            st.session_state[_VIEW_BAR] = VIEW_LABELS[int(st.session_state[_VIEW_IDX])]
            return
        st.session_state[_VIEW_IDX] = VIEW_LABELS.index(label)

    def _mode_control(view_idx: int) -> str:
        # Chart|Table applies to the CURRENT view only: one key per view,
        # so toggling one view never flips another.
        key = f"case_view_mode_{view_idx}"
        st.session_state.setdefault(key, MODE_LABELS[0])

        def _restore() -> None:
            if st.session_state.get(key) is None:
                st.session_state[key] = MODE_LABELS[0]

        choice = st.segmented_control(
            str(views["mode_label"]), MODE_LABELS, key=key, on_change=_restore,
            label_visibility="collapsed",
        )
        return choice or MODE_LABELS[0]

    def _takeaway(text: str) -> None:
        st.markdown(f'<div class="case-takeaway">{_e(text)}</div>',
                    unsafe_allow_html=True)

    # Comparison-view switcher, above the two columns so Case facts (left) and the
    # comparison heading (right) start at the same height. This direct tab control
    # replaces the old prev/next stepper and its "n of 3" counter — the tabs alone
    # already show and switch every view.
    st.segmented_control(
        str(views["selector_label"]), VIEW_LABELS, key=_VIEW_BAR,
        on_change=_on_view_bar, label_visibility="collapsed",
    )
    view_idx = int(st.session_state[_VIEW_IDX])

    left, right = st.columns([35, 65], gap="large")

    with left:
        facts = copy["facts"]
        section_title(facts["heading"], icon="file-text")
        exporter = record.get("exporter_name")
        importer = record.get("importer_name")
        exporter = exporter if pd.notna(exporter) else record["exporter_iso3"]
        importer = importer if pd.notna(importer) else record["importer_iso3"]
        implied_label = _tip(
            f'{_e(facts["implied_uv"])} {render_icon("info")}', facts["implied_uv_tip"]
        )
        # Unit-value-vs-benchmark carries the valid-extreme note on hover (only
        # when this observation IS an extreme retained as valid), so the caveat
        # sits on the metric it explains rather than as a loose footnote.
        vs_benchmark_label = _e(facts["vs_benchmark"])
        if record.get("valid_extreme_flag"):
            vs_benchmark_label = _tip(
                f'{_e(facts["vs_benchmark"])} {render_icon("info")}',
                facts["valid_extreme_note"],
            )
        # Data quality carries the caveat specific to this observation on hover:
        # the benchmark comparability note when present, else the general note.
        benchmark_caveat = record.get("benchmark_caveat")
        quality_caveat = (
            str(benchmark_caveat)
            if benchmark_caveat and pd.notna(benchmark_caveat)
            else copy["strip"]["quality_tip"]
        )
        quality_value = (
            f'{quality_pill(record["quality_status"])} '
            f'{_tip(render_icon("info"), quality_caveat)}'
        )
        # The score follows the review rank because it is what produced it.
        score_label = _tip(
            f'{_e(facts["score"])} {render_icon("info")}', facts["score_tip"]
        )
        multiple_1dp = f"{case_multiple:.1f}"
        render_fact_list([
            (_e(facts["rank"]), f"#{int(record['rank'])}"),
            (score_label, _e(fm.score(record["selected_review_priority_score"]))),
            (_e(facts["year"]), str(case_year)),
            (_e(facts["corridor"]),
             f"{_e(exporter)} ({_e(record['exporter_iso3'])}) → "
             f"{_e(importer)} ({_e(record['importer_iso3'])})"),
            (_e(facts["product"]),
             f"{_e(record['product_name'])} · HS6 {_e(record['hs6'])}"),
            (_e(facts["trade_value"]), _e(fm.money(record["trade_value_usd"]))),
            (_e(facts["quantity"]), _e(fm.quantity_mt(record["quantity_metric_ton"]))),
            (implied_label,
             _e(fm.money(record["unit_value_usd_per_metric_ton"]) + " / mt")),
            (_e(facts["benchmark"]),
             _e(fm.money(record["benchmark_price_usd_per_metric_ton"]) + " / mt")),
            (vs_benchmark_label,
             _e(facts["vs_benchmark_value"].format(multiple=multiple_1dp))),
            (_e(facts["quality"]), quality_value),
        ])
        ledger("review_queue", "features", "panel")

    with right:
        if view_idx == 0:
            # ---- View 1 · Combined: vs the market AND vs its own history ----
            vw = views["combined"]
            # Heading left, Chart|Table toggle in the top-right corner; the
            # takeaway then runs full width beneath them.
            head_col, mode_col = st.columns([3.4, 1], vertical_alignment="center")
            with head_col:
                _view_heading(str(vw["title"]), "line-chart")
            with mode_col:
                mode = _mode_control(0)
            case_m = market.loc[market["year"] == case_year].iloc[0]
            case_o = own.loc[own["year"] == case_year].iloc[0]
            if pd.isna(case_m["multiple"]):
                _takeaway(vw["takeaway_unavailable"])
            elif pd.notna(case_o["multiple_vs_prior"]):
                _takeaway(vw["takeaway"].format(
                    year=case_year,
                    market_multiple=f"{case_m['multiple']:.1f}",
                    history_multiple=f"{case_o['multiple_vs_prior']:.1f}",
                    prior_years=int(case_o["prior_years_used"])))
            else:
                _takeaway(vw["takeaway_market_only"].format(
                    year=case_year, market_multiple=f"{case_m['multiple']:.1f}"))
            if mode == MODE_LABELS[0]:
                show(case_combined_view(market, own, vw),
                     height=case_view_height(), key="case_view_combined")
            else:
                obs = market[market["observed"]].merge(
                    own[own["observed"]][["year", "prior_median", "multiple_vs_prior"]],
                    on="year", how="left")
                ct = vw["table"]
                plain_table(pd.DataFrame({
                    ct["year"]: obs["year"].astype(int).astype(str),
                    ct["implied_uv"]: obs["unit_value"].map(lambda v: _na(v, fm.money)),
                    ct["benchmark"]: obs["benchmark"].map(lambda v: _na(v, fm.money)),
                    ct["market_multiple"]: obs["multiple"].map(
                        lambda v: _na(v, lambda x: f"{x:,.2f}×")),
                    ct["prior_median"]: obs["prior_median"].map(
                        lambda v: _na(v, fm.money)),
                    ct["history_multiple"]: obs["multiple_vs_prior"].map(
                        lambda v: _na(v, lambda x: f"{x:,.2f}×")),
                }))
            st.caption(str(vw["note"]))

        else:
            # ---- View 2 · Peer position ------------------------------------
            vw = views["peers"]
            if position is None:
                _view_heading(str(vw["title"]), "list-ordered")
                render_empty_state(str(vw["takeaway_unavailable"]), level="warning")
            else:
                # Heading left, Chart|Table toggle in the top-right corner; the
                # takeaway then runs full width beneath them.
                head_col, mode_col = st.columns([3.4, 1], vertical_alignment="center")
                with head_col:
                    _view_heading(str(vw["title"]), "list-ordered")
                with mode_col:
                    mode = _mode_control(1)
                _takeaway(vw["takeaway"].format(
                    percentile=f"{position['percentile']:.1%}",
                    peers=f"{position['peer_count']:,}", year=case_year))
                if mode == MODE_LABELS[0]:
                    show(case_peer_view(position, vw),
                         height=case_view_height(), key="case_view_peers")
                else:
                    pt = vw["table"]
                    plain_table(pd.DataFrame({
                        pt["measure"]: [
                            pt["case_multiple"], pt["case_percentile"],
                            pt["peer_count"], pt["median_multiple"],
                            pt["p95_multiple"], pt["at_or_above_3x"],
                        ],
                        pt["value"]: [
                            f"{position['case_ratio']:,.2f}×",
                            f"{position['percentile']:.1%}",
                            f"{position['peer_count']:,}",
                            f"{position['median_multiple']:,.2f}×",
                            f"{position['p95_multiple']:,.2f}×",
                            f"{position['peers_at_or_above_3x']:,}",
                        ],
                    }))
                st.caption(vw["population_note"].format(
                    year=case_year, peers=f"{position['peer_count']:,}",
                    family=short_labels.get(family_id, record["product_name"])))
                if position["n_outside"]:
                    st.caption(vw["outside_note"].format(n=position["n_outside"]))

# ---- Tab 2: Why It Ranked High (plain-English reasons + comparison cards) -----
with why_tab:
    why = copy["why"]

    def _signal_value(kind: str, number, raw) -> str:
        # The numeric token for the Case-result column; interpretation is joined
        # by the caller. Every log field is already exp()'d in signal_number.
        if number is None:
            return str(why["value_missing"])
        if kind == "log_multiple":
            return str(why["value_multiple"]).format(multiple=f"{number:.1f}").strip()
        if kind == "percentile":
            return str(why["value_percentile"]).format(
                value=wrh.percentile_ordinal(number))
        if kind == "zscore":
            direction = why["direction_above"] if number >= 0 else why["direction_below"]
            return str(why["value_zscore"]).format(
                z=f"{abs(number):.1f}", direction=direction)
        if kind == "count":
            return str(why["value_count"]).format(n=int(number))
        if kind == "flag":
            return str(why["value_flag_yes"] if number >= 0.5 else why["value_flag_no"])
        return str(why["value_magnitude"]).format(value=f"{number:.2f}")

    section_title(why["heading"], icon="file-search")

    # 1) Dynamic ranking summary — only the case's flagged evidence types appear.
    #    The governed "reasons, not a finding" note rides INSIDE the banner.
    clause_keys = wrh.summary_clause_keys(record, case_evidence)
    clauses = [str(why["summary_clauses"][k]) for k in clause_keys
               if k in why["summary_clauses"]]
    if clauses:
        if len(clauses) == 1:
            body = clauses[0]
        else:
            body = (str(why["summary_join"]).join(clauses[:-1])
                    + str(why["summary_final_join"]) + clauses[-1])
        summary_text = str(why["summary_prefix"]) + body + str(why["summary_suffix"])
    else:
        summary_text = str(why["summary_empty"])
    st.markdown(
        f'<div class="why-summary anim">{_e(summary_text)}'
        f'<div class="why-summary-note">{_e(why["summary_note"])}</div></div>',
        unsafe_allow_html=True,
    )

    # 2) Four comparison cards (2x2), each a distinct accent colour and staggered
    #    entrance. Each shows the real per-case value; a card shows its data-absence
    #    line only when the feature is genuinely missing.
    section_title(why["cards_heading"], icon="sliders")
    cards_meta = wrh.card_metrics(record)
    card_copy = why["cards"]
    with st.container(key="why_cards"):
        grid = [st.columns(2, gap="medium"), st.columns(2, gap="medium")]
        cells = [grid[0][0], grid[0][1], grid[1][0], grid[1][1]]
        for i, (meta, cell) in enumerate(zip(cards_meta, cells)):
            c = card_copy[meta["slot"]]
            caveat_tip = _tip(render_icon("info"), c["caveat"])
            anim_cls = f"anim d{i + 1}"
            with cell:
                if not meta["available"]:
                    st.markdown(
                        comparison_card_markup(
                            title=c["title"], value_html=_e(c["unavailable"]),
                            support="", caveat_tip_html=caveat_tip, available=False,
                            extra_classes=anim_cls),
                        unsafe_allow_html=True,
                    )
                    continue
                magnitude = meta["magnitude"]
                secondary_html = ""
                if meta["slot"] == "C":
                    template = c["value_increase"] if meta["direction"] == "above" \
                        else c["value_decrease"]
                    value_html = _e(str(template))
                    dir_word = c["direction_above"] if meta["direction"] == "above" \
                        else c["direction_below"]
                    secondary_html = _e(str(c["secondary"]).format(
                        z=f"{magnitude:.1f}", direction=dir_word))
                    result_str = f"{magnitude:.1f} robust deviations {dir_word} prior history"
                else:
                    if meta["slot"] == "B":
                        template = c["value_increase"] if meta["direction"] == "above" \
                            else c["value_decrease"]
                    else:  # A, D — change direction
                        template = c["value_increase"] if meta["direction"] == "increase" \
                            else c["value_decrease"]
                    value_html = _e(str(template).format(multiple=f"{magnitude:.1f}"))
                    result_str = f"{magnitude:.2f}×"
                st.markdown(
                    comparison_card_markup(
                        title=c["title"], value_html=value_html, support=c["support"],
                        caveat_tip_html=caveat_tip, secondary_html=secondary_html,
                        extra_classes=f"compare-card-{meta['slot'].lower()} {anim_cls}"),
                    unsafe_allow_html=True,
                )
                with st.expander(why["how_calculated_label"]):
                    st.markdown(
                        f"**{why['how_result_label']}:** {result_str}  \n"
                        f"**{why['how_metric_label']}:** `{c['metric']}`  \n"
                        f"**{why['how_comparison_label']}:** {c['comparison']}  \n"
                        f"**{why['how_derivation_label']}:** {c['derivation']}  \n"
                        f"{c['caveat']}"
                    )

    # 3) Full analytical signal profile (collapsed). Custom table: monospace
    #    technical field names, native-title tooltips on labels, sticky header.
    with st.expander(why["signals_heading"]):
        st.caption(why["signals_description"])
        profile = wrh.signal_profile(record)
        sig_cols = why["signals_columns"]
        sig_meta = why["signals"]
        rows_html = []
        for row in profile:
            field = row["field"]
            meta = sig_meta.get(field)
            if meta is None:  # display-label mapping must cover every rendered signal
                continue
            token = _signal_value(row["kind"], row["number"], row["raw"])
            if row["kind"] == "flag" or row["number"] is None:
                case_result = token
            else:
                case_result = f"{token} — {meta['interpretation']}"
            rows_html.append(
                f'<tr><td class="mono">{_e(field)}</td>'
                f'<td title="{_e(meta["tooltip"])}">{_e(meta["label"])}</td>'
                f'<td>{_e(case_result)}</td>'
                f'<td>{_e(meta["derived"])}</td>'
                f'<td>{_e(meta["time_safety"])}</td></tr>'
            )
        if rows_html:
            header = "".join(
                f"<th>{_e(sig_cols[k])}</th>"
                for k in ("field", "label", "result", "derived", "time_safety")
            )
            st.markdown(
                f'<div class="data-table-wrap signals-scroll">'
                f'<table class="data-table zebra"><thead><tr>{header}</tr></thead>'
                f'<tbody>{"".join(rows_html)}</tbody></table></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info(why["signals_empty"])

    ledger("evidence", "features")

# ---- Tab 3: Caveats -----------------------------------------------------------
def _caveat_card(icon: str, accent_class: str, heading: str, intro: str,
                 bullets: list[str], delay: str) -> None:
    # One category of caveats in a white, bordered card: coloured icon + heading,
    # a plain intro line, then the bullets. anim gives a staggered entrance.
    items = "".join(f"<li>{_e(b)}</li>" for b in bullets)
    st.markdown(
        f'<div class="caveat-card {accent_class} anim {delay}">'
        f'<div class="caveat-head">{render_icon(icon, class_name="caveat-icon")}'
        f'<span>{_e(heading)}</span></div>'
        f'<div class="caveat-intro">{_e(intro)}</div>'
        f'<ul class="caveat-list">{items}</ul></div>',
        unsafe_allow_html=True,
    )


with limits_tab:
    lim = copy["limitations"]
    case_caveats = (
        case_evidence["caveat"].dropna().unique().tolist()
        if not case_evidence.empty else []
    )
    if record.get("benchmark_caveat") and pd.notna(record.get("benchmark_caveat")):
        case_caveats.append(str(record["benchmark_caveat"]))
    case_caveats = list(dict.fromkeys(case_caveats)) or [lim["no_caveats"]]
    _caveat_card("file-search", "caveat-card-case", lim["case_heading"],
                 lim["case_intro"], case_caveats, "d1")

    project_bullets = list(content["limitations"]) + [
        f"{copy['caveat']} {lim['closing_suffix']}"
    ]
    _caveat_card("shield-check", "caveat-card-project", lim["project_heading"],
                 lim["project_intro"], project_bullets, "d2")

# Reveal the case summary strip and each section heading as it scrolls into view.
render_scroll_reveal(".section-heading, .st-key-case_strip, .st-key-why_cards")
