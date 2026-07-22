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
    reveal_ms = int(motion.get("business_reveal_ms", 720))
    motion_easing = motion.get("easing", "ease-out")
    scene_ms = int(motion.get("scene_step_ms", 120))
    family_colors = theme["families"]
    challenge_accent = theme["status"]["severity"]["high"]["color"]
    outcome_blue = source_roles["official"]["accent"]
    outcome_amber = source_roles["typology"]["accent"]
    case_maroon = theme["chart"].get("case_corridor", "#A62E4E")
    context_violet = theme["chart"].get("case_prior", "#7C5CA6")
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

    /* Icon-only return to the welcome page. It sits in the brand area rather
       than in a navigation group, so it reads as a global home action. The text
       stays in the accessibility tree but is visually clipped. */
    .st-key-sidebar_home {{
        height: 0;
        margin: 0;
        position: relative;
        z-index: 2;
    }}
    .st-key-sidebar_home [data-testid="stPageLink"] {{ margin: 0 !important; }}
    .st-key-sidebar_home [data-testid="stPageLink"] a {{
        position: absolute;
        right: 0;
        bottom: 0.2rem;
        width: 2.15rem;
        height: 2.15rem;
        min-height: 2.15rem;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center;
        gap: 0 !important;
        border: 1px solid rgba(234, 240, 248, 0.22) !important;
        border-left: 1px solid rgba(234, 240, 248, 0.22) !important;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.04);
        opacity: 0.78;
        transition: opacity {hover_ms}ms ease-out,
                    background {hover_ms}ms ease-out,
                    border-color {hover_ms}ms ease-out;
    }}
    .st-key-sidebar_home [data-testid="stPageLink"] a span[data-testid="stIconMaterial"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100%;
        height: 100%;
        margin: 0 !important;
        line-height: 1 !important;
    }}
    .st-key-sidebar_home [data-testid="stPageLink"] a p {{
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
    }}
    .st-key-sidebar_home [data-testid="stPageLink"] a:hover {{
        opacity: 1;
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: {teal500} !important;
        transform: none !important;
    }}
    .st-key-sidebar_home [data-testid="stPageLink"] a:focus-visible {{
        outline: 2px solid {teal500};
        outline-offset: 2px;
    }}

    /* Pin the foot of the sidebar (the creator "about" block) to
       the bottom: the sidebar's outer vertical block becomes a full-height flex
       column, and the layout wrapper holding the bottom block takes the slack. */
    [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{
        display: flex;
        flex-direction: column;
        min-height: calc(100vh - 4.5rem);
    }}
    [data-testid="stSidebarUserContent"] [data-testid="stLayoutWrapper"]:has(.st-key-sidebar_bottom) {{
        margin-top: auto;
        margin-bottom: 2.2rem;  /* clear the fixed human-review boundary ribbon */
    }}
    /* Divider that sets the creator block off from the nav above. */
    .about-sep {{
        border-top: 1px solid rgba(234, 240, 248, 0.16);
        margin: 0;
    }}
    /* Creator / about block. Links inherit the frost sidebar link colour; they
       sit slightly dimmed and brighten on hover. */
    .about-card {{ margin: 1.2rem 0 0.1rem 0.15rem; }}
    .about-name {{
        color: {p["sidebar_ink"]};
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 0.12rem;
    }}
    .about-bio {{
        color: {p["sidebar_muted"]};
        font-size: 0.78rem;
        line-height: 1.42;
        margin-bottom: 0.5rem;
    }}
    .about-links {{ display: flex; flex-wrap: wrap; gap: 0.3rem 0.85rem; }}
    .about-link {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        font-size: 0.8rem;
        font-weight: 600;
        text-decoration: none;
        opacity: 0.82;
        transition: opacity {hover_ms}ms ease-out;
    }}
    .about-link svg {{ width: 0.95rem; height: 0.95rem; flex: none; }}
    .about-link:hover {{ opacity: 1; text-decoration: underline; }}

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
    /* Optional leading icon on a page title (Trade Landscape keeps its landmark). */
    .page-title-icon {{
        width: 1.7rem;
        height: 1.7rem;
        color: {p["accent"]};
        vertical-align: -0.18em;
        margin-right: 0.55rem;
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
    @media (max-width: {int(theme["breakpoints"]["narrow_px"])}px) {{
        .boundary-ribbon {{
            display: grid;
            grid-template-columns: 1rem 1fr;
            justify-content: start;
            align-items: center;
            gap: 0.2rem 0.45rem;
            padding: 0.42rem 0.75rem;
            font-size: 0.68rem;
            line-height: 1.3;
        }}
        .boundary-ribbon .boundary-icon {{ width: 1rem; height: 1rem; }}
        .boundary-ribbon .stamp {{ margin-right: 0; }}
        .boundary-ribbon > span:last-child {{ grid-column: 1 / -1; }}
    }}
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
    /* Caveat note: a soft-red accent (not the teal interactive colour) marks it
       as a caution — "a high rank is not a finding", read before the queue. */
    .queue-interpretation-boundary {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        width: 100%;
        box-sizing: border-box;
        padding: 0.58rem 0.75rem;
        color: {p["ink"]};
        background: color-mix(in srgb, {challenge_accent} 10%, white);
        border: 1px solid color-mix(in srgb, {challenge_accent} 30%, white);
        border-left: 3px solid {challenge_accent};
        border-radius: 8px;
        font-size: 0.9rem;
        line-height: 1.4;
        animation: rise-in {landing_entry_ms}ms {motion_easing} both;
    }}
    .queue-interpretation-boundary svg {{
        width: 1rem;
        height: 1rem;
        color: {challenge_accent};
        flex: none;
    }}

    /* Export note: an info icon beside the export button whose tooltip carries
       the rounding / full-precision-export note (was a footer caption). The
       tooltip is right-anchored so it never runs off the page edge. */
    .queue-export-info {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }}
    .queue-export-tip.tip {{
        display: inline-flex;
        text-decoration: none;
        color: {p["muted"]};
        line-height: 1;
    }}
    .queue-export-tip.tip:hover, .queue-export-tip.tip:focus-visible {{ color: {outcome_blue}; }}
    .queue-export-tip.tip svg {{ width: 1.15rem; height: 1.15rem; }}
    .queue-export-tip.tip::after {{ left: auto; right: 0; }}
    .queue-export-tip.tip::before {{ left: auto; right: 0.5em; }}

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
    .st-key-queue_results_header {{ margin-top: 0.2rem; }}
    .st-key-queue_results_header .section-heading {{ margin-top: 0; }}
    .st-key-queue_results_header .section-icon {{ color: {outcome_blue}; }}
    .st-key-queue_results_header .section-label {{ font-size: 1.16rem; }}
    .st-key-queue_results_header .section-caption {{
        max-width: 760px;
        margin-bottom: 0;
        line-height: 1.4;
    }}
    [data-testid="stMain"] .st-key-queue_results_header [data-testid="stDownloadButton"] button {{
        min-height: 42px;
        border-color: {p["accent"]};
        color: {at};
    }}

    .st-key-queue_case_banner {{
        background: {sel_bg};
        border: 1px solid color-mix(in srgb, {sel_acc} 72%, white);
        border-left: 4px solid {source_roles["typology"]["accent"]};
        border-radius: 8px;
        padding: 0.65rem 0.9rem;
        box-shadow: 0 2px 8px {shadow};
        margin: 0.35rem 0 0.65rem;
        transition: background-color {standard_ms}ms {motion_easing},
                    border-color {standard_ms}ms {motion_easing};
    }}
    .st-key-queue_case_banner [data-testid="stHorizontalBlock"] {{
        align-items: stretch;
        min-height: 58px;
    }}
    .st-key-queue_case_banner [data-testid="stColumn"] {{
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .st-key-queue_case_banner [data-testid="stMarkdownContainer"],
    .st-key-queue_score_guidance [data-testid="stMarkdownContainer"] {{
        margin-bottom: 0 !important;
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
        position: relative;
        border: 1px solid color-mix(in srgb, {btn2b} 62%, white);
        border-radius: 8px;
        box-shadow: 0 4px 14px {shadow};
        background: {p["panel_bg"]};
    }}
    /* The interactive grid's header can't be recoloured directly (Streamlit hands
       glide-data-grid an explicit theme, and the overlay can only darken — never
       lighten to white). A lighter blue band + a firm bottom border marks the
       header row while keeping the grid's dark header text readable. */
    .st-key-queue_table_region div[data-testid="stDataFrame"]::before {{
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 40px;
        z-index: 2;
        pointer-events: none;
        mix-blend-mode: multiply;
        background: color-mix(in srgb, {p["sidebar_bg"]} 22%, transparent);
        border-bottom: 2px solid color-mix(in srgb, {outcome_blue} 80%, transparent);
    }}

    .st-key-queue_score_guidance {{
        min-height: 82px;
        margin: 0.75rem 0 0.55rem;
        padding: 0.75rem 0.9rem;
        color: {p["ink"]};
        background: color-mix(in srgb, {outcome_blue} 8%, white);
        border: 1px solid color-mix(in srgb, {outcome_blue} 26%, white);
        border-left: 3px solid {outcome_blue};
        border-radius: 8px;
    }}
    .queue-guidance-content {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
        min-height: 56px;
    }}
    /* Second note (unit value) stacks under the score note, divided by a rule. */
    .queue-guidance-content + .queue-guidance-content {{
        margin-top: 0.5rem;
        padding-top: 0.65rem;
        border-top: 1px solid color-mix(in srgb, {outcome_blue} 18%, white);
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
    .st-key-queue_table_notes {{ margin: 0 0 0.55rem; }}
    .queue-technical-notes {{
        color: {p["muted"]};
        background: color-mix(in srgb, {p["panel_bg"]} 82%, {p["page_bg"]});
        border: 1px solid {p["border"]};
        border-radius: 8px;
        padding: 0.65rem 0.8rem;
        font-size: 0.82rem;
        line-height: 1.45;
    }}
    .queue-technical-notes p {{ margin: 0 0 0.45rem; }}
    .queue-technical-notes p:last-child {{ margin-bottom: 0; }}

    @media (max-width: 1100px) {{
        .st-key-dashboard_filter_panel [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
    }}
    @media (max-width: 780px) {{
        .st-key-dashboard_filter_panel {{ padding: 0.75rem; }}
        .st-key-queue_case_banner [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
        .st-key-queue_filter_chips [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
        .st-key-queue_score_guidance {{ padding: 0.7rem; }}
    }}

    /* ---- Selected Case Review: compact selected-case strip. Same muted-amber
       selection role as the Review Queue banner — "the case you are carrying",
       never an alarm. Facts + score + the change-case control sit on one wash;
       ink text carries the identity, amber only marks selection. ---- */
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
        font-size: 1.3rem;
        font-weight: 600;
        line-height: 1.4;
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
    /* Trade Landscape: push the value/quantity toggle to the right corner. */
    .st-key-pa_scale_mode {{ width: fit-content; margin-left: auto; }}
    .st-key-pa_scale_mode [data-testid="stSegmentedControl"] {{ margin-left: auto; }}
    /* Selected Case Review: the Chart|Table toggle sits in the top-right corner
       of the comparison heading row (flush right within its column). */
    .st-key-case_view_mode_0, .st-key-case_view_mode_1 {{ width: fit-content; margin-left: auto; }}
    .st-key-case_view_mode_0 [data-testid="stSegmentedControl"],
    .st-key-case_view_mode_1 [data-testid="stSegmentedControl"] {{ margin-left: auto; }}
    /* Chart sub-headings clear the takeaway above them. */
    .chart-subhead {{
        color: {p["ink"]};
        font-weight: 700;
        font-size: 0.95rem;
        margin: 0.9rem 0 0.25rem 0;
    }}
    /* Trade Landscape: each Scale / Market / Queue Profile section is a subtle
       card that lifts off the plane, so the three read as distinct blocks on scroll.
       Each fades up on entrance, staggered. */
    .st-key-pa_card_scale,
    .st-key-pa_card_market,
    .st-key-pa_card_patterns {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 12px;
        box-shadow: 0 4px 14px {shadow};
        padding: 1.1rem 1.4rem 0.7rem 1.4rem;
        margin-bottom: 1.1rem;
        animation: rise-in {entry_ms}ms ease-out both;
    }}
    .st-key-pa_card_market {{ animation-delay: {step_ms}ms; }}
    .st-key-pa_card_patterns {{ animation-delay: {step_ms * 2}ms; }}
    /* Breathing room between each section title and the subtitle line under it,
       across the three landscape cards (scale / market / queue profile). */
    .st-key-pa_card_scale .case-takeaway,
    .st-key-pa_card_market .case-takeaway,
    .st-key-pa_card_patterns .case-takeaway {{
        margin-top: 0.6rem;
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
    /* Governed "reasons, not a finding" note, riding inside the summary banner. */
    .why-summary-note {{
        color: {navy7};
        font-size: 0.85rem;
        font-weight: 600;
        line-height: 1.45;
        margin-top: 0.5rem;
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
    /* Why It Ranked High — four distinct category accents (not one green hue),
       reusing the case-chart palette so the page reads as one system. A shared
       min-height keeps the two cards in each row the same height, and top margin
       gives the "evidence behind the ranking" heading room to breathe. */
    .st-key-why_cards {{ margin-top: 0.85rem; }}
    .st-key-why_cards .compare-card {{ border-top-width: 4px; min-height: 11.5rem; }}
    .st-key-why_cards .compare-card-a {{ border-top-color: {p["accent"]}; }}
    .st-key-why_cards .compare-card-b {{ border-top-color: {theme["chart"]["case_benchmark"]}; }}
    .st-key-why_cards .compare-card-c {{ border-top-color: {theme["chart"]["case_prior"]}; }}
    .st-key-why_cards .compare-card-d {{ border-top-color: {theme["chart"]["case_corridor"]}; }}
    /* Uniform height for the "How calculated" drawers so an open row reads evenly. */
    .st-key-why_cards [data-testid="stExpanderDetails"] {{ min-height: 11.5rem; }}

    /* Caveats tab — each category in its own white, bordered card with a coloured
       top accent + icon, so the caveats read as organised blocks, not a flat list. */
    .caveat-card {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 4px solid {p["accent"]};
        border-radius: 12px;
        box-shadow: 0 4px 14px {shadow};
        padding: 1.05rem 1.35rem 1.15rem 1.35rem;
        margin-bottom: 1.1rem;
    }}
    .caveat-card-case {{ border-top-color: {theme["families"]["gold_unwrought"]}; }}
    .caveat-card-project {{ border-top-color: {p["accent"]}; }}
    .caveat-head {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        color: {p["ink"]};
        font-size: 1.08rem;
        font-weight: 750;
    }}
    .caveat-icon {{ width: 1.3rem; height: 1.3rem; flex: none; }}
    .caveat-card-case .caveat-icon {{ color: {theme["families"]["gold_unwrought"]}; }}
    .caveat-card-project .caveat-icon {{ color: {p["accent"]}; }}
    .caveat-intro {{
        color: {p["muted"]};
        font-size: 0.9rem;
        line-height: 1.45;
        margin: 0.4rem 0 0.7rem 0;
    }}
    .caveat-list {{ margin: 0; padding-left: 1.15rem; color: {p["ink"]}; }}
    .caveat-list li {{ font-size: 0.95rem; line-height: 1.5; margin-bottom: 0.45rem; }}
    .caveat-list li:last-child {{ margin-bottom: 0; }}
    .signals-scroll {{ max-height: 460px; overflow-y: auto; }}
    table.data-table td.mono {{
        font-family: "Consolas", "SFMono-Regular", monospace;
        font-size: 0.83rem;
        white-space: nowrap;
        color: {p["ink"]};
    }}
    table.data-table td[title] {{ cursor: help; }}

    /* ---- Landing page (Business Problem and Value): narrative sections ---- */
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
    /* Bank Implementation Pathway: generous inter-section spacing matching the
       Business Problem & Value rhythm (3.75rem between sections), scoped to the
       page so the shared landing-section spacing elsewhere is untouched. */
    [data-testid="stMain"]:has(.bank-page-marker) .landing-section {{
        margin-bottom: 3.75rem;
    }}
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
        line-height: 1.58;
        font-weight: 500;
        max-width: 92ch;
    }}
    /* Closing statement is rendered as separate paragraphs; keep them spaced. */
    p.bottom-line-text {{ margin: 0 0 0.75rem 0; }}
    p.bottom-line-text:last-of-type {{ margin-bottom: 0.9rem; }}
    /* Data-trust closing footer: match the Bank Implementation Pathway footer
       type — smaller and full-width — so the two closing panels read the same
       and the copy fills the panel instead of leaving a wide right margin. */
    .st-key-dtrq_closing .bottom-line-text {{
        font-size: 0.88rem;
        line-height: 1.5;
        max-width: none;
    }}
    /* Data-trust closing: the navy wrap-up panel that also holds the model-
       evaluation link, so the bottom line and its next step read as one block. */
    .st-key-dtrq_closing {{
        background: {p["sidebar_bg"]};
        border-radius: 12px;
        padding: 1.15rem 1.35rem 1.3rem 1.35rem;
        margin-top: 0.4rem;
        animation: rise-in {entry_ms}ms ease-out both;
    }}
    [data-testid="stMain"] .st-key-dtrq_closing [data-testid="stPageLink"] a {{
        background: transparent;
        border-color: {p["sidebar_muted"]};
        width: fit-content;
        margin-top: 0.3rem;
    }}
    [data-testid="stMain"] .st-key-dtrq_closing [data-testid="stPageLink"] a p {{
        color: #FFFFFF !important;
    }}
    [data-testid="stMain"] .st-key-dtrq_closing [data-testid="stPageLink"] a span[data-testid="stIconMaterial"] {{
        color: {p["accent"]};
    }}
    [data-testid="stMain"] .st-key-dtrq_closing [data-testid="stPageLink"] a:hover {{
        background: rgba(255, 255, 255, 0.08);
        border-color: {p["accent"]};
        box-shadow: none;
        transform: translateY(-1px);
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
       Business Problem and Value: balanced narrative grid + manual story
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
        /* No measure cap: "Evidence-First Trade Pattern Triage" stays on one
           line, bounded only by the 1220px page column, and still wraps
           naturally on narrow screens where that column shrinks. */
        max-width: none;
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
        transition: border-color {standard_ms}ms {motion_easing},
                    box-shadow {standard_ms}ms {motion_easing},
                    transform {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_page .twin-card.response {{ border-top-color: {p["accent"]}; }}
    .st-key-business_value_page .twin-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px {shadow};
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
        transition: border-color {standard_ms}ms {motion_easing},
                    box-shadow {standard_ms}ms {motion_easing},
                    transform {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_page .stat-tile:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px {shadow};
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
        position: relative;
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
    .st-key-business_value_story .commodity-title-row {{
        display: flex;
        align-items: center;
        gap: 0.42rem;
        min-width: 0;
    }}
    .st-key-business_value_story .commodity-info {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.15rem;
        height: 1.15rem;
        flex: none;
        text-decoration: none;
    }}
    .st-key-business_value_story .commodity-info svg {{
        width: 0.95rem;
        height: 0.95rem;
    }}
    .st-key-business_value_story .commodity-info.tip::after {{
        left: auto;
        right: 0;
        width: min(21rem, 70vw);
        max-width: min(21rem, 70vw);
    }}
    .st-key-business_value_story .commodity-info.tip::before {{
        left: auto;
        right: 0.25rem;
    }}
    .st-key-business_value_story .family-crude-palm-oil {{
        border-top-color: {family_colors["crude_palm_oil"]};
    }}
    .st-key-business_value_story .family-crude-palm-oil .commodity-icon {{
        color: {family_colors["crude_palm_oil"]};
        background: color-mix(in srgb, {family_colors["crude_palm_oil"]} 13%, white);
    }}
    .st-key-business_value_story .family-crude-palm-oil .commodity-info {{
        color: {family_colors["crude_palm_oil"]};
    }}
    .st-key-business_value_story .family-refined-copper-cathodes {{
        border-top-color: {family_colors["refined_copper_cathodes"]};
    }}
    .st-key-business_value_story .family-refined-copper-cathodes .commodity-icon {{
        color: {family_colors["refined_copper_cathodes"]};
        background: color-mix(in srgb, {family_colors["refined_copper_cathodes"]} 13%, white);
    }}
    .st-key-business_value_story .family-refined-copper-cathodes .commodity-info {{
        color: {family_colors["refined_copper_cathodes"]};
    }}
    .st-key-business_value_story .family-gold-unwrought {{
        border-top-color: {family_colors["gold_unwrought"]};
    }}
    .st-key-business_value_story .family-gold-unwrought .commodity-icon {{
        color: {family_colors["gold_unwrought"]};
        background: color-mix(in srgb, {family_colors["gold_unwrought"]} 14%, white);
    }}
    .st-key-business_value_story .family-gold-unwrought .commodity-info {{
        color: {family_colors["gold_unwrought"]};
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
        transition: box-shadow {standard_ms}ms {motion_easing},
                    transform {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_story .quote-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px {shadow};
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
        transition: box-shadow {standard_ms}ms {motion_easing},
                    transform {standard_ms}ms {motion_easing};
    }}
    .st-key-business_value_story .story-process-stage:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px {shadow};
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
    .st-key-business_value_page .bottom-line-text {{
        max-width: none;
        font-size: 0.88rem;
        line-height: 1.5;
        font-weight: 500;
    }}
    .st-key-business_value_page .value-chip-row {{
        margin-top: 0.6rem;
        gap: 0.4rem;
    }}
    .st-key-business_value_page .value-chip {{
        padding: 0.14rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 600;
    }}

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

    /* Generic scroll-reveal hidden state (shared across content pages; driver
       is components/scroll_reveal.py). Each section fades + rises as ONE block
       as it enters view, over a FIXED {reveal_ms}ms — clearly visible at any
       scroll SPEED and in every browser, and it re-triggers on scroll back.
       The observer applies the transition INLINE, so a markdown section or a
       keyed container both fade uniformly; this class only holds the hidden
       state. Sections default to visible, so the page is never blank if the
       script is blocked, and reduced motion is forced visible below. */
    .reveal-off {{
        opacity: 0 !important;
        transform: translateY(28px) !important;
    }}

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
        /* On narrow screens, anchor the bubble to the full card instead of the
           icon so long product names can never push the explanation off-screen. */
        .st-key-business_value_story .commodity-info.tip::after,
        .st-key-business_value_story .commodity-info.tip::before {{
            content: none;
        }}
        .st-key-business_value_story .commodity-card::after {{
            content: attr(data-tip);
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            z-index: 80;
            box-sizing: border-box;
            width: 100%;
            padding: 0.65rem 0.75rem;
            color: {p["sidebar_ink"]};
            background: {p["sidebar_bg"]};
            border: 1px solid {p["accent"]};
            border-radius: 6px;
            box-shadow: 0 8px 22px rgba(15, 34, 58, 0.22);
            font-size: 0.76rem;
            font-weight: 500;
            line-height: 1.45;
            opacity: 0;
            visibility: hidden;
            transform: translateY(2px);
            transition: opacity 160ms ease-out, transform 160ms ease-out,
                        visibility 0s linear 160ms;
            pointer-events: none;
        }}
        .st-key-business_value_story .commodity-card:focus-within::after,
        .st-key-business_value_story .commodity-card:has(.commodity-info:hover)::after {{
            opacity: 1;
            visibility: visible;
            transform: translateY(-4px);
            transition: opacity 160ms ease-out, transform 160ms ease-out,
                        visibility 0s;
        }}
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
    .bank-pathway-hero .page-subtitle {{
        width: 100%;
        max-width: none;
    }}
    .bank-section-heading {{ margin-bottom: 0.85rem; max-width: none; }}
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
    .bank-section-info {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.18rem;
        height: 1.18rem;
        margin-left: 0.42rem;
        color: {p["accent"]};
        vertical-align: -0.16rem;
        text-decoration: none;
    }}
    .bank-section-info svg {{ width: 1.05rem; height: 1.05rem; }}
    .bank-section-info.tip::after {{
        width: min(31rem, 78vw);
        max-width: min(31rem, 78vw);
    }}
    .bank-section-caption {{
        color: {p["muted"]};
        font-size: 0.96rem;
        line-height: 1.55;
        margin-top: 0.3rem;
    }}
    .bank-role .landing-prose {{
        max-width: none;
        font-size: 1.04rem;
        line-height: 1.66;
        margin-bottom: 0.75rem;
    }}

    /* Scroll-driven reveal: each bank section fades and rises in as it scrolls
       into view (pure CSS — no JS). Deliberately clear on this text-heavy page,
       so scrolling has a sense of progression. Browsers without animation-timeline
       simply show the sections; reduced-motion users are pinned visible below. */
    @keyframes bank-scroll-reveal {{
        from {{ opacity: 0; transform: translateY(30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @supports (animation-timeline: view()) {{
        .bank-reveal {{
            animation-name: bank-scroll-reveal;
            animation-duration: 1ms;
            animation-timing-function: ease-out;
            animation-fill-mode: both;
            animation-timeline: view();
            animation-range: entry 0% cover 34%;
        }}
        /* Inner cards/steps lag their section slightly for a layered reveal. */
        .bank-reveal .bank-icon-card,
        .bank-reveal .bank-fit-step,
        .bank-reveal .bank-ai-step {{
            animation-name: bank-scroll-reveal;
            animation-duration: 1ms;
            animation-timing-function: ease-out;
            animation-fill-mode: both;
            animation-timeline: view();
            animation-range: entry 0% cover 42%;
        }}
    }}

    .bank-fit-rail {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin-top: 1.05rem;
    }}
    .bank-fit-step {{
        --bank-tone: {outcome_blue};
        --bank-soft: {source_roles["official"]["soft"]};
        position: relative;
        display: grid;
        grid-template-columns: 2.55rem minmax(0, 1fr);
        gap: 0.75rem;
        align-items: start;
        min-height: 6.4rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid var(--bank-tone);
        border-radius: 8px;
        padding: 0.85rem;
        box-shadow: 0 4px 14px {shadow};
    }}
    .bank-fit-step-2 {{ --bank-tone: {outcome_amber}; --bank-soft: {source_roles["typology"]["soft"]}; }}
    .bank-fit-step-3 {{ --bank-tone: {p["accent"]}; --bank-soft: {p["accent_soft"]}; }}
    .bank-fit-step:not(:last-child)::after {{
        content: "→";
        position: absolute;
        z-index: 2;
        right: -0.83rem;
        top: calc(50% - 0.7rem);
        color: {p["muted"]};
        font-size: 1.25rem;
        font-weight: 700;
    }}
    .bank-fit-icon {{ background: var(--bank-soft); color: var(--bank-tone); }}
    .bank-fit-copy {{ min-width: 0; }}
    .bank-fit-label {{
        color: var(--bank-tone);
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}
    .bank-fit-question {{
        color: {p["ink"]};
        font-size: 0.9rem;
        font-weight: 650;
        line-height: 1.45;
        margin-top: 0.2rem;
    }}

    .bank-architecture {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) 7.5rem minmax(0, 1fr);
        gap: 1rem;
        align-items: stretch;
        margin-top: 0.9rem;
    }}
    .bank-state {{
        min-width: 0;
        height: 100%;
        padding: 1rem;
        background: {source_roles["official"]["soft"]};
        border-top: 3px solid {outcome_blue};
    }}
    .bank-state-future {{
        background: {p["accent_soft"]};
        border-top-color: {p["accent"]};
    }}
    .bank-state-kicker {{
        color: {source_roles["official"]["text"]};
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
        background: {source_roles["official"]["soft"]};
        border: 1px solid {p["border"]};
        color: {source_roles["official"]["text"]};
        font-size: 0.76rem;
        font-weight: 800;
    }}
    .bank-state-future .bank-node-index {{ background: {p["accent_soft"]}; color: {at}; }}
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
        align-self: center;
        color: {p["muted"]};
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
        border-left: 3px solid {outcome_amber};
        padding: 0.75rem 0.9rem;
        margin-top: 0.75rem;
        font-size: 0.82rem;
        line-height: 1.45;
    }}
    .bank-feedback-note svg {{
        color: {source_roles["typology"]["text"]};
        width: 1.05rem;
        height: 1.05rem;
        flex: none;
        margin-top: 0.08rem;
    }}

    .bank-domain-grid, .bank-value-grid {{ display: grid; gap: 0.8rem; }}
    .bank-domain-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .bank-value-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .bank-icon-card {{
        --bank-tone: {p["accent"]};
        --bank-soft: {p["accent_soft"]};
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        min-width: 0;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid var(--bank-tone);
        border-radius: 8px;
        padding: 0.85rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out, box-shadow {hover_ms}ms ease-out;
    }}
    .bank-icon-card:hover {{
        transform: translateY(-2px);
        box-shadow: {surfaces["shadow_hover"]};
    }}
    .bank-icon-card.domain.bank-card-1,
    .bank-icon-card.value.bank-card-1 {{ --bank-tone: {outcome_blue}; --bank-soft: {source_roles["official"]["soft"]}; }}
    .bank-icon-card.domain.bank-card-2,
    .bank-icon-card.value.bank-card-3 {{ --bank-tone: {outcome_amber}; --bank-soft: {source_roles["typology"]["soft"]}; }}
    .bank-icon-card.domain.bank-card-3,
    .bank-icon-card.value.bank-card-2 {{ --bank-tone: {p["accent"]}; --bank-soft: {p["accent_soft"]}; }}
    .bank-icon-card.domain.bank-card-4 {{ --bank-tone: {case_maroon}; --bank-soft: color-mix(in srgb, {case_maroon} 10%, white); }}
    .bank-icon-card.domain.bank-card-5,
    .bank-icon-card.value.bank-card-4 {{ --bank-tone: {context_violet}; --bank-soft: color-mix(in srgb, {context_violet} 11%, white); }}
    .bank-icon-card.domain.bank-card-6 {{ --bank-tone: {navy7}; --bank-soft: color-mix(in srgb, {navy7} 10%, white); }}
    .bank-card-icon {{ background: var(--bank-soft); color: var(--bank-tone); flex: none; }}
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

    /* AI reads as an assistive layer via a soft violet wash; the prominent
       left accent bar was dropped as distracting. */
    .bank-ai-shell {{
        background: color-mix(in srgb, {context_violet} 7%, white);
        border-radius: 10px;
        padding: 1rem;
    }}
    .bank-ai-value {{
        display: grid;
        grid-template-columns: 1.35rem minmax(0, 1fr);
        gap: 0.65rem;
        align-items: start;
        color: {p["sidebar_ink"]};
        background: {navy7};
        border-radius: 6px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.9rem;
        font-size: 0.84rem;
        font-weight: 600;
        line-height: 1.5;
    }}
    .bank-ai-value svg {{
        width: 1.15rem;
        height: 1.15rem;
        color: {outcome_amber};
        margin-top: 0.12rem;
    }}
    .bank-ai-flow {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) 2.5rem minmax(0, 1.15fr) 2.5rem minmax(0, 1fr);
        gap: 0.65rem;
        align-items: stretch;
    }}
    .bank-ai-step {{
        --ai-tone: {outcome_blue};
        --ai-soft: {source_roles["official"]["soft"]};
        display: grid;
        grid-template-columns: 2.65rem minmax(0, 1fr);
        gap: 0.75rem;
        align-items: start;
        min-width: 0;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid var(--ai-tone);
        border-radius: 8px;
        padding: 0.85rem;
    }}
    .bank-ai-step-2 {{ --ai-tone: {context_violet}; --ai-soft: color-mix(in srgb, {context_violet} 11%, white); }}
    .bank-ai-step-3 {{ --ai-tone: {outcome_amber}; --ai-soft: {source_roles["typology"]["soft"]}; }}
    .bank-ai-icon {{ background: var(--ai-soft); color: var(--ai-tone); }}
    .bank-ai-copy {{ min-width: 0; }}
    .bank-ai-kicker {{
        color: var(--ai-tone);
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}
    .bank-ai-title {{ color: {p["ink"]}; font-size: 0.94rem; font-weight: 750; margin-top: 0.12rem; }}
    .bank-ai-detail {{ color: {p["muted"]}; font-size: 0.82rem; line-height: 1.48; margin-top: 0.22rem; }}
    .bank-ai-arrow {{
        display: grid;
        place-items: center;
        color: {context_violet};
        font-size: 1.35rem;
        font-weight: 750;
    }}
    .bank-ai-support {{
        margin-top: 0.9rem;
        padding-top: 0.85rem;
        border-top: 1px solid color-mix(in srgb, {context_violet} 22%, white);
    }}
    .bank-ai-support-title {{ color: {p["ink"]}; font-size: 0.8rem; font-weight: 750; }}
    .bank-ai-output-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 0.45rem;
    }}
    .bank-ai-output {{
        --ai-output-tone: {outcome_blue};
        --ai-output-soft: {source_roles["official"]["soft"]};
        display: grid;
        grid-template-columns: 2.25rem minmax(0, 1fr);
        gap: 0.65rem;
        align-items: start;
        min-width: 0;
        background: {p["panel_bg"]};
        border-left: 3px solid var(--ai-output-tone);
        padding: 0.7rem 0.75rem;
    }}
    .bank-ai-output-2 {{ --ai-output-tone: {p["accent"]}; --ai-output-soft: {p["accent_soft"]}; }}
    .bank-ai-output-3 {{ --ai-output-tone: {outcome_amber}; --ai-output-soft: {source_roles["typology"]["soft"]}; }}
    .bank-ai-output-4 {{ --ai-output-tone: {context_violet}; --ai-output-soft: color-mix(in srgb, {context_violet} 11%, white); }}
    .bank-ai-output-icon {{
        width: 2.1rem;
        height: 2.1rem;
        background: var(--ai-output-soft);
        color: var(--ai-output-tone);
    }}
    .bank-ai-output-icon svg {{ width: 1.05rem; height: 1.05rem; }}
    .bank-ai-output-copy {{ min-width: 0; }}
    .bank-ai-output-title {{
        color: {p["ink"]};
        font-size: 0.82rem;
        font-weight: 750;
        line-height: 1.35;
    }}
    .bank-ai-output-detail {{
        color: {p["muted"]};
        font-size: 0.76rem;
        line-height: 1.45;
        margin-top: 0.18rem;
    }}
    .bank-ai-guardrails {{ margin-top: 0.8rem; }}
    .bank-ai-guardrail-grid {{ display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.4rem; }}
    .bank-ai-guardrail {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        color: {navy7};
        background: {p["panel_bg"]};
        border: 1px solid color-mix(in srgb, {context_violet} 30%, white);
        border-radius: 999px;
        padding: 0.35rem 0.55rem;
        font-size: 0.74rem;
        font-weight: 650;
        line-height: 1.25;
    }}
    .bank-ai-guardrail svg {{ width: 0.85rem; height: 0.85rem; color: {context_violet}; flex: none; }}

    /* This is a closing summary, not a second headline. Keep it quieter than
       the page's explanatory body copy while preserving the navy boundary. */
    .bank-closing .bottom-line {{ padding: 0.9rem 1rem; }}
    .bank-closing .bottom-line-text {{
        max-width: none;
        font-size: 0.88rem;
        line-height: 1.5;
        font-weight: 500;
    }}
    .bank-closing .value-chip-row {{ margin-top: 0.6rem; gap: 0.4rem; }}
    .bank-closing .value-chip {{
        padding: 0.14rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 600;
    }}

    @media (max-width: 1050px) {{
        .bank-domain-grid, .bank-value-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .bank-ai-flow {{ grid-template-columns: 1fr; }}
        .bank-ai-arrow {{ transform: rotate(90deg); min-height: 1.6rem; }}
    }}
    @media (max-width: 780px) {{
        .bank-section-info.tip::after {{
            left: auto;
            right: 0;
        }}
        .bank-section-info.tip::before {{
            left: auto;
            right: 0.3rem;
        }}
        .bank-architecture {{ grid-template-columns: 1fr; }}
        .bank-bridge {{ flex-direction: row; justify-content: center; padding: 0.2rem 0; }}
        .bank-bridge svg {{ transform: rotate(90deg); }}
        .bank-fit-rail {{ grid-template-columns: 1fr; }}
        .bank-fit-step {{ min-height: 0; }}
        .bank-fit-step:not(:last-child)::after {{
            right: auto;
            left: calc(50% - 0.35rem);
            top: auto;
            bottom: -1.15rem;
            transform: rotate(90deg);
        }}
        .bank-ai-output-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 560px) {{
        .bank-domain-grid, .bank-value-grid {{ grid-template-columns: 1fr; }}
        .bank-icon-card {{ padding: 0.75rem; }}
        .bank-ai-shell {{ padding: 0.75rem; }}
        .bank-ai-step {{ grid-template-columns: 2.35rem minmax(0, 1fr); padding: 0.75rem; }}
        .bank-ai-value {{ grid-template-columns: 1.2rem minmax(0, 1fr); }}
        .bank-ai-guardrail {{ width: 100%; }}
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
    /* Gold Quantity Coverage: the mental-model banner recoloured as one red
       "coverage boundary" note — light-red fill, dark text, red accent, icon
       and stamp — merging the old navy banner and the red caveat box. Rendered
       static (not sticky) so a red bar never trails the page. */
    .mental-model.coverage-boundary {{
        background: color-mix(in srgb, {challenge_accent} 12%, white);
        color: {p["ink"]};
        border-left: 3px solid {challenge_accent};
        box-shadow: 0 4px 14px color-mix(in srgb, {challenge_accent} 16%, transparent);
    }}
    .mental-model.coverage-boundary .banner-icon {{
        background: color-mix(in srgb, {challenge_accent} 18%, white);
        color: {challenge_accent};
    }}
    .mental-model.coverage-boundary .mm-stamp {{ color: {challenge_accent}; }}
    [data-testid="stElementContainer"]:has(.mental-model.coverage-boundary) {{
        position: static;
        top: auto;
        z-index: auto;
        margin-bottom: 1.1rem;  /* breathing room before the KPI band */
    }}
    /* Generous inter-section spacing on the coverage page (matches the Business
       Problem & Value rhythm) so each question reads as its own block. */
    [data-testid="stMain"]:has(.gc-page-marker) .section-heading {{
        margin-top: 3.4rem;
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .stat-band.three {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .gc-kpi-frequency {{
        border-top-color: {family_colors["gold_unwrought"]};
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .gc-kpi-frequency .stat-label {{
        color: {family_colors["gold_unwrought"]};
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .gc-kpi-coverage {{
        border-top-color: {p["accent"]};
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .gc-kpi-coverage .stat-label {{
        color: {at};
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .gc-kpi-pattern {{
        border-top-color: {case_maroon};
    }}
    [data-testid="stMain"]:has(.gc-page-marker) .gc-kpi-pattern .stat-label {{
        color: {case_maroon};
    }}
    /* Five-tile trust band (extends the landing stat-band). */
    .stat-band.five {{ grid-template-columns: repeat(5, 1fr); }}
    @media (max-width: 1250px) {{ .stat-band.five {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (max-width: 900px) {{ .stat-band.five {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 560px) {{ .stat-band.five {{ grid-template-columns: 1fr; }} }}

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
        display: block;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-left: 4px solid {p["accent"]};
        border-radius: 8px;
        color: {p["ink"]};
        font-size: 0.95rem;
        font-weight: 650;
        padding: 0.6rem 1rem;
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
        border-top: 3px solid {p["border"]};
        border-radius: 10px;
        padding: 0.8rem 0.95rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out, box-shadow {hover_ms}ms ease-out;
    }}
    /* Family cards carry their family colour (top rule + dot), matching the
       commodity cards on the Business Problem and Value page. */
    /* Each family card takes its family colour: top rule, dot, and the role
       label. Gold and palm are lightened hues, so the role text is deepened
       toward ink for legibility while staying recognisably the family colour. */
    .fam-card.fam-gold_unwrought {{ border-top-color: {family_colors["gold_unwrought"]}; }}
    .fam-card.fam-gold_unwrought .chip-dot {{ background: {family_colors["gold_unwrought"]}; }}
    .fam-card.fam-gold_unwrought .fam-role {{
        color: color-mix(in srgb, {family_colors["gold_unwrought"]} 70%, {p["ink"]});
    }}
    .fam-card.fam-refined_copper_cathodes {{ border-top-color: {family_colors["refined_copper_cathodes"]}; }}
    .fam-card.fam-refined_copper_cathodes .chip-dot {{ background: {family_colors["refined_copper_cathodes"]}; }}
    .fam-card.fam-refined_copper_cathodes .fam-role {{ color: {family_colors["refined_copper_cathodes"]}; }}
    .fam-card.fam-crude_palm_oil {{ border-top-color: {family_colors["crude_palm_oil"]}; }}
    .fam-card.fam-crude_palm_oil .chip-dot {{ background: {family_colors["crude_palm_oil"]}; }}
    .fam-card.fam-crude_palm_oil .fam-role {{
        color: color-mix(in srgb, {family_colors["crude_palm_oil"]} 82%, {p["ink"]});
    }}
    /* Record-example table (What does one row represent?): match the label
       column to the navigation panel so the field/value split is immediate. */
    table.data-table td.rec-k {{
        color: {p["sidebar_ink"]};
        background: {p["sidebar_bg"]};
        font-weight: 650;
        white-space: nowrap;
        width: 34%;
    }}
    /* Full inner grid for the key-value fact table. Row separators must read in
       BOTH columns, so they are set per background: a solid steel line on the
       white value cells and a frost line on the navy label cells (one light
       colour would vanish on the navy). A teal divider follows the label column,
       and a hairline frames the whole grid so the outer edge is defined too. */
    table.data-table.grid-lines {{
        border: 1px solid #B4C2D2;
    }}
    table.data-table.grid-lines tbody td {{
        border-top: 1px solid #B4C2D2;
    }}
    table.data-table.grid-lines tbody tr:first-child td {{ border-top: none; }}
    /* The navy label column has an opaque background, which under
       border-collapse paints over the collapsed row border (it is computed but
       hidden — the white column's border shows, the navy one's does not). Draw
       the row separator as a 1px line in the cell BACKGROUND instead, so it is
       always painted on top of the navy. */
    table.data-table.grid-lines tbody td.rec-k {{
        border-top: none;
        border-right: 2px solid {p["accent"]};
        background:
            linear-gradient(to bottom, rgba(248, 250, 253, 0.6) 1px, transparent 1px),
            {p["sidebar_bg"]};
    }}
    table.data-table.grid-lines tbody tr:first-child td.rec-k {{
        background: {p["sidebar_bg"]};
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
    /* One real prepared observation: horizontal on desktop, scrollable on
       narrow screens without forcing the page itself to overflow. */
    .prep-record-panel {{
        margin-top: 0.75rem;
        margin-bottom: 1.35rem;
    }}
    .prep-record-table {{ margin: 0.15rem 0 0.35rem; }}
    .prep-record-table table {{ min-width: 1120px; }}
    .prep-record-table table.data-table thead th {{
        background: {p.get("table_stripe", "#EFF3FA")};
        color: {p["muted"]};
        border-bottom: 2px solid {p["accent"]};
        font-size: 0.72rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}
    .prep-record-table table.data-table tbody td {{
        color: {p["ink"]};
        font-size: 0.84rem;
        font-weight: 600;
        white-space: nowrap;
    }}
    .prep-record-table table.data-table td.mono {{
        color: {p["ledger_ink"]};
        font-family: "Consolas", "SFMono-Regular", monospace;
        font-size: 0.76rem;
    }}
    /* Derived-signals table: same styling as the prepared-row table, but it
       replicates the eight prepared-row columns and appends three derived
       signals, so it needs more room and scrolls horizontally on narrow screens. */
    .prep-signals-table table {{ min-width: 1360px; }}
    /* Clear break between the "Scoring the {{focus_year}} observation" year strip
       above and the signals-table intro + table below, so the demonstration
       reads as its own step rather than crowding the year strip. The element also
       carries .prep-body (whose `margin: 0 …` shorthand zeroes margin-top), so we
       raise specificity here to make this top margin win. */
    [data-scene] p.sig-table-intro {{ margin-top: 3.6rem; margin-bottom: 0.9rem; }}
    /* Header info icon: a small cue that the column carries a native-title
       definition (data dictionary). Native title avoids the CSS-tooltip
       clipping that the table's horizontal-scroll wrapper would cause. */
    .prep-record-table table.data-table thead th[title] {{ cursor: help; }}
    .prep-record-table table.data-table thead th .th-info {{
        margin-left: 0.15rem;
        color: {p["accent"]};
        font-size: 0.82em;
        font-weight: 700;
        text-transform: none;
    }}
    /* Time-safety year strip. Final state = what reduced-motion users see:
       history lit, focus framed, later years greyed with a hidden tag. */
    /* The "Scoring the {{focus_year}} observation" block is centred as a unit —
       heading, year strip and caption — so it reads as a distinct focal step. */
    .year-block {{ text-align: center; }}
    .year-block .year-strip {{ justify-content: center; }}
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
    /* History years use the review-queue red (severity high, #C65D63) rather than
       teal — this page already leans heavily on teal. The focus year is a faded
       red with a thick red border (inset, so the chip keeps the others' size) and
       dark text, so it stands out without the heavy navy fill that distracted. */
    .yr.lit {{ background: {challenge_accent}; color: {p["panel_bg"]}; }}
    .yr.focus {{
        background: color-mix(in srgb, {challenge_accent} 16%, white);
        color: {p["ink"]};
        box-shadow: inset 0 0 0 2.5px {challenge_accent};
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
    .year-section-heading {{ margin-top: 1.1rem; }}

    /* ---- Model Evaluation & Controls: the queue-build flow (top of page), the
       "tested on a copy" scenario groups, and the blend split bar. ---- */
    .mc-flow {{
        display: flex;
        align-items: stretch;
        gap: 0.4rem;
        margin: 0.45rem 0 0.6rem 0;
    }}
    .mc-flow-step {{
        flex: 1 1 0;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 10px;
        box-shadow: 0 4px 14px {shadow};
        padding: 0.7rem 0.8rem 0.8rem 0.8rem;
    }}
    .mc-flow-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 50%;
        background: {p["accent_soft"]};
        color: {at};
        font-size: 0.78rem;
        font-weight: 800;
        margin-bottom: 0.4rem;
    }}
    .mc-flow-title {{ color: {p["ink"]}; font-size: 0.92rem; font-weight: 750; line-height: 1.3; }}
    .mc-flow-detail {{ color: {p["muted"]}; font-size: 0.8rem; line-height: 1.4; margin-top: 0.2rem; }}
    .mc-flow-arrow {{
        flex: 0 0 auto;
        align-self: center;
        color: {p["accent"]};
        font-size: 1.15rem;
        font-weight: 700;
        user-select: none;
    }}

    .scenario {{
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-radius: 12px;
        box-shadow: 0 4px 14px {shadow};
        padding: 1rem 1.25rem 1.1rem 1.25rem;
        margin: 0.3rem 0 0.5rem 0;
    }}
    .scenario-copy {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-bottom: 0.85rem;
    }}
    .scenario-copy-real {{
        background: {p["accent_soft"]};
        color: {at};
        border-radius: 8px;
        font-weight: 750;
        font-size: 0.9rem;
        padding: 0.35rem 0.75rem;
    }}
    .scenario-copy-arrow {{ color: {p["accent"]}; font-weight: 800; font-size: 1.05rem; }}
    .scenario-copy-test {{
        background: {ev["tint"]};
        color: {ev["label_ink"]};
        border: 1px dashed {ev["border"]};
        border-radius: 8px;
        font-weight: 750;
        font-size: 0.9rem;
        padding: 0.32rem 0.72rem;
    }}
    .scenario-copy-note {{ color: {p["muted"]}; font-size: 0.82rem; }}
    .scenario-groups {{
        display: grid;
        grid-template-columns: 1.4fr 1fr;
        gap: 1rem;
    }}
    .scenario-group {{ border-radius: 10px; padding: 0.75rem 0.9rem; }}
    .scenario-group.catch {{
        background: {ev["tint"]};
        border: 1px solid {ev["border"]};
    }}
    .scenario-group.ignore {{ background: {p["page_bg"]}; border: 1px solid {p["border"]}; }}
    .scenario-group-head {{
        display: flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }}
    .scenario-group.catch .scenario-group-head {{ color: {ev["label_ink"]}; }}
    .scenario-group.ignore .scenario-group-head {{ color: {p["muted"]}; }}
    .scenario-ic {{ width: 1.05rem; height: 1.05rem; flex: none; }}
    .scenario-item {{ border-top: 1px solid {p["table_stripe"]}; padding: 0.42rem 0; }}
    .scenario-item:first-of-type {{ border-top: none; }}
    .scenario-item-title {{ color: {p["ink"]}; font-size: 0.9rem; font-weight: 700; }}
    .scenario-item-detail {{ color: {p["muted"]}; font-size: 0.82rem; line-height: 1.4; margin-top: 0.05rem; }}
    .scenario-test-notes {{
        margin-top: 0.85rem;
        padding: 0.7rem 0.85rem 0.75rem 0.85rem;
        border: 1px solid {p["border"]};
        border-radius: 8px;
        background: {p["page_bg"]};
        color: {p["ink"]};
        font-size: 0.84rem;
        line-height: 1.45;
    }}
    .scenario-test-notes-heading {{
        color: {p["accent"]};
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }}
    .scenario-test-notes ul {{ margin: 0; padding-left: 1.15rem; }}
    .scenario-test-notes li {{ margin: 0.25rem 0; padding-left: 0.15rem; }}
    .scenario-test-notes li::marker {{ color: {p["accent"]}; }}

    /* This narrative page needs clearer pauses between major sections. The
       marker scopes the spacing to Model Evaluation & Controls only. */
    [data-testid="stElementContainer"]:has(.mc-page-marker) {{
        position: absolute;
        height: 0;
    }}
    [data-testid="stMain"]:has(.mc-page-marker) .section-heading {{
        position: relative;
        margin-top: 2.15rem;
        margin-bottom: 0.9rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid {p["border"]};
    }}
    [data-testid="stMain"]:has(.mc-page-marker) .section-heading::after {{
        content: "";
        position: absolute;
        left: 0;
        bottom: -1px;
        width: 3.1rem;
        height: 3px;
        border-radius: 999px;
        background: {p["accent"]};
    }}

    /* Compact audit facts inside "How these results are calculated". The full
       formula table below uses the shared Data Dictionary table treatment. */
    .mc-eval-facts {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.35rem 0 0.8rem 0;
    }}
    .mc-eval-fact {{
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 0.25rem;
        min-height: 4.7rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.65rem 0.75rem;
    }}
    .mc-eval-fact span {{
        color: {p["muted"]};
        font-size: 0.76rem;
        line-height: 1.3;
    }}
    .mc-eval-fact strong {{
        color: {p["ink"]};
        font-size: 1.15rem;
        font-variant-numeric: tabular-nums;
    }}

    .method-path {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.65rem 0 1rem 0;
    }}
    .method-step {{
        min-height: 9.25rem;
        background: {p["panel_bg"]};
        border: 1px solid {p["border"]};
        border-top: 3px solid {p["accent"]};
        border-radius: 8px;
        padding: 0.8rem 0.9rem;
        box-shadow: 0 4px 14px {shadow};
        transition: transform {hover_ms}ms ease-out,
                    box-shadow {hover_ms}ms ease-out;
    }}
    .method-step:nth-child(2) {{ border-top-color: {case_maroon}; }}
    .method-step:nth-child(3) {{ border-top-color: {outcome_amber}; }}
    .method-step:hover {{
        transform: translateY(-2px);
        box-shadow: 0 7px 18px rgba(35, 53, 77, 0.14);
    }}
    .method-step-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        color: {at};
        background: {p["accent_soft"]};
        margin-bottom: 0.5rem;
    }}
    .method-step-icon svg {{ width: 1.05rem; height: 1.05rem; }}
    .method-step-title {{
        color: {p["ink"]};
        font-size: 0.94rem;
        font-weight: 750;
        line-height: 1.3;
    }}
    .method-step-detail {{
        color: {p["muted"]};
        font-size: 0.82rem;
        line-height: 1.45;
        margin-top: 0.25rem;
    }}

    .blend {{ margin: 0.25rem 0 0.5rem 0; }}
    .blend-eq {{
        font-family: "Consolas", "SFMono-Regular", monospace;
        font-size: 1.0rem;
        font-weight: 700;
        color: {p["ink"]};
        background: color-mix(in srgb, {case_maroon} 9%, white);
        border: 1px solid color-mix(in srgb, {case_maroon} 25%, white);
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.6rem;
    }}
    .blend-bar {{
        display: flex;
        height: 2.4rem;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid {p["border"]};
    }}
    .blend-seg {{
        display: flex;
        align-items: center;
        justify-content: center;
        color: {p["panel_bg"]};
        font-size: 0.85rem;
        font-weight: 750;
        white-space: nowrap;
        overflow: hidden;
    }}
    .blend-challenger {{ background: {case_maroon}; }}
    .blend-rule {{ background: {navy7}; }}
    .method-rule-eq {{ margin: 0.35rem 0 0.8rem 0; }}
    .rule-adjustment-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 0.45rem 0 0.75rem 0;
    }}
    .rule-adjustment-card {{
        border: 1px solid {p["border"]};
        border-top: 3px solid {navy7};
        border-radius: 8px;
        background: {p["panel_bg"]};
        padding: 0.85rem 0.95rem;
        color: {p["ink"]};
    }}
    .rule-adjustment-quality {{ border-top-color: {case_maroon}; }}
    .rule-adjustment-head {{
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        margin-bottom: 0.55rem;
    }}
    .rule-adjustment-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        flex: 0 0 2rem;
        border-radius: 50%;
        color: {navy7};
        background: color-mix(in srgb, {navy7} 10%, white);
    }}
    .rule-adjustment-quality .rule-adjustment-icon {{
        color: {case_maroon};
        background: color-mix(in srgb, {case_maroon} 10%, white);
    }}
    .rule-adjustment-icon svg {{ width: 1rem; height: 1rem; }}
    .rule-adjustment-title {{ font-size: 0.94rem; font-weight: 800; line-height: 1.3; }}
    .rule-adjustment-question {{
        color: {p["muted"]};
        font-size: 0.8rem;
        line-height: 1.4;
        margin-top: 0.12rem;
    }}
    .rule-adjustment-card p {{
        margin: 0 0 0.6rem 0;
        font-size: 0.84rem;
        line-height: 1.5;
    }}
    .rule-adjustment-effect {{
        border-left: 3px solid {navy7};
        background: color-mix(in srgb, {navy7} 6%, white);
        padding: 0.55rem 0.65rem;
        font-size: 0.82rem;
        line-height: 1.45;
    }}
    .rule-adjustment-quality .rule-adjustment-effect {{
        border-left-color: {case_maroon};
        background: color-mix(in srgb, {case_maroon} 6%, white);
    }}
    .rule-adjustment-example {{
        color: {p["muted"]};
        font-size: 0.78rem;
        line-height: 1.4;
        margin-top: 0.55rem;
    }}
    .method-tradeoff {{
        color: {p["ink"]};
        background: color-mix(in srgb, {case_maroon} 7%, white);
        border: 1px solid color-mix(in srgb, {case_maroon} 24%, white);
        border-left: 4px solid {case_maroon};
        border-radius: 8px;
        padding: 0.75rem 0.9rem;
        line-height: 1.5;
        margin: 0.45rem 0 0.55rem 0;
    }}

    /* "What keeps it honest" — allowed vs not-allowed language as two equal-height
       cards (grid stretch), coloured blue (may say) and rose (may not say) so the
       page is not another stack of green boxes. */
    .say-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        align-items: stretch;
        margin: 0.3rem 0 0.5rem 0;
    }}
    .say-card {{ border-radius: 10px; padding: 0.8rem 1rem 0.9rem 1rem; }}
    .say-allowed {{
        background: color-mix(in srgb, {theme["chart"]["case_benchmark"]} 9%, white);
        border: 1px solid color-mix(in srgb, {theme["chart"]["case_benchmark"]} 34%, white);
    }}
    .say-notallowed {{
        background: color-mix(in srgb, {theme["chart"]["case_corridor"]} 7%, white);
        border: 1px solid color-mix(in srgb, {theme["chart"]["case_corridor"]} 30%, white);
    }}
    .say-head {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.92rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }}
    .say-allowed .say-head {{ color: {theme["chart"]["case_benchmark"]}; }}
    .say-notallowed .say-head {{ color: {theme["chart"]["case_corridor"]}; }}
    .say-mark {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.35rem;
        height: 1.35rem;
        border-radius: 50%;
        font-size: 0.82rem;
        font-weight: 800;
        color: {p["panel_bg"]};
        flex: none;
    }}
    .say-allowed .say-mark {{ background: {theme["chart"]["case_benchmark"]}; }}
    .say-notallowed .say-mark {{ background: {theme["chart"]["case_corridor"]}; }}
    .say-list {{ margin: 0; padding-left: 1.1rem; color: {p["ink"]}; }}
    .say-list li {{ font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.35rem; }}
    .say-list li:last-child {{ margin-bottom: 0; }}

    /* Model-evaluation handoff: one restrained red footer joins the coverage
       question and its next action without presenting it as another alert. */
    .st-key-mc_next_page {{
        background: color-mix(in srgb, {case_maroon} 7%, white);
        border: 1px solid color-mix(in srgb, {case_maroon} 24%, white);
        border-left: 4px solid {case_maroon};
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-top: 1rem;
    }}
    .st-key-mc_next_page .mc-next-text {{
        color: {p["ink"]};
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.5;
        margin: 0;
    }}
    .st-key-mc_next_page [data-testid="stHorizontalBlock"] {{
        align-items: center;
        min-height: 4.5rem;
    }}
    .st-key-mc_next_page [data-testid="stColumn"] {{
        min-height: 4.5rem;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }}
    .st-key-mc_next_page [data-testid="stVerticalBlock"] {{
        justify-content: center;
        min-height: 4.5rem;
    }}
    .st-key-mc_next_page [data-testid="stElementContainer"]:has(.mc-next-text) {{
        min-height: 4.5rem;
    }}
    .st-key-mc_next_page [data-testid="stPageLink"] {{
        display: flex;
        align-items: center;
        height: 100%;
    }}
    [data-testid="stMain"] .st-key-mc_next_page [data-testid="stPageLink"] a {{
        display: flex;
        justify-content: center;
        width: 100%;
        background: {case_maroon};
        border-color: {case_maroon};
    }}
    [data-testid="stMain"] .st-key-mc_next_page [data-testid="stPageLink"] a p {{
        color: #FFFFFF !important;
        font-size: 0.86rem;
        text-align: center;
    }}
    [data-testid="stMain"] .st-key-mc_next_page [data-testid="stPageLink"] a:hover {{
        background: color-mix(in srgb, {case_maroon} 88%, black);
        border-color: color-mix(in srgb, {case_maroon} 88%, black);
    }}

    /* ---- Gold Quantity Coverage: finding strip, follow-up cards, pathway
       comparison band. The caveat box and KPI band reuse shared classes. ---- */
    .gc-strip {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.3rem 0 0.75rem 0;
    }}
    .gc-strip-chip {{
        background: {p["accent_soft"]};
        color: {p["ink"]};
        border: 1px solid {p["border"]};
        border-radius: 999px;
        padding: 0.22rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 650;
        font-variant-numeric: tabular-nums;
    }}
    .gc-size-guide {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.55rem 1rem;
        min-height: 52px;
        margin: 0.45rem 0 0.2rem;
        padding: 0.45rem 0.75rem;
        background: color-mix(in srgb, {outcome_blue} 5%, white);
        border: 1px solid color-mix(in srgb, {outcome_blue} 20%, white);
        border-radius: 7px;
    }}
    .gc-size-label {{
        color: {p["ink"]};
        font-size: 0.76rem;
        font-weight: 800;
        margin-right: 0.15rem;
    }}
    .gc-size-item {{
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        color: {p["muted"]};
        font-size: 0.74rem;
        white-space: nowrap;
    }}
    .gc-bubble {{
        display: inline-block;
        flex: none;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 0 0 3px color-mix(in srgb, {outcome_blue} 12%, transparent);
    }}
    .gc-bubble.one {{
        width: 12px; height: 12px;
        background: {theme["chart"]["network_node_one"]};
    }}
    .gc-bubble.two {{
        width: 17px; height: 17px;
        background: {theme["chart"]["network_node_two"]};
    }}
    .gc-bubble.twelve {{
        width: 42px; height: 42px;
        background: {theme["chart"]["network_hub"]};
    }}
    .gc-followups {{ margin-top: 1rem; }}
    /* The two follow-up cards: amber = the material one-off to check, teal = the
       repeated source-data pattern. A header row carries an icon, the kicker
       label and a large emphasis metric so each card leads with its number. */
    .gc-oneoff {{ border-top-color: {family_colors["gold_unwrought"]}; }}
    .gc-card-head {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.45rem;
    }}
    .gc-card-icon {{
        display: inline-flex;
        width: 1.9rem;
        height: 1.9rem;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        flex: none;
    }}
    .gc-card-icon svg {{ width: 1.05rem; height: 1.05rem; }}
    .gc-oneoff .gc-card-icon {{
        background: color-mix(in srgb, {family_colors["gold_unwrought"]} 16%, white);
        color: {family_colors["gold_unwrought"]};
    }}
    .gc-repeated .gc-card-icon {{
        background: {p["accent_soft"]};
        color: {p["accent"]};
    }}
    .gc-followups .twin-label {{ margin-bottom: 0; flex: 1; }}
    .gc-oneoff .twin-label {{ color: {family_colors["gold_unwrought"]}; }}
    .gc-definition-tip.tip {{
        display: inline-flex;
        vertical-align: middle;
        margin-left: 0.2rem;
        color: {p["accent"]};
        text-decoration: none;
    }}
    .gc-definition-tip.tip svg {{ width: 0.9rem; height: 0.9rem; }}
    .gc-card-metric {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        line-height: 1.05;
        font-size: 1.35rem;
        font-weight: 800;
        color: {p["ink"]};
        font-variant-numeric: tabular-nums;
    }}
    .gc-card-metric small {{
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {p["muted"]};
    }}
    .gc-card-title {{
        color: {p["ink"]};
        font-size: 1.02rem;
        font-weight: 750;
        margin: 0.15rem 0 0.35rem 0;
    }}
    .gc-followups .twin-card p {{
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 0;
        color: {p["ink"]};
    }}
    .gc-card-action {{
        color: {p["muted"]};
        font-size: 0.82rem;
        line-height: 1.45;
        border-top: 1px dashed {p["border"]};
        padding-top: 0.5rem;
        margin-top: 0.6rem;
    }}
    /* Section divider — a hairline with a short accent segment at the left,
       matching the Business Problem & Value section rule. */
    .gc-rule {{
        position: relative;
        height: 1px;
        background: {p["border"]};
        margin: 0.55rem 0 1.2rem 0;
    }}
    .gc-rule::before {{
        content: "";
        position: absolute;
        inset: -1px auto auto 0;
        width: 34px;
        height: 3px;
        background: {p["accent"]};
        border-radius: 2px;
    }}
    /* Country-code reference beside the persistent-gap network — a compact
       label above the shared reference table. */
    .gc-cmap-head {{
        color: {p["muted"]};
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }}
    .st-key-gc_country_map .data-table-wrap {{ width: 100%; }}
    .st-key-gc_country_map .data-table th,
    .st-key-gc_country_map .data-table td {{ white-space: nowrap; }}
    .st-key-gc_country_map .data-table th:nth-child(2),
    .st-key-gc_country_map .data-table td:nth-child(2) {{ min-width: 9rem; }}
    .gc-conclusion {{
        display: grid;
        grid-template-columns: minmax(0, 1.25fr) minmax(17rem, 0.75fr);
        gap: 1.2rem;
        align-items: center;
        color: {p["sidebar_ink"]};
        background: {p["sidebar_bg"]};
        border-left: 4px solid {p["accent"]};
        border-radius: 8px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 7px 20px color-mix(in srgb, {p["sidebar_bg"]} 16%, transparent);
    }}
    .gc-conclusion-title {{
        color: #FFFFFF;
        font-size: 1.02rem;
        font-weight: 800;
        line-height: 1.35;
        margin-bottom: 0.35rem;
    }}
    .gc-conclusion p {{
        color: {p["sidebar_ink"]};
        font-size: 0.88rem;
        line-height: 1.55;
        margin: 0;
    }}
    .gc-conclusion-actions {{
        display: grid;
        gap: 0.42rem;
    }}
    .gc-conclusion-actions span {{
        position: relative;
        color: #FFFFFF;
        border: 1px solid color-mix(in srgb, {p["sidebar_ink"]} 32%, transparent);
        border-radius: 6px;
        padding: 0.48rem 0.65rem 0.48rem 1.7rem;
        font-size: 0.78rem;
        font-weight: 650;
        line-height: 1.35;
    }}
    .gc-conclusion-actions span::before {{
        content: "✓";
        position: absolute;
        left: 0.62rem;
        color: {p["accent"]};
        font-weight: 900;
    }}
    .st-key-gc_next_page {{
        display: flex;
        justify-content: flex-end;
        margin-top: 0.55rem;
    }}
    .st-key-gc_next_page [data-testid="stPageLink"] a {{
        width: auto;
        min-width: 17rem;
        justify-content: center;
        background: {p["accent"]};
        border-color: {p["accent"]};
    }}
    .st-key-gc_next_page [data-testid="stPageLink"] a p,
    .st-key-gc_next_page [data-testid="stPageLink"] a span {{
        color: #FFFFFF !important;
        font-weight: 750;
    }}
    .st-key-gc_next_page [data-testid="stPageLink"] a:hover {{
        background: {at};
        border-color: {at};
    }}
    @media (max-width: 1050px) {{
        .src-grid, .fam-grid {{ grid-template-columns: 1fr; }}
        .src-preview {{ position: static; opacity: 1; visibility: visible;
                        transform: none; margin-top: 0.5rem; }}
        .fam-card .src-preview {{ margin-top: 0.5rem; }}
        [data-testid="stMain"]:has(.gc-page-marker) .stat-band.three {{
            grid-template-columns: 1fr;
        }}
        .gc-conclusion {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 900px) {{
        .mc-flow {{ flex-direction: column; }}
        .mc-flow-arrow {{ transform: rotate(90deg); align-self: center; }}
        .scenario-groups {{ grid-template-columns: 1fr; }}
        .mc-eval-facts {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .method-path {{ grid-template-columns: 1fr; }}
        .method-step {{ min-height: 0; }}
        .rule-adjustment-grid {{ grid-template-columns: 1fr; }}
        [data-testid="stMain"]:has(.mc-page-marker) .section-heading {{
            margin-top: 1.75rem;
        }}
        .st-key-mc_next_page [data-testid="stHorizontalBlock"],
        .st-key-mc_next_page [data-testid="stColumn"],
        .st-key-mc_next_page [data-testid="stVerticalBlock"],
        .st-key-mc_next_page [data-testid="stElementContainer"]:has(.mc-next-text) {{
            min-height: 0;
        }}
    }}
    @media (max-width: 560px) {{
        .mc-eval-facts {{ grid-template-columns: 1fr; }}
        .mental-model.coverage-boundary {{
            display: block;
            padding: 0.9rem 1rem;
        }}
        .mental-model.coverage-boundary .banner-icon {{
            display: none;
        }}
        .mental-model.coverage-boundary .mm-stamp {{
            display: block;
            white-space: normal;
            margin: 0 0 0.35rem 0;
        }}
        .st-key-gc_next_page,
        .st-key-gc_next_page [data-testid="stPageLink"],
        .st-key-gc_next_page [data-testid="stPageLink"] a {{
            width: 100%;
        }}
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
    /* Highlighted glossary term inside a heading ("corridor"): accent colour on
       top of the .tip dotted-underline, signalling a hoverable definition. */
    .section-label .corridor-term {{
        color: {p["accent"]};
        font-weight: 800;
        text-decoration-color: {p["accent"]};
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
       methodology-scene storyboard, merge/year keyframes, hover previews).
       Every keyframe above runs FROM an offset TO the natural state, so with
       animation disabled the final layout is what renders. Kept LAST in the
       sheet, with !important, so it always wins. ---- */
    @media (prefers-reduced-motion: reduce) {{
        [data-testid="stSidebar"] [data-testid="stPageLink"] a,
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
        [data-testid="stMain"] [data-testid="stPageLink"] a,
        [data-testid="stMain"] [data-testid="stPageLink"] a:hover,
        [data-testid="stMain"] [data-testid="stButton"] button,
        [data-testid="stMain"] [data-testid="stBaseButton-primary"]:hover,
        [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover,
        .anim, .bank-reveal, .bank-icon-card, .bank-ai-arrow,
        .bank-fit-step:not(:last-child)::after,
        .bank-fit-step, .bank-ai-step,
        .twin-card, .stat-tile, .flow-step, .method-step, .method-step:hover,
        .bv-entry, .story-panel, .commodity-card, .commodity-icon, .quote-card,
        .story-process-stage,
        .sb, .src-card, .fam-card,
        .yr.lit.yl1, .yr.lit.yl2, .yr.lit.yl3, .yr.lit.yl4, .yr.lit.yl5,
        .yr.focus.ylf,
        .case-banner-text,
        .queue-interpretation-boundary,
        .st-key-dashboard_filter_panel,
        .st-key-queue_case_banner,
        .st-key-queue_table_region,
        .st-key-pa_card_scale, .st-key-pa_card_market,
        .st-key-pa_card_patterns, .st-key-dtrq_closing,
        .welcome-accent, .welcome-eyebrow, .welcome-title, .welcome-sub,
        .st-key-welcome_cta,
        .st-key-welcome_cta [data-testid="stIconMaterial"],
        .about-link,
        .tip::after, .tip::before {{
            animation: none !important;
            transition: none !important;
            transform: none !important;
        }}
        .src-preview {{
            transition: none !important;
            transform: none !important;
        }}
        /* Never leave a reveal section hidden under reduced motion, even if the
           observer added .reveal-off before checking the media query. */
        .reveal-off {{
            opacity: 1 !important;
            transform: none !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def apply_landing_styles() -> None:
    """Welcome-screen sheet, injected AFTER the global sheet on the root route only.

    Turns the frame into a full-viewport institutional navy hero: sidebar space
    and collapse control hidden, ribbon clearance gone, the hero centred with
    margin-auto (so short viewports degrade to normal scrolling instead of
    clipping), a restrained staggered entrance, and one teal CTA. Reduced motion
    for the .welcome-* elements is killed by the consolidated block in the
    global sheet — it loads first but wins through !important.
    """
    theme = load_theme()
    p = theme["palette"]
    b = theme["boundary"]
    layout = theme["layout"]
    motion = theme.get("motion", {})
    # Welcome-specific pacing: deliberately slower than the dashboard pages'
    # entry_ms/entry_step_ms so the hero reads as a curtain-up, not a blink.
    entry_ms = int(motion.get("welcome_entry_ms", 640))
    step_ms = int(motion.get("welcome_stagger_ms", 130))
    hover_ms = int(motion.get("hover_ms", 180))
    easing = motion.get("easing", "ease-out")
    teal500 = p.get("teal_500", p["accent"])
    narrow = int(theme["breakpoints"]["narrow_px"])
    css = f"""
    <style>
    /* ---- Welcome screen: the only route without the dashboard chrome. ---- */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}

    /* Deep institutional navy with a very subtle tonal lift toward the top. */
    html, body, .stApp {{
        background: {b["border"]};
    }}
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(
            180deg,
            color-mix(in srgb, {p["navy_700"]} 34%, {p["sidebar_bg"]}) 0%,
            {p["sidebar_bg"]} 46%,
            {b["border"]} 100%);
    }}
    [data-testid="stMain"],
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    [data-testid="stHeader"] [data-testid="stToolbar"] {{
        color: {p["sidebar_muted"]};
    }}

    /* Viewport-centred hero column. margin-auto centring (not justify-content)
       keeps the top reachable when the viewport is short. */
    [data-testid="stMain"] {{
        display: flex;
        flex-direction: column;
    }}
    [data-testid="stMain"] .block-container {{
        margin-top: auto;
        margin-bottom: auto;
        max-width: 900px;
        width: 100%;
        padding: 3rem {int(layout["desktop_padding_px"])}px 3.5rem;
    }}

    .welcome-hero {{
        text-align: center;
        color: {p["sidebar_ink"]};
    }}
    /* Streamlit appends a heading-anchor element inside markdown h1; on the
       hero it renders as a phantom third line plus link chrome on hover. */
    .welcome-hero [data-testid="stHeaderActionElements"] {{
        display: none;
    }}
    /* Style-only markdown containers each cost one flex-gap slot above the
       hero. Collapse them — on this route every <style> carrier is style-only
       (same pattern as the ribbon wrapper) — so the hero sits at optical
       centre instead of ~20px low. */
    [data-testid="stMain"] [data-testid="stElementContainer"]:has(style) {{
        position: absolute;
        height: 0;
        overflow: hidden;
    }}
    .welcome-accent {{
        width: 62px;
        height: 3px;
        border-radius: 999px;
        margin: 0 auto 32px;
        background: {teal500};
    }}
    .welcome-eyebrow {{
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.19em;
        text-transform: uppercase;
        color: {p["sidebar_muted"]};
        margin-bottom: 26px;
    }}
    /* Element+class selectors: Streamlit styles markdown h1/p through
       [data-testid="stMarkdownContainer"] rules; these must outrank them or
       the hero loses its margins (auto-centring) and type scale. The size is
       capped so the longest phrase line ("Trade-Based Money Laundering
       (TBML)") stays on one line within the 900px column; per-line wrapping
       still kicks in on narrow viewports. */
    .welcome-hero h1.welcome-title {{
        margin: 0 0 30px;
        padding: 0; /* Streamlit gives markdown h1 default block padding */
        font-size: clamp(30px, 4vw, 44px);
        font-weight: 800;
        letter-spacing: -0.008em;
        line-height: 1.2;
        color: {p["sidebar_ink"]};
    }}
    .welcome-title-line {{
        display: block;
    }}
    .welcome-hero p.welcome-sub {{
        margin: 0 auto;
        max-width: 33em;
        font-size: clamp(16px, 2vw, 19px);
        line-height: 1.66;
        color: color-mix(in srgb, {p["sidebar_muted"]} 78%, {p["sidebar_ink"]});
    }}

    /* The one primary action: real Streamlit button, centred. Styled as a
       quiet ghost pill — frost outline on navy, no heavy fill or glow — with
       the arrow nudging right on hover as the single micro-interaction. The
       keyed container is a flex column (stVerticalBlock): centring at that
       level works whatever width the inner wrappers take. */
    .st-key-welcome_cta {{
        margin-top: 40px;
        align-items: center;
    }}
    .st-key-welcome_cta [data-testid="stElementContainer"],
    .st-key-welcome_cta [data-testid="stButton"] {{
        display: flex;
        justify-content: center;
        width: auto;
    }}
    /* Label first, arrow after — Streamlit renders the icon before the label
       inside the button's inner flex span. */
    .st-key-welcome_cta [data-testid="stButton"] button [data-has-shortcut] {{
        flex-direction: row-reverse;
    }}
    .st-key-welcome_cta [data-testid="stButton"] button {{
        min-height: 50px;
        padding: 0 30px;
        border-radius: 999px;
        font-size: 15.5px;
        font-weight: 600;
        letter-spacing: 0.01em;
        background: color-mix(in srgb, {p["sidebar_ink"]} 5%, transparent);
        border: 1px solid color-mix(in srgb, {p["sidebar_ink"]} 30%, transparent);
        color: {p["sidebar_ink"]};
        box-shadow: none;
        transition: border-color {hover_ms}ms {easing},
                    background {hover_ms}ms {easing},
                    box-shadow {hover_ms}ms {easing},
                    transform {hover_ms}ms {easing};
    }}
    .st-key-welcome_cta [data-testid="stButton"] button [data-testid="stIconMaterial"] {{
        transition: transform {hover_ms}ms {easing};
    }}
    /* Hover/active must out-rank the global stMain primary rules (same trick
       as the Replay variant): the ghost warms toward teal and the arrow leads
       the eye forward — never the global light-surface hover that recedes on
       navy. */
    [data-testid="stMain"] .st-key-welcome_cta [data-testid="stBaseButton-primary"]:hover:not(:disabled) {{
        background: color-mix(in srgb, {teal500} 14%, transparent);
        border-color: {teal500};
        color: {p["sidebar_ink"]};
        transform: translateY(-1px);
        box-shadow: 0 10px 26px color-mix(in srgb, {b["border"]} 55%, transparent);
    }}
    [data-testid="stMain"] .st-key-welcome_cta [data-testid="stBaseButton-primary"]:hover:not(:disabled) [data-testid="stIconMaterial"] {{
        transform: translateX(3px);
    }}
    [data-testid="stMain"] .st-key-welcome_cta [data-testid="stBaseButton-primary"]:active:not(:disabled) {{
        transform: translateY(0);
        background: color-mix(in srgb, {teal500} 22%, transparent);
    }}
    .st-key-welcome_cta [data-testid="stButton"] button:focus-visible {{
        outline: 3px solid {teal500};
        outline-offset: 3px;
    }}

    /* Restrained entrance: accent+eyebrow, then title, description, CTA.
       Slightly longer travel suits the slower welcome pacing. */
    @keyframes welcome-rise {{
        from {{ opacity: 0; transform: translateY(14px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .welcome-accent,
    .welcome-eyebrow,
    .welcome-title,
    .welcome-sub,
    .st-key-welcome_cta {{
        animation: welcome-rise {entry_ms}ms {easing} both;
    }}
    .welcome-title {{ animation-delay: {step_ms}ms; }}
    .welcome-sub {{ animation-delay: {step_ms * 2}ms; }}
    .st-key-welcome_cta {{ animation-delay: {step_ms * 3}ms; }}

    @media (max-width: {narrow}px) {{
        [data-testid="stMain"] .block-container {{
            padding-left: 24px;
            padding-right: 24px;
        }}
        .st-key-welcome_cta {{
            align-items: stretch;
        }}
        .st-key-welcome_cta [data-testid="stElementContainer"],
        .st-key-welcome_cta [data-testid="stButton"],
        .st-key-welcome_cta [data-testid="stButton"] button {{
            width: 100%;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def apply_dashboard_entry_styles() -> None:
    """One-shot dashboard entrance for the render right after the landing CTA.

    Injected for that single run (the session flag is consumed), so widget
    reruns never replay it: content fades up ~8px while the sidebar slides in
    from the left at desktop widths only — never fighting Streamlit's own
    collapse transform on narrow viewports. The sheet is transient, so it
    carries its own reduced-motion guard; the sidebar needs animation-only
    killing (a blanket transform: none would break collapse positioning).
    """
    theme = load_theme()
    motion = theme.get("motion", {})
    ms = int(motion.get("dashboard_entry_ms", 340))
    delay_ms = int(motion.get("dashboard_entry_delay_ms", 160))
    sidebar_ms = int(motion.get("dashboard_sidebar_ms", 560))
    easing = motion.get("easing", "ease-out")
    sidebar_min = int(theme["breakpoints"]["sidebar_px"])
    css = f"""
    <style>
    /* Choreography: the navigation slides fully in from the left edge first,
       and the page content fades up under it a beat later — the shell visibly
       "arrives" around the story. Opacity-only on the content column: the
       boundary ribbon lives INSIDE .block-container and is position: fixed —
       any transform on an ancestor would re-root it away from the viewport.
       The slide lives on the sidebar, which contains no fixed descendants. */
    @keyframes dash-enter {{
        from {{ opacity: 0; }}
        to   {{ opacity: 1; }}
    }}
    @keyframes dash-enter-side {{
        from {{ transform: translateX(-100%); }}
        to   {{ transform: translateX(0); }}
    }}
    [data-testid="stMain"] .block-container {{
        animation: dash-enter {ms}ms {easing} {delay_ms}ms both;
    }}
    @media (min-width: {sidebar_min}px) {{
        [data-testid="stSidebar"] {{
            animation: dash-enter-side {sidebar_ms}ms {easing} both;
        }}
    }}
    /* This sheet's own wrapper must not cost a flex-gap slot for one render
       (it would nudge the whole page down 16px, then snap on the next rerun).
       The flex child is the layout wrapper AROUND the keyed block, so collapse
       that; a <style> keeps applying from inside a display:none subtree. */
    [data-testid="stLayoutWrapper"]:has(.st-key-dash_entry_sheet),
    [data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-dash_entry_sheet) {{
        display: none;
    }}
    @media (prefers-reduced-motion: reduce) {{
        [data-testid="stMain"] .block-container,
        [data-testid="stSidebar"] {{
            animation: none !important;
        }}
    }}
    </style>
    """
    with st.container(key="dash_entry_sheet"):
        st.markdown(css, unsafe_allow_html=True)
