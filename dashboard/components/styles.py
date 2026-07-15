"""
Global CSS derived from dashboard/config/dashboard_theme.yml.

Design language: "deep blue" — Storm-navy ink on a cool blue plane, near-white
cards that lift off the plane, a deep-navy sidebar frame with frost text, one
Steel accent, an amber boundary stamp, and a mono-set provenance ledger line
under panels. CSS targets Streamlit's PUBLIC hooks only (data-testid attributes
and our own classes) — never generated internal class names, which change
between releases.
"""

from __future__ import annotations

import streamlit as st

from dashboard.services.data_loader import load_theme


def apply_global_styles() -> None:
    theme = load_theme()
    p = theme["palette"]
    b = theme["boundary"]
    css = f"""
    <style>
    .block-container {{
        max-width: 1440px;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }}

    /* Deep-navy sidebar: anchors the darkest blue in the frame. The default
       fill is secondaryBackgroundColor (near-white); we override it here and
       force all sidebar text/nav/icons to frost so they stay legible on navy.
       The sidebar holds only brand text + navigation (no input widgets), so a
       broad light-text rule here is safe. */
    [data-testid="stSidebar"] {{
        background: {p["sidebar_bg"]};
        border-right: 1px solid {p["sidebar_bg"]};
    }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] span[data-testid="stIconMaterial"] {{
        color: {p["sidebar_ink"]} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{
        color: {p["sidebar_muted"]} !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(234, 240, 248, 0.22);
    }}
    /* Selected / hovered nav item: a subtle frost wash so the light label
       stays readable on navy (primaryColor tint can be too dark here). */
    [data-testid="stSidebarNav"] a:hover {{
        background: rgba(234, 240, 248, 0.10);
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background: rgba(234, 240, 248, 0.16);
    }}

    [data-testid="stMetric"] {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 0.9rem 1rem 0.75rem 1rem;
    }}
    [data-testid="stMetricLabel"] {{ color: {p["muted"]}; }}
    [data-testid="stMetricValue"] {{
        color: {p["ink"]};
        font-variant-numeric: normal;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {p["border"]};
        border-radius: 10px;
        overflow: hidden;
    }}

    .page-eyebrow {{
        color: {p["accent"]};
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .page-title {{
        color: {p["ink"]};
        font-size: 2.05rem;
        line-height: 1.12;
        font-weight: 750;
        margin: 0;
    }}
    .page-subtitle {{
        color: {p["muted"]};
        font-size: 1rem;
        margin-top: 0.4rem;
        margin-bottom: 1.1rem;
    }}

    /* The boundary stamp: amber notice with an uppercase micro-label. */
    .boundary-banner {{
        background: {b["bg"]};
        border: 1px solid {b["border"]};
        border-left: 4px solid {b.get("accent", b["border"])};
        border-radius: 8px;
        padding: 0.7rem 1rem;
        margin: 0.35rem 0 1.1rem 0;
        color: {b["ink"]};
    }}
    .boundary-banner .stamp {{
        display: block;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }}

    .section-label {{
        color: {p["ink"]};
        font-size: 1.12rem;
        font-weight: 700;
        margin-top: 0.7rem;
        margin-bottom: 0.15rem;
    }}
    .section-caption {{
        color: {p["muted"]};
        font-size: 0.88rem;
        margin-bottom: 0.5rem;
    }}

    /* Provenance ledger: the signature element. Every panel can state the
       exact file backing it, set small and monospaced like a custody record. */
    .ledger {{
        color: {p["ledger_ink"]};
        font-family: "Consolas", "SFMono-Regular", monospace;
        font-size: 0.72rem;
        letter-spacing: 0.01em;
        margin: 0.25rem 0 0.9rem 0;
        opacity: 0.85;
    }}
    .ledger::before {{ content: "⌂ "; }}

    /* Evidence cards carry a teal ledger-rule on the left. */
    .evidence-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
        color: {p["ink"]};
    }}
    .evidence-card .evidence-meta {{
        color: {p["muted"]};
        font-size: 0.78rem;
        margin-top: 0.35rem;
    }}

    .status-pill {{
        display: inline-block;
        border-radius: 999px;
        padding: 0.1rem 0.55rem;
        font-size: 0.76rem;
        font-weight: 700;
        border: 1px solid currentColor;
        background: transparent;
    }}

    .source-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.8rem;
        color: {p["ink"]};
    }}
    .source-card h4 {{ margin: 0 0 0.25rem 0; }}
    .source-card .source-row {{
        font-size: 0.86rem;
        margin: 0.15rem 0;
        color: {p["ink"]};
    }}
    .source-card .source-row b {{ color: {p["muted"]}; font-weight: 600; }}

    .info-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 0.85rem 1rem;
        color: {p["ink"]};
        height: 100%;
    }}
    .info-card h4 {{ margin: 0.25rem 0 0.3rem 0; }}
    .info-card p {{ margin: 0; color: {p["muted"]}; font-size: 0.9rem; }}
    .step-pill {{
        display: inline-block;
        border-radius: 999px;
        padding: 0.12rem 0.5rem;
        font-size: 0.72rem;
        font-weight: 700;
        background: {p["accent_soft"]};
        color: {p["accent"]};
        border: 1px solid {p["accent"]};
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
