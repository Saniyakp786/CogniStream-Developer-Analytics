# CogniStream: Developer Flow-State & Cognitive Load Analytics

**Infotact Solutions Internship Project – Data Analytics**

## 1. Project Overview

CogniStream is a developer productivity analytics project designed to understand developers' working patterns, focus time, interruptions, flow state, and cognitive load.

The project analyzes developer activity data and generates meaningful insights to help understand productivity and improve work efficiency.

## 2. Project Objectives

- Analyze developer productivity and work patterns.
- Measure focus time and flow-state duration.
- Understand interruptions and context switching.
- Analyze cognitive load.
- Generate KPIs and visual reports.
- Maintain data quality through validation and automated testing.
- Explore an AI-powered RAG assistant for project data.

## 3. Key Features

- Data cleaning and preprocessing.
- Exploratory Data Analysis (EDA).
- Productivity KPI calculation.
- Developer productivity dashboard.
- RAG-based AI assistant.
- Automated data validation.
- Data quality summary report in JSON.
- Unit and integration testing.

## 4. Technologies Used

- **Programming:** Python
- **Data Analysis:** Pandas, NumPy
- **Visualization:** Matplotlib, Streamlit
- **AI Assistant:** RAG, Gemini API
- **Testing:** Pytest
- **Data Format:** CSV, JSON
- **Version Control:** Git and GitHub

## 5. Project Folder Structure

```text
CogniStream-Developer-Analytics/
│
├── data/
│   ├── developer_productivity_dataset.csv
│   └── cleaned_developer_productivity.csv
│
├── src/
│   ├── cleaning.py
│   ├── eda.py
│   ├── kpis.py
│   ├── validation.py
│   └── data_quality_report.py
│
├── rag/
│   ├── ingest.py
│   └── .gitkeep
│
├── dashboard/
│
├── reports/
│   ├── charts/
│   └── data_quality_report.json
│
├── tests/
│
├── docs/
├── notebooks/
├── requirements.txt
├── README.md
└── app.py
```

## 6. Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/Saniyakp786/CogniStream-Developer-Analytics.git
```

### Step 2: Open the project folder

```bash
cd CogniStream-Developer-Analytics
```

### Step 3: Create a virtual environment

```bash
python -m venv .venv
```

### Step 4: Activate the environment

Windows CMD:

```cmd
.venv\Scripts\activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

## 7. Running the Project

### Phase 1: Data Cleaning

```bash
python src/cleaning.py
```

Output:
- Cleaned developer productivity dataset.
- Data quality report in Markdown format.

### Phase 2: Exploratory Data Analysis

```bash
python src/eda.py
```

Output:
- EDA charts.
- Data analysis findings.

### Phase 3: Dashboard

```bash
streamlit run app.py
```

### Phase 4: RAG AI Assistant

Create a `.env` file using the example configuration:

```cmd
copy .env.example .env
```

Add your Gemini API key to the `.env` file.

Run:

```bash
python rag/ingest.py
streamlit run app.py
```

Optional neural embeddings:

```bash
pip install -r requirements-rag-extra.txt
```

## 8. Data Validation and Quality Reporting

CogniStream includes a reusable data validation module to check dataset quality.

### Validation checks

- Dataset is not empty.
- Required columns are present.
- Missing values.
- Duplicate records.
- Duplicate session IDs.
- Numeric values.
- Productivity score range.
- Date and time formats.
- Cross-field logical validation.

### Run data validation

```bash
python src/validation.py
```

The validation module generates a data quality summary containing:

- Total validation checks.
- Passed checks.
- Failed checks.
- Pass percentage.
- Overall status.
- Failed validation details.

The summary is exported to:

```text
reports/data_quality_report.json
```

## 9. Running Unit Tests

Run all project tests:

```bash
python -m pytest -v
```

Run a specific test file:

```bash
python -m pytest tests/test_validation.py -v
```

```bash
python -m pytest tests/test_data_quality_report.py -v
```

## 10. Development Progress

### Day 22 – RAG Retriever Improvements

- Improved text chunking.
- Fixed long-text splitting.
- Added retriever unit tests.
- Tested empty documents and chunk ID assignment.
- Result: 4 tests passed.

### Day 23 – RAG Pipeline Integration Testing

- Added integration tests.
- Tested Retriever search functionality.
- Tested Assistant and Retriever integration.
- Verified low-score document filtering.
- Result: 4 integration tests passed.
- Full test suite: 12 tests passed.

### Day 24 – RAG Index Persistence Testing

- Added RAG index persistence tests.
- Verified saved chunks and metadata.
- Validated embedding backend metadata.
- Verified saved NumPy vectors.
- Result: 4 persistence tests passed.
- Full test suite: 16 tests passed.

### Day 25 – Reusable Data Validation Module

- Created a reusable data validation module.
- Added checks for missing values, duplicates, numeric values, and data formats.
- Added validation unit tests.
- Result: 26 total tests passed.

### Day 26 – Advanced Data Validation

- Added cross-field logical validation.
- Checked focus duration against coding duration.
- Checked flow-state duration against focus duration.
- Result: 21 validation checks passed.
- Full test suite: 28 tests passed.

### Day 27 – Data Quality Summary Report

- Created a reusable data quality reporting module.
- Generated total, passed, and failed validation counts.
- Calculated validation pass percentage.
- Added failed-check details.
- Exported the report in JSON format.
- Added report unit tests.
- Result: 21 validation checks passed with 100% pass percentage.
- Full test suite: 32 tests passed.

### Day 28 – Project Documentation

- Improved the main README.md.
- Added project overview and objectives.
- Documented technologies and project structure.
- Added installation and execution instructions.
- Documented data validation and testing.
- Updated development progress through Day 27.

## 11. Testing Summary

Latest verified project test result:

**32 tests passed successfully.**

Data validation result:

- Total checks: 21
- Passed: 21
- Failed: 0
- Pass percentage: 100%

## 12. Repository

GitHub Repository:

https://github.com/Saniyakp786/CogniStream-Developer-Analytics

Branch: `Sani`

---

**Developed as part of the Infotact Solutions Data Analytics Internship.**