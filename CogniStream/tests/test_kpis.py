"""
Tests for src/kpis.py (the single place where dashboard numbers are calculated).

Run from the project root:
    python tests/test_kpis.py          (or: pytest tests)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import kpis  # noqa: E402

DF = kpis.load_clean()


def make_small_df():
    """Four hand-made sessions so every expected number can be checked by eye."""
    return pd.DataFrame({
        "developer_id": ["D1", "D1", "D2", "D3"],
        "session_id": ["S1", "S2", "S3", "S4"],
        "session_date": pd.to_datetime(
            ["2025-01-06", "2025-01-07", "2025-02-03", "2025-02-04"]),
        "experience_level": ["Junior", "Junior", "Senior", "Mid"],
        "work_mode": ["Remote", "Office", "Remote", "Hybrid"],
        "task_type": ["Bug Fixing", "Feature Development", "Bug Fixing", "Testing"],
        "task_complexity": ["Low", "High", "Medium", "High"],
        "productivity_score": [50.0, 70.0, 80.0, 60.0],
        "coding_duration_minutes": [100.0, 120.0, 140.0, 160.0],
        "focus_duration_minutes": [80.0, 100.0, 100.0, 120.0],
        "flow_state_duration_minutes": [0.0, 20.0, 40.0, 20.0],
        "interruption_count": [0, 2, 4, 8],
        "context_switch_count": [1, 3, 5, 7],
        "cognitive_load_level": ["Low", "Medium", "High", "High"],
    })


# ---------- load_clean ----------

def test_load_clean_returns_non_empty_frame_with_dates():
    assert not DF.empty
    assert pd.api.types.is_datetime64_any_dtype(DF["session_date"])
    for col in ("developer_id", "productivity_score", "cognitive_load_level"):
        assert col in DF.columns


def test_load_clean_raises_clear_error_for_missing_file():
    try:
        kpis.load_clean(ROOT / "data" / "does_not_exist.csv")
    except FileNotFoundError as exc:
        assert "cleaning.py" in str(exc)   # the message tells the user how to fix it
    else:
        raise AssertionError("expected FileNotFoundError")


# ---------- apply_filters ----------

def test_apply_filters_with_no_arguments_keeps_every_row():
    assert len(kpis.apply_filters(DF)) == len(DF)


def test_apply_filters_single_and_combined_filters():
    df = make_small_df()
    assert len(kpis.apply_filters(df, experience=["Junior"])) == 2
    assert len(kpis.apply_filters(df, work_mode=["Remote"])) == 2
    both = kpis.apply_filters(df, experience=["Junior"], work_mode=["Remote"])
    assert list(both["session_id"]) == ["S1"]
    assert len(kpis.apply_filters(df, complexity=["High"])) == 2
    assert len(kpis.apply_filters(df, task_type=["Testing"])) == 1


def test_apply_filters_date_range_is_inclusive():
    df = make_small_df()
    out = kpis.apply_filters(df, date_range=("2025-01-06", "2025-01-07"))
    assert list(out["session_id"]) == ["S1", "S2"]


def test_apply_filters_can_return_empty_without_crashing():
    out = kpis.apply_filters(make_small_df(), experience=["Lead"])
    assert out.empty


# ---------- overview_kpis ----------

def test_overview_kpis_matches_hand_calculation():
    k = kpis.overview_kpis(make_small_df())
    assert k["sessions"] == 4
    assert k["developers"] == 3
    assert k["avg_productivity_score"] == 65.0
    assert k["avg_coding_minutes"] == 130.0
    assert k["avg_focus_minutes"] == 100.0
    assert k["avg_flow_minutes"] == 20.0
    assert k["avg_interruptions"] == 3.5
    assert k["avg_context_switches"] == 4.0
    assert k["pct_high_cognitive_load"] == 50.0
    assert k["pct_sessions_with_flow"] == 75.0       # 3 of 4 sessions have flow > 0
    assert k["flow_share_of_focus_pct"] == 20.0      # 80 flow minutes / 400 focus minutes


def test_overview_kpis_is_empty_safe():
    assert kpis.overview_kpis(DF.iloc[0:0]) == {}


def test_overview_kpis_real_data_stays_in_valid_ranges():
    k = kpis.overview_kpis(DF)
    assert k["sessions"] == len(DF)
    assert 0 <= k["avg_productivity_score"] <= 100
    assert 0 <= k["pct_high_cognitive_load"] <= 100
    assert 0 <= k["pct_sessions_with_flow"] <= 100
    assert 0 <= k["flow_share_of_focus_pct"] <= 100


# ---------- load_distribution ----------

def test_load_distribution_has_fixed_order_and_sums_to_100():
    out = kpis.load_distribution(DF)
    assert list(out.index) == kpis.LOAD_ORDER
    assert out["sessions"].sum() == len(DF)
    assert abs(out["percent"].sum() - 100) < 0.5     # rounding can leave a tiny gap


def test_load_distribution_fills_missing_levels_with_zero():
    df = make_small_df()
    df = df[df["cognitive_load_level"] != "Low"]
    out = kpis.load_distribution(df)
    assert out.loc["Low", "sessions"] == 0
    assert out.loc["High", "sessions"] == 2


# ---------- summary_by ----------

def test_summary_by_groups_and_averages_correctly():
    out = kpis.summary_by(make_small_df(), "work_mode")
    assert out.loc["Remote", "sessions"] == 2
    assert out.loc["Remote", "avg_productivity"] == 65.0   # (50 + 80) / 2
    assert out["sessions"].sum() == 4


def test_summary_by_cognitive_load_uses_low_medium_high_order():
    out = kpis.summary_by(DF, "cognitive_load_level")
    assert list(out.index) == kpis.LOAD_ORDER


# ---------- interruption_bands ----------

def test_interruption_bands_put_sessions_in_the_right_band():
    out = kpis.interruption_bands(make_small_df())
    # interruptions are 0, 2, 4, 8  ->  bands 0-1, 2-3, 4-5, 6+
    assert list(out.index) == ["0-1", "2-3", "4-5", "6+"]
    assert list(out["sessions"]) == [1, 1, 1, 1]


def test_interruption_bands_cover_every_session_in_real_data():
    out = kpis.interruption_bands(DF)
    assert out["sessions"].sum() == len(DF)


# ---------- correlation_matrix ----------

def test_correlation_matrix_is_square_symmetric_with_unit_diagonal():
    corr = kpis.correlation_matrix(DF)
    assert list(corr.index) == kpis.NUMERIC_FOR_CORR
    assert list(corr.columns) == kpis.NUMERIC_FOR_CORR
    assert (corr.values.diagonal() == 1.0).all()
    assert corr.equals(corr.T)
    assert corr.abs().max().max() <= 1.0


def test_correlation_matrix_accepts_pearson_method():
    corr = kpis.correlation_matrix(DF, method="pearson")
    assert corr.shape == (len(kpis.NUMERIC_FOR_CORR), len(kpis.NUMERIC_FOR_CORR))


# ---------- monthly_trend ----------

def test_monthly_trend_has_one_row_per_month():
    out = kpis.monthly_trend(make_small_df())
    assert list(out.index) == ["2025-01", "2025-02"]
    assert list(out["sessions"]) == [2, 2]
    assert out.loc["2025-01", "avg_productivity"] == 60.0   # (50 + 70) / 2


def test_monthly_trend_real_data_is_sorted_and_complete():
    out = kpis.monthly_trend(DF)
    assert list(out.index) == sorted(out.index)
    assert out["sessions"].sum() == len(DF)


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