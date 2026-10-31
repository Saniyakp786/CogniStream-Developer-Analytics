# CogniStream – Data Quality Report

## Day 19: Dataset Quality Inspection

### 1. Dataset Overview

| Metric | Result |
|---|---:|
| Dataset Name | developer_productivity_dataset.csv |
| Total Records | 1,000 |
| Total Columns | 20 |
| Unique Developers | 50 |
| Unique Sessions | 1,000 |

### 2. Missing Value Analysis

All 20 columns were checked for missing values.

- Total missing values: 0
- Missing value percentage: 0%

**Result:** No missing values were detected.

### 3. Duplicate Analysis

- Total duplicate rows: 0
- Duplicate percentage: 0%

**Result:** No duplicate records were detected.

### 4. Data Type Analysis

The dataset contains:
- Text columns for developer details, task information, dates and work modes.
- Numeric columns for coding duration, focus duration, interruptions, context switches, completed tasks, bugs and productivity score.

Date and time columns are currently stored as strings.

### 5. Unique Value Analysis

| Column | Unique Values |
|---|---:|
| developer_id | 50 |
| session_id | 1,000 |
| session_date | 200 |
| experience_level | 4 |
| task_type | 7 |
| task_complexity | 3 |
| cognitive_load_level | 3 |
| work_mode | 3 |

### 6. Numeric Summary

| Metric | Average |
|---|---:|
| Coding Duration | 138.18 minutes |
| Focus Duration | 90.10 minutes |
| Interruptions | 3.70 |
| Context Switches | 5.07 |
| Break Duration | 23.30 minutes |
| Flow State Duration | 24.29 minutes |
| Tasks Completed | 2.65 |
| Bug Count | 1.15 |
| Meeting Duration | 32.74 minutes |
| Productivity Score | 49.09 |

### 7. Final Data Quality Status

**Status: GOOD**

The dataset contains 1,000 records and 20 columns, with zero missing values and zero duplicate rows.

### 8. Conclusion

The dataset passed the basic missing-value and duplicate-record checks. It is suitable for further exploratory data analysis and dashboard development based on these checks.

Further validation of date/time formats, value ranges and business rules can improve data reliability.

---
**Project:** CogniStream – Developer Flow-State & Cognitive Load Analytics  
**Activity:** Day 19 – Data Quality Inspection