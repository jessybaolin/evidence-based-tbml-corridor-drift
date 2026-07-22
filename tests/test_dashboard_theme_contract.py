"""Static contracts that keep dashboard pages inside the shared visual system."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "dashboard" / "app_pages"
THEME_PATH = ROOT / "dashboard" / "config" / "dashboard_theme.yml"
STREAMLIT_CONFIG = ROOT / ".streamlit" / "config.toml"


def _page_sources() -> dict[Path, str]:
    return {path: path.read_text(encoding="utf-8") for path in PAGES.glob("*.py")}


def test_pages_have_no_local_visual_values_or_global_styles():
    forbidden_colour = re.compile(r"#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(")
    for path, source in _page_sources().items():
        assert not forbidden_colour.search(source), path
        assert "<style" not in source.lower(), path
        assert "load_theme" not in source, path


def test_pages_do_not_bypass_shared_plotly_theme():
    for path, source in _page_sources().items():
        assert "import plotly" not in source, path
        assert "st.plotly_chart" not in source, path
        assert "plotly.graph_objects" not in source, path


def test_native_streamlit_theme_matches_yaml_core_palette():
    theme = yaml.safe_load(THEME_PATH.read_text(encoding="utf-8"))
    with STREAMLIT_CONFIG.open("rb") as handle:
        native = tomllib.load(handle)["theme"]
    palette = theme["palette"]
    assert native["primaryColor"] == palette["accent"]
    # backgroundColor is intentionally the panel white (not page_bg): it drives
    # the st.dataframe (glide) header fill, which we keep white to match the
    # cells. The visual page plane (page_bg) is painted by styles.py CSS instead.
    assert native["backgroundColor"] == palette["panel_bg"]
    assert native["secondaryBackgroundColor"] == palette["panel_bg"]
    assert native["textColor"] == palette["ink"]


def test_expanded_theme_sections_and_semantic_roles_exist():
    theme = yaml.safe_load(THEME_PATH.read_text(encoding="utf-8"))
    required = {
        "palette", "typography", "spacing", "layout", "surfaces", "components",
        "source_roles", "selection", "families", "status", "chart", "motion",
        "breakpoints",
    }
    assert required <= theme.keys()
    assert set(theme["source_roles"]) == {"official", "benchmark", "typology"}
    assert theme["components"]["kpi"]["accent"] == theme["palette"]["accent"]
    assert not any(key.startswith("kpi_") for key in theme["palette"])


def test_load_bearing_page_directory_and_design_authority():
    assert PAGES.is_dir()
    assert not (ROOT / "dashboard" / "pages").exists()
    memory = ROOT / ".claude" / "agent-memory" / "streamlit-dashboard-refinement-qa"
    obsolete_name = "dashboard-" + "winter-blue-palette"
    assert (memory / "dashboard-design-system.md").is_file()
    assert not (memory / f"{obsolete_name}.md").exists()
    for path in [ROOT / ".claude", ROOT / "dashboard", ROOT / "tests"]:
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix in {".md", ".py", ".yml", ".toml"}:
                assert obsolete_name not in candidate.read_text(
                    encoding="utf-8", errors="ignore"
                ), candidate


def test_boundary_footer_is_rendered_once_by_entry_point():
    entry = (ROOT / "dashboard" / "streamlit_app.py").read_text(encoding="utf-8")
    assert entry.count("render_boundary_footer()") == 1
    for path, source in _page_sources().items():
        assert "render_boundary_footer" not in source, path
        assert "boundary_ribbon" not in source, path


def test_every_page_uses_the_shared_header_contract():
    for path, source in _page_sources().items():
        if path.name == "landing.py":
            # The welcome screen has no dashboard header by design; it must
            # render through the shared landing component instead of ad-hoc UI.
            assert "render_landing(" in source, path
            continue
        assert "page_header(" in source or "render_page_header(" in source, path
