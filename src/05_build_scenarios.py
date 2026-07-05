"""
05_build_scenarios.py — Inject synthetic review-priority scenarios (for model evaluation ONLY).

PIPELINE STEP: 6 of 12  (runs after 04_build_features.py, before 06_train_evaluate_models.py)

WHAT IT DOES:
  Public BACI data has no confirmed money-laundering labels, so the project cannot train
  a supervised model on real labels. Instead it FREEZES the clean panel and then injects a
  small set of controlled, synthetic transformations (e.g. overvaluation, undervaluation,
  low-volume/high-value) plus "hard negatives" (unusual-but-benign cases). These give the
  models something to be evaluated against. Two safety rules are central:
    1. Labels are kept in a SEPARATE file — scenario_panel.parquet never contains the
       label column, so labels can't leak into features.
    2. A fixed seed (project.yml: primary_seed) makes the injection reproducible.
  All the transformation logic lives in tbml_common.inject_scenarios().

READS (inputs):
  - data/processed/corridor_product_year_panel.parquet — the frozen clean panel

WRITES (outputs):
  - data/processed/scenario_panel.parquet     — panel with synthetic rows transformed (NO labels)
  - data/processed/scenario_labels.parquet    — the labels + split, stored separately
  - data/processed/scenario_injections.csv    — audit of exactly what was changed and how
  - data/processed/scenario_split_manifest.json — seed, hashes, and train/val/test counts

RUN:  python src/05_build_scenarios.py
"""
from __future__ import annotations

import pandas as pd

# inject_scenarios does the work; project_config() reads the reproducibility seed from project.yml.
from tbml_common import DATA_PROCESSED, ensure_dirs, inject_scenarios, project_config, write_json


def main() -> None:
    ensure_dirs()

    # ---- Load the frozen clean panel ----
    panel = pd.read_parquet(DATA_PROCESSED / "corridor_product_year_panel.parquet")

    # ---- Inject scenarios deterministically ----
    # A fixed seed means the same rows get the same synthetic transformations every run.
    seed = int(project_config()["primary_seed"])
    # Returns: the transformed panel (no labels), the separate labels table,
    # an injection audit, and a manifest (seed/hashes/split counts).
    scenario_panel, labels, injections, manifest = inject_scenarios(panel, seed)

    # ---- Persist the four artifacts ----
    # Note labels are written to their OWN file — they are never merged into scenario_panel,
    # which is what keeps the synthetic target out of the model's feature inputs.
    scenario_panel.to_parquet(DATA_PROCESSED / "scenario_panel.parquet", index=False)
    labels.to_parquet(DATA_PROCESSED / "scenario_labels.parquet", index=False)
    injections.to_csv(DATA_PROCESSED / "scenario_injections.csv", index=False)
    write_json(DATA_PROCESSED / "scenario_split_manifest.json", manifest)

    # Console receipt: how many rows were injected, and the positive / hard-negative counts.
    print(f"scenario injections={len(injections):,}; positives={int(labels['synthetic_review_priority'].sum()):,}; hard negatives={int(labels['hard_negative'].sum()):,}")


if __name__ == "__main__":
    main()
