"""Page header (eyebrow / title / subtitle) + section titles + provenance ledger."""

from __future__ import annotations

from dashboard.components.banners import render_dataset_strip
from dashboard.components.page_shell import render_page_header, render_section_heading
from dashboard.services import path_resolver as paths


def page_header(title: str, subtitle: str, eyebrow: str = "Stakeholder analytics") -> None:
    render_page_header(title, subtitle, eyebrow)


def section_title(title: str, caption: str | None = None,
                  icon: str = "layers") -> None:
    render_section_heading(title, caption, icon)


def ledger(*file_keys: str, note: str = "") -> None:
    # The provenance ledger line: which repository files back this panel.
    parts = [paths.relpath(key) for key in file_keys]
    if note:
        parts.append(note)
    render_dataset_strip(" · ".join(parts))
