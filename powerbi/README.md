# CogniStream — Power BI Desktop export

Build the **same 6 report pages** as the Streamlit app, using the cleaned CSV and DAX measures that match `src/kpis.py`.

## 0. Prepare the data file (one-time)

From the project root (`CogniStream/`):

```powershell
python src/cleaning.py
python src/export_powerbi.py
```

This copies `data/cleaned_developer_productivity.csv` → `powerbi/data/cleaned_developer_productivity.csv`.

## 1. Get Data

1. Open **Power BI Desktop**.
2. **Home → Get data → Text/CSV**.
3. Select `powerbi/data/cleaned_developer_productivity.csv`.
4. Click **Transform Data** (Power Query) before loading.

## 2. Set data types (Power Query)

| Column | Type |
|--------|------|
| developer_id, session_id | Text (or Whole Number if all numeric IDs) |
| session_date | Date |
| start_time, end_time | Time or Text |
| experience_level, task_type, task_complexity, cognitive_load_level, work_mode | Text |
| coding_duration_minutes, focus_duration_minutes, flow_state_duration_minutes, break_duration_minutes, meeting_minutes | Decimal Number |
| interruption_count, context_switch_count, tasks_completed, bug_count | Whole Number |
| productivity_score | Decimal Number |

Close & Apply. Rename the table to **DeveloperProductivity** (so the DAX in `measures.dax` works as written).

## 3. Add calculated columns and measures

1. Open `powerbi/measures.dax` in a text editor.
2. In Power BI: **Model view** or **Report view → New column / New measure**.
3. Paste each calculated column first:
   - `Interruption Band`
   - `Cognitive Load Sort`
4. Then create each measure (`Sessions`, `Developers`, `Avg Productivity`, …).
5. Select column `cognitive_load_level` → **Column tools → Sort by column → Cognitive Load Sort**.

## 4. Apply the report theme

**View → Themes → Browse for themes** → select `powerbi/theme.json`.

Palette: `#118DFF`, `#12239E`, `#E66C37`, `#6B007B`, `#E044A7`, `#744EC2`, `#D9B300`, `#D64550`.  
Semantic load colours (use in legends/conditional formatting): Low `#2BA84A`, Medium `#F2C811`, High `#D64550`.  
Font: Segoe UI.

## 5. Add slicers (Filters pane feel)

On every page (or on a shared filter page synced with sync-slicers):

- Experience level (slicer)
- Work mode (slicer)
- Task type (slicer)
- Task complexity (slicer)
- session_date (Between date slicer)

Optional: put slicers on the left in a narrow column to mimic the Streamlit sidebar.

## 6. Build the 6 pages

Create six report pages with these names and visuals.

### Page 1 — Overview

| Visual | Fields / measures |
|--------|-------------------|
| **Card** × 8 | Sessions, Developers, Avg Productivity, Avg Focus Minutes, Avg Flow Minutes, Avg Interruptions, High Load %, Flow Share of Focus % |
| **Gauge** | Avg Productivity (axis 0–100) |
| **Donut** | Legend: cognitive_load_level; Values: Count of session_id (data labels on) |
| **Line + area** | Axis: Month of session_date; Values: Avg Productivity (markers on) |
| **Clustered bar** | Top 10: developer_id by Avg Productivity (filter: sessions ≥ 5 via visual-level filter on Count of session_id) |

### Page 2 — Productivity Analysis

| Visual | Fields |
|--------|--------|
| **Scatter (bubble)** | X: flow_state_duration_minutes; Y: productivity_score; Legend: cognitive_load_level; Size: focus_duration_minutes |
| **Clustered column** | Axis: Interruption Band; Values: Avg Productivity (data labels, 1 decimal) |
| **Clustered column** | Axis: task_type / work_mode / experience_level (use bookmarks or separate visuals); Values: Avg Productivity |
| **Matrix** | Rows: category; Values: averages (conditional formatting colour scale) |

### Page 3 — Cognitive Load Analysis

| Visual | Fields |
|--------|--------|
| **Donut** | cognitive_load_level share |
| **Box plot** or **Clustered column** | Interruptions / context switches by cognitive_load_level |
| **Matrix** | Rows: task_complexity; Columns: cognitive_load_level; Values: % of row (show value as % of row total) + colour scale |
| **Table / Matrix** | summary by cognitive_load_level (Avg Productivity, Avg Focus, Avg Flow, …) |

### Page 4 — Flow-State Analysis

| Visual | Fields |
|--------|--------|
| **Card** | Avg Flow Minutes; Sessions with Zero Flow |
| **Scatter** | Flow vs productivity_score, colour = cognitive_load_level |
| **Box / column** | Flow by Interruption Band |
| **Histogram** (or column on bins) | flow_state_duration_minutes distribution |
| **Clustered column** | Avg Flow Minutes by task_type |

### Page 5 — AI Assistant

Power BI Desktop has no Gemini chat. Options:

- Keep a **text box** explaining that the AI Assistant lives in the Streamlit app (`streamlit run app.py`).
- Or embed a link/button to the Streamlit URL if you host it.

Do **not** send raw CSV rows to any external API from Power BI without a reviewed privacy design.

### Page 6 — Reports

- **Table** of key measures
- Button / instructions to export data from Power BI (**… → Export data**)
- Optional: paste summaries from `reports/data_quality_report.md` and `reports/eda_findings.md` into text boxes

## 7. Caution text (add as a text box on Overview)

> Charts show associations, not causation. Formulas of `productivity_score` and `cognitive_load_level` are not provided. Dataset origin is not confirmed.

## 8. Small-sample warning

The Low cognitive-load group is small (~54 sessions in the full file). When a slicer leaves a group under **30 sessions**, treat averages as unreliable (same rule as the Streamlit app).

## File list in this folder

| File | Purpose |
|------|---------|
| `README.md` | This guide |
| `measures.dax` | DAX columns + measures aligned with `src/kpis.py` |
| `theme.json` | Report theme (palette + Segoe UI) |
| `data/cleaned_developer_productivity.csv` | Created by `python src/export_powerbi.py` |
