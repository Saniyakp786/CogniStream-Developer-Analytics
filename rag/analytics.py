"""
CogniStream - Phase 4: numbers for the assistant.

Numeric questions are answered with Pandas (through src/kpis.py), NOT by the language model.
get_facts(question, df) returns a list of {"label", "source", "text"} dictionaries.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import kpis  # noqa: E402

TRIGGERS = ["average", "avg", "mean", "how many", "percent", "%", "count", "total", "compare",
            "summar", "pattern", "correl", "trend", "highest", "lowest", "distribution",
            "factor", "associated", "relationship", "overview", "kpi", "how much"]


def wants_numbers(question):
    q = question.lower()
    return any(t in q for t in TRIGGERS)


def _has(q, words):
    return any(re.search(w, q) for w in words)


def _load_associations(df):
    """Spearman association between the ordered load label and numeric columns."""
    code = df["cognitive_load_level"].map({"Low": 0, "Medium": 1, "High": 2})
    cols = ["interruption_count", "context_switch_count", "focus_duration_minutes",
            "flow_state_duration_minutes", "meeting_minutes", "bug_count", "productivity_score"]
    out = {c: round(df[c].corr(code, method="spearman"), 2) for c in cols}
    return pd.Series(out, name="spearman_with_load_(Low=0,Medium=1,High=2)").to_frame()


def get_facts(question, df):
    q = question.lower()
    facts = []

    def add(label, source, obj):
        text = obj.to_markdown() if hasattr(obj, "to_markdown") else str(obj)
        facts.append({"label": label, "source": source, "text": text})

    if df.empty:
        return facts

    broad = _has(q, [r"summar", r"pattern", r"overview", r"kpi"])
    topic_hits = 0

    if broad or _has(q, [r"cognitive", r"load", r"factor", r"associated"]):
        add("Cognitive load distribution", "kpis.load_distribution", kpis.load_distribution(df))
        add("Averages by cognitive load level", "kpis.summary_by('cognitive_load_level')",
            kpis.summary_by(df, "cognitive_load_level"))
        topic_hits += 1
        if _has(q, [r"factor", r"associated", r"related"]) and len(df) > 5:
            add("Association of numeric columns with load level",
                "Spearman correlation (rag/analytics.py)", _load_associations(df))
    if broad or _has(q, [r"interrupt"]):
        add("Productivity and flow by interruption band", "kpis.interruption_bands", kpis.interruption_bands(df))
        topic_hits += 1
    if broad or _has(q, [r"correl", r"relationship", r"associat", r"factor"]):
        if len(df) > 5:
            corr = kpis.correlation_matrix(df)["productivity_score"].drop("productivity_score").sort_values()
            add("Spearman correlation with productivity_score", "kpis.correlation_matrix", corr.to_frame("rho"))
            topic_hits += 1
    for words, col, label in [
        ([r"experience", r"senior", r"junior", r"\blead\b", r"\bmid\b"], "experience_level", "experience level"),
        ([r"remote", r"office", r"hybrid", r"work mode"], "work_mode", "work mode"),
        ([r"task type", r"bug fix", r"refactor", r"code review", r"testing", r"documentation"], "task_type", "task type"),
        ([r"complexity"], "task_complexity", "task complexity"),
    ]:
        if _has(q, words):
            add(f"Averages by {label}", f"kpis.summary_by('{col}')", kpis.summary_by(df, col))
            topic_hits += 1
    if _has(q, [r"trend", r"month", r"over time"]):
        add("Monthly trend", "kpis.monthly_trend", kpis.monthly_trend(df))
        topic_hits += 1
    if _has(q, [r"flow"]) and not broad:
        flow = {
            "avg_flow_minutes": round(df["flow_state_duration_minutes"].mean(), 1),
            "sessions_with_zero_flow": int((df["flow_state_duration_minutes"] == 0).sum()),
            "flow_share_of_focus_pct": kpis.overview_kpis(df)["flow_share_of_focus_pct"],
        }
        add("Flow-state statistics", "kpis.overview_kpis (flow)", pd.Series(flow, name="value").to_frame())
        topic_hits += 1

    # Headline numbers go first for broad questions or when no specific topic matched
    if broad or topic_hits == 0:
        facts.insert(0, {"label": "Headline KPIs", "source": "kpis.overview_kpis",
                         "text": pd.Series(kpis.overview_kpis(df), name="value").to_frame().to_markdown()})
    return facts
