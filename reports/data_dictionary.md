# Data dictionary

Purpose: Explain the key fields, units, and caveats used by the lab.

| field                              | meaning                                             | type           | caveat                                                      |
|:-----------------------------------|:----------------------------------------------------|:---------------|:------------------------------------------------------------|
| t                                  | BACI source year                                    | raw            | Source field retained.                                      |
| k / hs6                            | Six-character HS6 product code                      | raw / identity | Kept as string and zero-filled if needed.                   |
| i / exporter_code                  | BACI numeric exporter code                          | raw / identity | Mapped to ISO3 for display.                                 |
| j / importer_code                  | BACI numeric importer code                          | raw / identity | Mapped to ISO3 for display.                                 |
| v                                  | Trade value in thousands of current USD             | raw            | BACI unit.                                                  |
| q                                  | Quantity in metric tons                             | raw            | BACI unit; missing quantity blocks unit value.              |
| trade_value_usd                    | Nominal trade value in USD                          | derived        | `v * 1000`.                                                 |
| unit_value_usd_per_metric_ton      | Aggregate unit value                                | derived        | `trade_value_usd / quantity_metric_ton`; not invoice price. |
| benchmark_price_usd_per_metric_ton | World Bank benchmark on metric-ton basis            | derived        | Gold is converted from USD/troy ounce to USD/metric ton.    |
| benchmark_residual                 | Log unit value minus log benchmark                  | feature        | Macro context gap, not fair-value finding.                  |
| robust_historical_z                | Current log unit value vs prior corridor median/MAD | feature        | Uses prior years only.                                      |
| same_family_year_peer_percentile   | Same-year peer percentile                           | feature        | Compares to same HS6/family and year.                       |
| synthetic_review_priority          | Scenario evaluation target                          | label          | Separate from features; not a crime label.                  |
| selected_review_priority_score     | Final ranking score                                 | output         | Used for review queue only.                                 |
| evidence_id                        | Stable evidence row ID                              | output         | Links brief statements to recomputable facts.               |