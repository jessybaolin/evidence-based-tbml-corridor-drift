"""Build the Evidence-First TBML Technical Implementation Companion.

The source is intentionally separate from the legacy document under docs/.
This builder:

1. validates the headline claims against current project artefacts;
2. regenerates publication charts from current data;
3. renders LaTeX-style math to SVG;
4. converts the 38 explicit Markdown page sections to paged HTML/PDF;
5. checks page count, bookmarks, links, and searchable text.

Run from the repository root:

    .venv\\Scripts\\python.exe reports\\technical_companion\\build_technical_companion.py
"""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import markdown
import matplotlib
import numpy as np
import pandas as pd
from pypdf import PdfReader
from weasyprint import HTML

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = HERE / "technical_companion_source.md"
HTML_OUT = HERE / "technical_companion_source.html"
PDF_OUT = HERE / "technical_companion.pdf"
ASSETS = HERE / "assets"
MATH = ASSETS / "math"
QA_JSON = HERE / "technical_companion_build_verification.json"

PANEL = ROOT / "data" / "processed" / "corridor_product_year_panel.parquet"
FEATURES = ROOT / "data" / "processed" / "corridor_features.parquet"
QUEUE = ROOT / "data" / "outputs" / "top_ranked_corridors.csv"
MODEL_COMPARISON = ROOT / "data" / "outputs" / "model_comparison.csv"
SHAP = ROOT / "data" / "outputs" / "shap_summary_values.csv"

VERSION_DATE = date.today().strftime("%d %B %Y")
EXPECTED_PAGES = 38

NAVY = "#20324f"
NAVY_2 = "#304868"
INK = "#1f2f49"
MUTED = "#66758d"
LINE = "#d5deea"
CANVAS = "#f4f7fb"
TEAL = "#0b9797"
TEAL_SOFT = "#e5f5f3"
BLUE = "#4779c7"
BLUE_SOFT = "#edf3fc"
AMBER = "#d99b16"
AMBER_SOFT = "#fff4dc"
RED = "#a62e4e"
RED_SOFT = "#f9edf1"
PALM = "#4c9b70"
COPPER = "#b75b28"
GOLD = "#d5a21b"


def commit_hash() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
    ).strip()


def validate_claims() -> dict[str, object]:
    """Recompute the principal document facts and fail on drift."""
    panel = pd.read_parquet(PANEL)
    features = pd.read_parquet(FEATURES)
    queue = pd.read_csv(QUEUE)
    metrics = pd.read_csv(MODEL_COMPARISON)

    eligible = panel["model_eligible"].astype(bool)
    gold = panel[panel["family_id"] == "gold_unwrought"]
    gold_gap = gold[gold["quantity_metric_ton"].isna()]

    route_rows: list[dict[str, object]] = []
    for (exporter, importer), group in gold.groupby(
        ["exporter_iso3", "importer_iso3"], dropna=False
    ):
        route_rows.append(
            {
                "exporter": exporter,
                "importer": importer,
                "active_years": int(group["year"].nunique()),
                "gap_years": int(group["quantity_metric_ton"].isna().sum()),
                "gap_value": float(
                    group.loc[
                        group["quantity_metric_ton"].isna(), "trade_value_usd"
                    ].sum()
                ),
            }
        )
    routes = pd.DataFrame(route_rows)
    persistent = routes[
        (routes["active_years"] == 8) & (routes["gap_years"] == 8)
    ]

    test_hybrid = metrics[
        (metrics["split"] == "test")
        & (metrics["family_id"] == "all")
        & (metrics["model"] == "hybrid")
    ].iloc[0]
    test_xgb = metrics[
        (metrics["split"] == "test")
        & (metrics["family_id"] == "all")
        & (metrics["model"] == "xgboost")
    ].iloc[0]

    facts: dict[str, object] = {
        "commit": commit_hash(),
        "panel_rows": int(len(panel)),
        "eligible_rows": int(eligible.sum()),
        "eligible_value_share": float(
            panel.loc[eligible, "trade_value_usd"].sum()
            / panel["trade_value_usd"].sum()
        ),
        "feature_rows": int(len(features)),
        "queue_rows": int(len(queue)),
        "queue_family_counts": queue["family_id"].value_counts().to_dict(),
        "missing_quantity_rows": int(panel["quantity_metric_ton"].isna().sum()),
        "gold_missing_rows": int(len(gold_gap)),
        "gold_missing_value_share": float(
            gold_gap["trade_value_usd"].sum() / gold["trade_value_usd"].sum()
        ),
        "persistent_gold_routes": int(len(persistent)),
        "persistent_gold_value": float(persistent["gap_value"].sum()),
        "hybrid_precision_50": float(test_hybrid["precision_at_k"]),
        "hybrid_recall_50": float(test_hybrid["recall_at_k"]),
        "hybrid_lift_50": float(test_hybrid["lift_at_k"]),
        "hybrid_ap": float(test_hybrid["average_precision"]),
        "hybrid_hard_negative_fpr": float(
            test_hybrid["hard_negative_false_positive_rate"]
        ),
        "xgb_precision_50": float(test_xgb["precision_at_k"]),
    }

    assert facts["panel_rows"] == 25_844
    assert facts["eligible_rows"] == 23_656
    assert math.isclose(float(facts["eligible_value_share"]), 0.9992343682392455)
    assert facts["feature_rows"] == 25_844
    assert facts["queue_rows"] == 50
    assert facts["queue_family_counts"] == {
        "gold_unwrought": 18,
        "crude_palm_oil": 18,
        "refined_copper_cathodes": 14,
    }
    assert facts["missing_quantity_rows"] == 2_188
    assert facts["gold_missing_rows"] == 1_877
    assert math.isclose(float(facts["gold_missing_value_share"]), 0.0004148757843927828)
    assert facts["persistent_gold_routes"] == 14
    assert math.isclose(float(facts["persistent_gold_value"]), 1_000_119.0)
    assert math.isclose(float(facts["hybrid_precision_50"]), 0.48)
    assert math.isclose(float(facts["hybrid_recall_50"]), 0.2222222222222222)
    assert math.isclose(float(facts["hybrid_lift_50"]), 26.81333333333333)
    assert math.isclose(float(facts["hybrid_ap"]), 0.2978486730162115)
    assert math.isclose(float(facts["hybrid_hard_negative_fpr"]), 0.0)
    assert math.isclose(float(facts["xgb_precision_50"]), 0.50)
    return facts


def chart_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Aptos", "Segoe UI", "DejaVu Sans"],
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "axes.titleweight": 600,
            "axes.edgecolor": LINE,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "grid.color": "#e3e9f1",
            "grid.linewidth": 0.7,
        }
    )


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.savefig(
        ASSETS / name,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.close(fig)


def make_charts() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    MATH.mkdir(parents=True, exist_ok=True)
    chart_style()

    panel = pd.read_parquet(PANEL)
    queue = pd.read_csv(QUEUE)
    metrics = pd.read_csv(MODEL_COMPARISON)
    shap_values = pd.read_csv(SHAP)

    labels = {
        "gold_unwrought": "Gold",
        "refined_copper_cathodes": "Copper",
        "crude_palm_oil": "Palm oil",
    }
    colours = {
        "gold_unwrought": GOLD,
        "refined_copper_cathodes": COPPER,
        "crude_palm_oil": PALM,
    }

    # Coverage by year and family.
    counts = (
        panel.groupby(["year", "family_id"], as_index=False)
        .size()
        .rename(columns={"size": "rows"})
    )
    fig, ax = plt.subplots(figsize=(8.3, 3.3))
    for family in labels:
        subset = counts[counts["family_id"] == family]
        ax.plot(
            subset["year"],
            subset["rows"],
            marker="o",
            linewidth=2,
            color=colours[family],
            label=labels[family],
        )
    ax.set_title("Annual observation coverage remains broad across all three families")
    ax.set_xlabel("Year")
    ax.set_ylabel("Official observations")
    ax.grid(axis="y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    save_figure(fig, "coverage_by_year.png")

    # Population versus queue composition.
    population = panel["family_id"].value_counts(normalize=True)
    queued = queue["family_id"].value_counts(normalize=True)
    order = ["gold_unwrought", "refined_copper_cathodes", "crude_palm_oil"]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8.3, 3.35))
    w = 0.34
    ax.bar(
        x - w / 2,
        [100 * population.get(f, 0) for f in order],
        width=w,
        color="#b9c6d8",
        label="Full population",
    )
    ax.bar(
        x + w / 2,
        [100 * queued.get(f, 0) for f in order],
        width=w,
        color=[colours[f] for f in order],
        label="Top 50 queue",
    )
    ax.set_xticks(x, [labels[f] for f in order])
    ax.set_ylabel("Share of observations (%)")
    ax.set_title("The review queue is not a miniature copy of the population")
    ax.grid(axis="y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    save_figure(fig, "population_vs_queue.png")

    # Gold missing-quantity coverage: row share versus value share.
    family_rows = []
    for family, group in panel.groupby("family_id"):
        gap = group[group["quantity_metric_ton"].isna()]
        family_rows.append(
            {
                "family": family,
                "row_share": 100 * len(gap) / len(group),
                "value_share": 100
                * gap["trade_value_usd"].sum()
                / group["trade_value_usd"].sum(),
            }
        )
    gap_stats = pd.DataFrame(family_rows).set_index("family").loc[order]
    fig, axes = plt.subplots(1, 2, figsize=(8.3, 3.35))
    for ax, field, title in [
        (axes[0], "row_share", "Rows without usable quantity"),
        (axes[1], "value_share", "Trade value those rows represent"),
    ]:
        values = gap_stats[field]
        bars = ax.bar(
            [labels[f] for f in order],
            values,
            color=[colours[f] for f in order],
            width=0.62,
        )
        ax.set_title(title)
        ax.set_ylabel("Share within family (%)")
        ax.grid(axis="y")
        ax.spines[["top", "right"]].set_visible(False)
        for bar, value in zip(bars, values, strict=True):
            label = f"{value:.2f}%" if value >= 0.01 else f"{value:.4f}%"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                label,
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK,
            )
    fig.suptitle(
        "Gold has the largest record-level gap, but the excluded value is small",
        fontsize=11,
        fontweight=600,
    )
    fig.subplots_adjust(top=0.78, wspace=0.28)
    save_figure(fig, "gold_quantity_coverage.png")

    # Overall test comparison.
    test = metrics[
        (metrics["split"] == "test") & (metrics["family_id"] == "all")
    ].copy()
    model_order = ["rule", "logistic", "isolation", "xgboost", "hybrid"]
    display = {
        "rule": "Weighted sum",
        "logistic": "Logistic",
        "isolation": "Isolation Forest",
        "xgboost": "XGBoost",
        "hybrid": "Selected hybrid",
    }
    test = test.set_index("model").loc[model_order].reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(8.3, 3.5))
    c = ["#8190a7", "#8190a7", "#8190a7", RED, NAVY]
    axes[0].barh(
        [display[m] for m in test["model"]],
        100 * test["precision_at_k"],
        color=c,
    )
    axes[0].invert_yaxis()
    axes[0].set_title("Precision@50")
    axes[0].set_xlabel("Planted-pattern share of top 50 (%)")
    axes[0].grid(axis="x")
    axes[1].barh(
        [display[m] for m in test["model"]],
        test["lift_at_k"],
        color=c,
    )
    axes[1].invert_yaxis()
    axes[1].set_title("Lift@50")
    axes[1].set_xlabel("Times more concentrated than random")
    axes[1].grid(axis="x")
    for ax in axes:
        ax.spines[["top", "right", "left"]].set_visible(False)
    fig.suptitle(
        "Held-out 2023-2024 scenario test", fontsize=11, fontweight=600
    )
    fig.subplots_adjust(top=0.78, wspace=0.58)
    save_figure(fig, "model_test_comparison.png")

    # Family-level hybrid metrics.
    fam = metrics[
        (metrics["split"] == "test")
        & (metrics["model"] == "hybrid")
        & (metrics["family_id"] != "all")
    ].copy()
    fam["label"] = fam["family_id"].map(labels)
    fam = fam.set_index("family_id").loc[order].reset_index()
    x = np.arange(len(fam))
    fig, ax = plt.subplots(figsize=(8.3, 3.3))
    ax.bar(
        x - 0.18,
        100 * fam["precision_at_k"],
        width=0.36,
        color=RED,
        label="Precision@50",
    )
    ax.bar(
        x + 0.18,
        100 * fam["recall_at_k"],
        width=0.36,
        color=NAVY,
        label="Recall@50",
    )
    ax.set_xticks(x, fam["label"])
    ax.set_ylabel("Share (%)")
    ax.set_title("Performance differs materially by product family")
    ax.grid(axis="y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    save_figure(fig, "family_hybrid_performance.png")

    # Global SHAP.
    top_shap = shap_values.sort_values(
        "mean_abs_shap", ascending=True
    ).tail(10)
    fig, ax = plt.subplots(figsize=(8.3, 3.8))
    ax.barh(
        top_shap["feature_name"].str.replace("_", " "),
        top_shap["mean_abs_shap"],
        color=RED,
    )
    ax.set_title("Global XGBoost contribution summary")
    ax.set_xlabel("Mean absolute SHAP value")
    ax.grid(axis="x")
    ax.spines[["top", "right", "left"]].set_visible(False)
    save_figure(fig, "global_shap.png")

    # Bring current dashboard captures into the output bundle without altering them.
    capture_source = ROOT / "references" / "project_brief" / "assets"
    for name in [
        "dashboard_07_ranking_table.png",
        "dashboard_04_selected_case.png",
        "dashboard_05_bank_pathway.png",
        "dashboard_06_ai_prototype.png",
    ]:
        source = capture_source / name
        if source.exists():
            shutil.copy2(source, ASSETS / name)


def render_math_svg(tex: str, fontsize: float, name: str) -> Path:
    path = MATH / f"{name}.svg"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.patch.set_alpha(0)
    fig.text(
        0,
        0,
        f"${tex}$",
        fontsize=fontsize,
        math_fontfamily="stix",
        color=INK,
    )
    fig.savefig(
        path,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.02,
        transparent=True,
    )
    plt.close(fig)
    return path


def extract_math(text: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}
    counter = 0

    def display(match: re.Match[str]) -> str:
        nonlocal counter
        key = f"§§MATHD{counter}§§"
        svg = render_math_svg(
            match.group(1).strip(), 13.5, f"technical_companion_d{counter}"
        )
        mapping[key] = (
            f'<div class="math-display"><img src="{svg.relative_to(HERE).as_posix()}" '
            f'alt="{match.group(1).strip()}"></div>'
        )
        counter += 1
        return key

    def inline(match: re.Match[str]) -> str:
        nonlocal counter
        key = f"§§MATHI{counter}§§"
        svg = render_math_svg(
            match.group(1).strip(), 9.2, f"technical_companion_i{counter}"
        )
        mapping[key] = (
            f'<img class="math-inline" src="{svg.relative_to(HERE).as_posix()}" '
            f'alt="{match.group(1).strip()}">'
        )
        counter += 1
        return key

    text = re.sub(r"\$\$(.+?)\$\$", display, text, flags=re.S)
    text = re.sub(r"\$([^$\n]+?)\$", inline, text)
    return text, mapping


CSS = r"""
@page {
  size: A4;
  margin: 13mm 14mm 16mm;
  @bottom-left {
    content: "Evidence-First TBML Triage System | Technical Implementation Companion";
    font-family: "Aptos", "Segoe UI", Arial, sans-serif;
    font-size: 7pt;
    color: #718096;
  }
  @bottom-center {
    content: "Commit __COMMIT__";
    font-family: "Aptos", "Segoe UI", Arial, sans-serif;
    font-size: 7pt;
    color: #718096;
  }
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-family: "Aptos", "Segoe UI", Arial, sans-serif;
    font-size: 7pt;
    color: #718096;
  }
}
@page cover {
  margin: 13mm 14mm 13mm;
  @bottom-left { content: none; }
  @bottom-center { content: none; }
  @bottom-right { content: none; }
}

:root {
  --navy: #20324f;
  --navy2: #304868;
  --ink: #1f2f49;
  --muted: #66758d;
  --line: #d5deea;
  --canvas: #f4f7fb;
  --teal: #0b9797;
  --teal-soft: #e5f5f3;
  --blue: #4779c7;
  --blue-soft: #edf3fc;
  --amber: #d99b16;
  --amber-soft: #fff4dc;
  --red: #a62e4e;
  --red-soft: #f9edf1;
  --palm: #4c9b70;
  --copper: #b75b28;
  --gold: #d5a21b;
}

* { box-sizing: border-box; }
html { font-family: "Aptos", "Segoe UI", Arial, sans-serif; color: var(--ink); }
body {
  margin: 0;
  background: white;
  font-size: 8.75pt;
  line-height: 1.42;
  font-weight: 400;
}
.page {
  break-after: page;
  min-height: 257mm;
  position: relative;
}
.page:last-child { break-after: auto; }
.page.cover { page: cover; min-height: 271mm; }

h1 {
  margin: 0 0 3mm;
  color: var(--navy);
  font-size: 19pt;
  font-weight: 600;
  line-height: 1.13;
  letter-spacing: 0;
  bookmark-level: 1;
}
h2 {
  margin: 5.2mm 0 2.2mm;
  color: var(--navy);
  font-size: 12pt;
  font-weight: 600;
  line-height: 1.2;
  break-after: avoid;
  bookmark-level: 2;
}
h3 {
  margin: 3.8mm 0 1.5mm;
  color: var(--navy);
  font-size: 9.7pt;
  font-weight: 600;
  line-height: 1.25;
  break-after: avoid;
  bookmark-level: 3;
}
p { margin: 0 0 2.5mm; }
ul, ol { margin: 1.2mm 0 2.8mm; padding-left: 5mm; }
li { margin: 0 0 1mm; }
strong { color: var(--navy); font-weight: 600; }
a { color: var(--teal); text-decoration: none; }
code {
  font-family: Consolas, "SFMono-Regular", monospace;
  font-size: 7.6pt;
  background: #f0f3f7;
  padding: 0.3mm 0.8mm;
  border-radius: 0.7mm;
  overflow-wrap: anywhere;
  word-break: break-word;
}
pre {
  margin: 2.5mm 0;
  padding: 3mm;
  background: #f4f7fb;
  border: 0.6pt solid var(--line);
  border-radius: 1.5mm;
  font-size: 7.3pt;
  line-height: 1.35;
  white-space: pre-wrap;
  page-break-inside: avoid;
}
blockquote {
  margin: 4mm 0;
  padding: 3.5mm 4mm;
  border: 0.6pt solid #e4c3cd;
  border-left: 2.2mm solid var(--red);
  background: var(--red-soft);
  border-radius: 1.5mm;
  page-break-inside: avoid;
}
blockquote p { margin: 0; }

table {
  width: 100%;
  border-collapse: collapse;
  margin: 2.5mm 0 3mm;
  font-size: 7.4pt;
  line-height: 1.3;
  break-inside: avoid;
}
th {
  padding: 2mm 2.2mm;
  background: var(--navy);
  color: white;
  font-weight: 600;
  text-align: left;
  border-right: 0.4pt solid #7d8ca3;
}
td {
  padding: 1.8mm 2.2mm;
  vertical-align: top;
  border: 0.45pt solid #d9e1eb;
}
tr:nth-child(even) td { background: #f0f4f8; }
.compact-table table { font-size: 6.75pt; }
.compact-table th, .compact-table td { padding: 1.35mm 1.6mm; }
.tiny-table table { font-size: 6.1pt; line-height: 1.22; }
.tiny-table th, .tiny-table td { padding: 1.05mm 1.3mm; }

.eyebrow {
  color: var(--teal);
  font-size: 8pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 2.8mm;
}
.lede {
  color: var(--navy2);
  font-size: 10.1pt;
  line-height: 1.45;
  max-width: 175mm;
  margin-bottom: 4mm;
}
.small { color: var(--muted); font-size: 7.7pt; }
.note { color: var(--muted); font-size: 7.8pt; line-height: 1.35; }
.section-rule {
  width: 12mm;
  height: 1mm;
  background: var(--teal);
  border-radius: 1mm;
  margin: 0 0 4mm;
}
.page-label {
  color: var(--teal);
  font-size: 7.4pt;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 2.5mm;
}

.cover {
  background: linear-gradient(180deg, #ffffff 0%, #f4f7fb 100%);
  padding-top: 6mm;
}
.cover h1 { font-size: 30pt; max-width: 175mm; margin-top: 6mm; }
.cover .subtitle {
  color: var(--navy2);
  font-size: 15pt;
  font-weight: 500;
  margin: 1mm 0 7mm;
}
.cover .summary {
  max-width: 162mm;
  color: var(--muted);
  font-size: 11pt;
  line-height: 1.45;
}
.cover-identity {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 3mm;
  margin: 10mm 0 6mm;
}
.cover-id {
  min-height: 29mm;
  padding: 3.5mm;
  border: 0.65pt solid var(--line);
  border-top: 1.6mm solid var(--teal);
  border-radius: 1.8mm;
  background: white;
}
.cover-id.blue { border-top-color: var(--blue); }
.cover-id.amber { border-top-color: var(--amber); }
.cover-id.navy { border-top-color: var(--navy); }
.cover-id strong { display: block; font-size: 14pt; margin-bottom: 1.4mm; }
.cover-id span { color: var(--muted); font-size: 7.5pt; text-transform: uppercase; }
.cover-links {
  margin-top: 6mm;
  padding: 4mm;
  border: 0.6pt solid #bcdedb;
  border-radius: 1.8mm;
  background: var(--teal-soft);
  font-size: 8.5pt;
}

.toc-list { margin-top: 5mm; }
.toc-item {
  display: grid;
  grid-template-columns: 10mm 1fr 10mm;
  gap: 3mm;
  align-items: center;
  min-height: 17mm;
  padding: 2.5mm 3mm;
  border-bottom: 0.5pt solid var(--line);
  color: var(--ink);
}
.toc-item:first-child { border-top: 0.5pt solid var(--line); }
.toc-item > span { color: var(--teal); font-weight: 700; }
.toc-item strong { display: block; font-size: 9.2pt; }
.toc-item small { display: block; color: var(--muted); font-size: 7.4pt; }
.toc-item b { color: var(--muted); text-align: right; font-weight: 500; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 3mm;
  margin: 4mm 0;
}
.kpi {
  min-height: 31mm;
  padding: 3.2mm;
  border: 0.6pt solid var(--line);
  border-top: 1.5mm solid var(--teal);
  border-radius: 1.7mm;
  background: white;
}
.kpi.blue { border-top-color: var(--blue); }
.kpi.amber { border-top-color: var(--amber); }
.kpi.red { border-top-color: var(--red); }
.kpi strong { display: block; font-size: 17pt; line-height: 1.05; margin-bottom: 1.7mm; }
.kpi span { color: var(--muted); font-size: 7.2pt; text-transform: uppercase; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 3.5mm; margin: 3mm 0; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3mm; margin: 3mm 0; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.8mm; margin: 3mm 0; }
.card {
  padding: 3.5mm;
  border: 0.6pt solid var(--line);
  border-top: 1.3mm solid var(--teal);
  border-radius: 1.7mm;
  background: white;
  break-inside: avoid;
}
.card.blue { border-top-color: var(--blue); }
.card.amber { border-top-color: var(--amber); }
.card.red { border-top-color: var(--red); }
.card.navy { border-top-color: var(--navy); }
.card.palm { border-top-color: var(--palm); }
.card.copper { border-top-color: var(--copper); }
.card.gold { border-top-color: var(--gold); }
.card h3 { margin-top: 0; }
.card p:last-child, .card ul:last-child { margin-bottom: 0; }
.decision {
  margin: 3mm 0;
  padding: 3.2mm;
  background: var(--blue-soft);
  border: 0.6pt solid #c9d8ee;
  border-radius: 1.5mm;
  break-inside: avoid;
}
.decision strong { color: var(--blue); }
.status {
  display: inline-block;
  padding: 0.6mm 1.8mm;
  border-radius: 4mm;
  background: var(--teal-soft);
  color: #247d7d;
  font-size: 6.8pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.status.future { background: var(--amber-soft); color: #9b6d08; }

.flow {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5mm;
  margin: 5mm 0;
}
.flow.six { grid-template-columns: repeat(3, 1fr); row-gap: 6mm; }
.flow-node {
  position: relative;
  min-height: 34mm;
  padding: 3.4mm;
  border: 0.65pt solid #c8d6e9;
  border-top: 1.5mm solid var(--blue);
  border-radius: 1.7mm;
  background: #f8fafd;
  break-inside: avoid;
}
.flow-node.teal { border-top-color: var(--teal); background: #f4fbfa; }
.flow-node.amber { border-top-color: var(--amber); background: #fffbf2; }
.flow-node.red { border-top-color: var(--red); background: #fff7f9; }
.flow-node:not(:last-child)::after {
  content: "→";
  position: absolute;
  right: -4.4mm;
  top: 13mm;
  color: var(--teal);
  font-size: 13pt;
  font-weight: 600;
}
.flow.six .flow-node:nth-child(3)::after { content: ""; }
.flow.six .flow-node:nth-child(4)::before {
  content: "↓";
  position: absolute;
  top: -5.5mm;
  left: 50%;
  color: var(--teal);
  font-size: 13pt;
}
.flow-node b {
  display: block;
  color: var(--muted);
  font-size: 6.7pt;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 1.2mm;
}
.flow-node strong { display: block; font-size: 8.7pt; margin-bottom: 1.2mm; }
.flow-node small { color: var(--muted); font-size: 7.2pt; line-height: 1.3; }

.stack {
  display: flex;
  flex-direction: column;
  gap: 2mm;
  margin: 3mm 0;
}
.stack-row {
  display: grid;
  grid-template-columns: 34mm 1fr;
  gap: 3mm;
  padding: 2.5mm 3mm;
  border: 0.55pt solid var(--line);
  border-left: 1.7mm solid var(--teal);
  border-radius: 1.2mm;
  background: white;
  break-inside: avoid;
}
.stack-row strong { font-size: 8pt; }
.stack-row span { color: var(--muted); font-size: 7.7pt; }
.stack-row > * { min-width: 0; }

.figure {
  margin: 3mm 0;
  break-inside: avoid;
}
.figure img {
  display: block;
  width: 100%;
  max-height: 132mm;
  object-fit: contain;
  border: 0.7pt solid #bdc9d8;
  border-radius: 1.6mm;
  background: white;
}
.figure.compact img { max-height: 88mm; }
.figure.queue img { height: auto; max-height: 102mm; object-fit: contain; }
.figure.case img { height: 112mm; object-fit: cover; object-position: top; }
.caption {
  margin-top: 1.2mm;
  color: var(--muted);
  font-size: 7.2pt;
  line-height: 1.3;
}

.equation-box {
  padding: 3mm 4mm;
  background: #f5f7fa;
  border: 0.6pt solid var(--line);
  border-radius: 1.5mm;
  break-inside: avoid;
}
.math-display { text-align: center; margin: 2mm 0; break-inside: avoid; }
.math-display img { max-width: 92%; max-height: 13mm; }
.math-inline { vertical-align: -23%; max-height: 4mm; }

.matrix {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3mm;
  margin: 3mm 0;
}
.matrix > div {
  padding: 3.2mm;
  border-radius: 1.5mm;
  border: 0.6pt solid var(--line);
}
.matrix .do { background: var(--teal-soft); border-color: #b5ddda; }
.matrix .dont { background: var(--red-soft); border-color: #e6c6cf; }

.banner {
  display: flex;
  align-items: center;
  min-height: 24mm;
  padding: 4mm;
  border-radius: 1.8mm;
  background: var(--navy);
  color: white;
  break-inside: avoid;
}
.banner strong { color: white; }
.banner.red { background: var(--red); }
.banner.teal { background: #247d7d; }

.two-track {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 12mm minmax(0, 1fr);
  gap: 3mm;
  align-items: stretch;
  margin: 4mm 0;
}
.track {
  min-width: 0;
  padding: 3.5mm;
  border: 0.7pt solid var(--line);
  border-top: 1.7mm solid var(--blue);
  border-radius: 1.7mm;
  background: white;
}
.track.future { border-top-color: var(--amber); background: #fffbf2; }
.track-link {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--teal);
  font-size: 16pt;
  font-weight: 600;
}

.page-break-note {
  position: absolute;
  bottom: 2mm;
  left: 0;
  right: 0;
  color: var(--muted);
  font-size: 6.8pt;
}
""".replace("__COMMIT__", commit_hash())


def render_source() -> str:
    text = SOURCE.read_text(encoding="utf-8").replace(
        "{{SOURCE_COMMIT}}", commit_hash()
    )
    chunks = [chunk.strip() for chunk in text.split("<!-- PAGEBREAK -->")]
    if len(chunks) != EXPECTED_PAGES:
        raise ValueError(
            f"Expected {EXPECTED_PAGES} explicit page chunks, found {len(chunks)}"
        )

    rendered_pages: list[str] = []
    math_mapping: dict[str, str] = {}
    for index, chunk in enumerate(chunks, start=1):
        class_match = re.search(r"<!--\s*CLASS:\s*([^>]+?)\s*-->", chunk)
        page_class = class_match.group(1).strip() if class_match else ""
        chunk = re.sub(r"<!--\s*CLASS:\s*[^>]+?\s*-->", "", chunk)
        chunk, page_math = extract_math(chunk)
        math_mapping.update(page_math)
        body = markdown.markdown(
            chunk,
            extensions=[
                "tables",
                "fenced_code",
                "smarty",
                "toc",
                "attr_list",
                "md_in_html",
            ],
            output_format="html5",
        )
        for key, value in page_math.items():
            body = body.replace(key, value)
        body = re.sub(
            r"<p><em>((?:Figure|Table) .*?)</em></p>",
            r'<p class="caption"><em>\1</em></p>',
            body,
            flags=re.S,
        )
        rendered_pages.append(
            f'<section class="page page-{index} {page_class}">{body}</section>'
        )
    return "\n".join(rendered_pages)


def build() -> dict[str, object]:
    facts = validate_claims()
    make_charts()
    content = render_source()
    document = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='author' content='Jesslyn Guo Baolin'>"
        "<title>Evidence-First TBML Triage System | Technical Implementation Companion</title>"
        f"<style>{CSS}</style></head><body>{content}</body></html>"
    )
    HTML_OUT.write_text(document, encoding="utf-8")
    HTML(string=document, base_url=str(HERE)).write_pdf(PDF_OUT)

    reader = PdfReader(str(PDF_OUT))
    page_count = len(reader.pages)
    if page_count != EXPECTED_PAGES:
        raise ValueError(
            f"PDF page count is {page_count}; expected {EXPECTED_PAGES}. "
            "Inspect page overflow before accepting the build."
        )
    outline = reader.outline
    if not outline:
        raise ValueError("PDF bookmarks are missing")

    annotations = 0
    searchable_pages = 0
    for page in reader.pages:
        if (page.extract_text() or "").strip():
            searchable_pages += 1
        annotations += len(page.get("/Annots", []))
    if searchable_pages != page_count:
        raise ValueError("One or more PDF pages contain no searchable text")
    if annotations < 20:
        raise ValueError(
            f"Expected internal/external links, found only {annotations} annotations"
        )

    result = {
        "status": "pass",
        "generated_at": VERSION_DATE,
        "source_commit": facts["commit"],
        "page_count": page_count,
        "expected_page_count": EXPECTED_PAGES,
        "bookmarks_present": True,
        "link_annotations": annotations,
        "searchable_pages": searchable_pages,
        "headline_claims_validated": facts,
        "output": str(PDF_OUT.relative_to(ROOT)),
    }
    QA_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    verification = build()
    print(json.dumps(verification, indent=2))
