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

## Run Phase 4 (AI assistant)
```
pip install -r requirements.txt
copy .env.example .env      (then put your Gemini key in .env)
python rag/ingest.py
streamlit run app.py
```
Optional neural embeddings: pip install -r requirements-rag-extra.txt

## Day 22 - RAG Retriever Improvements and Unit Testing

### Work Completed
- Improved text chunking in the RAG retriever.
- Fixed the long-text splitting issue.
- Added unit tests for retriever functionality.
- Tested document chunk creation, empty documents, long-text splitting, and chunk ID assignment.

### Testing
- Command: python -m pytest tests/test_retriever.py -v
- Result: All 4 tests passed.

## Day 23 - RAG Pipeline Integration Testing

### Work Completed
- Added integration tests for the RAG pipeline.
- Tested Retriever search functionality.
- Tested Assistant and Retriever integration.
- Verified low-score document filtering.
- Tested empty retriever handling.
- Used mock components to test without external API calls.

### Testing
- Command: python -m pytest tests/test_rag_integration.py -v
- Result: All 4 integration tests passed.
- Full test suite: python -m pytest -v
- Result: All 12 tests passed.

## Day 24 - RAG Index Persistence Testing

### Work Completed
- Added tests for RAG index persistence.
- Verified that chunks, metadata, and vector files are saved.
- Checked saved chunks against the original chunks.
- Validated embedding backend metadata.
- Verified saved NumPy vectors match the original vectors.

### Testing
- Command: python -m pytest tests/test_index_persistence.py -v
- Result: All 4 persistence tests passed.
- Full test suite: python -m pytest -v
- Result: All 16 tests passed.
