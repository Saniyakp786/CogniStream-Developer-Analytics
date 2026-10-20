"""
CogniStream - Phase 1: Data inspection, validation and cleaning.

Run from the project root:
    python src/cleaning.py

Input : data/developer_productivity_dataset.csv
Output: data/cleaned_developer_productivity.csv
        reports/data_quality_report.md

Rules followed:
  * NO rows are deleted and NO values are changed without a stated rule.
  * Suspicious rows are only FLAGGED (flag_* columns), never removed.
  * Original columns are kept as they are; new columns are only added.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "developer_productivity_dataset.csv"
CLEAN_PATH = ROOT / "data" / "cleaned_developer_productivity.csv"
REPORT_PATH = ROOT / "reports" / "data_quality_report.md"

EXPECTED_COLUMNS = [
    "developer_id", "session_id", "session_date", "start_time", "end_time",
    "experience_level", "task_type", "task_complexity",
    "coding_duration_minutes", "focus_duration_minutes", "interruption_count",
    "context_switch_count", "break_duration_minutes", "cognitive_load_level",
    "flow_state_duration_minutes", "tasks_completed", "bug_count",
    "meeting_minutes", "work_mode", "productivity_score",
]
CATEGORICAL = ["experience_level", "task_type", "task_complexity",
               "cognitive_load_level", "work_mode"]
NUMERIC = ["coding_duration_minutes", "focus_duration_minutes",
           "interruption_count", "context_switch_count",
           "break_duration_minutes", "flow_state_duration_minutes",
           "tasks_completed", "bug_count", "meeting_minutes",
           "productivity_score"]

findings = []  # each item: (check name, result, status)


def record(name, result, status):
    """status: PASS / FLAG / INFO"""
    findings.append((name, result, status))
    print(f"[{status}] {name}: {result}")


def load_data(path=RAW_PATH):
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Put developer_productivity_dataset.csv "
            "inside the data/ folder."
        )
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Dataset is empty.")
    return df


def check_structure(df):
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra_cols = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")
    record("Shape", f"{df.shape[0]} rows x {df.shape[1]} columns", "INFO")
    record("Unexpected extra columns", str(extra_cols) if extra_cols else "none",
           "PASS" if not extra_cols else "INFO")
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    record("Missing values", "none in any column" if nulls.empty else nulls.to_dict(),
           "PASS" if nulls.empty else "FLAG")
    dup_rows = int(df.duplicated().sum())
    dup_ids = int(df["session_id"].duplicated().sum())
    record("Duplicate rows", str(dup_rows), "PASS" if dup_rows == 0 else "FLAG")
    record("Duplicate session_id", str(dup_ids), "PASS" if dup_ids == 0 else "FLAG")
    record("Unique developers", str(df["developer_id"].nunique()), "INFO")


def clean_text_and_dates(df):
    df = df.copy()
    # Rule 1: strip spaces from text columns (does not change meaning)
    changed = 0
    for col in ["developer_id", "session_id"] + CATEGORICAL:
        original = df[col].astype(str)
        stripped = original.str.strip()
        changed += int((stripped != original).sum())
        df[col] = stripped
    record("Whitespace cleanup", f"{changed} values changed", "PASS" if changed == 0 else "INFO")

    for col in CATEGORICAL:
        record(f"Categories: {col}", df[col].value_counts().to_dict(), "INFO")

    # Rule 2: parse dates and times; invalid values become NaT and are reported
    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
    bad_dates = int(df["session_date"].isna().sum())
    record("Date parsing",
           f"{bad_dates} invalid dates; range {df['session_date'].min().date()} "
           f"to {df['session_date'].max().date()}",
           "PASS" if bad_dates == 0 else "FLAG")
    weekend = int((df["session_date"].dt.dayofweek >= 5).sum())
    record("Weekend sessions", str(weekend), "INFO")

    start = pd.to_datetime(df["start_time"], format="%H:%M:%S", errors="coerce")
    end = pd.to_datetime(df["end_time"], format="%H:%M:%S", errors="coerce")
    bad_times = int(start.isna().sum() + end.isna().sum())
    record("Time parsing", f"{bad_times} invalid time values", "PASS" if bad_times == 0 else "FLAG")
    df["session_duration_minutes"] = (end - start).dt.total_seconds() / 60
    bad_order = int((df["session_duration_minutes"] <= 0).sum())
    record("end_time after start_time", f"{bad_order} rows violate this",
           "PASS" if bad_order == 0 else "FLAG")
    return df


def check_numeric_and_logic(df):
    neg = {c: int((df[c] < 0).sum()) for c in NUMERIC if (df[c] < 0).any()}
    record("Negative values", "none" if not neg else neg, "PASS" if not neg else "FLAG")
    out_of_range = int(((df["productivity_score"] < 0) | (df["productivity_score"] > 100)).sum())
    record("productivity_score within 0-100", f"{out_of_range} rows outside",
           "PASS" if out_of_range == 0 else "FLAG")

    checks = {
        "focus <= coding": df["focus_duration_minutes"] > df["coding_duration_minutes"],
        "flow <= focus": df["flow_state_duration_minutes"] > df["focus_duration_minutes"],
        "coding <= session length": df["coding_duration_minutes"] > df["session_duration_minutes"],
    }
    for name, violated in checks.items():
        record(f"Logic: {name}", f"{int(violated.sum())} violations",
               "PASS" if violated.sum() == 0 else "FLAG")
    gap = (df["session_duration_minutes"] - df["coding_duration_minutes"]
           - df["break_duration_minutes"] - df["meeting_minutes"]).abs()
    n_gap = int((gap > 0.01).sum())
    record("Logic: coding + break + meeting = session length",
           f"{n_gap} rows differ", "PASS" if n_gap == 0 else "FLAG")

    # Outliers (IQR rule) - REPORTED ONLY, never removed
    out = {}
    for c in NUMERIC:
        q1, q3 = df[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        n = int(((df[c] < q1 - 1.5 * iqr) | (df[c] > q3 + 1.5 * iqr)).sum())
        if n:
            out[c] = n
    record("IQR outliers (kept, not removed)", out if out else "none", "INFO")


def add_flags_and_features(df):
    df = df.copy()
    df["focus_ratio"] = (df["focus_duration_minutes"] / df["coding_duration_minutes"]).round(4)
    df["flow_ratio"] = (df["flow_state_duration_minutes"] / df["focus_duration_minutes"]).round(4)

    # FLAG 1: same developer, same day, a session starts before the previous one ends
    start = pd.to_datetime(df["start_time"], format="%H:%M:%S")
    end = pd.to_datetime(df["end_time"], format="%H:%M:%S")
    tmp = pd.DataFrame({"dev": df["developer_id"], "date": df["session_date"],
                        "start": start, "end": end}, index=df.index)
    tmp = tmp.sort_values(["dev", "date", "start"])
    grp = tmp.groupby(["dev", "date"])
    overlaps_next = grp["start"].shift(-1) < tmp["end"]
    overlaps_prev = overlaps_next.groupby([tmp["dev"], tmp["date"]]).shift(1, fill_value=False)
    flagged = (overlaps_next | overlaps_prev.astype(bool)).reindex(df.index)
    df["flag_overlapping_session"] = flagged.astype(bool)

    # FLAG 2 / 3: unusual but possibly valid
    df["flag_low_focus_ratio"] = df["focus_ratio"] < 0.2
    df["flag_zero_flow"] = df["flow_state_duration_minutes"] == 0

    record("Flag: overlapping sessions (same developer, same day)",
           f"{int(overlaps_next.sum())} overlapping pairs; "
           f"{int(df['flag_overlapping_session'].sum())} rows flagged (kept)", "FLAG")
    record("Flag: focus/coding ratio < 0.2",
           f"{int(df['flag_low_focus_ratio'].sum())} rows (kept)", "FLAG")
    record("Flag: flow-state = 0 minutes",
           f"{int(df['flag_zero_flow'].sum())} rows (kept; plausible with many interruptions)", "INFO")
    record("Class balance: cognitive_load_level",
           f"{df['cognitive_load_level'].value_counts().to_dict()} - Low is small, interpret with care",
           "FLAG")
    return df


def check_definitions(df):
    num = df[NUMERIC]
    X = num.drop(columns="productivity_score")
    X = (X - X.mean()) / X.std()
    A = np.c_[np.ones(len(X)), X.values]
    y = num["productivity_score"].values
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    r2 = 1 - ((y - A @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    record("productivity_score definition",
           f"Formula/source NOT provided. A linear fit on other numeric columns gives R2={r2:.2f}, "
           "so it is related to them but the exact formula is unknown. Do not invent one.", "FLAG")
    record("cognitive_load_level definition",
           "Rule/source NOT provided. Levels overlap in interruptions and context switches, "
           "so it is not a simple threshold. Treat it as a given label.", "FLAG")
    record("Data origin",
           "Source of dataset (real or synthetic) is not stated. Confirm with mentor before "
           "calling results real-world evidence.", "FLAG")


def write_report(raw_rows, clean_rows):
    lines = [
        "# CogniStream - Data Quality Report", "",
        f"Raw rows: {raw_rows} | Cleaned rows: {clean_rows} | Rows deleted: {raw_rows - clean_rows}", "",
        "Cleaning rules: (1) strip whitespace in text columns, (2) parse dates/times, "
        "(3) add derived columns (session_duration_minutes, focus_ratio, flow_ratio), "
        "(4) add flag_* columns. No row was deleted and no value was overwritten.", "",
        "| Status | Check | Result |", "|---|---|---|",
    ]
    for name, result, status in findings:
        lines.append(f"| {status} | {name} | {str(result).replace('|', '/')} |")
    lines += ["", "**Legend:** PASS = no problem found; FLAG = needs review or caution; "
              "INFO = descriptive only.",
              "Flagged rows are unusual but NOT confirmed errors."]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    raw = load_data()
    check_structure(raw)
    df = clean_text_and_dates(raw)
    check_numeric_and_logic(df)
    df = add_flags_and_features(df)
    check_definitions(df)
    df["session_date"] = df["session_date"].dt.strftime("%Y-%m-%d")
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)
    write_report(len(raw), len(df))
    print(f"\nSaved: {CLEAN_PATH}\nSaved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
