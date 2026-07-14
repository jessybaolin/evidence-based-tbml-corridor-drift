"""Source registry, URL validation, and data-dictionary construction."""

from __future__ import annotations

from dashboard.services import data_dictionary as dictionary
from dashboard.services import data_loader as load
from dashboard.services.source_registry import (
    REGISTRY_URLS, build_source_cards, is_valid_https_url,
)


def test_all_source_urls_are_valid_https():
    cards = build_source_cards(load.load_data_source_notes(), load.load_source_manifest())
    assert len(cards) == 4  # BACI, World Bank, FATF 2020, FATF 2021
    for card in cards:
        assert is_valid_https_url(card.url), f"{card.key}: {card.url!r}"
        assert card.url_origin  # every URL declares where it came from


def test_cepii_url_comes_from_project_metadata():
    cards = {card.key: card for card in build_source_cards(
        load.load_data_source_notes(), load.load_source_manifest()
    )}
    assert "cepii.fr" in cards["cepii_baci"].url
    assert cards["cepii_baci"].url_origin.startswith("project metadata")
    assert "worldbank.org" in REGISTRY_URLS["worldbank_cmo"]
    assert "fatf-gafi.org" in REGISTRY_URLS["fatf_2020"]


def test_source_cards_survive_missing_metadata():
    # The appendix must stay functional when optional metadata is absent.
    cards = build_source_cards(None, None)
    assert len(cards) == 4
    assert all(card.name for card in cards)


def test_url_validator_rejects_bad_urls():
    assert not is_valid_https_url("http://example.com")   # not https
    assert not is_valid_https_url("https://bad url.com")  # embedded space
    assert not is_valid_https_url("")


def test_dictionary_build_covers_key_fields(panel, features, queue, evidence, comparison):
    schemas = {
        "corridor_product_year_panel.parquet": panel,
        "corridor_features.parquet": features,
        "top_ranked_corridors.csv": queue,
        "evidence_table.csv": evidence,
        "model_comparison.csv": comparison,
    }
    table = dictionary.build_dictionary(
        schemas, load.load_feature_explanations(), load.load_data_dictionary_md()
    )
    fields = set(table["field"])
    for expected in ["obs_id", "hs6", "robust_historical_z", "benchmark_residual",
                     "selected_review_priority_score", "severity", "quality_status"]:
        assert expected in fields, expected
    # Documented features carry approved wording, not invented text.
    z_rows = table[(table["field"] == "robust_historical_z")
                   & (table["definition_source"] == "reports/feature_explanation_table.md")]
    assert not z_rows.empty
    assert "historical pattern" in z_rows.iloc[0]["definition"]
    # Schema-inferred rows are labelled as such and carry no invented definition.
    inferred = table[table["definition_source"] == "schema-inferred"]
    assert not inferred.empty
    assert (inferred["definition"] == "").all()
