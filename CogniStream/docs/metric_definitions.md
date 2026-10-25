# Metric Definitions

## Flow-state duration
In this project flow-state duration means the value of the column flow_state_duration_minutes: the minutes in a session that the dataset records as flow state. The dataset does not say how flow was detected or measured, so no further definition can be given. In every row the flow minutes are at most the focus minutes.

## Productivity score
Productivity is measured by the column productivity_score, which ranges from 5 to 98. The dataset does not provide the formula or source of this score. A linear fit using the other numeric columns explains about 89 percent of its variation (R squared 0.89), so the score is related to those columns, but the exact formula is unknown and must not be invented.

## Cognitive load level
cognitive_load_level has three labels: Low, Medium, and High. The rule that assigns them is not provided. Their ranges of interruptions and context switches overlap, so the label is not a simple threshold on one column. It is treated as a given label. In the full dataset 675 sessions are High, 271 Medium, and 54 Low, so Low is a small group and its averages are less reliable.

## KPIs shown in the dashboard
All KPIs are calculated by the Python file src/kpis.py.
- Average productivity score: mean of productivity_score.
- Average focus, coding, and flow minutes: means of the matching duration columns.
- Average interruptions and context switches: means of interruption_count and context_switch_count.
- High cognitive load percent: share of sessions with cognitive_load_level equal to High.
- Flow share of focus: total flow minutes divided by total focus minutes.
- Spearman correlation: a rank-based association between two numeric columns, from minus 1 to plus 1. It describes association only and does not show cause and effect.
