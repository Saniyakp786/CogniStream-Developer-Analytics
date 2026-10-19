
import pandas as pd
from pathlib import Path

# Locate the project dataset
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "developer_productivity_dataset.csv"


def inspect_dataset():
    if not DATASET_PATH.exists():
        print(f"Dataset not found: {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH)

    print("\n===== COGNISTREAM: DATASET INSPECTION =====")
    print(f"\nDataset file: {DATASET_PATH.name}")
    print(f"Total rows: {df.shape[0]}")
    print(f"Total columns: {df.shape[1]}")

    print("\n===== COLUMN NAMES =====")
    for column in df.columns:
        print(f"- {column}")

    print("\n===== DATA TYPES =====")
    print(df.dtypes.to_string())

    print("\n===== MISSING VALUES =====")
    print(df.isnull().sum().to_string())

    print("\n===== DUPLICATE ROWS =====")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\n===== DATASET PREVIEW =====")
    print(df.head().to_string(index=False))

    print("\n===== INSPECTION COMPLETED =====")


if __name__ == "__main__":
    inspect_dataset()
