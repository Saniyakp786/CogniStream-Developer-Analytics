
"""CogniStream - Reusable dataset validation module."""

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "developer_id",
    "session_id",
    "session_date",
    "start_time",
    "end_time",
    "experience_level",
    "task_type",
    "task_complexity",
    "coding_duration_minutes",
    "focus_duration_minutes",
    "interruption_count",
    "context_switch_count",
    "break_duration_minutes",
    "cognitive_load_level",
    "flow_state_duration_minutes",
    "tasks_completed",
    "bug_count",
    "meeting_minutes",
    "work_mode",
    "productivity_score",
]

NUMERIC_COLUMNS = [
    "coding_duration_minutes",
    "focus_duration_minutes",
    "interruption_count",
    "context_switch_count",
    "break_duration_minutes",
    "flow_state_duration_minutes",
    "tasks_completed",
    "bug_count",
    "meeting_minutes",
    "productivity_score",
]


def validate_dataframe(df):
    """Validate a DataFrame without modifying its records."""

    results = []

    def add_result(check, passed, details):
        results.append({
            "check": check,
            "status": "PASS" if passed else "FAIL",
            "details": details,
        })

    # Check 1: Empty dataset
    add_result(
        "Dataset not empty",
        not df.empty,
        f"{len(df)} rows found"
    )

    if df.empty:
        return results

    # Check 2: Required columns
    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]

    add_result(
        "Required columns",
        not missing_columns,
        f"Missing columns: {missing_columns}"
        if missing_columns else "All required columns are present"
    )

    # Stop checks that require unavailable columns
    available_columns = set(df.columns)

    # Check 3: Missing values
    null_count = int(df.isna().sum().sum())

    add_result(
        "Missing values",
        null_count == 0,
        f"{null_count} missing values found"
    )

    # Check 4: Duplicate records
    duplicate_rows = int(df.duplicated().sum())

    add_result(
        "Duplicate records",
        duplicate_rows == 0,
        f"{duplicate_rows} duplicate rows found"
    )

    # Check 5: Duplicate session IDs
    if "session_id" in available_columns:
        duplicate_ids = int(df["session_id"].duplicated().sum())

        add_result(
            "Duplicate session IDs",
            duplicate_ids == 0,
            f"{duplicate_ids} duplicate session IDs found"
        )

    # Check 6: Numeric values
    for col in NUMERIC_COLUMNS:
        if col not in available_columns:
            continue

        values = pd.to_numeric(df[col], errors="coerce")
        invalid_count = int(values.isna().sum())
        negative_count = int((values.dropna() < 0).sum())

        add_result(
            f"Numeric values: {col}",
            invalid_count == 0 and negative_count == 0,
            f"{invalid_count} invalid and {negative_count} negative values"
        )

    # Check 7: Productivity score range
    if "productivity_score" in available_columns:
        scores = pd.to_numeric(
            df["productivity_score"], errors="coerce"
        )

        invalid_scores = int(
            ((scores < 0) | (scores > 100)).sum()
        )

        add_result(
            "Productivity score range (0-100)",
            invalid_scores == 0,
            f"{invalid_scores} scores outside the valid range"
        )

    # Check 8: Date format
    if "session_date" in available_columns:
        dates = pd.to_datetime(
            df["session_date"], errors="coerce"
        )

        invalid_dates = int(dates.isna().sum())

        add_result(
            "Session date format",
            invalid_dates == 0,
            f"{invalid_dates} invalid dates found"
        )

    # Check 9: Time format
    for col in ["start_time", "end_time"]:
        if col not in available_columns:
            continue

        times = pd.to_datetime(
            df[col], format="%H:%M:%S", errors="coerce"
        )

        invalid_times = int(times.isna().sum())

        add_result(
            f"Time format: {col}",
            invalid_times == 0,
            f"{invalid_times} invalid time values"
        )

    return results


def validate_csv(file_path):
    """Load and validate a CSV file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    return validate_dataframe(df)


def print_validation_report(results):
    """Display validation results."""

    print("\nCogniStream - Data Validation Report")
    print("=" * 45)

    for result in results:
        print(
            f"[{result['status']}] "
            f"{result['check']}: {result['details']}"
        )

    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)

    print("=" * 45)
    print(f"Total checks: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    dataset = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "developer_productivity_dataset.csv"
    )

    report = validate_csv(dataset)
    print_validation_report(report)
