"""Status pills for quality status and evidence severity.

Colour never carries the state alone — every pill contains its text label
(status colours on white can sit below 3:1 contrast; the label is the relief).
"""

from __future__ import annotations

import html

from dashboard.services.data_loader import load_theme


def quality_pill(status: str) -> str:
    status_theme = load_theme()["status"]
    fallback = {**status_theme["fallback"],
                "label": str(status).replace("_", " ").capitalize()}
    spec = status_theme["quality"].get(str(status), fallback)
    return _pill(spec["label"], spec["color"])


def severity_pill(severity: str) -> str:
    status_theme = load_theme()["status"]
    fallback = {**status_theme["fallback"], "label": str(severity).capitalize()}
    spec = status_theme["severity"].get(str(severity).lower(), fallback)
    return _pill(f"{spec['label']} severity", spec["color"])


def _pill(label: str, color: str) -> str:
    return f'<span class="status-pill" style="color:{color};">{html.escape(label)}</span>'


def quality_label(status: str) -> str:
    # Plain-text label for tables (st.dataframe cannot render HTML pills).
    return load_theme()["status"]["quality"].get(str(status), {}).get(
        "label", str(status).replace("_", " ").capitalize()
    )
