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


@pytest.mark.parametrize("page", PAGES)
def test_boundary_ribbon_visible_verbatim(page):
    # The fixed footer ribbon must carry the boundary VERBATIM on every page.
    at = _run_page(page)
    assert _verbatim_boundary() in _rendered_text(at), page


def test_entry_point_renders_default_page():
    at = AppTest.from_file(str(ENTRY_POINT), default_timeout=120)
    at.run()
    assert not at.exception
    assert _verbatim_boundary() in _rendered_text(at)


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
    assert "only real official observations enter the review queue" in text
    assert f"{len(panel):,}" in text, "observation count missing"
    assert f"{eligible_pct:.1f}%" in text, "eligibility share missing"
    assert f"{value_share:.1f}%" in text, "trade-value coverage missing"
    assert "Scene 1 of 3" in text
    assert "data-tip" in text, "KPI tooltips missing"


def test_data_trust_scene_navigation_and_corrected_wording():
    # Scene walk: 1 (sources) -> 2 (prepare; carries the corrected
    # quantity-not-value exclusion wording) -> 3 (evaluation wall) -> back.
    at = _run_page("from_data_to_review_queue.py")
    assert "Three sources, each with one clearly separated role" in _rendered_text(at)

    at = at.button(key="dtrq_next").click().run()
    text = _rendered_text(at)
    assert not at.exception
    assert "Scene 2 of 3" in text
    assert (
        "Rows without a valid reported quantity cannot support implied "
        "unit-value analysis" in text
    )
    assert "retained for audit" in text
    assert "not a suspicion signal" in text

    at = at.button(key="dtrq_next").click().run()
    text = _rendered_text(at)
    assert not at.exception
    assert "Scene 3 of 3" in text
    assert "Controlled evaluation copy—not official findings" in text
    assert "Only the selected method returns. Synthetic rows never cross." in text
    assert "Benchmark gap" in text, "real evidence-check names missing"

    at = at.button(key="dtrq_prev").click().run()
    assert "Scene 2 of 3" in _rendered_text(at)


def test_bank_implementation_pathway_is_explicitly_future_state():
    at = _run_page("bank_implementation_pathway.py")
    assert not at.exception
    text = _rendered_text(at)
    assert (
        "Future-state design only. Private bank-data integration, "
        "case-management connectivity, and production decisioning have not been built."
    ) in text
    assert "It would not replace transaction monitoring" in text
    assert "Analyst dispositions are not unquestioned ground-truth labels" in text


def test_bank_implementation_pathway_names_required_bank_context():
    at = _run_page("bank_implementation_pathway.py")
    text = _rendered_text(at)
    for label in (
        "KYC/CDD and expected activity",
        "Trade-finance documentation",
        "Shipment and customs records",
        "Payments and correspondent data",
        "Sanctions and adverse media",
        "Beneficial ownership",
    ):
        assert label in text, label
    for stage in (
        "Offline enrichment pilot",
        "Controlled workflow integration",
        "Validated operational use",
    ):
        assert stage in text, stage


def test_navigation_group_order_and_renamed_reference_page():
    source = ENTRY_POINT.read_text(encoding="utf-8")
    assert source.index('"Business & Review"') < source.index('"Methodology"')
    assert source.index('"Methodology"') < source.index('"Future State"')
    assert source.index('"Future State"') < source.index('"Appendix"')
    assert '"title": "Model Evaluation & Controls"' in source
    assert '"title": "Bank Implementation Pathway"' in source
    assert '"title": "Data Dictionary"' in source


def test_renamed_methodology_and_dictionary_titles_render():
    model = _run_page("model_and_controls.py")
    dictionary = _run_page("appendix.py")
    assert "Model Evaluation &amp; Controls" in _rendered_text(model)
    assert "Data Dictionary" in _rendered_text(dictionary)


def test_review_queue_filters_and_empty_state():
    at = _run_page("review_queue.py")
    # The score slider now lives inside the collapsed "Advanced filters"
    # expander; AppTest reaches it by key regardless. Narrow it to an
    # impossible band -> transparent empty state.
    slider = next(s for s in at.slider if s.key == "queue_score_range")
    low = slider.value[0]
    at = slider.set_value((low, low)).run()
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


def test_review_queue_export_size_control_and_score_note():
    at = _run_page("review_queue.py")
    assert not at.exception
    assert len(at.download_button) == 1, "CSV export button missing"
    assert len(at.segmented_control) == 1, "queue-size control missing"
    assert at.segmented_control[0].value == "Top 50"
    assert at.segmented_control[0].options == ["Top 50"]
    # The verbatim score explainer must appear on the page (column tooltip
    # copy is the same YAML anchor, so one assertion covers both).
    content = yaml.safe_load(
        (REPO_ROOT / "dashboard" / "config" / "dashboard_content.yml").read_text(encoding="utf-8")
    )
    assert content["pages"]["review_queue"]["score_note"] in _rendered_text(at)


def test_review_queue_summary_and_guidance_are_derived_and_separated():
    from dashboard.services import dashboard_metrics as metrics
    from dashboard.services import data_loader as load

    content = load.load_content()
    queue = load.load_review_queue()
    features = load.load_features(columns=(
        "obs_id", "exporter_name", "importer_name", "benchmark_residual",
        "robust_historical_z",
    ))
    enriched = metrics.enrich_queue(queue, features, content["family_short_labels"])
    scores = enriched["selected_review_priority_score"]

    at = _run_page("review_queue.py")
    text = _rendered_text(at)
    assert f"<strong>{len(enriched):,}</strong> results" in text
    assert f"<strong>{enriched['family_label'].nunique():,}</strong> product families" in text
    assert f"{scores.min():.3f}&ndash;{scores.max():.3f}" in text
    assert "How to read the score" in text
    assert content["pages"]["review_queue"]["caveat"] in text
    assert any(expander.label == "Table notes and methodology" for expander in at.expander)


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


def test_review_queue_reset_and_clear_advanced_controls():
    at = _run_page(
        "review_queue.py",
        queue_years=[2022],
        queue_families=["Gold"],
    )
    at = at.button(key="queue_reset_filters").click().run()
    assert not at.exception
    assert next(item for item in at.multiselect if item.key == "queue_years").value == []
    assert next(item for item in at.multiselect if item.key == "queue_families").value == []

    slider = next(item for item in at.slider if item.key == "queue_score_range")
    default_range = slider.value
    narrowed = (default_range[0], round(default_range[1] - 0.001, 4))
    at = slider.set_value(narrowed).run()
    assert next(item for item in at.slider if item.key == "queue_score_range").value == narrowed

    at = at.button(key="queue_clear_advanced").click().run()
    assert not at.exception
    assert next(
        item for item in at.slider if item.key == "queue_score_range"
    ).value == default_range


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
    assert ("The World Bank benchmark provides broad market context; "
            "it is not invoice-level fair value.") in text
    # Removed from the visible page: score internals, the method formula and
    # the retired trend tab.
    assert "Rule score" not in text
    assert "Challenger score" not in text
    assert "Hybrid:" not in text
    assert "Trade & Benchmark Trend" not in text


def test_case_view_carousel_switches_without_changing_case():
    from dashboard.services.data_loader import load_review_queue

    default_id = str(load_review_queue().sort_values("rank").iloc[0]["obs_id"])
    at = _run_page("case_investigation.py")
    assert "wider commodity market" in _rendered_text(at)

    at = at.button(key="case_view_next").click().run()
    assert not at.exception
    assert "own prior behaviour" in _rendered_text(at)
    assert at.session_state["tbml_selected_obs_id"] == default_id

    at = at.button(key="case_view_next").click().run()
    assert not at.exception
    assert "comparable corridors" in _rendered_text(at)
    assert at.session_state["tbml_selected_obs_id"] == default_id

    at = at.button(key="case_view_prev").click().run()
    assert "own prior behaviour" in _rendered_text(at)
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
