# Model card - Evidence-First TBML Corridor Drift Lab



Purpose: Document the review-priority scoring layer and its limits.



<div class='boundary'>This output prioritises an unusual corridor-product pattern for human review. It does not establish money laundering, misinvoicing, or criminal intent.</div>



## Intended use

Rank unusual exporter-importer-HS6-year patterns from official public aggregate data for human review.



## Prohibited use

Do not use model scores as proof of money laundering, misinvoicing, fraud, sanctions evasion, or criminal intent. Do not use this public aggregate panel as a customer-screening decision system.



## Data and labels

The training labels are controlled synthetic review-priority scenarios and hard negatives used for evaluation only. They are not confirmed TBML labels.



## Model candidates

Rules baseline, logistic regression baseline, XGBoost challenger, Isolation Forest side signal, and validation-selected hybrid score.



## Selection decision

Retained scoring approach: `hybrid_score` using challenger `xgboost`. Hybrid challenger weight chosen on validation only: `0.75`.



## Test-set metric summary

| model     |   precision_at_k |   recall_at_k |   lift_at_k |   average_precision |   hard_negative_false_positive_rate |
|:----------|-----------------:|--------------:|------------:|--------------------:|------------------------------------:|
| xgboost   |             0.5  |     0.231481  |    27.9306  |           0.306143  |                                   0 |
| hybrid    |             0.48 |     0.222222  |    26.8133  |           0.297849  |                                   0 |
| rule      |             0.14 |     0.0648148 |     7.82056 |           0.0996167 |                                   0 |
| logistic  |             0.06 |     0.0277778 |     3.35167 |           0.0770069 |                                   0 |
| isolation |             0.06 |     0.0277778 |     3.35167 |           0.0499403 |                                   0 |



## Interpretability

SHAP is used only as model-contribution context. It is not factual, causal, invoice-level, legal, or typology evidence.