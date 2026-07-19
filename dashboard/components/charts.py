"""
Reusable Plotly charts with one shared template.

Chart rules applied throughout (and worth keeping in future iterations):
  - one y-axis per chart, never dual axes — different units get separate charts;
  - colour follows the entity: each product family keeps its hue everywhere;
  - emphasis pattern: the series that matters in the accent hue, context in gray;
  - hairline solid gridlines, thin marks, tooltips on everything;
  - no synthetic/indexed values — charts draw the analytical values as stored.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from dashboard.components.status_badges import quality_label
from dashboard.services import formatting as fm
from dashboard.services.data_loader import load_content, load_theme

def chart_layout(height: int | None = None) -> dict:
    full = load_theme()
    theme = full["chart"]
    p = full["palette"]
    # Transparent paper/plot so a chart harmonises with whatever cool surface it
    # sits on (near-white card or the blue plane). Axis titles keep Storm ink;
    # tick labels drop to muted so the grid/axis chrome stays recessive and cool.
    # Tooltips are themed to the card surface (Storm ink on near-white, frost
    # border) instead of Plotly's default white/near-black.
    axis = dict(
        gridcolor=theme["grid_color"],
        linecolor=theme["axis_color"],
        zeroline=False,
        tickfont=dict(color=p["muted"]),
        title=dict(font=dict(color=p["ink"])),
    )
    return dict(
        template="plotly_white",
        font=dict(family=theme["font_family"], color=p["ink"], size=13),
        height=height or theme["height"],
        margin=theme["margin"],
        paper_bgcolor=theme["transparent"],
        plot_bgcolor=theme["transparent"],
        xaxis=dict(**axis),
        yaxis=dict(**axis),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=p["ink"])),
        hoverlabel=dict(
            font=dict(family=theme["font_family"], size=12, color=p["ink"]),
            bgcolor=p["panel_bg"],
            bordercolor=p["border"],
        ),
    )


def family_color_map() -> dict[str, str]:
    # Keyed by the SHORT display label used on axes/legends; colour follows the
    # family entity on every page and under every filter.
    theme = load_theme()
    labels = load_content()["family_short_labels"]
    return {labels.get(fam, fam): color for fam, color in theme["families"].items()}


def show(fig: go.Figure, height: int | None = None, key: str | None = None) -> None:
    # Keys must be STABLE across reruns (a changing key remounts the chart and
    # discards zoom/pan state) and unique per page — callers pass a literal.
    apply_chart_theme(fig, height)
    st.plotly_chart(fig, width="stretch", key=key,
                    config={"displayModeBar": False})


def apply_chart_theme(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Apply the canonical Plotly layout and return the same figure."""
    fig.update_layout(**chart_layout(height))
    return fig


# ---- Simple aggregates -------------------------------------------------------

def bar_by_family(frame: pd.DataFrame, x: str, y: str, y_title: str,
                  hover: list[str] | None = None) -> go.Figure:
    # Categories ARE the families -> identity colouring with the fixed map.
    fig = px.bar(
        frame, x=x, y=y, color=x, color_discrete_map=family_color_map(),
        text_auto=",.0f", hover_data=hover or [],
    )
    fig.update_traces(marker_line_width=0, width=0.55)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title=y_title)
    return fig


def bar_single(frame: pd.DataFrame, x: str, y: str, y_title: str = "",
               x_title: str = "", horizontal: bool = False,
               text_fmt: str = ",.0f") -> go.Figure:
    # One-series magnitude -> a single hue (emphasis blue), never a value ramp.
    color = load_theme()["chart"]["emphasis"]
    if horizontal:
        fig = px.bar(frame, x=y, y=x, orientation="h", text_auto=text_fmt)
        fig.update_layout(yaxis_title="", xaxis_title=y_title or x_title,
                          yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(frame, x=x, y=y, text_auto=text_fmt)
        fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    fig.update_traces(marker_color=color, marker_line_width=0, width=0.55)
    fig.update_layout(showlegend=False)
    return fig


def small_multiples_by_family(frame: pd.DataFrame, value_col: str,
                              hover_label: str, value_prefix: str = "",
                              value_suffix: str = "", value_fmt: str = ".3s") -> go.Figure:
    """One panel per family over year, each on its OWN scale.

    Gold dwarfs the others (value and benchmark alike), so a shared y-axis would
    flatten palm oil and copper to the baseline — the panels are deliberately not
    comparable in height. Line colour follows the family entity.
    """
    fig = px.line(
        frame, x="year", y=value_col, facet_col="family_label",
        color="family_label", color_discrete_map=family_color_map(),
        markers=True, facet_col_wrap=3, facet_col_spacing=0.07,
    )
    fig.update_yaxes(matches=None, showticklabels=True, title_text="")
    fig.update_xaxes(dtick=1, title_text="")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_traces(
        line=dict(width=2.5), marker=dict(size=6),
        hovertemplate=(f"<b>%{{x}}</b><br>{hover_label}: {value_prefix}"
                       f"%{{y:{value_fmt}}}{value_suffix}<extra></extra>"),
    )
    fig.update_layout(showlegend=False)
    return fig


def lines_by_family(frame: pd.DataFrame, y: str, y_title: str,
                    hover_label: str) -> go.Figure:
    """One line per family on a shared axis — for comparable magnitudes (counts)."""
    fig = px.line(
        frame, x="year", y=y, color="family_label",
        color_discrete_map=family_color_map(), markers=True,
    )
    fig.update_traces(
        line=dict(width=2.5), marker=dict(size=6),
        hovertemplate=(f"<b>%{{x}}</b> · %{{fullData.name}}"
                       f"<br>{hover_label}: %{{y:,.0f}}<extra></extra>"),
    )
    fig.update_layout(xaxis_title="", yaxis_title=y_title, legend_title_text="",
                      xaxis=dict(dtick=1))
    return fig


def score_strip(queue: pd.DataFrame) -> go.Figure:
    # Review scores by year, coloured by family. Evidence counts are constant
    # in the current outputs, so no size channel — position + colour only.
    fig = px.strip(
        queue, x="year", y="selected_review_priority_score", color="family_label",
        color_discrete_map=family_color_map(),
        hover_data={"corridor": True, "hs6": True, "rank": True,
                    "selected_review_priority_score": ":.3f", "family_label": False},
    )
    fig.update_traces(marker=dict(size=9, opacity=0.85), jitter=0.35)
    fig.update_layout(xaxis_title="", yaxis_title="Review-priority score",
                      legend_title_text="")
    return fig


def histogram_emphasis(population: pd.Series, selected: pd.Series,
                       x_title: str, population_name: str,
                       selected_name: str) -> go.Figure:
    # Emphasis pattern: the full official population in context gray, the
    # review queue in the accent hue. Same axis, same bins, shared tooltip.
    theme = load_theme()["chart"]
    fig = go.Figure()
    fig.add_histogram(x=population, name=population_name,
                      marker_color=theme["context_gray"], opacity=0.55, nbinsx=60)
    fig.add_histogram(x=selected, name=selected_name,
                      marker_color=theme["emphasis"], opacity=0.9, nbinsx=60)
    fig.update_layout(barmode="overlay", xaxis_title=x_title, yaxis_title="Observations")
    return fig


def severity_stack(frame: pd.DataFrame) -> go.Figure:
    # Severity is a status scale -> reserved status colours with text labels.
    status = load_theme()["status"]["severity"]
    color_map = {key: spec["color"] for key, spec in status.items()}
    fig = px.bar(
        frame, x="evidence_type", y="rows", color="severity",
        color_discrete_map=color_map, text_auto=True,
        category_orders={"severity": ["high", "medium", "low"]},
    )
    fig.update_traces(marker_line_color=load_theme()["chart"]["marker_outline"],
                      marker_line_width=2, width=0.55)
    fig.update_layout(xaxis_title="", yaxis_title="Evidence rows", legend_title_text="Severity")
    return fig


# ---- Model comparison ----------------------------------------------------------

def model_metric_bar(view: pd.DataFrame, metric: str, metric_label: str,
                     emphasis_models: set[str]) -> go.Figure:
    # Emphasis chart: the selected scorer(s) in accent, baselines in gray.
    theme = load_theme()["chart"]
    ordered = view.sort_values(metric, ascending=True)
    colors = [
        theme["emphasis"] if model in emphasis_models else theme["context_gray"]
        for model in ordered["model"]
    ]
    fig = go.Figure(go.Bar(
        x=ordered[metric], y=ordered["model"], orientation="h",
        marker_color=colors, marker_line_width=0, width=0.55,
        text=[f"{v:.3f}" for v in ordered[metric]], textposition="outside",
        hovertemplate="%{y}: %{x:.4f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title=metric_label, yaxis_title="")
    return fig


def shap_importance_bar(values: pd.DataFrame) -> go.Figure:
    """Global challenger contribution ranking using the shared emphasis colour."""
    ranked = values.sort_values("mean_abs_shap", ascending=True)
    fig = go.Figure(go.Bar(
        x=ranked["mean_abs_shap"], y=ranked["feature_name"], orientation="h",
        marker_color=load_theme()["chart"]["emphasis"], marker_line_width=0, width=0.55,
        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Mean |SHAP| (challenger model)", yaxis_title="")
    return fig


def headline_bar(frame: pd.DataFrame, label_col: str, value_col: str,
                 emphasis_label: str, x_title: str) -> go.Figure:
    """Plain 'how much better' bars (a share, 0-100%), one method emphasised.

    For the stakeholder 'does it work?' beat: the chosen method against the simple
    rules and a random-review baseline. Percent labels, no metric jargon.
    """
    theme = load_theme()["chart"]
    ordered = frame.sort_values(value_col, ascending=True)
    colors = [theme["emphasis"] if label == emphasis_label else theme["context_gray"]
              for label in ordered[label_col]]
    fig = go.Figure(go.Bar(
        x=ordered[value_col], y=ordered[label_col], orientation="h",
        marker_color=colors, marker_line_width=0, width=0.6,
        text=[f"{v:.0f}%" for v in ordered[value_col]], textposition="outside",
        hovertemplate="%{y}: %{x:.0f}%<extra></extra>",
    ))
    top = float(ordered[value_col].max())
    fig.update_layout(xaxis_title=x_title, yaxis_title="",
                      xaxis=dict(range=[0, max(100.0, top * 1.15)], ticksuffix="%"))
    return fig


def driver_dumbbell(frame: pd.DataFrame, queue_label: str, population_label: str,
                    x_title: str) -> go.Figure:
    """One shared 0-100 percentile scale showing the queue is extreme on every lens.

    Each row is a drift lens; a grey dot marks a typical route (the 50th
    percentile) and an accent dot marks a typical queue row, joined by a line.
    The visual point: on all four measures at once, queue rows sit near the top.
    """
    theme = load_theme()["chart"]
    fig = go.Figure()
    for _, row in frame.iterrows():
        fig.add_scatter(
            x=[row["population_pct"], row["queue_pct"]], y=[row["label"], row["label"]],
            mode="lines", line=dict(color=theme["axis_color"], width=2),
            showlegend=False, hoverinfo="skip",
        )
    fig.add_scatter(
        x=frame["population_pct"], y=frame["label"], mode="markers", name=population_label,
        marker=dict(size=12, color=theme["context_gray"],
                    line=dict(color=theme["marker_outline"], width=1)),
        hovertemplate="%{y}<br>" + population_label + ": %{x:.0f} of 100<extra></extra>",
    )
    fig.add_scatter(
        x=frame["queue_pct"], y=frame["label"], mode="markers", name=queue_label,
        marker=dict(size=13, color=theme["emphasis"],
                    line=dict(color=theme["marker_outline"], width=1)),
        hovertemplate="%{y}<br>" + queue_label + ": %{x:.0f} of 100<extra></extra>",
    )
    fig.update_layout(xaxis_title=x_title, yaxis_title="",
                      xaxis=dict(range=[0, 100]), legend_title_text="")
    return fig


# ---- Selected Case Review: the three comparison views ---------------------------
#
# Shared rules (notebook §6.2 + the case-page spec):
#   - corridor value = family colour; comparison series = dotted context gray
#     (market benchmark) or dashed navy (prior corridor median); the selected
#     year = one muted-amber diamond (theme selection tokens) in every view;
#   - missing years/values GAP (connectgaps=False, NaN y) — never zero-filled;
#   - short legends; the long explanations live in tooltips and captions;
#   - one fixed height (case_view_height) so switching views never jumps.

def case_view_height() -> int:
    """One fixed height (theme token) shared by the three comparison views."""
    return int(load_theme()["chart"]["height_tall"])


def _dash(value, formatter) -> str:
    # NA-safe hover cell: missing analytical values show an em dash, never 0.
    if value is None or pd.isna(value):
        return "—"
    return formatter(value)


def _add_case_diamond(fig: go.Figure, x, y, text: str | None = None) -> None:
    # The selected-year marker: muted amber diamond (selection role tokens).
    theme = load_theme()
    mode = "markers+text" if text else "markers"
    fig.add_scatter(
        x=x, y=y, mode=mode, showlegend=False,
        marker=dict(symbol="diamond", size=14, color=theme["selection"]["border"],
                    line=dict(color=theme["chart"]["marker_outline"], width=2)),
        text=[text] if text else None, textposition="top center",
        textfont=dict(size=12, color=theme["palette"]["ink"]),
        hoverinfo="skip",
    )


def case_market_view(frame: pd.DataFrame, family_id: str, copy: dict) -> go.Figure:
    """View 1 — corridor implied unit value vs the annual World Bank benchmark."""
    theme = load_theme()
    chart = theme["chart"]
    family_color = theme["families"].get(family_id, chart["emphasis"])
    hover = copy["hover"]
    quality = frame["quality_status"].map(lambda s: _dash(s, quality_label))
    custom = list(zip(
        frame["trade_value_usd"].map(lambda v: _dash(v, fm.money)),
        frame["quantity_metric_ton"].map(lambda v: _dash(v, fm.quantity_mt)),
        frame["unit_value"].map(lambda v: _dash(v, lambda x: fm.money(x) + "/mt")),
        frame["benchmark"].map(lambda v: _dash(v, lambda x: fm.money(x) + "/mt")),
        frame["multiple"].map(lambda v: _dash(v, lambda x: f"{x:,.2f}×")),
        quality,
    ))
    template = (
        "<b>%{x}</b>"
        f"<br>{hover['trade_value']}: %{{customdata[0]}}"
        f"<br>{hover['quantity']}: %{{customdata[1]}}"
        f"<br>{hover['implied_uv']}: %{{customdata[2]}}"
        f"<br>{hover['benchmark']}: %{{customdata[3]}}"
        f"<br>{hover['multiple']}: %{{customdata[4]}}"
        f"<br>{hover['quality']}: %{{customdata[5]}}"
        "<extra></extra>"
    )
    fig = go.Figure()
    fig.add_scatter(
        x=frame["year"], y=frame["benchmark"], mode="lines+markers",
        name=copy["series_benchmark"], connectgaps=False,
        line=dict(color=chart["context_gray"], width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="%{x} · " + copy["series_benchmark"] + " $%{y:,.0f}/mt<extra></extra>",
    )
    fig.add_scatter(
        x=frame["year"], y=frame["unit_value"], mode="lines+markers",
        name=copy["series_corridor"], connectgaps=False,
        line=dict(color=family_color, width=2.5), marker=dict(size=7),
        customdata=custom, hovertemplate=template,
    )
    focus = frame[frame["is_case_year"] & frame["unit_value"].notna()]
    if not focus.empty:
        _add_case_diamond(fig, focus["year"], focus["unit_value"])
    fig.update_layout(yaxis_title=copy["y_title"], xaxis_title="",
                      xaxis=dict(dtick=1), yaxis=dict(rangemode="tozero"))
    return fig


def case_history_view(frame: pd.DataFrame, family_id: str, copy: dict) -> go.Figure:
    """View 2 — corridor implied unit value vs its own prior-year median.

    `prior_median` arrives already exponentiated (case_summary owns the log→
    level conversion); missing medians and unobserved years stay as gaps.
    """
    theme = load_theme()
    chart = theme["chart"]
    family_color = theme["families"].get(family_id, chart["emphasis"])
    hover = copy["hover"]
    quality = frame["quality_status"].map(lambda s: _dash(s, quality_label))
    custom = list(zip(
        frame["unit_value"].map(lambda v: _dash(v, lambda x: fm.money(x) + "/mt")),
        frame["prior_median"].map(lambda v: _dash(v, lambda x: fm.money(x) + "/mt")),
        frame["multiple_vs_prior"].map(lambda v: _dash(v, lambda x: f"{x:,.2f}×")),
        frame["prior_years_used"].map(lambda v: _dash(v, lambda x: f"{int(x)}")),
        quality,
    ))
    template = (
        "<b>%{x}</b>"
        f"<br>{hover['implied_uv']}: %{{customdata[0]}}"
        f"<br>{hover['prior_median']}: %{{customdata[1]}}"
        f"<br>{hover['multiple']}: %{{customdata[2]}}"
        f"<br>{hover['prior_years']}: %{{customdata[3]}}"
        f"<br>{hover['quality']}: %{{customdata[4]}}"
        "<extra></extra>"
    )
    fig = go.Figure()
    fig.add_scatter(
        x=frame["year"], y=frame["prior_median"], mode="lines+markers",
        name=copy["series_prior"], connectgaps=False,
        line=dict(color=theme["palette"]["navy_700"], width=2, dash="dash"),
        marker=dict(size=6),
        hovertemplate="%{x} · " + copy["series_prior"] + " $%{y:,.0f}/mt<extra></extra>",
    )
    fig.add_scatter(
        x=frame["year"], y=frame["unit_value"], mode="lines+markers",
        name=copy["series_corridor"], connectgaps=False,
        line=dict(color=family_color, width=2.5), marker=dict(size=7),
        customdata=custom, hovertemplate=template,
    )
    focus = frame[frame["is_case_year"] & frame["unit_value"].notna()]
    if not focus.empty:
        _add_case_diamond(fig, focus["year"], focus["unit_value"])
    fig.update_layout(yaxis_title=copy["y_title"], xaxis_title="",
                      xaxis=dict(dtick=1), yaxis=dict(rangemode="tozero"))
    return fig


def case_peer_view(position: dict, copy: dict) -> go.Figure:
    """View 3 — where the case sits among same-family, same-year peers.

    Bars come precomputed from case_summary.peer_position (log10-spaced bins on
    a linear axis with power-of-ten tick labels — Plotly bars misbehave on true
    log axes). Peers outside the drawn window stay in the percentile maths; the
    page states how many are not drawn.
    """
    theme = load_theme()
    chart = theme["chart"]
    p = theme["palette"]
    bins = position["bins"]
    custom = list(zip(
        bins["ratio_low"].map(lambda v: f"{v:,.2g}"),
        bins["ratio_high"].map(lambda v: f"{v:,.2g}"),
        bins["count"].astype(int),
    ))
    fig = go.Figure(go.Bar(
        x=bins["log_center"], y=bins["count"],
        width=(bins["log_right"] - bins["log_left"]) * 0.92,
        marker_color=chart["context_gray"], marker_line_width=0,
        customdata=custom,
        hovertemplate=("%{customdata[0]}×–%{customdata[1]}× · %{customdata[2]} "
                       + copy["bar_hover_suffix"] + "<extra></extra>"),
        showlegend=False,
    ))
    fig.add_vline(
        x=0.0, line_color=p["navy_700"], line_width=1.5, line_dash="dash",
        annotation_text=copy["reference_label"], annotation_position="top right",
        annotation_font=dict(size=11, color=p["muted"]),
    )
    lo = float(bins["log_left"].min())
    hi = float(bins["log_right"].max())
    marker_x = min(max(position["case_log_ratio"], lo), hi)
    marker_y = max(position["max_count"] * 0.24, 1.0)
    label = copy["case_label"].format(multiple=f"{position['case_ratio']:,.1f}")
    _add_case_diamond(fig, [marker_x], [marker_y], text=label)
    tickvals = list(range(int(lo), int(hi) + 1))
    fig.update_layout(
        xaxis=dict(range=[lo - 0.05, hi + 0.05], tickvals=tickvals,
                   ticktext=[f"{10 ** t:g}×" for t in tickvals],
                   title=copy["x_title"]),
        yaxis_title=copy["y_title"], bargap=0.0, showlegend=False,
    )
    return fig
