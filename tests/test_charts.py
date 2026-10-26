"""Tests for dashboard/charts.py. Skipped automatically when plotly is not installed.

Run:  python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

try:
    import plotly  # noqa: F401
    HAVE_PLOTLY = True
except ImportError:  # pragma: no cover
    HAVE_PLOTLY = False

if HAVE_PLOTLY:
    import kpis
    from dashboard import charts
    from dashboard.palette import LOAD_COLORS, THEMES


@unittest.skipUnless(HAVE_PLOTLY, "plotly is not installed")
class ChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = kpis.load_clean()
        cls.t = THEMES["Light"]

    def slices(self):
        df = self.df
        yield "all", df
        yield "low load only", df[df["cognitive_load_level"] == "Low"]
        yield "one row", df.head(1)
        yield "twelve rows", df.head(12)
        yield "lead + office", df[(df["experience_level"] == "Lead") & (df["work_mode"] == "Office")]

    def test_scatter_uses_filtered_rows_and_load_colours(self):
        for name, d in self.slices():
            with self.subTest(name):
                fig = charts.load_scatter(d, "flow_state_duration_minutes", "productivity_score", self.t)
                self.assertEqual(sum(len(tr.x) for tr in fig.data), len(d))
                for tr in fig.data:
                    level = tr.legendgroup
                    self.assertEqual(tr.marker.color, LOAD_COLORS[level])

    def test_donut_order_and_colours(self):
        fig = charts.load_donut(kpis.load_distribution(self.df), self.t)
        pie = fig.data[0]
        self.assertEqual(list(pie.labels), kpis.LOAD_ORDER)
        self.assertEqual(list(pie.marker.colors), [LOAD_COLORS[k] for k in kpis.LOAD_ORDER])
        self.assertEqual(sum(pie.values), len(self.df))

    def test_every_builder_survives_every_slice(self):
        for name, d in self.slices():
            with self.subTest(name):
                ref = kpis.productivity_reference(self.df)
                charts.productivity_bullet(d["productivity_score"].mean(), ref, self.t)
                month = kpis.monthly_trend(d).reset_index().rename(columns={"session_date": "month"})
                charts.monthly_trend_chart(month, d["productivity_score"].mean(), self.t)
                charts.flow_histogram(d, self.t)
                counts, pct = kpis.load_by_complexity(d)
                charts.load_complexity_heatmap(counts, pct, self.t)
                charts.load_comparison(kpis.summary_by(d, "cognitive_load_level"), self.t)
                charts.band_comparison(kpis.flow_by_band(d), self.t)
                for metric in charts.SUMMARY_METRICS.values():
                    charts.small_multiples(
                        d, [("task_type", None), ("work_mode", kpis.WORK_MODE_ORDER),
                            ("experience_level", kpis.EXPERIENCE_ORDER)],
                        metric, "metric", self.t)
                if len(d) >= 10:
                    charts.correlation_heatmap(kpis.correlation_matrix(d), self.t)

    def test_box_plot_skips_small_groups(self):
        low = self.df[self.df["cognitive_load_level"] == "Low"].head(5)
        fig, excluded = charts.load_box(low, "interruption_count", "Interruptions", self.t)
        self.assertIsNone(fig)
        self.assertEqual([lvl for lvl, _ in excluded], kpis.LOAD_ORDER)
        fig, excluded = charts.load_box(self.df, "interruption_count", "Interruptions", self.t)
        self.assertEqual(len(fig.data), 3)
        self.assertEqual(excluded, [])

    def test_new_overview_charts_use_filtered_data_and_handle_small_slices(self):
        for name, d in self.slices():
            with self.subTest(name=name):
                area = charts.monthly_task_area(d, self.t)
                treemap = charts.task_work_treemap(d, self.t)
                pie = charts.category_pie(d, "task_type", self.t)
                ribbon = charts.developer_ribbon(d, self.t)
                self.assertIsNotNone(area)
                self.assertIsNotNone(treemap)
                self.assertIsNotNone(pie)
                self.assertIsNotNone(ribbon)
                if not d.empty:
                    self.assertEqual(sum(int(v) for v in pie.data[0].values), d["task_type"].notna().sum())

    def test_empty_figure_is_available(self):
        fig = charts.empty_figure("No data", self.t)
        self.assertEqual(len(fig.data), 0)


if __name__ == "__main__":
    unittest.main()
