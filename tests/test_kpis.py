"""Tests for src/kpis.py (run:  python -m unittest discover -s tests -v)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import kpis  # noqa: E402


class KpiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = kpis.load_clean()

    def test_overview_matches_manual_numbers(self):
        k = kpis.overview_kpis(self.df)
        self.assertEqual(k["sessions"], len(self.df))
        self.assertAlmostEqual(k["avg_productivity_score"], round(self.df["productivity_score"].mean(), 1))
        self.assertAlmostEqual(
            k["pct_high_cognitive_load"],
            round((self.df["cognitive_load_level"] == "High").mean() * 100, 1))

    def test_empty_frame_is_safe(self):
        self.assertEqual(kpis.overview_kpis(self.df.iloc[0:0]), {})

    def test_filters_combine(self):
        out = kpis.apply_filters(self.df, experience=["Lead"], work_mode=["Office"])
        self.assertTrue((out["experience_level"] == "Lead").all())
        self.assertTrue((out["work_mode"] == "Office").all())
        self.assertLess(len(out), len(self.df))

    def test_date_filter(self):
        out = kpis.apply_filters(self.df, date_range=("2025-03-01", "2025-03-31"))
        self.assertGreater(len(out), 0)
        self.assertTrue(out["session_date"].between("2025-03-01", "2025-03-31").all())

    def test_interruption_band_matches_existing_bins(self):
        banded = kpis.add_interruption_band(self.df)
        counts = banded["interruption_band"].value_counts().reindex(kpis.BAND_LABELS)
        old = kpis.interruption_bands(self.df)["sessions"].reindex(kpis.BAND_LABELS)
        self.assertEqual(list(counts), list(old))

    def test_flow_by_band_sessions_add_up(self):
        fb = kpis.flow_by_band(self.df)
        self.assertEqual(int(fb["sessions"].sum()), len(self.df))
        self.assertTrue(((fb["pct_zero_flow"] >= 0) & (fb["pct_zero_flow"] <= 100)).all())

    def test_developer_ranking_min_sessions_rule(self):
        rank = kpis.developer_ranking(self.df, min_sessions=5, top_n=10)
        self.assertLessEqual(len(rank), 10)
        self.assertTrue((rank["sessions"] >= 5).all())
        self.assertTrue(rank["avg_productivity"].is_monotonic_decreasing)
        strict = kpis.developer_ranking(self.df, min_sessions=10_000)
        self.assertTrue(strict.empty)

    def test_load_by_complexity(self):
        counts, pct = kpis.load_by_complexity(self.df)
        self.assertEqual(int(counts.to_numpy().sum()), len(self.df))
        self.assertTrue(((pct.sum(axis=1) - 100).abs() < 0.3).all())
        self.assertEqual(list(counts.columns), kpis.LOAD_ORDER)

    def test_load_by_complexity_missing_group_is_zero_not_error(self):
        sub = self.df[self.df["task_complexity"] == "High"]
        counts, pct = kpis.load_by_complexity(sub)
        self.assertEqual(int(counts.loc["Low"].sum()), 0)
        self.assertEqual(float(pct.loc["Low"].sum()), 0.0)

    def test_spearman_safe_cases(self):
        self.assertIsNone(kpis.spearman(self.df.head(2), "flow_state_duration_minutes", "productivity_score"))
        const = self.df.head(10).copy()
        const["productivity_score"] = 50.0
        self.assertIsNone(kpis.spearman(const, "flow_state_duration_minutes", "productivity_score"))
        rho = kpis.spearman(self.df, "flow_state_duration_minutes", "productivity_score")
        self.assertGreaterEqual(rho, -1)
        self.assertLessEqual(rho, 1)

    def test_compare_to_baseline(self):
        sub = self.df.head(100)
        d = kpis.compare_to_baseline(kpis.overview_kpis(sub), kpis.overview_kpis(self.df))
        self.assertAlmostEqual(
            d["avg_productivity_score"],
            round(kpis.overview_kpis(sub)["avg_productivity_score"]
                  - kpis.overview_kpis(self.df)["avg_productivity_score"], 2))


if __name__ == "__main__":
    unittest.main()
