"""Page header (eyebrow / title / subtitle) + section titles + provenance ledger."""

from __future__ import annotations

from dashboard.components.banners import render_dataset_strip
from dashboard.components.page_shell import render_page_header, render_section_heading
from dashboard.services import path_resolver as paths


def page_header(title: str, subtitle: str, eyebrow: str = "Stakeholder analytics",
                icon: str | None = None) -> None:
    render_page_header(title, subtitle, eyebrow, icon=icon)


def section_title(title: str, caption: str | None = None,
                  icon: str = "layers", info: str | None = None) -> None:
    render_section_heading(title, caption, icon, info)


def ledger(*file_keys: str, note: str = "") -> None:
    """Render a panel's optional analytic note.

    The repository file paths that used to head this strip are deliberately NOT
    shown: they are build-time provenance that a dashboard viewer does not need.
    The artefact keys are still passed and validated here, so each panel keeps
    documenting in code which pipeline outputs back it — the audit trail lives in
    the source, not on screen. With no note, nothing is rendered.
    """
    for key in file_keys:
        paths.relpath(key)  # raises on an unknown artefact key
    if note:
        render_dataset_strip(note)
