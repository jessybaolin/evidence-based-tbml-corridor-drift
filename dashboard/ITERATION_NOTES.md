# Iteration notes — TBML review dashboard

Working notes so the next refinement cycle (human or AI) does not have to
rediscover decisions. First working version completed 2026-07-14.

## Current implementation

- **Completed pages:** Executive Overview, Review Queue, Case Investigation,
  Portfolio Analytics, Model & Controls, Appendix — all render from real
  pipeline outputs; 41 automated tests pass (contracts, metrics, sources,
  AppTest page renders).
- **Actual data connected:** `top_ranked_corridors.csv`, `evidence_table.csv`,
  `corridor_product_year_panel.parquet`, `corridor_features.parquet`,
  `model_comparison.csv`, `model_selection.json`,
  `hybrid_validation_candidates.csv`, `shap_summary_values.csv`,
  `logistic_coefficients.csv`, `xgboost_parameters.json`,
  `scenario_split_manifest.json`, `source_manifest.json`,
  `data_source_notes.json`, `source_file_inventory.csv`,
  `feature_explanation_table.md`, `data_dictionary.md`, `configs/*.yml`,
  `reports/figures/{model_comparison,hard_negative_comparison,shap_summary}.png`.
- **Reusable components:** styles (global CSS), page_header (+ section titles
  + provenance ledger), boundary_banner, kpi_cards, status_badges, charts
  (shared Plotly layout + 9 chart builders), tables (queue + plain), filters,
  evidence_panel, empty_states, source_cards.
- **Visual theme:** "governed calm" — ink `#10243E` on `#F5F7FA`, white
  panels, hairline borders, teal `#0B7A75` accent, amber boundary stamp.
  Family series colours are fixed (palm oil blue `#2A78D6`, copper aqua
  `#1BAF7A`, gold yellow `#EDA100` — validated reference palette slots 1–3);
  status colours are reserved and always paired with text labels.
  Signature element: the **provenance ledger** line (mono-set file citation
  under each panel) + teal left ledger-rule on evidence cards.
- **Prototype elements retained:** st.Page/st.navigation architecture with
  grouped sidebar, page header hierarchy, boundary banner concept, queue
  filter → single-row-select → session-state → case page flow, ProgressColumn
  score bars, tabbed case layout, Model & Controls tab set,
  allowed/not-allowed language panel, light teal `.streamlit/config.toml`.
- **Prototype elements replaced/removed:** all sample CSVs, hardcoded KPI
  values, `make_demo_trend()` (indexed synthetic trend), the prototype
  banner, the Analyst Brief tab (GenAI out of scope), flat model-comparison
  table (real file is split × family × model).
- **Known gaps:** see per-page notes and Open design decisions below.

## Page-level status

### Executive Overview
- **Purpose:** ten-second orientation for a non-technical stakeholder.
- **Components:** boundary banner, 2×4 KPI rows, top-5 preview table, family
  coverage bar, quality summary bullets, limitations bullets, step cards.
- **Data:** panel (KPIs, coverage), queue (preview), evidence/model files (KPIs),
  source_manifest (verification KPI), model_selection (method KPI).
- **Accepted decisions:** two KPI rows of four (scope row + governance row);
  limitations verbatim from the final report; no model diagnostics here.
- **Known issues:** KPI cards can feel dense on ~1280px laptops; the coverage
  chart repeats on Portfolio (acceptable for now, different question).
- **Next refinements:** consider a compact "pipeline in one line" graphic;
  possibly show data as-of date from file mtimes.

### Review Queue
- **Purpose:** filter/sort/select the 50 ranked official observations.
- **Components:** filters row (9 controls + reset), queue_table (single-row
  select), selection confirmation, CSV download, ledger.
- **Data:** queue enriched with features (country names, residuals).
- **Accepted decisions:** empty multiselects mean "no restriction"; slider
  spans observed score range with padding; raw columns preserved in download.
- **Known issues:** with only 50 rows and scores 0.954–0.989 the score slider
  has a narrow useful band; searchable table relies on the search box (not
  st.dataframe built-in search).
- **Next refinements:** column visibility toggle; persistent filter presets;
  show benchmark residual column optionally.

### Case Investigation
- **Purpose:** understand why one observation ranked highly.
- **Components:** case selector, 4 header metrics + quality pill, five tabs
  (Summary / Trend / Why / Evidence / Limitations), evidence cards, ledger.
- **Data:** queue + features (record), panel (corridor history), evidence
  table, feature_explanation_table.md (approved interpretations), global SHAP
  figure (labelled global).
- **Accepted decisions:** no Analyst Brief tab; interpretations only from the
  approved table; log-scale toggle for the unit-value chart; the selected year
  is direct-labelled on trend charts.
- **Known issues:** signals table shows raw feature names (snake_case) beside
  approved wording — could carry display names; trend charts for corridors
  with 1 observed year look sparse (correctly so, but worth a note).
- **Next refinements:** small sparkline row in the header; per-signal severity
  badges aligned with the evidence thresholds; "compare with corridor peers"
  view.

### Portfolio Analytics
- **Purpose:** patterns across the review population.
- **Components:** candidates by year / family bars, score strip, residual
  emphasis histogram, three concentration bars, severity stack, ledger.
- **Data:** queue (+ enrichment), evidence, panel (population residuals).
- **Accepted decisions:** population-vs-queue emphasis histogram instead of a
  queue-only score histogram (only 50 scores exist); no map — ISO3 codes alone
  don't justify one analytically; evidence size channel dropped (all counts=4).
- **Known issues:** concentration charts can crowd at 3-across below ~1200px.
- **Next refinements:** quality-status split of the queue; novelty/reactivation
  counts (fields exist in features); optional treemap of corridors.

### Model & Controls
- **Purpose:** evaluation, selection, controls, and interpretation limits.
- **Components:** six tabs (Performance, Hard Negatives, Model Selection,
  Data Splits, Integrity Controls, Interpretation Boundaries).
- **Data:** model_comparison (split×family×model), model_selection,
  hybrid_candidates, xgboost_parameters, logistic_coefficients,
  shap_summary_values, scenario_split_manifest, source_manifest + inventory,
  live contract checks from services/data_contracts.py.
- **Accepted decisions:** scenario-vs-real framing banner at the top; emphasis
  colouring (selected scorer accent, baselines gray); governance note that the
  hybrid is not best on every metric; integrity checks run live on page load.
- **Known issues:** six tabs is a lot — Integrity Controls could merge into
  Data Splits; family-level metrics are behind the family selectbox rather
  than shown side by side.
- **Next refinements:** small-multiple family comparison; validation-vs-test
  delta view; render the split timeline graphically.

### Appendix
- **Purpose:** data dictionary + official sources without crowding main pages.
- **Components:** two tabs; dictionary filters (category/dataset/source/search)
  with thematic sections; four source cards with URL provenance labels.
- **Data:** feature_explanation_table.md + data_dictionary.md + live schemas
  of five artefacts; data_source_notes.json + source_manifest.json +
  REGISTRY_URLS.
- **Accepted decisions:** definitions are never invented — undocumented fields
  say "schema-inferred" with an empty definition; URL origin is always shown.
- **Known issues:** the dictionary lists ~180 field×dataset rows — the
  category sections keep it readable but some duplication across datasets
  remains (same field in panel and features appears twice, by design).
- **Next refinements:** de-duplicate identical fields across datasets with a
  "datasets" list column; add the typology cards (configs/typology_context.yml)
  as a third reference tab if stakeholders ask for typology context.

## Recommended next visual refinements
1. Responsive pass at 1280×800 and 1440×900 (KPI rows, 3-across concentration).
2. Consistent chart heights per row (portfolio row currently mixes 320/380).
3. Consider `st.dataframe` column pinning (rank/score) on the queue.
4. A more distinctive sidebar brand block (currently text-only).
5. Dark-theme variant of dashboard_theme.yml (charts already read tokens).

## Recommended next content refinements
1. Signals table: add stakeholder display names next to raw feature names.
2. Executive explanation paragraph could shrink by a third.
3. Surface `benchmark_caveat` more prominently on gold cases (unit-value gap
   is the story stakeholders will ask about).
4. Consider renaming "Data quality" column to "Data confidence" pending
   stakeholder wording review.
5. The queue caveat line could repeat above the download button.

## Open design decisions (review with stakeholders, don't guess)
- Should the queue show **rule vs challenger score** columns, or is the single
  blended score less confusing?
- Is the **top-50 cut** the right queue size for review capacity, and should
  the dashboard support a configurable top-N beyond 50 (requires pipeline
  change — scores for all rows are not persisted)?
- Do stakeholders want **novelty/reactivation** surfaced as queue filters?
- Should the Appendix include the FATF **typology cards** verbatim?
- Percentage formatting for scores (0.989 vs 98.9%) — currently 3-decimal raw.

## Adversarial review outcome (2026-07-14, first version)

A four-lens multi-agent review (demo-data, boundary language, data-join
correctness, code quality) raised 9 findings; all were independently verified
and all are FIXED in this version:
1. (high) Orphaned queue-table selection after a filter change could crash or
   silently open the wrong case → bounds check + content-derived table key
   (`review_queue.py`).
2. (medium) Chart element keys changed every rerun (module-global counter) →
   stable per-callsite keys through `charts.show(key=...)`.
3. (medium) Hardcoded caption "2022 dominates the current run" → derived from
   the plotted frame (`portfolio_analytics.py`).
4. (medium) Appendix dictionary attributed `synthetic_review_priority` to the
   official raw BACI extract → curated dataset override to
   scenario_labels.parquet.
5. (low) Hardcoded "200 evidence rows" caption → f-string from the loaded frame.
6. (low) BACI source card substituted hardcoded release/revision/filename when
   metadata was missing → absent facts now render "not recorded".
7. (low) `benchmark_consistency_gap` showed "—" on the case page → definition
   quoted from src/tbml_common.py and labelled code-derived.
8. (low) Tests pinned regenerable artefact values → expectations now derive
   from the loaded artefacts.
9. (dup of 3/5, same fix).

## Tooling notes for future AI iterations
- Run tests with `python -m pytest tests/ -q` (41 tests, ~6s).
- AppTest quirk: `selectbox.options` returns FORMATTED labels; use
  `select_index()` and compare raw values from session state.
- Streamlit ≥1.59: `st.dataframe(height=...)` accepts int | "stretch" |
  "content" — never None; `width="stretch"` replaces use_container_width.
- pandas 3.x in the venv: avoid `applymap`, mind copy-on-write.
- The pipeline rewrites `top_ranked_corridors.csv` in step 07 (adds real
  `key_evidence_count` as the LAST column) — don't assume column order.
