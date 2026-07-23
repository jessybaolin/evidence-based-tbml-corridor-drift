"""Trade Landscape and Patterns — the reading frame before the review queue.

Part 1 sets the context from the full official panel: scale (value by family)
and market movement (benchmarks). Part 2 profiles the Top 50 review queue before
the queue table. All copy lives in dashboard_content.yml; every number is
derived from the loaded frames, and every chart is built through a
components/charts.py builder.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.charts import (
    bar_by_family, bar_single, small_multiples_by_family, show,
)
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.components.tables import plain_table
from dashboard.services import dashboard_metrics as metrics
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm

content = load.load_content()
copy = content["pages"]["portfolio_analytics"]
short_labels = content["family_short_labels"]
# No title icon: this was the only page in the set whose title carried one.
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

panel = load.load_panel(columns=(
    "obs_id", "year", "family_id", "exporter_iso3", "importer_iso3", "hs6",
    "trade_value_usd", "quantity_metric_ton",
    "benchmark_price_usd_per_metric_ton", "benchmark_residual",
))
queue = load.load_review_queue()
features = load.load_features(columns=(
    "obs_id", "exporter_name", "importer_name", "benchmark_residual", "robust_historical_z",
))
enriched = metrics.enrich_queue(queue, features, short_labels)


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _takeaway(text: str) -> None:
    # One-line, readable takeaway above a chart (skim path).
    st.markdown(f'<div class="case-takeaway">{_e(text)}</div>', unsafe_allow_html=True)


# ---- Objective (skimmable, states what the page is for) ----------------------
st.markdown(f'<div class="why-summary">{_e(copy["objective"])}</div>',
            unsafe_allow_html=True)

# ---- Context strip: derived headline figures ---------------------------------
summary = metrics.landscape_summary(panel, short_labels)
years_text = f"{summary['year_start']}–{summary['year_end']}"
strip = copy["strip"]
tiles = [
    (f"${summary['total_value'] / 1e12:.1f}T", strip["value_label"],
     strip["value_detail"].format(years=years_text), "acc-teal"),
    (f"{summary['dominant_share']:.0f}%",
     strip["dominant_label"].format(family=summary["dominant_family_label"]),
     strip["dominant_detail"], "acc-amber"),
    (f"{summary['n_families']}", strip["families_label"],
     strip["families_detail"], "acc-blue"),
    (f"{summary['n_corridors']:,}", strip["corridors_label"],
     strip["corridors_detail"], "acc-green"),
]
strip_html = "".join(
    f'<div class="stat-tile {accent}"><div class="stat-value">{_e(value)}</div>'
    f'<div class="stat-label">{_e(label)}</div>'
    f'<div class="stat-detail">{_e(detail)}</div></div>'
    for value, label, detail, accent in tiles
)
st.markdown(f'<div class="stat-band four">{strip_html}</div>', unsafe_allow_html=True)

# =============================================================================
# PART 1 — THE TRADE LANDSCAPE (the full official population)
# The section divider is intentionally dropped: the page title (with the
# landmark icon) already names this half, so the three cards start straight away.
# =============================================================================
scale_frame = metrics.trade_scale_by_family_year(panel, short_labels)

# Each landscape section is a subtle card (styles.py .st-key-pa_card_*) that
# lifts off the plane and fades up on entrance, so Scale / Market / Queue Profile
# read as distinct blocks while scrolling.

# ---- 4.1 Scale (with a value / quantity toggle) ------------------------------
with st.container(key="pa_card_scale"):
    sc = copy["scale"]
    head_col, toggle_col = st.columns([3, 1.1], vertical_alignment="bottom")
    with head_col:
        section_title(sc["heading"], icon="chart-pie")
    with toggle_col:
        _MODE_KEY = "pa_scale_mode"
        st.session_state.setdefault(_MODE_KEY, sc["toggle_value"])
        mode = st.segmented_control(
            sc["toggle_label"], [sc["toggle_value"], sc["toggle_quantity"]],
            key=_MODE_KEY, label_visibility="collapsed",
        ) or sc["toggle_value"]
    if mode == sc["toggle_quantity"]:
        _takeaway(sc["takeaway_quantity"])
        show(small_multiples_by_family(scale_frame, "quantity_metric_ton",
                                       hover_label=sc["y_quantity"],
                                       y_title=sc["y_quantity"],
                                       hover_values=scale_frame["quantity_metric_ton"].map(
                                           fm.quantity_mt)),
             key="pa_scale_small_multiples")
    else:
        _takeaway(sc["takeaway_value"].format(
            family=summary["dominant_family_label"], share=f"{summary['dominant_share']:.0f}"))
        show(small_multiples_by_family(scale_frame, "trade_value_usd",
                                       hover_label=sc["y_value"],
                                       y_title=sc["y_value"],
                                       hover_values=scale_frame["trade_value_usd"].map(
                                           fm.compact_usd)),
             key="pa_scale_small_multiples")
    st.caption(sc["caption"])

    table_copy = sc["table"]
    table_columns = table_copy["columns"]
    scale_table = (
        scale_frame[["year", "family_label", "trade_value_usd", "quantity_metric_ton"]]
        .rename(columns={
            "year": table_columns["year"],
            "family_label": table_columns["family"],
            "trade_value_usd": table_columns["trade_value"],
            "quantity_metric_ton": table_columns["quantity"],
        })
        .sort_values([table_columns["year"], table_columns["family"]],
                     ascending=[False, True])
        .reset_index(drop=True)
    )
    with st.expander(table_copy["label"], expanded=False):
        st.caption(table_copy["caption"])
        plain_table(
            scale_table,
            height=390,
            formatters={
                table_columns["year"]: lambda value: f"{int(value)}",
                table_columns["trade_value"]: lambda value: fm.money(value, 2),
                table_columns["quantity"]: lambda value: f"{float(value):,.3f}",
            },
        )
        st.download_button(
            table_copy["download_label"],
            data=scale_table.to_csv(index=False).encode("utf-8"),
            file_name="trade_scale_by_family_year.csv",
            mime="text/csv",
            help=table_copy["download_help"],
            icon=":material/download:",
            key="pa_scale_table_download",
        )
    ledger("panel")

# ---- 4.2 Market context: benchmarks moved ------------------------------------
with st.container(key="pa_card_market"):
    mk = copy["market"]
    section_title(mk["heading"], icon="line-chart")
    _takeaway(mk["takeaway"])
    benchmark_frame = metrics.benchmark_by_family_year(panel, short_labels)
    show(small_multiples_by_family(benchmark_frame,
                                   "benchmark", hover_label=mk["y_benchmark"],
                                   y_title=mk["y_benchmark"],
                                   hover_values=benchmark_frame["benchmark"].map(
                                       lambda value: f"{fm.money(value)}/mt")),
         key="pa_benchmark_small_multiples")
    st.caption(mk["caption"])
    ledger("panel")

# =============================================================================
# PART 2 — PROFILE OF THE TOP 50 REVIEW QUEUE (the queue's shape, trimmed)
# Wrapped in the same subtle card as the landscape sections, so it reads as one
# more distinct block rather than floating on the plane below them.
# =============================================================================
with st.container(key="pa_card_patterns"):
    section_title(copy["patterns_heading"], icon="checklist")
    _takeaway(copy["patterns_intro"])

    p1, p2 = st.columns(2, gap="large")
    with p1:
        by_year = metrics.candidates_by_year(enriched)
        top_year = by_year.loc[by_year["candidates"].idxmax()]
        section_title(
            copy["by_year"]["heading"],
            copy["by_year"]["caption"].format(
                year=int(top_year["year"]), n=int(top_year["candidates"]),
                total=int(by_year["candidates"].sum())),
            icon="calendar",
        )
        show(bar_single(by_year, x="year", y="candidates", y_title=copy["by_year"]["y"]),
             key="pa_candidates_by_year")
    with p2:
        section_title(copy["by_family"]["heading"], copy["by_family"]["caption"], icon="package")
        show(bar_by_family(metrics.candidates_by_family(enriched), x="family_label",
                           y="candidates", y_title=copy["by_family"]["y"]),
             key="pa_candidates_by_family")
    ledger("review_queue")

# Reveal each landscape section as it scrolls into view.
render_scroll_reveal(
    ".st-key-pa_card_scale, .st-key-pa_card_market, .st-key-pa_card_patterns"
)
