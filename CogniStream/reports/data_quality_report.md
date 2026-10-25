# CogniStream - Data Quality Report

Raw rows: 1000 | Cleaned rows: 1000 | Rows deleted: 0

Cleaning rules: (1) strip whitespace in text columns, (2) parse dates/times, (3) add derived columns (session_duration_minutes, focus_ratio, flow_ratio), (4) add flag_* columns. No row was deleted and no value was overwritten.

| Status | Check | Result |
|---|---|---|
| INFO | Shape | 1000 rows x 20 columns |
| PASS | Unexpected extra columns | none |
| PASS | Missing values | none in any column |
| PASS | Duplicate rows | 0 |
| PASS | Duplicate session_id | 0 |
| INFO | Unique developers | 50 |
| PASS | Whitespace cleanup | 0 values changed |
| INFO | Categories: experience_level | {'Senior': 408, 'Mid': 307, 'Junior': 218, 'Lead': 67} |
| INFO | Categories: task_type | {'Feature Development': 302, 'Bug Fixing': 221, 'Code Review': 134, 'Refactoring': 96, 'Testing': 91, 'DevOps/Deployment': 89, 'Documentation': 67} |
| INFO | Categories: task_complexity | {'Medium': 481, 'Low': 290, 'High': 229} |
| INFO | Categories: cognitive_load_level | {'High': 675, 'Medium': 271, 'Low': 54} |
| INFO | Categories: work_mode | {'Remote': 430, 'Office': 302, 'Hybrid': 268} |
| PASS | Date parsing | 0 invalid dates; range 2025-01-06 to 2025-10-10 |
| INFO | Weekend sessions | 0 |
| PASS | Time parsing | 0 invalid time values |
| PASS | end_time after start_time | 0 rows violate this |
| PASS | Negative values | none |
| PASS | productivity_score within 0-100 | 0 rows outside |
| PASS | Logic: focus <= coding | 0 violations |
| PASS | Logic: flow <= focus | 0 violations |
| PASS | Logic: coding <= session length | 0 violations |
| PASS | Logic: coding + break + meeting = session length | 0 rows differ |
| INFO | IQR outliers (kept, not removed) | {'interruption_count': 13, 'context_switch_count': 24, 'flow_state_duration_minutes': 6, 'tasks_completed': 2, 'bug_count': 6, 'meeting_minutes': 1} |
| FLAG | Flag: overlapping sessions (same developer, same day) | 35 overlapping pairs; 69 rows flagged (kept) |
| FLAG | Flag: focus/coding ratio < 0.2 | 59 rows (kept) |
| INFO | Flag: flow-state = 0 minutes | 36 rows (kept; plausible with many interruptions) |
| FLAG | Class balance: cognitive_load_level | {'High': 675, 'Medium': 271, 'Low': 54} - Low is small, interpret with care |
| FLAG | productivity_score definition | Formula/source NOT provided. A linear fit on other numeric columns gives R2=0.89, so it is related to them but the exact formula is unknown. Do not invent one. |
| FLAG | cognitive_load_level definition | Rule/source NOT provided. Levels overlap in interruptions and context switches, so it is not a simple threshold. Treat it as a given label. |
| FLAG | Data origin | Source of dataset (real or synthetic) is not stated. Confirm with mentor before calling results real-world evidence. |

**Legend:** PASS = no problem found; FLAG = needs review or caution; INFO = descriptive only.
Flagged rows are unusual but NOT confirmed errors.