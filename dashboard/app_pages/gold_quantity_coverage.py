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


# ---- Header: title · coverage mental model · caveat · KPI band ---------------
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])
render_info_banner(copy["mental_model_stamp"], copy["mental_model"], icon="shield-check")
st.markdown(
    f'<div class="queue-interpretation-boundary" role="note">'
    f'{render_icon("info")}<span>{_e(copy["caveat"])}</span></div>',
    unsafe_allow_html=True,
)

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
ledger("panel", note="coverage derived live from the official panel")

# ---- 1 · How much cannot be assessed? ----------------------------------------
s1 = copy["section1"]
section_title(s1["heading"], s1["caption"], icon="chart-pie")
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
st.markdown(
    f'<div class="twin-grid gc-followups">'
    f'<div class="twin-card"><div class="twin-label">{_e(oneoff["kicker"])}</div>'
    f'<div class="gc-card-title">{_e(oneoff["title"].format(route=f"{largest["exporter_name"]} → {largest["importer_name"]}", year=largest["year"]))}</div>'
    f'<p>{_e(oneoff["body"].format(value=fm.compact_usd(largest["value_usd"]), share=f"{largest["share_of_gap_value"]:.1%}", active_years=n_years))}</p>'
    f'<div class="gc-card-action">{_e(oneoff["action"])}</div></div>'
    f'<div class="twin-card response"><div class="twin-label">{_e(repeated["kicker"])}</div>'
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
show(persistent_gap_network(nodes, edges, view, copy["charts"]["network"]),
     height=430, key="gc_network")
st.caption(s3["guardrail"])

network_table = edges.assign(
    route=edges["exporter_name"] + " → " + edges["importer_name"],
    gap_value_usd=edges["gap_value_usd"].map(fm.money),
)[["route", "active_years", "gap_years", "gap_value_usd"]]
with st.container(key="gc_network_table"):
    st.caption(s3["table_intro"])
    plain_table(network_table, column_labels={
        "route": s3["table_columns"]["route"],
        "active_years": s3["table_columns"]["active_years"],
        "gap_years": s3["table_columns"]["gap_years"],
        "gap_value_usd": s3["table_columns"]["gap_value"],
    })

# ---- Closing: the two pathways side by side ----------------------------------
closing = copy["closing"]
section_title(closing["heading"], closing["caption"], icon="checklist")
compare_rows = "".join(
    f'<div class="gc-compare-row"><div>{_e(row["left"])}</div>'
    f'<div>{_e(row["right"])}</div></div>'
    for row in closing["compare"]["rows"]
)
st.markdown(
    f'<div class="gc-compare">'
    f'<div class="gc-compare-head"><div>{_e(closing["compare"]["left_title"])}</div>'
    f'<div>{_e(closing["compare"]["right_title"])}</div></div>'
    f'{compare_rows}</div>',
    unsafe_allow_html=True,
)
_takeaway(closing["statement"])

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

with st.expander(copy["source_label"]):
    st.caption(copy["source_intro"].format(gap_rows=f'{summary["gap_rows"]:,}'))
    export = gc.followup_export(panel)
    preview = export.head(15).assign(
        trade_value_usd=export.head(15)["trade_value_usd"].map(fm.money),
        quantity=str(copy["missing_labels"]["quantity"]),
    )[["obs_id", "source_row_id", "year", "route", "trade_value_usd",
       "quantity", "source_version"]]
    plain_table(preview, column_labels={
        "obs_id": "Observation ID", "source_row_id": "Source row",
        "year": "Year", "route": "Route",
        "trade_value_usd": "Declared value (USD)", "quantity": "Quantity",
        "source_version": "Source version",
    })
    st.download_button(
        copy["export_label"],
        data=export.to_csv(index=False).encode("utf-8"),
        file_name="gold_quantity_followup_queue.csv",
        mime="text/csv", help=copy["export_help"],
        icon=":material/download:",
    )

ledger("panel", "features", note="no gap row is model-eligible")

# Reveal the story sections and charts as they scroll into view.
render_scroll_reveal(
    ".section-heading, .st-key-gc_products_rows, .st-key-gc_products_value, "
    ".st-key-gc_scatter, .st-key-gc_network, .st-key-gc_network_table"
)
