# Data Quality Summary

These are the results of the Phase 1 validation on the full dataset of 1000 rows and 20 columns. No rows were deleted and no values were overwritten.

## Checks that passed
There are no missing values, no duplicate rows, and no duplicate session_id values. All dates and times parse correctly, and end_time is after start_time in every row. There are no negative values and productivity_score stays within 0 to 100. In every row focus is at most coding, flow is at most focus, and coding plus break plus meeting equals the session length. Category labels are consistent.

## Issues flagged for review
These rows are unusual but are not confirmed errors, so they were kept and only flagged.
- Overlapping sessions: there are 35 pairs where the same developer has overlapping sessions on the same day, so 69 rows are flagged. This could be a data-entry issue or parallel logging.
- Low focus ratio: 59 sessions have focus time below 20 percent of coding time.
- Zero flow: 36 sessions have no flow time. This looks plausible for sessions with many interruptions.
- Outliers: a few sessions are outliers by the IQR rule in interruptions, context switches, flow minutes, tasks completed, bug count, and meeting minutes. They were kept as valid observations.
- Class imbalance: cognitive load has 675 High, 271 Medium, and only 54 Low sessions.

## Known limitations
The formulas for productivity_score and cognitive_load_level are not provided. The origin of the dataset is not stated, so it should not be presented as real-world evidence until the source is confirmed.
