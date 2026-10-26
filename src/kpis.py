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


# ======================================================================
# Chart helpers added for the Power BI-style dashboard upgrade.
# They reuse the same columns and rules as the functions above, so the
# dashboard, the AI assistant and the Power BI DAX stay consistent.
# ======================================================================
SMALL_N = 30                 # groups below this many sessions are flagged as unreliable
MIN_SESSIONS_DEVELOPER = 5   # a developer needs at least this many sessions to be ranked
BAND_LABELS = ["0-1", "2-3", "4-5", "6+"]
BAND_BINS = [-1, 1, 3, 5, 100]   # same bins as interruption_bands()
EXPERIENCE_ORDER = ["Junior", "Mid", "Senior", "Lead"]
WORK_MODE_ORDER = ["Remote", "Hybrid", "Office"]
COMPLEXITY_ORDER = ["Low", "Medium", "High"]
CATEGORY_ORDERS = {
    "experience_level": EXPERIENCE_ORDER,
    "work_mode": WORK_MODE_ORDER,
    "task_complexity": COMPLEXITY_ORDER,
    "cognitive_load_level": LOAD_ORDER,
    "interruption_band": BAND_LABELS,
}


def add_interruption_band(df):
    """Copy of df with an 'interruption_band' column (same bins as interruption_bands)."""
    out = df.copy()
    out["interruption_band"] = pd.cut(out["interruption_count"], bins=BAND_BINS, labels=BAND_LABELS)
    return out


def developer_ranking(df, min_sessions=MIN_SESSIONS_DEVELOPER, top_n=10):
    """Developers ranked by average productivity; needs at least min_sessions sessions each."""
    g = df.groupby("developer_id").agg(
        sessions=("session_id", "count"),
        avg_productivity=("productivity_score", "mean"),
    ).reset_index()
    g = g[g["sessions"] >= min_sessions].sort_values(
        ["avg_productivity", "developer_id"], ascending=[False, True])
    return g.head(top_n).round(2).reset_index(drop=True)


def load_by_complexity(df):
    """Counts and row-% of cognitive_load_level for each task_complexity.

    Returns (counts, percent). Both are indexed by COMPLEXITY_ORDER and have the
    columns LOAD_ORDER; a complexity with no sessions has 0 counts and 0 percent.
    """
    counts = pd.crosstab(df["task_complexity"], df["cognitive_load_level"])
    counts = counts.reindex(index=COMPLEXITY_ORDER, columns=LOAD_ORDER).fillna(0).astype(int)
    totals = counts.sum(axis=1)
    percent = counts.div(totals.where(totals > 0), axis=0).fillna(0.0).mul(100).round(1)
    return counts, percent


def flow_by_band(df):
    """Per interruption band: sessions, average flow, share of sessions with zero flow, productivity."""
    bands = pd.cut(df["interruption_count"], bins=BAND_BINS, labels=BAND_LABELS)
    g = df.groupby(bands, observed=True).agg(
        sessions=("session_id", "count"),
        avg_flow=("flow_state_duration_minutes", "mean"),
        avg_productivity=("productivity_score", "mean"),
        pct_zero_flow=("flow_state_duration_minutes", lambda s: (s == 0).mean() * 100),
    ).round(2)
    return g.reindex(BAND_LABELS).dropna(how="all")


def share_by(df, column):
    """Sessions and percent of sessions for each value of a category column."""
    counts = df[column].value_counts()
    out = counts.to_frame("sessions")
    out["percent"] = (out["sessions"] / out["sessions"].sum() * 100).round(1)
    return out


def spearman(df, col_a, col_b):
    """Spearman association between two numeric columns, or None if it cannot be computed."""
    pair = df[[col_a, col_b]].dropna()
    if len(pair) < 3 or pair[col_a].nunique() < 2 or pair[col_b].nunique() < 2:
        return None
    return round(float(pair[col_a].corr(pair[col_b], method="spearman")), 2)


def productivity_reference(df):
    """Reference numbers of productivity_score used to draw the bullet gauge bands."""
    s = df["productivity_score"].dropna()
    if s.empty:
        return {}
    return {
        "min": float(s.min()), "q1": float(s.quantile(0.25)), "median": float(s.median()),
        "q3": float(s.quantile(0.75)), "max": float(s.max()), "mean": float(s.mean()),
    }


def compare_to_baseline(current, baseline):
    """Difference (current - baseline) for numeric overview_kpis values. Empty-safe."""
    out = {}
    for key, value in current.items():
        base = baseline.get(key)
        if isinstance(value, (int, float)) and isinstance(base, (int, float)):
            out[key] = round(value - base, 2)
    return out
