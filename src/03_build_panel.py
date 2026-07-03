"""Build the analysis panel dataset from ingested sources for the TBML corridor-drift pipeline."""

from __future__ import annotations

import pandas as pd

# build_panel is the workhorse; sha256_file stamps the panel with the source file's
# hash for provenance; read_baci_raw re-validates the staged BACI on the way in.
from tbml_common import BACI_FILE, DATA_INTERIM, DATA_PROCESSED, ensure_dirs, get_raw_path, read_baci_raw, sha256_file, build_panel


def main() -> None:
    ensure_dirs()

    # ---- Load the staged BACI rows ----
    # Prefer the interim staging copy from step 02; if it isn't there, read straight
    # from data/raw so this script can still run standalone.
    raw_path = DATA_INTERIM / "raw_baci_selected.parquet"
    raw = read_baci_raw(raw_path if raw_path.exists() else get_raw_path(BACI_FILE))


    # ---- Require the benchmark staging file ----
    # The panel joins World Bank prices, so step 02 must have run first.
    benchmarks = DATA_INTERIM / "worldbank_commodity_benchmarks.parquet"
    if not benchmarks.exists():
        raise FileNotFoundError("Run 02_ingest_official_sources.py before panel construction")
    benchmark_frame = pd.read_parquet(benchmarks)

    # ---- Build the panel + exclusion audit ----
    # build_panel returns (retained clean panel, audit of excluded/caveated rows).
    # The third argument is the source file hash, recorded on every panel row for lineage.
    panel, audit = build_panel(raw, benchmark_frame, sha256_file(get_raw_path(BACI_FILE)))

    # ---- Persist both tables ----
    panel.to_parquet(DATA_PROCESSED / "corridor_product_year_panel.parquet", index=False)
    panel.to_csv(DATA_PROCESSED / "panel.csv", index=False)
    audit.to_csv(DATA_PROCESSED / "exclusion_audit.csv", index=False)
    print(f"panel rows={len(panel):,}; audit/caveat rows={len(audit):,}")



if __name__ == "__main__":
    main()