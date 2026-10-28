
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import kpis


def test_load_clean_returns_dataframe():
    df = kpis.load_clean()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_overview_kpis_contains_expected_metrics():
    df = kpis.load_clean()
    result = kpis.overview_kpis(df)

    expected = {
        "sessions",
        "developers",
        "avg_productivity_score",
        "avg_coding_minutes",
        "avg_focus_minutes",
        "avg_flow_minutes",
        "avg_interruptions",
        "avg_context_switches",
        "pct_high_cognitive_load",
        "pct_sessions_with_flow",
        "flow_share_of_focus_pct",
    }

    assert expected.issubset(result.keys())
    assert result["sessions"] == len(df)
    assert result["developers"] > 0


def test_apply_filters_returns_dataframe():
    df = kpis.load_clean()
    filtered = kpis.apply_filters(df)

    assert isinstance(filtered, pd.DataFrame)
    assert len(filtered) == len(df)
