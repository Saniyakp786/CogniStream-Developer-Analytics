# CogniStream - Power BI Desktop guide

This folder lets you rebuild the CogniStream report in **Power BI Desktop**.

> **Important**
> - The Streamlit dashboard uses **Plotly** charts. Plotly charts are not Power BI visuals, so they cannot be copied into Power BI. This guide tells you how to build the *equivalent* native visuals.
> - **No `.pbix` file is included.** A `.pbix` can only be created in Power BI Desktop, so you build it by following the steps below.
> - Numbers are meant to match the Streamlit app and `src/kpis.py`. After building a page, compare the cards with the Streamlit app (same filters) to confirm.
> - Caution that must stay visible on the report: *charts show associations, not causation; the formulas of `productivity_score` and `cognitive_load_level` are not provided; the dataset origin (real or synthetic) is not confirmed.*

## 0. Prepare the data files (one time)

From the project root (`CogniStream/`):

```powershell
python src/cleaning.py
python src/export_powerbi.py
```

This creates, in `powerbi/data/`:

| File | Use |
|------|-----|
| `cleaned_developer_productivity.csv` | main table (1 row = 1 session) |
| `correlation_matrix_spearman.csv` | fixed Spearman correlations of ALL sessions, for the heatmap matrix (does **not** react to slicers) |

## 1. Load data and set types

1. **Home > Get data > Text/CSV** > `powerbi/data/cleaned_developer_productivity.csv` > **Transform Data**.
2. Set the types:

| Column | Type |
|--------|------|
| developer_id, session_id | Text |
| session_date | Date |
| start_time, end_time | Time or Text |
| experience_level, task_type, task_complexity, cognitive_load_level, work_mode | Text |
| coding / focus / flow / break / meeting minutes | Decimal Number |
| interruption_count, context_switch_count, tasks_completed, bug_count | Whole Number |
| productivity_score | Decimal Number |

3. **Close & Apply**, then rename the table to **DeveloperProductivity** (the DAX uses this name).
4. Load `correlation_matrix_spearman.csv` as a second table named **CorrelationSnapshot** (no relationship needed).

## 2. Add columns and measures

Open `measures.dax`. In **Report view > New column / New measure**:

1. Create the **calculated columns** first: `Interruption Band`, `Cognitive Load Sort`, `Month Start`, `Interruption Band Sort`, `Experience Sort`, `Work Mode Sort`, `Complexity Sort`, `Flow Bin`.
2. Set **Sort by column** (Column tools):

| Column | Sort by |
|--------|---------|
| cognitive_load_level | Cognitive Load Sort |
| Interruption Band | Interruption Band Sort |
| experience_level | Experience Sort |
| work_mode | Work Mode Sort |
| task_complexity | Complexity Sort |

3. Create every **measure** in the file (original ones first, then the section "Added for the Power BI-style chart upgrade").
4. Format measures: averages 1 decimal, `Avg Interruptions` 2 decimals, `%` measures 1 decimal with a `%` suffix (the DAX already multiplies by 100, so use format "0.0" and add the suffix in the card label).

## 3. Theme

**View > Themes > Browse for themes** > `theme.json`.
Colours: primary blue `#118DFF`, navy `#12239E`, purple `#744EC2`, orange `#E66C37`. Cognitive load always uses **Low `#2BA84A`, Medium `#F2C811`, High `#D64550`**.
If Power BI reports a theme error, tell me the message; the JSON itself is valid.

### Cognitive-load colours on every visual that uses the load legend
Theme colours are assigned in order, so set the load colours yourself: select the visual > **Format > Visual > Legend/Colors** (or *Data colors*) > set Low / Medium / High to the three colours above. Do this for the donut, scatter, histogram and bar charts that use `cognitive_load_level`.

## 4. Slicers and interactions

Add these slicers on every page (or on page 1 and use **View > Sync slicers**):

| Slicer | Field | Style |
|--------|-------|-------|
| Date range | session_date | Between |
| Experience level | experience_level | Dropdown or list |
| Work mode | work_mode | List |
| Task type | task_type | Dropdown |
| Task complexity | task_complexity | List |

Add a **button > Clear all slicers** (Insert > Buttons > Clear all slicers) as the reset button.
**Interactions:** select a slicer, then **Format > Edit interactions** and keep *Filter* on every chart. For the CorrelationSnapshot matrix choose *None* (it is a fixed snapshot).
Cross-highlighting between charts (clicking a donut slice or a bar) already works: click an element to filter the other visuals; click again or on empty space to clear.

## 5. Pages and visuals

Use a white tile background and a 4 px radius (the theme does this). Titles: Segoe UI Semibold 14.

### Page 1 - Overview

| Visual | Type | Fields | Formatting |
|--------|------|--------|-----------|
| 8 KPI cards | **Card (new)** or Card | Sessions, Developers, Avg Productivity, Avg Focus Minutes, Avg Flow Minutes, Avg Interruptions, High Load %, Flow Share of Focus % | Add reference label: for Avg Productivity use **Avg Productivity Context** (or the new card "reference labels"). Colour the context text: **Format > Callout value / Reference label > Font color > fx > Rules**: `Avg Productivity vs All` >= 0 -> `#2BA84A`, < 0 -> `#D64550`. |
| Productivity bullet | **Gauge** (Power BI has no bullet shape: use the **Bullet Chart** visual from AppSource if you want exact parity) | Value: Avg Productivity; Min 0; Max 100; Target: Avg Productivity (All Sessions) | Target marker colour orange `#E66C37`. |
| Cognitive load donut | **Donut chart** | Legend: cognitive_load_level; Values: Sessions | Data labels: *Category, percent of total*; detail labels outside; load colours; Rotation off. Tooltip: add `Load Share %`. |
| Monthly trend | **Line and clustered column chart** | X axis: Month Start (continuous date); Column Y: Sessions; Line Y: Avg Productivity | Line markers on, data labels on for the line (1 decimal); columns light blue (`#118DFF` at 75 % transparency). Add **Analytics > Constant line** = Avg Productivity (All Sessions) is not possible for a measure, so use **Average line** on the line series. Tooltip: Sessions, Avg Flow Minutes, Avg Interruptions, Small Sample Flag. |
| Developer ranking | **Clustered bar chart** (use a **Lollipop** custom visual from AppSource for the stick-and-dot look) | Y axis: developer_id; X axis: Eligible Avg Productivity | **Filters pane > visual-level filter on developer_id > Top N = 10 by Eligible Avg Productivity**. Sort descending. Data labels 1 decimal. Tooltip: Sessions. The measure is blank for developers with fewer than 5 sessions, so they are not ranked. |
| Caution text | **Text box** | the caution sentence at the top of this file | |

### Page 2 - Productivity Analysis

| Visual | Type | Fields | Formatting |
|--------|------|--------|-----------|
| Flow vs productivity | **Scatter chart** | X: flow_state_duration_minutes (do not aggregate: *Don't summarize*); Y: productivity_score (*Don't summarize*); Legend: cognitive_load_level; Size: focus_duration_minutes; Details: session_id | Load colours; marker transparency ~25 %. Tooltips: developer_id, task_type, task_complexity, interruption_count, Cognitive load. Add **Analytics > Trend line** only if you describe it as association. |
| Productivity by interruption band | **Clustered bar** (or Lollipop visual) | Axis: Interruption Band; Values: Avg Productivity | Data labels 1 decimal; Analytics > **Average line** for the overall level. Tooltips: Sessions, Small Sample Flag. Conditional format: **Data colors > fx > Rules** on `Sessions` < 30 -> grey `#A19F9D`. |
| Group comparison (small multiples) | **Clustered bar chart** with **Small multiples** | Axis: task_type; Values: Avg Productivity; **Small multiples: work_mode** (or experience_level) | Sort axis by value. To compare task type, work mode and experience level, make three copies of the visual, or one visual plus a **field parameter** (Modeling > New parameter > Fields) holding task_type, work_mode, experience_level and put it on the axis. Add a slicer for the field parameter. |
| Summary matrix | **Matrix** | Rows: a field parameter or task_type; Values: Sessions, Avg Productivity, Avg Focus Minutes, Avg Flow Minutes, Avg Interruptions | **Cell elements > Background color > fx > Gradient** on Avg Productivity (min `#FFFFFF`, max `#118DFF`). Add Small Sample Flag as a value. |
| Correlation heatmap | **Matrix** (heatmap look) on **CorrelationSnapshot** | Rows: variable_x; Columns: variable_y; Values: **Sum of spearman_rho** (one row per pair, so the sum is the value) | **Background color > fx > Gradient with 3 colours**: minimum -1 `#E66C37`, centre 0 `#FFFFFF`, maximum 1 `#118DFF`. Show values with 2 decimals. Note on the visual: *snapshot of all sessions; does not change with slicers; association only.* |

### Page 3 - Cognitive Load Analysis

| Visual | Type | Fields | Formatting |
|--------|------|--------|-----------|
| Load distribution | **Donut** or **Clustered column** | Legend/Axis: cognitive_load_level; Values: Sessions | Load colours, labels on, order Low-Medium-High (sort column set in step 2). |
| Complexity x load heatmap | **Matrix** | Rows: task_complexity; Columns: cognitive_load_level; Values: **Load Share %** and Sessions | Background colour gradient on Load Share % (white to `#118DFF`, min 0, max 100). Each row adds up to 100 %. Add Small Sample Flag as a tooltip. |
| Box / distribution | Power BI has no native box plot. Use the **Box and Whisker chart** from AppSource, or a **Clustered column** of Avg per level | Category: cognitive_load_level; Values: the metric | Use box plots only when each level has at least 10 sessions (the Low group has about 54 sessions in the full file, so check the Sessions card first). |
| Comparison by load | **Clustered column chart** x4 (or **Small multiples**) | Axis: cognitive_load_level; Values: Avg Focus Minutes, Avg Flow Minutes, Avg Interruptions, Avg Productivity (one visual per measure because the scales differ) | Load colours as *Data colors > fx > Field value > Load Color*. Add Sessions in the tooltip and Small Sample Flag. |
| Summary table | **Table / Matrix** | Rows: cognitive_load_level; Values: Sessions, Avg Productivity, Avg Focus Minutes, Avg Flow Minutes, Avg Interruptions, Avg Context Switches | Gradient on each column. |

### Page 4 - Flow-State Analysis

| Visual | Type | Fields | Formatting |
|--------|------|--------|-----------|
| Cards | **Card** | Avg Flow Minutes, Sessions with Zero Flow, Zero Flow % | |
| Flow distribution | **Stacked column chart** | X: Flow Bin; Legend: cognitive_load_level; Y: Sessions | X axis type *Continuous* if available; load colours; gap 5 %. |
| Flow vs productivity | **Scatter chart** | same as page 2 | |
| Average flow by task type | **Clustered bar** (or Lollipop) | Axis: task_type; Values: Avg Flow Minutes | Sort descending; labels 1 decimal; Small Sample Flag in tooltip. |
| Interruption bands | **Clustered column** (two visuals) | Axis: Interruption Band; Values: Avg Flow Minutes / Zero Flow % | Sorted by Interruption Band Sort. |

### Page 5 - AI Assistant
Power BI Desktop does not have the Gemini chat. Add a text box saying the assistant lives in the Streamlit app (`streamlit run app.py`). Do not send raw rows to an external API from Power BI without a reviewed privacy design.

### Page 6 - Reports
A **Table** of key measures, instructions to use *... > Export data*, and optional text boxes with the summaries from `reports/data_quality_report.md` and `reports/eda_findings.md`.

## 6. Small-sample rule
A group with fewer than **30 sessions** is unreliable (same rule as the Streamlit app). Show **Small Sample Flag** in tooltips and use the grey conditional colour on `Sessions` < 30. In the full file the Low cognitive-load group has about 54 sessions, so it becomes small as soon as a slicer narrows the data.

## 7. Streamlit vs Power BI differences (be honest in your report)
- Spearman correlations are calculated in Python. In Power BI the heatmap shows a **fixed snapshot** exported by `src/export_powerbi.py`.
- The Streamlit gauge is a true bullet gauge; Power BI's built-in gauge is a half-circle (a bullet visual needs an AppSource custom visual).
- Box plots and lollipop charts need AppSource custom visuals in Power BI; the guide names a native alternative for each.
- Hover tooltips, sort orders and colours were designed to match, but the two tools will never look pixel-identical.

## File list in this folder

| File | Purpose |
|------|---------|
| `README.md` | This guide |
| `measures.dax` | DAX columns + measures aligned with `src/kpis.py` |
| `theme.json` | Report theme (palette, Segoe UI, page background, grid lines) |
| `data/cleaned_developer_productivity.csv` | Created by `python src/export_powerbi.py` |
| `data/correlation_matrix_spearman.csv` | Created by `python src/export_powerbi.py` |
