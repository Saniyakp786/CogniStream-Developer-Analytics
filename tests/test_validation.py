
import pandas as pd

from src.validation import validate_dataframe, REQUIRED_COLUMNS


def create_valid_dataframe():
    """Create a small valid dataset for testing."""

    data = {
        column: [1] for column in REQUIRED_COLUMNS
    }

    data.update({
        "developer_id": ["DEV001"],
        "session_id": ["SESSION001"],
        "session_date": ["2026-11-05"],
        "start_time": ["09:00:00"],
        "end_time": ["10:00:00"],
        "experience_level": ["Intermediate"],
        "task_type": ["Coding"],
        "task_complexity": ["Medium"],
        "cognitive_load_level": ["Medium"],
        "work_mode": ["Remote"],
        "productivity_score": [75],
        "coding_duration_minutes": [60],
        "focus_duration_minutes": [50],
        "flow_state_duration_minutes": [30],
    })

    return pd.DataFrame(data)


def get_status(results, check_name):
    for result in results:
        if result["check"] == check_name:
            return result["status"]

    raise AssertionError(f"Check not found: {check_name}")


def test_valid_dataset():
    df = create_valid_dataframe()
    results = validate_dataframe(df)

    assert all(r["status"] == "PASS" for r in results)


def test_empty_dataset():
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    results = validate_dataframe(df)

    assert get_status(results, "Dataset not empty") == "FAIL"


def test_missing_required_column():
    df = create_valid_dataframe()
    df = df.drop(columns=["developer_id"])

    results = validate_dataframe(df)

    assert get_status(results, "Required columns") == "FAIL"


def test_missing_values():
    df = create_valid_dataframe()
    df.loc[0, "task_type"] = None

    results = validate_dataframe(df)

    assert get_status(results, "Missing values") == "FAIL"


def test_duplicate_session_id():
    df = pd.concat(
        [create_valid_dataframe(), create_valid_dataframe()],
        ignore_index=True
    )

    results = validate_dataframe(df)

    assert get_status(results, "Duplicate session IDs") == "FAIL"


def test_negative_numeric_value():
    df = create_valid_dataframe()
    df.loc[0, "interruption_count"] = -5

    results = validate_dataframe(df)

    assert get_status(
        results, "Numeric values: interruption_count"
    ) == "FAIL"


def test_invalid_productivity_score():
    df = create_valid_dataframe()
    df.loc[0, "productivity_score"] = 120

    results = validate_dataframe(df)

    assert get_status(
        results, "Productivity score range (0-100)"
    ) == "FAIL"


def test_invalid_session_date():
    df = create_valid_dataframe()
    df.loc[0, "session_date"] = "invalid-date"

    results = validate_dataframe(df)

    assert get_status(results, "Session date format") == "FAIL"


def test_invalid_start_time():
    df = create_valid_dataframe()
    df.loc[0, "start_time"] = "invalid-time"

    results = validate_dataframe(df)

    assert get_status(
        results, "Time format: start_time"
    ) == "FAIL"


def test_original_dataframe_not_modified():
    df = create_valid_dataframe()
    original = df.copy(deep=True)

    validate_dataframe(df)

    pd.testing.assert_frame_equal(df, original)

def test_focus_duration_exceeds_coding_duration():
    df = create_valid_dataframe()
    df.loc[0, "focus_duration_minutes"] = 80
    df.loc[0, "coding_duration_minutes"] = 60

    results = validate_dataframe(df)

    assert get_status(
        results, "Focus duration <= Coding duration"
    ) == "FAIL"


def test_flow_duration_exceeds_focus_duration():
    df = create_valid_dataframe()
    df.loc[0, "flow_state_duration_minutes"] = 60
    df.loc[0, "focus_duration_minutes"] = 50

    results = validate_dataframe(df)

    assert get_status(
        results, "Flow duration <= Focus duration"
    ) == "FAIL"
