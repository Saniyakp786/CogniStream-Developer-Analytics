import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "developer_productivity_dataset.csv"


def validate_dataset(df):
    print("\n===== DAY 20: DATA VALIDATION =====")

    missing_ids = df["developer_id"].isnull().sum()
    print(f"Missing Developer IDs: {missing_ids}")

    duplicate_sessions = df["session_id"].duplicated().sum()
    print(f"Duplicate Session IDs: {duplicate_sessions}")

    numeric_columns = df.select_dtypes(include="number").columns

    print("\nNegative Value Check:")
    for column in numeric_columns:
        negative_count = (df[column] < 0).sum()
        print(f"{column}: {negative_count}")

    invalid_scores = (
        (df["productivity_score"] < 0) |
        (df["productivity_score"] > 100)
    ).sum()

    print(f"\nInvalid Productivity Scores: {invalid_scores}")
    print("\n===== VALIDATION COMPLETED =====")


def inspect_dataset():
    if not DATASET_PATH.exists():
        print(f"Dataset not found: {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH)

    print("\n===== COGNISTREAM: DATA QUALITY INSPECTION =====")
    print(f"\nDataset: {DATASET_PATH.name}")
    print(f"Total Rows: {df.shape[0]}")
    print(f"Total Columns: {df.shape[1]}")

    print("\n===== MISSING VALUE ANALYSIS =====")
    missing = df.isnull().sum()
    missing_percent = (missing / len(df)) * 100

    missing_report = pd.DataFrame({
        "Missing Values": missing,
        "Missing Percentage": missing_percent
    })
    print(missing_report.to_string())

    print("\n===== DUPLICATE ANALYSIS =====")
    duplicates = df.duplicated().sum()
    duplicate_percent = (duplicates / len(df)) * 100

    print(f"Duplicate Rows: {duplicates}")
    print(f"Duplicate Percentage: {duplicate_percent:.2f}%")

    print("\n===== UNIQUE VALUES =====")
    for column in df.columns:
        print(f"{column}: {df[column].nunique()} unique values")

    print("\n===== NUMERIC SUMMARY =====")
    print(df.describe().round(2).to_string())

    print("\n===== DATA QUALITY STATUS =====")
    if missing.sum() == 0 and duplicates == 0:
        print("Status: GOOD - No missing values or duplicate rows found.")
    else:
        print("Status: REVIEW REQUIRED - Data quality issues detected.")

    validate_dataset(df)

    print("\n===== INSPECTION COMPLETED =====")


if __name__ == "__main__":
    inspect_dataset()