# Technical Companion Figure Inventory

## Visual policy

The revised companion uses current project data and current dashboard captures.
Architecture and process diagrams are rendered as HTML/CSS vector content in
the PDF. Statistical charts are regenerated from current CSV/Parquet outputs.
Legacy mock-ups and superseded diagrams are excluded.

## Planned visual inventory

| ID | Working title | Type | Source | Status |
|---|---|---|---|---|
| F1 | System at a glance | Vector lifecycle | Current pipeline and dashboard modules | New |
| F2 | Implemented lifecycle from source to live dashboard | Vector architecture | `src/`, dashboard, requirements, deployment config | New |
| F3 | Data architecture and artefact lineage | Vector data flow | Current tables and `path_resolver.py` | New |
| F4 | Coverage by year and family | Line/bar chart | Panel Parquet | New |
| F5 | Population versus Top-50 composition | Paired bar chart | Panel and queue | New |
| F6 | Gold quantity-coverage gap | Focused bar/callout chart | Panel and gold notebook | New |
| F7 | Time-safe feature timeline | Vector timeline | `build_features()` | New |
| F8 | Official versus controlled-scenario separation | Vector process diagram | Scenario code and manifest | New |
| F9 | Weighted-sum score construction | Vector formula diagram | Threshold config and `score_rules()` | New |
| F10 | Model selection chronology | Vector flow | Project config and model script | New |
| F11 | Model comparison on held-out test | Grouped bar chart | `model_comparison.csv` | New |
| F12 | Family-level hybrid performance | Small-multiple chart | `model_comparison.csv` | New |
| F13 | Global XGBoost contribution summary | Horizontal bar chart | `shap_summary_values.csv` | New |
| F14 | Current Top 50 Review Queue | Dashboard capture | `references/project_brief/assets/dashboard_07_ranking_table.png` | Reuse current capture |
| F15 | Selected case analytics | Dashboard capture | `references/project_brief/assets/dashboard_04_selected_case.png` | Reuse current capture |
| F16 | Streamlit component and data-service architecture | Vector component diagram | Dashboard modules and services | New |
| F17 | GitHub to Streamlit Community Cloud deployment | Vector deployment flow | Repository/config/requirements | New |
| F18 | Current to future bank pathway | Vector implementation-status summary | Current bank pathway page and project references | New |

## Excluded visuals

- `docs/brief_assets/fig_architecture.png`: omits the current dashboard and
  deployment layers.
- `docs/brief_assets/fig_brief_flow*.png`: predates the current evidence and
  page structure.
- `docs/brief_assets/fig_future_state*.png`: replaced by the current dashboard
  bank-pathway capture and a new implementation-status diagram.
- `docs/brief_assets/fig_model_comparison*.png`: model values are regenerated
  from the current comparison CSV.
- `docs/brief_assets/fig_shap.png`: values are regenerated from the current
  SHAP CSV in the revised palette.
- All prototype screenshots under
  `references/tbml_streamlit_multipage_prototype/`.

## Dashboard capture verification

The reused captures are repository-local images generated from the current
dashboard build for the stakeholder brief. They show current official outputs,
not sample data. The technical companion crops them to the relevant analytical
surface and adds a light document border; it does not recreate the tables
manually.
