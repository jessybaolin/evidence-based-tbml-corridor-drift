"""Render every dashboard page headlessly with Streamlit's AppTest.

Pages run through the real entry point (streamlit_app.py + st.navigation +
AppTest.switch_page) so every run exercises the app shell: global styles, the
custom sidebar, main-area page links, and the fixed boundary ribbon that
streamlit_app.py renders once per run. A page passes when it renders without
an exception and the VERBATIM conclusion boundary (configs/project.yml) is
present in its output.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = REPO_ROOT / "dashboard" / "streamlit_app.py"
PAGES = [
    "executive_overview.py",
    "review_queue.py",
    "case_investigation.py",
    "portfolio_analytics.py",
    "from_data_to_review_queue.py",
    "bank_implementation_pathway.py",
    "model_and_controls.py",
    "gold_quantity_coverage.py",
    "appendix.py",
]


def _run_page(page: str, **session_state) -> AppTest:
    # Runs through the entry script + st.navigation (MPA v2), so each page is
    # rendered with the real app shell. This depends on the page files living
    # in app_pages/ — a directory literally named "pages" would flip Streamlit
    # (and AppTest.switch_page) onto the MPA-v1 path, which executes the page
    # file alone, without the shell or the boundary ribbon.
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.switch_page(f"app_pages/{page}")
    for key, value in session_state.items():
        at.session_state[key] = value
    return at.run()


def _rendered_text(at: AppTest) -> str:
    chunks = [str(getattr(block, "value", "")) for block in at.markdown]
    chunks += [str(getattr(block, "body", "")) for block in getattr(at, "caption", [])]
    return " ".join(chunks)


def _verbatim_boundary() -> str:
    # Read the source of truth directly, independent of the dashboard loaders.
    config = yaml.safe_load(
        (REPO_ROOT / "configs" / "project.yml").read_text(encoding="utf-8")
    )
    return str(config["conclusion_boundary"])


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    at = _run_page(page)
    assert not at.exception, f"{page} raised: {at.exception}"
    # streamlit_app.py converts MissingOutputError into st.error + st.stop;
    # make sure that path never fired (other st.error uses are legitimate).
    assert not any(
        "Required project output is missing" in str(getattr(block, "value", ""))
        for block in at.error
    ), f"{page} hit a missing-output error state"


# The boundary ribbon rides on every dashboard page verbatim, for consistency.
BOUNDARY_PAGES = list(PAGES)


@pytest.mark.parametrize("page", BOUNDARY_PAGES)
def test_boundary_ribbon_visible_verbatim(page):
    # The fixed footer ribbon must carry the boundary VERBATIM on these pages.
    at = _run_page(page)
    assert _verbatim_boundary() in _rendered_text(at), page


def test_entry_point_renders_default_page():
    # The root/default route is the full-screen landing: it deliberately drops
    # the shell, so the ribbon must be ABSENT here. Every dashboard page keeps
    # verbatim-ribbon coverage in test_boundary_ribbon_visible_verbatim; the
    # full landing contract lives in tests/test_dashboard_landing.py.
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.run()
    assert not at.exception
    text = _rendered_text(at)
    assert "Evidence-First" in text
    assert _verbatim_boundary() not in text


def test_landing_page_numbers_are_derived():
    # The narrative copy must show the live pipeline facts, not typed-in numbers.
    from dashboard.services.data_loader import load_evidence, load_panel, load_review_queue

    panel = load_panel(columns=("obs_id",))
    queue = load_review_queue()
    evidence = load_evidence()
    at = _run_page("executive_overview.py")
    text = _rendered_text(at)
    assert f"{len(panel):,}" in text, "observation count missing"
    assert f"Top {len(queue)}" in text, "queue size missing"
    assert f"drawn from {evidence['evidence_type'].nunique()} checks" in text
    assert "data-tip" in text, "CSS tooltips missing"


def test_landing_page_tooltip_names_real_evidence_checks():
    at = _run_page("executive_overview.py")
    text = _rendered_text(at)
    for label in ("History deviation", "Benchmark gap", "Value–quantity divergence"):
        assert label in text, label


def test_landing_story_control_defaults_and_persists():
    content = yaml.safe_load(
        (REPO_ROOT / "dashboard" / "config" / "dashboard_content.yml").read_text(
            encoding="utf-8"
        )
    )["pages"]["executive_overview"]
    labels = [
        content["what_heading"],
        content["why_heading"],
        content["pipeline_heading"],
    ]

    at = _run_page("executive_overview.py")
    control = next(
        item for item in at.segmented_control
        if item.key == "business_value_story_tab"
    )
    assert control.options == labels
    assert control.value == labels[0]
    assert "Explore the project" in _rendered_text(at)

    at = control.set_value(labels[1]).run()
    assert not at.exception
    assert content["quote_before"] in _rendered_text(at)
    assert next(
        item for item in at.segmented_control
        if item.key == "business_value_story_tab"
    ).value == labels[1]

    at = at.run()
    assert next(
        item for item in at.segmented_control
        if item.key == "business_value_story_tab"
    ).value == labels[1]


def test_landing_story_control_exposes_existing_project_and_pipeline_content():
    content = yaml.safe_load(
        (REPO_ROOT / "dashboard" / "config" / "dashboard_content.yml").read_text(
            encoding="utf-8"
        )
    )["pages"]["executive_overview"]
    labels = [
        content["what_heading"],
        content["why_heading"],
        content["pipeline_heading"],
    ]
    at = _run_page("executive_overview.py")
    assert all(
        family_class in _rendered_text(at)
        for family_class in (
            "family-crude-palm-oil",
            "family-refined-copper-cathodes",
            "family-gold-unwrought",
        )
    )
    text = _rendered_text(at)
    assert text.count("commodity-info tip") == 3
    for explanation in content["commodity_info"].values():
        assert explanation in text
    for gold_hs6 in ("710811", "710812", "710813", "710820"):
        assert gold_hs6 in text

    styles = (REPO_ROOT / "dashboard" / "components" / "styles.py").read_text(
        encoding="utf-8"
    )
    for selector in (
        ".st-key-business_value_page .twin-card:hover",
        ".st-key-business_value_page .stat-tile:hover",
        ".st-key-business_value_story .quote-card:hover",
        ".st-key-business_value_story .story-process-stage:hover",
    ):
        hover_rule = styles.split(selector, 1)[1].split("}}", 1)[0]
        assert "transform: translateY(-2px)" in hover_rule
        assert "box-shadow: 0 6px 16px" in hover_rule

    control = next(
        item for item in at.segmented_control
        if item.key == "business_value_story_tab"
    )
    at = control.set_value(labels[2]).run()
    text = _rendered_text(at)
    assert not at.exception
    for step in content["pipeline_steps"]:
        assert step in text
    assert any(
        content["pipeline_cta"] in str(getattr(link, "label", ""))
        for link in at.get("page_link")
    )


def test_data_trust_page_mental_model_and_derived_kpis():
    # The Data Coverage & Trust page must show its one mental model and a KPI
    # strip whose numbers come from the panel, never typed-in copy.
    from dashboard.services.data_loader import load_panel

    panel = load_panel(columns=("obs_id", "model_eligible", "trade_value_usd"))
    eligible = panel["model_eligible"].astype(bool)
    eligible_pct = 100.0 * eligible.sum() / len(panel)
    value_share = (
        100.0 * panel.loc[eligible, "trade_value_usd"].sum()
        / panel["trade_value_usd"].sum()
    )
    at = _run_page("from_data_to_review_queue.py")
    text = _rendered_text(at)
    assert "only real trade records ever reach the review queue" in text
    assert f"{len(panel):,}" in text, "observation count missing"
    assert f"{eligible_pct:.1f}%" in text, "eligibility share missing"
    assert f"{value_share:.1f}%" in text, "trade-value coverage missing"
    assert "Scene 1 of 3" not in text
    assert "Page 1 of 3" not in text
    assert "data-tip" in text, "KPI tooltips missing"


def test_data_trust_scene_navigation_and_simplified_preparation():
    # Two-scene walk: 1 (sources) -> 2 (prepare; carries a real prepared row and
    # the concise quantity exclusion). Scene 3 ("Test, rank & explain") was
    # retired to the Model Evaluation & Controls page, so Scene 2 is the final
    # scene: it carries the closing statement and a link to that page, and there
    # is no third scene to advance into.
    from dashboard.services.data_loader import load_content, load_panel, load_review_queue

    at = _run_page("from_data_to_review_queue.py")
    assert "Three sources, each with one clearly separated role" in _rendered_text(at)

    at = at.button(key="dtrq_next").click().run()
    text = _rendered_text(at)
    assert not at.exception
    assert "Standardise units" in text
    assert "Convert reported trade values to USD and quantities to metric tons." in text
    assert "Rows without a valid reported quantity are excluded from modelling." in text
    assert "Time-safe simply means no peeking into the future." in text
    # The time-safe example is tied to the real sample observation's year (2021),
    # so the future years it must not use are 2022, 2023 or 2024.
    assert "it cannot use 2022, 2023 or 2024" in text
    assert "CEPII BACI extract" not in text
    assert "Trade value: thousand USD" not in text
    assert "View provenance" not in text
    assert "retained for audit" not in text
    assert "not a suspicion signal" not in text

    panel = load_panel(columns=("obs_id", "trade_value_usd"))
    queue_ids = set(load_review_queue()["obs_id"])
    candidates = panel[~panel["obs_id"].isin(queue_ids)]
    sample = candidates.loc[candidates["trade_value_usd"].idxmax()]
    assert str(sample["obs_id"]) in text, "real prepared observation missing"

    # Scene 2 is now the final scene: the closing statement renders here, and Next
    # is disabled because the evaluation wall (old Scene 3) is gone.
    assert "accountable human review" in text
    assert at.button(key="dtrq_next").disabled
    assert "Controlled evaluation copy—not official findings" not in text
    assert "Only the selected method returns. Synthetic rows never cross." not in text

    # The model-validation deep dive is offered as an on-demand link, not a scene.
    cta = load_content()["pages"]["from_data_to_review_queue"]["model_eval_cta"]
    link_labels = [str(getattr(pl, "label", "")) for pl in at.get("page_link")]
    assert any(cta in label for label in link_labels), "Model Evaluation link missing"

    at = at.button(key="dtrq_prev").click().run()
    assert "Three sources, each with one clearly separated role" in _rendered_text(at)


def test_data_trust_row_labels_match_navigation_colours():
    styles = (
        REPO_ROOT / "dashboard" / "components" / "styles.py"
    ).read_text(encoding="utf-8")
    selector = styles.split("table.data-table td.rec-k", 1)[1].split("}}", 1)[0]
    assert 'color: {p["sidebar_ink"]}' in selector
    assert 'background: {p["sidebar_bg"]}' in selector


def test_bank_implementation_pathway_is_explicitly_future_state():
    at = _run_page("bank_implementation_pathway.py")
    assert not at.exception
    text = _rendered_text(at)
    assert (
        "Future-state design only. Connections to private bank data, "
        "case-management systems and production decisions have not been built."
    ) in text
    assert "this queue could be an early signal for review" in text
    assert "sit alongside transaction monitoring" in text
    assert "bank-section-info tip" in text
    assert "Analyst decisions can provide useful feedback" in text


def test_bank_implementation_pathway_names_required_bank_context():
    at = _run_page("bank_implementation_pathway.py")
    text = _rendered_text(at)
    for label in (
        "KYC/CDD and expected activity",
        "Trade-finance documents",
        "Shipment and customs records",
        "Payments and correspondent data",
        "Sanctions and adverse media",
        "Beneficial ownership",
    ):
        assert label in text, label
    assert "How a bank could start safely" not in text


def test_bank_implementation_pathway_bounds_the_ai_extension():
    at = _run_page("bank_implementation_pathway.py")
    assert not at.exception
    text = _rendered_text(at)
    assert "Where AI could help: connect the records, leave the decision to the analyst" in text
    assert "It would not decide whether the activity is suspicious" in text
    assert "The useful part is not writing a summary" in text
    assert "Find the bank activity behind the public signal" in text
    assert "Check whether the records tell the same story" in text
    assert "Lay out the case for the analyst" in text
    for output in (
        "Related activity in one view",
        "Document and payment comparison",
        "Explanations checked against the records",
        "Ask questions about the case",
    ):
        assert output in text
    assert "Practical extensions" not in text
    assert "Keep a log and use fixed templates if validation fails" in text
    assert "Public data points to a pattern" in text
    assert "What bank records add" in text
    assert "How this could help a wholesale-banking AFC team" in text
    assert "Proposed benefits to test in a controlled pilot" not in text
    assert "What must stay controlled" not in text

    styles = (
        REPO_ROOT / "dashboard" / "components" / "styles.py"
    ).read_text(encoding="utf-8")
    assert "animation-timeline: view()" in styles
    assert ".anim, .bank-reveal" in styles
    assert "align-items: stretch" in styles
    assert ".bank-icon-card.domain.bank-card-4" in styles
    assert ".bank-ai-output-grid" in styles
    closing_text = styles.split(".bank-closing .bottom-line-text", 1)[1].split("}}", 1)[0]
    assert "font-size: 0.88rem" in closing_text

    business_closing_text = (
        styles.split(".st-key-business_value_page .bottom-line-text", 1)[1]
        .split("}}", 1)[0]
    )
    assert "font-size: 0.88rem" in business_closing_text


def test_navigation_group_order_and_renamed_reference_page():
    source = ENTRY_POINT.read_text(encoding="utf-8")
    assert '"title": "Business Problem and Value"' in source
    assert '"title": "Business Problem & Value"' not in source
    assert source.index('"Business & Review"') < source.index('"Methodology"')
    assert source.index('"Methodology"') < source.index('"Future State"')
    assert source.index('"Future State"') < source.index('"Appendix"')
    assert '"title": "Model Evaluation & Controls"' in source
    assert '"title": "Unscored Gold Records"' in source
    assert '"title": "Gold Quantity Coverage"' not in source
    assert '"title": "Bank Implementation Pathway"' in source
    assert '"title": "Data Dictionary"' in source


def test_renamed_methodology_and_dictionary_titles_render():
    model = _run_page("model_and_controls.py")
    dictionary = _run_page("appendix.py")
    assert "Model Evaluation &amp; Controls" in _rendered_text(model)
    assert "Data Dictionary" in _rendered_text(dictionary)


def test_review_queue_filters_and_empty_state():
    from dashboard.services.data_loader import load_review_queue

    queue = load_review_queue()
    observed = set(zip(queue["exporter_iso3"], queue["importer_iso3"]))
    empty_pair = next(
        (exporter, importer)
        for exporter in sorted(queue["exporter_iso3"].unique())
        for importer in sorted(queue["importer_iso3"].unique())
        if (exporter, importer) not in observed
    )
    at = _run_page(
        "review_queue.py",
        queue_exporters=[empty_pair[0]],
        queue_importers=[empty_pair[1]],
    )
    assert not at.exception
    assert any("No review candidates match" in str(block.value) for block in at.info)


def test_review_queue_banner_default_and_current():
    from dashboard.services.data_loader import load_review_queue

    queue = load_review_queue().sort_values("rank")
    at = _run_page("review_queue.py")
    assert not at.exception
    text = _rendered_text(at)
    # No selection this session -> the banner names the default (top-ranked)
    # case that Selected Case Review would open with.
    assert f"Default case #{int(queue.iloc[0]['rank'])}:" in text
    assert "Select another row to change it." in text

    carried = queue.iloc[6]
    at2 = _run_page("review_queue.py", tbml_selected_obs_id=carried["obs_id"])
    assert not at2.exception
    text2 = _rendered_text(at2)
    assert f"Current case #{int(carried['rank'])}:" in text2
    assert "Default case" not in text2


def test_review_queue_cell_pick_updates_case_and_checked_marker():
    import pandas as pd

    from dashboard.services import dashboard_metrics as metrics
    from dashboard.services import data_loader as load

    content = load.load_content()
    queue = load.load_review_queue()
    features = load.load_features(columns=(
        "obs_id", "exporter_name", "importer_name", "benchmark_residual",
        "robust_historical_z",
    ))
    enriched = metrics.enrich_queue(queue, features, content["family_short_labels"])
    table_identity = (
        f"queue_table_{pd.util.hash_pandas_object(enriched['obs_id'], index=False).sum():x}"
    )
    picked = enriched.iloc[1]
    at = _run_page(
        "review_queue.py",
        **{
            f"{table_identity}_default": {
                "selection": {"rows": [], "columns": [], "cells": [[1, "corridor"]]},
            },
        },
    )

    assert not at.exception
    assert f"Current case #{int(picked['rank'])}:" in _rendered_text(at)
    markers = at.dataframe[0].value["current_case"]
    assert int(markers.sum()) == 1
    assert bool(markers.iloc[1])


def test_review_queue_export_simplified_filters_and_score_note():
    at = _run_page("review_queue.py")
    assert not at.exception
    assert len(at.download_button) == 1, "CSV export button missing"
    assert not at.segmented_control, "queue-size control should be removed"
    assert not at.slider, "advanced score filter should be removed"
    assert all(expander.label != "Advanced filters" for expander in at.expander)
    text = _rendered_text(at)
    assert "Year, product family, exporter and importer scope" not in text
    assert "Queue size" not in text
    # The verbatim score explainer must appear on the page (column tooltip
    # copy is the same YAML anchor, so one assertion covers both).
    content = yaml.safe_load(
        (REPO_ROOT / "dashboard" / "config" / "dashboard_content.yml").read_text(encoding="utf-8")
    )
    assert content["pages"]["review_queue"]["score_note"] in _rendered_text(at)
    # Unit value is now explained as a footer note ("How unit value is
    # calculated"), not an in-grid tooltip, so its label carries no ⓘ marker and
    # the definition text renders in the page.
    unit_value = content["pages"]["review_queue"]["columns"]["unit_value_usd_per_metric_ton"]
    assert not unit_value["label"].endswith("ⓘ")
    assert "not observed from an invoice or transaction price" in unit_value["help"]
    assert unit_value["help"] in _rendered_text(at)
    assert "How unit value is calculated" in _rendered_text(at)


def test_review_queue_redundant_counts_are_removed_and_guidance_is_retained():
    from dashboard.services import data_loader as load

    content = load.load_content()
    at = _run_page("review_queue.py")
    text = _rendered_text(at)
    assert "matching observations" not in text
    assert "queue-result-count" not in text
    assert "queue-state-summary" not in text
    assert "Score range" not in text
    assert "How to read the score" in text
    assert content["pages"]["review_queue"]["caveat"] in text
    assert not any(expander.label == "Table notes and methodology" for expander in at.expander)
    assert content["pages"]["review_queue"]["table_caption_precision"] in text
    # The product-family/HS6 legend caption was removed: the HS6 codes now live
    # in the Product-family filter dropdown labels instead.
    assert "Colored dots identify product families" not in text


def test_review_queue_country_filters_show_names_and_keep_iso_values():
    at = _run_page("review_queue.py")
    exporter = next(item for item in at.multiselect if item.key == "queue_exporters")
    importer = next(item for item in at.multiselect if item.key == "queue_importers")

    assert "Spain (ESP)" in exporter.options
    assert "Nepal (NPL)" in importer.options

    at = exporter.select("Spain (ESP)").run()
    exporter = next(item for item in at.multiselect if item.key == "queue_exporters")
    assert exporter.value == ["ESP"]


def test_review_queue_product_column_uses_flat_family_dot():
    at = _run_page("review_queue.py")
    products = at.dataframe[0].value["product"].astype(str)
    for label in ("Gold", "Palm oil", "Copper"):
        family_rows = products[products.str.endswith(label)]
        assert not family_rows.empty, label
        # Flat "●" dot; the family colour is applied by the Styler, not the text.
        assert family_rows.str.startswith("●").all(), label
    # No glossy emoji markers remain.
    assert not products.str.contains("🟡|🟢|🟠").any()


def test_review_queue_active_chip_clears_only_its_filter():
    at = _run_page(
        "review_queue.py",
        queue_years=[2022],
        queue_families=["Gold"],
    )
    assert not at.exception
    labels = {button.label for button in at.button}
    assert "Year: 2022" in labels
    assert "Product: Gold" in labels

    at = at.button(key="queue_clear_queue_years").click().run()
    assert not at.exception
    year = next(item for item in at.multiselect if item.key == "queue_years")
    family = next(item for item in at.multiselect if item.key == "queue_families")
    assert year.value == []
    assert family.value == ["Gold"]


def test_review_queue_reset_clears_primary_filters():
    at = _run_page(
        "review_queue.py",
        queue_years=[2022],
        queue_families=["Gold"],
        queue_exporters=["ITA"],
        queue_importers=["NPL"],
    )
    at = at.button(key="queue_reset_filters").click().run()
    assert not at.exception
    for key in (
        "queue_years", "queue_families", "queue_exporters", "queue_importers",
    ):
        assert next(item for item in at.multiselect if item.key == key).value == []


def test_case_investigation_selectbox_changes_case():
    # AppTest exposes FORMATTED labels via .options; select by index and check
    # the raw obs_id landed in session state.
    from dashboard.services.data_loader import load_review_queue

    queue = load_review_queue()
    expected = queue.sort_values("rank").iloc[4]["obs_id"]
    at = _run_page("case_investigation.py")
    selector = at.selectbox[0]
    assert len(selector.options) == len(queue)
    at = selector.select_index(4).run()
    assert not at.exception
    assert at.session_state["tbml_selected_obs_id"] == expected


def test_case_investigation_respects_queue_selection():
    from dashboard.services.data_loader import load_review_queue

    carried = load_review_queue().sort_values("rank").iloc[7]["obs_id"]
    at = _run_page("case_investigation.py", tbml_selected_obs_id=carried)
    assert not at.exception
    assert at.selectbox[0].value == carried


def test_case_strip_governed_copy_and_removed_kpis():
    # The compact strip replaces the old KPI cards; the governed tooltip texts
    # ride verbatim, and the removed header/summary items stay removed.
    from dashboard.services.data_loader import load_review_queue

    top = load_review_queue().sort_values("rank").iloc[0]
    at = _run_page("case_investigation.py")
    assert not at.exception
    text = _rendered_text(at)
    assert f"#{int(top['rank'])}" in text
    assert f"{top['exporter_iso3']} → {top['importer_iso3']}" in text
    assert ("This score determines review order. A higher score means higher "
            "review priority; it is not a probability or finding of financial "
            "crime.") in text
    assert ("Annual reported trade value divided by reported quantity. "
            "It is an aggregate average, not an invoice price.") in text
    # Combined comparison note: benchmark is market context, not fair value.
    assert "the World Bank benchmark is the world market price" in text
    assert "not invoice-level fair value" in text
    # Removed from the visible page: score internals, the method formula and
    # the retired trend tab.
    assert "Rule score" not in text
    assert "Challenger score" not in text
    assert "Hybrid:" not in text
    assert "Trade & Benchmark Trend" not in text


def test_case_view_switcher_changes_view_without_changing_case():
    # The comparison view is switched by the segmented-control tabs directly.
    # Market and own-history are now ONE combined view; Peer position is the other.
    # (Headings highlight the word "corridor" in a tooltip span, so assertions use
    # substrings that don't cross that word.)
    from dashboard.services.data_loader import load_review_queue

    default_id = str(load_review_queue().sort_values("rank").iloc[0]["obs_id"])
    at = _run_page("case_investigation.py")
    assert "the market and its own history" in _rendered_text(at)

    def _switch(app, label):
        bar = next(s for s in app.segmented_control if s.key == "case_view_bar")
        return bar.set_value(label).run()

    at = _switch(at, "Peer position")
    assert not at.exception
    assert "How unusual was the case among comparable" in _rendered_text(at)
    assert at.session_state["tbml_selected_obs_id"] == default_id

    at = _switch(at, "Market & history")
    assert not at.exception
    assert "the market and its own history" in _rendered_text(at)
    assert at.session_state["tbml_selected_obs_id"] == default_id


def test_case_view_table_mode_shows_same_frame_and_keeps_case():
    from dashboard.services.data_loader import load_review_queue

    top = load_review_queue().sort_values("rank").iloc[0]
    default_id = str(top["obs_id"])
    multiple = float(top["unit_value_usd_per_metric_ton"]) / float(
        top["benchmark_price_usd_per_metric_ton"]
    )
    at = _run_page("case_investigation.py")
    mode = next(s for s in at.segmented_control if s.key == "case_view_mode_0")
    at = mode.set_value("Table").run()
    assert not at.exception
    text = _rendered_text(at)
    # The market table renders from the SAME prepared frame as the chart: the
    # case-year benchmark multiple appears with the table's 2-dp format.
    assert f"{multiple:,.2f}×" in text
    assert "Benchmark multiple" in text
    assert at.session_state["tbml_selected_obs_id"] == default_id


def test_case_change_refreshes_strip_facts_and_takeaway():
    from dashboard.services.data_loader import load_review_queue

    queue = load_review_queue().sort_values("rank")
    target = queue.iloc[4]
    multiple = float(target["unit_value_usd_per_metric_ton"]) / float(
        target["benchmark_price_usd_per_metric_ton"]
    )
    at = _run_page("case_investigation.py")
    at = at.selectbox[0].select_index(4).run()
    assert not at.exception
    text = _rendered_text(at)
    assert f"#{int(target['rank'])}" in text
    assert f"{target['exporter_iso3']} → {target['importer_iso3']}" in text
    # The market takeaway recomputes for the new case (1-dp multiple).
    assert f"{multiple:.1f}× the annual World Bank benchmark" in text
    assert at.session_state["tbml_selected_obs_id"] == str(target["obs_id"])


def test_model_controls_split_switch():
    at = _run_page("model_and_controls.py")
    split_box = at.selectbox[0]
    at = split_box.select("validation").run()
    assert not at.exception


def test_appendix_dictionary_search():
    at = _run_page("appendix.py")
    search = next(t for t in at.text_input if t.key == "dict_search")
    at = search.set_value("residual").run()
    assert not at.exception


def test_appendix_dictionary_is_a_stakeholder_field_shortlist():
    at = _run_page("appendix.py")
    assert not at.exception
    text = _rendered_text(at)

    assert [tab.label for tab in at.tabs] == ["Key Data Fields", "Official Data Sources"]
    assert "Fields used in analysis and review" in text
    assert "Trade and benchmark measures" in text
    assert "Historical and peer comparison signals" in text
    assert "Review-priority outputs" in text
    assert not at.multiselect

    for removed in (
        "Documented definitions come from",
        "Identifiers",
        "Source values",
        "Quality fields",
        "Evidence fields",
        "Other",
        "Field category",
        "Definition source",
    ):
        assert removed not in text


def test_appendix_source_copy_is_concise_and_omits_provenance_rows():
    at = _run_page("appendix.py")
    assert not at.exception
    text = _rendered_text(at)

    for removed in (
        "Definitions, analytical fields, and official data sources.",
        "Publisher, release, units, transformations, and provenance for every source",
        "Provenance:",
        "Source URLs document dataset provenance",
        "Column k was read and stored as a six-character string",
        "no edition date recorded; pinned by SHA-256",
    ):
        assert removed not in text

    assert "Rows were filtered to the three selected HS6 codes only." in text
    assert "CMO-Historical-Data-Annual.xlsx" in text
    assert "Annual Prices (Nominal)" in text
