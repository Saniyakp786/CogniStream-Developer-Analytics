"""
CogniStream - data preparation for the dashboard charts.

Pure pandas / numpy: NO plotly or streamlit imports, so everything here can be
unit-tested (see tests/test_chart_data.py). Averages and KPIs still come from
src/kpis.py (single source of truth); this module only reshapes data for charts.
"""
import numpy as np
import pandas as pd

import kpis

LOAD_ORDER = kpis.LOAD_ORDER
BAND_ORDER = ["0-1", "2-3", "4-5", "6+"]
EXPERIENCE_ORDER = ["Junior", "Mid", "Senior", "Lead"]
COMPLEXITY_ORDER = ["Low", "Medium", "High"]

# Groups smaller than this are drawn hollow / hatched and called out as unreliable.
SMALL_N = 30

PRETTY = {
    "productivity_score": "Productivity",
    "coding_duration_minutes": "Coding min",
    "focus_duration_minutes": "Focus min",
    "flow_state_duration_minutes": "Flow min",
    "interruption_count": "Interruptions",
    "context_switch_count": "Context switches",
    "break_duration_minutes": "Break min",
    "meeting_minutes": "Meeting min",
    "tasks_completed": "Tasks done",
    "bug_count": "Bugs",
}


def pretty(col):
    """Short human label for a column name."""
    return PRETTY.get(col, col.replace("_", " ").capitalize())


# ---------- grouping helpers ----------
def add_band(df):
    """Add an interruption_band column (same bins as kpis.interruption_bands)."""
    out = df.copy()
    out["interruption_band"] = pd.cut(
        out["interruption_count"], bins=[-1, 1, 3, 5, 1000], labels=BAND_ORDER
    )
    return out


def developer_ranking(df, min_sessions=5, top_n=10, ascending=False):
    """
    Rank developers by average productivity.
    Only developers with at least `min_sessions` sessions are eligible, so one lucky
    session cannot put someone at the top.
    Returns (ranked_frame, eligible_count, total_developers).
    """
    g = (
        df.groupby("developer_id")
        .agg(
            sessions=("session_id", "count"),
            avg_productivity=("productivity_score", "mean"),
            avg_flow=("flow_state_duration_minutes", "mean"),
            avg_interruptions=("interruption_count", "mean"),
        )
        .reset_index()
    )
    total = int(len(g))
    eligible = g[g["sessions"] >= min_sessions]
    ranked = eligible.sort_values("avg_productivity", ascending=ascending).head(top_n)
    return ranked.round(2).reset_index(drop=True), int(len(eligible)), total


def group_summary(df, column, order=None):
    """Per-category averages with session counts and a small-sample flag."""
    g = df.groupby(column, observed=True).agg(
        sessions=("session_id", "count"),
        avg_productivity=("productivity_score", "mean"),
        avg_focus=("focus_duration_minutes", "mean"),
        avg_flow=("flow_state_duration_minutes", "mean"),
        avg_interruptions=("interruption_count", "mean"),
    )
    if order is not None:
        g = g.reindex([o for o in order if o in g.index])
    g = g[g["sessions"] > 0].round(2).reset_index()
    g["small"] = g["sessions"] < SMALL_N
    g["label"] = g[column].astype(str) + "  (n=" + g["sessions"].astype(str) + ")"
    return g


def band_summary(df):
    """Interruption-band averages in a fixed order, empty bands dropped."""
    d = add_band(df)
    g = d.groupby("interruption_band", observed=True).agg(
        sessions=("session_id", "count"),
        avg_productivity=("productivity_score", "mean"),
        avg_flow=("flow_state_duration_minutes", "mean"),
    )
    g = g.reindex([b for b in BAND_ORDER if b in g.index])
    g = g[g["sessions"] > 0].round(2).reset_index()
    g["small"] = g["sessions"] < SMALL_N
    return g


def binned_trend(df, x, y, bins=10, min_rows=50):
    """
    Mean of y inside equal-count bins of x (a simple, assumption-free trend line).
    Returns None when there is too little data to draw a trustworthy line.
    """
    if len(df) < min_rows or df[x].nunique() < bins:
        return None
    q = pd.qcut(df[x], bins, duplicates="drop")
    g = df.groupby(q, observed=True).agg(bx=(x, "mean"), by=(y, "mean"), n=(x, "size"))
    g = g.reset_index(drop=True)
    return g if len(g) >= 3 else None


def correlation_lower(df):
    """
    Spearman correlation matrix (from kpis) with pretty labels and the upper
    triangle blanked, so each pair appears once. Returns None if < 3 rows.
    """
    if len(df) < 3:
        return None
    c = kpis.correlation_matrix(df)
    labels = [pretty(col) for col in c.columns]
    z = c.to_numpy(dtype=float).copy()
    z[np.triu_indices_from(z, k=1)] = np.nan
    return pd.DataFrame(z, index=labels, columns=labels)


def complexity_load_matrix(df):
    """Task complexity x cognitive load: (row-percent matrix, count matrix)."""
    counts = (
        pd.crosstab(df["task_complexity"], df["cognitive_load_level"])
        .reindex(index=COMPLEXITY_ORDER, columns=LOAD_ORDER)
        .fillna(0)
        .astype(int)
    )
    row_sum = counts.sum(axis=1).replace(0, np.nan)
    pct = counts.div(row_sum, axis=0) * 100  # rows with no sessions stay NaN
    return pct.round(1), counts


def load_summary(df):
    """Averages per cognitive-load level (Low/Medium/High), missing levels dropped."""
    g = kpis.summary_by(df, "cognitive_load_level")
    g = g[g["sessions"].fillna(0) > 0].reset_index()
    g["small"] = g["sessions"] < SMALL_N
    return g


def distribution_mode(df, column, min_n=SMALL_N):
    """
    Decide how to draw a per-load-level distribution.
      'violin' - every present group has >= min_n values (shape is meaningful)
      'box'    - at least one group is small (box + every point is more honest)
      'none'   - nothing to draw
    Returns (mode, sizes_by_level).
    """
    sizes = (
        df.groupby("cognitive_load_level")[column].count().reindex(LOAD_ORDER).fillna(0).astype(int)
    )
    present = sizes[sizes > 0]
    if present.empty:
        return "none", sizes
    return ("violin" if (present >= min_n).all() else "box"), sizes


def compare_to_baseline(current, baseline, higher_is_better=True, decimals=1, tol=0.01):
    """
    Context line for a KPI card: (text, tone). tone is 'good' / 'bad' / 'neutral'.
    Differences under `tol` (relative) count as 'in line with all sessions'.
    """
    if baseline in (None, 0) or current is None or pd.isna(current) or pd.isna(baseline):
        return None, "neutral"
    diff = float(current) - float(baseline)
    if abs(diff) / abs(float(baseline)) < tol:
        return "In line with all sessions", "neutral"
    arrow = "\u25B2" if diff > 0 else "\u25BC"
    if higher_is_better is None:
        tone = "neutral"
    else:
        tone = "good" if (diff > 0) == higher_is_better else "bad"
    return f"{arrow} {abs(diff):.{decimals}f} vs all sessions", tone
