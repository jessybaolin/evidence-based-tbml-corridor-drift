"""
Central read-only loading layer between the analytical pipeline and the pages.

WHAT IT DOES:
    Loads every CSV/Parquet/JSON/YAML/Markdown artefact the dashboard shows,
    caches stable reads with st.cache_data, preserves analytical values exactly
    (HS6 stays a six-character string), and fails loudly — a missing REQUIRED
    file raises MissingOutputError with the pipeline stage to run; a missing
    OPTIONAL file returns None so the page can show a transparent empty state.

READS (inputs): the files registered in services.path_resolver.DATA_FILES.
WRITES (outputs): nothing — the dashboard never mutates analytical outputs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from dashboard.services import path_resolver as paths

# Which pipeline stage regenerates each artefact — used in error/empty states
# so a stakeholder-facing message always says what to run.
_REGENERATE_HINTS = {
    "review_queue": "python src/06_train_evaluate_models.py (then src/07_build_evidence.py)",
    "evidence": "python src/07_build_evidence.py",
    "panel": "python src/03_build_panel.py",
    "features": "python src/04_build_features.py",
    "model_comparison": "python src/06_train_evaluate_models.py",
    "model_selection": "python src/06_train_evaluate_models.py",
    "hybrid_candidates": "python src/06_train_evaluate_models.py",
    "scenario_split_manifest": "python src/05_build_scenarios.py",
    "scenario_labels": "python src/05_build_scenarios.py",
    "shap_summary_values": "python src/06_train_evaluate_models.py",
    "logistic_coefficients": "python src/06_train_evaluate_models.py",
    "xgboost_parameters": "python src/06_train_evaluate_models.py",
    "analyst_briefs": "python src/08_build_briefs.py",
    "source_manifest": "python src/01_verify_sources.py",
    "source_file_inventory": "python src/01_verify_sources.py",
    "exclusion_audit": "python src/03_build_panel.py",
    "benchmarks": "python src/02_ingest_official_sources.py",
    "feature_explanations": "python src/09_generate_reports.py",
    "data_dictionary_md": "python src/09_generate_reports.py",
}


class MissingOutputError(FileNotFoundError):
    """A required analytical output is absent — the dashboard cannot substitute data."""


def _resolve(name: str) -> Path | None:
    # Shared existence handling: required -> raise with the regeneration hint,
    # optional -> None (pages render components.empty_states instead).
    spec = paths.DATA_FILES[name]
    path = spec["path"]
    if path.exists():
        return path
    if spec["required"]:
        hint = _REGENERATE_HINTS.get(name, "the relevant pipeline stage")
        raise MissingOutputError(
            f"Required project output is missing: {paths.relpath(name)}. "
            f"Run `{hint}` from the repository root, then reload the dashboard."
        )
    return None


# ---- Tabular outputs -------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_review_queue() -> pd.DataFrame:
    # hs6 must stay a six-character string; scores stay raw floats.
    path = _resolve("review_queue")
    frame = pd.read_csv(path, dtype={"hs6": "string", "obs_id": "string"})
    frame["hs6"] = frame["hs6"].str.zfill(6)
    return frame


@st.cache_data(show_spinner=False)
def load_evidence() -> pd.DataFrame:
    path = _resolve("evidence")
    return pd.read_csv(path, dtype={"obs_id": "string", "evidence_id": "string"})


@st.cache_data(show_spinner=False)
def load_panel(columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    # The 25,844-row clean panel. Pages request only the columns they need so a
    # widget interaction never re-reads the full 50-column table.
    path = _resolve("panel")
    frame = pd.read_parquet(path, columns=list(columns) if columns else None)
    if "hs6" in frame.columns:
        frame["hs6"] = frame["hs6"].astype("string").str.zfill(6)
    return frame


@st.cache_data(show_spinner=False)
def load_features(columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    path = _resolve("features")
    frame = pd.read_parquet(path, columns=list(columns) if columns else None)
    if "hs6" in frame.columns:
        frame["hs6"] = frame["hs6"].astype("string").str.zfill(6)
    return frame


@st.cache_data(show_spinner=False)
def load_model_comparison() -> pd.DataFrame:
    return pd.read_csv(_resolve("model_comparison"))


@st.cache_data(show_spinner=False)
def load_hybrid_candidates() -> pd.DataFrame | None:
    path = _resolve("hybrid_candidates")
    return pd.read_csv(path) if path else None


@st.cache_data(show_spinner=False)
def load_shap_summary_values() -> pd.DataFrame | None:
    path = _resolve("shap_summary_values")
    return pd.read_csv(path) if path else None


@st.cache_data(show_spinner=False)
def load_logistic_coefficients() -> pd.DataFrame | None:
    path = _resolve("logistic_coefficients")
    return pd.read_csv(path) if path else None


@st.cache_data(show_spinner=False)
def load_source_file_inventory() -> pd.DataFrame | None:
    path = _resolve("source_file_inventory")
    return pd.read_csv(path) if path else None


@st.cache_data(show_spinner=False)
def load_scenario_labels() -> pd.DataFrame | None:
    # Used ONLY by integrity checks (queue must carry clean-panel values);
    # scenario labels are never rendered as findings.
    path = _resolve("scenario_labels")
    return pd.read_parquet(path) if path else None


@st.cache_data(show_spinner=False)
def load_benchmarks() -> pd.DataFrame | None:
    path = _resolve("benchmarks")
    if not path:
        return None
    frame = pd.read_parquet(path)
    frame["hs6"] = frame["hs6"].astype("string").str.zfill(6)
    return frame


# ---- JSON / YAML -----------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_model_selection() -> dict:
    return json.loads(_resolve("model_selection").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_scenario_split_manifest() -> dict | None:
    path = _resolve("scenario_split_manifest")
    return json.loads(path.read_text(encoding="utf-8")) if path else None


@st.cache_data(show_spinner=False)
def load_analyst_briefs() -> list | None:
    # The landing page cites the briefs' existence and COUNT as a pipeline
    # deliverable; brief text itself is never rendered in the dashboard.
    path = _resolve("analyst_briefs")
    return json.loads(path.read_text(encoding="utf-8")) if path else None


@st.cache_data(show_spinner=False)
def load_source_manifest() -> dict | None:
    path = _resolve("source_manifest")
    return json.loads(path.read_text(encoding="utf-8")) if path else None


@st.cache_data(show_spinner=False)
def load_data_source_notes() -> dict | None:
    path = _resolve("data_source_notes")
    return json.loads(path.read_text(encoding="utf-8")) if path else None


@st.cache_data(show_spinner=False)
def load_xgboost_parameters() -> dict | None:
    path = _resolve("xgboost_parameters")
    return json.loads(path.read_text(encoding="utf-8")) if path else None


@st.cache_data(show_spinner=False)
def load_project_config() -> dict:
    return yaml.safe_load(_resolve("project_config").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_families_config() -> list[dict]:
    payload = yaml.safe_load(_resolve("hs_families").read_text(encoding="utf-8"))
    return payload["families"]


@st.cache_data(show_spinner=False)
def load_benchmark_series_config() -> list[dict] | None:
    path = _resolve("benchmark_series")
    if not path:
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))["benchmarks"]


def conclusion_boundary() -> str:
    # Single source of truth for the boundary sentence: configs/project.yml.
    return str(load_project_config()["conclusion_boundary"])


# ---- Dashboard configuration ------------------------------------------------

@st.cache_data(show_spinner=False)
def load_theme() -> dict:
    return yaml.safe_load(
        (paths.DASHBOARD_CONFIG / "dashboard_theme.yml").read_text(encoding="utf-8")
    )


@st.cache_data(show_spinner=False)
def load_content() -> dict:
    return yaml.safe_load(
        (paths.DASHBOARD_CONFIG / "dashboard_content.yml").read_text(encoding="utf-8")
    )


# ---- Markdown reference documents -------------------------------------------

def _parse_markdown_table(text: str) -> pd.DataFrame:
    # Parse the first pipe-table in a markdown document. The pipeline writes
    # these tables with pandas.to_markdown, so the format is stable.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue  # separator row
        rows.append(cells)
    if len(rows) < 2:
        return pd.DataFrame()
    header, *body = rows
    body = [r for r in body if len(r) == len(header)]
    return pd.DataFrame(body, columns=header)


@st.cache_data(show_spinner=False)
def load_feature_explanations() -> pd.DataFrame | None:
    # Approved plain-English interpretations (feature_name | derivation | ... |
    # plain_english_interpretation) used on the case page and in the appendix.
    path = _resolve("feature_explanations")
    if not path:
        return None
    table = _parse_markdown_table(path.read_text(encoding="utf-8"))
    return table if not table.empty else None


@st.cache_data(show_spinner=False)
def load_data_dictionary_md() -> pd.DataFrame | None:
    # The pipeline's own dictionary: field | meaning | type | caveat.
    path = _resolve("data_dictionary_md")
    if not path:
        return None
    table = _parse_markdown_table(path.read_text(encoding="utf-8"))
    return table if not table.empty else None


# ---- Figures -----------------------------------------------------------------

def figure_path(name: str) -> Path | None:
    path = paths.FIGURE_FILES.get(name)
    return path if path and path.exists() else None


def regenerate_hint(name: str) -> str:
    return _REGENERATE_HINTS.get(name, "the relevant pipeline stage")
