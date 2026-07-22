"""Gold Quantity Coverage — the official gold records outside unit-value scoring.

Positioned directly after Model Evaluation & Controls: once the viewer knows how
the Top 50 is built, this page answers the question that leaves behind — which
gold records never reached that assessment because usable quantity was
unavailable. The story runs through three questions on one scrolling page:

  1. Is the blind spot material?        (row share vs value share, by product)
  2. Is it isolated or systematic?     (one large row vs an eight-year pattern)
  3. Where does the repeat pattern sit? (route network)

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
from dashboard.components.charts import coverage_share_bars, persistent_gap_network, show
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
render_info_banner(
    copy["mental_model_stamp"].format(
        gap_value_share=f'{summary["gap_value_share"]:.4%}',
    ),
    copy["mental_model"].format(
        gap_row_rate=f'{summary["gap_row_rate"]:.2%}',
        gap_value_share=f'{summary["gap_value_share"]:.4%}',
    ),
    icon="info",
    class_name="coverage-boundary",
)

kpis = copy["kpis"]
tiles = [
    (f'{summary["gap_row_rate"]:.2%}', kpis["row_gap"]["label"],
     kpis["row_gap"]["detail"].format(
         gap_rows=f'{summary["gap_rows"]:,}', gold_rows=f'{summary["gold_rows"]:,}'),
     "database", "gc-kpi-frequency"),
    (f'{summary["assessable_value_share"]:.4%}', kpis["value_coverage"]["label"],
     kpis["value_coverage"]["detail"].format(
         gap_value_share=f'{summary["gap_value_share"]:.4%}'),
     "shield-check", "gc-kpi-coverage"),
    (f'{persistence["persistent"]}', kpis["repeat_routes"]["label"],
     kpis["repeat_routes"]["detail"].format(n_years=n_years),
     "rotate-cw", "gc-kpi-pattern"),
]
tiles_html = "".join(
    kpi_card_markup(value, _e(label), detail, icon, extra_classes=extra_class)
    for value, label, detail, icon, extra_class in tiles
)
st.markdown(f'<div class="stat-band three anim">{tiles_html}</div>', unsafe_allow_html=True)
ledger("panel", note="coverage derived live from the official dataset")

# ---- 1 · Is the blind spot material? ----------------------------------------
s1 = copy["section1"]
section_title(s1["heading"], icon="chart-pie")
_rule()
st.markdown(s1["body"].format(
    gap_rows=f'{summary["gap_rows"]:,}',
    gold_rows=f'{summary["gold_rows"]:,}',
    gap_row_rate=f'{summary["gap_row_rate"]:.2%}',
    gap_value=_billions(summary["gap_value_usd"]),
    gap_value_share=f'{summary["gap_value_share"]:.4%}',
    assessable_value_share=f'{summary["assessable_value_share"]:.4%}',
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
_takeaway(s1["takeaway"].format(
    assessable_value_share=f'{summary["assessable_value_share"]:.4%}',
))

# ---- 2 · Is the blind spot isolated or systematic? -------------------------
s2 = copy["section2"]
section_title(s2["heading"], s2["caption"], icon="line-chart")
_rule()
st.markdown(s2["body"].format(
    affected=f'{persistence["affected"]:,}',
    full_history=f'{persistence["full_history"]:,}',
    persistent=persistence["persistent"],
    n_years=n_years,
))

largest = summary["largest"]

cards = s2["cards"]
oneoff = cards["oneoff"]
repeated = cards["repeated"]
oneoff_route = f'{largest["exporter_name"]} → {largest["importer_name"]}'
oneoff_metric = f'{largest["share_of_gap_value"]:.1%}'
repeated_metric = f'{persistence["persistent"]}'
repeated_gap_share = persistence["persistent_value_usd"] / summary["gap_value_usd"]
gold_value_usd = summary["gap_value_usd"] / summary["gap_value_share"]
repeated_gold_share = persistence["persistent_value_usd"] / gold_value_usd
st.markdown(
    f'<div class="twin-grid gc-followups">'
    f'<div class="twin-card gc-oneoff">'
    f'<div class="gc-card-head">'
    f'<span class="gc-card-icon">{render_icon("file-search")}</span>'
    f'<span class="twin-label">{_e(oneoff["kicker"])}</span>'
    f'<span class="gc-card-metric">{_e(oneoff_metric)}<small>of gap value</small></span></div>'
    f'<div class="gc-card-title">{_e(oneoff["title"].format(route=oneoff_route, year=largest["year"]))}</div>'
    f'<p>{_e(oneoff["body"].format(value=fm.compact_usd(largest["value_usd"]), share=oneoff_metric, active_years=n_years, other_years=n_years - 1, gold_share=f"{largest["share_of_gold_value"]:.4%}"))}</p>'
    f'<div class="gc-card-action">{_e(oneoff["action"])}</div></div>'
    f'<div class="twin-card response gc-repeated">'
    f'<div class="gc-card-head">'
    f'<span class="gc-card-icon">{render_icon("rotate-cw")}</span>'
    f'<span class="twin-label">{_e(repeated["kicker"])} '
    f'<span class="tip gc-definition-tip" tabindex="0" role="note" '
    f'data-tip="{_e(repeated["definition"])}">{render_icon("info")}</span></span>'
    f'<span class="gc-card-metric">{_e(repeated_metric)}<small>corridors</small></span></div>'
    f'<div class="gc-card-title">{_e(repeated["title"].format(count=persistence["persistent"]))}</div>'
    f'<p>{_e(repeated["body"].format(full_history=persistence["full_history"], n_years=n_years, count=persistence["persistent"], value=fm.compact_usd(persistence["persistent_value_usd"]), share=f"{repeated_gap_share:.4%}", gold_share=f"{repeated_gold_share:.6%}"))}</p>'
    f'<div class="gc-card-action">{_e(repeated["action"])}</div></div>'
    f'</div>',
    unsafe_allow_html=True,
)
_takeaway(s2["takeaway"].format(
    gap_value=_billions(summary["gap_value_usd"]),
))

# ---- 3 · Where does the repeat pattern sit? ---------------------------------
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
view_counts = {
    "persistent": findings["persistent"],
    "outbound": findings["nld_outbound"],
    "inbound": findings["nld_inbound"],
    "reciprocal_routes": int(edges["reciprocal"].sum()),
    "other": int(edges["category"].eq("other").sum()),
}
view_labels = {
    key: str(s3["views"][key]).format(**view_counts) for key in VIEW_KEYS
}
picked = st.segmented_control(
    s3["view_label"], [view_labels[k] for k in VIEW_KEYS],
    key="gc_network_view", default=view_labels["all"],
)
view = next((k for k, label in view_labels.items() if label == picked), "all")
size_guide = s3["size_guide"]
st.markdown(
    f'<div class="gc-size-guide">'
    f'<span class="gc-size-label">{_e(size_guide["label"])}</span>'
    f'<span class="gc-size-item"><i class="gc-bubble one"></i>{_e(size_guide["one"])}</span>'
    f'<span class="gc-size-item"><i class="gc-bubble two"></i>{_e(size_guide["two"])}</span>'
    f'<span class="gc-size-item"><i class="gc-bubble twelve"></i>{_e(size_guide["twelve"])}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Network on the left (explorable: drag to zoom, pan, reset via the hover mode
# bar) with a country-code reference panel on the right so ISO3 node labels
# resolve to full names at a glance.
graph_col, map_col = st.columns([2.25, 1.35], gap="medium")
with graph_col:
    show(persistent_gap_network(nodes, edges, view, copy["charts"]["network"]),
         height=520, key="gc_network",
         config={"displaylogo": False,
                 "modeBarButtonsToRemove": ["select2d", "lasso2d"]})
with map_col:
    # Country-code reference in the shared reference-table treatment (navy
    # header, zebra rows), capped so it aligns with the graph rather than
    # dangling into the caption below.
    with st.container(key="gc_country_map"):
        cmap = nodes.sort_values(["connections", "iso3"], ascending=[False, True])
        cols = s3["country_map_columns"]
        st.markdown(f'<div class="gc-cmap-head">{_e(s3["country_map_label"])}</div>',
                    unsafe_allow_html=True)
        plain_table(
            cmap[["iso3", "country", "connections"]],
            column_labels={"iso3": cols["iso3"], "country": cols["country"],
                           "connections": cols["connections"]},
            height=488,
        )
st.caption(s3["network_note"])
st.caption(s3["guardrail"])

with st.expander(s3["table_label"]):
    st.markdown(s3["table_intro"])
    relationship_labels = s3["relationship_labels"]
    network_table = edges.assign(
        route=edges["exporter_name"] + " → " + edges["importer_name"],
        relationship=edges["category"].map(relationship_labels),
        gap_value_usd=edges["gap_value_usd"].map(fm.money),
    )[["route", "relationship", "reciprocal", "gap_value_usd"]]
    plain_table(network_table, column_labels={
        "route": s3["table_columns"]["route"],
        "relationship": s3["table_columns"]["relationship"],
        "reciprocal": s3["table_columns"]["reciprocal"],
        "gap_value_usd": s3["table_columns"]["gap_value"],
    })

conclusion = copy["conclusion"]
conclusion_body = conclusion["body"].format(gap_rows=f'{summary["gap_rows"]:,}')
section_title(conclusion["heading"], conclusion["caption"], icon="shield-check")
_rule()
st.markdown(
    f'<div class="gc-conclusion">'
    f'<div class="gc-conclusion-copy"><div class="gc-conclusion-title">'
    f'{_e(conclusion["title"])}</div><p>{_e(conclusion_body)}</p></div>'
    f'<div class="gc-conclusion-actions">'
    f'<span>{_e(conclusion["actions"][0])}</span>'
    f'<span>{_e(conclusion["actions"][1].format(persistent=persistence["persistent"]))}</span>'
    f'<span>{_e(conclusion["actions"][2])}</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)
with st.container(key="gc_next_page"):
    st.page_link(
        "app_pages/bank_implementation_pathway.py",
        label=conclusion["cta"],
        icon=":material/arrow_forward:",
    )

ledger("panel", "features", note="no gap row is model-eligible")

# Reveal the story sections and charts as they scroll into view.
render_scroll_reveal(
    ".section-heading, .st-key-gc_products_rows, .st-key-gc_products_value, "
    ".st-key-gc_network"
)
