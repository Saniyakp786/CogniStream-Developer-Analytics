# CogniStream: Visualization Guide (Power BI-style upgrade)

Code layout
- `src/kpis.py`: every number (unchanged, single source of truth)
- `dashboard/chart_data.py`: reshapes data for charts (pure pandas, unit-tested)
- `dashboard/charts.py`: Plotly figure builders (no Streamlit calls)
- `dashboard/powerbi_style.py`: palette, templates, CSS, KPI cards, visual tiles
- `dashboard/views.py`: page layout, filters' empty states (AI Assistant and Reports pages unchanged)

## Chart catalogue

| Page | Visual | Question it answers | Why this chart |
|---|---|---|---|
| Overview | KPI cards with "vs all sessions" line | How does this selection compare with everything? | Context turns a number into a signal |
| Overview | Bullet gauge | Where does average productivity sit against the full dataset? | Neutral track: the score formula is not provided, so no good/bad bands are invented |
| Overview | Donut | What share of sessions is Low / Medium / High load? | Part-to-whole with 3 parts; total sits in the hole |
| Overview | Monthly trend (marker area = sessions) | Is productivity moving over time? | Marker size and hollow markers show how thin each month is |
| Overview | Developer lollipop (Top/Bottom 10, minimum-session slider) | Who is highest / lowest? | Ranked values with little ink; eligibility rule stops 1-session flukes |
| Productivity | Bubble scatter + binned-average line | Does more flow mean more productivity? | Shows every session, load level and focus time; trend line cuts through overplotting |
| Productivity | Interruption-band lollipop | Do interruptions cost productivity? | Few ordered bands suit a dot-and-stem plot |
| Productivity | 2x2 small multiples (task type, work mode, experience, complexity) | Which groups are more productive? | Same x-scale in every panel, n in every label |
| Productivity | Spearman heatmap (lower triangle) | Which measures move together? | Each pair once, diverging colours, values in cells |
| Cognitive load | Count bars | How many sessions per load level? | Labels carry count, share and a small-sample flag |
| Cognitive load | Complexity x load heatmap | Does harder work raise load? | Row percentages (rows sum to 100%) with n in each cell |
| Cognitive load | Violin or box (selectable measure) | How is a measure spread within each load level? | Violin only when every group has 30+ sessions, otherwise box plus every point |
| Cognitive load | 4 mini bar charts | How do focus, flow, interruptions, productivity differ by load? | Units differ, so each has its own scale |
| Flow | 2-D density + binned line | How do flow and productivity relate? | Density stays readable when points overlap (differs from the bubble chart on purpose) |
| Flow | Bars + line by interruption band | Do interruptions shorten flow and lower productivity? | Two measures on one band axis |
| Flow | Stacked histogram + median | How long is a typical flow period? | Stacked by load with shared bin edges |
| Flow | Dot plot by task type | Which task types support more flow? | Ranked dots, n in labels |

## Colour rules
- Green / amber / red = Low / Medium / High cognitive load (also good/bad deltas). Used for nothing else.
- Productivity = blue, focus = navy, flow = purple, interruptions = orange, on every page.
- Hollow markers or hatched bars = fewer than 30 sessions.

## Interaction
Hover tooltips with n on every chart; legend click to isolate a load level; sidebar filters
(date range, experience, work mode, task type, complexity) drive every page; page-level controls
(Top/Bottom 10, minimum sessions, measure selector); empty and small-sample states.

## Requirements and tests
- Plotly 5+ (hatched bars), Streamlit 1.29+ (bordered tiles; older versions fall back to plain containers).
- `python tests/test_chart_data.py` runs the data-prep tests against `data/cleaned_developer_productivity.csv`.
