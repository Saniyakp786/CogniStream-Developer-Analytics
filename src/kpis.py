"""
CogniStream - Phase 2: KPI functions (Member 2 owns this file).

Every function takes a DataFrame and returns numbers / a DataFrame.
The dashboard (Phase 3) and the AI assistant (Phase 4) will import these,
so numbers are calculated in ONE place only.
Only columns that really exist in the dataset are used.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH = ROOT / "data" / "cleaned_developer_productivity.csv"

LOAD_ORDER = ["Low", "Medium", "High"]
NUMERIC_FOR_CORR = [
    "productivity_score", "coding_duration_minutes", "focus_duration_minutes",
    "flow_state_duration_minutes", "interruption_count", "context_switch_count",
    "break_duration_minutes", "meeting_minutes", "tasks_completed", "bug_count",
]


def load_clean(path=CLEAN_PATH):
    """Load the cleaned dataset. Raises a clear error if Phase 1 was not run."""
    if not Path(path).exists():
        raise FileNotFoundError(
            "cleaned_developer_productivity.csv not found. Run: python src/cleaning.py"
        )
    df = pd.read_csv(path, parse_dates=["session_date"])
    if df.empty:
        raise ValueError("Cleaned dataset is empty.")
    return df


def apply_filters(df, experience=None, work_mode=None, task_type=None,
                  complexity=None, date_range=None):
    """Each filter is an optional list (or (start, end) for date_range)."""
    out = df
    if experience:
        out = out[out["experience_level"].isin(experience)]
    if work_mode:
        out = out[out["work_mode"].isin(work_mode)]
    if task_type:
        out = out[out["task_type"].isin(task_type)]
    if complexity:
        out = out[out["task_complexity"].isin(complexity)]
    if date_range:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        out = out[(out["session_date"] >= start) & (out["session_date"] <= end)]
    return out


def overview_kpis(df):
    """Headline numbers. Returns a dict (empty-safe)."""
    if df.empty:
        return {}
    return {
        "sessions": int(len(df)),
        "developers": int(df["developer_id"].nunique()),
        "avg_productivity_score": round(df["productivity_score"].mean(), 1),
        "avg_coding_minutes": round(df["coding_duration_minutes"].mean(), 1),
        "avg_focus_minutes": round(df["focus_duration_minutes"].mean(), 1),
        "avg_flow_minutes": round(df["flow_state_duration_minutes"].mean(), 1),
        "avg_interruptions": round(df["interruption_count"].mean(), 2),
        "avg_context_switches": round(df["context_switch_count"].mean(), 2),
        "pct_high_cognitive_load": round((df["cognitive_load_level"] == "High").mean() * 100, 1),
        "pct_sessions_with_flow": round((df["flow_state_duration_minutes"] > 0).mean() * 100, 1),
        "flow_share_of_focus_pct": round(
            df["flow_state_duration_minutes"].sum() / df["focus_duration_minutes"].sum() * 100, 1),
    }


def load_distribution(df):
    counts = df["cognitive_load_level"].value_counts().reindex(LOAD_ORDER).fillna(0).astype(int)
    out = counts.to_frame("sessions")
    out["percent"] = (out["sessions"] / out["sessions"].sum() * 100).round(1)
    return out


def summary_by(df, column):
    """Average metrics for each value of a category column."""
    g = df.groupby(column).agg(
        sessions=("session_id", "count"),
        avg_productivity=("productivity_score", "mean"),
        avg_focus=("focus_duration_minutes", "mean"),
        avg_flow=("flow_state_duration_minutes", "mean"),
        avg_interruptions=("interruption_count", "mean"),
        avg_context_switches=("context_switch_count", "mean"),
    ).round(2)
    if column == "cognitive_load_level":
        g = g.reindex(LOAD_ORDER)
    return g


def interruption_bands(df):
    """Group sessions by number of interruptions and compare outcomes."""
    bands = pd.cut(df["interruption_count"], bins=[-1, 1, 3, 5, 100],
                   labels=["0-1", "2-3", "4-5", "6+"])
    return df.groupby(bands, observed=True).agg(
        sessions=("session_id", "count"),
        avg_productivity=("productivity_score", "mean"),
        avg_flow=("flow_state_duration_minutes", "mean"),
    ).round(2)


def correlation_matrix(df, method="spearman"):
    """Association between numeric columns. Correlation is NOT causation."""
    return df[NUMERIC_FOR_CORR].corr(method=method).round(2)


def monthly_trend(df):
    m = df.groupby(df["session_date"].dt.to_period("M")).agg(
        sessions=("session_id", "count"),
        avg_productivity=("productivity_score", "mean"),
        avg_flow=("flow_state_duration_minutes", "mean"),
        avg_interruptions=("interruption_count", "mean"),
    ).round(2)
    m.index = m.index.astype(str)
    return m
