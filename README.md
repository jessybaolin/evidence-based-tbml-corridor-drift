# Evidence-First TBML Corridor Drift Lab

Ranks unusual exporter–importer–HS6–year patterns in official public trade
data (CEPII BACI, World Bank benchmarks) for **human review**, with
recomputable evidence and strict non-overclaiming language.

> This output prioritises an unusual corridor-product pattern for human
> review. It does not establish money laundering, misinvoicing, or criminal
> intent.

## Analytical pipeline

Numbered scripts in `src/` (00–09) verify sources, build the clean panel and
time-safe features, evaluate models on controlled synthetic scenarios, score
the real observations, and generate the evidence table and reports. Generated
artefacts live in `data/processed/`, `data/outputs/`, and `reports/`.

## Stakeholder dashboard

A multipage Streamlit dashboard presents the generated outputs (it depends on
them — run the pipeline first):

```powershell
python -m streamlit run dashboard/streamlit_app.py
```

See [dashboard/README.md](dashboard/README.md) for pages, data dependencies,
and iteration guidance. The dashboard's design skeleton came from a local
reference prototype at `references/tbml_streamlit_multipage_prototype/`
(git-ignored, kept for comparison).

### Dependencies

- `requirements.txt` — the slim **dashboard runtime** (pinned), used by
  Streamlit Community Cloud to build the deployed app.
- `requirements-pipeline.txt` — the **full data pipeline + notebook** environment
  (`src/`, tests, report generation): `pip install -r requirements-pipeline.txt`.

## Tests

```powershell
python -m pytest tests/ -q
```
