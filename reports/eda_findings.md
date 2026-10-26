# CogniStream - EDA Findings (auto-generated from the data)

Important: these are ASSOCIATIONS in this dataset. They do not prove cause and effect. The origin of the dataset (real or synthetic) is not confirmed, and the formulas for productivity_score and cognitive_load_level are unknown.

## Headline KPIs
- sessions: 1000
- developers: 50
- avg productivity score: 49.1
- avg coding minutes: 138.2
- avg focus minutes: 90.1
- avg flow minutes: 24.3
- avg interruptions: 3.7
- avg context switches: 5.07
- pct high cognitive load: 67.5
- pct sessions with flow: 96.4
- flow share of focus pct: 27.0

## Cognitive load
| cognitive_load_level   |   sessions |   percent |
|:-----------------------|-----------:|----------:|
| Low                    |         54 |       5.4 |
| Medium                 |        271 |      27.1 |
| High                   |        675 |      67.5 |

Averages by load level:

| cognitive_load_level   |   sessions |   avg_productivity |   avg_focus |   avg_flow |   avg_interruptions |   avg_context_switches |
|:-----------------------|-----------:|-------------------:|------------:|-----------:|--------------------:|-----------------------:|
| Low                    |         54 |              69.67 |      117.38 |      44.29 |                1.17 |                   2.06 |
| Medium                 |        271 |              59.92 |      104.37 |      33.93 |                2.4  |                   3.55 |
| High                   |        675 |              43.1  |       82.19 |      18.82 |                4.43 |                   5.91 |

- High-load sessions average productivity 43.1 vs 69.67 for Low-load sessions (Low has only 54 sessions, so treat with care).

## Interruptions
| interruption_count   |   sessions |   avg_productivity |   avg_flow |
|:---------------------|-----------:|-------------------:|-----------:|
| 0-1                  |        133 |              69.94 |      46.04 |
| 2-3                  |        369 |              55.44 |      29.7  |
| 4-5                  |        325 |              42.23 |      16.81 |
| 6+                   |        173 |              32.41 |      10.06 |

- Sessions with 0-1 interruptions average 69.94 productivity; sessions with 6+ interruptions average 32.41.

## Spearman correlation with productivity_score
|                             |   rho |
|:----------------------------|------:|
| interruption_count          | -0.61 |
| context_switch_count        | -0.57 |
| bug_count                   | -0.4  |
| meeting_minutes             | -0.35 |
| break_duration_minutes      |  0.35 |
| coding_duration_minutes     |  0.66 |
| tasks_completed             |  0.68 |
| focus_duration_minutes      |  0.81 |
| flow_state_duration_minutes |  0.9  |

## By experience level
| experience_level   |   sessions |   avg_productivity |   avg_focus |   avg_flow |   avg_interruptions |   avg_context_switches |
|:-------------------|-----------:|-------------------:|------------:|-----------:|--------------------:|-----------------------:|
| Junior             |        218 |              43.57 |       86.37 |      18.27 |                3.52 |                   4.95 |
| Lead               |         67 |              47.65 |       83.68 |      24    |                4.21 |                   5.51 |
| Mid                |        307 |              49.77 |       89.56 |      23.61 |                3.54 |                   4.84 |
| Senior             |        408 |              51.78 |       93.56 |      28.06 |                3.84 |                   5.22 |

## By work mode
| work_mode   |   sessions |   avg_productivity |   avg_focus |   avg_flow |   avg_interruptions |   avg_context_switches |
|:------------|-----------:|-------------------:|------------:|-----------:|--------------------:|-----------------------:|
| Hybrid      |        268 |              49.97 |       95.9  |      25.15 |                3.62 |                   5.04 |
| Office      |        302 |              43.52 |       81.03 |      19.57 |                4.83 |                   6.15 |
| Remote      |        430 |              52.46 |       92.86 |      27.06 |                2.96 |                   4.32 |

## By task type
| task_type           |   sessions |   avg_productivity |   avg_focus |   avg_flow |   avg_interruptions |   avg_context_switches |
|:--------------------|-----------:|-------------------:|------------:|-----------:|--------------------:|-----------------------:|
| Bug Fixing          |        221 |              46.74 |       84.99 |      22.88 |                3.84 |                   5.95 |
| Code Review         |        134 |              52.71 |       92.63 |      26.12 |                3.62 |                   5.82 |
| DevOps/Deployment   |         89 |              50.05 |       92.65 |      23.58 |                3.84 |                   4.88 |
| Documentation       |         67 |              54.43 |       88.31 |      24.57 |                3.52 |                   3.73 |
| Feature Development |        302 |              45.82 |       88.3  |      23.65 |                3.64 |                   4.86 |
| Refactoring         |         96 |              54.24 |      102.87 |      28.31 |                3.81 |                   3.94 |
| Testing             |         91 |              50.03 |       90.14 |      23.34 |                3.58 |                   4.82 |

## By task complexity
| task_complexity   |   sessions |   avg_productivity |   avg_focus |   avg_flow |   avg_interruptions |   avg_context_switches |
|:------------------|-----------:|-------------------:|------------:|-----------:|--------------------:|-----------------------:|
| High              |        229 |              47.07 |       91.35 |      22.84 |                3.58 |                   4.91 |
| Low               |        290 |              49.49 |       89.64 |      22.41 |                3.69 |                   5.06 |
| Medium            |        481 |              49.82 |       89.79 |      26.11 |                3.77 |                   5.14 |

## Monthly trend
- First month (2025-01) average productivity 51.14, last month (2025-10) 49.62.

| session_date   |   sessions |   avg_productivity |   avg_flow |   avg_interruptions |
|:---------------|-----------:|-------------------:|-----------:|--------------------:|
| 2025-01        |         87 |              51.14 |      26.59 |                3.47 |
| 2025-02        |        107 |              49.29 |      25.07 |                3.72 |
| 2025-03        |        104 |              49.39 |      25.3  |                3.83 |
| 2025-04        |         94 |              49.16 |      23.65 |                3.65 |
| 2025-05        |        113 |              49.17 |      24.17 |                3.79 |
| 2025-06        |         98 |              46.77 |      21.42 |                3.94 |
| 2025-07        |        134 |              48.43 |      23.43 |                3.72 |
| 2025-08        |        114 |              48.3  |      22.09 |                3.82 |
| 2025-09        |        100 |              50.46 |      26.88 |                3.54 |
| 2025-10        |         49 |              49.62 |      25.69 |                3.27 |