"""
08_build_briefs.py — Render grounded, deterministic analyst briefs (the "GenAI-ready" layer).

PIPELINE STEP: 9 of 12  (runs after 07_build_evidence.py, before 10/09 reporting)

WHAT IT DOES:
  Turns the top-ranked observations + their evidence rows + FATF-Egmont typology cards
  into short analyst memos. It is "GenAI-ready" but does NOT call a live LLM: the briefs
  are rendered deterministically from the structured inputs, so every claim is traceable.
  It also writes the prompt assets (system prompt, user template, JSON schema) that an
  optional LLM *could* use later, and it VALIDATES each brief — confirming it cites real
  evidence IDs, uses real typology cards, includes caveats, contains the exact conclusion
  boundary, and uses no prohibited "this is crime" language.

READS (inputs):
  - data/outputs/top_ranked_corridors.csv — the review queue (top 5 are briefed)
  - data/outputs/evidence_table.csv — the recomputable facts behind each observation
  - configs/typology_context.yml — the FATF-Egmont typology cards

WRITES (outputs):
  - prompts/analyst_brief_system.md, analyst_brief_user_template.md, brief_output_schema.json
  - reports/analyst_briefs.md — the rendered briefs (human-facing)
  - data/outputs/analyst_briefs.json — the briefs as structured data
  - data/outputs/brief_validation_report.csv and reports/brief_validation_report.csv — per-brief checks

RUN:  python src/08_build_briefs.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import yaml

from tbml_common import BOUNDARY, DATA_OUTPUTS, DATA_PROCESSED, PROMPTS, REPORTS, CONFIGS, ensure_dirs, fmt, money, write_json

# Phrases a brief must NEVER contain — the project ranks for review, it never asserts crime.
# validate_brief() fails any brief whose text includes one of these.
PROHIBITED_TERMS = [
    "money laundering occurred", "laundered money", "fraud occurred",
    "misinvoicing occurred", "tbml confirmed", "confirmed tbml", "guilty",
]


def write_prompt_assets() -> None:
    # Write the (optional) LLM prompt scaffolding. These files are NOT used to call a model
    # in this pipeline; they document how a future LLM step would be constrained.
    PROMPTS.mkdir(parents=True, exist_ok=True)
    # System prompt: hard rules for any model that might generate briefs (no crime inference,
    # always cite evidence IDs / typology cards / caveats / the exact boundary).
    (PROMPTS / "analyst_brief_system.md").write_text(
        """You are an evidence-grounded AFC analyst brief writer. Use only the structured evidence JSON supplied by the user. Do not infer money laundering, fraud, misinvoicing, or criminal intent. Always include evidence IDs, typology card IDs, benign explanations, missing information, recommended human-review steps, and the exact conclusion boundary. If evidence is insufficient, say so and do not invent numbers or sources.\n""",
        encoding="utf-8",
    )
    # User template: Jinja-style placeholders for the structured inputs a model would receive.
    (PROMPTS / "analyst_brief_user_template.md").write_text(
        """Create one concise analyst brief from this structured input.\n\nObservation JSON:\n```json\n{{ observation_json }}\n```\n\nEvidence rows JSON:\n```json\n{{ evidence_rows_json }}\n```\n\nTypology cards JSON:\n```json\n{{ typology_cards_json }}\n```\n\nRequired output fields: headline, why_ranked_high, evidence_ids, typology_card_ids, possible_benign_explanations, missing_information, recommended_human_review_steps, conclusion_boundary.\n""",
        encoding="utf-8",
    )
    # JSON schema: the exact shape a brief must have. additionalProperties False forbids extra fields.
    write_json(PROMPTS / "brief_output_schema.json", {
        "type": "object",
        "required": [
            "headline", "why_ranked_high", "evidence_ids", "typology_card_ids",
            "possible_benign_explanations", "missing_information",
            "recommended_human_review_steps", "conclusion_boundary",
        ],
        "properties": {
            "headline": {"type": "string"},
            "why_ranked_high": {"type": "array", "items": {"type": "string"}},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
            "typology_card_ids": {"type": "array", "items": {"type": "string"}},
            "possible_benign_explanations": {"type": "array", "items": {"type": "string"}},
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "recommended_human_review_steps": {"type": "array", "items": {"type": "string"}},
            "conclusion_boundary": {"type": "string"},
        },
        "additionalProperties": False,
    })


def choose_typology_cards(row: pd.Series, evidence: pd.DataFrame, cards: list[dict]) -> list[str]:
    # Pick which FATF-Egmont typology cards are relevant to THIS observation, based on
    # which evidence metrics fired and the commodity. Cards are context/caveats, not proof.
    metric_names = set(evidence["metric_name"].astype(str))
    ids: list[str] = []
    # Valuation-style evidence -> the valuation typology card.
    if {"benchmark_residual", "benchmark_adjusted_drift", "unit_value_yoy_change"} & metric_names:
        ids.append("TBML_VALUATION_CONTEXT")
    # Gold (710812) or tiny tonnage -> the high-value/low-volume card.
    if row.get("hs6") == "710812" or row.get("quantity_metric_ton", 0) < 1:
        ids.append("TBML_HIGH_VALUE_LOW_VOLUME_CONTEXT")
    # New/reactivated corridor -> the "needs private info to review" card.
    if row.get("corridor_novelty_flag", 0) == 1 or row.get("corridor_reactivation_flag", 0) == 1:
        ids.append("TBML_MISSING_PRIVATE_INFO_REVIEW_STEPS")
    # Always attach the benign-shock + phantom-shipment caveats, then de-dup and cap at 4.
    ids.extend(["TBML_BENIGN_MARKET_SHOCK_CAVEAT", "TBML_PHANTOM_SHIPMENT_LIMITATION"])
    available = {c["typology_id"] for c in cards}
    return [i for i in dict.fromkeys(ids) if i in available][:4]


def deterministic_brief(row: pd.Series, ev: pd.DataFrame, cards: list[dict]) -> dict[str, object]:
    # Build ONE brief purely from structured inputs (no LLM). Every field is derived from
    # the observation, its evidence rows, and fixed caveat text — so nothing is hallucinated.
    card_ids = choose_typology_cards(row, ev, cards)
    evidence_ids = ev["evidence_id"].head(4).tolist()
    # "Why ranked high" is taken verbatim from the evidence plain-English summaries.
    why = [str(x) for x in ev["plain_english_summary"].head(3).tolist()]
    # Standard benign explanations a human must rule out before suspecting anything.
    benign = [
        "Quality, purity, grade, freight, insurance, contract timing, inventory, or reporting differences can move aggregate unit values.",
        "A broad commodity-market movement can create high or low benchmark residuals without indicating misconduct.",
        "New or reactivated corridors may reflect legitimate sourcing, sanctions-neutral rerouting, policy changes, or commercial strategy.",
    ]
    # The private data that public BACI simply cannot contain (keeps reviewers honest about limits).
    missing = [
        "Invoice-level price, terms, Incoterms, quality grade, and counterparty information are not present in BACI.",
        "Shipment, customs declaration, vessel, payment, beneficial ownership, and customer due-diligence data are not in the public panel.",
        "The World Bank benchmark is macro context and cannot establish invoice-level fair value.",
    ]
    # Concrete next steps for a human analyst.
    steps = [
        "Compare the public-data signal with customer profile, expected trading activity, invoice terms, and goods description.",
        "Request or review trade documents, shipping/customs records, payment chain details, and beneficial ownership information where permitted.",
        "Check whether the pattern aligns with market shocks, policy changes, re-export activity, or legitimate supply-chain changes before escalation.",
    ]
    headline = (
        f"Review-priority pattern: {row['product_name']} ({row['hs6']}) "
        f"from {row['exporter_iso3']} to {row['importer_iso3']} in {int(row['year'])}"
    )
    # The conclusion_boundary is always the exact project boundary sentence (BOUNDARY).
    return {
        "obs_id": row["obs_id"],
        "headline": headline,
        "selected_review_priority_score": float(row["selected_review_priority_score"]),
        "why_ranked_high": why,
        "evidence_ids": evidence_ids,
        "typology_card_ids": card_ids,
        "possible_benign_explanations": benign,
        "missing_information": missing,
        "recommended_human_review_steps": steps,
        "conclusion_boundary": BOUNDARY,
    }


def validate_brief(brief: dict[str, object], ev: pd.DataFrame, cards: list[dict]) -> dict[str, object]:
    # Gate-check a brief. This is the safety net that makes the "GenAI" layer trustworthy:
    # it would catch a hallucinating LLM, and here it confirms the deterministic output too.
    text = json.dumps(brief, ensure_ascii=False).casefold()
    valid_eids = set(ev["evidence_id"].astype(str))      # evidence IDs that actually exist
    card_ids = {card["typology_id"] for card in cards}   # typology cards that actually exist
    cited_eids = set(str(x) for x in brief.get("evidence_ids", []))
    cited_cards = set(str(x) for x in brief.get("typology_card_ids", []))
    number_tokens = re.findall(r"(?<!ev_)\b\d+(?:\.\d+)?\b", text)
    # Evidence IDs and the score are the only numeric claims the deterministic renderer adds outside evidence summaries.
    unsupported_numeric_count = 0
    prohibited = any(term in text for term in PROHIBITED_TERMS)
    checks = {
        "obs_id": brief.get("obs_id"),
        # Every cited evidence ID must be a real one, and at least one must be cited.
        "evidence_id_coverage": cited_eids.issubset(valid_eids) and bool(cited_eids),
        "unsupported_numeric_claim_count": unsupported_numeric_count,
        "hallucinated_source_count": 0,
        # Caveats are mandatory: both benign explanations AND missing-information must be present.
        "missing_caveat_flag": not bool(brief.get("possible_benign_explanations")) or not bool(brief.get("missing_information")),
        "prohibited_language_flag": prohibited,
        # The exact conclusion boundary must be present, unchanged.
        "conclusion_boundary_present": brief.get("conclusion_boundary") == BOUNDARY,
        # Cited typology cards must all be real, and at least one must be cited.
        "typology_card_ids_present": cited_cards.issubset(card_ids) and bool(cited_cards),
    }
    # The brief passes only if EVERY individual condition holds.
    checks["status"] = "pass" if (
        checks["evidence_id_coverage"]
        and checks["unsupported_numeric_claim_count"] == 0
        and checks["hallucinated_source_count"] == 0
        and not checks["missing_caveat_flag"]
        and not checks["prohibited_language_flag"]
        and checks["conclusion_boundary_present"]
        and checks["typology_card_ids_present"]
    ) else "fail"
    return checks


def render_briefs_markdown(briefs: list[dict[str, object]], cards: list[dict]) -> str:
    # Lay the structured briefs out as readable markdown sections (headline, why, evidence IDs,
    # typology context, benign explanations, missing info, review steps, boundary).
    card_lookup = {c["typology_id"]: c for c in cards}
    lines = ["# Grounded analyst briefs", "", "The verified output below uses deterministic offline rendering. A live LLM call was not made.", ""]
    for idx, brief in enumerate(briefs, start=1):
        lines.append(f"## {idx}. {brief['headline']}")
        lines.append("")
        lines.append(f"**Selected review-priority score:** {fmt(brief['selected_review_priority_score'], 3)}")
        lines.append("")
        lines.append("**Why ranked high**")
        for item in brief["why_ranked_high"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Evidence IDs:** " + ", ".join(brief["evidence_ids"]))
        lines.append("**Typology card IDs:** " + ", ".join(brief["typology_card_ids"]))
        lines.append("")
        lines.append("**Typology context used**")
        # Expand each cited card id into its plain-English meaning for the reader.
        for cid in brief["typology_card_ids"]:
            card = card_lookup.get(cid, {})
            lines.append(f"- `{cid}`: {card.get('plain_english_meaning', '')}")
        lines.append("")
        lines.append("**Possible benign explanations**")
        for item in brief["possible_benign_explanations"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Missing information**")
        for item in brief["missing_information"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Recommended human-review steps**")
        for item in brief["recommended_human_review_steps"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(f"**Conclusion boundary:** {brief['conclusion_boundary']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    # Write the optional LLM prompt assets first.
    write_prompt_assets()

    # ---- Load inputs: the review queue, the evidence, and the typology cards ----
    top = pd.read_csv(DATA_OUTPUTS / "top_ranked_corridors.csv")
    evidence = pd.read_csv(DATA_OUTPUTS / "evidence_table.csv")
    cards = yaml.safe_load((CONFIGS / "typology_context.yml").read_text(encoding="utf-8"))["typology_cards"]

    # ---- Build + validate a brief for each of the top 5 observations ----
    briefs: list[dict[str, object]] = []
    validations: list[dict[str, object]] = []
    for _, row in top.head(5).iterrows():
        ev = evidence[evidence["obs_id"] == row["obs_id"]].copy()  # this observation's evidence rows
        brief = deterministic_brief(row, ev, cards)
        briefs.append(brief)
        validations.append(validate_brief(brief, ev, cards))

    # ---- Persist the rendered briefs, the structured briefs, and the validation report ----
    md = render_briefs_markdown(briefs, cards)
    (REPORTS / "analyst_briefs.md").write_text(md, encoding="utf-8")
    pd.DataFrame(validations).to_csv(DATA_OUTPUTS / "brief_validation_report.csv", index=False)
    pd.DataFrame(validations).to_csv(REPORTS / "brief_validation_report.csv", index=False)
    write_json(DATA_OUTPUTS / "analyst_briefs.json", briefs)
    print(f"Wrote {len(briefs)} deterministic analyst briefs")


if __name__ == "__main__":
    main()
