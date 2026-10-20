
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANING_SCRIPT = PROJECT_ROOT / "src" / "cleaning.py"
CLEANED_DATA = PROJECT_ROOT / "data" / "cleaned_developer_productivity.csv"
QUALITY_REPORT = PROJECT_ROOT / "reports" / "data_quality_report.md"


@pytest.fixture(scope="session")
def cleaning_run():
    """Run the cleaning script once before the tests."""
    result = subprocess.run(
        [sys.executable, str(CLEANING_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, (
        f"Cleaning script failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    return result


def test_cleaning_script_runs_successfully(cleaning_run):
    assert cleaning_run.returncode == 0


def test_cleaned_dataset_exists(cleaning_run):
    assert CLEANED_DATA.is_file()


def test_cleaned_dataset_has_rows_and_columns(cleaning_run):
    df = pd.read_csv(CLEANED_DATA)
    assert not df.empty
    assert len(df.columns) > 0


def test_cleaned_dataset_has_no_missing_values(cleaning_run):
    df = pd.read_csv(CLEANED_DATA)
    assert not df.isna().any().any()


def test_session_ids_are_unique(cleaning_run):
    df = pd.read_csv(CLEANED_DATA)
    assert "session_id" in df.columns
    assert not df["session_id"].duplicated().any()


def test_quality_report_exists(cleaning_run):
    assert QUALITY_REPORT.is_file()
    assert QUALITY_REPORT.stat().st_size > 0
