"""Documentation downloads for stakeholder-facing project deliverables."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from dashboard.components.icons import render_icon
from dashboard.components.page_header import page_header, section_title
from dashboard.services import data_loader as load

content = load.load_content()
copy = content["pages"]["documentation"]
page_header(copy["title"], copy["subtitle"], copy["eyebrow"])

DELIVERABLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "deliverables"


def _render_documentation_styles() -> None:
    theme = load.load_theme()
    p = theme["palette"]
    challenge_accent = theme["status"]["severity"]["high"]["color"]
    shadow = p.get("card_shadow", "rgba(29,45,70,0.08)")
    css = f"""
    <style>
    .doc-download-card {{
        display: flex !important;
        gap: 0.85rem !important;
        min-height: 132px !important;
        background: {p["panel_bg"]} !important;
        border: 1px solid {p["border"]} !important;
        border-top: 3px solid {challenge_accent} !important;
        border-radius: 8px !important;
        padding: 0.95rem 1.05rem !important;
        box-shadow: 0 4px 14px {shadow} !important;
        transition: transform 180ms ease-out, box-shadow 180ms ease-out !important;
    }}
    .doc-download-card:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(198, 93, 99, 0.14) !important;
    }}
    .doc-download-icon {{
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 2.3rem !important;
        height: 2.3rem !important;
        border-radius: 8px !important;
        background: rgba(198, 93, 99, 0.12) !important;
        color: {challenge_accent} !important;
        flex: none !important;
    }}
    .doc-download-icon svg {{ width: 1.15rem !important; height: 1.15rem !important; }}
    .doc-download-copy {{ min-width: 0 !important; }}
    .doc-download-title {{
        color: {p["ink"]} !important;
        font-size: 1rem !important;
        font-weight: 750 !important;
        line-height: 1.25 !important;
    }}
    .doc-download-detail {{
        color: {p["muted"]} !important;
        font-size: 0.88rem !important;
        line-height: 1.45 !important;
        margin-top: 0.3rem !important;
    }}
    .doc-download-meta {{
        color: {challenge_accent} !important;
        font-size: 0.76rem !important;
        font-weight: 750 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        margin-top: 0.55rem !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def _e(text: object) -> str:
    return html.escape(str(text), quote=True)


@st.cache_data(show_spinner=False)
def _read_pdf(file_name: str) -> bytes:
    path = DELIVERABLES_DIR / file_name
    if not path.is_file():
        return b""
    return path.read_bytes()


def _download_card(item: dict, key: str) -> None:
    pdf_bytes = _read_pdf(item["file_name"])
    available = bool(pdf_bytes)
    status = item["status_available"] if available else item["status_missing"]
    button_help = item["button_help_available"] if available else item["button_help_missing"]
    st.markdown(
        f'<div class="doc-download-card">'
        f'<div class="doc-download-icon">{render_icon(item["icon"])}</div>'
        f'<div class="doc-download-copy">'
        f'<div class="doc-download-title">{_e(item["title"])}</div>'
        f'<div class="doc-download-detail">{_e(item["detail"])}</div>'
        f'<div class="doc-download-meta">{_e(status)}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    st.download_button(
        item["button_label"],
        data=pdf_bytes,
        file_name=item["file_name"],
        mime="application/pdf",
        disabled=not available,
        icon=":material/download:",
        key=key,
        help=button_help,
    )


_render_documentation_styles()
section_title(copy["section_heading"], copy["section_caption"], icon="package")

cols = st.columns(2, gap="medium")
for index, item in enumerate(copy["items"]):
    with cols[index]:
        _download_card(item, f"doc_download_{index}")
