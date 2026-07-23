"""Focused contracts for shared visual component anatomy."""

from __future__ import annotations

import pytest

from dashboard.components.cards import SOURCE_ROLES, kpi_card_markup, source_card_markup
from dashboard.components.icons import icon_names, render_icon
from dashboard.services.data_loader import load_theme


def test_icon_registry_is_local_and_uses_current_color():
    expected = {
        "database", "calendar", "package", "shield-check", "chart-pie", "brain",
        "layers", "landmark", "line-chart", "file-search", "file-text", "rotate-cw",
        "info",
    }
    assert expected <= set(icon_names())
    svg = render_icon("database")
    assert 'stroke="currentColor"' in svg
    assert 'fill="none"' in svg
    assert 'aria-hidden="true"' in svg
    assert "http" not in svg


def test_kpi_markup_uses_one_shared_anatomy_and_teal_accent():
    markup = kpi_card_markup("25,844", "Observations", "Official rows", "database")
    assert "kpi-card" in markup
    assert "kpi-icon" in markup
    assert "icon-badge" in markup
    assert "acc-blue" not in markup
    theme = load_theme()
    assert theme["components"]["kpi"]["accent"] == theme["palette"]["accent"]


def test_source_renderer_accepts_only_approved_roles():
    assert SOURCE_ROLES == {"official", "benchmark", "typology"}
    for role, icon in [
        ("official", "landmark"), ("benchmark", "line-chart"),
        ("typology", "file-search"),
    ]:
        markup = source_card_markup(
            role=role, icon=icon, eyebrow="Role", title="Source",
            sections_html='<div class="src-row">Body</div>',
        )
        assert f"source-role-{role}" in markup
        assert "source-icon" in markup
    with pytest.raises(ValueError):
        source_card_markup(
            role="decorative", icon="info", eyebrow="Role", title="Source",
            sections_html="Body",
        )


def test_selection_tokens_are_semantic_and_shared():
    theme = load_theme()
    assert theme["selection"]["background"] == theme["palette"]["amber_soft"]
    assert theme["selection"]["border"] == theme["palette"]["amber"]
    assert theme["selection"]["text"] == theme["palette"]["ink"]
    # The focus ink used for the selected record's identity is the shared deep
    # amber, not a one-off hex invented for the case strip.
    assert theme["selection"]["focus_text"] == theme["palette"]["amber_ink"]

