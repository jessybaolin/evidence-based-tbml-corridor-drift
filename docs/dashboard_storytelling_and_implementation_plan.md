# Dashboard Storytelling and Implementation Plan

Prepared for the Evidence-First TBML Corridor Drift Lab dashboard discovery phase.

Core boundary for every dashboard page:

> This output prioritises an unusual corridor-product pattern for human review. It does not establish money laundering, misinvoicing, or criminal intent.

## 1. Executive assessment

### What the project does

The repository builds an evidence-first review-priority lab for public, official-derived annual trade observations. It uses a filtered CEPII BACI HS17 extract for 2017-2024 and three HS6 product families:

- `151110` crude palm oil
- `740311` refined copper cathodes
- `710812` non-monetary unwrought gold

The project combines official-derived trade rows, World Bank annual commodity benchmarks, time-safe feature engineering, controlled synthetic scenarios for model evaluation, a selected review-priority scoring approach, evidence rows, deterministic analyst briefs, and static reports.

The project does not prove TBML, misinvoicing, fraud, sanctions evasion, or criminal intent. Scores are review-priority ranking scores only.

### What is implemented

Implemented and verified from repository files:

- Source verification and hashing: `src/01_verify_sources.py`, `data/outputs/source_manifest.json`, `data/outputs/source_file_inventory.csv`.
- Raw-to-interim staging: `src/02_ingest_official_sources.py`, `data/interim/raw_baci_selected.parquet`, `data/interim/worldbank_commodity_benchmarks.parquet`.
- Clean panel construction: `src/03_build_panel.py`, `data/processed/corridor_product_year_panel.parquet`, `data/processed/panel.csv`, `data/processed/exclusion_audit.csv`.
- Time-safe features: `src/04_build_features.py`, `data/processed/corridor_features.parquet`, `reports/feature_explanation_table.md`.
- Synthetic scenario layer for evaluation only: `src/05_build_scenarios.py`, `data/processed/scenario_panel.parquet`, `data/processed/scenario_labels.parquet`, `data/processed/scenario_injections.csv`, `data/processed/scenario_split_manifest.json`.
- Model comparison and official scoring: `src/06_train_evaluate_models.py`, `data/outputs/model_scores.csv`, `model_comparison.csv`, `scenario_model_evaluation.csv`, `model_selection.json`, `top_ranked_corridors.csv`, `model_bundle.joblib`, figures, and SHAP summary.
- Evidence generation: `src/07_build_evidence.py`, `data/outputs/evidence_table.csv`, updated `top_ranked_corridors.csv`.
- Deterministic grounded briefs and validation: `src/08_build_briefs.py`, `reports/analyst_briefs.md`, `data/outputs/analyst_briefs.json`, `brief_validation_report.csv`, prompt assets.
- Report generation: `src/09_generate_reports.py`, `reports/final_analysis_report.md/.html/.pdf`, `reports/model_card.md/.html`, `reports/data_dictionary.md/.html`, diagrams, `data/outputs/report_manifest.json`.

### What is verified

Verified from code and outputs:

- BACI extract has 25,844 rows, years 2017-2024, and exact HS6 coverage for the three families.
- BACI `v` is treated as thousands of current USD and converted to USD by multiplying by 1,000.
- BACI `q` is treated as metric tons; 2,188 rows have missing quantity and are retained for audit but excluded from modelling.
- Gold benchmark conversion uses USD/troy ounce to USD/metric ton with factor `1_000_000 / 31.1034768`.
- Scenario labels are stored separately from `scenario_panel.parquet`; `scenario_panel` does not contain `synthetic_review_priority`, `hard_negative`, or `scenario_id`.
- Train/validation/test split is year-based: train 2017-2020, validation 2021-2022, test 2023-2024.
- The selected official scoring approach is `hybrid_score`, using XGBoost as challenger with validation-selected challenger weight `0.75`.
- The official review queue has 50 rows and does not include synthetic label or split fields.
- Evidence table has 200 rows, exactly 4 evidence rows per top-ranked observation.
- Brief validation passes for the 5 generated briefs: evidence IDs present, no unsupported numeric claims, no hallucinated sources, caveat and boundary present.

### What is incomplete

- `src/10_make_dashboard.py` exists but is zero bytes. There is no implemented dashboard.
- Expected scripts `11_run_all.py` and `99_validate_outputs.py` are not present. Not verified from the current repository.
- No dashboard-ready data layer exists. Current dashboard would need to join several analytical outputs at runtime or add a preparation script.
- The generated analyst briefs cover only the top 5 cases, and all top 5 are 2022 gold observations. This is useful but too narrow for the full interview story.
- The final report says the package includes a "static dashboard concept", but no dashboard mockup output was found. This claim is not verified from the current repository.
- The repo has a dirty git state: `.gitignore` modified and many generated files untracked at the time of discovery.

### Strongest aspects

- Clear official-data versus synthetic-evaluation separation.
- Good source provenance and hashing.
- Time-safe feature logic is explicit and documented.
- Synthetic hard negatives directly address false-positive risk.
- Model metrics are separated from official review queue outputs.
- Evidence rows and deterministic briefs make the storytelling auditable.
- The top-ranked queue is caveated and bounded as human-review prioritisation.

### Weakest aspects

- Dashboard layer is absent.
- Some generated outputs are report-ready but not dashboard-ready.
- Primary brief set is commodity-clustered around gold and Nepal/Netherlands, which may feel narrow if used alone.
- The chosen hybrid has lower test average precision than XGBoost alone, although it keeps strong ranking performance. The dashboard must explain the selection as governance-oriented blend, not "best model by every metric".
- There is no formal output validator script currently present.

### Main presentation risks

- Overclaiming that a high score means TBML or misinvoicing.
- Presenting synthetic scenario performance as real-world TBML detection.
- Treating World Bank benchmarks as invoice-level fair value.
- Letting gold dominate the story without acknowledging product-specific limitations.
- Showing SHAP as evidence rather than model-contribution explanation.

## 2. Repository map

### Git and repository state

Discovery began with `git status --short`. The tree was dirty:

- Modified: `.gitignore`.
- Untracked generated artifacts include reports, prompt assets, analyst briefs, report manifests, diagrams, and new source scripts `08_build_briefs.py`, `09_generate_reports.py`, `10_make_dashboard.py`.
- Git also warned that it could not access `C:\Users\jessl/.config/git/ignore`.

This does not block dashboard planning, but it should be cleaned before implementation work.

### Important file inventory

| Path | Purpose | Pipeline stage | Inputs | Outputs | Status | Dashboard relevance | Notes |
|---|---|---:|---|---|---|---|---|
| `requirements.txt` | Python dependencies | Environment | None | None | Current | Medium | Includes pandas, pyarrow, sklearn, xgboost, shap, matplotlib, report libraries, graphviz, ipykernel. |
| `data/outputs/environment_check.json` | Dependency version check | 00 | Installed env | JSON report | Current | Medium | Overall status pass. |
| `configs/project.yml` | Project years, seeds, splits, top-k, boundary | Config | None | None | Current | High | Defines train/validation/test years and conclusion boundary. |
| `configs/hs_families.yml` | Product family metadata | Config | None | None | Current | High | Source for product labels and commodity caveats. |
| `configs/benchmark_series.yml` | World Bank benchmark mapping | Config | None | None | Current | High | Includes gold conversion caveat. |
| `configs/thresholds.yml` | Rule scoring, model selection, evidence thresholds | Config | None | None | Current | High | Source for score component thresholds and hybrid weights. |
| `configs/scenario_catalog.yml` | Scenario definitions | Config | None | None | Current | Medium | Good appendix/methodology content. |
| `configs/typology_context.yml` | FATF-Egmont typology cards and allowed language | Config | None | None | Current | High | Used in briefs and caveats, not model features. |
| `data/raw/baci_hs17_v202601_selected_2017_2024_151110_740311_710812.parquet` | Official-derived trade extract | Raw data | CEPII BACI filtering outside repo | Raw rows | Current | High | 25,844 records, official-derived, not synthetic. |
| `data/raw/data_source_notes.json` | Provenance and expected counts | Raw metadata | Manual extraction metadata | None | Current | High | Source verification depends on it. |
| `data/raw/CMO-Historical-Data-Annual.xlsx` | World Bank annual benchmark prices | Raw data | World Bank workbook | Benchmarks | Current | High | Macro benchmark only. |
| `data/raw/*FATF*.pdf` | FATF-Egmont context PDFs | Raw context | PDF files | Typology context | Current | Medium | Readability verified; not row-level evidence. |
| `data/raw/country_codes_V202601.csv` | BACI country lookup | Raw lookup | Official code table | ISO/name mapping | Current | Medium | Supports display labels. |
| `data/raw/product_codes_HS17_V202601.csv` | HS17 product lookup | Raw lookup | Official code table | Product descriptions | Current | Medium | Supports product labels. |
| `src/tbml_common.py` | Shared constants, I/O, feature, panel, scenario helpers | Source | Configs and data | Helper outputs | Current | High | Core logic lives here. |
| `src/00_check_environment.py` | Dependency check | Source | Environment | `environment_check.json` | Current | Medium | Useful methodology page artifact. |
| `src/01_verify_sources.py` | Source hashing and verification | Source | Raw files | `source_manifest.json`, inventory CSV | Current | High | Must-have governance component source. |
| `src/02_ingest_official_sources.py` | Stage raw BACI and benchmarks | Source | Raw BACI, workbook | Interim parquet | Current | Medium | Reproducibility layer. |
| `src/03_build_panel.py` | Build clean panel and audit | Source | Interim BACI, benchmarks | Panel parquet/CSV, audit CSV | Current | High | Dashboard data landscape source. |
| `src/04_build_features.py` | Build features and feature dictionary | Source | Clean panel | Feature parquet, feature explanation table | Current | High | Case and methodology source. |
| `src/05_build_scenarios.py` | Controlled synthetic scenarios | Source | Clean panel | Scenario panel, labels, manifest, audit | Current | High for governance | Must be kept separate from official cases. |
| `src/06_train_evaluate_models.py` | Model training, scoring, evaluation, official queue | Source | Scenario features/labels, official features | Scores, comparison, queue, SHAP | Current | High | Main review queue and validation source. |
| `src/07_build_evidence.py` | Evidence rows for top official observations | Source | Features, top queue | Evidence table, updated queue | Current | High | Must-have case-investigation source. |
| `src/08_build_briefs.py` | Deterministic briefs and prompt assets | Source | Top queue, evidence, typology config | Briefs, validation, prompts | Current | High | Supports grounded analyst brief workflow. |
| `src/09_generate_reports.py` | Report and diagram generation | Source | Outputs and reports | Final report, model card, data dictionary, diagrams | Current | Medium | Good source for static documentation and diagrams. |
| `src/10_make_dashboard.py` | Placeholder dashboard script | Source | None | None | Empty | High risk | Zero bytes. Do not rely on it. |
| `data/processed/corridor_product_year_panel.parquet` | Clean official panel | Processed data | Staged BACI and benchmarks | 25,844 panel rows | Current | High | Data landscape, coverage, case history. |
| `data/processed/corridor_features.parquet` | Official feature table | Processed data | Clean panel | 25,844 feature rows | Current | High | Case investigation, scoring drivers. |
| `data/processed/scenario_panel.parquet` | Scenario-transformed panel without labels | Processed evaluation data | Clean panel | 25,844 rows | Current | Medium | Governance page only. |
| `data/processed/scenario_labels.parquet` | Synthetic labels and splits | Processed evaluation data | Scenario injection | 25,844 rows | Current | High for validation | Must not be mixed with official cases. |
| `data/processed/scenario_split_manifest.json` | Scenario split manifest and hashes | Validation metadata | Scenario injection | Manifest | Current | High | Documents label separation and split. |
| `data/outputs/model_scores.csv` | Scenario model scores | Model output | Scenario features/labels | 23,656 scored eligible scenario rows | Current | High for governance | Evaluation data only. |
| `data/outputs/model_comparison.csv` | Metrics by split, family, model | Model output | Scenario scores | 40 metric rows | Current | High | Model governance page. |
| `data/outputs/model_selection.json` | Selected scorer metadata | Model output | Validation selection | JSON selection | Current | High | Explains chosen score. |
| `data/outputs/top_ranked_corridors.csv` | Official review queue | Official output | Official features and selected scorer | Top 50 queue | Current | Must-have | No synthetic columns. |
| `data/outputs/evidence_table.csv` | Evidence rows for top queue | Evidence output | Top queue and features | 200 evidence rows | Current | Must-have | 4 rows per top case. |
| `data/outputs/analyst_briefs.json` | Structured deterministic briefs | Brief output | Evidence, queue, typology config | 5 briefs | Current | High | Covers only top 5. |
| `reports/analyst_briefs.md` | Human-facing briefs | Report | Brief JSON | Markdown briefs | Current | High | Good case narrative source. |
| `reports/final_analysis_report.md/.html/.pdf` | Final analytical report | Report | Generated outputs | Report | Current | Medium | Good reference, not dashboard source of truth. |
| `reports/model_card.md` | Model card | Report | Model outputs | Model card | Current | High for governance | Clear intended/prohibited use. |
| `reports/data_dictionary.md` | Data dictionary | Report | Static field list | Data dictionary | Current | Medium | Helpful appendix. |
| `reports/figures/*.png` | Static architecture and model figures | Figures | Graphviz/matplotlib | PNG figures | Current | Medium | Can be reused in appendix if visually acceptable. |
| `data-profiling/*.ipynb` | Scratch profiling notebooks | Notebooks | Processed/output data | Local exploration | Current/uncertain | Low to medium | Useful for analysis, not production dashboard layer. |
| `evidence_table.csv` | Convenience copy of evidence table at repo root | Duplicate output | `src/07_build_evidence.py` | CSV copy | Duplicate | Low | Prefer `data/outputs/evidence_table.csv`. |

### Missing or outdated expected files

| Expected item | Status |
|---|---|
| `README.md` | Not found. Not verified from the current repository. |
| `CLAUDE.md` | Not found at repository root. `.claude/` settings exist but are not project documentation. |
| `official_data_lab_manual.md` | Not found. Not verified from the current repository. |
| `src/11_run_all.py` | Not found. Not verified from the current repository. |
| `src/99_validate_outputs.py` | Not found. Not verified from the current repository. |
| `dashboard_mockup.html` / `dashboard_mockup.png` | Not found. Not verified from the current repository. |

## 3. Verified end-to-end architecture

### Actual pipeline map

| Stage | Purpose | Inputs | Main logic | Outputs | Validation | Business meaning | Dashboard use | Limitations |
|---|---|---|---|---|---|---|---|---|
| 00 environment | Confirm dependencies | Installed Python env | Import package list | `environment_check.json` | Status pass | Reproducibility | Methodology/control page | Does not validate data correctness. |
| 01 source verification | Confirm source integrity | Raw BACI, notes, World Bank workbook, FATF PDFs, lookups | SHA-256 hashing, row-count checks, workbook parsing, PDF readability | `source_manifest.json`, `source_file_inventory.csv` | BACI counts/year/HS6 pass; PDFs readable | Chain of custody | Provenance panel | Manual web-check statement not independently reverified here. |
| 02 ingest | Stage raw official data | Raw BACI parquet, World Bank workbook | Normalize BACI fields and benchmark units | `raw_baci_selected.parquet`, `worldbank_commodity_benchmarks.parquet` | Required columns and benchmark rows | Reproducible input handoff | Data lineage | No analytical fields yet. |
| 03 panel | Build official analytical grain | Staged BACI and benchmarks | Map countries/products, calculate trade value/unit value, join benchmark, assign quality | `corridor_product_year_panel.parquet`, `panel.csv`, `exclusion_audit.csv` | No duplicate `obs_id`; no duplicate grain | One row per year-exporter-importer-HS6 | Data landscape and case history | Annual aggregate only. |
| 04 features | Build time-safe official features | Clean panel | Prior-year history, peer percentiles, benchmark residual/drift, missingness/quality flags | `corridor_features.parquet`, feature explanation report | Time-safety documented | Converts trade rows into review signals | Case investigation and official scoring | Missing quantities block modelling for 2,188 rows. |
| 05 scenarios | Create evaluation labels only | Clean panel | Deterministic synthetic transformations and hard negatives | `scenario_panel.parquet`, `scenario_labels.parquet`, injection audit, split manifest | Label separation documented; labels not in panel | Evaluates ranking behaviour without real TBML labels | Model governance page | Synthetic labels are not crime labels. |
| 06 models | Compare scorers and rank official rows | Scenario features/labels, official features | Rule, logistic, XGBoost, Isolation Forest, hybrid; validation selection; official scoring | `model_scores.csv`, `model_comparison.csv`, `top_ranked_corridors.csv`, SHAP and figures | Test metrics generated; selected scorer recorded | Produces review queue | Review queue and governance pages | Scores are not calibrated probabilities. |
| 07 evidence | Explain top official rows | Official features, top queue | Select strongest thresholded metrics per top row | `evidence_table.csv`, updated queue counts | 4 evidence rows per top 50 | Makes ranking auditable | Case evidence cards | Evidence is still aggregate-data evidence only. |
| 08 briefs | Produce grounded analyst briefs | Queue, evidence, typology config | Deterministic brief rendering and validation | Brief JSON/MD, prompt assets, validation report | 5 briefs pass validation | Shows human-review workflow | Case page and appendix | Only top 5 briefed; all are gold. |
| 09 reports | Generate static reports | Outputs and figures | Markdown/HTML/PDF rendering and diagrams | Final report, model card, data dictionary | Report hashes in manifest | Stakeholder documentation | Appendix/methodology | Reports are not interactive. |
| 10 dashboard | Placeholder | None | None | None | None | Not implemented | Future work | Empty file. |

### Claim verification

| Claim | Code evidence | Output evidence | Classification |
|---|---|---|---|
| Source data is official-derived, not synthetic | `src/01_verify_sources.py`, `source_notes_check` in `tbml_common.py` | `source_manifest.json` says `not_synthetic: true` | Verified |
| BACI covers 2017-2024 and exactly three HS6 codes | `EXPECTED_YEARS`, `EXPECTED_HS6` in `tbml_common.py` | `source_manifest.json`, panel counts | Verified |
| `v` is thousands of USD and multiplied by 1,000 | `build_panel` in `tbml_common.py`; data dictionary | Panel fields `trade_value_usd` | Verified |
| Gold benchmark is converted to USD/metric ton | `extract_worldbank_benchmarks` in `tbml_common.py` | `source_manifest.json`, benchmark parquet | Verified |
| Features are time-safe | `build_features` uses shifted/prior-year logic and same-year peers | `feature_explanation_table.md` | Verified from code and docs |
| Scenario labels are separated from features | `src/05_build_scenarios.py` writes labels separately | `scenario_panel` has no label columns; manifest states separation | Verified |
| Train/validation/test split is time-based | `split_for_year` in `tbml_common.py`, project config | `scenario_split_manifest.json` | Verified |
| Hybrid selected on validation | `src/06_train_evaluate_models.py` | `model_selection.json` | Verified |
| XGBoost is selected challenger | `src/06_train_evaluate_models.py` | `model_selection.json` | Verified |
| Official review queue excludes synthetic rows | `src/06_train_evaluate_models.py` scores `corridor_features.parquet` | `top_ranked_corridors.csv` has no synthetic columns | Verified |
| SHAP is model contribution only | `src/06_train_evaluate_models.py`, `model_card.md` | `shap_summary_values.csv`, `shap_summary.png` | Verified |
| Evidence supports every top case | `src/07_build_evidence.py` | 200 evidence rows for 50 top rows | Verified |
| Analyst briefs are grounded and validated | `src/08_build_briefs.py` | `brief_validation_report.csv` all pass for top 5 | Verified for top 5 only |
| Dashboard exists | `src/10_make_dashboard.py` | No dashboard artifact found | Contradicted / not verified |
| Full production validation script exists | None found | None found | Not verified from current repository |

### Lineage trace: top official observation

Candidate: `obs_c1178b54e91326a9b0f5`, rank 1, 2022 ESP to NLD, HS6 `710812`, non-monetary unwrought gold.

| Lineage step | File | Join keys / identifiers | Evidence from repository |
|---|---|---|---|
| Raw source row | `data/raw/baci_hs17_v202601_selected_2017_2024_151110_740311_710812.parquet` | `t`, `k`, `i`, `j`, `v`, `q` | Source row ID stored downstream as `source_row_id`. |
| Clean panel | `data/processed/corridor_product_year_panel.parquet` | `obs_id`, `source_row_id`, `year`, `exporter_code`, `importer_code`, `hs6` | Adds ISO3s, product name, benchmark, quality fields. |
| Feature row | `data/processed/corridor_features.parquet` | `obs_id` | Adds benchmark residual, prior history, unit-value change, quality flags. |
| Official score | `data/outputs/top_ranked_corridors.csv` | `obs_id` | Rank 1, selected score `0.989129`, rule score `1.0`, selected challenger score `0.985506`. |
| Evidence rows | `data/outputs/evidence_table.csv` | `obs_id`, `evidence_id` | 4 evidence rows: history deviation, benchmark-adjusted drift, benchmark gap, annual unit-value change. |
| Analyst brief | `reports/analyst_briefs.md`, `data/outputs/analyst_briefs.json` | `obs_id`, `evidence_id` | Brief 1 includes evidence IDs and boundary statement. |
| Proposed dashboard | Dashboard-ready case bundle | `obs_id` as persistent selected-case state | Show case header, history, score drivers, evidence cards, caveats, recommended next steps. |

History for the selected case shows the value/quantity/unit-value trajectory from 2017-2024. In 2022, unit value rises to about USD 368.4m per metric ton versus a World Bank gold benchmark of about USD 57.9m per metric ton, with log benchmark residual `1.850496`, robust historical z `18.826742`, and unit-value year-over-year log change `1.858804`. This supports review priority, not a conclusion about invoice accuracy or intent.

## 4. Business problem and value proposition

TBML is difficult because trade activity is complex, cross-border, document-heavy, and often explainable by legitimate commercial factors. Wholesale banks see customers, payments, trade-finance instruments, counterparties, and documentation, but analysts still need prioritisation because the possible review universe can be large.

This project demonstrates an external public-data lens:

- It starts with official-derived aggregate trade flows.
- It identifies corridor-product-year patterns that are unusual relative to history, peers, and broad commodity benchmarks.
- It ranks rows for human review.
- It attaches evidence and caveats so an analyst can decide what to check next.

The banking value is not automated detection. The value is better triage discipline:

- Prioritise limited analyst attention.
- Explain why an observation ranked highly.
- Separate ranking signals from evidence and caveats.
- Avoid confusing data-quality weakness with suspicion.
- Support a human-in-the-loop review workflow.
- Show how public-data signals could complement private bank data.

The dashboard should help a UOB wholesale-banking director answer:

- Which observations deserve review first?
- Why did an observation rank highly?
- Is the pattern unusual relative to history, peers, and broad commodity prices?
- What benign explanations remain?
- What private bank records would be needed next?
- Did the modelling approach improve the review queue over simple baselines?
- How were false positives and governance handled?
- What does this project prove, and what does it not prove?

## 5. Technical narrative

The technical story should be rigorous but not code-first.

| Concept | Business explanation | Technical explanation | Dashboard wording | Tooltip | Caveat |
|---|---|---|---|---|---|
| Official source provenance | The analysis starts from traceable public data. | Input files are hashed and checked against expected years, HS6 codes, and row counts. | Source-verified official-derived trade extract | The project checks file hashes, row counts, years, product codes, and benchmark files before analysis. | Official-derived does not mean complete investigative evidence. |
| Analytical grain | Each row is one annual corridor-product observation. | Grain is year, exporter, importer, HS6. | One row per exporter-importer-product-year | A row is an annual aggregate, not an invoice or shipment. | Cannot identify customer, invoice, shipment, or payment. |
| Unit value | Converts value and quantity into an aggregate implied price. | `trade_value_usd / quantity_metric_ton`. | Aggregate unit value | BACI value is thousands of USD; quantity is metric tons. | Not invoice price or contract fair value. |
| Benchmark residual | Compares aggregate unit value to broad commodity context. | `log_unit_value - log(benchmark_price_usd_per_metric_ton)`. | Gap to broad commodity benchmark | World Bank prices give broad annual context. | Benchmark is not invoice-level fair value. |
| Time-safe history | Compare the current row to prior corridor behavior. | Shifted prior-year median/MAD and previous-observation changes. | Compared with prior corridor history | Uses prior years only; no future rows. | Short history can make metrics unstable. |
| Same-year peer percentile | Compare to other corridors in the same product/year. | Percentile of benchmark residual by family/year. | Same-product peer position | Shows where the row sits among contemporaneous peers. | Peer group still aggregates heterogeneous commercial terms. |
| Synthetic scenarios | Test ranking behaviour without real TBML labels. | Controlled transformations and hard negatives stored separately. | Controlled evaluation scenarios | Public BACI has no confirmed TBML labels, so scenarios evaluate behaviour only. | Not proof of real-world TBML detection. |
| Hybrid score | Blend transparent rules and selected ML challenger. | Hybrid = `(1-w)*rule + w*xgboost`, `w=0.75`. | Review-priority ranking score | Selected using validation split only. | Not calibrated probability. |
| SHAP | Explain model contribution patterns. | Mean absolute SHAP for XGBoost features. | Model contribution summary | Shows which features influenced model output. | Not evidence or causal proof. |
| Evidence rows | Convert score drivers into recomputable facts. | Top metrics selected per case with threshold, severity, caveat. | Evidence cards | Every evidence card cites source field, value, threshold, and caveat. | Aggregate-data evidence only. |
| Analyst brief | Package evidence into bounded review memo. | Deterministic renderer with validation. | Grounded analyst brief | Uses only structured evidence and typology cards. | Current briefs are deterministic, not a live LLM call. |

## 6. Data-profile findings

### Core datasets

| Dataset | Shape | Dashboard role |
|---|---:|---|
| `data/processed/corridor_product_year_panel.parquet` | 25,844 x 50 | Coverage, quality, history, case context. |
| `data/processed/corridor_features.parquet` | 25,844 x 44 | Official features and case investigation. |
| `data/processed/scenario_panel.parquet` | 25,844 x 50 | Evaluation-only transformed panel without labels. |
| `data/processed/scenario_labels.parquet` | 25,844 x 8 | Evaluation labels and splits only. |
| `data/processed/scenario_features.parquet` | 25,844 x 44 | Scenario feature table for model evaluation. |
| `data/outputs/model_scores.csv` | 23,656 x 29 | Scenario model scores for governance page. |
| `data/outputs/model_comparison.csv` | 40 x 12 | Validation/test metrics by split/family/model. |
| `data/outputs/top_ranked_corridors.csv` | 50 x 21 | Official review queue. |
| `data/outputs/evidence_table.csv` | 200 x 16 | Evidence cards for top official cases. |
| `data/outputs/analyst_briefs.json` | 5 briefs | Grounded brief workflow for top 5 only. |
| `data/outputs/shap_summary_values.csv` | 15 x 2 | Model contribution appendix/governance. |

### Coverage and quality

- Panel rows: 25,844.
- Years: 2017: 2,783; 2018: 3,094; 2019: 3,279; 2020: 3,162; 2021: 3,358; 2022: 3,510; 2023: 3,445; 2024: 3,213.
- Families: crude palm oil 6,717; gold 12,205; copper 6,922.
- Exporter ISO3 count: 202. Importer ISO3 count: 213. Corridor count: 4,952.
- No duplicate `obs_id`. No duplicate year/exporter/importer/HS6 grain.
- Quality status: fully usable 11,894; usable with caveat 11,762; excluded from modelling retained for audit 2,188.
- Missing quantity: 2,188 rows. By family: gold 1,877, copper 224, palm oil 87.
- Benchmark coverage: no missing benchmark values in panel.

Gold has the most material quality caveat: 1,877 missing-quantity rows and many high-ranked small-quantity observations. The dashboard should make this visible, not hide it.

### Feature profile

- Model-eligible rows: 23,656. Non-eligible rows: 2,188.
- `robust_historical_z` has 8,840 missing values, mainly due to lack of sufficient prior history or missing unit value.
- `benchmark_adjusted_drift`, `unit_value_yoy_change`, and `value_quantity_divergence` each have 9,091 missing values.
- `same_family_year_peer_percentile` has 2,188 missing values, matching missing quantity/unit value exclusions.
- Data-quality score distribution: 3: 1,592; 4: 14,227; 5: 5,337; 6: 4,688.

### Scenario/evaluation profile

- `scenario_panel.parquet` has no label columns.
- `scenario_labels.parquet` has 25,844 rows and no duplicate `obs_id/year/family_id` keys.
- Split rows: train 12,318; validation 6,868; test 6,658.
- Synthetic positives: 108 in each split.
- Hard negatives: 72 in each split.
- Scenario IDs: five scenario types, 108 rows each; remaining 25,304 rows have no scenario ID.

### Model validation findings

Test split, all families, top-k 50:

| Model | Precision@50 | Recall@50 | Lift@50 | Average precision | Hard-negative FPR |
|---|---:|---:|---:|---:|---:|
| XGBoost | 0.50 | 0.231 | 27.93 | 0.306 | 0.000 |
| Hybrid | 0.48 | 0.222 | 26.81 | 0.298 | 0.000 |
| Rule | 0.14 | 0.065 | 7.82 | 0.100 | 0.000 |
| Logistic | 0.06 | 0.028 | 3.35 | 0.077 | 0.000 |
| Isolation | 0.06 | 0.028 | 3.35 | 0.050 | 0.000 |

Validation split, all families:

- XGBoost has highest validation average precision (`0.386`) and precision@50 (`0.62`), with hard-negative FPR `0.0`.
- Hybrid has validation precision@50 `0.46`, average precision `0.309`, hard-negative FPR `0.0139`.
- The selected hybrid is still strong on test, but the dashboard should not imply it dominates XGBoost on every metric.

### Official review queue findings

- Top queue rows: 50.
- Top families: gold 18, palm oil 18, copper 14.
- Top years: 2018: 6; 2019: 7; 2020: 6; 2021: 4; 2022: 16; 2023: 5; 2024: 6.
- Top quality: 45 usable with caveat, 5 fully usable.
- Scores range from `0.954222` to `0.989129`.
- Top queue contains no synthetic columns.
- Every top row has 4 evidence rows.

### Evidence findings

Evidence rows by type:

- `history_deviation`: 47
- `annual_unit_value_change`: 46
- `benchmark_adjusted_drift`: 45
- `benchmark_gap`: 33
- `value_quantity_divergence`: 29

Severity:

- High: 152
- Medium: 48

The evidence layer is strong enough for case cards, but it currently covers only the top 50 official observations.

### Brief findings

Five briefs were generated, all passed validation, and all include the conclusion boundary. However, all five are gold cases from 2022. For an interview dashboard, use the top brief as the primary case, but also surface a product-diverse official review queue and include non-gold alternatives.

## 7. Ranked storytelling candidates

Scoring scale: 1 low, 5 high. "Risk" is reverse-scored, where 5 means low risk of misleading.

| Story or insight | Supporting evidence | Business relevance | Technical value | Visual potential | Risk score | Total | Placement | Priority |
|---|---|---:|---:|---:|---:|---:|---|---|
| Evidence-first public-data review queue for official observations | `top_ranked_corridors.csv`, `evidence_table.csv` | 5 | 5 | 5 | 4 | 19 | Main story | Must show |
| Clear boundary: ranking signal, not crime probability | `project.yml`, `model_card.md`, reports | 5 | 4 | 3 | 5 | 17 | Every page | Must show |
| Top official case has recomputable evidence and grounded brief | `top_ranked_corridors.csv`, `evidence_table.csv`, `analyst_briefs.md` | 5 | 5 | 5 | 4 | 19 | Main story | Must show |
| Synthetic evaluation separated from official review queue | `scenario_split_manifest.json`, `scenario_panel`, `scenario_labels` | 5 | 5 | 4 | 5 | 19 | Governance page | Must show |
| XGBoost/hybrid improves scenario ranking over rule/logistic/isolation | `model_comparison.csv` | 4 | 5 | 4 | 4 | 17 | Governance page | Should show |
| Hard-negative false-positive guardrail | `model_comparison.csv`, `scenario_catalog.yml` | 5 | 5 | 4 | 4 | 18 | Governance page | Must show |
| Source provenance and hash chain | `source_manifest.json`, `source_file_inventory.csv` | 4 | 5 | 3 | 5 | 17 | Methodology | Should show |
| Data-quality distribution and missing quantities, especially gold | `corridor_product_year_panel.parquet`, `corridor_features.parquet` | 5 | 4 | 5 | 5 | 19 | Data quality page | Must show |
| Time-safe feature construction | `src/04_build_features.py`, `feature_explanation_table.md` | 4 | 5 | 4 | 5 | 18 | Methodology | Should show |
| SHAP contribution summary | `shap_summary_values.csv`, `shap_summary.png` | 3 | 4 | 3 | 3 | 13 | Appendix/governance | Optional |
| FATF-Egmont typology cards | `typology_context.yml`, briefs | 3 | 3 | 3 | 4 | 13 | Case caveat/appendix | Optional |
| Full country map of flows | Panel data | 2 | 2 | 4 | 2 | 10 | Exclude | Exclude |
| Raw feature table dump | `corridor_features.parquet` | 2 | 3 | 1 | 2 | 8 | Exclude | Exclude |
| Live LLM brief generation | Prompt assets only | 3 | 3 | 3 | 2 | 11 | Future only | Exclude from current claims |

## 8. Mandatory storytelling recommendation

### Primary recommended narrative

**Central message:** The project shows how a bank can turn public aggregate trade data into a bounded, evidence-first review-priority workflow: source-verified inputs, time-safe signals, scenario-tested ranking, official-observation review queue, evidence cards, and grounded analyst briefs.

**Opening problem:** Wholesale trade review is hard because cross-border trade patterns can be unusual for many legitimate reasons, but analysts still need a defensible way to prioritise limited review capacity.

**Core findings to show:**

1. The project starts with verified official-derived data: 25,844 annual corridor-product rows across 2017-2024 and three commodity families.
2. Data quality is explicitly separated from review priority: 2,188 rows are excluded from modelling due to missing quantities, and gold has the strongest missing-quantity caveat.
3. The official review queue is synthetic-free and product-diverse in the top 50: gold 18, palm oil 18, copper 14.
4. A selected case is explainable through recomputable evidence: history deviation, benchmark gap/drift, and annual unit-value movement.
5. Model validation is honest: synthetic scenarios test ranking behaviour, hard negatives test false-positive sensitivity, and scores are not probabilities.

**Primary official-observation case study:** Rank 1, `obs_c1178b54e91326a9b0f5`, 2022 ESP to NLD, HS6 `710812`, non-monetary unwrought gold.

Why this case:

- Highest selected review-priority score: `0.989129`.
- Has 8-year corridor history in the panel.
- Has 4 evidence rows and a validated analyst brief.
- Evidence includes robust historical z `18.827`, benchmark residual `1.850`, benchmark-adjusted drift `1.858`, and unit-value change `1.859`.
- It is strong enough to explain the workflow, while its gold/small-quantity caveats force responsible interpretation.

**Order of presentation:**

1. Business problem and boundary.
2. Source coverage and data-quality reality.
3. Evidence-first pipeline.
4. Official review queue.
5. Primary case drill-down.
6. Model validation and hard-negative guardrail.
7. Grounded brief and next-review steps.
8. Limitations and bank-extension roadmap.

**Technical decisions worth highlighting:**

- Source hash manifest.
- Unit normalization including gold conversion.
- One row per annual corridor-product grain.
- Time-safe historical features.
- Scenario labels stored separately from scenario features.
- Validation/test split by year.
- Baseline versus challenger model comparison.
- Hard-negative testing.
- Evidence rows before analyst brief text.
- Deterministic brief validation.

**Analyses to exclude from main presentation:**

- Raw SHAP feature table except as a short governance appendix.
- Full raw feature dumps.
- Maps without a precise analytical question.
- Live GenAI claims. Current brief generation is deterministic.
- Any display that implies case criminality, invoice-level mispricing, or customer risk.

**Main takeaway:** The director should remember that this is a responsible triage design: public data cannot conclude TBML, but it can create a disciplined, explainable review queue that tells analysts what to examine next.

### Page transitions

1. From problem to scope: "Before looking at cases, I want to show exactly what data the analysis is and is not using."
2. From scope to pipeline: "Once the data boundary is clear, the next question is how an annual trade row becomes a review-priority signal."
3. From pipeline to queue: "That evidence-first pipeline produces a queue of official observations, not synthetic examples."
4. From queue to case: "A ranking is only useful if an analyst can understand why a row rose to the top."
5. From case to evidence: "The case is not a conclusion; it is a bundle of facts, caveats, and next questions."
6. From evidence to validation: "The remaining question is whether the ranking method behaves better than simpler baselines under controlled evaluation."
7. From validation to roadmap: "Finally, the right operational question is how this public-data lens would complement private bank controls."

**Closing statement:** "This dashboard does not automate a TBML decision; it demonstrates a governed review-priority workflow that is source-traceable, evidence-first, and clear about what human investigators must verify next."

### Questions the narrative is designed to answer

- What does a high score mean?
- Why should a director trust the queue?
- What evidence supports a high-ranked case?
- How are false positives considered?
- What can public data add to a bank?
- What cannot be concluded without private records?

### Why this narrative is stronger than alternatives

It balances business judgement and technical credibility. A purely business-first story risks underplaying modelling discipline. A purely technical story risks overwhelming the director and losing the AFC workflow value. The recommended narrative uses one case to make the workflow concrete, then uses governance evidence to build trust.

### Alternative A: Business-first narrative

Focus:

- AFC review problem.
- Analyst workload and prioritisation.
- Official queue.
- Case evidence.
- Human-review next steps.
- Banking extension.

Strength: clearest for a director. Weakness: may underuse the repo's model validation strengths.

### Alternative B: Technical-first narrative

Focus:

- Source provenance.
- Feature engineering.
- Scenario injection.
- Model validation.
- SHAP.
- Evidence generation.
- Brief validation.

Strength: demonstrates technical rigour. Weakness: can feel like a code walkthrough rather than a stakeholder dashboard.

### Narrative comparison

| Criterion | Primary recommendation | Business-first alternative | Technical-first alternative |
|---|---:|---:|---:|
| Fit for UOB director | 5 | 5 | 3 |
| Clarity | 5 | 5 | 3 |
| Business relevance | 5 | 5 | 3 |
| Technical credibility | 5 | 3 | 5 |
| Interview memorability | 5 | 4 | 3 |
| Risk of becoming too technical | 4 | 5 | 2 |
| Responsible-AI communication | 5 | 4 | 5 |
| Overall recommendation | 5 | 4 | 3 |

## 9. Recommended case studies

### Primary case

Rank 1: `obs_c1178b54e91326a9b0f5`, 2022 ESP to NLD, gold.

Use because it has the highest rank, full evidence, a validated brief, and a rich history. It is also useful for teaching caveats: annual aggregate data, tiny quantity, gold purity/form unknown, and benchmark not invoice fair value.

### Alternative case

Rank 8: `obs_7c72b96c0b2d861bdbbc`, 2022 CAF to CHE, gold.

Use because it is the highest-ranked fully usable case. Score `0.978825`, 4 evidence rows, quality status fully usable. It avoids making the primary case depend on a `usable_with_caveat` status.

### Product-diverse appendix cases

- Rank 6: `obs_c88105f77b1bef6f7d3d`, 2022 ITA to MKD, crude palm oil. Score `0.980196`, 4 evidence rows, but usable with caveat.
- Rank 7: `obs_1a481444e8f53a79dfee`, 2024 GBR to ITA, refined copper cathodes. Score `0.980173`, 4 evidence rows, but usable with caveat.
- Rank 9: `obs_e4204c85264cb9a8ffe2`, 2018 USA to IRL, refined copper cathodes. Score `0.978747`, 4 evidence rows, usable with caveat.

Recommendation: Use rank 1 as the main walkthrough, but show a queue/table that makes product diversity visible. Keep rank 8 as the backup if challenged on caveated quality status.

## 10. Dashboard story arc

| Step | Stakeholder question | Key takeaway | Dashboard page | Visual/component | Supporting dataset | Business message | Technical message | Caveat | Presentation guidance | Transition |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | What problem are you solving? | Public data can help prioritise review but cannot conclude crime. | Executive overview | Boundary banner, project purpose, scope cards | `project.yml`, `source_manifest.json` | This supports triage. | Scope is bounded. | No customer/invoice data. | Start with human-review boundary. | "Now I will show what data sits behind this." |
| 2 | What data do you have? | 25,844 official-derived rows across 3 commodities and 8 years. | Data landscape | Year/family coverage, quality status | Panel parquet | Scope is clear. | Source verification and panel grain. | Annual aggregate only. | Mention gold quantity issue early. | "From this data, the pipeline builds review signals." |
| 3 | How does a row become a signal? | Signals compare history, peers, and benchmarks without future leakage. | Methodology summary | Pipeline diagram, signal cards | Features, feature table | Signals are explainable. | Time-safe features. | Benchmark is macro context. | Avoid formulas first. | "These signals feed a queue of official observations." |
| 4 | Which rows should be reviewed first? | The review queue is official-only and evidence-linked. | Official queue | Ranked table, filters, selected row state | Top queue, evidence counts | Prioritises analyst attention. | Scores are reproducible. | Score is not probability. | Sort by selected score. | "Let's open the top case." |
| 5 | Why did this case rank highly? | Four recomputable evidence rows explain the ranking. | Case investigation | Case header, history line, evidence cards | Features, evidence | Analysts can see why. | Evidence rows source values and thresholds. | Not invoice proof. | Walk through one metric at a time. | "Evidence also tells us what remains unknown." |
| 6 | What should an analyst do next? | The brief turns evidence into caveated next steps. | Case investigation | Analyst brief panel | Brief JSON/MD | Human review workflow. | Deterministic grounded rendering. | Current briefs only top 5. | Emphasise missing private records. | "Now I will show how the ranking method was tested." |
| 7 | Is the model credible? | XGBoost/hybrid outperform simple baselines on synthetic evaluation. | Model validation | Metric table/bar charts | Model comparison | Better triage than simple rules. | Validation/test split and hard negatives. | Synthetic labels only. | Separate official cases from scenario evaluation. | "That completes the current build; next is operational extension." |
| 8 | How could a bank use this? | Public signals complement private bank data and case systems. | Extension roadmap | Future data map | Plan only | Shows operational thinking. | Data contract architecture. | Future state, not implemented. | Avoid implying UOB data access. | "The final takeaway is responsible prioritisation." |

## 11. Page-by-page dashboard blueprint

### Page 1: Executive overview

Purpose: Establish the business problem, project scope, and conclusion boundary.

What the director should understand: This is a review-priority and evidence workflow, not a crime-detection claim.

Components:

- Boundary banner.
- Scope cards: years 2017-2024, 25,844 panel rows, 3 HS6 families, top-k 50.
- Simplified pipeline: source verification to queue to evidence to brief.
- Small top-5 queue preview.
- One-sentence value proposition.

Default caveat: "Scores are ranking signals for human review, not probabilities."

### Page 2: Data landscape and quality

Purpose: Show analytical coverage and quality constraints before any case review.

What the director should understand: The project is honest about data quality, especially quantity missingness and gold caveats.

Components:

- Rows by year.
- Rows by family.
- Quality status distribution.
- Missing quantity by family.
- Country/corridor coverage cards.
- Benchmark coverage card.

Important caveat: Missing quantity blocks unit-value-based modelling; gold has 1,877 missing-quantity rows.

### Page 3: Official review queue

Purpose: Present official observations ranked for review.

What the director should understand: The queue contains official observations only; synthetic scenarios do not appear here.

Components:

- Ranked table with filters.
- Score type label: "Selected review-priority score".
- Columns: rank, year, exporter, importer, HS6/product, family, score, quality status, evidence count.
- Click row to select case.
- Product/year/quality filters.
- Search by `obs_id`, exporter, importer.

Caveat: "A high rank means the row has unusual analytical signals; it is not a finding of wrongdoing."

### Page 4: Case investigation

Purpose: Make a selected case explainable and caveated.

What the director should understand: A case is reviewed through facts, evidence, caveats, and missing information.

Components:

- Case header and selected score.
- Historical line chart: trade value, quantity, unit value, benchmark.
- Signal cards: history deviation, benchmark residual, benchmark-adjusted drift, unit-value change, value-quantity divergence, peer percentile.
- Evidence cards from `evidence_table.csv`.
- Data-quality and caveat panel.
- Analyst brief panel if available.
- Recommended next review steps.

Caveat: "Aggregate unit value is not invoice price."

### Page 5: Model validation and governance

Purpose: Demonstrate that model choice was evaluated responsibly.

What the director should understand: Evaluation uses synthetic scenarios only because real TBML labels are unavailable.

Components:

- Split timeline: train 2017-2020, validation 2021-2022, test 2023-2024.
- Model comparison table and bars.
- Hard-negative false-positive chart.
- Selected model card.
- Scenario explanation panel.
- Optional SHAP contribution summary.

Caveat: "Scenario performance tests model behaviour; it does not prove real-world TBML detection."

### Page 6: Methodology and controls

Purpose: Provide progressive technical disclosure for interview follow-up.

What the director should understand: The pipeline is auditable and reproducible.

Components:

- Source manifest and hashes.
- Data lineage table.
- Feature explanation accordion.
- Label separation statement.
- Evidence-generation rules.
- Brief-validation checks.
- Limitations.

Caveat: "FATF-Egmont materials are typology context, not labels or row-level evidence."

### Page 7: Banking extension roadmap

Purpose: Show how the concept could be operationalised with private bank data.

What the director should understand: Public-data prioritisation could complement, not replace, internal controls.

Components:

- Future data sources: customer profile, invoices, trade-finance instruments, payments, shipping documents, beneficial ownership, sanctions/adverse media, case outcomes.
- Proposed human workflow: review queue to analyst case pack to feedback loop.
- Governance controls: calibration, thresholds, review outcomes, audit trail, model monitoring.

Caveat: Clearly label all future inputs as not currently present in the repository.

## 12. Component-to-data matrix

| Page | Component | Stakeholder question | Source file | Source fields | Transformation | Visual type | Interaction | Default view | Tooltip | Caveat | Empty state | Validation rule | Priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Overview | Boundary banner | What can this conclude? | `configs/project.yml` | `conclusion_boundary` | None | Banner | None | Always visible | Exact project boundary | Applies to all pages | Do not render dashboard without boundary | Boundary text present | Must-have |
| Overview | Scope cards | What data is covered? | `source_manifest.json`, panel | years, row count, HS6 counts | Aggregate counts | KPI cards | None | 2017-2024, 25,844, 3 families | Official-derived BACI extract | Public aggregate only | Show "not available" | Counts match manifest | Must-have |
| Data quality | Rows by year | How much coverage exists? | Panel parquet | `year`, `obs_id` | Count rows by year | Bar chart | Year filter | All years | Annual panel row count | Not transaction count | Empty chart with message | No duplicate `obs_id` | Must-have |
| Data quality | Family distribution | Which commodities dominate? | Panel parquet | `family_id`, `hs6`, `product_name` | Count rows | Bar chart | Family filter | All families | Product family row count | Product scope is intentionally narrow | Empty chart | Family in config | Must-have |
| Data quality | Quantity missingness | Where is analysis constrained? | Panel parquet | `family_id`, `quantity_metric_ton`, `quality_status` | Missing count/rate | Bar chart | Family filter | By family | Missing quantity blocks unit-value metrics | Gold has material caveat | Show zero if none | Missingness calculated | Must-have |
| Queue | Ranked review table | What should be reviewed first? | `top_ranked_corridors.csv` | `rank`, `obs_id`, `year`, `exporter_iso3`, `importer_iso3`, `hs6`, `product_name`, `selected_review_priority_score`, `quality_status`, `key_evidence_count` | Sort by rank | Table | Filter/search/click | Top 50 | Review-priority ranking score | Not probability | No rows after filters | No synthetic columns allowed | Must-have |
| Queue | Score distribution | How concentrated are scores? | Top queue or official scores if prepared | `selected_review_priority_score` | Histogram | Distribution | Filter | Top 50 | Distribution of selected ranking scores | Scores not calibrated probabilities | Show empty | Numeric scores 0-1 | Should-have |
| Case | Case header | What row is selected? | Top queue | identity fields, score, quality | None | Header/card | Selected case state | Rank 1 | Case identity and score | Official observation only | Prompt to select row | `obs_id` exists in queue | Must-have |
| Case | Historical trend | How did the corridor change over time? | `corridor_features.parquet` | `year`, `exporter_iso3`, `importer_iso3`, `hs6`, `trade_value_usd`, `quantity_metric_ton`, `unit_value_usd_per_metric_ton`, `benchmark_price_usd_per_metric_ton` | Filter same exporter/importer/HS6 | Line chart | Hover/select metric | Selected case history | Annual aggregate trend | Not invoice/shipment trend | "No prior history" | At least selected row present | Must-have |
| Case | Evidence cards | Which facts support review? | `evidence_table.csv` | `evidence_id`, `metric_name`, `observed_value`, `threshold`, `severity`, `plain_english_summary`, `caveat` | Filter by `obs_id` | Cards | Expand detail | Selected case evidence | Recomputable evidence row | Evidence is aggregate-data evidence | "No evidence generated" | Evidence IDs unique | Must-have |
| Case | Analyst brief | What should analyst do next? | `analyst_briefs.json` or MD | headline, why, evidence IDs, missing info, steps, boundary | Filter by `obs_id` | Text panel | Copy/download | Brief if available | Deterministic grounded brief | Top 5 only currently | "Brief not generated for this case" | Evidence IDs exist | Should-have |
| Governance | Split timeline | How was evaluation separated over time? | `scenario_split_manifest.json` | train/validation/test years, counts | None | Timeline | None | All splits | Time-based evaluation split | Synthetic labels only | Show unavailable | Manifest present | Must-have |
| Governance | Model metrics | Did model improve ranking? | `model_comparison.csv` | split, family, model, precision, recall, lift, AP, hard-negative FPR | Filter split/family | Table/bar | Split/family selectors | Test/all families | Top-k metrics on controlled scenarios | Not real TBML labels | Empty message | Required columns present | Must-have |
| Governance | SHAP summary | What influenced challenger scores? | `shap_summary_values.csv` | `feature_name`, `mean_abs_shap` | Sort descending | Bar chart | Hover | Top 10 features | Model contribution magnitude | Not source evidence | Hide if missing | File present | Optional |
| Methodology | Source manifest | Are sources traceable? | `source_manifest.json` | source inventory, hashes, checks | None | Table | Expand | Key files | SHA-256 file inventory | Does not certify all external truth | Show missing | Hashes non-empty | Should-have |
| Methodology | Feature dictionary | What do features mean? | `reports/feature_explanation_table.md` or config | feature name, derivation, caveat | None | Accordion/table | Expand | Plain-English first | Feature derivation and time-safety | Technical details in appendix | Show missing | Table exists | Should-have |
| Roadmap | Future bank data | How would this extend inside a bank? | Plan text | N/A | None | Diagram/list | None | Future-state labels | Possible private data complements | Not implemented | Always show as future | Explicit future label | Should-have |

## 13. Technology recommendation

### Framework comparison

| Criterion | Streamlit | Plotly Dash | Python backend plus separate frontend |
|---|---:|---:|---:|
| Fit with current Python repo | 5 | 4 | 3 |
| Development effort | 5 | 3 | 1 |
| Interactivity | 4 | 5 | 5 |
| Visual polish | 4 | 4 | 5 |
| State management | 3 | 4 | 5 |
| Maintainability | 4 | 4 | 3 |
| Testing | 3 | 4 | 4 |
| Deployment simplicity | 5 | 4 | 2 |
| Interview reliability | 5 | 4 | 3 |
| Risk of overengineering | 5 | 4 | 1 |
| Case-investigation workflow | 4 | 5 | 5 |
| Offline fallback | 4 | 4 | 3 |

Recommended framework: **Streamlit with Plotly charts**.

Reason: The repository is Python-first, the dashboard is for an interview demonstration, and the main need is a polished read-only analytical app rather than a production case-management system. Streamlit can load parquet/CSV outputs directly, cache data, maintain selected-case state, and support a case drill-down with relatively low implementation risk.

Dash is a strong alternative if more precise multi-page state and table interactions are required. A separate frontend is not justified for the MVP and would risk overengineering.

Recommended local run command after implementation:

```text
streamlit run dashboard/app.py
```

Recommended charting:

- Plotly Express / Plotly Graph Objects for charts.
- Streamlit native tables or `st.dataframe` for initial MVP; consider AgGrid only if needed.

Offline fallback:

- Export a static HTML/PDF walkthrough from key dashboard screenshots and the final report.
- Keep `reports/final_analysis_report.pdf` as fallback if the app fails during interview.

## 14. Dashboard data architecture

Do not make the analytical pipeline rerun on filter changes. Use this boundary:

```text
Validated analytical pipeline -> dashboard-ready datasets -> read-only interactive dashboard
```

### Recommended folder structure

```text
dashboard/
  app.py
  pages/
    1_Executive_Overview.py
    2_Data_Landscape.py
    3_Official_Review_Queue.py
    4_Case_Investigation.py
    5_Model_Validation.py
    6_Methodology_Controls.py
    7_Banking_Extension_Roadmap.py
  components/
    charts.py
    copy.py
    tables.py
  data_loader.py
  styles.py
src/
  10_prepare_dashboard_data.py
data/dashboard/
  dashboard_summary.json
  dashboard_review_queue.parquet
  dashboard_case_history.parquet
  dashboard_evidence.parquet
  dashboard_model_metrics.csv
  dashboard_case_briefs.json
  dashboard_metadata.json
```

### Recommended dashboard-ready data contracts

| Output | Grain | Required fields | Source |
|---|---|---|---|
| `dashboard_summary.json` | Project | boundary, years, row counts, family counts, quality counts, selected model, top-k | configs, manifest, panel, model selection |
| `dashboard_review_queue.parquet` | One row per top official observation | rank, obs_id, year, exporter/importer ISO3, names if available, hs6, family_id, product_name, score, rule_score, challenger_score, quality_status, data_quality_score, evidence_count | `top_ranked_corridors.csv` plus optional feature enrichments |
| `dashboard_case_history.parquet` | One row per year for each top case corridor-HS6 | selected_obs_id, history_obs_id, year, value, quantity, unit value, benchmark, residual, drift metrics, quality | `corridor_features.parquet` filtered by top case corridors |
| `dashboard_evidence.parquet` | One row per evidence item | obs_id, evidence_id, evidence_type, metric_name, observed, threshold, severity, summary, caveat | `evidence_table.csv` |
| `dashboard_model_metrics.csv` | One row per split/family/model | split, family, model, n, positives, k, precision, recall, lift, AP, hard-negative FPR, ordinary FPR | `model_comparison.csv` |
| `dashboard_case_briefs.json` | One object per briefed case | obs_id, headline, why, evidence IDs, typology IDs, benign explanations, missing info, steps, boundary | `analyst_briefs.json` |
| `dashboard_metadata.json` | Project/governance | source hashes, report hashes, scenario split manifest, model selection, generated_at | manifests and selection JSON |

Caching strategy:

- Use `st.cache_data` for all dashboard-ready file loads.
- Use file modification time or content hash in metadata to invalidate cache.
- Do not call training or feature-building scripts from the dashboard.

Testing strategy:

- Unit test dashboard data prep: row counts, required columns, no synthetic fields in official queue, evidence IDs link to known `obs_id`.
- Smoke test app import and page rendering.
- Manual interview rehearsal with offline fallback.

## 15. Pre-implementation gaps

### Blocking

| Gap | Why it blocks | Required fix |
|---|---|---|
| No dashboard-ready data layer | App would need fragile joins at runtime | Add `src/10_prepare_dashboard_data.py` or equivalent before app coding. |
| `src/10_make_dashboard.py` is empty | There is no existing dashboard implementation to extend | Either repurpose it as prep script or create `dashboard/` app cleanly. |
| Dashboard mockup claim not supported | Report mentions static dashboard concept but no artifact exists | Avoid claiming dashboard exists; correct wording before presentation. |
| No selected case history bundle | Case page needs same-corridor historical rows | Generate `dashboard_case_history.parquet`. |
| Need final primary/backup case decision | Dashboard defaults and interview script depend on it | Use rank 1 primary, rank 8 backup unless user chooses otherwise. |

### Important

| Gap | Why it matters | Required fix |
|---|---|---|
| Briefs only top 5 and all gold | Non-gold selected cases lack brief panels | Generate deterministic briefs for selected copper/palm backup cases or show "brief not generated". |
| Dirty git/untracked outputs | Hard to tell source of truth | Commit or clean generated artifacts before implementation branch. |
| No formal validation script | Harder to assert dashboard data integrity | Add `99_validate_outputs.py` or dashboard prep validation. |
| Hybrid selection nuance | XGBoost alone outperforms hybrid on some metrics | Explain hybrid as retained approach and show XGBoost comparison honestly. |
| Gold caveats | Top story could appear overconfident | Put caveat near gold case visuals. |

### Nice to have

| Gap | Reason |
|---|---|
| Better display labels for all country names | Improves readability. |
| Prepared feature-to-plain-English dictionary as JSON | Simplifies tooltips. |
| Static screenshot fallback deck | Reduces interview risk. |
| More polished report diagrams | Useful if embedded in app. |

## 16. Implementation roadmap

### Stage 0: Correct misleading or unreliable data issues

Tasks:

- Create dashboard data prep outputs under `data/dashboard/`.
- Remove or correct any claim that a dashboard/mockup already exists.
- Decide default case and backup case.
- Add validation checks for official queue, synthetic separation, evidence linkage, and required fields.
- Optionally generate briefs for rank 6/7/8 product-diverse cases.

Files affected:

- `src/10_prepare_dashboard_data.py` or `src/10_make_dashboard.py`
- `data/dashboard/*`
- Possibly `reports/final_analysis_report.md` if correcting wording

Dependencies:

- Current analytical outputs must exist.

Acceptance criteria:

- Dashboard-ready files exist with documented schemas.
- Official queue contains no synthetic columns.
- Every queue row in dashboard data has evidence count.
- Case history exists for primary and backup cases.
- Boundary text is available in metadata.

Risks:

- Runtime app joins become brittle if prep is skipped.

### Stage 1: Minimum viable stakeholder dashboard

Tasks:

- Build Streamlit app shell.
- Implement overview, data landscape, review queue.
- Load only dashboard-ready datasets.
- Add global filters and selected-case state.

Files affected:

- `dashboard/app.py`
- `dashboard/data_loader.py`
- `dashboard/pages/*`

Acceptance criteria:

- App runs locally.
- Queue filters work.
- Boundary visible.
- No synthetic labels on official pages.

### Stage 2: Case-investigation drill-down

Tasks:

- Add selected case page.
- Add history charts, evidence cards, data-quality caveats.
- Add brief panel where available.

Acceptance criteria:

- Rank 1 case renders correctly.
- Rank 8 backup renders correctly.
- Missing brief state is professional.

### Stage 3: Model-governance and methodology pages

Tasks:

- Add model comparison, split timeline, hard-negative FPR.
- Add source provenance and feature explanation sections.
- Add SHAP summary as appendix component.

Acceptance criteria:

- Scenario page clearly says labels are controlled scenarios.
- Official/synthetic distinction is visually obvious.

### Stage 4: Visual polish and deployment

Tasks:

- Apply restrained banking-oriented styling.
- Improve labels/tooltips.
- Create offline fallback screenshots or static walkthrough.
- Test on interview machine.

Acceptance criteria:

- 10-15 minute walkthrough works without code edits.
- Text does not overclaim.
- App has fallback assets.

### Stage 5: Optional extensions

Tasks:

- Add case comparison.
- Add analyst note export.
- Add feedback/outcome placeholder schema.
- Add optional Dash version if Streamlit state becomes limiting.

Acceptance criteria:

- Extensions remain clearly future-state unless data exists.

## 17. Interview walkthrough

### Opening

Click: Executive overview.

Say: "This project is a public-data review-priority lab for trade patterns. It ranks unusual corridor-product-year observations for human review, and it deliberately does not conclude money laundering or misinvoicing."

Emphasise: Boundary and human-in-the-loop review.

Likely question: "What does a high score mean?"

Answer: "It means the row has stronger review-priority signals relative to the features and selected scorer. It is not a probability of crime."

Transition: "Before looking at the queue, I will show the data boundary."

### Data landscape

Click: Data landscape.

Say: "The analysis covers 25,844 annual official-derived BACI rows from 2017 to 2024 across palm oil, copper, and gold. Data quality is explicit: 2,188 rows lack quantity and are excluded from modelling but retained for audit."

Emphasise: Gold missing quantity is material.

Likely question: "Why these commodities?"

Answer: "They give a focused demonstration across an Asia bulk commodity anchor, an industrial commodity, and a high-value typology-relevant commodity, each with a World Bank benchmark."

Transition: "The next question is how these rows become review signals."

### Pipeline and signals

Click: Methodology summary.

Say: "The model does not look into the future. It compares each row to prior corridor history, same-year product peers, and broad commodity benchmarks."

Emphasise: Time safety and benchmark caveat.

Likely question: "Is the benchmark fair value?"

Answer: "No. It is broad market context. It cannot prove an invoice price is wrong."

Transition: "Those signals produce an official-observation review queue."

### Review queue

Click: Official review queue.

Say: "This table contains official observations only. Synthetic scenarios are not shown here. The top 50 is product-diverse: 18 gold, 18 palm oil, and 14 copper observations."

Emphasise: Official-only separation.

Likely question: "Why is the top case gold?"

Answer: "Gold often has high-value/low-volume caveats, and this row shows strong divergence from its own history and benchmark context. The dashboard keeps those caveats visible."

Transition: "I will open the top case to show how the score becomes evidence."

### Case drill-down

Click: Rank 1 case.

Say: "This 2022 ESP-to-NLD gold observation ranked highest. The score is explained by four evidence rows: history deviation, benchmark-adjusted drift, benchmark gap, and annual unit-value change."

Emphasise: Evidence IDs and caveats.

Likely question: "How do you know it is not a false positive?"

Answer: "I do not know from public data alone. The system gives benign explanations and required private records to check. It also evaluates hard negatives in the scenario layer to test over-alerting behaviour."

Transition: "That leads to the model-governance page."

### Model validation

Click: Model validation.

Say: "Because public BACI has no confirmed TBML labels, evaluation uses controlled scenarios and hard negatives. On the test split, XGBoost and the hybrid rank positives much better than rules, logistic regression, or isolation forest, while keeping hard-negative FPR at zero in the all-family test summary."

Emphasise: Synthetic labels are not crime labels.

Likely question: "Why use both rules and ML?"

Answer: "Rules provide an auditable baseline. ML tests whether interactions among signals improve ranking. The hybrid retains some transparent rule structure while using the stronger challenger."

Transition: "Finally, the question is how this would fit inside a bank."

### Banking extension

Click: Roadmap.

Say: "Inside a bank, this public-data queue would not replace existing controls. It could enrich triage by pointing analysts to external corridor-product patterns, then analysts would compare with customers, invoices, payments, shipping documents, beneficial ownership, and case outcomes."

Likely question: "What would you improve next?"

Answer: "First, create a dashboard-ready data layer and formal validation checks. Then add private-data integration design, analyst feedback, and model monitoring."

Closing: "The value is not that public data proves TBML. The value is a governed, evidence-first way to decide what deserves human review and what facts should be checked next."

## 18. Final recommendation

NOT READY TO IMPLEMENT

The planning phase is complete enough to guide implementation, but dashboard coding should wait until these blocking issues are resolved:

1. Create the dashboard-ready data layer and schemas under `data/dashboard/`.
2. Correct or avoid unsupported claims that a dashboard/mockup already exists.
3. Generate selected-case history bundles for case investigation.
4. Decide whether to generate briefs beyond the top 5, especially for the recommended fully usable backup and product-diverse cases.
5. Add validation checks that official dashboard pages cannot accidentally expose synthetic labels or scenario rows.

Once Stage 0 is complete, the project will be ready for a Streamlit MVP implementation.
