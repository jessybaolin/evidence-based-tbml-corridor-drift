"""
Global CSS derived from dashboard/config/dashboard_theme.yml.

Design language: "Navy · Teal · Warm Amber" — navy ink on a bright pale
blue-grey plane, TRULY WHITE cards that lift off the plane on a soft shadow, a
deep-navy sidebar frame with frost text and a teal active indicator, TEAL as the
single interactive colour (links, selection, focus, primary action, chart
emphasis), a warm amber caveat counterpoint, a navy boundary ribbon fixed to the
bottom of every page, and a mono-set provenance ledger line under panels. Small
teal TEXT on light uses the deeper teal_hover for AA; brighter accent teal is for
fills/borders/icons. CSS targets Streamlit's PUBLIC hooks only (data-testid
attributes and our own classes) — never generated internal class names.

Motion: one fade-up entrance for page sections, one hover lift for cards/tiles/
links, button/segment hover transitions, CSS-only tooltips — all transform/
opacity, all disabled in the prefers-reduced-motion block at the END of the
sheet (kept last plus !important so it always wins the cascade).
"""

from __future__ import annotations

import streamlit as st

from dashboard.services.data_loader import load_theme


def apply_global_styles() -> None:
    theme = load_theme()
    p = theme["palette"]
    b = theme["boundary"]
    mm = theme["mental_model"]
    ev = theme["evaluation"]
    layout = theme["layout"]
    surfaces = theme["surfaces"]
    kpi = theme["components"]["kpi"]
    source_roles = theme["source_roles"]
    selection = theme["selection"]
    ev_op = float(ev.get("receded_opacity", 0.90))
    # Teal has two roles: `accent` (bright) for fills/borders/icons/focus/chart
    # emphasis; `at` (deeper teal_hover) for small teal TEXT on light, for AA.
    at = p.get("teal_hover", p["accent"])
    teal500 = p.get("teal_500", b.get("accent", p["accent"]))
    sel_bg = selection["background"]
    sel_acc = selection["border"]
    sel = p.get("sidebar_sel_bg", p["sidebar_bg"])
    hover_bg = p.get("sidebar_hover_bg", p["sidebar_bg"])
    shadow = p.get("card_shadow", "rgba(29,45,70,0.08)")
    navy7 = p.get("navy_700", p["ink"])
    btn2b = p.get("btn_secondary_border", p["border"])
    motion = theme.get("motion", {})
    entry_ms = int(motion.get("entry_ms", 350))
    step_ms = int(motion.get("entry_step_ms", 70))
    hover_ms = int(motion.get("hover_ms", 180))
    fast_ms = int(motion.get("fast_ms", 120))
    standard_ms = int(motion.get("standard_ms", hover_ms))
    landing_entry_ms = int(motion.get("landing_entry_ms", 260))
    landing_stagger_ms = int(motion.get("landing_stagger_ms", 45))
    motion_easing = motion.get("easing", "ease-out")
    scene_ms = int(motion.get("scene_step_ms", 120))
    travel_ms = int(motion.get("travel_ms", 600))
    family_colors = theme["families"]
    challenge_accent = theme["status"]["severity"]["high"]["color"]
    outcome_blue = source_roles["official"]["accent"]
    outcome_amber = source_roles["typology"]["accent"]
    css = f"""
    <style>
    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {{
        background: {p["page_bg"]};
    }}
    .block-container {{
        max-width: {int(layout["max_width_px"])}px;
        padding-left: {int(layout["desktop_padding_px"])}px;
        padding-right: {int(layout["desktop_padding_px"])}px;
        padding-top: 1.4rem;
        /* Clearance for the fixed boundary ribbon: content can never hide
           beneath it, even with the ribbon text wrapped onto two lines. */
        padding-bottom: {int(layout["footer_clearance_px"])}px;
    }}
    @media (max-width: {int(theme["breakpoints"]["narrow_px"])}px) {{
        .block-container {{
            padding-left: {int(layout["narrow_padding_px"])}px;
            padding-right: {int(layout["narrow_padding_px"])}px;
        }}
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
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarHeader"],
    [data-testid="stSidebarUserContent"] {{
        background: {p["sidebar_bg"]};
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
        margin: 0.3rem 0 0.15rem 0;
    }}

    /* Trim the sidebar's top padding so the brand hugs the top-left corner. */
    [data-testid="stSidebarHeader"] {{
        padding-top: 0.25rem;
        padding-bottom: 0;
        min-height: 0;
        height: auto;
    }}
    [data-testid="stSidebarUserContent"] {{
        padding-top: 0;
    }}

    /* Brand block — custom HTML so we fully control size and spacing. */
    .brand-title {{
        color: {p["sidebar_ink"]};
        font-size: 1.6rem;
        line-height: 1.16;
        font-weight: 800;
        margin: 0.1rem 0 0.45rem 0;
    }}
    .brand-sub {{
        color: {p["sidebar_muted"]};
        font-size: 0.9rem;
        line-height: 1.4;
        margin: 0 0 0.35rem 0;
    }}
    .brand-rule {{
        border-top: 1px solid rgba(234, 240, 248, 0.22);
        margin: 0.35rem 0 0.5rem 0;
    }}

    /* Custom navigation. Streamlit's built-in auto-nav is hidden (it injects a
       fixed vertical gap we can't override); we render st.page_link instead, so
       the sidebar is one flow with NO gap between the title and the links.
       Restrained hover: a transparent 2px left rule fades to frost and the label
       eases 2px right; the active page keeps a solid frost rule. */
    .nav-group {{
        color: {p["sidebar_muted"]};
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 0.75rem 0 0.2rem 0.15rem;
    }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] {{
        margin: 0.05rem 0;
    }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a {{
        padding: 0.42rem 0.6rem;
        border-radius: 7px;
        /* Fixed 3px rule that only changes COLOUR between states, so switching
           pages never shifts the label by a pixel. */
        border-left: 3px solid transparent;
        transition: background-color 150ms ease-out,
                    border-left-color 150ms ease-out,
                    transform 150ms ease-out;
    }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a p {{
        font-size: 0.9rem;
        font-weight: 600;
        line-height: 1.25;
        color: {p["sidebar_ink"]} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
        background: {hover_bg};
        border-left-color: {teal500}66;
        transform: translateX(2px);
    }}
    /* Selected page: navy fill + a solid teal left indicator. */
    [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {{
        background: {sel};
        border-left-color: {teal500};
    }}

    /* st.metric cards match the .stat-tile card language: white, bordered, a
       soft lift shadow, and a thin teal top accent. */
    [data-testid="stMetric"] {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 10px;
        padding: 0.85rem 1rem 0.75rem 1rem;
        box-shadow: 0 4px 14px {shadow};
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

    /* Styled reference tables (components/tables.plain_table): full control over
       borders, header tint, and cell colours that st.dataframe's canvas grid
       cannot give. Themed to the blue palette. The interactive review queue
       stays an st.dataframe (it needs row selection). */
    .data-table-wrap {{
        overflow-x: auto;
        border: 1px solid {p["border"]};
        border-radius: 10px;
        background: {p["panel_bg"]};
        margin: 0.2rem 0 0.7rem 0;
    }}
    table.data-table {{
        border-collapse: collapse;
        width: 100%;
        font-size: 0.9rem;
        color: {p["ink"]};
    }}
    table.data-table thead th {{
        position: sticky;
        top: 0;
        z-index: 1;
        background: {p["sidebar_bg"]};   /* navy — matches the navigation panel */
        color: {p["sidebar_ink"]};       /* frost text on navy */
        font-weight: 700;
        letter-spacing: 0.01em;
        text-align: left;
        white-space: nowrap;
        padding: 0.6rem 0.85rem;
        border-bottom: 2px solid {p["accent"]};
    }}
    table.data-table tbody td {{
        padding: 0.5rem 0.85rem;
        border-top: 1px solid rgba(35, 53, 77, 0.08);
        vertical-align: top;
    }}
    table.data-table.zebra tbody tr:nth-child(even) {{
        background: {p.get("table_stripe", "#EFF3FA")};
    }}
    table.data-table tbody tr:hover {{
        background: {p["accent_soft"]};
    }}
    table.data-table td.num,
    table.data-table th.num {{
        text-align: right;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }}

    .page-eyebrow {{
        color: {at};
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

    .page-header {{ margin-bottom: 0.2rem; }}

    .section-heading {{
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        margin-top: 0.7rem;
    }}
    .section-heading .section-icon {{
        color: {p["accent"]};
        width: 1.25rem;
        height: 1.25rem;
        margin-top: 0.76rem;
        flex: none;
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
        opacity: 0.9;
    }}
    .dataset-strip {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: {int(surfaces["radius_px"])}px;
        padding: 0.55rem 0.75rem;
        box-shadow: {surfaces["shadow"]};
    }}
    .dataset-strip svg {{ color: {p["ledger_ink"]}; flex: none; }}
    .dataset-strip span {{ overflow-wrap: anywhere; }}

    /* Evidence cards carry a teal ledger-rule on the left. */
    .evidence-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
        color: {p["ink"]};
        box-shadow: 0 4px 14px {shadow};
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
        box-shadow: 0 4px 14px {shadow};
    }}
    .source-card h4 {{ margin: 0 0 0.25rem 0; }}
    .source-card .source-row {{
        font-size: 0.86rem;
        margin: 0.15rem 0;
        color: {p["ink"]};
    }}
    .source-card .source-row b {{ color: {p["muted"]}; font-weight: 600; }}
    .source-origin {{ opacity: 0.72; }}

    .icon-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: {int(theme["components"]["icon"]["badge_size_px"])}px;
        height: {int(theme["components"]["icon"]["badge_size_px"])}px;
        border-radius: 50%;
        flex: none;
    }}
    .icon-badge svg {{ width: 1.45rem; height: 1.45rem; }}

    .info-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 0.85rem 1rem;
        color: {p["ink"]};
        height: 100%;
        box-shadow: 0 4px 14px {shadow};
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
        color: {at};
        border: 1px solid {p["accent"]};
    }}

    /* ---- Boundary ribbon: the human-review boundary, fixed to the bottom of
       every page. Rendered ONCE in streamlit_app.py (boundary_ribbon). Sits
       above main content but BELOW the sidebar (Streamlit sidebar z-index is
       100), so the navy sidebar deliberately covers its left end. ---- */
    .boundary-ribbon {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 60;
        background: {b["bg"]};
        color: {b["ink"]};
        border-top: 3px solid {b.get("accent", b["border"])};
        box-shadow: 0 -6px 18px rgba(2, 18, 47, 0.28);
        padding: 0.55rem 1.2rem;
        font-size: 0.88rem;
        line-height: 1.4;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        text-align: left;
    }}
    @media (min-width: 993px) {{
        /* Keep the text clear of the expanded sidebar; the steel FILL still
           runs edge-to-edge underneath it. */
        .boundary-ribbon {{ padding-left: 21rem; }}
    }}
    @media (min-width: 993px) and (max-width: 1100px) {{
        .boundary-ribbon {{
            padding-left: 19.5rem;
            font-size: 0.8rem;
            line-height: 1.3;
        }}
    }}
    .boundary-ribbon .stamp {{
        display: inline-block;
        color: {b.get("label", b["ink"])};
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-right: 0.6rem;
        white-space: nowrap;
    }}
    .boundary-icon {{ width: 1.2rem; height: 1.2rem; color: {b["accent"]}; flex: none; }}
    /* The ribbon's own element wrapper must not add flex-gap spacing to the
       page flow (its only child is position:fixed). :has() degrades to a
       harmless no-op gap on very old browsers. */
    [data-testid="stElementContainer"]:has(.boundary-ribbon) {{
        position: absolute;
        height: 0;
    }}

    /* ---- Main-area page links styled as calm CTA pills. Scoped to stMain so
       the sidebar navigation rules above are untouched. ---- */
    [data-testid="stMain"] [data-testid="stPageLink"] a {{
        border: 1px solid {p["accent"]};
        background: {p["panel_bg"]};
        border-radius: 8px;
        padding: 0.45rem 0.95rem;
        width: fit-content;
        transition: background-color {hover_ms}ms ease-out,
                    box-shadow {hover_ms}ms ease-out,
                    transform {hover_ms}ms ease-out;
    }}
    [data-testid="stMain"] [data-testid="stPageLink"] a p {{
        color: {at} !important;
        font-weight: 700;
        font-size: 0.95rem;
    }}
    [data-testid="stMain"] [data-testid="stPageLink"] a span[data-testid="stIconMaterial"] {{
        color: {p["accent"]};
    }}
    [data-testid="stMain"] [data-testid="stPageLink"] a:hover {{
        background: {p["accent_soft"]};
        box-shadow: 0 4px 12px rgba(35, 53, 77, 0.16);
        transform: translateY(-1px);
    }}

    .st-key-dashboard_filter_panel {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: {int(surfaces["radius_large_px"])}px;
        padding: {int(theme["components"]["filters"]["padding_px"])}px;
        box-shadow: {surfaces["shadow"]};
        margin: 0.35rem 0 0.8rem 0;
    }}
    .st-key-dashboard_filter_panel .section-heading {{ margin-top: 0; }}

    /* ---- Buttons (main area only; the sidebar carries no st.button). Teal is
       the primary action; secondary is a quiet white/navy-outline; Replay is a
       pale-navy utility variant. Scoped to stMain so sidebar nav is untouched. ---- */
    [data-testid="stMain"] [data-testid="stButton"] button {{
        border-radius: 8px;
        font-weight: 650;
        transition: background-color {hover_ms}ms ease-out,
                    border-color {hover_ms}ms ease-out,
                    box-shadow {hover_ms}ms ease-out,
                    transform {hover_ms}ms ease-out;
    }}
    [data-testid="stMain"] [data-testid="stBaseButton-primary"] {{
        background: {p["accent"]};
        border: 1px solid {p["accent"]};
        color: #FFFFFF;
    }}
    [data-testid="stMain"] [data-testid="stBaseButton-primary"]:hover:not(:disabled) {{
        background: {at};
        border-color: {at};
        box-shadow: 0 4px 12px {shadow};
        transform: translateY(-1px);
    }}
    [data-testid="stMain"] [data-testid="stBaseButton-secondary"] {{
        background: {p["panel_bg"]};
        border: 1px solid {btn2b};
        color: {navy7};
    }}
    [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover:not(:disabled) {{
        border-color: {p["accent"]};
        color: {at};
        background: {p["accent_soft"]};
    }}
    [data-testid="stMain"] [data-testid="stButton"] button:disabled {{ opacity: 0.5; }}
    /* Replay = pale-navy utility. The keyed wrapper (.st-key-<key>) is a stable
       Streamlit hook; this selector out-specifies the secondary rule above. */
    [data-testid="stMain"] .st-key-dtrq_replay_btn [data-testid="stBaseButton-secondary"] {{
        background: {p.get("table_stripe", "#EFF3F8")};
        border-color: {btn2b};
        color: {navy7};
    }}
    [data-testid="stMain"] .st-key-dtrq_replay_btn [data-testid="stBaseButton-secondary"]:hover:not(:disabled) {{
        background: {p["panel_bg"]};
        border-color: {navy7};
        color: {navy7};
    }}

    /* ---- Segmented control (scene stage bar): ACTIVE segment = teal fill +
       white text; inactive = white + grey border. Streamlit exposes the active
       option via stBaseButton-segmented_controlActive. This is active-vs-inactive
       (segmented_control has no per-segment completed/upcoming state). ---- */
    [data-testid="stMain"] [data-testid="stBaseButton-segmented_control"] {{
        background: {p["panel_bg"]};
        border-color: {btn2b};
        color: {navy7};
    }}
    [data-testid="stMain"] [data-testid="stBaseButton-segmented_controlActive"] {{
        background: {p["accent"]};
        border-color: {p["accent"]};
        color: #FFFFFF;
    }}

    /* ---- Review Queue: current-case banner. Muted amber = the palette's
       attention role — a "this is the case you are carrying" marker, never an
       alarm. Ink on the wash is 11.9:1 (AA); the deep-amber border is
       decorative (the fill + text identify the banner, never colour alone).
       The page_link inside restyles to the teal primary pill so the single
       interactive colour stays teal even on the amber card. ---- */
    .st-key-queue_case_banner {{
        background: {sel_bg};
        border: 1px solid {sel_acc};
        border-left: 4px solid {sel_acc};
        border-radius: 10px;
        padding: 0.6rem 0.95rem;
        box-shadow: 0 2px 8px {shadow};
    }}
    .case-banner-text {{
        color: {p["ink"]};
        font-size: 0.98rem;
        line-height: 1.45;
        animation: rise-in 260ms ease-out both;
    }}
    .case-banner-text strong {{ font-weight: 750; }}
    [data-testid="stMain"] .st-key-queue_case_banner [data-testid="stPageLink"] a {{
        background: {p["accent"]};
        border-color: {p["accent"]};
        width: 100%;
        justify-content: center;
    }}
    [data-testid="stMain"] .st-key-queue_case_banner [data-testid="stPageLink"] a p {{
        color: #FFFFFF !important;
    }}
    [data-testid="stMain"] .st-key-queue_case_banner [data-testid="stPageLink"] a span[data-testid="stIconMaterial"] {{
        color: #FFFFFF;
    }}
    [data-testid="stMain"] .st-key-queue_case_banner [data-testid="stPageLink"] a:hover {{
        background: {at};
        border-color: {at};
    }}

    /* ---- Top 50 Review Queue: compact operational review surface. ---- */
    .st-key-queue_header .page-header {{ margin-bottom: 0.55rem; }}
    .st-key-queue_header .page-subtitle {{
        max-width: 1000px;
        color: {p["muted"]};
        font-size: 1.08rem;
        font-weight: 450;
        line-height: 1.5;
        margin-bottom: 0.75rem;
    }}
    .queue-interpretation-boundary {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        max-width: 1000px;
        padding: 0.58rem 0.75rem;
        color: {p["ink"]};
        background: color-mix(in srgb, {p["accent_soft"]} 68%, white);
        border: 1px solid color-mix(in srgb, {p["accent"]} 34%, white);
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        font-size: 0.9rem;
        line-height: 1.4;
        animation: rise-in {landing_entry_ms}ms {motion_easing} both;
    }}
    .queue-interpretation-boundary svg {{
        width: 1rem;
        height: 1rem;
        color: {p["accent"]};
        flex: none;
    }}

    .st-key-dashboard_filter_panel {{
        background: color-mix(in srgb, {p["page_bg"]} 60%, white);
        border-color: color-mix(in srgb, {btn2b} 58%, white);
        border-radius: 8px;
        padding: 0.6rem 0.85rem;
        gap: 0.375rem;
        margin: 0.65rem 0 0.75rem 0;
        box-shadow: 0 3px 12px {shadow};
        animation: rise-in {landing_entry_ms}ms {motion_easing} both;
    }}
    .st-key-dashboard_filter_panel .section-heading {{ margin: 0; }}
    .st-key-dashboard_filter_panel .section-icon {{ margin-top: 0.15rem; }}
    .st-key-dashboard_filter_panel .section-label {{
        margin-top: 0;
        font-size: 1rem;
    }}
    .st-key-dashboard_filter_panel .section-caption {{
        margin: 0.05rem 0 0;
        font-size: 0.8rem;
        line-height: 1.35;
    }}
    .st-key-queue_reset_filters button {{
        min-height: 38px;
        padding: 0.35rem 0.65rem;
    }}
    .st-key-dashboard_filter_panel [data-testid="stMultiSelect"] label,
    .st-key-dashboard_filter_panel [data-testid="stWidgetLabel"] {{
        color: {p["ink"]};
        font-weight: 650;
    }}
    .st-key-dashboard_filter_panel [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
        min-height: 42px;
        background: {p["panel_bg"]};
        border: 1px solid {btn2b};
        border-radius: 8px;
        transition: border-color {standard_ms}ms {motion_easing},
                    box-shadow {standard_ms}ms {motion_easing};
    }}
    .st-key-dashboard_filter_panel [data-testid="stMultiSelect"] [data-baseweb="select"] > div:hover {{
        border-color: {p["accent"]};
    }}
    .st-key-dashboard_filter_panel [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {{
        border-color: {p["accent"]};
        box-shadow: 0 0 0 3px color-mix(in srgb, {p["accent_soft"]} 82%, white);
    }}
    .st-key-dashboard_filter_panel [data-testid="stMultiSelect"] svg {{
        color: {navy7};
    }}
    .st-key-dashboard_filter_panel [data-testid="stButtonGroup"] {{ width: fit-content; }}
    .st-key-dashboard_filter_panel [role="radiogroup"] {{ max-width: none; }}
    .st-key-dashboard_filter_panel [role="radio"] {{ min-height: 38px; }}
    .queue-size-helper {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        margin-top: 1.15rem;
        color: {p["muted"]};
        font-size: 0.78rem;
    }}
    .queue-size-helper svg {{ width: 0.95rem; height: 0.95rem; color: {p["accent"]}; }}
    .queue-filter-result {{
        margin-top: 1.15rem;
        color: {p["muted"]};
        font-size: 0.82rem;
        text-align: right;
        white-space: nowrap;
    }}
    .queue-filter-result strong {{ color: {p["ink"]}; font-size: 0.98rem; }}
    .st-key-dashboard_filter_panel [data-testid="stExpander"] {{
        background: color-mix(in srgb, {p["table_stripe"]} 74%, white);
        border: 1px solid {p["border"]};
        border-radius: 8px;
    }}
    .st-key-dashboard_filter_panel [data-testid="stExpander"] summary {{
        min-height: 38px;
        color: {p["ink"]};
        font-weight: 650;
    }}
    .st-key-dashboard_filter_panel [data-testid="stSlider"] {{ padding-bottom: 0.2rem; }}
    .st-key-queue_clear_advanced button {{ width: fit-content; min-height: 34px; }}

    .st-key-queue_results_header {{ margin-top: 0.2rem; }}
    .st-key-queue_results_header .section-heading {{ margin-top: 0; }}
    .st-key-queue_results_header .section-icon {{ color: {outcome_blue}; }}
    .st-key-queue_results_header .section-label {{ font-size: 1.16rem; }}
    .st-key-queue_results_header .section-caption {{
        max-width: 760px;
        margin-bottom: 0;
        line-height: 1.4;
    }}
    .queue-result-count {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        color: {p["muted"]};
        background: color-mix(in srgb, {outcome_blue} 8%, white);
        border: 1px solid color-mix(in srgb, {outcome_blue} 25%, white);
        border-radius: 8px;
        line-height: 1.05;
    }}
    .queue-result-count strong {{ color: {outcome_blue}; font-size: 1.05rem; }}
    .queue-result-count span {{ font-size: 0.7rem; text-transform: uppercase; }}
    [data-testid="stMain"] .st-key-queue_results_header [data-testid="stDownloadButton"] button {{
        min-height: 42px;
        border-color: {p["accent"]};
        color: {at};
    }}

    .st-key-queue_case_banner {{
        background: color-mix(in srgb, {sel_bg} 58%, white);
        border: 1px solid color-mix(in srgb, {sel_acc} 72%, white);
        border-left: 4px solid {source_roles["typology"]["accent"]};
        border-radius: 8px;
        padding: 0.65rem 0.9rem;
        box-shadow: 0 2px 8px {shadow};
        margin: 0.35rem 0 0.65rem;
        transition: background-color {standard_ms}ms {motion_easing},
                    border-color {standard_ms}ms {motion_easing};
    }}
    .current-case-label {{
        color: {source_roles["typology"]["text"]};
        font-size: 0.67rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }}
    .case-banner-text {{ font-size: 0.93rem; animation: none; }}

    .queue-state-summary {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.55rem 1.25rem;
        min-height: 38px;
        margin: 0 0 0.45rem;
        padding: 0.45rem 0.7rem;
        color: {p["muted"]};
        background: color-mix(in srgb, {p["table_stripe"]} 64%, white);
        border-top: 1px solid {p["border"]};
        border-bottom: 1px solid {p["border"]};
        font-size: 0.82rem;
    }}
    .queue-state-summary strong {{ color: {p["ink"]}; font-variant-numeric: tabular-nums; }}
    .st-key-queue_filter_chips {{ margin: 0 0 0.45rem; }}
    .st-key-queue_filter_chips button {{
        min-height: 34px;
        border-radius: 999px !important;
        background: {p["panel_bg"]};
        color: {navy7};
        font-size: 0.8rem;
    }}
    .st-key-queue_table_region {{
        margin-top: 0.15rem;
        animation: rise-in {landing_entry_ms}ms {motion_easing} both;
    }}
    .st-key-queue_table_region div[data-testid="stDataFrame"] {{
        border: 1px solid color-mix(in srgb, {btn2b} 62%, white);
        border-radius: 8px;
        box-shadow: 0 4px 14px {shadow};
        background: {p["panel_bg"]};
    }}

    .st-key-queue_score_guidance {{
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        margin: 0.75rem 0 0.55rem;
        padding: 0.75rem 0.9rem;
        color: {p["ink"]};
        background: color-mix(in srgb, {outcome_blue} 8%, white);
        border: 1px solid color-mix(in srgb, {outcome_blue} 26%, white);
        border-left: 3px solid {outcome_blue};
        border-radius: 8px;
    }}
    .queue-guidance-icon {{
        display: grid;
        place-items: center;
        width: 1.8rem;
        height: 1.8rem;
        flex: none;
        color: {outcome_blue};
        background: color-mix(in srgb, {outcome_blue} 12%, white);
        border-radius: 50%;
    }}
    .queue-guidance-icon svg {{ width: 1rem; height: 1rem; }}
    .queue-guidance-label {{
        color: {outcome_blue};
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }}
    .queue-guidance-text {{ color: {p["ink"]}; font-size: 0.9rem; line-height: 1.45; }}
    .st-key-queue_table_notes [data-testid="stExpander"] {{
        background: transparent;
        border: 1px solid {p["border"]};
        border-radius: 8px;
    }}
    .st-key-queue_table_notes [data-testid="stExpander"] summary {{ min-height: 40px; }}
    .queue-technical-notes {{ color: {p["muted"]}; font-size: 0.82rem; line-height: 1.45; }}
    .queue-technical-notes p {{ margin: 0 0 0.45rem; }}
    .queue-technical-notes p:last-child {{ margin-bottom: 0; }}

    @media (max-width: 1100px) {{
        .st-key-dashboard_filter_panel [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
        .st-key-queue_results_header .queue-result-count {{ align-items: flex-start; padding-left: 0.65rem; }}
    }}
    @media (max-width: 780px) {{
        .st-key-dashboard_filter_panel {{ padding: 0.75rem; }}
        .queue-filter-result {{ text-align: left; margin-top: 0.35rem; }}
        .queue-size-helper {{ margin-top: 0.35rem; }}
        .st-key-queue_case_banner [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
        .queue-state-summary {{ align-items: flex-start; flex-direction: column; gap: 0.25rem; }}
        .st-key-queue_filter_chips [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
        .st-key-queue_score_guidance {{ padding: 0.7rem; }}
    }}

    /* ---- Selected Case Review: compact selected-case strip. Same muted-amber
       selection role as the Review Queue banner — "the case you are carrying",
       never an alarm. Facts + score + quality + the change-case control sit on
       one wash; ink text carries the identity, amber only marks selection. ---- */
    .st-key-case_strip {{
        background: {sel_bg};
        border: 1px solid {sel_acc};
        border-left: 4px solid {sel_acc};
        border-radius: 10px;
        padding: 0.55rem 0.95rem 0.65rem 0.95rem;
        box-shadow: 0 2px 8px {shadow};
    }}
    .case-strip-facts {{
        color: {p["ink"]};
        font-size: 1.02rem;
        line-height: 1.45;
        overflow-wrap: anywhere;
    }}
    .case-strip-facts strong {{ font-weight: 800; }}
    .case-strip-metric {{
        display: flex;
        flex-direction: column;
        gap: 0.12rem;
    }}
    .case-strip-label {{
        color: {navy7};
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        line-height: 1.35;
    }}
    .case-strip-label svg {{ vertical-align: -3px; }}
    .case-strip-value {{
        color: {p["ink"]};
        font-size: 1.12rem;
        font-weight: 750;
        font-variant-numeric: tabular-nums;
    }}

    /* Case facts panel: quiet label/value rows on the white card surface. */
    .fact-list {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: {int(surfaces["radius_px"])}px;
        padding: 0.2rem 0.9rem;
    }}
    .fact-row {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        padding: 0.44rem 0;
        border-bottom: 1px solid {p["table_stripe"]};
    }}
    .fact-row:last-child {{ border-bottom: none; }}
    .fact-k {{
        color: {p["muted"]};
        font-size: 0.88rem;
        flex: 0 0 auto;
    }}
    .fact-k svg {{ vertical-align: -3px; }}
    .fact-v {{
        color: {p["ink"]};
        font-weight: 650;
        font-size: 0.92rem;
        text-align: right;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
    }}

    /* Carousel prev/next: keep the short arrow labels on one line — the
       columns stack to full width below Streamlit's narrow breakpoint, so
       nowrap can never clip there. */
    [data-testid="stMain"] .st-key-case_view_prev button p,
    [data-testid="stMain"] .st-key-case_view_next button p {{
        white-space: nowrap;
    }}

    /* One-line dynamic takeaway above each comparison view. */
    .case-takeaway {{
        color: {p["ink"]};
        font-size: 1.0rem;
        font-weight: 650;
        line-height: 1.45;
        margin: 0.1rem 0 0.3rem 0;
    }}

    /* ---- Why It Ranked High: summary · comparison cards · signals table ---- */
    .why-summary {{
        background: {p["accent_soft"]};
        border-left: 4px solid {p["accent"]};
        border-radius: 10px;
        padding: 0.8rem 1.1rem;
        color: {p["ink"]};
        font-size: 1.1rem;
        line-height: 1.5;
        margin: 0.1rem 0 0.35rem 0;
    }}
    .compare-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 10px;
        padding: 0.9rem 1.05rem 0.95rem 1.05rem;
        box-shadow: 0 4px 14px {shadow};
        height: 100%;
        display: flex;
        flex-direction: column;
    }}
    .compare-card-muted {{
        border-top-color: {p["border"]};
        background: {p["page_bg"]};
    }}
    .compare-head {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
    }}
    .compare-title {{
        color: {p["muted"]};
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}
    .compare-head .tip {{ color: {p["muted"]}; line-height: 1; }}
    .compare-head svg {{ vertical-align: middle; }}
    .compare-value {{
        color: {p["ink"]};
        font-size: 1.15rem;
        font-weight: 750;
        line-height: 1.34;
        margin: 0.4rem 0 0.2rem 0;
    }}
    .compare-card-muted .compare-value {{
        color: {p["muted"]};
        font-weight: 650;
        font-size: 1.0rem;
    }}
    .compare-secondary {{
        color: {at};
        font-size: 0.86rem;
        font-weight: 650;
        margin-bottom: 0.25rem;
    }}
    .compare-support {{
        color: {p["muted"]};
        font-size: 0.9rem;
        line-height: 1.45;
        margin-top: auto;
    }}
    .signals-scroll {{ max-height: 460px; overflow-y: auto; }}
    table.data-table td.mono {{
        font-family: "Consolas", "SFMono-Regular", monospace;
        font-size: 0.83rem;
        white-space: nowrap;
        color: {p["ink"]};
    }}
    table.data-table td[title] {{ cursor: help; }}

    /* ---- Landing page (Business Problem & Value): narrative sections ---- */
    .hero-block {{ padding: 0.3rem 0 0.4rem 0; }}
    .hero-block .page-title {{
        font-size: 2.45rem;
        letter-spacing: -0.012em;
        max-width: 30ch;
    }}
    .hero-block .page-subtitle {{
        font-size: 1.12rem;
        max-width: 62ch;
        margin-top: 0.55rem;
        margin-bottom: 0.4rem;
    }}

    .landing-section {{ margin: 1.5rem 0 0.4rem 0; }}
    .landing-heading {{
        color: {p["ink"]};
        font-size: 1.26rem;
        font-weight: 750;
        margin-bottom: 0.5rem;
    }}
    .landing-heading::before {{
        content: "";
        display: block;
        width: 26px;
        height: 3px;
        border-radius: 2px;
        background: {p["accent"]};
        margin-bottom: 0.45rem;
    }}
    .landing-prose {{
        color: {p["ink"]};
        font-size: 1rem;
        line-height: 1.62;
        max-width: 76ch;
        margin: 0.35rem 0 0.6rem 0;
    }}

    /* Twin cards: the challenge (recessive gray rule) vs the project response
       (Steel rule) — same emphasis convention as the charts. */
    .twin-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.9rem;
        margin: 0.8rem 0 0.4rem 0;
    }}
    .twin-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {theme["chart"]["context_gray"]};
        border-radius: 10px;
        padding: 0.95rem 1.15rem 0.85rem 1.15rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out, box-shadow {hover_ms}ms ease-out;
    }}
    .twin-card.response {{ border-top-color: {p["accent"]}; }}
    .twin-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(35, 53, 77, 0.16);
    }}
    .twin-label {{
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: {p["muted"]};
        margin-bottom: 0.35rem;
    }}
    .twin-card.response .twin-label {{ color: {at}; }}
    .twin-card ul {{
        margin: 0.2rem 0 0 1.1rem;
        padding: 0;
        color: {p["ink"]};
    }}
    .twin-card li {{ margin: 0.3rem 0; line-height: 1.5; }}

    /* Commodity chips: colour dot + name — colour never stands alone. The
       inset ring keeps the dot visible even for the lighter family hues. */
    .chip-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin: 0.15rem 0 0.7rem 0;
    }}
    .chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 999px;
        padding: 0.28rem 0.85rem;
        color: {p["ink"]};
        font-size: 0.92rem;
        font-weight: 600;
    }}
    .chip-dot {{
        background: {p["accent"]};
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex: none;
        box-shadow: inset 0 0 0 1px rgba(35, 53, 77, 0.30);
    }}

    /* Stat band: what stakeholders receive. */
    .stat-band {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.9rem;
        margin: 0.6rem 0 0.7rem 0;
    }}
    .stat-tile {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 10px;
        padding: 0.95rem 1.05rem 0.85rem 1.05rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out, box-shadow {hover_ms}ms ease-out;
    }}
    .stat-tile.acc-blue,
    .stat-tile.acc-teal,
    .stat-tile.acc-amber,
    .stat-tile.acc-green,
    .stat-tile.acc-violet {{ border-top-color: {kpi["accent"]}; }}
    .stat-tile:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(35, 53, 77, 0.16);
    }}
    .stat-value {{
        color: {p["ink"]};
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }}
    .stat-label {{
        color: {at};
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 0.2rem;
    }}
    .stat-detail {{
        color: {p["muted"]};
        font-size: 0.86rem;
        line-height: 1.45;
        margin-top: 0.35rem;
    }}
    .kpi-card {{
        display: flex;
        gap: 0.85rem;
        min-height: {int(kpi["min_height_px"])}px;
    }}
    .kpi-icon {{ background: {kpi["icon_bg"]}; color: {kpi["icon_color"]}; }}
    .kpi-copy {{ min-width: 0; }}

    /* Pipeline flow strip. */
    .flow-strip {{
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.55rem;
        margin: 0.55rem 0 0.6rem 0;
    }}
    .flow-step {{
        background: {p["accent_soft"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        padding: 0.5rem 0.95rem;
        color: {p["ink"]};
        font-size: 0.95rem;
        font-weight: 650;
        transition: background-color {hover_ms}ms ease-out, border-color {hover_ms}ms ease-out;
    }}
    .flow-step:hover {{
        background: {p["panel_bg"]};
        border-color: {p["accent"]};
    }}
    .flow-arrow {{
        color: {p["accent"]};
        font-weight: 700;
        user-select: none;
    }}

    /* Before / with-this-project question reframe. */
    .quote-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.9rem;
        margin: 0.6rem 0 0.8rem 0;
    }}
    .quote-card {{
        border-radius: 10px;
        padding: 0.95rem 1.15rem;
        box-shadow: 0 4px 14px {shadow};
    }}
    .quote-card.before {{
        background: {p.get("table_stripe", "#EFF3FA")};
        border: 1px solid {p["border"]};
    }}
    .quote-card.after {{
        background: {b["bg"]};
        border: 1px solid {b["border"]};
    }}
    .quote-label {{
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
        color: {p["muted"]};
    }}
    .quote-card.after .quote-label {{ color: {b.get("label", b["ink"])}; }}
    .quote-text {{
        font-size: 1.12rem;
        font-weight: 650;
        line-height: 1.45;
        color: {p["ink"]};
    }}
    .quote-card.after .quote-text {{ color: {b["ink"]}; }}

    /* Bottom line: the one-sentence summary strip on navy, echoing the sidebar. */
    .bottom-line {{
        background: {p["sidebar_bg"]};
        border-radius: 12px;
        padding: 1.1rem 1.35rem;
        margin-top: 0.4rem;
    }}
    .bottom-line-text {{
        color: {p["sidebar_ink"]};
        font-size: 1.06rem;
        line-height: 1.55;
        font-weight: 500;
        max-width: 90ch;
    }}
    .value-chip-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }}
    .value-chip {{
        border: 1px solid rgba(234, 240, 248, 0.45);
        border-radius: 999px;
        padding: 0.18rem 0.75rem;
        color: {p["sidebar_ink"]};
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }}

    @media (max-width: 900px) {{
        .stat-band {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    @media (max-width: 780px) {{
        .twin-grid, .quote-grid {{ grid-template-columns: 1fr; }}
        .hero-block .page-title {{ font-size: 2rem; }}
    }}
    @media (max-width: 560px) {{
        .stat-band {{ grid-template-columns: 1fr; }}
    }}

    /* ================================================================
       Business Problem & Value: balanced narrative grid + manual story
       module. Everything is scoped to the keyed page container so the
       generic landing primitives remain available to other pages.
       ================================================================ */
    .st-key-business_value_page {{
        width: 100%;
        max-width: 1220px;
        margin-inline: auto;
    }}
    .business-value-page {{ display: none; }}
    .st-key-business_value_page .hero-block {{
        padding: 0.35rem 0 0;
        margin-bottom: 3.35rem;
    }}
    .st-key-business_value_page .hero-block .page-title {{
        font-size: 2.55rem;
        line-height: 1.1;
        letter-spacing: 0;
        max-width: 29ch;
    }}
    .st-key-business_value_page .hero-block .page-subtitle {{
        max-width: 72ch;
        margin-top: 0.75rem;
        margin-bottom: 0;
        line-height: 1.55;
    }}
    .st-key-business_value_page .bv-section {{
        margin: 0 0 3.75rem 0;
    }}
    .st-key-business_value_page .story-section-header {{
        margin-bottom: 1.45rem;
    }}
    .st-key-business_value_page .story-section-title {{
        color: {p["ink"]};
        font-size: 1.32rem;
        font-weight: 760;
        line-height: 1.3;
    }}
    .st-key-business_value_page .story-section-rule {{
        position: relative;
        height: 1px;
        margin-top: 0.7rem;
        background: {p["border"]};
    }}
    .st-key-business_value_page .story-section-rule::before {{
        content: "";
        position: absolute;
        inset: -1px auto auto 0;
        width: 34px;
        height: 3px;
        background: {p["accent"]};
        border-radius: 2px;
    }}
    .st-key-business_value_page .bv-readable {{ max-width: 110ch; }}
    .st-key-business_value_page .landing-prose {{
        max-width: none;
        font-size: 1rem;
        line-height: 1.64;
        margin: 0 0 0.75rem 0;
    }}

    /* Challenge / response: equal, restrained comparison surfaces. */
    .st-key-business_value_page .twin-grid {{
        align-items: stretch;
        gap: 1rem;
        margin: 1.25rem 0 0 0;
    }}
    .st-key-business_value_page .twin-card {{
        display: flex;
        flex-direction: column;
        min-height: 154px;
        border-radius: 8px;
        border-top-color: {challenge_accent};
        padding: 1rem 1.15rem;
        box-shadow: 0 2px 8px {shadow};
        transition: border-color {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_page .twin-card.response {{ border-top-color: {p["accent"]}; }}
    .st-key-business_value_page .twin-card:hover {{
        transform: none;
        box-shadow: 0 2px 8px {shadow};
    }}
    .st-key-business_value_page .twin-card.challenge .twin-label {{ color: {challenge_accent}; }}

    /* Four stakeholder outputs: same anatomy, restrained semantic accents. */
    .st-key-business_value_page .stat-band {{
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin: 0;
    }}
    .st-key-business_value_page .stat-tile {{
        min-height: 150px;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px {shadow};
    }}
    .st-key-business_value_page .stat-tile:hover {{
        transform: none;
        box-shadow: 0 2px 8px {shadow};
    }}
    .st-key-business_value_page .kpi-icon {{ width: 38px; height: 38px; }}
    .st-key-business_value_page .outcome-teal {{ border-top-color: {p["accent"]}; }}
    .st-key-business_value_page .outcome-blue {{ border-top-color: {outcome_blue}; }}
    .st-key-business_value_page .outcome-amber {{ border-top-color: {outcome_amber}; }}
    .st-key-business_value_page .outcome-navy {{ border-top-color: {navy7}; }}
    .st-key-business_value_page .outcome-teal .stat-label {{ color: {p["accent"]}; }}
    .st-key-business_value_page .outcome-blue .stat-label {{ color: {outcome_blue}; }}
    .st-key-business_value_page .outcome-amber .stat-label {{ color: {outcome_amber}; }}
    .st-key-business_value_page .outcome-navy .stat-label {{ color: {navy7}; }}
    .st-key-business_value_page .outcome-blue .kpi-icon {{
        color: {outcome_blue};
        background: color-mix(in srgb, {outcome_blue} 12%, white);
    }}
    .st-key-business_value_page .outcome-amber .kpi-icon {{
        color: {outcome_amber};
        background: color-mix(in srgb, {outcome_amber} 14%, white);
    }}
    .st-key-business_value_page .outcome-navy .kpi-icon {{
        color: {navy7};
        background: color-mix(in srgb, {navy7} 11%, white);
    }}
    .st-key-business_value_stakeholders {{ margin-bottom: 3.75rem; }}
    .st-key-business_value_stakeholders .bv-section {{ margin-bottom: 0.7rem; }}

    /* Manual story selector: all options visible, stable-height content. */
    .st-key-business_value_page .bv-explore {{ margin-bottom: 0.2rem; }}
    .st-key-business_value_story {{ margin-bottom: 3.75rem; }}
    .st-key-business_value_story_tab {{
        width: min(720px, 100%);
    }}
    .st-key-business_value_story_tab [data-testid="stButtonGroup"],
    .st-key-business_value_story_tab [role="radiogroup"] {{
        width: 100%;
        display: flex;
    }}
    .st-key-business_value_story_tab [role="radiogroup"] {{
        flex: 1 1 auto;
        max-width: none;
    }}
    .st-key-business_value_story_tab [role="radio"] {{
        flex: 1 1 0;
        min-width: 0;
        min-height: 48px;
        padding: 0.55rem 0.8rem;
        transition: background-color {standard_ms}ms {motion_easing},
                    border-color {standard_ms}ms {motion_easing},
                    color {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_story_tab button p {{
        white-space: nowrap;
        text-align: center;
        line-height: 1.25;
    }}
    .st-key-business_value_story .story-panel {{
        min-height: 278px;
        margin-top: 0.8rem;
        padding: 1.25rem 1.35rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        box-shadow: 0 2px 8px {shadow};
        animation: bv-panel-in {standard_ms}ms {motion_easing} both;
    }}
    .st-key-business_value_story .story-panel-heading {{
        color: {p["ink"]};
        font-size: 1.12rem;
        font-weight: 750;
        line-height: 1.35;
        margin-bottom: 0.8rem;
    }}
    .st-key-business_value_story .landing-prose:last-child {{ margin-bottom: 0; }}

    /* Editorial product-family cards; family colour remains local here. */
    .st-key-business_value_story .commodity-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 1rem 0;
    }}
    .st-key-business_value_story .commodity-card {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 0;
        min-height: 94px;
        padding: 0.85rem 0.9rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 8px;
        box-shadow: 0 2px 8px {shadow};
        transition: border-color {standard_ms}ms {motion_easing},
                    box-shadow {standard_ms}ms {motion_easing},
                    transform {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_story .commodity-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px {shadow};
    }}
    .st-key-business_value_story .commodity-icon {{
        width: 38px;
        height: 38px;
        flex: none;
        transition: transform {fast_ms}ms {motion_easing};
    }}
    .st-key-business_value_story .commodity-card:hover .commodity-icon {{
        transform: scale(1.02);
    }}
    .st-key-business_value_story .commodity-title {{
        min-width: 0;
        color: {p["ink"]};
        font-size: 0.91rem;
        font-weight: 700;
        line-height: 1.35;
        overflow-wrap: anywhere;
    }}
    .st-key-business_value_story .family-crude-palm-oil {{
        border-top-color: {family_colors["crude_palm_oil"]};
    }}
    .st-key-business_value_story .family-crude-palm-oil .commodity-icon {{
        color: {family_colors["crude_palm_oil"]};
        background: color-mix(in srgb, {family_colors["crude_palm_oil"]} 13%, white);
    }}
    .st-key-business_value_story .family-refined-copper-cathodes {{
        border-top-color: {family_colors["refined_copper_cathodes"]};
    }}
    .st-key-business_value_story .family-refined-copper-cathodes .commodity-icon {{
        color: {family_colors["refined_copper_cathodes"]};
        background: color-mix(in srgb, {family_colors["refined_copper_cathodes"]} 13%, white);
    }}
    .st-key-business_value_story .family-gold-unwrought {{
        border-top-color: {family_colors["gold_unwrought"]};
    }}
    .st-key-business_value_story .family-gold-unwrought .commodity-icon {{
        color: {family_colors["gold_unwrought"]};
        background: color-mix(in srgb, {family_colors["gold_unwrought"]} 14%, white);
    }}

    /* Why-it-matters comparison and connected review-queue flow. */
    .st-key-business_value_story .quote-grid {{ margin: 0 0 1rem 0; }}
    .st-key-business_value_story .quote-card {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 116px;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        box-shadow: none;
    }}
    .st-key-business_value_story .story-process-flow {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1.35rem;
        margin-top: 1rem;
    }}
    .st-key-business_value_process_panel {{
        min-height: 278px;
        margin-top: 0.8rem;
        padding: 1.25rem 1.35rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        box-shadow: 0 2px 8px {shadow};
        animation: bv-panel-in {standard_ms}ms {motion_easing} both;
    }}
    .st-key-business_value_process_panel .story-panel-process {{
        min-height: 0;
        margin: 0;
        padding: 0;
        background: transparent;
        border: 0;
        border-radius: 0;
        box-shadow: none;
        animation: none;
    }}
    .st-key-business_value_process_panel [data-testid="stPageLink"] {{
        margin-top: 1rem;
    }}
    .st-key-business_value_story .story-process-stage {{
        --process-accent: {p["accent"]};
        position: relative;
        min-width: 0;
        min-height: 118px;
        padding: 0.9rem;
        background: color-mix(in srgb, var(--process-accent) 7%, white);
        border: 1px solid color-mix(in srgb, var(--process-accent) 28%, white);
        border-top: 3px solid var(--process-accent);
        border-radius: 8px;
        animation: bv-panel-in {standard_ms}ms {motion_easing} both;
    }}
    .st-key-business_value_story .story-process-stage:not(:last-child)::after {{
        content: "→";
        position: absolute;
        top: 50%;
        right: -1.02rem;
        color: var(--process-accent);
        font-size: 1rem;
        font-weight: 800;
        transform: translateY(-50%);
    }}
    .st-key-business_value_story .process-stage-1 {{ --process-accent: {outcome_blue}; }}
    .st-key-business_value_story .process-stage-2 {{
        --process-accent: {family_colors["refined_copper_cathodes"]};
        animation-delay: {landing_stagger_ms}ms;
    }}
    .st-key-business_value_story .process-stage-3 {{
        --process-accent: {p["accent"]};
        animation-delay: {landing_stagger_ms * 2}ms;
    }}
    .st-key-business_value_story .process-stage-4 {{
        --process-accent: {family_colors["crude_palm_oil"]};
        animation-delay: {landing_stagger_ms * 3}ms;
    }}
    .st-key-business_value_story .process-stage-meta {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.65rem;
    }}
    .st-key-business_value_story .process-stage-number {{
        display: inline-grid;
        place-items: center;
        width: 1.55rem;
        height: 1.55rem;
        border-radius: 50%;
        color: #FFFFFF;
        background: var(--process-accent);
        font-size: 0.72rem;
        font-weight: 800;
    }}
    .st-key-business_value_story .process-stage-icon {{
        width: 1.15rem;
        height: 1.15rem;
        color: var(--process-accent);
    }}
    .st-key-business_value_story .process-stage-title {{
        color: {p["ink"]};
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1.35;
        overflow-wrap: anywhere;
    }}

    .st-key-business_value_page .bv-final {{ margin-bottom: 0.4rem; }}
    .st-key-business_value_page .bottom-line {{
        border-radius: 8px;
        padding: 1.25rem 1.35rem;
        box-shadow: 0 2px 8px {shadow};
    }}
    .st-key-business_value_page .bottom-line-text {{ max-width: none; }}

    @keyframes bv-rise-in {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes bv-panel-in {{
        from {{ opacity: 0; transform: translateY(3px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .st-key-business_value_page .bv-entry {{
        animation: bv-rise-in {landing_entry_ms}ms {motion_easing} both;
    }}
    .st-key-business_value_page .bv-d1 {{ animation-delay: {landing_stagger_ms}ms; }}
    .st-key-business_value_page .bv-d2 {{ animation-delay: {landing_stagger_ms * 2}ms; }}
    .st-key-business_value_page .bv-d3 {{ animation-delay: {landing_stagger_ms * 3}ms; }}
    .st-key-business_value_page .bv-d4 {{ animation-delay: {landing_stagger_ms * 4}ms; }}

    @media (max-width: 1100px) {{
        .st-key-business_value_page .stat-band {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .st-key-business_value_story .story-process-flow {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .st-key-business_value_story .story-process-stage::after {{ display: none; }}
    }}
    @media (max-width: 780px) {{
        .st-key-business_value_page .hero-block {{ margin-bottom: 2.75rem; }}
        .st-key-business_value_page .hero-block .page-title {{ font-size: 2rem; }}
        .st-key-business_value_page .bv-section,
        .st-key-business_value_stakeholders,
        .st-key-business_value_story {{ margin-bottom: 3rem; }}
        .st-key-business_value_story .commodity-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 600px) {{
        .st-key-business_value_page .stat-band,
        .st-key-business_value_story .story-process-flow {{ grid-template-columns: 1fr; }}
        .st-key-business_value_story_tab [role="radiogroup"] {{ flex-wrap: wrap; }}
        .st-key-business_value_story_tab [role="radio"] {{
            flex: 1 1 100%;
        }}
        .st-key-business_value_story .story-panel {{
            min-height: 0;
            padding: 1rem;
        }}
        .st-key-business_value_process_panel {{
            min-height: 0;
            padding: 1rem;
        }}
    }}

    /* ---- Bank Implementation Pathway: future-state operating model. ---- */
    .bank-section-heading {{ margin-bottom: 0.7rem; max-width: 82ch; }}
    .bank-section-title {{
        color: {p["ink"]};
        font-size: 1.26rem;
        font-weight: 750;
    }}
    .bank-section-title::before {{
        content: "";
        display: block;
        width: 26px;
        height: 3px;
        border-radius: 2px;
        background: {p["accent"]};
        margin-bottom: 0.45rem;
    }}
    .bank-section-caption {{
        color: {p["muted"]};
        font-size: 0.9rem;
        line-height: 1.5;
        margin-top: 0.25rem;
    }}
    .bank-role .landing-prose {{ max-width: 84ch; }}

    .bank-architecture {{
        display: grid;
        grid-template-columns: minmax(0, 0.9fr) 9rem minmax(0, 1.1fr);
        gap: 1rem;
        align-items: center;
        margin-top: 0.9rem;
    }}
    .bank-state {{
        min-width: 0;
        padding: 1rem;
        background: {p.get("table_stripe", "#EFF3FA")};
        border-top: 3px solid {theme["chart"]["context_gray"]};
    }}
    .bank-state-future {{
        background: {p["accent_soft"]};
        border-top-color: {p["accent"]};
    }}
    .bank-state-kicker {{
        color: {p["muted"]};
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}
    .bank-state-future .bank-state-kicker {{ color: {at}; }}
    .bank-state-title {{
        color: {p["ink"]};
        font-size: 1.08rem;
        font-weight: 750;
        margin: 0.15rem 0 0.7rem 0;
    }}
    .bank-flow {{ display: grid; gap: 0.45rem; }}
    .bank-flow-node {{
        display: grid;
        grid-template-columns: 1.65rem minmax(0, 1fr);
        gap: 0.65rem;
        align-items: start;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 6px;
        padding: 0.7rem 0.75rem;
    }}
    .bank-node-index {{
        display: inline-grid;
        place-items: center;
        width: 1.65rem;
        height: 1.65rem;
        border-radius: 50%;
        background: {p["accent_soft"]};
        border: 1px solid {p["border"]};
        color: {at};
        font-size: 0.76rem;
        font-weight: 800;
    }}
    .bank-node-copy {{ min-width: 0; }}
    .bank-node-title {{
        color: {p["ink"]};
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1.35;
    }}
    .bank-node-detail {{
        color: {p["muted"]};
        font-size: 0.8rem;
        line-height: 1.4;
        margin-top: 0.12rem;
        overflow-wrap: anywhere;
    }}
    .bank-flow-arrow {{
        color: {p["muted"]};
        font-size: 0.95rem;
        line-height: 0.8;
        text-align: center;
    }}
    .bank-bridge {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.45rem;
        color: {at};
        font-size: 0.78rem;
        font-weight: 750;
        line-height: 1.35;
        text-align: center;
    }}
    .bank-bridge svg {{ width: 1.45rem; height: 1.45rem; }}
    .bank-feedback-note {{
        display: flex;
        align-items: flex-start;
        gap: 0.55rem;
        color: {p["muted"]};
        background: {p["panel_bg"]};
        border-left: 3px solid {sel_acc};
        padding: 0.75rem 0.9rem;
        margin-top: 0.75rem;
        font-size: 0.82rem;
        line-height: 1.45;
    }}
    .bank-feedback-note svg {{
        color: {sel_acc};
        width: 1.05rem;
        height: 1.05rem;
        flex: none;
        margin-top: 0.08rem;
    }}

    .bank-domain-grid, .bank-value-grid {{ display: grid; gap: 0.8rem; }}
    .bank-domain-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .bank-value-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .bank-icon-card {{
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        min-width: 0;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.85rem;
        box-shadow: 0 4px 14px {shadow};
    }}
    .bank-icon-card.value {{ border-top-color: {navy7}; }}
    .bank-card-icon {{ background: {p["accent_soft"]}; color: {at}; flex: none; }}
    .bank-card-copy {{ min-width: 0; }}
    .bank-card-title {{
        color: {p["ink"]};
        font-size: 0.9rem;
        font-weight: 750;
        line-height: 1.35;
    }}
    .bank-card-detail {{
        color: {p["muted"]};
        font-size: 0.8rem;
        line-height: 1.45;
        margin-top: 0.25rem;
        overflow-wrap: anywhere;
    }}

    .bank-adoption {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0;
        margin-top: 0.75rem;
    }}
    .bank-stage {{
        position: relative;
        min-width: 0;
        padding: 0.1rem 1.25rem 0.25rem 0;
    }}
    .bank-stage:not(:last-child)::after {{
        content: "";
        position: absolute;
        top: 1rem;
        left: 2.2rem;
        right: 0.45rem;
        height: 2px;
        background: {p["border"]};
        z-index: 0;
    }}
    .bank-stage-number {{
        position: relative;
        z-index: 1;
        display: grid;
        place-items: center;
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        background: {p["accent"]};
        color: white;
        font-size: 0.82rem;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }}
    .bank-stage-title {{ color: {p["ink"]}; font-size: 0.92rem; font-weight: 750; line-height: 1.35; }}
    .bank-stage-detail {{
        color: {p["muted"]};
        font-size: 0.82rem;
        line-height: 1.5;
        margin-top: 0.25rem;
        overflow-wrap: anywhere;
    }}

    .bank-controls {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.7rem 1.2rem;
        background: {p.get("table_stripe", "#EFF3FA")};
        border-left: 3px solid {navy7};
        padding: 0.9rem 1rem;
    }}
    .bank-control-item {{
        display: grid;
        grid-template-columns: 1.2rem minmax(0, 1fr);
        gap: 0.55rem;
        align-items: start;
        min-width: 0;
    }}
    .bank-control-item > svg {{
        color: {at};
        width: 1.05rem;
        height: 1.05rem;
        margin-top: 0.12rem;
    }}
    .bank-control-title {{ color: {p["ink"]}; font-size: 0.86rem; font-weight: 750; }}
    .bank-control-detail {{
        color: {p["muted"]};
        font-size: 0.79rem;
        line-height: 1.45;
        margin-top: 0.15rem;
        overflow-wrap: anywhere;
    }}

    @media (max-width: 1050px) {{
        .bank-domain-grid, .bank-value-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 780px) {{
        .bank-architecture {{ grid-template-columns: 1fr; }}
        .bank-bridge {{ flex-direction: row; justify-content: center; padding: 0.2rem 0; }}
        .bank-bridge svg {{ transform: rotate(90deg); }}
        .bank-adoption {{ grid-template-columns: 1fr; gap: 0.9rem; }}
        .bank-stage {{ padding-right: 0; padding-left: 2.8rem; }}
        .bank-stage-number {{ position: absolute; left: 0; top: 0; }}
        .bank-stage:not(:last-child)::after {{
            top: 2rem;
            bottom: -0.9rem;
            left: 0.95rem;
            right: auto;
            width: 2px;
            height: auto;
        }}
    }}
    @media (max-width: 560px) {{
        .bank-domain-grid, .bank-value-grid, .bank-controls {{ grid-template-columns: 1fr; }}
        .bank-icon-card {{ padding: 0.75rem; }}
    }}

    /* ================================================================
       Methodology story page (From Data to Review Queue): sticky mental-
       model strip, five-tile trust band, three scenes with storyboard
       entrances, source/family hover previews, preparation pipeline,
       derived funnel, time-safety year strip, and the official-vs-
       evaluation fork. All colours come from theme tokens; every animated
       selector here is also listed in the reduced-motion block at the end.
       ================================================================ */

    /* Sticky mental-model strip. The sticky must sit on the ELEMENT
       CONTAINER (the strip's own wrapper is exactly its own height, so
       sticky on the inner div would never engage). top clears Streamlit's
       fixed header; z-index 55 stays below the sidebar (100) and the
       boundary ribbon (60). */
    [data-testid="stElementContainer"]:has(.mental-model) {{
        position: sticky;
        top: 3.75rem;
        z-index: 55;
    }}
    .mental-model {{
        background: {mm["bg"]};
        color: {mm["ink"]};
        display: flex;
        align-items: center;
        gap: 0.8rem;
        min-height: {int(theme["components"]["banner"]["min_height_px"])}px;
        border-radius: 9px;
        border-left: 3px solid {mm["accent"]};
        box-shadow: 0 4px 14px rgba(2, 18, 47, 0.24);
        padding: {int(theme["components"]["banner"]["padding_y_px"])}px {int(theme["components"]["banner"]["padding_x_px"])}px;
        font-size: 0.92rem;
        line-height: 1.45;
    }}
    .mental-model .mm-stamp {{
        color: {p["sidebar_muted"]};
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-right: 0.6rem;
        white-space: nowrap;
    }}
    .banner-icon {{ background: {mm["icon_bg"]}; color: {mm["accent"]}; }}
    [data-testid="stElementContainer"]:has(.mental-model.future-boundary) {{
        position: static;
        top: auto;
        z-index: auto;
    }}

    /* Five-tile trust band (extends the landing stat-band). */
    .stat-band.five {{ grid-template-columns: repeat(5, 1fr); }}
    @media (max-width: 1250px) {{ .stat-band.five {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (max-width: 900px) {{ .stat-band.five {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 560px) {{ .stat-band.five {{ grid-template-columns: 1fr; }} }}

    /* Scene indicator pill next to the stage controls. */
    .scene-indicator {{
        display: inline-block;
        color: {p["muted"]};
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.3rem 0;
        white-space: nowrap;
    }}

    /* Storyboard beats: one fade-up, staggered so each scene reads as a
       sequence on entry and on Replay (the page remounts the scene DOM by
       changing a data-replay attribute). */
    .sb {{ animation: rise-in {entry_ms}ms ease-out both; }}
    .sb.b1 {{ animation-delay: {scene_ms}ms; }}
    .sb.b2 {{ animation-delay: {scene_ms * 2}ms; }}
    .sb.b3 {{ animation-delay: {scene_ms * 3}ms; }}
    .sb.b4 {{ animation-delay: {scene_ms * 4}ms; }}
    .sb.b5 {{ animation-delay: {scene_ms * 5}ms; }}
    .sb.b6 {{ animation-delay: {scene_ms * 6}ms; }}
    .sb.b7 {{ animation-delay: {scene_ms * 7}ms; }}
    .sb.b8 {{ animation-delay: {scene_ms * 8}ms; }}

    /* ---- Scene 1: source cards with CSS-only hover/focus previews ---- */
    .src-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.9rem;
        margin: 0.55rem 0 0.6rem 0;
    }}
    .src-card {{
        position: relative;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 10px;
        padding: 0.9rem 1.05rem 0.8rem 1.05rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out, box-shadow {hover_ms}ms ease-out;
    }}
    .src-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(35, 53, 77, 0.16);
    }}
    .src-card:focus-visible {{
        outline: 2px solid {p["accent"]};
        outline-offset: 2px;
    }}
    .source-card-head {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.55rem;
    }}
    .src-kicker {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: {at};
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }}
    .src-card.src-baci,
    .src-card.source-role-official {{ border-top-color: {source_roles["official"]["accent"]}; }}
    .src-card.src-worldbank,
    .src-card.source-role-benchmark {{ border-top-color: {source_roles["benchmark"]["accent"]}; }}
    .src-card.src-fatf,
    .src-card.source-role-typology {{ border-top-color: {source_roles["typology"]["accent"]}; }}
    .src-card.src-baci .src-kicker,
    .src-card.src-baci .src-lab,
    .source-role-official .src-kicker,
    .source-role-official .src-lab,
    .source-role-official .src-hint {{ color: {source_roles["official"]["text"]}; }}
    .src-card.src-worldbank .src-kicker,
    .src-card.src-worldbank .src-lab,
    .source-role-benchmark .src-kicker,
    .source-role-benchmark .src-lab,
    .source-role-benchmark .src-hint {{ color: {source_roles["benchmark"]["text"]}; }}
    .src-card.src-fatf .src-kicker,
    .src-card.src-fatf .src-lab,
    .source-role-typology .src-kicker,
    .source-role-typology .src-lab,
    .source-role-typology .src-hint {{ color: {source_roles["typology"]["text"]}; }}
    .source-role-official .source-icon {{
        color: {source_roles["official"]["accent"]};
        background: {source_roles["official"]["soft"]};
    }}
    .source-role-benchmark .source-icon {{
        color: {source_roles["benchmark"]["accent"]};
        background: {source_roles["benchmark"]["soft"]};
    }}
    .source-role-typology .source-icon {{
        color: {source_roles["typology"]["accent"]};
        background: {source_roles["typology"]["soft"]};
    }}
    .src-name {{
        color: {p["ink"]};
        font-size: 1.12rem;
        font-weight: 750;
        margin: 0.15rem 0 0.45rem 0;
    }}
    .src-lab {{
        display: block;
        color: {p["muted"]};
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 0.12rem;
    }}
    .src-row {{
        color: {p["ink"]};
        font-size: 0.88rem;
        line-height: 1.5;
        margin: 0 0 0.55rem 0;
    }}
    .src-row.src-boundary {{
        border-top: 1px dashed {p["border"]};
        padding-top: 0.5rem;
        margin-bottom: 0.2rem;
    }}
    .src-never ul {{
        margin: 0.1rem 0 0 1.05rem;
        padding: 0;
    }}
    .src-never li {{ margin: 0.12rem 0; }}
    .appendix-source-card {{ margin-bottom: 0.85rem; }}
    .appendix-source-card .source-row {{
        color: {p["ink"]};
        font-size: 0.86rem;
        line-height: 1.45;
        padding: 0.3rem 0;
        border-top: 1px dashed {p["border"]};
    }}
    .appendix-source-card .source-row b {{
        color: inherit;
        font-weight: 750;
    }}
    .src-hint {{
        color: {p["muted"]};
        font-size: 0.72rem;
        margin-top: 0.45rem;
    }}
    /* Hover preview: an absolutely-positioned overlay (no layout shift),
       navy like the tooltips, opened on hover AND :focus-within. */
    .src-preview {{
        position: absolute;
        left: 0.5rem;
        right: 0.5rem;
        bottom: 0.5rem;
        z-index: 6;
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        border: 1px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.6rem 0.75rem;
        font-size: 0.8rem;
        line-height: 1.45;
        box-shadow: 0 10px 24px rgba(2, 18, 47, 0.32);
        opacity: 0;
        visibility: hidden;
        transform: translateY(6px);
        transition: opacity 180ms ease-out, transform 180ms ease-out,
                    visibility 0s linear 180ms;
        pointer-events: none;
    }}
    .src-card:hover .src-preview,
    .src-card:focus-within .src-preview {{
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
        transition: opacity 180ms ease-out, transform 180ms ease-out, visibility 0s;
    }}
    .pv-title {{
        color: {p["sidebar_muted"]};
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .pv-row {{
        display: flex;
        justify-content: space-between;
        gap: 0.6rem;
        padding: 0.06rem 0;
    }}
    .pv-k {{ color: {p["sidebar_muted"]}; white-space: nowrap; }}
    .pv-v {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .pv-cap {{
        color: {p["sidebar_muted"]};
        font-size: 0.7rem;
        margin-top: 0.35rem;
        line-height: 1.4;
    }}

    /* Unit of analysis: equation + corridor visual. */
    .unit-eq {{
        display: inline-block;
        background: {p["accent_soft"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        color: {p["ink"]};
        font-size: 0.95rem;
        font-weight: 650;
        padding: 0.5rem 0.95rem;
        margin: 0.2rem 0 0.65rem 0;
    }}
    .corridor-visual {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.3rem;
        margin: 0.5rem 0 0.6rem 0;
    }}
    .cv-lane {{
        display: flex;
        align-items: center;
        width: 100%;
        max-width: 660px;
    }}
    .cv-node {{
        flex: none;
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        border-radius: 9px;
        padding: 0.45rem 0.9rem;
        text-align: center;
    }}
    .cv-role {{
        display: block;
        color: {p["sidebar_muted"]};
        font-size: 0.62rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
    }}
    .cv-name {{ font-weight: 700; font-size: 0.94rem; }}
    .cv-link {{
        flex: 1 1 auto;
        position: relative;
        text-align: center;
        padding: 0 0.5rem;
        min-width: 120px;
    }}
    .cv-link::before {{
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        top: 50%;
        border-top: 2px solid {p["accent"]};
    }}
    .cv-link span {{
        position: relative;
        z-index: 1;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 999px;
        color: {p["ink"]};
        font-size: 0.76rem;
        font-weight: 650;
        padding: 0.16rem 0.6rem;
        white-space: nowrap;
    }}
    .cv-year {{ color: {p["muted"]}; font-size: 0.8rem; }}
    .cv-arrow {{ color: {p["accent"]}; font-weight: 700; line-height: 1; }}
    .cv-row-chip {{
        background: {p["panel_bg"]};
        border: 1px solid {p["accent"]};
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        color: {p["ink"]};
        font-size: 0.88rem;
        padding: 0.45rem 0.9rem;
    }}
    .twin-card p {{
        margin: 0;
        color: {p["ink"]};
        font-size: 0.92rem;
        line-height: 1.5;
    }}

    /* Family cards (why these three products) with the same reveal overlay. */
    .fam-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.9rem;
        margin: 0.55rem 0 0.55rem 0;
    }}
    .fam-card {{
        position: relative;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 0.8rem 0.95rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out, box-shadow {hover_ms}ms ease-out;
    }}
    .fam-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(35, 53, 77, 0.16);
    }}
    .fam-card:focus-visible {{
        outline: 2px solid {p["accent"]};
        outline-offset: 2px;
    }}
    .fam-head {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.15rem;
    }}
    .fam-name {{ color: {p["ink"]}; font-weight: 750; font-size: 0.98rem; }}
    .fam-role {{
        color: {at};
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .fam-body {{
        color: {p["ink"]};
        font-size: 0.85rem;
        line-height: 1.5;
    }}
    .tag-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.35rem 0 0.55rem 0;
    }}
    .tag {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 999px;
        color: {at};
        font-size: 0.74rem;
        font-weight: 700;
        padding: 0.16rem 0.6rem;
    }}

    /* ---- Scene 2: preparation pipeline ---- */
    .pipe-strip {{
        display: flex;
        flex-wrap: wrap;
        align-items: stretch;
        gap: 0.5rem;
        margin: 0.55rem 0 0.75rem 0;
    }}
    .pipe-stage {{
        flex: 1 1 170px;
        min-width: 160px;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 0.65rem 0.8rem;
        box-shadow: 0 4px 14px {shadow};
    }}
    .pipe-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        font-size: 0.74rem;
        font-weight: 800;
    }}
    .pipe-title {{
        color: {p["ink"]};
        font-size: 0.9rem;
        font-weight: 750;
        margin: 0.3rem 0 0.15rem 0;
    }}
    .pipe-body {{
        color: {p["muted"]};
        font-size: 0.78rem;
        line-height: 1.45;
    }}
    .pipe-arrow {{
        align-self: center;
        color: {p["accent"]};
        font-weight: 700;
        user-select: none;
    }}
    .prep-panel {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 10px;
        padding: 0.8rem 0.95rem;
        margin-bottom: 0.15rem;
        box-shadow: 0 4px 14px {shadow};
    }}
    .prep-kicker {{
        color: {at};
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }}
    .prep-body {{
        color: {p["ink"]};
        font-size: 0.88rem;
        line-height: 1.52;
        margin: 0 0 0.45rem 0;
    }}
    .mini-note {{
        color: {p["muted"]};
        font-size: 0.78rem;
        line-height: 1.45;
        margin-top: 0.35rem;
    }}
    .file-card {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: {p.get("table_stripe", "#EFF3FA")};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        padding: 0.5rem 0.7rem;
        margin-bottom: 0.45rem;
    }}
    .file-doc {{
        flex: none;
        width: 24px;
        height: 30px;
        border: 2px solid {p["accent"]};
        border-radius: 3px;
        background:
            repeating-linear-gradient(
                to bottom,
                transparent 0 5px,
                {p["border"]} 5px 7px
            ) center / 60% 60% no-repeat,
            {p["panel_bg"]};
    }}
    .file-name {{ color: {p["ink"]}; font-size: 0.84rem; font-weight: 650; }}
    .verify-badge {{
        display: inline-block;
        color: {theme["status"]["quality"]["fully_usable"]["color"]};
        border: 1px solid currentColor;
        border-radius: 999px;
        background: {p["panel_bg"]};
        font-size: 0.72rem;
        font-weight: 800;
        padding: 0.08rem 0.5rem;
        margin-left: auto;
        white-space: nowrap;
    }}
    .conv-row {{
        display: block;
        background: {p["accent_soft"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        color: {p["ink"]};
        font-size: 0.86rem;
        font-weight: 600;
        padding: 0.42rem 0.7rem;
        margin: 0.3rem 0;
    }}
    /* Records merging into one clean row (plays on scene entry / Replay). */
    .merge-tiles {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.45rem;
        margin: 0.2rem 0;
    }}
    .merge-tile {{
        background: {p.get("table_stripe", "#EFF3FA")};
        border: 1px solid {p["border"]};
        border-radius: 6px;
        color: {p["muted"]};
        font-size: 0.74rem;
        font-weight: 650;
        padding: 0.28rem 0.55rem;
    }}
    .merge-tile.ma {{ animation: merge-a {entry_ms}ms ease-out {scene_ms * 2}ms both; }}
    .merge-tile.mb {{ animation: merge-b {entry_ms}ms ease-out {scene_ms * 3}ms both; }}
    .merge-tile.mc {{ animation: merge-c {entry_ms}ms ease-out {scene_ms * 4}ms both; }}
    .merge-arrow {{
        text-align: center;
        color: {p["accent"]};
        font-weight: 700;
        line-height: 1.1;
    }}
    .merge-row {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["accent"]};
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        color: {p["ink"]};
        font-size: 0.85rem;
        font-weight: 650;
        padding: 0.42rem 0.75rem;
        animation: rise-in {entry_ms}ms ease-out {scene_ms * 6}ms both;
    }}
    .merge-row .lineage {{
        color: {p["ledger_ink"]};
        font-family: "Consolas", "SFMono-Regular", monospace;
        font-size: 0.8rem;
    }}
    @keyframes merge-a {{
        from {{ opacity: 0; transform: translateX(-18px); }}
        to   {{ opacity: 1; transform: none; }}
    }}
    @keyframes merge-b {{
        from {{ opacity: 0; transform: translateY(-12px); }}
        to   {{ opacity: 1; transform: none; }}
    }}
    @keyframes merge-c {{
        from {{ opacity: 0; transform: translateX(18px); }}
        to   {{ opacity: 1; transform: none; }}
    }}

    /* Usability funnel — bar widths carry the derived share. */
    .funnel {{
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        margin: 0.45rem 0 0.25rem 0;
    }}
    .funnel-bar {{
        border-radius: 7px;
        font-size: 0.86rem;
        font-weight: 650;
        padding: 0.42rem 0.8rem;
        white-space: nowrap;
        width: fit-content;
        min-width: 40%;
    }}
    .funnel-bar.f1 {{
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        width: 100%;
    }}
    .funnel-bar.f2 {{
        background: {p["accent"]};
        color: {p["panel_bg"]};
    }}
    .funnel-drop {{
        color: {p["accent"]};
        font-weight: 700;
        margin-left: 1.1rem;
        line-height: 1;
    }}
    .funnel-note {{
        color: {p["ink"]};
        font-size: 0.86rem;
        margin-top: 0.15rem;
    }}

    /* Time-safety year strip. Final state = what reduced-motion users see:
       history lit, focus framed, later years greyed with a hidden tag. */
    .year-strip {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0.5rem 0 0.35rem 0;
    }}
    .yr {{
        border-radius: 7px;
        padding: 0.28rem 0.6rem;
        font-size: 0.84rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        text-align: center;
        line-height: 1.25;
    }}
    .yr small {{
        display: block;
        font-size: 0.58rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}
    .yr.lit {{ background: {p["accent"]}; color: {p["panel_bg"]}; }}
    .yr.focus {{
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        box-shadow: 0 0 0 2px {b.get("accent", p["accent"])};
    }}
    .yr.hid {{
        background: {p.get("table_stripe", "#EFF3FA")};
        border: 1px dashed {p["border"]};
        color: {p["muted"]};
    }}
    .yr.lit.yl1 {{ animation: lit-in 420ms ease-out {scene_ms * 2}ms both; }}
    .yr.lit.yl2 {{ animation: lit-in 420ms ease-out {scene_ms * 3}ms both; }}
    .yr.lit.yl3 {{ animation: lit-in 420ms ease-out {scene_ms * 4}ms both; }}
    .yr.lit.yl4 {{ animation: lit-in 420ms ease-out {scene_ms * 5}ms both; }}
    .yr.lit.yl5 {{ animation: lit-in 420ms ease-out {scene_ms * 6}ms both; }}
    .yr.focus.ylf {{ animation: lit-in 420ms ease-out {scene_ms * 7}ms both; }}
    @keyframes lit-in {{
        from {{ opacity: 0.15; }}
        to   {{ opacity: 1; }}
    }}
    .sig-chip-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.45rem 0 0.2rem 0;
    }}
    .sig-chip {{
        flex: 1 1 200px;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.42rem 0.7rem;
    }}
    .sig-name {{ color: {p["ink"]}; font-size: 0.84rem; font-weight: 750; }}
    .sig-q {{ color: {p["muted"]}; font-size: 0.78rem; line-height: 1.4; }}

    /* ---- Scene 3: the fork — official lane vs controlled evaluation copy.
       The wall is structural (dashed divider + label), never colour alone. ---- */
    .fork {{
        display: grid;
        grid-template-columns: 1fr 42px 1fr;
        gap: 0.75rem;
        align-items: stretch;
        margin: 0.55rem 0 0.4rem 0;
    }}
    .fork-top {{
        grid-column: 1 / -1;
        justify-self: center;
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        border-radius: 9px;
        font-weight: 750;
        font-size: 0.95rem;
        padding: 0.45rem 1.15rem;
    }}
    .fork-split {{
        grid-column: 1 / -1;
        display: grid;
        grid-template-columns: 1fr 42px 1fr;
        color: {p["accent"]};
        font-weight: 700;
        text-align: center;
        line-height: 1;
        user-select: none;
    }}
    .lane {{
        border-radius: 10px;
        padding: 0.8rem 0.95rem;
    }}
    .lane.official {{
        background: {p["panel_bg"]};
        border: 1px solid {p["accent"]};
        border-top: 3px solid {p["accent"]};
        box-shadow: 0 6px 16px rgba(35, 53, 77, 0.10);
    }}
    .lane.eval {{
        background: {ev["tint"]};
        border: 2px dashed {ev["border"]};
    }}
    .lane-kicker {{
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 0.1rem;
    }}
    .lane.official .lane-kicker {{ color: {at}; }}
    .lane.eval .lane-kicker {{ color: {ev["label_ink"]}; }}
    .lane-sub {{ color: {p["muted"]}; font-size: 0.8rem; margin-bottom: 0.45rem; }}
    .eval-label {{
        display: inline-block;
        color: {ev["label_ink"]};
        border: 1px dashed {ev["border"]};
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 750;
        padding: 0.14rem 0.6rem;
        margin-bottom: 0.5rem;
    }}
    .lane-step {{
        display: flex;
        gap: 0.5rem;
        align-items: baseline;
        border-top: 1px solid rgba(35, 53, 77, 0.10);
        padding: 0.34rem 0;
        color: {p["ink"]};
        font-size: 0.86rem;
        line-height: 1.45;
    }}
    .lane-step:first-of-type {{ border-top: none; }}
    .lane-step .n {{
        flex: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        font-size: 0.7rem;
        font-weight: 800;
    }}
    .lane.official .lane-step .n {{ background: {p["accent_soft"]}; color: {at}; }}
    .lane.eval .lane-step .n {{
        background: transparent;
        border: 1px dashed {ev["border"]};
        color: {ev["label_ink"]};
    }}
    .lane-note {{
        color: {ev["label_ink"]};
        font-size: 0.76rem;
        font-weight: 650;
        margin-top: 0.4rem;
    }}
    .wall {{ position: relative; }}
    .wall::before {{
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 50%;
        border-left: 2px dashed {ev["border"]};
    }}
    .wall span {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(90deg);
        white-space: nowrap;
        background: {p["page_bg"]};
        color: {p["muted"]};
        font-size: 0.62rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        padding: 0 0.55rem;
    }}
    /* The one travelling element: the SELECTED MODEL chip returns from the
       evaluation lane into the official lane. Keyframes end at the natural
       position, so reduced-motion users simply see it in place. */
    .model-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: {p["accent"]};
        color: {p["panel_bg"]};
        border-radius: 999px;
        font-size: 0.86rem;
        font-weight: 750;
        padding: 0.3rem 0.85rem;
        box-shadow: 0 6px 14px rgba(35, 53, 77, 0.24);
    }}
    .s3-chip {{ animation: model-return {travel_ms}ms cubic-bezier(0.2, 0.7, 0.3, 1) {scene_ms * 8}ms both; }}
    @keyframes model-return {{
        from {{ opacity: 0; transform: translateX(200px) translateY(-8px); }}
        to   {{ opacity: 1; transform: none; }}
    }}
    .res-detail {{ color: {p["muted"]}; font-size: 0.76rem; margin: 0.18rem 0 0 0.2rem; }}
    .s3-late1 {{ animation: rise-in {entry_ms}ms ease-out {scene_ms * 8 + travel_ms}ms both; }}
    .s3-late2 {{ animation: rise-in {entry_ms}ms ease-out {scene_ms * 8 + travel_ms + 150}ms both; }}
    .queue-node {{
        display: inline-block;
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 750;
        padding: 0.4rem 0.85rem;
    }}
    /* Entrance + end-state emphasis drop for the evaluation lane (opacity
       {ev_op} verified AA for its label/ink/muted text over the plane). */
    .s3-eval {{
        animation: rise-in {entry_ms}ms ease-out {scene_ms * 4}ms both,
                   recede 450ms ease-out {scene_ms * 8 + travel_ms + 300}ms forwards;
    }}
    @keyframes recede {{
        from {{ opacity: 1; }}
        to   {{ opacity: {ev_op}; }}
    }}

    /* Final output stage + FATF separation. */
    .out-flow {{
        display: flex;
        flex-direction: column;
        gap: 0.22rem;
        margin: 0.4rem 0 0.3rem 0;
    }}
    .out-node {{
        width: fit-content;
        max-width: 100%;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-left: 3px solid {p["accent"]};
        border-radius: 8px;
        color: {p["ink"]};
        font-size: 0.9rem;
        font-weight: 650;
        padding: 0.42rem 0.85rem;
    }}
    .out-node.review {{
        background: {p["sidebar_bg"]};
        border-color: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
    }}
    .out-arrow {{
        color: {p["accent"]};
        font-weight: 700;
        margin-left: 1.05rem;
        line-height: 1;
        user-select: none;
    }}
    .fatf-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.7rem;
        max-width: 720px;
        margin: 0.45rem 0 0.2rem 0;
    }}
    .fatf-input {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        color: {p["ink"]};
        font-size: 0.86rem;
        font-weight: 650;
        text-align: center;
    }}
    .fatf-input.evidence {{ border-top: 3px solid {p["accent"]}; }}
    .fatf-input.context {{ border-top: 3px solid {theme["chart"]["context_gray"]}; }}
    .fatf-input small {{
        display: block;
        color: {p["muted"]};
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.1rem;
    }}
    .fatf-join {{
        grid-column: 1 / -1;
        text-align: center;
        color: {p["accent"]};
        font-weight: 700;
        line-height: 1;
        user-select: none;
    }}
    .fatf-out {{
        grid-column: 1 / -1;
        justify-self: center;
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 750;
        padding: 0.4rem 1rem;
    }}
    .bl-reminder {{
        color: {p["sidebar_muted"]};
        font-size: 0.84rem;
        margin-top: 0.55rem;
    }}

    @media (max-width: 1050px) {{
        .src-grid, .fam-grid {{ grid-template-columns: 1fr; }}
        .src-preview {{ position: static; opacity: 1; visibility: visible;
                        transform: none; margin-top: 0.5rem; }}
        .fam-card .src-preview {{ margin-top: 0.5rem; }}
    }}
    @media (max-width: 900px) {{
        .fork, .fork-split {{ grid-template-columns: 1fr; }}
        .wall {{ display: none; }}
        .fork-split span:nth-child(2) {{ display: none; }}
        .fatf-grid {{ grid-template-columns: 1fr; }}
    }}

    /* ---- CSS-only tooltips (no JS executes inside st.markdown HTML). The
       bubble opens on hover AND keyboard focus (spans carry tabindex="0"). ---- */
    .tip {{
        position: relative;
        cursor: help;
        text-decoration: underline dotted;
        text-decoration-thickness: 1px;
        text-underline-offset: 3px;
    }}
    .tip:focus-visible {{
        outline: 2px solid {p["accent"]};
        outline-offset: 2px;
        border-radius: 2px;
    }}
    .tip::after {{
        content: attr(data-tip);
        position: absolute;
        bottom: calc(100% + 8px);
        left: 0;
        z-index: 70;
        width: max-content;
        max-width: min(340px, 78vw);
        background: {p["sidebar_bg"]};
        color: {p["sidebar_ink"]};
        border: 1px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.55rem 0.75rem;
        font-size: 0.82rem;
        font-weight: 500;
        line-height: 1.45;
        letter-spacing: normal;
        text-transform: none;
        text-align: left;
        white-space: normal;
        box-shadow: 0 8px 22px rgba(2, 18, 47, 0.30);
        opacity: 0;
        visibility: hidden;
        transform: translateY(0);
        transition: opacity 160ms ease-out, transform 160ms ease-out,
                    visibility 0s linear 160ms;
        pointer-events: none;
    }}
    .tip::before {{
        content: "";
        position: absolute;
        bottom: calc(100% + 3px);
        left: 1.1em;
        z-index: 71;
        border: 5px solid transparent;
        border-top-color: {p["sidebar_bg"]};
        opacity: 0;
        visibility: hidden;
        transition: opacity 160ms ease-out, visibility 0s linear 160ms;
        pointer-events: none;
    }}
    .tip:hover::after, .tip:focus::after, .tip:focus-visible::after {{
        opacity: 1;
        visibility: visible;
        transform: translateY(-4px);
        transition: opacity 160ms ease-out, transform 160ms ease-out, visibility 0s;
    }}
    .tip:hover::before, .tip:focus::before, .tip:focus-visible::before {{
        opacity: 1;
        visibility: visible;
        transition: opacity 160ms ease-out, visibility 0s;
    }}

    /* ---- Entrance motion: one fade-up, staggered per section. Streamlit only
       remounts changed DOM nodes, so this replays on page switches — not on
       every widget rerun. ---- */
    @keyframes rise-in {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .anim {{ animation: rise-in {entry_ms}ms ease-out both; }}
    .anim.d1 {{ animation-delay: {step_ms}ms; }}
    .anim.d2 {{ animation-delay: {step_ms * 2}ms; }}
    .anim.d3 {{ animation-delay: {step_ms * 3}ms; }}
    .anim.d4 {{ animation-delay: {step_ms * 4}ms; }}
    .anim.d5 {{ animation-delay: {step_ms * 5}ms; }}
    .anim.d6 {{ animation-delay: {step_ms * 6}ms; }}

    /* ---- Reduced motion: kill EVERY transition/animation/transform declared
       above (sidebar nav, main CTAs, cards, tiles, tooltips, entrances, the
       methodology-scene storyboard, merge/year/model-return keyframes, hover
       previews). Every keyframe above runs FROM an offset TO the natural
       state, so with animation disabled the final layout is what renders.
       Kept LAST in the sheet, with !important, so it always wins. ---- */
    @media (prefers-reduced-motion: reduce) {{
        [data-testid="stSidebar"] [data-testid="stPageLink"] a,
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
        [data-testid="stMain"] [data-testid="stPageLink"] a,
        [data-testid="stMain"] [data-testid="stPageLink"] a:hover,
        [data-testid="stMain"] [data-testid="stButton"] button,
        [data-testid="stMain"] [data-testid="stBaseButton-primary"]:hover,
        [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover,
        .anim, .twin-card, .stat-tile, .flow-step,
        .bv-entry, .story-panel, .commodity-card, .commodity-icon,
        .story-process-stage,
        .sb, .src-card, .fam-card,
        .merge-tile.ma, .merge-tile.mb, .merge-tile.mc, .merge-row,
        .yr.lit.yl1, .yr.lit.yl2, .yr.lit.yl3, .yr.lit.yl4, .yr.lit.yl5,
        .yr.focus.ylf,
        .s3-chip, .s3-late1, .s3-late2,
        .case-banner-text,
        .queue-interpretation-boundary,
        .st-key-dashboard_filter_panel,
        .st-key-queue_case_banner,
        .st-key-queue_table_region,
        .tip::after, .tip::before {{
            animation: none !important;
            transition: none !important;
            transform: none !important;
        }}
        /* The receding evaluation lane must not carry transform:none blindly —
           its recede is opacity-only. Disable both of its animations and pin
           the readable full-emphasis end state. */
        .s3-eval {{
            animation: none !important;
            opacity: 1 !important;
        }}
        .src-preview {{
            transition: none !important;
            transform: none !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
