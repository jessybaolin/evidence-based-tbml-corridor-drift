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

## Polish iteration (2026-07-15) — motion, tables, brand, chart chrome

Centralised-only changes; no page files edited, all data/metric logic and the
conclusion boundary untouched. 43 tests stay green.

1. **Sidebar nav hover motion** (`components/styles.py`) — the ONLY animation in
   the app. `[data-testid="stSidebarNav"] a` gets a 150ms ease-out transition on
   background / a constant-width transparent left rule (fades to frost) / a 2px
   translateX indent on hover; `aria-current` keeps a solid frost rule. A scoped
   `@media (prefers-reduced-motion: reduce)` disables the transition + transform.
   No JS, no reflow (border width is constant; only colour + transform animate).
2. **Brand block above the nav + rename** (`styles.py` + `dashboard_content.yml`).
   Reorder via flexbox: a double-`:has()` selector self-selects the exact sidebar
   container holding BOTH `stSidebarNav` and `stSidebarUserContent` as direct
   children, sets it `flex-direction:column`, and `order`s user content (1) before
   nav (2); collapse control (`stSidebarHeader`) stays on top. Degrades to a no-op
   if the DOM changes. Renamed: `app.title` = "Evidence-First TBML Triage System",
   `app.short_title` = "TBML Triage System" (browser tab), `app.subtitle` =
   "Turns official public trade data into a ranked queue of unusual
   corridor–product–year patterns for human review." Boundary wording unchanged.
3. **Table readability** (`components/tables.py` + new `palette.table_stripe`
   token). st.dataframe is a canvas grid — per-cell CSS won't stick, so readability
   is tuned via the levers that DO reach it: `row_height` (queue 38 / plain 36),
   header `help` tooltips + pinned Rank on the queue, and a pandas Styler that
   paints a faint cool zebra (`#EFF3FA`) on odd rows of every `plain_table`
   (st.dataframe honours a Styler's `background-color`). Numerics stay
   right-aligned/tabular by column type; NO values reformatted (meaning intact).
   `plain_table(..., zebra=False)` disables striping per call.
4. **Chart chrome harmony** (`components/charts.py` `_layout`). Transparent
   paper/plot retained (sits on card or plane); axis tick labels dropped to
   `muted` (cool, recessive) while titles keep Storm ink; tooltips themed to the
   card surface (Storm ink on near-white `#F8FBFE`, frost border) instead of
   Plotly's default. NO series hue touched — family trio and emphasis/context are
   byte-for-byte unchanged. Re-verified numerically (OKLab dE ×100, Machado 1.0):
   family worst pair copper–gold protanopia = 9.1 (≥8 floor), normal min 22.9;
   emphasis-vs-context dE 23.9–24.6. New text pairs clear WCAG: axis ticks muted
   on plane 4.69:1 / on card 6.38:1, tooltip/title ink 12:1, zebra text ≥5.96:1.
   Static pipeline PNGs on "From Data to Review Queue" were left as-is (already on
   the white card, well sized) — a true in-theme recolour needs a pipeline-figure
   regeneration (`reports/figures/*.png`), which is out of scope for the dashboard.
   Optional future: render them via `st.graphviz_chart` from `reports/figures/*.dot`
   with themed nodes.

Cannot see the rendered browser in this environment — the hover motion, the
title-above-nav order, table legibility, and chart harmony are human visual
checks. AppTest (exception-free + boundary present) and computed WCAG/CVD numbers
are the available evidence.

## Data Coverage & Trust rebuild (2026-07-17, latest)

47 tests green (was 45; +2 scene-page tests). `app_pages/from_data_to_review_queue.py`
fully rebuilt as the interactive "Data Coverage & Trust" story:

1. **Page frame**: H1 "From Trusted Public Data to Review-Ready Evidence";
   sticky mental-model strip (`.mental-model`, position: sticky) keeps the one
   takeaway visible while scrolling; 5-tile trust KPI strip — observations
   (25,844) · period (2017–2024) · families (3) · eligible for scoring (91.5%,
   23,656 rows) · trade-value coverage (99.9%) — ALL derived live from the
   panel's `model_eligible` + `trade_value_usd`; KPI hover definitions reuse
   the `.tip` CSS tooltips. Trade value framed as public trade coverage, never
   bank exposure.
2. **Scene mechanics**: three scenes (Sources & scope / Prepare the data /
   Test, rank & explain) behind a persistent st.segmented_control stage bar +
   Previous/Next/Replay st.buttons (keys `dtrq_prev`/`dtrq_next`/
   `dtrq_replay_btn`) + "Scene N of 3". Replay/scene-switch works by embedding
   a counter in the scene wrapper's data attribute → markdown changes → DOM
   remounts → the CSS entrance storyboard replays. No auto-advance, no loops.
3. **Scene 1**: three source cards (CEPII BACI / World Bank CMO / FATF–Egmont)
   each with supplies/credible/use/boundary + CSS hover-reveal previews built
   from REAL rows (largest non-queue flow as the BACI sample; latest gold
   benchmark year); raw BACI field names kept off the canvas. Unit-of-analysis
   block (equation + real corridor visual + It is / It is not). Product-family
   cards (stress / benchmark / scale-and-stability) with hover HS6 + benchmark
   unit + what-it-tests, four selection tags.
4. **Scene 2**: five-stage pipeline; provenance expander holds the SHA-256s;
   three standardisation examples; record-merge micro-animation with lineage
   icon; usability funnel (total → eligible → value share) with the CORRECTED
   exclusion wording — missing/invalid QUANTITY (not value) blocks implied
   unit-value analysis; rows retained for audit; "a missing quantity is a data
   limitation, not a suspicion signal". Time-safe panel: definition + five
   signal chips, each verified against real feature families
   (robust_historical_z / same_family_year_peer_percentile /
   benchmark_residual+drift / value_quantity_divergence /
   corridor_novelty+reactivation flags) + the year strip (history lit, focus
   year highlighted, later years ✕ hidden).
5. **Scene 3**: HTML/CSS forked pipeline — blue official lane vs dashed
   evaluation lane (new `evaluation:` theme tokens; label "Controlled
   evaluation copy—not official findings", colour never alone); only the
   selected-model chip animates back across (travel_ms 600, natural state =
   end position for reduced-motion); eval lane recedes to 0.90 opacity after.
   Output flow (case → evidence rows → caveated brief → human review) with
   real evidence-check tags; FATF two-input separation diagram + brief
   structure + layer-role table; brief text never rendered (no-LLM rule).
6. **Closing**: bottom-line statement + "Annual public aggregates—not
   invoices, customers or bank exposure." Technical companion expander now
   holds the four pipeline PNGs (moved off the canvas), the raw BACI field
   table from data_source_notes, and the checksum records.
7. **Tests**: +2 — mental model + derived KPI values on default render;
   scene walk via the Prev/Next buttons asserting the corrected quantity
   wording (scene 2), the evaluation-wall labels and real check names
   (scene 3), and back-navigation.

## Nav cleanup: drop copy page, reorder (2026-07-17, later)

45 tests green (was 48; −3 copy-page tests). Changes in this pass:

1. **Removed the frozen comparison page** `business_problem_value_copy.py` (the
   before/after was done). Deleted: the page file, its PAGE_GROUPS entry, the
   `pages.business_problem_value_copy` content block, the legacy
   `boundary_banner()` helper, and its `.boundary-banner` CSS — all had that page
   as their only consumer. The boundary now lives ONLY in the fixed footer ribbon.
2. **Reordered navigation.** `From Data to Review Queue` moved out of "Trust &
   Methodology" into "Business & Review" as item 2, directly under "Business
   Problem & Value" — so the group reads intro → how the queue is built → queue →
   case → patterns. "Trust & Methodology" now holds Model Validation & Controls +
   Appendix. `st.page_link` targets unaffected (paths still registered).
3. **Tests**: dropped `business_problem_value_copy.py` from PAGES and removed
   `test_copy_page_keeps_previous_content`. Every remaining page still asserts the
   verbatim boundary via the ribbon.

## Landing-page redesign + boundary ribbon (2026-07-17)

48 tests green (was 43). Changes in this pass:

1. **Narrative landing page** (`app_pages/executive_overview.py`, full rewrite;
   nav label unchanged). Answers, in order: problem → what the project does →
   what it produces → why it matters → what it does not claim. H1 "Evidence-
   Backed Trade Pattern Triage". Sections: hero · business problem +
   challenge/response twin cards · what-it-does prose + commodity chips (family
   colour dot + official product name) · stakeholder stat band (25,844 obs /
   Top 50 queue / 4 evidence points per case / 5 caveated analyst briefs — ALL
   derived live from panel/queue/evidence/analyst_briefs.json) · pipeline flow
   strip · before/after question reframe · navy bottom-line strip + value chips.
   No queue table, no charts (they live on their pages). All copy in
   `dashboard_content.yml` (`pages.executive_overview`), numbers via
   `str.format` placeholders. New loader `load_analyst_briefs()` +
   `analyst_briefs` registry entry (count/existence only — brief TEXT is never
   rendered; no-LLM rule intact).
2. **Boundary ribbon replaces per-page banners** (`boundary_banner.py`
   `boundary_ribbon()`, rendered ONCE in `streamlit_app.py` before
   `navigation.run()`). Slim fixed footer on EVERY page: Steel fill, frost
   text, uppercase stamp label, 3px Frost-Blue top rule, z-index 60 (below the
   sidebar's 100 — navy sidebar intentionally covers its left end; text is
   inset 21rem at ≥993px so it clears the sidebar). `.block-container`
   padding-bottom 6.5rem so content never hides beneath it. The old
   `.boundary-banner` CSS + `boundary_banner()` stay ONLY for the frozen copy
   page. Verbatim text still from `configs/project.yml`.
3. **pages/ → app_pages/ rename** (all 8 page files). A directory literally
   named "pages" next to the entry point flips Streamlit onto its MPA-v1
   compatibility path (`PagesManager.uses_pages_directory`), under which a
   cold-session deep link (and AppTest.switch_page) executes the page file
   ALONE — no styles, no sidebar, no ribbon. Renaming removes the hazard for
   public hosting and lets tests run pages through the real shell.
4. **CSS-only tooltips** (`.tip` span + `data-tip` attr, hover AND
   keyboard-focus via tabindex): corridor-term definition in the prose, and
   the evidence tile listing the 5 real evidence checks from
   `evidence_table.csv` (history deviation, annual unit-value change,
   benchmark-adjusted drift, benchmark gap, value–quantity divergence; display
   names in `content.evidence_type_labels`). Navy bubble, frost text.
5. **Motion** (new `motion:` tokens in dashboard_theme.yml): one `rise-in`
   fade-up (350ms ease-out, both) staggered 70ms across landing sections —
   replays on page switch, not on widget reruns; hover lift on twin cards,
   stat tiles + main-area page-link CTAs; flow-step hover brighten. ALL of it
   (plus the older sidebar-nav hover) disabled in one consolidated
   `prefers-reduced-motion` block kept LAST in the sheet with !important.
6. **Tests** (`test_dashboard_pages.py`): pages now run through
   `streamlit_app.py` + `AppTest.switch_page` (real shell), boundary asserted
   VERBATIM (read from configs/project.yml) on every page run incl. the copy
   page; new landing tests (derived numbers, evidence-check names, tooltip
   presence) + copy-page freeze test (old content + banner AND ribbon).
7. **Frozen comparison page**: `business_problem_value_copy.py` retargeted to
   duplicated content block `pages.business_problem_value_copy`; otherwise
   byte-identical, still uses the in-page banner. Delete page + content block
   + banner helper together when comparison is done.

Contrast (computed, WCAG): ribbon text 6.57:1 / label 5.46:1 on Steel; tooltip
frost on navy 10.85:1; bottom-line frost on navy 10.85:1; quote-after frost on
Steel 6.57:1; flow-step ink on accent_soft 9.80:1; before-quote ink on stripe
11.18:1. Chip dots are sub-3:1 non-text marks (copper 2.71, gold 2.08) —
mitigated with an inset ink ring + the product NAME in the chip (colour never
alone). Rendered-browser look (ribbon overlap at odd widths, animation feel,
tooltip position) still needs a human pass — AppTest can't see pixels.

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
