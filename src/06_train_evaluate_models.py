"""
WHAT IT DOES:
  This is the modelling core. It builds five review-priority scorers and compares them with
  a strict time discipline (train 2017-2020, select on validation 2021-2022, look at test
  2023-2024 only once):
    - rule       : transparent, hand-weighted score from the features (auditable baseline)
    - logistic   : linear ML baseline
    - xgboost    : non-linear challenger
    - isolation  : unsupervised outlier score (side signal)
    - hybrid     : blend of the rule score and the best supervised challenger
  Models are trained/evaluated against the SYNTHETIC scenario labels (public BACI has no real
  labels). The winning hybrid is then applied to the REAL official observations to produce the
  review queue. Every score is a *ranking* signal, never a probability of crime.

READS (inputs):
  - data/processed/scenario_panel.parquet + scenario_labels.parquet — training/eval data
  - data/processed/corridor_features.parquet — the real observations to rank

WRITES (outputs):
  - data/outputs/model_scores.csv, model_comparison.csv, scenario_model_evaluation.csv
  - data/outputs/logistic_coefficients.csv, hybrid_validation_candidates.csv
  - data/outputs/xgboost_parameters.json, model_selection.json, model_bundle.joblib
  - data/outputs/top_ranked_corridors.csv — the official review queue (no synthetic rows)
  - data/outputs/shap_summary_values.csv + figures/{model_comparison,hard_negative_comparison,shap_summary}.png

"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from tbml_common import (
    DATA_OUTPUTS, DATA_PROCESSED, FIGURES, build_features, ensure_dirs, feature_columns,
    project_config, thresholds, write_json,
)


def bounded_abs(series: pd.Series, reference: float) -> pd.Series:
    # Normalize a feature into 0..1 by dividing |value| by a reference threshold and clipping.
    # This turns "how far past normal" into a comparable component for the rule score.
    return (series.abs() / reference).clip(0, 1).fillna(0.0)

def score_rules(features: pd.DataFrame) -> pd.DataFrame:
    # The transparent, fully auditable baseline scorer. It is a fixed weighted sum of normalized
    # feature "components" (history drift, benchmark gap, drift, year-over-year, divergence, peer
    # position, novelty, reactivation, valid-extreme), minus credits/penalties. All weights and
    # reference thresholds come from configs/thresholds.yml so the logic is inspectable.
    settings = thresholds()["rules"]
    out = features[["obs_id"]].copy()
    # Each component is a 0..1 signal; reference values set "how big is notable".
    out["rule_history_component"] = bounded_abs(features["robust_historical_z"], float(settings["robust_z_reference"]))
    out["rule_benchmark_residual_component"] = bounded_abs(features["benchmark_residual"], float(settings["benchmark_residual_reference"]))
    out["rule_benchmark_drift_component"] = bounded_abs(features["benchmark_adjusted_drift"], float(settings["benchmark_drift_reference"]))
    out["rule_yoy_component"] = bounded_abs(features["unit_value_yoy_change"], float(settings["yoy_reference"]))
    out["rule_divergence_component"] = bounded_abs(features["value_quantity_divergence"], float(settings["divergence_reference"]))
    # Peer percentile component = distance from the middle (0.5), scaled to 0..1.
    out["rule_peer_component"] = ((features["same_family_year_peer_percentile"] - 0.5).abs() * 2).clip(0, 1).fillna(0.0)
    out["rule_novelty_component"] = features["corridor_novelty_flag"].fillna(0).clip(0, 1).astype(float)
    out["rule_reactivation_component"] = features["corridor_reactivation_flag"].fillna(0).clip(0, 1).astype(float)
    out["rule_valid_extreme_component"] = features["valid_extreme_flag"].fillna(False).astype(float)
    # Credit for movement that is consistent with the benchmark (less suspicious); penalty for low data quality.
    consistency_credit = (
        1.0 - bounded_abs(
            features["benchmark_consistency_gap"],
            # 0.35 was the original fixed reference. The fallback preserves
            # that behaviour when an older thresholds file is still in use.
            float(settings.get("benchmark_consistency_reference", 0.35)),
        )
    ) * float(settings["benchmark_consistency_credit"])
    quality_penalty = ((6.0 - features["data_quality_score"].clip(0, 6)) / 6.0).fillna(1.0) * float(settings["quality_penalty_weight"])
    # Weighted sum of the positive components (weights are deliberately fixed and documented).
    positive = (
        float(settings["history_weight"]) * out["rule_history_component"]
        + float(settings["benchmark_residual_weight"]) * out["rule_benchmark_residual_component"]
        + float(settings["benchmark_drift_weight"]) * out["rule_benchmark_drift_component"]
        + float(settings["yoy_weight"]) * out["rule_yoy_component"]
        + float(settings["divergence_weight"]) * out["rule_divergence_component"]
        + float(settings["peer_weight"]) * out["rule_peer_component"]
        + float(settings["novelty_weight"]) * out["rule_novelty_component"]
        + float(settings["reactivation_weight"]) * out["rule_reactivation_component"]
        + float(settings["valid_extreme_weight"]) * out["rule_valid_extreme_component"]
    )
    # Rule scores are engineering ranking scores, not calibrated probabilities.
    out["rule_score"] = (positive - consistency_credit - quality_penalty).clip(0, 1)
    return out


def metric_at_k(frame: pd.DataFrame, score_col: str, k: int) -> dict[str, float | int]:
    # Evaluate a score by ranking rows and looking at the top k. Returns precision/recall/lift
    # at k, plus how many HARD NEGATIVES (unusual-but-benign) slipped into the top (a key
    # over-alerting guard), the ordinary false-positive rate, and average precision overall.
    # If I sort rows by this score, how good are the top k rows?

    # obs_id is only a tie-breaker. If two rows have the same score, sort them consistently by ID.
    ranked = frame.sort_values([score_col, "obs_id"], ascending=[False, True], kind="mergesort")
    k_eff = min(k, len(ranked))
    top = ranked.head(k_eff)

    # positives : how many synthetic review-priority rows exist
    # positives_top : how many synthetic positive rows appear in the top k
    positives = int(frame["synthetic_review_priority"].sum())
    positives_top = int(top["synthetic_review_priority"].sum())

    # precision@k: how clean the top-k queue is
    # recall@k: Of all positives available, how many did the top k catch?
    precision = positives_top / k_eff if k_eff else 0.0
    recall = positives_top / positives if positives else 0.0

    # prevalence: positive rate in the whole group
    # lift: how much better the top k is than random picking
    prevalence = positives / len(frame) if len(frame) else 0.0
    lift = precision / prevalence if prevalence > 0 else 0.0  # how much better than random


    # Hard negative: synthethic_review_priority = 0 & hard_negative = True
    # Will the scorer get fooled by something unusual-looking but benign
    # Ordinary Negatives are rows that are not synthetic positives, not hard negatives. Regular non-priority rows
    hard_total = int(frame["hard_negative"].sum())
    hard_top = int(top["hard_negative"].sum())

    # ordinary_total = number of normal non-priority rows
    ordinary_total = int(((frame["synthetic_review_priority"] == 0) & (~frame["hard_negative"])).sum())
    ordinary_top = int(((top["synthetic_review_priority"] == 0) & (~top["hard_negative"])).sum())
    try:
        # average precision: How good is the ranking across many possible thresholds, not only top k?
        ap = float(average_precision_score(frame["synthetic_review_priority"], frame[score_col]))
    except Exception:
        ap = float("nan")  # average precision is undefined if a split has only one class
    return {
        "n": int(len(frame)), "positives": positives, "k": int(k_eff),
        "precision_at_k": precision, "recall_at_k": recall, "lift_at_k": lift,
        "average_precision": ap,

        # of all hard-negative rows, what fraction apepared in the top-k list?
        # the false positive means hard negative have true label, synthetic_Review_priority = 0 so they are not supposed to appear on top
        "hard_negative_false_positive_rate": hard_top / hard_total if hard_total else 0.0,
        "ordinary_false_positive_rate": ordinary_top / ordinary_total if ordinary_total else 0.0,
    }


def evaluate(scored: pd.DataFrame, score_cols: list[str], k: int) -> pd.DataFrame:
    # Compute metric_at_k for every (split, family, model) combination. "all" aggregates
    # across the three commodity families. Only validation + test splits are scored here.
    rows = []
    for split in ["validation", "test"]:
        split_frame = scored[scored["split"] == split]
        # Create a list for fam in ["all", "gold", "palm oil", "copper"]
        for fam in ["all"] + sorted(split_frame["family_id"].unique().tolist()):
            group = split_frame if fam == "all" else split_frame[split_frame["family_id"] == fam]
            if group.empty:
                continue
            # score columns: rule_score, logistic_score, xgbost_score, isolation_score, hybrid_score
            for col in score_cols:
                # For this split, this family, and this score column, compute the metrics and store them as one row.
                rows.append({"split": split, "family_id": fam, "model": col.replace("_score", ""), **metric_at_k(group, col, min(k, len(group)))})
    return pd.DataFrame(rows)


def fit_models(scenario_features: pd.DataFrame, labels: pd.DataFrame):
    # Train the supervised + unsupervised models on the TRAIN split only, tuning XGBoost on
    # validation. Labels are joined here (they live in a separate file) and only model-eligible
    # rows are used.

    cols = feature_columns()
    data = scenario_features.merge(labels, on=["obs_id", "year", "family_id"], validate="one_to_one")
    data = data[data["model_eligible"]].copy()

    # Build the train/validation matrices from the time-based split.
    x_train = data.loc[data["split"] == "train", cols].astype(float)
    y_train = data.loc[data["split"] == "train", "synthetic_review_priority"].astype(int)
    x_val = data.loc[data["split"] == "validation", cols].astype(float)
    y_val = data.loc[data["split"] == "validation", "synthetic_review_priority"].astype(int)
    if y_train.nunique() < 2 or y_val.nunique() < 2:
        raise ValueError("Train and validation splits need both positive and negative scenario labels")

    # ---- Logistic baseline: median-impute -> standardize -> balanced logistic regression ----
    logistic = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear", random_state=project_config()["primary_seed"])),
    ])
    logistic.fit(x_train, y_train)

    # ---- XGBoost challenger: try 3 small/regularized configs, keep the best on validation AP ----
    neg = max(1, int((y_train == 0).sum()))
    pos = max(1, int((y_train == 1).sum()))
    candidates = []
    for params in [
        {"max_depth": 2, "learning_rate": 0.06, "min_child_weight": 2.0, "reg_lambda": 4.0},
        {"max_depth": 3, "learning_rate": 0.05, "min_child_weight": 4.0, "reg_lambda": 6.0},
        {"max_depth": 2, "learning_rate": 0.09, "min_child_weight": 6.0, "reg_lambda": 8.0},
    ]:
        model = XGBClassifier(
            n_estimators=160, objective="binary:logistic", eval_metric="aucpr", tree_method="hist",
            subsample=0.9, colsample_bytree=0.9, reg_alpha=0.15, scale_pos_weight=neg / pos,  # scale_pos_weight handles class imbalance
            random_state=project_config()["primary_seed"], n_jobs=1, **params,
        )
        model.fit(x_train, y_train, eval_set=[(x_val, y_val)], verbose=False)
        val_score = model.predict_proba(x_val)[:, 1]
        ap = average_precision_score(y_val, val_score)
        candidates.append((ap, params, model))

    # Best validation average precision wins (ties broken deterministically by params).
    candidates.sort(key=lambda item: (-item[0], tuple(sorted(item[1].items()))))
    xgb = candidates[0][2]

    # ---- Isolation Forest: unsupervised outlier detector (side signal only) ----
    iso = Pipeline([("imputer", SimpleImputer(strategy="median")), ("model", IsolationForest(n_estimators=160, random_state=project_config()["primary_seed"], n_jobs=1))])
    iso.fit(x_train)

    # ---- Logistic coefficients (for transparency) sorted by absolute influence ----
    transformed_names = logistic.named_steps["imputer"].get_feature_names_out(cols)
    coefs = pd.DataFrame({"transformed_feature": transformed_names, "coefficient": logistic.named_steps["model"].coef_[0]})
    coefs = coefs.sort_values("coefficient", key=np.abs, ascending=False, kind="mergesort")
    return data, cols, logistic, xgb, iso, candidates, coefs


# Create a dataframe made of ml_model scores.
def add_model_scores(features: pd.DataFrame, cols: list[str], logistic, xgb, iso) -> pd.DataFrame:
    # Apply the three fitted ML models to produce per-row scores.
    x = features[cols].astype(float)
    out = features[["obs_id"]].copy()
    out["logistic_score"] = logistic.predict_proba(x)[:, 1]
    out["xgboost_score"] = xgb.predict_proba(x)[:, 1]
    # Isolation Forest: negate decision_function so "more anomalous" = higher, then min-max to 0..1.
    raw = -iso.decision_function(x)
    mn, mx = float(np.min(raw)), float(np.max(raw))
    out["isolation_score"] = 0.0 if np.isclose(mn, mx) else (raw - mn) / (mx - mn)
    return out


def main() -> None:
    ensure_dirs()
    cfg = project_config()
    top_k = int(cfg["top_k"])

    # ---- Build scenario features + fit all models ----
    scenario_panel = pd.read_parquet(DATA_PROCESSED / "scenario_panel.parquet") # datasets that were modified
    labels = pd.read_parquet(DATA_PROCESSED / "scenario_labels.parquet")

    # Recompute features on the scenario panel (same time-safe logic as the official panel).
    scenario_features = build_features(scenario_panel)
    scenario_features.to_parquet(DATA_PROCESSED / "scenario_features.parquet", index=False)

    # model_data comes from scenario_features.merge(labels, on=["obs_id", "year", "family_id"], validate="one_to_one")
    # and model_eligible == 1
    model_data, cols, logistic, xgb, iso, xgb_candidates, coefs = fit_models(scenario_features, labels)


    # ---- Score every eligible scenario row with all four base scorers ----
    eligible_features = scenario_features[scenario_features["model_eligible"]].copy()
    base = eligible_features[["obs_id", "year", "family_id", "hs6", "exporter_iso3", "importer_iso3", "product_name"]].merge(labels, on=["obs_id", "year", "family_id"], validate="one_to_one")
    rule_scores = score_rules(eligible_features)     # score for weighted sum average
    ml_scores = add_model_scores(eligible_features, cols, logistic, xgb, iso)
    scored = base.merge(rule_scores, on="obs_id", validate="one_to_one").merge(ml_scores, on="obs_id", validate="one_to_one")
    score_cols = ["rule_score", "logistic_score", "xgboost_score", "isolation_score"]
    initial_metrics = evaluate(scored, score_cols, top_k)
    print(initial_metrics)
    #base.to_parquet(data_profiling / "ml_model_base.parquet", index=False)
    #rule_scores.to_parquet(data_profiling / "ml_model_rule_scores.parquet", index=False)


    # ---- Pick the supervised challenger on VALIDATION only ----
    validation_all = initial_metrics[(initial_metrics["split"] == "validation") & (initial_metrics["family_id"] == "all")]
    selection_settings = thresholds()["model_selection"]
    challenger_metric = str(selection_settings["challenger_metric"])
    hybrid_metric = str(selection_settings["hybrid_metric"])
    supported_metrics = {"precision_at_k", "recall_at_k", "lift_at_k", "average_precision"}
    if challenger_metric not in supported_metrics or hybrid_metric not in supported_metrics:
        raise ValueError("Unsupported model-selection metric in configs/thresholds.yml")

    # Select the supervised challenger across the full validation ranking, with
    # hard-negative FPR as a secondary guardrail.
    supervised = validation_all[validation_all["model"].isin(["logistic", "xgboost"])].sort_values(
        [challenger_metric, "hard_negative_false_positive_rate"],
        ascending=[False, True], kind="mergesort"
    )
    selected_challenger = str(supervised.iloc[0]["model"])
    selected_col = f"{selected_challenger}_score"  #xgboost_score


    # ---- Pick the hybrid blend weight on VALIDATION only ----
    # Try each configured weight w: hybrid = (1-w)*rule + w*challenger; keep the best on validation.
    candidates = []
    for w in selection_settings["hybrid_weights"]:
        col = f"hybrid_candidate_{w:.2f}"
        scored[col] = (1 - float(w)) * scored["rule_score"] + float(w) * scored[selected_col]
        metrics = metric_at_k(scored[scored["split"] == "validation"], col, top_k)
        candidates.append({"challenger_weight": float(w), **metrics})
    # The operational queue has a fixed review capacity, so the blend is chosen
    # on validation precision@k. Average precision remains a deterministic
    # tie-breaker, followed by the more rules-heavy blend.
    hybrid_sort = [hybrid_metric, "hard_negative_false_positive_rate"]
    hybrid_ascending = [False, True]
    if hybrid_metric != "average_precision":
        hybrid_sort.append("average_precision")
        hybrid_ascending.append(False)
    hybrid_sort.append("challenger_weight")
    hybrid_ascending.append(True)
    hybrid_table = pd.DataFrame(candidates).sort_values(
        hybrid_sort, ascending=hybrid_ascending, kind="mergesort")
    selected_weight = float(hybrid_table.iloc[0]["challenger_weight"])
    scored["hybrid_score"] = (1 - selected_weight) * scored["rule_score"] + selected_weight * scored[selected_col]
    score_cols.append("hybrid_score")


    # ---- Final evaluation (now including the test split) + write all model artifacts ----
    metrics = evaluate(scored, score_cols, top_k)
    scored.to_csv(DATA_OUTPUTS / "model_scores.csv", index=False)
    metrics.to_csv(DATA_OUTPUTS / "model_comparison.csv", index=False)
    metrics.to_csv(DATA_OUTPUTS / "scenario_model_evaluation.csv", index=False)
    coefs.to_csv(DATA_OUTPUTS / "logistic_coefficients.csv", index=False)
    hybrid_table.to_csv(DATA_OUTPUTS / "hybrid_validation_candidates.csv", index=False)
    write_json(DATA_OUTPUTS / "xgboost_parameters.json", {
        "selected_parameters": xgb_candidates[0][1],
        "validation_average_precision": float(xgb_candidates[0][0]),
        "tested_parameters": [{"average_precision": float(ap), **params} for ap, params, _ in xgb_candidates],
    })


    # Record exactly what was selected and the safe-language statement about the scores.
    selection = {
        "selected_challenger": selected_challenger, #xgb
        "selected_challenger_score_column": selected_col, #xgb_score
        "selected_hybrid_challenger_weight": selected_weight, #hybrid
        "selected_score_column": "hybrid_score",
        "selection_split": "validation",
        "challenger_selection_metric": challenger_metric,
        "hybrid_selection_metric": hybrid_metric,
        "score_language": "Scores are review-priority ranking scores, not calibrated probabilities of crime.",
    }
    write_json(DATA_OUTPUTS / "model_selection.json", selection)


    # Persist the fitted models + selection so scoring is reproducible without re-training.
    joblib.dump({"feature_columns": cols, "logistic": logistic, "xgboost": xgb, "isolation": iso, "selection": selection}, DATA_OUTPUTS / "model_bundle.joblib")


    # ---- Apply the selected hybrid to the REAL official observations ----
    # Score the real official observations. This ranking excludes synthetic scenario rows entirely.
    official_features = pd.read_parquet(DATA_PROCESSED / "corridor_features.parquet")
    official_eligible = official_features[official_features["model_eligible"]].copy()
    official_rule = score_rules(official_eligible)
    official_ml = add_model_scores(official_eligible, cols, logistic, xgb, iso) # Compute prediction
    official_scores = official_eligible.merge(official_rule, on="obs_id", validate="one_to_one").merge(official_ml, on="obs_id", validate="one_to_one")
    official_scores["selected_challenger_score"] = official_scores[selected_col] #xgb score

    # The final review-priority score uses the same hybrid weight chosen on validation.
    official_scores["selected_review_priority_score"] = (1 - selected_weight) * official_scores["rule_score"] + selected_weight * official_scores[selected_col]
    # Take the top-k highest-scoring official rows as the review queue.
    top = official_scores.sort_values(["selected_review_priority_score", "obs_id"], ascending=[False, True], kind="mergesort").head(top_k).copy()
    top.insert(0, "rank", range(1, len(top) + 1))
    top["key_evidence_count"] = 0  # placeholder; step 07 fills this in with real evidence counts
    top_cols = [
        "rank", "obs_id", "year", "exporter_iso3", "importer_iso3", "hs6", "family_id", "product_name",
        "trade_value_usd", "quantity_metric_ton", "unit_value_usd_per_metric_ton", "benchmark_price_usd_per_metric_ton",
        "selected_review_priority_score", "rule_score", "selected_challenger_score", "quality_status", "data_quality_score",
        "valid_extreme_flag", "key_evidence_count", "source_row_id", "source_version",
    ]
    top[top_cols].to_csv(DATA_OUTPUTS / "top_ranked_corridors.csv", index=False)

     # ---- Figures: model comparison + hard-negative guard + SHAP contributions ----
    FIGURES.mkdir(parents=True, exist_ok=True)
    val_plot = metrics[(metrics["split"] == "test") & (metrics["family_id"] == "all")].copy()
    # Bar chart: average precision per model on the test split.
    plt.figure(figsize=(8, 4.8))
    plt.bar(val_plot["model"], val_plot["average_precision"])
    plt.title("Scenario test average precision by model")
    plt.ylabel("Average precision")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "model_comparison.png", dpi=180)
    plt.close()

    # Bar chart: hard-negative false-positive rate per model (lower = less over-alerting).
    plt.figure(figsize=(8, 4.8))
    plt.bar(val_plot["model"], val_plot["hard_negative_false_positive_rate"])
    plt.title("Scenario test hard-negative false-positive rate")
    plt.ylabel("Hard-negative FPR @ top-k")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / "hard_negative_comparison.png", dpi=180)
    plt.close()

    # SHAP contribution summary for the XGBoost challenger. This is model contribution, not legal or factual evidence.
    # Overall: which features mattered most across many rows?
    # Row-level: which features pushed this specific row's score up or down?
    sample = official_eligible.sort_values("obs_id", kind="mergesort").sample(n=min(500, len(official_eligible)), random_state=cfg["primary_seed"])
    x_sample = sample[cols].astype(float)
    explainer = shap.TreeExplainer(xgb)
    shap_values = explainer.shap_values(x_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    # Mean absolute SHAP per feature = average contribution magnitude; keep the top 15.
    mean_abs = np.abs(shap_values).mean(axis=0)
    shap_df = pd.DataFrame({"feature_name": cols, "mean_abs_shap": mean_abs}).sort_values("mean_abs_shap", ascending=False).head(15)
    shap_df.to_csv(DATA_OUTPUTS / "shap_summary_values.csv", index=False)
    plt.figure(figsize=(8, 5.5))
    plt.barh(shap_df["feature_name"][::-1], shap_df["mean_abs_shap"][::-1])
    plt.title("XGBoost challenger SHAP contribution summary")
    plt.xlabel("Mean |SHAP value|")
    plt.tight_layout()
    plt.savefig(FIGURES / "shap_summary.png", dpi=180)
    plt.close()
    print(json.dumps(selection, indent=2))


if __name__ == "__main__":
    main()
