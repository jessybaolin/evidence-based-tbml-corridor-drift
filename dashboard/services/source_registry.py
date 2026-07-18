"""
Official data-source registry for the Data Dictionary page.

WHAT IT DOES:
    Builds one card per official source by combining what the PROJECT METADATA
    records (data/raw/data_source_notes.json, data/outputs/source_manifest.json
    — publisher, release, years, units, hashes, caveats) with URLs.

URL POLICY:
    Project metadata contains exactly one URL (the CEPII BACI homepage). The
    World Bank and FATF-Egmont URLs are NOT in project metadata, so they live
    here in an explicitly maintained registry, verified against the official
    sites on 2026-07-14. Every card states which of the two origins its URL has.
    Source URLs document dataset provenance; they are never row-level evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceCard:
    key: str
    name: str
    publisher: str
    project_use: str
    url: str
    url_origin: str            # "project metadata" | "dashboard registry (verified 2026-07-14)"
    release: str = ""
    years_used: str = ""
    fields_used: str = ""
    original_unit: str = ""
    transformation: str = ""
    provenance: str = ""
    caveat: str = ""
    files: list[str] = field(default_factory=list)


# URLs maintained by the dashboard because project metadata does not record
# them. If FATF or the World Bank reorganise their sites, update here only.
REGISTRY_URLS = {
    "worldbank_cmo": "https://www.worldbank.org/en/research/commodity-markets",
    "fatf_2020": "https://www.fatf-gafi.org/en/publications/Methodsandtrends/Trade-based-money-laundering-trends-and-developments.html",
    "fatf_2021": "https://www.fatf-gafi.org/en/publications/Methodsandtrends/Trade-based-money-laundering-indicators.html",
}


def is_valid_https_url(url: str) -> bool:
    # Displayed URLs must be https and structurally sane. (CEPII's own readme
    # uses http://; the notes file records the https form, which is what we show.)
    return isinstance(url, str) and url.startswith("https://") and " " not in url and "." in url


def build_source_cards(
    notes: dict | None,
    manifest: dict | None,
) -> list[SourceCard]:
    notes = notes or {}
    manifest = manifest or {}
    inventory = {item.get("file_name"): item for item in manifest.get("source_inventory", [])}

    # --- CEPII BACI: everything from project metadata, including the URL. ---
    # Facts absent from the metadata render as absent — the card never
    # substitutes hardcoded release/revision/filename values.
    hs6_desc = notes.get("hs6_code_descriptions", {})
    hs_revision = str(notes.get("hs_revision") or "")
    baci_release = str(notes.get("baci_release") or "")
    baci_name = str(notes.get("baci_source_name") or "CEPII BACI")
    if hs_revision and baci_release:
        baci_name += f" ({hs_revision}, release {baci_release})"
    baci = SourceCard(
        key="cepii_baci",
        name=baci_name,
        publisher=notes.get("source_provider", "CEPII"),
        project_use="Annual bilateral trade value and quantity by HS6 product — the official observations analysed by this lab.",
        url=notes.get("source_homepage", ""),
        url_origin="project metadata (data_source_notes.json)",
        release=(f"BACI release {baci_release}, {hs_revision}"
                 if baci_release and hs_revision else "not recorded in project metadata"),
        years_used=_years_label(notes.get("years_included", [])),
        fields_used="t, k, i, j, v, q — " + "; ".join(
            f"{code} {desc}" for code, desc in sorted(hs6_desc.items())
        ),
        original_unit="v: thousands of current USD; q: metric tons",
        transformation=notes.get("important_transformations_done_before_upload", ""),
        provenance=notes.get("data_provenance", "official-derived"),
        caveat="The repository Parquet is an official-derived filtered extract (three HS6 codes), not the full BACI release.",
        files=[notes["filtered_output_file"]] if notes.get("filtered_output_file") else [],
    )

    # --- World Bank CMO ("Pink Sheet"): metadata for facts, registry for URL. ---
    wb_note = notes.get("world_bank_workbook_note", "")
    wb_check = manifest.get("world_bank_source_check", {})
    worldbank = SourceCard(
        key="worldbank_cmo",
        name="World Bank Commodity Markets Outlook — 'Pink Sheet' annual prices",
        publisher="World Bank",
        project_use="Annual benchmark prices for palm oil, copper, and gold (broad market context for unit values).",
        url=REGISTRY_URLS["worldbank_cmo"],
        url_origin="dashboard registry (verified 2026-07-14)",
        release="CMO-Historical-Data-Annual.xlsx, sheet 'Annual Prices (Nominal)' (no edition date recorded; pinned by SHA-256)",
        years_used=_years_label(wb_check.get("years", notes.get("years_included", []))),
        fields_used="Palm oil, Copper, Gold annual nominal prices",
        original_unit="Palm oil and copper: USD per metric ton; gold: USD per troy ounce",
        transformation="Gold converted to USD per metric ton: price × (1,000,000 / 31.1034768). Palm oil and copper used as published.",
        provenance="official (World Bank workbook, hash-pinned)",
        caveat="Benchmarks are macro market context, not corridor-specific landed cost or invoice-level fair value.",
        files=["CMO-Historical-Data-Annual.xlsx"],
    )
    if wb_note:
        worldbank.project_use += f" Project note: {wb_note}"

    # --- FATF–Egmont reference PDFs: context only, URLs from the registry. ---
    fatf_2020 = SourceCard(
        key="fatf_2020",
        name="Trade-Based Money Laundering: Trends and Developments (2020)",
        publisher="FATF and Egmont Group",
        project_use="Typology and caveat context only. Not a model input, not row-level evidence, and never a label.",
        url=REGISTRY_URLS["fatf_2020"],
        url_origin="dashboard registry (verified 2026-07-14)",
        release="Published December 2020",
        years_used="n/a (reference document)",
        fields_used="Typology context for the project's typology cards",
        provenance="official reference document (hash-pinned PDF)",
        caveat="FATF-Egmont material informs wording and caveats; it contributes no data to scores or evidence.",
        files=["Trade-Based-Money-Laundering-Trends-and-Developments_2020.pdf"],
    )
    fatf_2021 = SourceCard(
        key="fatf_2021",
        name="Trade-Based Money Laundering: Risk Indicators (2021)",
        publisher="FATF and Egmont Group",
        project_use="Typology and caveat context only. Not a model input, not row-level evidence, and never a label.",
        url=REGISTRY_URLS["fatf_2021"],
        url_origin="dashboard registry (verified 2026-07-14)",
        release="Published March 2021",
        years_used="n/a (reference document)",
        fields_used="Risk-indicator context for the project's typology cards",
        provenance="official reference document (hash-pinned PDF)",
        caveat="FATF-Egmont material informs wording and caveats; it contributes no data to scores or evidence.",
        files=["Trade-Based-Money-Laundering-Risk-Indicators_2021.pdf"],
    )

    # Attach recorded SHA-256 hashes from the manifest inventory where present.
    cards = [baci, worldbank, fatf_2020, fatf_2021]
    for card in cards:
        hashes = [
            f"{name}: sha256 {inventory[name]['sha256'][:16]}…"
            for name in card.files if name in inventory
        ]
        if hashes:
            card.provenance += " — " + "; ".join(hashes)
    return cards


def _years_label(years) -> str:
    ys = sorted(int(y) for y in years) if years else []
    return f"{ys[0]}–{ys[-1]}" if ys else ""
