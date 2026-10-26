# CogniStream: Developer Flow-State & Cognitive Load Analytics

Infotact Solutions internship project (Data Analytics).

## Folder structure
- data/        raw dataset (cleaned file is created here)
- src/         cleaning.py (Phase 1), kpis.py (Phase 2)
- rag/         RAG assistant (Phase 4)
- dashboard/   Streamlit pages (Phase 3)
- reports/     data_quality_report.md is created here
- tests/, docs/, notebooks/

## Run Phase 1 (Windows, VS Code terminal)
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/cleaning.py
```
Output: data/cleaned_developer_productivity.csv and reports/data_quality_report.md

## Run Phase 2 (EDA and KPIs)
```
pip install -r requirements.txt
python src/eda.py
```
Output: reports/charts/*.png and reports/eda_findings.md

## Run Phase 3 (dashboard)
```
pip install -r requirements.txt
streamlit run app.py
```

## Power BI-style chart upgrade
New files: `dashboard/charts.py` (Plotly Graph Objects chart builders), `dashboard/palette.py` (colours/themes),
`tests/` (unit tests). `src/kpis.py` only gained new helper functions (existing ones are unchanged).
The Power BI Desktop guide is in `powerbi/README.md` (no .pbix is included).

Run the tests (Windows, VS Code terminal, from the project root):
```
python -m unittest discover -s tests -v
```

## Run Phase 4 (AI assistant)
```
pip install -r requirements.txt
copy .env.example .env      (then put your Gemini key in .env)
python rag/ingest.py
streamlit run app.py
```
Optional neural embeddings: pip install -r requirements-rag-extra.txt

## Interactive Power BI-style dashboard implementation

The dashboard keeps the existing six report tabs, sidebar slicers, KPI definitions, source dataset, document index, and RAG assistant. The visuals use Plotly and are driven by the currently filtered DataFrame.

### Visuals by page
- **Overview:** KPI cards and productivity bullet gauge; cognitive-load donut; monthly productivity/session combo chart; stacked area chart of session volume by task type; task type → work mode treemap (tile size = sessions, colour = average productivity); task-type share pie; searchable/sortable/paginated session detail table; monthly developer productivity rank-change chart; developer ranking and per-developer drill-down.
- **Productivity Analysis:** Flow-vs-productivity and coding-vs-productivity bubble scatter plots; interruption-band comparison; metric small multiples; summary matrix; Spearman correlation heatmap.
- **Cognitive Load Analysis:** Cognitive-load donut, complexity/load heatmap, distribution box plots, metric comparisons, summary matrix and task-type drill-down.
- **Flow-State Analysis:** KPI cards, flow/productivity bubble scatter, flow-duration histogram, task-type comparison and interruption-band comparison.
- **AI Assistant:** Existing document-grounded RAG assistant remains available and uses the active sidebar filters for numeric context.
- **Reports:** Existing data/report downloads plus a searchable, sortable, paginated table of the filtered rows.

### Data-fit decisions
- A **waterfall chart** is intentionally not added: the source dataset does not contain validated additive contribution components for productivity or another total. Treating correlations or averages as contributions would be misleading.
- A **funnel chart** is intentionally not added: there is no defined sequential conversion/stage process in the dataset. Inventing stages would misrepresent the source data.
- All newly added visuals use existing dataset columns and respond to the same sidebar filters. The ribbon-style ranking requires at least two months and otherwise displays a clear empty-state message.

### Install and run
From the project root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Optional Gemini-backed responses: copy `.env.example` to `.env` and add your own `GEMINI_API_KEY`. Without a key, the existing offline retrieval mode remains available.

### Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py dashboard rag src tests
```
