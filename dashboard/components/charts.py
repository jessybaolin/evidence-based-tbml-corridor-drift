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


# ---- Case trend charts ----------------------------------------------------------

def unit_value_vs_benchmark(history: pd.DataFrame, case_year: int,
                            log_scale: bool = False) -> go.Figure:
    # Same unit (USD per metric ton) -> one axis, two series: corridor value in
    # the accent hue, World Bank benchmark as gray context. The selected year
    # is direct-labelled; everything else stays in the tooltip.
    theme = load_theme()["chart"]
    fig = go.Figure()
    fig.add_scatter(
        x=history["year"], y=history["benchmark_price_usd_per_metric_ton"],
        mode="lines+markers", name="World Bank benchmark",
        line=dict(color=theme["context_gray"], width=2),
        marker=dict(size=7),
        hovertemplate="%{x} · benchmark $%{y:,.0f}/mt<extra></extra>",
    )
    fig.add_scatter(
        x=history["year"], y=history["unit_value_usd_per_metric_ton"],
        mode="lines+markers", name="Aggregate unit value",
        line=dict(color=theme["emphasis"], width=2.5),
        marker=dict(size=8),
        hovertemplate="%{x} · unit value $%{y:,.0f}/mt<extra></extra>",
    )
    focus = history.loc[history["year"] == case_year]
    if not focus.empty and pd.notna(focus["unit_value_usd_per_metric_ton"].iloc[0]):
        fig.add_scatter(
            x=focus["year"], y=focus["unit_value_usd_per_metric_ton"],
            mode="markers+text", showlegend=False,
            marker=dict(size=13, color=theme["emphasis"],
                        line=dict(color=theme["marker_outline"], width=2)),
            text=[f"{int(case_year)}"], textposition="top center",
            hoverinfo="skip",
        )
    fig.update_layout(yaxis_title="USD per metric ton", xaxis_title="",
                      yaxis_type="log" if log_scale else "linear")
    return fig


def history_line(history: pd.DataFrame, column: str, y_title: str,
                 case_year: int, hover_fmt: str = ",.0f") -> go.Figure:
    # Single-series official history with the case year highlighted.
    theme = load_theme()["chart"]
    fig = go.Figure()
    fig.add_scatter(
        x=history["year"], y=history[column], mode="lines+markers",
        line=dict(color=theme["emphasis"], width=2), marker=dict(size=7),
        hovertemplate="%{x} · %{y:" + hover_fmt + "}<extra></extra>",
        showlegend=False,
    )
    focus = history.loc[history["year"] == case_year]
    if not focus.empty and pd.notna(focus[column].iloc[0]):
        fig.add_scatter(
            x=focus["year"], y=focus[column], mode="markers", showlegend=False,
            marker=dict(size=12, color=theme["emphasis"],
                        line=dict(color=theme["marker_outline"], width=2)),
            hoverinfo="skip",
        )
    fig.update_layout(yaxis_title=y_title, xaxis_title="")
    return fig


def residual_line(history: pd.DataFrame, case_year: int) -> go.Figure:
    # Benchmark residual vs the zero baseline (log scale gap; 0 = at benchmark).
    fig = history_line(history, "benchmark_residual",
                       "Log gap to benchmark (0 = at benchmark)", case_year, ".3f")
    fig.add_hline(y=0, line_color=load_theme()["chart"]["axis_color"], line_width=1)
    return fig
