"""Verify availability and integrity of official source data for the TBML corridor-drift pipeline.

WHAT IT DOES:
  Source verification is the project's "chain of custody". Before any analysis, it:
    - hashes every input file (SHA-256) into an inventory,
    - confirms the BACI extract matches its data_source_notes.json (years, HS6 families,
      row counts, required columns, and that it is official-derived, not synthetic),
    - parses the World Bank workbook and records benchmark units + the gold conversion,
    - confirms the two FATF-Egmont PDFs are READABLE (they are typology *context* only —
      never used as data, features, or evidence).
  The combined result is written to source_manifest.json, which later steps and the
  validator trust as the authoritative description of the inputs.

READS (inputs):
  - data/raw/* (BACI parquet, data_source_notes.json, World Bank xlsx, FATF PDFs, code lookups)

WRITES (outputs):
  - data/outputs/source_file_inventory.csv — file names, sizes, and SHA-256 hashes
  - data/outputs/source_manifest.json — full verification record (BACI/notes/benchmark/PDF checks)


"""

from __future__ import annotations

import json

import pandas as pd
from pypdf import PdfReader  # used only to confirm the FATF PDFs open and contain text

from tbml_common import (
    BACI_FILE, BOUNDARY, DATA_OUTPUTS, FATF_2020_FILE, FATF_2021_FILE,
    NOTES_FILE, WORLD_BANK_FILE, ensure_dirs, extract_worldbank_benchmarks, get_raw_path,
    input_inventory, read_baci_raw, read_json, sha256_file, source_notes_check,
    validate_baci_against_notes, write_json,
)

def check_pdf_readable(filename: str) -> dict[str, object]:
    # Open a FATF-Egmont PDF and pull text from up to the first 3 pages. We only need to
    # confirm it is a real, readable document (the project uses these as typology context,
    # so "readable" is the only requirement — we never parse them for analytical data).
    path = get_raw_path(filename)
    reader = PdfReader(str(path))
    pages = len(reader.pages)
    sample_text = ""
    for i in range(min(3, pages)):
        sample_text += reader.pages[i].extract_text() or ""
    return {
        "file_name": filename,
        # Consider it readable if it has pages and yielded a non-trivial amount of text.
        "readable": pages > 0 and len(sample_text.strip()) > 20,
        "pages": pages,
        "sample_text_length_first_pages": len(sample_text.strip()),
    }

def main() -> None:
    ensure_dirs()

    # ---- 1. Inventory + hash every declared input file ----
    inventory = input_inventory()
    inventory.to_csv(DATA_OUTPUTS / "source_file_inventory.csv", index=False)

    # ---- 2. Validate the BACI extract against its provenance notes ----
    # data_source_notes.json records the expected years/HS6/row counts; these helpers
    # confirm the actual parquet matches and that the notes say "official-derived, not synthetic".
    notes = read_json(get_raw_path(NOTES_FILE))
    baci = read_baci_raw(get_raw_path(BACI_FILE))
    baci_checks = validate_baci_against_notes(baci, notes)
    notes_checks = source_notes_check(notes)

    # ---- 3. Parse the World Bank workbook + summarize benchmarks ----
    # Confirms the expected "Annual Prices (Nominal)" sheet exists and records the units per
    # commodity plus the gold troy-ounce -> metric-ton conversion factor (1,000,000 / 31.1034768).
    wb_path = get_raw_path(WORLD_BANK_FILE)
    workbook = pd.ExcelFile(wb_path)
    benchmarks = extract_worldbank_benchmarks(wb_path)
    benchmark_summary = {
        "sheet_names": workbook.sheet_names,
        "annual_sheet_found": "Annual Prices (Nominal)" in workbook.sheet_names,
        "rows_extracted": int(len(benchmarks)),
        "years": sorted(benchmarks["benchmark_year"].unique().astype(int).tolist()),
        "units_by_family": benchmarks.groupby("family_id")["benchmark_unit_original"].first().to_dict(),
        "gold_conversion_factor": 1_000_000 / 31.1034768,
        # Spot-check one converted value (gold, 2024) so a reviewer can eyeball the unit math.
        "gold_2024_usd_per_metric_ton": float(benchmarks.loc[(benchmarks["family_id"] == "gold_unwrought") & (benchmarks["benchmark_year"] == 2024), "benchmark_price_usd_per_metric_ton"].iloc[0]),
    }

    # ---- 4. Confirm the FATF-Egmont PDFs are readable (typology context only) ----
    pdf_checks = [check_pdf_readable(FATF_2020_FILE), check_pdf_readable(FATF_2021_FILE)]

    # ---- 5. Assemble + write the source manifest ----
    # This single JSON is the authoritative "what are our inputs and are they valid" record.
    # BOUNDARY embeds the project's non-overclaiming conclusion sentence into the manifest.
    source_manifest = {
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "project_boundary": BOUNDARY,
        "source_inventory": inventory.to_dict(orient="records"),
        "baci_source_confirmed": {
            "expected_file": BACI_FILE,
            "sha256": sha256_file(get_raw_path(BACI_FILE)),
            **baci_checks,  # merge in the year/HS6/row-count check results
        },
        "data_source_notes_checks": notes_checks,
        "data_source_notes_payload": notes,
        "world_bank_source_check": benchmark_summary,
        "fatf_egmont_pdf_checks": pdf_checks,
        "fatf_egmont_web_check": {
            "status": "manual_web_check_recorded_in_reports",
            "summary": "Web search found official FATF pages for the 2020 trends report and 2021 risk indicators; no newer official TBML-specific replacement was identified during this run.",
        },
    }
    write_json(DATA_OUTPUTS / "source_manifest.json", source_manifest)

    # Console summary of the headline checks.
    print(json.dumps({
        "inventory_rows": len(inventory),
        "baci_row_count": baci_checks["row_count"],
        "baci_counts_match_notes": baci_checks["row_count_matches_notes"],
        "benchmark_rows": benchmark_summary["rows_extracted"],
        "pdf_checks": pdf_checks,
    }, indent=2))


if __name__ == "__main__":
    main()
