"""
Extract raw data and convert it into interim Parquet files.

WHAT IT DOES:
  Reads the two official source files (the filtered CEPII BACI trade extract and the
  World Bank commodity benchmark workbook) and saves them as tidy Parquet "staging"
  copies. This is a deliberate raw->interim hand-off: only official columns are kept,
  units are normalized for the benchmarks, and NO analytical/derived fields are added
  yet. Keeping a faithful staged copy makes every later step reproducible and auditable.

READS (inputs):
  - data/raw/baci_hs17_v202601_selected_2017_2024_151110_740311_710812.parquet — annual trade flows
  - data/raw/CMO-Historical-Data-Annual.xlsx — World Bank "Pink Sheet" benchmark prices

WRITES (outputs):
  - data/interim/raw_baci_selected.parquet — normalized raw BACI fields (t,k,i,j,v,q)
  - data/interim/worldbank_commodity_benchmarks.parquet — annual benchmark prices in USD/metric ton

"""

from __future__ import annotations

# All heavy lifting lives in the shared library tbml_common.py; this script just
# wires the helpers together. read_baci_raw / extract_worldbank_benchmarks do the
# loading + validation; get_raw_path resolves files under data/raw/.
from tbml_common import (
    BACI_FILE, DATA_INTERIM, WORLD_BANK_FILE, ensure_dirs, extract_worldbank_benchmarks,
    get_raw_path, read_baci_raw,
)

def main() -> None:
    ensure_dirs()

    # ---- Stage the BACI trade extract ----
    # This staging copy preserves only official BACI fields. Derived fields are created later.
    # read_baci_raw enforces the 6 required columns and keeps HS6 (k) as a 6-char string.
    baci = read_baci_raw(get_raw_path(BACI_FILE))
    baci.to_parquet(DATA_INTERIM / "raw_baci_selected.parquet", index=False)

    # ---- Stage the World Bank commodity benchmarks ----
    # extract_worldbank_benchmarks parses the annual sheet and converts gold from
    # USD/troy-ounce to USD/metric-ton so it is comparable with BACI quantities.
    benchmarks = extract_worldbank_benchmarks(get_raw_path(WORLD_BANK_FILE))
    benchmarks.to_parquet(DATA_INTERIM / "worldbank_commodity_benchmarks.parquet", index=False)

    # Quick console receipt so a human can sanity-check the row counts after a run.
    print(f"wrote {len(baci):,} BACI rows and {len(benchmarks):,} benchmark rows")


if __name__ == "__main__":
    main()