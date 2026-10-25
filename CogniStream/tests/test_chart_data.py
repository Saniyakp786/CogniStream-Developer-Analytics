"""
Tests for dashboard/chart_data.py (pure pandas - no plotly / streamlit needed).

Run from the project root:
    python tests/test_chart_data.py          (or: pytest tests)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import kpis  # noqa: E402
from dashboard import chart_data as cd  # noqa: E402

DF = kpis.load_clean()


def test_developer_ranking_respects_minimum_sessions():
    ranked, eligible, total = cd.developer_ranking(DF, min_sessions=5, top_n=10)
    assert total == DF["developer_id"].nunique() == 50
    assert (ranked["sessions"] >= 5).all()
    assert len(ranked) == 10 and eligible == 50
    assert ranked["avg_productivity"].is_monotonic_decreasing
    # a high minimum removes people instead of showing unreliable averages
    _, eligible_hi, _ = cd.developer_ranking(DF, min_sessions=25)
    assert eligible_hi < eligible
    bottom, _, _ = cd.developer_ranking(DF, ascending=True)
    assert bottom["avg_productivity"].is_monotonic_increasing
    assert bottom["avg_productivity"].iloc[0] <= ranked["avg_productivity"].iloc[-1]


def test_developer_ranking_empty_when_nobody_eligible():
    ranked, eligible, _ = cd.developer_ranking(DF, min_sessions=10_000)
    assert ranked.empty and eligible == 0


def test_group_summary_counts_labels_and_small_flag():
    g = cd.group_summary(DF, "experience_level", cd.EXPERIENCE_ORDER)
    assert g["experience_level"].tolist() == ["Junior", "Mid", "Senior", "Lead"]
    assert g["sessions"].sum() == len(DF)
    lead = g[g["experience_level"] == "Lead"].iloc[0]
    assert lead["sessions"] == 67 and not lead["small"]
    assert lead["label"] == "Lead  (n=67)"
    # numbers agree with kpis.summary_by (single source of truth)
    ref = kpis.summary_by(DF, "experience_level")
    for _, row in g.iterrows():
        assert abs(row["avg_productivity"] - ref.loc[row["experience_level"], "avg_productivity"]) < 0.01


def test_group_summary_flags_small_groups():
    tiny = DF[DF["task_type"] == "Documentation"].head(10)
    g = cd.group_summary(tiny, "task_type")
    assert bool(g["small"].iloc[0]) is True


def test_band_summary_matches_kpis_and_order():
    b = cd.band_summary(DF)
    assert b["interruption_band"].astype(str).tolist() == cd.BAND_ORDER
    assert b["sessions"].sum() == len(DF)
    ref = kpis.interruption_bands(DF)
    for _, row in b.iterrows():
        assert abs(row["avg_productivity"] - ref.loc[row["interruption_band"], "avg_productivity"]) < 0.01


def test_band_summary_drops_empty_bands():
    sub = DF[DF["interruption_count"] <= 1]
    b = cd.band_summary(sub)
    assert b["interruption_band"].astype(str).tolist() == ["0-1"]


def test_binned_trend():
    t = cd.binned_trend(DF, "flow_state_duration_minutes", "productivity_score")
    assert t is not None and 3 <= len(t) <= 10 and t["n"].sum() == len(DF)
    assert cd.binned_trend(DF.head(20), "flow_state_duration_minutes", "productivity_score") is None
    const = DF.copy()
    const["flow_state_duration_minutes"] = 5.0
    assert cd.binned_trend(const, "flow_state_duration_minutes", "productivity_score") is None


def test_correlation_lower_is_triangular_with_unit_diagonal():
    c = cd.correlation_lower(DF)
    n = len(c)
    assert c.shape == (10, 10) and list(c.index) == list(c.columns)
    z = c.to_numpy()
    assert np.isnan(z[np.triu_indices(n, k=1)]).all()
    assert np.allclose(np.diag(z), 1.0)
    assert np.nanmax(np.abs(z)) <= 1.0
    assert cd.correlation_lower(DF.head(2)) is None


def test_complexity_load_matrix_rows_sum_to_100():
    pct, counts = cd.complexity_load_matrix(DF)
    assert counts.to_numpy().sum() == len(DF)
    assert np.allclose(pct.sum(axis=1), 100.0, atol=0.3)
    assert pct.index.tolist() == cd.COMPLEXITY_ORDER and pct.columns.tolist() == cd.LOAD_ORDER


def test_complexity_load_matrix_missing_level_stays_nan():
    pct, counts = cd.complexity_load_matrix(DF[DF["task_complexity"] == "High"])
    assert pct.loc["Low"].isna().all() and counts.loc["Low"].sum() == 0


def test_load_summary_and_levels():
    s = cd.load_summary(DF)
    assert s["cognitive_load_level"].tolist() == cd.LOAD_ORDER
    assert s["sessions"].tolist() == [54, 271, 675]
    only_high = cd.load_summary(DF[DF["cognitive_load_level"] == "High"])
    assert only_high["cognitive_load_level"].tolist() == ["High"]


def test_distribution_mode_uses_sample_size():
    mode, sizes = cd.distribution_mode(DF, "interruption_count")
    assert mode == "violin" and sizes["Low"] == 54            # every level has 30+
    small = DF[(DF["cognitive_load_level"] != "Low") | (DF.index % 5 == 0)]
    low_small = small[(small["cognitive_load_level"] != "Low")]
    low_small = pd.concat([low_small, DF[DF["cognitive_load_level"] == "Low"].head(12)])
    assert cd.distribution_mode(low_small, "interruption_count")[0] == "box"
    assert cd.distribution_mode(DF.iloc[0:0], "interruption_count")[0] == "none"


def test_compare_to_baseline():
    assert cd.compare_to_baseline(60, 50, True)[1] == "good"
    assert cd.compare_to_baseline(60, 50, False)[1] == "bad"
    assert cd.compare_to_baseline(3.0, 3.01, False)[1] == "neutral"
    text, tone = cd.compare_to_baseline(55.0, 50.0, True)
    assert text.startswith("\u25B2 5.0") and tone == "good"
    assert cd.compare_to_baseline(5, 0)[0] is None
    assert cd.compare_to_baseline(None, 5)[0] is None
    assert cd.compare_to_baseline(7, 5, None)[1] == "neutral"


def test_filtered_subsets_do_not_crash_prep_functions():
    subsets = [
        DF[DF["experience_level"] == "Lead"],
        DF[DF["session_date"] < "2025-02-01"],
        DF[(DF["work_mode"] == "Office") & (DF["task_complexity"] == "High")].head(25),
    ]
    for sub in subsets:
        cd.group_summary(sub, "task_type")
        cd.band_summary(sub)
        cd.load_summary(sub)
        cd.complexity_load_matrix(sub)
        cd.correlation_lower(sub)
        cd.developer_ranking(sub, min_sessions=3)


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
