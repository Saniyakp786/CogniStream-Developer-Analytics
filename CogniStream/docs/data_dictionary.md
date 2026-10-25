# Data Dictionary

These descriptions come from the column names and the observed values. The dataset has no official data dictionary, so exact measurement methods are not known.

## Identifiers and time
- developer_id: identifier of the developer. There are 50 distinct developers.
- session_id: identifier of the work session. All 1000 values are unique.
- session_date: date of the session, from 2025-01-06 to 2025-10-10, weekdays only.
- start_time and end_time: session start and end time in HH:MM:SS format. end_time is after start_time in every row.

## Categories
- experience_level: Junior, Mid, Senior, or Lead.
- task_type: Feature Development, Bug Fixing, Code Review, Refactoring, Testing, DevOps/Deployment, or Documentation.
- task_complexity: Low, Medium, or High.
- cognitive_load_level: Low, Medium, or High. The rule that assigns this label is not provided.
- work_mode: Remote, Office, or Hybrid.

## Durations in minutes
- coding_duration_minutes: minutes spent coding in the session.
- focus_duration_minutes: minutes of focused work in the session.
- flow_state_duration_minutes: minutes spent in a flow state in the session.
- break_duration_minutes: minutes of breaks.
- meeting_minutes: minutes spent in meetings.

## Counts and scores
- interruption_count: number of interruptions in the session.
- context_switch_count: number of context switches in the session.
- tasks_completed: number of tasks completed.
- bug_count: number of bugs recorded.
- productivity_score: a score from 5 to 98 in this data. Its formula is not provided.

## Relationships that hold in every row
- flow_state_duration_minutes is never greater than focus_duration_minutes.
- focus_duration_minutes is never greater than coding_duration_minutes.
- coding_duration_minutes plus break_duration_minutes plus meeting_minutes equals the session length from start_time to end_time.

## Columns added by the cleaning step
- session_duration_minutes: end_time minus start_time, in minutes.
- focus_ratio: focus_duration_minutes divided by coding_duration_minutes.
- flow_ratio: flow_state_duration_minutes divided by focus_duration_minutes.
- flag_overlapping_session: true when the same developer has another session on the same day that overlaps in time.
- flag_low_focus_ratio: true when focus_ratio is below 0.2.
- flag_zero_flow: true when flow_state_duration_minutes is 0.
