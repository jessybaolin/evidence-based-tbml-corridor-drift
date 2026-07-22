"""Gold Quantity Coverage — the official gold records outside unit-value scoring.

Positioned directly after Model Evaluation & Controls: once the viewer knows how
the Top 50 is built, this page answers the question that leaves behind — which
gold records never reached that assessment because usable quantity was
unavailable. The story runs through three questions on one scrolling page:

  1. How much cannot be assessed?      (row share vs value share, by product)
  2. Large one-offs or repeated gaps?  (materiality vs persistence scatter)
  3. Where do the repeated gaps occur? (persistent-route network)

Every number is derived live from the official panel through
services.gold_coverage (the analysis notebook remains the verified spec); all
copy lives in dashboard_content.yml. Missing quantity is a coverage limitation
handled OUTSIDE the anomaly score — the page never treats it as a signal.
"""

from __future__ import annotations

import html

import streamlit as st

from dashboard.components.banners import render_info_banner
from dashboard.components.cards import kpi_card_markup
from dashboard.components.charts import (
    coverage_share_bars, gap_persistence_scatter, persistent_gap_network, show,
)
from dashboard.components.icons import render_icon
from dashboard.components.page_header import ledger, page_header, section_title
from dashboard.components.scroll_reveal import render_scroll_reveal
from dashboard.components.tables import plain_table
from dashboard.services import data_loader as load
from dashboard.services import formatting as fm
from dashboard.services import gold_coverage as gc

content = load.load_content()
copy = content["pages"]["gold_quantity_coverage"]

# ---- Derived facts (never typed in; the ledger names the backing file) -------
panel = gc.with_gap_flag(load.load_panel(columns=gc.PANEL_COLUMNS))
summary = gc.gold_summary(panel)
products = gc.product_coverage(panel)
corridors = gc.corridor_coverage(panel)
persistence = gc.persistence_summary(corridors)
nodes, edges = gc.persistent_network(corridors)
findings = gc.network_findings(edges)

n_years = len(summary["years"])


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


def _billions(value: float) -> str:
    return f"${value / 1e9:,.3f}B"


def _takeaway(text: str) -> None:
    st.markdown(f'<div class="case-takeaway">{_e(text)}</div>', unsafe_allow_html=True)


def _rule() -> None:
    # Section divider — a hairline with a short accent segment, matching the
    # Business Problem & Value section rule.
    st.markdown('<div class="gc-rule"></div>', unsafe_allow_html=True)


# ---- Header: title · one combined red coverage-boundary banner · KPI band -----
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
# Page marker: lets the CSS scope the generous inter-section spacing to this page.
st.markdown('<span class="gc-page-marker" aria-hidden="true"></span>',
            unsafe_allow_html=True)
render_info_banner(copy["mental_model_stamp"], copy["mental_model"],
                   icon="info", class_name="coverage-boundary")

kpis = copy["kpis"]
tiles = [
    (f'{summary["gap_rows"]:,}', kpis["gap_rows"]["label"],
     kpis["gap_rows"]["detail"].format(gold_rows=f'{summary["gold_rows"]:,}')),
    (f'{summary["gap_row_rate"]:.2%}', kpis["row_rate"]["label"],
     kpis["row_rate"]["detail"]),
    (_billions(summary["gap_value_usd"]), kpis["gap_value"]["label"],
     kpis["gap_value"]["detail"]),
    (f'{summary["gap_value_share"]:.4%}', kpis["value_share"]["label"],
     kpis["value_share"]["detail"]),
]
KPI_ICONS = ["database", "chart-pie", "landmark", "shield-check"]
tiles_html = "".join(
    kpi_card_markup(value, _e(label), detail, icon)
    for (value, label, detail), icon in zip(tiles, KPI_ICONS)
)
st.markdown(f'<div class="stat-band anim">{tiles_html}</div>', unsafe_allow_html=True)
ledger("panel", note="coverage derived live from the official dataset")

# ---- 1 · How much cannot be assessed? ----------------------------------------
s1 = copy["section1"]
section_title(s1["heading"], icon="chart-pie")
_rule()
st.markdown(s1["body"].format(
    gap_rows=f'{summary["gap_rows"]:,}',
    gold_rows=f'{summary["gold_rows"]:,}',
    gap_row_rate=f'{summary["gap_row_rate"]:.2%}',
    gap_value=_billions(summary["gap_value_usd"]),
    gap_value_share=f'{summary["gap_value_share"]:.4%}',
))
rows_col, value_col = st.columns(2, gap="large")
with rows_col:
    st.markdown(f'<div class="chart-subhead">{_e(s1["chart_rows_title"])}</div>',
                unsafe_allow_html=True)
    show(coverage_share_bars(products, "rows", copy["charts"]["products"]),
         height=300, key="gc_products_rows")
with value_col:
    st.markdown(f'<div class="chart-subhead">{_e(s1["chart_value_title"])}</div>',
                unsafe_allow_html=True)
    show(coverage_share_bars(products, "value", copy["charts"]["products"]),
         height=300, key="gc_products_value")
st.caption(s1["note"])
_takeaway(s1["takeaway"])

# ---- 2 · Large one-offs or repeated gaps? ------------------------------------
s2 = copy["section2"]
section_title(s2["heading"], s2["caption"], icon="line-chart")
_rule()
st.markdown(s2["body"])

largest = summary["largest"]
scatter_copy = dict(copy["charts"]["scatter"])
scatter_copy["annotation_largest"] = scatter_copy["annotation_largest"].format(
    share=f'{largest["share_of_gap_value"]:.1%}')
scatter_copy["annotation_persistent"] = scatter_copy["annotation_persistent"].format(
    count=persistence["persistent"],
    value=fm.compact_usd(persistence["persistent_value_usd"]))
show(gap_persistence_scatter(corridors[corridors["gap_years"].gt(0)], scatter_copy),
     height=430, key="gc_scatter")
st.caption(s2["log_note"])

cards = s2["cards"]
oneoff = cards["oneoff"]
repeated = cards["repeated"]
oneoff_route = f'{largest["exporter_name"]} → {largest["importer_name"]}'
oneoff_metric = f'{largest["share_of_gap_value"]:.1%}'
repeated_metric = f'{persistence["persistent"]}'
st.markdown(
    f'<div class="twin-grid gc-followups">'
    f'<div class="twin-card gc-oneoff">'
    f'<div class="gc-card-head">'
    f'<span class="gc-card-icon">{render_icon("file-search")}</span>'
    f'<span class="twin-label">{_e(oneoff["kicker"])}</span>'
    f'<span class="gc-card-metric">{_e(oneoff_metric)}<small>of gap value</small></span></div>'
    f'<div class="gc-card-title">{_e(oneoff["title"].format(route=oneoff_route, year=largest["year"]))}</div>'
    f'<p>{_e(oneoff["body"].format(value=fm.compact_usd(largest["value_usd"]), share=oneoff_metric, active_years=n_years))}</p>'
    f'<div class="gc-card-action">{_e(oneoff["action"])}</div></div>'
    f'<div class="twin-card response gc-repeated">'
    f'<div class="gc-card-head">'
    f'<span class="gc-card-icon">{render_icon("rotate-cw")}</span>'
    f'<span class="twin-label">{_e(repeated["kicker"])}</span>'
    f'<span class="gc-card-metric">{_e(repeated_metric)}<small>corridors</small></span></div>'
    f'<div class="gc-card-title">{_e(repeated["title"].format(count=persistence["persistent"]))}</div>'
    f'<p>{_e(repeated["body"].format(full_history=persistence["full_history"], n_years=n_years, count=persistence["persistent"], value=fm.compact_usd(persistence["persistent_value_usd"]), share=f"{persistence['persistent_value_usd'] / summary['gap_value_usd']:.4%}"))}</p>'
    f'<div class="gc-card-action">{_e(repeated["action"])}</div></div>'
    f'</div>',
    unsafe_allow_html=True,
)
_takeaway(s2["takeaway"])

with st.expander(s2["concentration_label"]):
    st.caption(s2["concentration_intro"].format(
        top10_share=f'{summary["top10_cumulative_share"]:.1%}'))
    concentration = gc.concentration_table(panel)
    concentration = concentration.assign(
        trade_value_usd=concentration["trade_value_usd"].map(fm.money),
        cumulative_share=concentration["cumulative_share"].map(lambda v: f"{v:.1%}"),
    )
    plain_table(concentration, column_labels={
        "obs_id": "Observation ID", "source_row_id": "Source row",
        "year": "Year", "route": "Route",
        "trade_value_usd": "Declared value (USD)",
        "cumulative_share": "Cumulative share of gap value",
    })

with st.expander(s2["persistence_label"]):
    st.caption(s2["persistence_intro"])
    queue = gc.persistence_queue(corridors)
    queue = queue.assign(
        route=queue["exporter_name"] + " → " + queue["importer_name"],
        gap_value_usd=queue["gap_value_usd"].map(fm.money),
    )[["route", "active_years", "gap_years", "gap_value_usd"]]
    plain_table(queue, column_labels={
        "route": "Route", "active_years": "Active years",
        "gap_years": "Years without usable quantity",
        "gap_value_usd": "Declared value (USD)",
    })

# ---- 3 · Where do the repeated gaps occur? -----------------------------------
s3 = copy["section3"]
section_title(s3["heading"], s3["caption"], icon="package")
_rule()
strip_items = s3["finding_strip"].format(
    nld_linked=findings["nld_linked"], persistent=findings["persistent"],
    outbound=findings["nld_outbound"], inbound=findings["nld_inbound"],
    reciprocal=", ".join(findings["reciprocal_partners"]),
).split(" · ")
strip_html = "".join(f'<span class="gc-strip-chip">{_e(item)}</span>'
                     for item in strip_items)
st.markdown(f'<div class="gc-strip">{strip_html}</div>', unsafe_allow_html=True)
st.markdown(s3["body"].format(
    value=fm.compact_usd(findings["value_usd"]),
    share=f'{findings["value_usd"] / summary["gap_value_usd"]:.4%}',
))

VIEW_KEYS = ["all", "nld_outbound", "nld_inbound", "reciprocal", "other"]
view_labels = {key: str(s3["views"][key]) for key in VIEW_KEYS}
picked = st.segmented_control(
    s3["view_label"], [view_labels[k] for k in VIEW_KEYS],
    key="gc_network_view", default=view_labels["all"],
)
view = next((k for k, label in view_labels.items() if label == picked), "all")

# Network on the left (explorable: drag to zoom, pan, reset via the hover mode
# bar) with a country-code reference panel on the right so ISO3 node labels
# resolve to full names at a glance.
graph_col, map_col = st.columns([2.6, 1], gap="medium")
with graph_col:
    show(persistent_gap_network(nodes, edges, view, copy["charts"]["network"]),
         height=460, key="gc_network",
         config={"displaylogo": False,
                 "modeBarButtonsToRemove": ["select2d", "lasso2d"]})
with map_col:
    # Country-code reference in the shared reference-table treatment (navy
    # header, zebra rows), capped so it aligns with the graph rather than
    # dangling into the caption below.
    cmap = nodes.sort_values(["connections", "iso3"], ascending=[False, True])
    cols = s3["country_map_columns"]
    st.markdown(f'<div class="gc-cmap-head">{_e(s3["country_map_label"])}</div>',
                unsafe_allow_html=True)
    plain_table(
        cmap[["iso3", "country", "connections"]],
        column_labels={"iso3": cols["iso3"], "country": cols["country"],
                       "connections": cols["connections"]},
        height=428,
    )
st.caption(s3["network_note"])
st.caption(s3["guardrail"])

with st.expander(s3["table_label"]):
    st.caption(s3["table_intro"])
    network_table = edges.assign(
        route=edges["exporter_name"] + " → " + edges["importer_name"],
        gap_value_usd=edges["gap_value_usd"].map(fm.money),
    )[["route", "active_years", "gap_years", "gap_value_usd"]]
    plain_table(network_table, column_labels={
        "route": s3["table_columns"]["route"],
        "active_years": s3["table_columns"]["active_years"],
        "gap_years": s3["table_columns"]["gap_years"],
        "gap_value_usd": s3["table_columns"]["gap_value"],
    })

# ---- Supporting evidence (kept out of the main flow) -------------------------
with st.expander(copy["trend_label"]):
    st.caption(copy["trend_intro"])
    trend = gc.annual_trend(panel)
    trend = trend.assign(
        gap_row_rate=trend["gap_row_rate"].map(lambda v: f"{v:.2%}"),
        gap_value_usd=trend["gap_value_usd"].map(fm.money),
    )
    plain_table(trend, column_labels={
        "year": copy["trend_columns"]["year"],
        "rows": copy["trend_columns"]["rows"],
        "gap_rows": copy["trend_columns"]["gap_rows"],
        "gap_row_rate": copy["trend_columns"]["gap_rate"],
        "gap_value_usd": copy["trend_columns"]["gap_value"],
    })

ledger("panel", "features", note="no gap row is model-eligible")

# Reveal the story sections and charts as they scroll into view.
render_scroll_reveal(
    ".section-heading, .st-key-gc_products_rows, .st-key-gc_products_value, "
    ".st-key-gc_scatter, .st-key-gc_network"
)
