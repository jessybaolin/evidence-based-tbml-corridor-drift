# Iteration notes — TBML review dashboard

Working notes so the next refinement cycle (human or AI) does not have to
rediscover decisions. First working version completed 2026-07-14.

## Current implementation

- **Completed pages (7):** Business Problem & Value, Official Review Queue,
  Selected Case Review, Queue Patterns, From Data to Review Queue (methodology
  story, added 2026-07-15), Model Validation & Controls, Appendix — all render
  from real pipeline outputs; 43 automated tests pass (contracts, metrics,
  sources, AppTest page renders).
- **Actual data connected:** `top_ranked_corridors.csv`, `evidence_table.csv`,
  `corridor_product_year_panel.parquet`, `corridor_features.parquet`,
  `model_comparison.csv`, `model_selection.json`,
  `hybrid_validation_candidates.csv`, `shap_summary_values.csv`,
  `logistic_coefficients.csv`, `xgboost_parameters.json`,
  `scenario_split_manifest.json`, `source_manifest.json`,
  `data_source_notes.json`, `source_file_inventory.csv`,
  `feature_explanation_table.md`, `data_dictionary.md`, `configs/*.yml`,
  `reports/figures/{model_comparison,hard_negative_comparison,shap_summary}.png`,
  `reports/figures/{official_data_pipeline_architecture,source_to_report_data_flow,time_safe_feature_construction_flow,train_validation_test_ml_workflow}.png`
  (methodology-story diagrams for the From Data to Review Queue page).
- **Reusable components:** styles (global CSS), page_header (+ section titles
  + provenance ledger), boundary_banner, kpi_cards, status_badges, charts
  (shared Plotly layout + 9 chart builders), tables (queue + plain), filters,
  evidence_panel, empty_states, source_cards.
- **Visual theme:** "deep blue" (updated 2026-07-15; superseded the earlier
  "winter blue" cream-plane pass, which was REJECTED because the Moonlight-cream
  plane made the whole page read as beige+white rather than blue). Now: cool
  BLUE plane (`#CFDAE8`) under Storm-navy ink, near-white cards (`#F8FBFE`) that
  lift off the plane, a deep-navy sidebar (`#23354D`) with frost text, one Steel
  slate-blue accent, frost hairlines, amber boundary stamp. Blue is the dominant
  hue by surface area (plane + navy sidebar + navy headings); white cards and the
  single amber caveat are the only non-blue notes. Moonlight cream is retired
  from the active palette. Family series colours are unchanged and stay a
  distinct CVD-safe trio (palm oil blue `#2A78D6`, copper aqua `#1BAF7A`, gold
  yellow `#EDA100`); status colours are reserved and always paired with text
  labels. Signature element: the **provenance ledger** line (mono-set file
  citation under each panel) + Steel left ledger-rule on evidence cards.

#### APPROVED colour mapping — "deep blue" (recorded design decision, 2026-07-15)

Reference palette transcribed from the brief image: Moonlight `#F0ECDD`,
Frost Blue `#8BA3C5`, Steel `#495B7D`, Storm `#23354D`, Oxford Blue `#02122F`.
The plane was moved from Moonlight cream to a Frost-derived cool blue so blue
dominates by area (the previous cream plane read as "beige"); cream was demoted
out of the active palette entirely. Change colours only in
`dashboard/config/dashboard_theme.yml` (+ keep `.streamlit/config.toml` in
sync; note `secondaryBackgroundColor` drives cards/widgets AND the default
sidebar — it is the near-white card surface, and `styles.py` re-skins the
sidebar to navy via `[data-testid="stSidebar"]`). Verified in Python (no Node):
WCAG contrast + OKLab CVD separation (Machado 1.0) — numbers below.

| Token | Hex | Role | Verified |
|---|---|---|---|
| `palette.ink` | `#23354D` Storm | primary text | 8.8:1 on blue plane, 12.0:1 on card |
| `palette.muted` | `#505D76` | secondary text | 4.7:1 on plane, 6.4:1 on card |
| `palette.page_bg` | `#CFDAE8` | app plane — the DOMINANT blue | ink 8.8:1; blue by area |
| `palette.panel_bg` | `#F8FBFE` | cards / chart surface | lifts off plane 1.36:1 |
| `palette.border` | `#B9C8DE` | bluer frost hairline | 1.20:1 vs plane (visible) |
| `palette.accent` | `#495B7D` Steel | links, eyebrows, selected, ledger rule | 6.6:1 card, 4.8:1 plane |
| `palette.accent_soft` | `#DCE5F2` | step-pill / soft wash | accent text 5.4:1 on it |
| `palette.ledger_ink` | `#3E4E68` | mono provenance lines | 8.1:1 card, 6.0:1 plane |
| `palette.sidebar_bg` | `#23354D` Storm navy | sidebar frame (anchors darkest blue) | frame 9.2:1 vs plane |
| `palette.sidebar_ink` | `#EAF0F8` | sidebar brand + nav text on navy | 10.9:1 on navy |
| `palette.sidebar_muted` | `#B7C6DE` | sidebar caption on navy | 7.2:1 on navy |
| `boundary.bg` | `#F7E4A6` | caveat card | pops 1.12:1 vs blue plane |
| `boundary.border` | `#E4C56A` | caveat hairline | — |
| `boundary.accent` | `#B07D16` | 4px left rule (caveat cue) | decorative rule, not text |
| `boundary.ink` | `#6E4E12` | caveat text | 6.0:1 on `boundary.bg` |
| `families.crude_palm_oil` | `#2A78D6` | Palm oil series | unchanged |
| `families.refined_copper_cathodes` | `#1BAF7A` | Copper series | unchanged |
| `families.gold_unwrought` | `#EDA100` | Gold series | unchanged |
| `chart.emphasis` | `#495B7D` Steel | the one highlighted series | dE 24.3 vs context |
| `chart.context_gray` | `#97A3B4` | de-emphasised context series | recessive by design (2.5:1) |
| `chart.grid_color` / `axis_color` | `#E5E9F0` / `#C2CBDA` | hairline grid / axis | on white card |

CVD verification (OKLab dE ×100, Machado severity 1.0): family pairs —
palm/copper 24.0 (deutan 23.1, protan 23.1); palm/gold 37.5 (39.0 / 31.6);
copper/gold 22.9 (deutan 16.6, **protan 9.1 — worst, still ≥ 8 floor**).
Family hues were therefore kept as the validated trio and NOT desaturated
into the navy palette (a monochrome ramp on nominal categories fails CVD).
`chart.emphasis` is the Steel brand accent (decoupled from palm-oil blue).
Limitation: contrast/CVD were computed numerically; the rendered browser
could not be visually inspected in this pass, so "blue is dominant" is argued
from the plane/sidebar/heading hexes + surface-area reasoning, not a screenshot.

#### Navigation — FINAL structure (2026-07-15, user-confirmed)

Two groups, seven pages. Icons are monochrome Material Symbols
(`icon=":material/<name>:"`) so they render in the frost sidebar colour. On-page
H1s live in `dashboard_content.yml pages.<key>.title` and are kept aligned to
the nav labels so nav and heading never disagree. (This SUPERSEDES the interim
group names "Story & Review Workflow" / "Validation & Reference" and the interim
Appendix title "Data Sources & Appendix".)

| Page file | Nav group | Nav + H1 title | Material icon |
|---|---|---|---|
| `executive_overview.py` | Business & Review | Business Problem & Value (default) | `account_balance` |
| `review_queue.py` | Business & Review | Official Review Queue | `checklist` |
| `case_investigation.py` | Business & Review | Selected Case Review | `search` |
| `portfolio_analytics.py` | Business & Review | Queue Patterns | `trending_up` |
| `from_data_to_review_queue.py` | Trust & Methodology | From Data to Review Queue | `account_tree` |
| `model_and_controls.py` | Trust & Methodology | Model Validation & Controls | `verified_user` |
| `appendix.py` | Trust & Methodology | Appendix | `menu_book` |

`from_data_to_review_queue.py` sits ABOVE Model Validation & Controls in the
Trust & Methodology group (governed methodology story → validation → reference).

Resolved this pass (the two label-consistency P2s from the prior pass):
`dashboard_content.yml navigation_steps` (the "how to use this dashboard" cards)
and the Appendix data-dictionary `pages` tags in `services/data_dictionary.py`
now use the FINAL nav labels ("Official Review Queue", "Selected Case Review",
"Queue Patterns", "Model Validation & Controls", "Business Problem & Value").
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

### From Data to Review Queue (methodology story, added 2026-07-15)
- **Purpose:** a governed, read-only narrative of how official public data
  becomes the review queue — for first-time / non-technical viewers who want the
  pipeline story before trusting the queue.
- **Components:** page_header + boundary_banner, an intro paragraph, a live
  "pipeline in real numbers" KPI strip, a four-stage walkthrough (heading +
  1–2 governed sentences + the documenting figure), a "Where the story stops"
  section, ledger.
- **Data:** panel (`len`, `model_eligible.sum`), review_queue (`len`),
  evidence (`len`, `nunique obs_id`) — all derived live, nothing hardcoded.
  Figures: `official_data_pipeline_architecture`, `source_to_report_data_flow`,
  `time_safe_feature_construction_flow`, `train_validation_test_ml_workflow`
  (added to `path_resolver.FIGURE_FILES`; loaded via `data_loader.figure_path`
  so a missing PNG degrades to `empty_states.missing_figure`, not a crash).
- **Accepted decisions:** the story STOPS at review queue + evidence — the
  analyst-brief / GenAI step is out of scope and its figure
  (`evidence_genai_grounded_brief_flow.png`) is deliberately NOT used; scenarios
  are labelled controlled evaluation constructs, never confirmed TBML; numbered
  stage markers are used because the pipeline genuinely IS an ordered sequence.
- **Known issues:** four full-width diagrams make the page long — a first-time
  viewer scrolls; the four stages are text+image only (no on-page interactivity
  by design). Diagram legibility at narrow widths is a human visual check.
- **Next refinements:** consider making the KPI strip a small horizontal funnel
  graphic; optional expanders to collapse individual stage diagrams.

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
- Run tests with `python -m pytest tests/ -q` (43 tests, ~8s).
- AppTest quirk: `selectbox.options` returns FORMATTED labels; use
  `select_index()` and compare raw values from session state.
- Streamlit ≥1.59: `st.dataframe(height=...)` accepts int | "stretch" |
  "content" — never None; `width="stretch"` replaces use_container_width.
- pandas 3.x in the venv: avoid `applymap`, mind copy-on-write.
- The pipeline rewrites `top_ranked_corridors.csv` in step 07 (adds real
  `key_evidence_count` as the LAST column) — don't assume column order.
