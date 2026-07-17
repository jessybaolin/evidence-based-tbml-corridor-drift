# TBML Corridor Review — multipage Streamlit analytics dashboard

An interactive, browser-based stakeholder dashboard for the **Evidence-First
TBML Corridor Drift Lab**. It presents the analytical pipeline's generated
outputs — the official review queue, per-case evidence, portfolio patterns,
model governance, and source provenance — as six navigable pages.

> **Human-review boundary** (shown on every page, loaded verbatim from
> `configs/project.yml`): *This output prioritises an unusual corridor-product
> pattern for human review. It does not establish money laundering,
> misinvoicing, or criminal intent.*

## What it is (and is not)

- **Multipage Streamlit analytics dashboard** — it opens in a web browser and
  has navigation like a small internal website, but its job is interactive
  analytical exploration, not public web content. Streamlit renders the whole
  interface from Python; there is **no Node.js, npm, React, Flask, or separate
  frontend/backend stack**.
- **Read-only presentation layer** — it never retrains models, rebuilds the
  panel, injects scenarios, or writes over analytical outputs. Changing a
  filter re-slices cached dataframes; it never reruns the pipeline.
- **No LLM / GenAI layer** — the project's optional analyst-brief artefacts
  are deliberately out of scope. Nothing in this dashboard calls an AI
  provider, and no such layer is required to run it.

## Requirements

Upstream outputs are produced by the pipeline in `src/` and must exist before
the dashboard has anything to show:

| File (repo-relative) | Backing pages | Regenerate with |
|---|---|---|
| `data/outputs/top_ranked_corridors.csv` | Overview, Queue, Case, Portfolio | `python src/06_train_evaluate_models.py` then `src/07_build_evidence.py` |
| `data/outputs/evidence_table.csv` | Case, Portfolio | `python src/07_build_evidence.py` |
| `data/processed/corridor_product_year_panel.parquet` | Overview, Case trends, Portfolio | `python src/03_build_panel.py` |
| `data/processed/corridor_features.parquet` | Queue enrichment, Case signals | `python src/04_build_features.py` |
| `data/outputs/model_comparison.csv`, `model_selection.json` | Model & Controls | `python src/06_train_evaluate_models.py` |
| `configs/project.yml`, `configs/hs_families.yml` | boundary, scope, labels | (checked-in configuration) |

Optional files (missing ones produce a labelled empty state, never fake data):
`hybrid_validation_candidates.csv`, `shap_summary_values.csv`,
`logistic_coefficients.csv`, `xgboost_parameters.json`, `source_manifest.json`,
`data_source_notes.json`, `source_file_inventory.csv`,
`scenario_split_manifest.json`, `reports/feature_explanation_table.md`,
`reports/data_dictionary.md`, `reports/figures/*.png`.

File discovery: `dashboard/services/path_resolver.py` walks up from its own
location until it finds `configs/project.yml` **and** `src/tbml_common.py`, so
the app works regardless of the terminal's working directory. All paths are
registered in one place (`DATA_FILES`) with purpose and required/optional
status.

## Install & run

```powershell
# from the repository root
.venv\Scripts\activate            # or create one: py -m venv .venv
python -m pip install -r requirements.txt
python -m streamlit run dashboard/streamlit_app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`). Keep the
terminal open while using the app.

Run the test suite:

```powershell
python -m pytest tests/ -q
```

## Pages

1. **Executive Overview** — boundary banner, one-paragraph explanation, eight
   derived KPI cards, top-five candidates, family coverage, data-quality
   summary, key limitations, navigation guidance.
2. **Review Queue** — the 50 top-ranked official observations with filters
   (year, family, exporter, importer, quality, score range, evidence count,
   search, top-N), single-row selection, and filtered CSV download.
3. **Case Investigation** — one selected observation in five tabs: Case
   Summary, Trade & Benchmark Trend (real corridor history from the clean
   panel), Why It Ranked High (actual feature values + approved plain-English
   interpretations; global SHAP labelled as global), Evidence (cards from
   `evidence_table.csv`), Limitations.
4. **Portfolio Analytics** — candidates by year/family, score strip, benchmark
   residual distribution (queue vs population), exporter/importer/corridor
   concentration, evidence severity mix.
5. **Model & Controls** — scenario-based comparison (split/family/metric),
   hard-negative false-positive rates, model selection record, split design,
   live integrity checks (including the no-synthetic-rows control), and
   allowed/not-allowed interpretation language.
6. **Appendix** — searchable data dictionary (documented + schema-inferred,
   with definition provenance) and official source cards with clickable URLs.

## How case selection works

Selecting a row on **Review Queue** stores the `obs_id` in
`st.session_state["tbml_selected_obs_id"]` (see
`services/session_state.py`). **Case Investigation** reads that key and falls
back to a case selector, so the page also works when opened directly or after
a browser refresh.

## Missing outputs & common errors

- **Required file missing** → a full-page error names the file and the exact
  pipeline command to run. The dashboard never substitutes demo data.
- **Optional file missing** → the affected panel shows: *"This panel is
  unavailable because the required project output has not been generated. Run
  the relevant analytical pipeline stage and reload the dashboard."*
- **`ModuleNotFoundError: dashboard`** → run from the repository root using
  the command above (the entry point bootstraps `sys.path` itself; only exotic
  launch methods bypass it).
- **Port already in use** → add `--server.port 8502`.

## Known limitations

- The pipeline persists scores for the **top 50** real observations only, so
  score-distribution views describe the queue, not the full population
  (population context uses the panel's benchmark residuals instead).
- SHAP is a **global** summary; row-level SHAP is not produced and therefore
  never displayed per case.
- World Bank CMO and FATF–Egmont URLs are not recorded in project metadata;
  they are maintained in `services/source_registry.py` and labelled as such.
- The queue's evidence counts are uniformly 4 in the current run, so evidence
  count is not a useful size/filter channel yet.

## Appendix data sources

Source cards combine project metadata (`data/raw/data_source_notes.json`,
`data/outputs/source_manifest.json`: publisher, release, units, SHA-256,
caveats) with official URLs. The CEPII BACI URL comes from project metadata;
the World Bank and FATF–Egmont URLs are maintained in the dashboard's source
registry (verified 2026-07-14). Source URLs document provenance only.

## Relationship to the reference prototype

`references/tbml_streamlit_multipage_prototype/` is the design skeleton this
implementation started from (navigation concept, page split, visual hierarchy,
selection flow). It remains untouched for comparison and is git-ignored. The
working implementation lives entirely in `dashboard/` and reads only real
pipeline outputs — every sample CSV, hardcoded KPI, and demo trend generator
from the prototype was replaced.

## Future iterations — where to edit what

| Change | Edit |
|---|---|
| Page wording, titles, captions, limitations | `dashboard/config/dashboard_content.yml` |
| KPI cards (selection/labels) | `dashboard_content.yml` (labels) + `services/dashboard_metrics.py` (`overview_kpis`) |
| Charts (type, series, defaults) | `components/charts.py` (page files only compose) |
| Dashboard colours / status styling | `dashboard/config/dashboard_theme.yml` (+ `.streamlit/config.toml` for the Streamlit base theme) |
| Page navigation (order, icons, groups) | `dashboard/streamlit_app.py` |
| Adding a queue filter | `components/filters.py` + `apply_queue_filters` in `services/dashboard_metrics.py` |
| Adding a stakeholder page | new file in `dashboard/app_pages/` + one `st.Page` entry in `streamlit_app.py` |
| Data-source paths | `services/path_resolver.py` (`DATA_FILES`) |
| Data contracts | `services/data_contracts.py` |
| Data dictionary metadata | `services/data_dictionary.py` (`CURATED`) — definitions come from `reports/` |
| Official source URLs | `services/source_registry.py` (`REGISTRY_URLS`) |

See `ITERATION_NOTES.md` for page-level status and the agreed design language.
