"""
Repository-root resolution and canonical paths for every file the dashboard reads.

WHAT IT DOES:
    Locates the repository root by walking up from this file and looking for the
    project's two anchor artefacts (configs/project.yml and src/tbml_common.py),
    so the dashboard works no matter which folder the terminal was opened from.

READS (inputs): nothing at import time beyond the filesystem walk.
WRITES (outputs): nothing — the dashboard never writes into the repository.
"""

from __future__ import annotations

from pathlib import Path

# Anchor files that uniquely identify the repository root. Both must exist so a
# stray configs/ folder elsewhere can never be mistaken for the project.
_ROOT_MARKERS = ("configs/project.yml", "src/tbml_common.py")


def repo_root() -> Path:
    # Walk upward from dashboard/services/ until both markers are present.
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if all((candidate / marker).exists() for marker in _ROOT_MARKERS):
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository root. The dashboard expects to live in "
        "<repo>/dashboard/ next to configs/project.yml and src/tbml_common.py."
    )


ROOT = repo_root()
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_OUTPUTS = ROOT / "data" / "outputs"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
CONFIGS = ROOT / "configs"
DASHBOARD_CONFIG = ROOT / "dashboard" / "config"

# Every analytical file the dashboard consumes, in one registry so pages can
# report provenance ("which file backs this panel") without hardcoding paths.
# required=True files raise a dashboard-facing error when absent;
# required=False files degrade to a transparent empty state.
DATA_FILES: dict[str, dict] = {
    "review_queue": {
        "path": DATA_OUTPUTS / "top_ranked_corridors.csv",
        "required": True,
        "official": True,
        "purpose": "Top-ranked real observations for human review",
    },
    "evidence": {
        "path": DATA_OUTPUTS / "evidence_table.csv",
        "required": True,
        "official": True,
        "purpose": "Recomputable evidence rows per review candidate",
    },
    "panel": {
        "path": DATA_PROCESSED / "corridor_product_year_panel.parquet",
        "required": True,
        "official": True,
        "purpose": "Clean annual corridor-product panel (all official rows)",
    },
    "features": {
        "path": DATA_PROCESSED / "corridor_features.parquet",
        "required": True,
        "official": True,
        "purpose": "Time-safe features for the real observations",
    },
    "model_comparison": {
        "path": DATA_OUTPUTS / "model_comparison.csv",
        "required": True,
        "official": False,  # scenario-based evaluation metrics
        "purpose": "Scenario-based model evaluation metrics",
    },
    "model_selection": {
        "path": DATA_OUTPUTS / "model_selection.json",
        "required": True,
        "official": False,
        "purpose": "Which challenger/weight/score column was selected and why",
    },
    "hybrid_candidates": {
        "path": DATA_OUTPUTS / "hybrid_validation_candidates.csv",
        "required": False,
        "official": False,
        "purpose": "Validation metrics per candidate hybrid weight",
    },
    "scenario_split_manifest": {
        "path": DATA_PROCESSED / "scenario_split_manifest.json",
        "required": False,
        "official": False,
        "purpose": "Train/validation/test split counts and label separation",
    },
    "scenario_labels": {
        "path": DATA_PROCESSED / "scenario_labels.parquet",
        "required": False,
        "official": False,
        "purpose": "Scenario labels (integrity checks only — never displayed as findings)",
    },
    "shap_summary_values": {
        "path": DATA_OUTPUTS / "shap_summary_values.csv",
        "required": False,
        "official": False,
        "purpose": "Global mean |SHAP| per feature (model-contribution context)",
    },
    "logistic_coefficients": {
        "path": DATA_OUTPUTS / "logistic_coefficients.csv",
        "required": False,
        "official": False,
        "purpose": "Logistic baseline coefficients",
    },
    "xgboost_parameters": {
        "path": DATA_OUTPUTS / "xgboost_parameters.json",
        "required": False,
        "official": False,
        "purpose": "Selected XGBoost parameters and tuning trials",
    },
    "analyst_briefs": {
        "path": DATA_OUTPUTS / "analyst_briefs.json",
        "required": False,
        "official": False,  # deterministic renderings over official evidence
        "purpose": "Deterministic caveated analyst briefs for the top-ranked cases "
                   "(the dashboard cites their existence/count only, never the text)",
    },
    "source_manifest": {
        "path": DATA_OUTPUTS / "source_manifest.json",
        "required": False,
        "official": True,
        "purpose": "Source verification record (hashes, counts, checks)",
    },
    "data_source_notes": {
        "path": DATA_RAW / "data_source_notes.json",
        "required": False,
        "official": True,
        "purpose": "Provenance notes for the BACI extract (URLs, units, counts)",
    },
    "source_file_inventory": {
        "path": DATA_OUTPUTS / "source_file_inventory.csv",
        "required": False,
        "official": True,
        "purpose": "SHA-256 inventory of the declared raw inputs",
    },
    "exclusion_audit": {
        "path": DATA_PROCESSED / "exclusion_audit.csv",
        "required": False,
        "official": True,
        "purpose": "Audit of caveated and excluded rows",
    },
    "benchmarks": {
        "path": ROOT / "data" / "interim" / "worldbank_commodity_benchmarks.parquet",
        "required": False,
        "official": True,
        "purpose": "World Bank annual benchmark rows (3 commodities x 8 years)",
    },
    "feature_explanations": {
        "path": REPORTS / "feature_explanation_table.md",
        "required": False,
        "official": True,
        "purpose": "Approved plain-English feature interpretations",
    },
    "data_dictionary_md": {
        "path": REPORTS / "data_dictionary.md",
        "required": False,
        "official": True,
        "purpose": "Pipeline-generated data dictionary (field/meaning/type/caveat)",
    },
    "project_config": {
        "path": CONFIGS / "project.yml",
        "required": True,
        "official": True,
        "purpose": "Project scope, split years, top-k, conclusion boundary",
    },
    "hs_families": {
        "path": CONFIGS / "hs_families.yml",
        "required": True,
        "official": True,
        "purpose": "HS6 family metadata and approved caveats",
    },
    "benchmark_series": {
        "path": CONFIGS / "benchmark_series.yml",
        "required": False,
        "official": True,
        "purpose": "Benchmark series mapping, units, conversion methods",
    },
}

# Existing report figures referenced (not regenerated) by the dashboard.
FIGURE_FILES: dict[str, Path] = {
    "model_comparison": FIGURES / "model_comparison.png",
    "hard_negative_comparison": FIGURES / "hard_negative_comparison.png",
    "shap_summary": FIGURES / "shap_summary.png",
    # Methodology-story diagrams for the "From Data to Review Queue" page.
    "official_data_pipeline_architecture": FIGURES / "official_data_pipeline_architecture.png",
    "source_to_report_data_flow": FIGURES / "source_to_report_data_flow.png",
    "time_safe_feature_construction_flow": FIGURES / "time_safe_feature_construction_flow.png",
    "train_validation_test_ml_workflow": FIGURES / "train_validation_test_ml_workflow.png",
}


def data_path(name: str) -> Path:
    if name not in DATA_FILES:
        raise KeyError(f"Unknown dashboard data file: {name!r}")
    return DATA_FILES[name]["path"]


def relpath(name: str) -> str:
    # Repo-relative path with forward slashes, used in provenance ledger lines.
    return data_path(name).relative_to(ROOT).as_posix()
