# Technical Companion Content Audit

## Audit identity

- Repository: `evidence-based-tbml-corridor-drift`
- Branch: `develop`
- Source commit: resolved dynamically at build time from the current `develop` HEAD
- Audit date: 23 July 2026
- Existing PDF: `docs/afc_aml_technical_companion.pdf`
- Existing editable source: `docs/afc_aml_technical_companion.md`
- Existing builder: `docs/build_brief_pdfs.py`
- Existing length: 7 A4 pages
- Revised output target: 32-38 A4 pages

The existing PDF is retained unchanged. The revised technical companion is built
separately under `reports/technical_companion/`.

## Source hierarchy used

1. Current generated outputs and processed data in `data/processed/` and
   `data/outputs/`.
2. Current pipeline code and configuration in `src/` and `configs/`.
3. Current dashboard implementation and data contracts in `dashboard/`.
4. Current profiling and model-analysis notebooks in `data-profiling/`.
5. Current validation artefacts and tests.
6. Current README and implementation notes.
7. Existing technical companion.
8. Superseded reports, prototypes, and mock-ups.

## Existing document structure

The seven-page companion currently covers:

1. Pipeline and execution order.
2. Data sources, provenance, and schema.
3. Analytical grain and canonical keys.
4. Unit values and benchmark construction.
5. Time-safe features and leakage prevention.
6. Data-quality treatment.
7. Scenario design and hard negatives.
8. Model candidates and selection.
9. Global SHAP interpretation.
10. Evidence rows and grounded-brief controls.
11. Validation framework and known limitations.
12. Technical extension roadmap.
13. A short alternative-case appendix and glossary.

This is a useful summary, but it is too compressed to function as a professional
implementation companion. It lacks the dashboard, deployment, full feature
definitions, model configurations, data profiling, current gold-coverage
analysis, reproducibility details, and implementation traceability requested by
the project.

## Reconciled current facts

| Claim | Verified current value | Source |
|---|---:|---|
| Analytical period | 2017-2024 | `configs/project.yml` |
| Official annual observations | 25,844 | `corridor_product_year_panel.parquet` |
| Model-eligible observations | 23,656 (91.53%) | panel `model_eligible` |
| Trade value represented by eligible rows | 99.9234% | panel calculation |
| Product-family rows | gold 12,205; copper 6,922; palm oil 6,717 | panel |
| Quality status | 11,894 fully usable; 11,762 usable with caveat; 2,188 excluded from modelling and retained for audit | panel |
| Rows without usable quantity | 2,188 (8.47%) | panel |
| Gold rows without usable quantity | 1,877 (15.38% of gold rows) | panel |
| Excluded gold value | USD 1,182,907,098 (0.04149% of gold value) | panel |
| Eight-year gold routes without usable quantity in any year | 14 of 702 routes present in all eight years | panel calculation |
| Value of those 14 routes | USD 1,000,119 (0.08455% of excluded gold value) | panel calculation |
| Scenario injections | 540 total; 180 per split | `scenario_split_manifest.json` |
| Positive scenarios per split | 108 | scenario labels/manifest |
| Benign hard negatives per split | 72 | scenario labels/manifest |
| Train / validation / test years | 2017-2020 / 2021-2022 / 2023-2024 | project config |
| Selected challenger | XGBoost | `model_selection.json` |
| Selected hybrid | 75% XGBoost + 25% weighted sum | model selection/candidates |
| Hybrid test precision@50 | 0.48 | `model_comparison.csv` |
| Hybrid test recall@50 | 0.2222 | model comparison |
| Hybrid test lift@50 | 26.8133 | model comparison |
| Hybrid test average precision | 0.29785 | model comparison |
| Hybrid test hard-negative false-positive rate | 0.0 | model comparison |
| Standalone XGBoost test precision@50 | 0.50 | model comparison |
| Top-50 family composition | 18 gold; 18 palm oil; 14 copper | `top_ranked_corridors.csv` |
| Evidence rows | 200 rows across 50 observations | `evidence_table.csv` |
| Evidence checks per queued observation | 4 | evidence table |
| Deterministic analyst briefs | 5, all passing validation | briefs/report |

## Outdated or inaccurate content to remove or correct

1. **Project naming.** The old title, "Evidence-Backed Trade Pattern Triage",
   does not match the current product identity, "Evidence-First TBML Triage
   System".
2. **Data-quality scoring statement.** The old document says data quality is
   never folded into review priority. The current fixed-weight score subtracts
   a data-quality reduction of up to `0.08`; this must be explained accurately.
3. **Dashboard omission.** The existing companion predates the current
   multipage stakeholder application and does not document its component,
   service, contract, caching, and session-state layers.
4. **Deployment omission.** The existing document does not describe the
   GitHub-connected Streamlit Community Cloud runtime or the split between
   `requirements.txt` and `requirements-pipeline.txt`.
5. **Gold coverage analysis.** The existing document states the overall missing
   quantity count but does not explain the current gold-specific coverage audit,
   its low value materiality, or its recurring route pattern.
6. **Feature coverage.** Several current features and edge-case conventions are
   not documented, including the unscaled MAD denominator, `0.05` MAD fallback,
   same-year peer percentile, benchmark-consistency gap, novelty, reactivation,
   and explicit missingness flags.
7. **Model detail.** Logistic preprocessing, XGBoost candidate parameters,
   Isolation Forest treatment, hybrid selection ordering, and family-level
   results are absent or too brief.
8. **Evidence boundary.** The existing SHAP section is directionally correct,
   but the revised document must distinguish global SHAP, row-level feature
   values, and deterministic evidence more explicitly.
9. **Future-state precision.** The extension roadmap is too short to distinguish
   current implementation from a bank-integrated design and an optional
   AI-assisted case-preparation concept.
10. **Reproducibility and controls.** Current dashboard contracts, runtime
    consistency checks, missing-output behaviour, and the test suite are not
    represented.

## Missing content

- Cover build identity and document control.
- Clickable contents and explicit section hierarchy.
- Full end-to-end lifecycle and deployment architecture.
- Data architecture with table grain, keys, row counts, units, producers, and
  consumers.
- Statistical profiling that motivates the feature design.
- Complete time-safe feature formulas and edge-case handling.
- Controlled scenario catalogue and label-separation control.
- Full rule formula, reductions, candidate models, model-selection chronology,
  and test interpretation.
- Official queue construction and current dashboard capture.
- Evidence construction and selected-case analytics.
- Streamlit implementation, data contracts, caching, state, and exports.
- Verified deployment path and dependency separation.
- Control matrix, reproducibility commands, limitations, and responsible
  interpretation.
- Feature, data-field, model, scenario, provenance, reproducibility, glossary,
  and traceability appendices.

## Conflicts and interpretation decisions

### Scenario counts

`scenario_labels.parquet` retains one label row for every official observation,
but only 540 rows are modified scenarios: 108 positives plus 72 hard negatives
in each of three temporal splits. The document must not describe all 25,844
label-table rows as injected scenarios.

### Validation and test selection

XGBoost is selected as the supervised challenger and the 75/25 hybrid weight is
selected on 2021-2022 validation data. Standalone XGBoost later performs
slightly better than the retained hybrid on the unopened 2023-2024 test.
Post-test reselection is intentionally avoided.

### Score semantics

Logistic and XGBoost produce classifier scores during controlled evaluation,
but the operational hybrid is used only to rank official observations. It is
not calibrated as a probability of crime or wrongdoing.

### Data quality

Missing quantity excludes a row from model scoring. Lower-but-usable data
quality can reduce the transparent weighted sum. Neither condition is itself a
suspicion signal.

### Dashboard deployment

The repository contains no active GitHub Actions deployment workflow. The
document will describe a GitHub-connected Streamlit Community Cloud deployment,
without claiming scheduled refresh, automated retraining, databases,
authentication, APIs, or monitoring services.

## Figures that can be reused

Current, repository-backed assets suitable for reuse:

- `references/project_brief/assets/dashboard_07_ranking_table.png`
- `references/project_brief/assets/dashboard_04_selected_case.png`
- `references/project_brief/assets/dashboard_05_bank_pathway.png`
- `references/project_brief/assets/dashboard_06_ai_prototype.png`
- `reports/figures/model_comparison.png` as a calculation reference only
- `reports/figures/shap_summary.png` as a calculation reference only

The queue and selected-case images are current dashboard captures. Model charts
will be regenerated from current CSV outputs to match the technical companion
style and verified values.

## Figures not to reuse

- Old technical-companion architecture and workflow figures that omit the
  dashboard and deployment layers.
- Static prototype screenshots under
  `references/tbml_streamlit_multipage_prototype/`.
- Old queue mock-ups or manually recreated queue tables.
- Legacy report charts whose labels or palette no longer match the current
  output.

## Proposed structure and page allocation

The revised document uses 38 A4 pages:

- Front matter: 4 pages.
- Core technical narrative: 26 pages.
- Appendices: 8 pages.

Core narrative:

1. Technical executive overview.
2. Scope, intended use, and boundaries.
3. End-to-end technical lifecycle.
4. Data architecture and artefact lineage.
5. Data transformations, sources, and product design.
6. Statistical profiling and gold quantity coverage.
7. Time-safe feature engineering.
8. Controlled evaluation scenarios.
9. Rules, models, hybrid selection, evaluation, and interpretation.
10. Official queue and evidence construction.
11. Streamlit implementation and deployment.
12. Validation, reproducibility, limitations, and future bank pathway.

Appendices:

A. Feature reference.
B. Data dictionary.
C. Model configuration.
D. Scenario catalogue.
E. Data sources and provenance.
F. Reproducibility and deployment.
G. Glossary.
H. Dashboard-to-implementation traceability.

## Major claim and figure sources

| Section | Primary implementation evidence |
|---|---|
| Scope and boundary | `configs/project.yml`, dashboard content, stakeholder brief |
| Architecture | `src/00-09`, `dashboard/streamlit_app.py`, dashboard services |
| Data design | panel/features/scenario/evidence schemas and `path_resolver.py` |
| Sources | source manifest, raw notes, HS and benchmark configuration |
| Profiling | current panel/features/queue plus profiling notebooks |
| Gold coverage | current panel, gold notebook, `gold_coverage.py`, tests |
| Features | `tbml_common.py`, feature explanation table, data dictionary |
| Scenarios | `tbml_common.py`, scenario config, labels, split manifest |
| Scoring and models | `06_train_evaluate_models.py`, thresholds, model artefacts |
| Evaluation | model comparison, candidates, coefficients, SHAP values |
| Queue | top-ranked CSV and current dashboard capture |
| Evidence | evidence CSV, `07_build_evidence.py`, selected-case services |
| Dashboard | page modules, components, services, tests, README |
| Deployment | requirements files, `.streamlit/config.toml`, entry point |
| Controls | source manifest, validation reports, contracts, tests |
| Future state | current bank pathway page and supporting references |

## Release QA record

- Final PDF: 38 A4 pages.
- Searchable text: present on all 38 pages.
- PDF outline: 66 bookmark entries.
- Link annotations: 144 internal links and 9 external links.
- Public links: the Streamlit application and GitHub repository both returned
  HTTP 200 on 23 July 2026.
- Render QA: all 38 HTML page equivalents passed horizontal and vertical
  overflow checks and were inspected through full-page captures and contact
  sheets.
- Test suite: 157 tests passed. The only warning was a non-analytical
  Pytest cache write restriction in the document-build sandbox.
- Visual defects corrected during QA: one over-wide lineage diagram, Markdown
  tables rendered as inline text, a nested glossary layout, and a fixed-height
  queue screenshot that cropped its edge columns.
- Statistical build assertions reconcile the headline counts, coverage,
  missing-quantity findings, queue composition, and held-out model metrics
  against the current Parquet and CSV outputs.
