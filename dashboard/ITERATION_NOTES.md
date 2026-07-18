# Iteration notes — TBML review dashboard

Working notes so the next refinement cycle (human or AI) does not have to
rediscover decisions. First working version completed 2026-07-14.

## 2026-07-18 — Selected Case Review: "Why It Ranked High" merge + comparison cards

Merged the old "Why It Ranked High" and "Evidence" tabs into one stakeholder
tab; final tabs are Case Summary · Why It Ranked High · Limitations. Scoring,
ranking, features and evidence generation untouched; presentation/wording only.
Tests 79 -> 103 (new `tests/test_why_ranked_high.py`, 18 checks over all 50 cases).

**New pure module `services/why_ranked_high.py`** (no Streamlit, unit-tested):
`signal_number()` is the ONLY place log space becomes a multiple — exp() for the
six log fields (unit_value_yoy_change, benchmark_residual, benchmark_adjusted_drift,
trade_value_yoy_change, quantity_yoy_change, value_quantity_divergence), x100 for
same_family_year_peer_percentile, identity for robust_historical_z (a z-score,
NEVER exp'd — exp(18.8) is nonsense), counts/flags/benchmark_consistency_gap kept
raw. `card_metrics()` returns the 4 card slots with availability + magnitude +
direction. `summary_clause_keys()` returns the evidence-row-driven summary keys.
`percentile_ordinal()` formats 99.36 -> "99.4th". `signal_profile()` orders the
12 signals by analytical importance.

**KEY DESIGN DECISION (data-driven, verified):** each queue case has exactly 4
evidence rows drawn from 5 evidence types, so which types are present VARIES
(benchmark_gap 33/50, value_quantity_divergence 29/50, etc.). Audited fact: for
every case LACKING a card's evidence type, the underlying feature is still
present and often large (rank 2 lacks a benchmark_gap row yet its benchmark
multiple is ~9x). Therefore: the **four comparison cards always show the real
per-case feature value** (a card shows its data-absence line only when the
feature is genuinely NaN — none in the current queue), while the **dynamic
top-of-tab summary is strictly evidence-row-driven** (names a comparison as a
reason only when that evidence_type is one of the case's rows). This never hides
a real signal and never claims an unflagged one. Cards read from the feature
(equal to the evidence row's observed_value, verified).

**Layout:** dynamic plain-English summary (`.why-summary`) + verbatim note
"These comparisons explain the review priority. They are reasons to examine the
pattern, not conclusions about wrongdoing." -> four cards in a 2x2 st.columns
grid (`components/cards.comparison_card_markup`, `.compare-card`; teal top rule,
no red severity badges; caveat = info-icon `.tip`; per-card "How calculated"
expander) -> collapsed "Signals for this observation" (custom `.data-table` with
monospace technical field column, native-title tooltips on display labels,
`.signals-scroll` sticky-header scroll; columns Technical field · Display label ·
Case result [value + interpretation] · How it is derived · Time-safety rule) ->
collapsed "Audit details" (raw evidence records; renamed from "Evidence as a
table"). Card C (robust_historical_z) shows plain-English primary + "{z} robust
deviations {above/below} the prior pattern" secondary — the z is never the
headline and never exp'd.

**Removed from the page:** the global SHAP block "Model-contribution context
(global)" (belongs on Model Validation & Controls, not an individual case) and
the raw `data_quality_flags` string (`quantity_missing=0; ...`) — the compact
header quality pill and Limitations tab carry quality context. All new copy is
in `dashboard_content.yml pages.case_investigation.why`. `dashboard_metrics.case_signals`
and `SIGNAL_FIELDS` are now unused by the page (kept; no consumer) — the signal
profile is built by `why_ranked_high.signal_profile` + content labels.

**Percentile wording note:** the signals-table "Case result" uses the spec's
ordinal form ("99.4th percentile", suffix from the last shown digit); the Case
Summary peer view still says "at or above 99.4% of peers". Both are the same
0-1 share x100.

## 2026-07-17 — Selected Case Review rework (strip header, comparison carousel, validation gate)

Rework of `app_pages/case_investigation.py` per notebook §6.2
(`data-profiling/business_Review_Data_profiling_revamped.ipynb`). Scoring
logic, ranking outputs and analytical datasets untouched. Tests 64 → 79.

**Header.** The four KPI cards (rank / score / evidence rows / quality) are
replaced by ONE compact amber selected-case strip (`.st-key-case_strip`, the
Review Queue selection treatment): `#RANK · YEAR · EXP → IMP · PRODUCT · HS6`
on the left; review-priority score with the governed tooltip, a compact
data-quality pill and the **Change case** selectbox on the right. The selectbox
remains the page's FIRST selectbox (AppTest drives `at.selectbox[0]`) and keeps
the `tbml_selected_obs_id` contract: it renders in the rightmost strip column
but EXECUTES first so the facts on its left describe this rerun's pick.

**Tabs.** "Trade & Benchmark Trend" is retired (its three chart builders left
`components/charts.py` with it). Remaining: Case Summary, Why It Ranked High,
Evidence, Limitations. All page copy moved to
`dashboard_content.yml pages.case_investigation` (the page previously
hardcoded nearly everything).

**Case Summary.** `st.columns([35, 65])`. Left: "Case facts" panel
(`cards.render_fact_list`, new `.fact-list` CSS) merging the old Observation +
Reported values sections; "Aggregate unit value" renamed **Implied unit value**
with the exact governed tooltip; removed from view: rule score, challenger
score, raw benchmark residual, obs_id, source paths, the "Hybrid: 75% …"
formula (now "Selected blended ranking method" + a page link to Model
Validation & Controls). obs_id / source row / source version / ledger live in a
collapsed **Data provenance** expander. Right: a three-view comparison carousel
(market comparison · own history · peer position) reusing the dtrq segmented +
prev/next mechanics with NEW keys (`case_view_idx`, `case_view_bar`,
`case_view_prev/next`), a per-view Chart|Table segmented control
(`case_view_mode_{i}` — one key per view, so toggling one view never flips
another), and one fixed chart height (`chart.height_tall` via
`charts.case_view_height()`), so switching views never jumps. No auto-rotate;
swipe is not possible in CSS/JS-free Streamlit and was deliberately skipped.

**Analytics.** All view analytics are pure functions in
`services/case_summary.py`: `corridor_series`, `market_comparison_frame`,
`own_history_frame` (exponentiates the NATURAL-LOG
`shifted_corridor_history_median` exactly once; prior years only; unobserved
years stay all-NaN so lines GAP — never filled), `peer_position` (notebook
§6.2b population: same family_id + year, finite ratio > 0, case included;
inclusive at-or-below percentile; log10 histogram bins clipped to 0.01×–100×
for DISPLAY while every peer stays in the percentile maths) and
`validate_case_view` — a runtime consistency gate the page runs before showing
any number (identity agreement across queue/features/panel, unit value =
value/quantity, multiple = uv/benchmark, prior-median recomputation, peer
membership/percentile, histogram conservation). Any violation renders a
governed warning INSTEAD of numbers. Charts and tables consume the same
prepared frames; new builders `case_market_view` / `case_history_view` /
`case_peer_view` live in `components/charts.py` (family colour for the
corridor, dotted grey benchmark, dashed navy prior median, muted-amber
selection diamonds from the theme selection tokens).

**Percentile wording.** The notebook prints "above 99.4% of peers" but
computes the INCLUSIVE at-or-below share `(ratio <= case).mean()` — so the
takeaway says "sits **at or above** {pct} of {n} same-product corridors",
which is mathematically true under the §6.2 formula. The stored feature
`same_family_year_peer_percentile` uses average-rank tie handling and can
differ by half a tie (e.g. rank 6: 0.8813 vs 0.8808); tests assert closeness,
not equality, and the display follows §6.2.

**Terminology.** `pages.case_investigation.caveat` updated to "The implied
unit value is an annual aggregate, not an invoice price." so the Limitations
closing line matches the renamed measure.

**Fixer round 1.** The Own-history table column originally titled "Prior
active-year count" (spec wording) is relabelled **"Prior years used for
median"**: the cell shows `prior_years_used` — prior years with a COMPUTABLE
unit value, i.e. the values the prior median is built from — while
"active-year count" is the project's name for `corridor_activity_history`
(src/tbml_common.py), which also counts missing-quantity prior years. The two
diverge for 4 of the 50 queue corridors (e.g. MYS→NPL gold 2022 shows 1 year
used vs 3 active prior years), so the old header understated corridor
activity. The hover ("Prior years used") and takeaway already labelled the
number correctly; only the header changed. Do not rename it back to
"active-year count" unless the column switches to `corridor_activity_history`.

## 2026-07-17 — Review Queue rework (filters, 9-column grid, amber current-case banner)

Stakeholder-facing UI rework of `app_pages/review_queue.py`. Ranking logic and
the queue-is-official contract untouched; every displayed number still comes
straight from `data/outputs/top_ranked_corridors.csv` (unit value and benchmark
price are published columns, not recomputed). Tests 47 → 53.

**Filters.** Removed: data-quality status, min-evidence, search, numeric top-N.
Kept: Year / Product family / Exporter / Importer. New `st.segmented_control`
"Queue size" (`key="queue_size"`, default "Top 50"). Data reality: the published
queue holds exactly **50 rows**, so "Top 500" is **inert, not fake-disabled** —
selecting it shows the same 50 rows and a governed caption explains the pipeline
publishes the top 50 (`queue_size_note`). A CSS-disabled segment was rejected:
`pointer-events:none` can't target one option reliably and could trap keyboard
focus; the Python cap (`top_n` via `nsmallest`) is honest and future-proof (if
the pipeline ever publishes ≥500, the control works for real — the option size
is parsed from the governed label so copy and behaviour cannot drift). Score
slider moved into a collapsed "Advanced filters" expander, key
`queue_score_range` unchanged (AppTest reaches it through the expander).

**Grid (9 columns, exact order):** Rank · Year · Corridor (`AAA → BBB`) ·
Product · Trade value (USD) · Quantity (metric tons) · Unit value (USD/t) ·
Benchmark price (USD/t) · Review-priority score. HS6 / Data quality / Evidence
count columns removed. `dashboard_metrics.queue_display_frame()` builds the
frame as a pure function (tests assert order, corridor format, clean product
label, rank stability under resort). Product shows the plain family label — an
earlier per-row "⚠ " caveat glyph was DROPPED at the user's request because
**45 of 50 published rows are `usable_with_caveat`**, so a glyph on 90 % of rows
was noise, not signal; per-observation caveats live on Selected Case Review, and
`quality_status` still rides the CSV export. Corridor codes include BACI
special partners (rank 26 = `USA → S19`, "Other Asia, nes") — shown as
published; the column help explains. Family→HS6 mapping lives in the Product
column help + under-table caption, derived live via `family_hs6_map()`.
Formats (glide can't do printf thousands separators): trade value + quantity
`"localized"` (grouped digits, ≤3 dp — values are integers / 3-dp tonnages, so
no noise), unit value + benchmark `"dollar"` (prices, cents meaningful), score
keeps the ProgressColumn `%.3f` (bars all sit ≥0.95 — the number, not the bar,
does the discriminating at Top-50 grain). Sorting stays numeric; full precision
is guaranteed in the CSV, stated in the caption. Missing benchmark would render
empty (none in the current queue).

**Selection & banner.** `st.dataframe` single-row selection kept — Streamlit
has NO row-click-anywhere; the grid's own checkbox-style selection column is
the row-pick affordance and cannot be hidden/configured (reported deviation).
The row pick is resolved BEFORE rendering by reading
`st.session_state[table_key].selection` (set by the click that triggered the
rerun), so the banner above the table never lags one interaction. Current case
= sticky `tbml_selected_obs_id` (bounds-checked against the full queue),
default = rank 1 (same default as Selected Case Review). Banner: amber card
(`st.container(key="queue_case_banner")`) — new tokens `palette.selected_bg
#FFF4CC` / `palette.selected_accent #D6A100` (amber = attention role). Ink on
the wash 11.87:1 AA; accent border decorative (2.1:1, fill+text identify the
banner); CTA `st.page_link` restyled as the teal primary pill (white on teal
3.93:1 = existing primary-button UI convention). Copy templates
`banner_default` / `banner_current` in content.yml; full country names from the
features join. The current-case row is tinted `selected_bg` via a pandas
Styler (per-row CSS can't reach the canvas grid; Styler backgrounds can) plus
zebra `table_stripe` on odd rows; when the grid's own selection is active its
translucent teal tint overlays the amber — acceptable (both mean "selected"),
chosen over dropping either cue. Banner text has a 260 ms rise-in (replays only
when the case changes — Streamlit only remounts changed DOM), registered in the
reduced-motion block.

**Export.** `Export current view (.csv)` sits right-aligned above the grid.
Contents via pure `queue_export_frame()`: current filters + queue size applied,
**always rank-ascending** — glide's client-side header sorting is not visible
to Python, so the export cannot follow an ad-hoc view sort (reported deviation,
disclosed in the caption). Columns: obs_id + the 9 display columns (product
without glyph) + quality_status + source_row_id + source_version, full
precision — keeps the old export's traceability guarantees in a stakeholder
shape.

**Score explainer** (verbatim, single YAML anchor for tooltip + note):
"The score combines several unusual-pattern signals to determine which
observations should be reviewed first. A higher score means higher review
priority—it is not the probability or a finding of financial crime."

## 2026-07-17 — Repalette to "Navy · Teal · Warm Amber" (supersedes "deep blue")

The all-blue "deep blue" plane read dull: too many surfaces shared one blue-grey
tone, so hierarchy was weak. New official direction keeps the institutional NAVY
(sidebar, headings, structure, the fixed boundary ribbon) but brightens the
canvas, makes cards TRULY WHITE so they lift on a soft shadow, uses TEAL as the
single interactive colour (links, selection, focus, primary action, chart
emphasis), and adds a warm AMBER caveat/attention counterpoint. Balance target
~70% neutral · 20% navy · 8% teal · 2% amber. All colour still lives in
`dashboard/config/dashboard_theme.yml`; `.streamlit/config.toml` kept in sync;
no page hardcodes a hex (pages reference tokens / CSS classes). WCAG + OKLab/
Machado CVD recomputed in Python (no Node).

Old → new token map (same keys cascade to every page; new keys added):

| Token | deep-blue | navy·teal·amber |
|---|---|---|
| `palette.ink` | `#23354D` | `#22314A` |
| `palette.muted` | `#505D76` | `#637087` (brief #68778E was 4.20:1 on the plane → darkened to AA) |
| `palette.page_bg` | `#CFDAE8` | `#F3F6FA` (brighter canvas) |
| `palette.panel_bg` | `#F8FBFE` | `#FFFFFF` (truly white cards) |
| `palette.border` | `#B9C8DE` | `#D5DFEA` |
| `palette.accent` | `#495B7D` Steel | `#0F8F8F` TEAL (fills/borders/icons/focus/chart emphasis) |
| `palette.accent_soft` | `#DCE5F2` | `#DDF4F1` (light teal) |
| `palette.ledger_ink` | `#3E4E68` | `#5A6B84` |
| `palette.sidebar_bg` | `#23354D` | `#1D2D46` (deep navy) |
| `palette.sidebar_ink` | `#EAF0F8` | `#F8FAFD` |
| `palette.sidebar_muted` | `#B7C6DE` | `#9FB0C8` |
| `palette.table_stripe` | `#EFF3FA` | `#EFF3F8` |
| **new** `palette.teal_500` | — | `#29B3AA` (accent lines: sidebar active rule, ribbon rule, mm rule) |
| **new** `palette.teal_hover` | — | `#0B7777` (button hover AND small teal TEXT on light, for AA) |
| **new** `palette.navy_700` | — | `#334966` (secondary/replay button text) |
| **new** `palette.sidebar_sel_bg` / `sidebar_hover_bg` | — | `#29405E` / `#243854` |
| **new** `palette.card_shadow` | — | `rgba(29,45,70,0.08)` (white-card lift) |
| **new** `palette.amber` / `amber_soft` | — | `#F2B544` / `#FFF3D8` (caveat/attention; decorative) |
| **new** `palette.btn_secondary_border` | — | `#7E8DA4` (brief #AEBBCB was 1.95:1 → darkened for a 3:1 control edge) |
| **new** `palette.kpi_{blue,teal,amber,green,violet}` | — | `#4078C0` `#0F8F8F` `#F2B544` `#2F9B78` `#7569B5` (KPI top-accents) |
| **new** `palette.src_{baci,worldbank,fatf}` | — | `#4078C0` `#0F8F8F` `#D89A2B` (source-role accents) |
| `boundary.bg` / `accent` / `ink` / `label` / `border` | `#495B7D`/`#8BA3C5`/`#F8FBFE`/`#DCE7F5`/`#3E5170` | `#1D2D46`/`#29B3AA`/`#F8FAFD`/`#DDF4F1`/`#16233A` (STAYS NAVY, teal top rule) |
| **new** `mental_model.{bg,accent,ink}` | — | `#223753` / `#29B3AA` / `#F8FAFD` |
| `families.crude_palm_oil` | `#2A78D6` | `#4D9B70` (green) |
| `families.refined_copper_cathodes` | `#1BAF7A` | `#B15C2E` (rust; brief #B86F3C nudged for CVD — see below) |
| `families.gold_unwrought` | `#EDA100` | `#D4A72C` (gold) |
| `evaluation.tint` / `border` | `#F3ECDA`/`#C2AA74` | `#FFF3D8`/`#D89A2B` (label_ink `#6E4E12` kept) |
| `status.quality.fully_usable` / `usable_with_caveat` | `#0A7D0A`/`#8A6D1D` | `#2F9B78`/`#D89A2B` |
| `status.severity.high` / `medium` | `#C23A3A`/`#C0622F` | `#C65D63`/`#D89A2B` (low `#8A6D1D` kept) |
| `chart.emphasis` | `#495B7D` | `#0F8F8F` (teal; dE 15.1 vs context_gray, kept) |
| `config.toml` primary/bg/2nd-bg/text | `#495B7D`/`#CFDAE8`/`#F8FBFE`/`#23354D` | `#0F8F8F`/`#F3F6FA`/`#FFFFFF`/`#22314A` |

Two teal roles: `accent` #0F8F8F (bright) for fills/borders/icons/focus/chart
emphasis (>=3:1 / large); `teal_hover` #0F8F8F→**#0B7777** for small teal TEXT on
light (5.4:1, AA) — eyebrows, KPI/stat labels, kickers, tags, step-pills, links,
CTA text. Arrows/connectors stay bright accent.

**CVD (OKLab dE ×100, Machado 1.0):** the weak pair is palm-vs-copper under
DEUTERanopia (the brief expected copper-gold, which is actually fine at 14.6).
Brief copper #B86F3C gave palm/copper deutan 6.5 (6–8 "floor, secondary-encoding
only"). Nudged copper #B86F3C → **#B15C2E** (redder rust, still commodity-true) →
palm/copper deutan **8.3** (≥8 target); palm/gold 17.1, copper/gold 18.6; all
normal-vision ≥18.8 (≥15 floor). Every family chart also pairs colour with a text
label (axis/legend), so the redundant-encoding guarantee holds regardless.

**WCAG:** every body-text pairing ≥4.5:1 (sidebar frost 6.3–13.3, teal-text
5.4/white, muted 4.6 plane / 5.0 white, eval label 6.9). Reported-not-blocking:
status-pill TEXT can sit below 4.5 by the project's documented "colour never
carries state alone" contract (lowest warning #D89A2B 2.45) — flagged for a
possible tinted-pill follow-up; src_fatf amber chip 2.45 on white carries an
inset ring (like the family dots); primary-button white-on-teal 3.93 (AA-large/UI
pass, below body 4.5 — hover #0B7777 is 5.4); the receded (0.90) eval lane-sub
fades to 3.77 by design (reduced-motion users see the 4.5 full-opacity state).

**Motion:** no new keyframes — recolour only, plus button/segment hover
transitions added to the SAME `prefers-reduced-motion` kill-block (kept last).
Sidebar active page now shows a teal `teal_500` left rule on a navy `sidebar_sel_bg`
fill (fixed 3px border, colour-only change → no layout shift). Buttons: Next =
teal primary, Previous = white/navy-outline secondary, Replay = pale-navy
(keyed `.st-key-dtrq_replay_btn`). Segmented control active segment = teal fill +
white text via `stBaseButton-segmented_controlActive` (active-vs-inactive).

Verified: `pytest tests -q` = **47 passed** (unchanged; no test asserts a colour);
all pages AppTest-render through the shell (styles applied) with no exception; live
server re-booted on 8501 with the new config → HTTP 200, clean Uvicorn log, 0
tracebacks. Rendered browser could not be visually inspected — the teal selection
states, white-card lift, KPI/source accents, button hierarchy and ribbon need the
user's eyes.

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
