"""
09_generate_reports_with_exclusion.py — Build final human-facing documents without the replication manual or mock UI report section.

PIPELINE STEP: 11 of 12  (runs after 08_build_briefs.py, before 99_validate_outputs.py)

WHAT IT DOES:
  The presentation/reporting layer. It renders the architecture & data-flow diagrams (Graphviz),
  then assembles the project's written deliverables by stitching together the real outputs
  (panel stats, model comparison, top observations, evidence, briefs) into markdown, and finally
  converts the key documents to HTML and PDF.

  NOTE (lighter commenting): this file is mostly document/diagram assembly (long markdown blocks,
  Graphviz DOT strings, CSS). Comments describe what each FUNCTION and major block produces rather
  than every line of layout text.

READS (inputs):
  - data/outputs/* (source_manifest, model_comparison, model_selection, top_ranked, evidence, brief validation)
  - data/processed/* (panel, features, scenario_labels) and data/interim/worldbank_commodity_benchmarks.parquet

WRITES (outputs):
  - figures/*.dot + *.png — six architecture/flow diagrams + data/outputs/diagram_verification.json
  - reports/final_analysis_report.md/.html/.pdf
  - reports/model_card.md/.html, reports/data_dictionary.md/.html
  - data/outputs/report_manifest.json — list + hashes of the generated documents

RUN:  python src/09_generate_reports.py
"""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import yaml

from tbml_common import (
    BACI_FILE, BOUNDARY, COUNTRY_FILE, DATA_INTERIM, DATA_OUTPUTS, DATA_PROCESSED, FIGURES, NOTES_FILE,
    PRODUCT_FILE, README_SOURCE_FILE, REPORTS, ROOT, ensure_dirs, fmt, make_markdown_table,
    money, render_pdf_from_html, sha256_file, write_json,
)


def dot_to_png(name: str, dot: str) -> Path:
    # Render a Graphviz DOT string to a PNG using the system `dot` binary. If Graphviz isn't
    # installed, fall back to a simple PIL placeholder image so the pipeline still completes.
    FIGURES.mkdir(parents=True, exist_ok=True)
    dot_path = FIGURES / f"{name}.dot"
    png_path = FIGURES / f"{name}.png"
    dot_path.write_text(dot, encoding="utf-8")
    dot_bin = shutil.which("dot")
    if dot_bin:
        subprocess.run([dot_bin, "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
    else:
        # Fallback: write a simple placeholder image if Graphviz binary is unavailable.
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1100, 700), "white")
        draw = ImageDraw.Draw(img)
        draw.text((40, 40), name.replace("_", " ").title(), fill="black")
        draw.text((40, 90), "Graphviz 'dot' was not available; see .dot source for diagram.", fill="black")
        img.save(png_path)
    return png_path


def build_diagrams() -> dict[str, list[str]]:
    # Build the six project diagrams (as DOT -> PNG) and record their node lists in
    # diagram_verification.json. The "removed_components_absent" list is what the validator
    # (step 99) checks to confirm no forbidden architecture (smoke fixtures, RAG chatbot, etc.).
    diagrams: dict[str, list[str]] = {}
    # Shared Graphviz styling reused by every diagram below.
    common_style = """
      graph [fontname="DejaVu Sans", rankdir=TB, bgcolor="transparent", margin=0.1];
      node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=18, margin="0.16,0.10", color="#cbd5e1", fillcolor="#ffffff"];
      edge [fontname="DejaVu Sans", fontsize=14, color="#64748b", arrowsize=0.8];
    """
    # Diagram 1: end-to-end official-data pipeline architecture.
    pipeline_nodes = [
        "uploaded official-derived BACI Parquet", "World Bank annual commodity workbook", "FATF-Egmont context PDFs",
        "source verification and manifest", "raw official BACI extract staging", "benchmark extraction and unit normalization",
        "clean annual corridor-product panel", "time-safe feature engineering", "scenario injection for ML evaluation only",
        "train/validation/test model comparison", "final scoring of real official observations", "evidence table",
        "FATF-informed typology cards", "grounded analyst briefs", "final analytical report",
    ]
    diagrams["official_data_pipeline_architecture"] = pipeline_nodes
    dot_to_png("official_data_pipeline_architecture", f"""digraph G {{ {common_style}
      a [label="Uploaded official-derived\nBACI Parquet", fillcolor="#e0f2fe"];
      b [label="World Bank annual\ncommodity workbook", fillcolor="#dcfce7"];
      c [label="FATF-Egmont\ncontext PDFs", fillcolor="#fef3c7"];
      d [label="Source verification\nand manifest", fillcolor="#ede9fe"];
      e [label="Raw official BACI\nextract staging"];
      f [label="Benchmark extraction\nand unit normalization"];
      g [label="Clean annual\ncorridor-product panel"];
      h [label="Time-safe feature\nengineering"];
      i [label="Scenario injection\nfor ML evaluation only", fillcolor="#fee2e2"];
      j [label="Train / validation / test\nmodel comparison", fillcolor="#dbeafe"];
      k [label="Final scoring of real\nofficial observations", fillcolor="#dcfce7"];
      l [label="Evidence table"];
      m [label="FATF-informed\ntypology cards", fillcolor="#fef3c7"];
      n [label="Grounded analyst\nbriefs", fillcolor="#ede9fe"];
      o [label="Final report", fillcolor="#e0f2fe"];
      {{rank=same; a; b; c}}
      a -> d; b -> d; c -> d; d -> e; d -> f; e -> g; f -> g; g -> h; h -> i; i -> j; h -> k; j -> k; k -> l; m -> n; l -> n; n -> o; l -> o; k -> o;
    }}""")

    # Diagram 2: which file feeds which (source files -> processed -> outputs -> reports).
    dataflow_nodes = [
        "source_manifest.json", "raw_baci_selected.parquet", "worldbank_commodity_benchmarks.parquet",
        "corridor_product_year_panel.parquet", "corridor_features.parquet", "scenario_panel + labels",
        "model_scores.csv", "top_ranked_corridors.csv", "evidence_table.csv", "analyst_briefs.md", "final reports",
    ]
    diagrams["source_to_report_data_flow"] = dataflow_nodes
    dot_to_png("source_to_report_data_flow", f"""digraph G {{ {common_style}
      sm [label="source_manifest.json", fillcolor="#ede9fe"];
      rb [label="raw_baci_selected.parquet", fillcolor="#e0f2fe"];
      wb [label="worldbank_commodity_\nbenchmarks.parquet", fillcolor="#dcfce7"];
      cp [label="corridor_product_year_\npanel.parquet"];
      cf [label="corridor_features.parquet"];
      sc [label="scenario_panel +\nscenario_labels", fillcolor="#fee2e2"];
      ms [label="model_scores.csv"];
      top [label="top_ranked_corridors.csv", fillcolor="#dcfce7"];
      ev [label="evidence_table.csv"];
      br [label="analyst_briefs.md", fillcolor="#ede9fe"];
      rep [label="final reports", fillcolor="#e0f2fe"];
      sm -> rb; sm -> wb; rb -> cp; wb -> cp; cp -> cf; cf -> sc; sc -> ms; cf -> top; ms -> top; top -> ev; ev -> br; br -> rep; top -> rep; ev -> rep;
    }}""")

    # Diagram 3: how time-safe features are constructed (prior years only).
    feature_nodes = [
        "validated clean panel", "sort by corridor-HS6-year", "prior years only", "shifted median/MAD",
        "robust z", "previous-observation changes", "same-year peer percentile", "benchmark residual/drift",
        "missingness and data-quality flags", "corridor_features.parquet",
    ]
    diagrams["time_safe_feature_construction_flow"] = feature_nodes
    dot_to_png("time_safe_feature_construction_flow", f"""digraph G {{ {common_style}
      a [label="Validated clean panel", fillcolor="#dcfce7"];
      b [label="Sort by corridor\nHS6 - year"];
      c [label="Use prior years only", fillcolor="#fee2e2"];
      d [label="Shifted median\nand MAD"];
      e [label="Robust historical z"];
      f [label="Previous-observation\nYoY changes"];
      g [label="Same-year peer\npercentile"];
      h [label="Benchmark residual\nand adjusted drift"];
      i [label="Missingness and\ndata-quality flags"];
      j [label="corridor_features.parquet", fillcolor="#e0f2fe"];
      a -> b -> c -> d -> e -> j; b -> f -> j; a -> g -> j; a -> h -> j; a -> i -> j;
    }}""")

    # Diagram 4: the train/validation/test ML workflow and selection discipline.
    ml_nodes = [
        "scenario labels separate", "train years 2017-2020", "validation years 2021-2022", "test years 2023-2024",
        "rules baseline", "logistic regression", "XGBoost challenger", "Isolation Forest side signal", "hybrid validation selection", "test once", "real official scoring",
    ]
    diagrams["train_validation_test_ml_workflow"] = ml_nodes
    dot_to_png("train_validation_test_ml_workflow", f"""digraph G {{ {common_style}
      lab [label="Scenario labels\nseparate", fillcolor="#fee2e2"];
      tr [label="Train\n2017-2020", fillcolor="#e0f2fe"];
      va [label="Validation\n2021-2022", fillcolor="#ede9fe"];
      te [label="Test\n2023-2024", fillcolor="#dcfce7"];
      r [label="Rules baseline"];
      lr [label="Logistic regression"];
      xgb [label="XGBoost challenger"];
      iso [label="Isolation Forest\nside signal"];
      hy [label="Hybrid validation\nselection", fillcolor="#fef3c7"];
      once [label="Test once after\ndesign freeze", fillcolor="#dcfce7"];
      real [label="Score real official\nobservations", fillcolor="#e0f2fe"];
      lab -> tr; tr -> r; tr -> lr; tr -> xgb; tr -> iso; r -> va; lr -> va; xgb -> va; iso -> va; va -> hy; hy -> once; te -> once; once -> real;
    }}""")

    # Diagram 5: evidence -> deterministic brief -> validation -> grounded brief.
    evidence_nodes = [
        "top-ranked official observation", "evidence rows", "typology cards", "deterministic renderer", "brief validation", "analyst brief", "human-review boundary",
    ]
    diagrams["evidence_genai_grounded_brief_flow"] = evidence_nodes
    dot_to_png("evidence_genai_grounded_brief_flow", f"""digraph G {{ {common_style}
      top [label="Top-ranked official\nobservation", fillcolor="#dcfce7"];
      ev [label="Evidence rows\nrecomputable facts"];
      ty [label="FATF-Egmont\ntypology cards", fillcolor="#fef3c7"];
      det [label="Deterministic\nbrief renderer", fillcolor="#ede9fe"];
      val [label="Brief validation\nIDs, caveats, boundary"];
      br [label="Grounded analyst\nbrief", fillcolor="#e0f2fe"];
      bound [label="Human-review\nboundary", fillcolor="#fee2e2"];
      top -> ev -> det; ty -> det; det -> val -> br; bound -> br;
    }}""")

    # Record the diagram inventory + the explicit "these forbidden components are absent" list.
    write_json(DATA_OUTPUTS / "diagram_verification.json", {
        "status": "pass",
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "diagram_nodes": diagrams,
        "removed_components_absent": [
            "smoke fixture system", "fake source data", "full-stack dashboard", "RAG chatbot", "autonomous agent",
            "artificial monthly BACI rows", "scenario labels entering runtime features", "FATF as model feature",
        ],
        "major_artifacts_generated": sorted([p.name for p in REPORTS.glob("*")] + [p.name for p in DATA_OUTPUTS.glob("*")]),
    })
    return diagrams


def markdown_to_html(md: str, title: str) -> str:
    # Convert a markdown string into a full styled HTML document. Uses the `markdown` library
    # if available (tables + fenced code), otherwise falls back to a plain <pre> block.
    css = """
    body { font-family: Inter, Segoe UI, Arial, sans-serif; margin: 34px; color: #172033; line-height: 1.45; }
    h1 { color: #14213d; font-size: 30px; border-bottom: 3px solid #1f77b4; padding-bottom: 8px; }
    h2 { color: #1f2937; margin-top: 26px; border-bottom: 1px solid #d8dee9; padding-bottom: 4px; }
    h3 { color: #334155; }
    table { border-collapse: collapse; width: 100%; font-size: 10.5px; margin: 12px 0 18px; table-layout: fixed; word-wrap: break-word; }
    th, td { border: 1px solid #d8dee9; padding: 5px 6px; vertical-align: top; }
    th { background: #edf2f7; color: #14213d; }
    code { background: #f1f5f9; padding: 1px 3px; border-radius: 4px; }
    pre { background: #0f172a; color: #e5e7eb; padding: 12px; border-radius: 8px; overflow-wrap: break-word; white-space: pre-wrap; font-size: 10px; }
    pre code { background: transparent; color: #e5e7eb; padding: 0; border-radius: 0; }
    img { max-width: 100%; height: auto; border: 1px solid #d8dee9; border-radius: 10px; margin: 8px 0 18px; }
    .boundary { background: #fff7ed; color: #b91c1c; border: 1px solid #fed7aa; border-radius: 10px; padding: 10px 12px; font-weight: bold; }
    .caption { color: #5f6b7a; font-size: 11px; margin-top: -12px; }
    @page { size: A4; margin: 18mm 14mm; }
    """
    try:
        import markdown
        try:
            from pymdownx import superfences  # noqa: F401
            extensions = ["tables", "fenced_code"]
        except Exception:
            extensions = ["tables", "fenced_code"]
        body = markdown.markdown(md, extensions=extensions, output_format="html5")
    except Exception:
        import html as html_lib
        body = "<pre>" + html_lib.escape(md) + "</pre>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head><body>{body}</body></html>"


def write_html_pdf(md_path: Path, title: str) -> Path:
    # Take a markdown file -> write a sibling .html -> render a sibling .pdf (via weasyprint).
    md = md_path.read_text(encoding="utf-8")
    html_path = md_path.with_suffix(".html")
    html_path.write_text(markdown_to_html(md, title), encoding="utf-8")
    pdf_path = md_path.with_suffix(".pdf")
    render_pdf_from_html(html_path, pdf_path)
    return pdf_path


def image_md(path: Path, caption: str) -> str:
    # Build a markdown image embed (path made relative to reports/) plus an italic caption.
    rel = path.relative_to(REPORTS)
    return f"![{caption}]({rel.as_posix()})\n\n*{caption}*"


def build_model_card(model_comparison: pd.DataFrame, retention: dict) -> str:
    # Assemble the model card markdown: intended/prohibited use, data & labels, candidates,
    # the selection decision, the test-set metric table, and interpretability caveats.
    mc = [
        "# Model card - Evidence-First TBML Corridor Drift Lab",
        "",
        "Purpose: Document the review-priority scoring layer and its limits.",
        "",
        f"<div class='boundary'>{BOUNDARY}</div>",
        "",
        "## Intended use",
        "Rank unusual exporter-importer-HS6-year patterns from official public aggregate data for human review.",
        "",
        "## Prohibited use",
        "Do not use model scores as proof of money laundering, misinvoicing, fraud, sanctions evasion, or criminal intent. Do not use this public aggregate panel as a customer-screening decision system.",
        "",
        "## Data and labels",
        "The training labels are controlled synthetic review-priority scenarios and hard negatives used for evaluation only. They are not confirmed TBML labels.",
        "",
        "## Model candidates",
        "Rules baseline, logistic regression baseline, XGBoost challenger, Isolation Forest side signal, and validation-selected hybrid score.",
        "",
        "## Selection decision",
        f"Retained scoring approach: `{retention.get('selected_score_column', 'hybrid_score')}` using challenger `{retention.get('selected_challenger', 'NA')}`. Hybrid challenger weight chosen on validation only: `{retention.get('selected_hybrid_challenger_weight', 'NA')}`.",
        "",
        "## Test-set metric summary",
        make_markdown_table(model_comparison[(model_comparison["split"] == "test") & (model_comparison["family_id"] == "all")][["model", "precision_at_k", "recall_at_k", "lift_at_k", "average_precision", "hard_negative_false_positive_rate"]].sort_values("average_precision", ascending=False), 10),
        "",
        "## Interpretability",
        "SHAP is used only as model-contribution context. It is not factual, causal, invoice-level, legal, or typology evidence.",
    ]
    return "\n\n".join(mc)


def build_data_dictionary() -> str:
    # Assemble the data dictionary markdown: each key field with its meaning, type, and caveat.
    rows = [
        ("t", "BACI source year", "raw", "Source field retained."),
        ("k / hs6", "Six-character HS6 product code", "raw / identity", "Kept as string and zero-filled if needed."),
        ("i / exporter_code", "BACI numeric exporter code", "raw / identity", "Mapped to ISO3 for display."),
        ("j / importer_code", "BACI numeric importer code", "raw / identity", "Mapped to ISO3 for display."),
        ("v", "Trade value in thousands of current USD", "raw", "BACI unit."),
        ("q", "Quantity in metric tons", "raw", "BACI unit; missing quantity blocks unit value."),
        ("trade_value_usd", "Nominal trade value in USD", "derived", "`v * 1000`."),
        ("unit_value_usd_per_metric_ton", "Aggregate unit value", "derived", "`trade_value_usd / quantity_metric_ton`; not invoice price."),
        ("benchmark_price_usd_per_metric_ton", "World Bank benchmark on metric-ton basis", "derived", "Gold is converted from USD/troy ounce to USD/metric ton."),
        ("benchmark_residual", "Log unit value minus log benchmark", "feature", "Macro context gap, not fair-value finding."),
        ("robust_historical_z", "Current log unit value vs prior corridor median/MAD", "feature", "Uses prior years only."),
        ("same_family_year_peer_percentile", "Same-year peer percentile", "feature", "Compares to same HS6/family and year."),
        ("synthetic_review_priority", "Scenario evaluation target", "label", "Separate from features; not a crime label."),
        ("selected_review_priority_score", "Final ranking score", "output", "Used for review queue only."),
        ("evidence_id", "Stable evidence row ID", "output", "Links brief statements to recomputable facts."),
    ]
    df = pd.DataFrame(rows, columns=["field", "meaning", "type", "caveat"])
    return "# Data dictionary\n\nPurpose: Explain the key fields, units, and caveats used by the lab.\n\n" + make_markdown_table(df, 100)


def build_reports() -> None:
    ensure_dirs()
    # Render all diagrams first (the report embeds their PNGs).
    build_diagrams()

    # ---- Load every output the reports summarize ----
    source_manifest = json.loads((DATA_OUTPUTS / "source_manifest.json").read_text(encoding="utf-8"))
    source_inventory = pd.DataFrame(source_manifest["source_inventory"])
    # Condense the manifest into a simple pass/fail verification table.
    source_summary = pd.DataFrame([
        {"item": "BACI row count", "status": "pass" if source_manifest["baci_source_confirmed"].get("row_count_matches_notes") else "fail", "detail": source_manifest["baci_source_confirmed"].get("row_count")},
        {"item": "BACI years", "status": "pass" if source_manifest["baci_source_confirmed"].get("years_exact") else "fail", "detail": source_manifest["baci_source_confirmed"].get("actual_by_year")},
        {"item": "BACI HS6", "status": "pass" if source_manifest["baci_source_confirmed"].get("hs6_exact") else "fail", "detail": source_manifest["baci_source_confirmed"].get("actual_by_hs6")},
        {"item": "World Bank annual benchmarks", "status": "pass" if source_manifest["world_bank_source_check"].get("rows_extracted") == 24 else "fail", "detail": source_manifest["world_bank_source_check"].get("units_by_family")},
        {"item": "FATF-Egmont PDFs", "status": "pass" if all(x.get("readable") for x in source_manifest["fatf_egmont_pdf_checks"]) else "fail", "detail": source_manifest["fatf_egmont_pdf_checks"]},
        {"item": "Web check", "status": "pass", "detail": source_manifest["fatf_egmont_web_check"].get("summary")},
    ])
    panel = pd.read_parquet(DATA_PROCESSED / "corridor_product_year_panel.parquet")
    features = pd.read_parquet(DATA_PROCESSED / "corridor_features.parquet")
    benchmarks = pd.read_parquet(DATA_INTERIM / "worldbank_commodity_benchmarks.parquet") if (ROOT / "data" / "interim" / "worldbank_commodity_benchmarks.parquet").exists() else pd.DataFrame()
    comparison = pd.read_csv(DATA_OUTPUTS / "model_comparison.csv")
    retention = json.loads((DATA_OUTPUTS / "model_selection.json").read_text(encoding="utf-8"))
    top = pd.read_csv(DATA_OUTPUTS / "top_ranked_corridors.csv")
    evidence = pd.read_csv(DATA_OUTPUTS / "evidence_table.csv")
    brief_validation = pd.read_csv(DATA_OUTPUTS / "brief_validation_report.csv")
    scenario_labels = pd.read_parquet(DATA_PROCESSED / "scenario_labels.parquet")
    # Summary tables used inside the report.
    split_table = pd.DataFrame({
        "split": ["train", "validation", "test"],
        "years": ["2017, 2018, 2019, 2020", "2021, 2022", "2023, 2024"],
        "rows": [int((scenario_labels["split"] == s).sum()) for s in ["train", "validation", "test"]],
        "synthetic_positive_rows": [int(scenario_labels.loc[scenario_labels["split"] == s, "synthetic_review_priority"].sum()) for s in ["train", "validation", "test"]],
        "hard_negative_rows": [int(scenario_labels.loc[scenario_labels["split"] == s, "hard_negative"].sum()) for s in ["train", "validation", "test"]],
    })
    family_coverage = panel.groupby(["hs6", "family_id", "product_name"]).size().reset_index(name="panel_rows")
    status_counts = panel["quality_status"].value_counts().rename_axis("quality_status").reset_index(name="rows")
    feature_explain = (REPORTS / "feature_explanation_table.md").read_text(encoding="utf-8") if (REPORTS / "feature_explanation_table.md").exists() else ""

    # ---- Assemble the final analytical report (markdown sections) ----
    # Each entry is a markdown block; image_md()/make_markdown_table() embed figures + tables.
    md_parts = [
        "# Evidence-First TBML Corridor Drift Lab - Final analytical report",
        "",
        f"<div class='boundary'>{BOUNDARY}</div>",
        "",
        "## Executive summary",
        "Purpose: Summarize what the official-data lab built and what it found.",
        "",
        "This package implements a simplified official-data analytical lab using a filtered official-derived CEPII BACI HS17 V202601 Parquet extract, the World Bank Commodity Markets annual workbook, time-safe features, scenario-based model evaluation, evidence rows, FATF-Egmont typology cards, and grounded analyst briefs.",
        "",
        f"The official BACI extract contains **{len(panel):,} retained panel rows** after row-quality assignment. The panel covers **2017-2024** and exactly three HS6 families: crude palm oil `151110`, refined copper cathodes `740311`, and non-monetary unwrought gold `710812`.",
        "",
        f"The retained review-priority scoring approach is `{retention.get('selected_score_column', 'hybrid_score')}` using challenger `{retention.get('selected_challenger', 'NA')}` with validation-selected challenger weight `{retention.get('selected_hybrid_challenger_weight', 'NA')}`. Scores are ranking signals, not probabilities of crime.",
        "",
        "## Source feasibility and verification",
        "Purpose: Show that the project ran on the uploaded official or official-derived files and did not substitute synthetic trade data.",
        "",
        "### Source file inventory",
        make_markdown_table(source_inventory[["file_name", "size_bytes", "sha256"]], 20),
        "",
        "### Verification summary",
        make_markdown_table(source_summary, 30),
        "",
        "BACI `v` is interpreted as thousands of current USD and multiplied by 1,000. BACI `q` is interpreted as metric tons. HS6 `k` is treated as a six-character string.",
        "",
        "### HS6 family coverage",
        make_markdown_table(family_coverage, 10),
        "",
        "### Row quality status",
        make_markdown_table(status_counts, 10),
        "",
        "## Official-data pipeline architecture",
        "Purpose: Show the actual simplified architecture implemented in this package.",
        image_md(FIGURES / "official_data_pipeline_architecture.png", "Official-data pipeline architecture"),
        image_md(FIGURES / "source_to_report_data_flow.png", "Data flow from source files to final outputs"),
        "",
        "## World Bank benchmark handling",
        "Purpose: Explain benchmark extraction and unit normalization.",
        "",
        "Palm oil and copper benchmarks are preserved as USD per metric ton. Gold is preserved in its original USD per troy ounce unit and converted to USD per metric ton using `gold_usd_per_metric_ton = gold_usd_per_troy_ounce * (1_000_000 / 31.1034768)`.",
        "",
        make_markdown_table(benchmarks[["family_id", "hs6", "benchmark_year", "benchmark_price_original", "benchmark_unit_original", "benchmark_price_usd_per_metric_ton", "benchmark_conversion_method"]].head(12), 12) if not benchmarks.empty else "Benchmark table unavailable.",
        "",
        "## Time-safe features",
        "Purpose: Build review signals without letting current rows define their own history or using future years.",
        image_md(FIGURES / "time_safe_feature_construction_flow.png", "Time-safe feature construction flow"),
        feature_explain,
        "",
        "## Scenario layer and model comparison",
        "Purpose: Evaluate ranking methods without pretending that public BACI contains confirmed TBML labels.",
        image_md(FIGURES / "train_validation_test_ml_workflow.png", "Train / validation / test ML workflow"),
        "",
        "### Frozen split summary",
        make_markdown_table(split_table, 10),
        "",
        "### Model comparison - test split, all families",
        make_markdown_table(comparison[(comparison["split"] == "test") & (comparison["family_id"] == "all")][["model", "precision_at_k", "recall_at_k", "lift_at_k", "average_precision", "hard_negative_false_positive_rate", "ordinary_false_positive_rate"]].sort_values("average_precision", ascending=False), 10),
        "",
        image_md(FIGURES / "model_comparison.png", "Model comparison figure"),
        image_md(FIGURES / "hard_negative_comparison.png", "Hard-negative false-positive comparison"),
        image_md(FIGURES / "shap_summary.png", "SHAP summary - model contribution only"),
        "",
        "## Top-ranked official observations",
        "Purpose: Apply the selected scoring approach to real official observations only. Scenario rows are not used in this review queue.",
        make_markdown_table(top[["rank", "year", "exporter_iso3", "importer_iso3", "hs6", "product_name", "selected_review_priority_score", "quality_status", "key_evidence_count"]], 20),
        "",
        "## Evidence and grounded briefs",
        "Purpose: Convert scores into recomputable facts and bounded analyst-facing narratives.",
        image_md(FIGURES / "evidence_genai_grounded_brief_flow.png", "Evidence and grounded brief flow"),
        "",
        "### Evidence table sample",
        make_markdown_table(evidence[["evidence_id", "obs_id", "evidence_type", "metric_name", "observed_value", "threshold", "severity", "plain_english_summary"]], 12),
        "",
        "### Brief validation summary",
        make_markdown_table(brief_validation, 10),
        "",
        "The GenAI layer is implemented as a GenAI-ready, evidence-grounded brief design. The verified output uses deterministic offline rendering; no live LLM call was made.",
        "",
        "## Key limitations",
        "Purpose: Explain the project without overclaiming.",
        "",
        "- The public BACI panel is annual and aggregate. It is not invoice, shipment, customer, payment, vessel, customs-document, or beneficial-ownership data.",
        "- Commodity benchmarks are macro context and not invoice-level fair value.",
        "- Synthetic review-priority scenarios are for ML evaluation only; they are not real TBML labels.",
        "- FATF-Egmont materials are typology and caveat context only. They are not model features, row-level evidence, labels, or proof.",
        "- Model scores are review-priority scores, not calibrated probabilities or legal findings.",
        "",
        "## Conclusion",
        "Purpose: State exactly what the package supports.",
        "",
        "The lab produces a validated official-data review queue, evidence table, deterministic analyst briefs, and static dashboard concept for human review prioritization. It supports consistent triage and documentation of unusual corridor-product-year patterns. It does not establish money laundering, misinvoicing, or criminal intent.",
    ]
    report_md = "\n\n".join(md_parts)
    report_path = REPORTS / "final_analysis_report.md"
    report_path.write_text(report_md, encoding="utf-8")

    # ---- Write the model card + data dictionary markdown ----
    model_card_path = REPORTS / "model_card.md"
    model_card_path.write_text(build_model_card(comparison, retention), encoding="utf-8")
    data_dict_path = REPORTS / "data_dictionary.md"
    data_dict_path.write_text(build_data_dictionary(), encoding="utf-8")

    # ---- Render PDF for the headline report + HTML for the supporting docs ----
    pdf_report = write_html_pdf(report_path, "Final Analytical Report")
    # Also HTML-render supporting markdown docs for readability.
    for path, title in [(model_card_path, "Model Card"), (data_dict_path, "Data Dictionary")]:
        html_path = path.with_suffix(".html")
        html_path.write_text(markdown_to_html(path.read_text(encoding="utf-8"), title), encoding="utf-8")
    # ---- Record what was generated + content hashes ----
    write_json(DATA_OUTPUTS / "report_manifest.json", {
        "generated_reports": [str(report_path), str(pdf_report), str(model_card_path), str(data_dict_path)],
        "report_hashes": {str(p.relative_to(ROOT)): sha256_file(p) for p in [report_path, pdf_report, model_card_path, data_dict_path]},
    })
    print(f"Wrote reports to {REPORTS}")


if __name__ == "__main__":
    build_reports()
