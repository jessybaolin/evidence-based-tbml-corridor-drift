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


section_title(copy["section_heading"], copy["section_caption"], icon="package")

cols = st.columns(2, gap="medium")
for index, item in enumerate(copy["items"]):
    with cols[index]:
        _download_card(item, f"doc_download_{index}")
