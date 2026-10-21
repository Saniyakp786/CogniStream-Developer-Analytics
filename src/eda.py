"""
CogniStream - Phase 2: Exploratory Data Analysis.

Run from the project root:
    python src/eda.py

Needs: data/cleaned_developer_productivity.csv  (run src/cleaning.py first)
Output: reports/charts/*.png  and  reports/eda_findings.md
All numbers in the findings file are calculated from the data, not typed by hand.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # saves files, no pop-up window
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kpis  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CHART_DIR = ROOT / "reports" / "charts"
FINDINGS_PATH = ROOT / "reports" / "eda_findings.md"
COLORS = {"Low": "#4CAF50", "Medium": "#FFC107", "High": "#F44336"}


def save(fig, name):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(CHART_DIR / name, dpi=130)
    plt.close(fig)
    print("saved chart:", name)


def make_charts(df):
    # 1. Productivity score distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["productivity_score"], bins=20, color="#4C78A8", edgecolor="white")
    ax.set(title="Productivity score distribution", xlabel="Productivity score", ylabel="Sessions")
    save(fig, "01_productivity_distribution.png")

    # 2. Cognitive load distribution
    dist = kpis.load_distribution(df)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(dist.index, dist["sessions"], color=[COLORS[i] for i in dist.index])
    for i, (n, p) in enumerate(zip(dist["sessions"], dist["percent"])):
        ax.text(i, n + 8, f"{n} ({p}%)", ha="center")
    ax.set(title="Cognitive load level (sessions)", ylabel="Sessions")
    save(fig, "02_cognitive_load_distribution.png")

    # 3. Interruptions vs productivity (box plot by band)
    bands = pd.cut(df["interruption_count"], bins=[-1, 1, 3, 5, 100], labels=["0-1", "2-3", "4-5", "6+"])
    groups = [df.loc[bands == b, "productivity_score"] for b in bands.cat.categories]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot(groups, tick_labels=list(bands.cat.categories))
    ax.set(title="Productivity by number of interruptions", xlabel="Interruptions per session",
           ylabel="Productivity score")
    save(fig, "03_interruptions_vs_productivity.png")

    # 4. Flow duration vs productivity (scatter, coloured by load)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for level in kpis.LOAD_ORDER:
        s = df[df["cognitive_load_level"] == level]
        ax.scatter(s["flow_state_duration_minutes"], s["productivity_score"], s=14,
                   alpha=0.6, label=level, color=COLORS[level])
    ax.set(title="Flow-state duration vs productivity", xlabel="Flow-state minutes",
           ylabel="Productivity score")
    ax.legend(title="Cognitive load")
    save(fig, "04_flow_vs_productivity.png")

    # 5. Average productivity and flow by cognitive load
    s = kpis.summary_by(df, "cognitive_load_level")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].bar(s.index, s["avg_productivity"], color=[COLORS[i] for i in s.index])
    axes[0].set(title="Avg productivity by load", ylabel="Score")
    axes[1].bar(s.index, s["avg_flow"], color=[COLORS[i] for i in s.index])
    axes[1].set(title="Avg flow minutes by load", ylabel="Minutes")
    save(fig, "05_load_vs_productivity_flow.png")

    # 6. Correlation heatmap
    corr = kpis.correlation_matrix(df)
    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), [c.replace("_minutes", "").replace("_count", "")
                                     for c in corr.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(corr)), [c.replace("_minutes", "").replace("_count", "")
                                     for c in corr.index])
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im)
    ax.set_title("Spearman correlation (association, not causation)")
    save(fig, "06_correlation_heatmap.png")

    # 7. Monthly trend
    m = kpis.monthly_trend(df)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(m.index, m["avg_productivity"], marker="o", color="#4C78A8")
    ax.set(title="Average productivity by month", ylabel="Score")
    plt.setp(ax.get_xticklabels(), rotation=45)
    save(fig, "07_monthly_trend.png")

    # 8. Productivity by task complexity and work mode
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, col in zip(axes, ["task_complexity", "work_mode"]):
        t = kpis.summary_by(df, col)
        ax.bar(t.index, t["avg_productivity"], color="#72B7B2")
        ax.set(title=f"Avg productivity by {col}", ylabel="Score")
    save(fig, "08_productivity_by_complexity_workmode.png")


def write_findings(df):
    k = kpis.overview_kpis(df)
    load = kpis.summary_by(df, "cognitive_load_level")
    bands = kpis.interruption_bands(df)
    corr = kpis.correlation_matrix(df)["productivity_score"].drop("productivity_score").sort_values()
    exp = kpis.summary_by(df, "experience_level")
    mode = kpis.summary_by(df, "work_mode")
    task = kpis.summary_by(df, "task_type")
    comp = kpis.summary_by(df, "task_complexity")
    month = kpis.monthly_trend(df)
    first_m, last_m = month.iloc[0], month.iloc[-1]

    L = ["# CogniStream - EDA Findings (auto-generated from the data)", "",
         "Important: these are ASSOCIATIONS in this dataset. They do not prove cause and effect. "
         "The origin of the dataset (real or synthetic) is not confirmed, and the formulas for "
         "productivity_score and cognitive_load_level are unknown.", "",
         "## Headline KPIs"]
    for key, v in k.items():
        L.append(f"- {key.replace('_', ' ')}: {v}")
    L += ["", "## Cognitive load",
          kpis.load_distribution(df).to_markdown(), "",
          "Averages by load level:", "", load.to_markdown(), "",
          f"- High-load sessions average productivity {load.loc['High', 'avg_productivity']} "
          f"vs {load.loc['Low', 'avg_productivity']} for Low-load sessions "
          f"(Low has only {int(load.loc['Low', 'sessions'])} sessions, so treat with care).", "",
          "## Interruptions", bands.to_markdown(), "",
          f"- Sessions with 0-1 interruptions average {bands.iloc[0]['avg_productivity']} productivity; "
          f"sessions with 6+ interruptions average {bands.iloc[-1]['avg_productivity']}.", "",
          "## Spearman correlation with productivity_score", corr.to_frame("rho").to_markdown(), "",
          "## By experience level", exp.to_markdown(), "",
          "## By work mode", mode.to_markdown(), "",
          "## By task type", task.to_markdown(), "",
          "## By task complexity", comp.to_markdown(), "",
          "## Monthly trend",
          f"- First month ({month.index[0]}) average productivity {first_m['avg_productivity']}, "
          f"last month ({month.index[-1]}) {last_m['avg_productivity']}.", "",
          month.to_markdown()]
    FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS_PATH.write_text("\n".join(L), encoding="utf-8")
    print("saved findings:", FINDINGS_PATH)


def main():
    df = kpis.load_clean()
    k = kpis.overview_kpis(df)
    print("\n=== HEADLINE KPIs ===")
    for key, v in k.items():
        print(f"{key:28s} {v}")
    print("\n=== BY COGNITIVE LOAD ===\n", kpis.summary_by(df, "cognitive_load_level"))
    print("\n=== BY INTERRUPTION BAND ===\n", kpis.interruption_bands(df))
    print("\n=== CORRELATION WITH PRODUCTIVITY (Spearman) ===")
    print(kpis.correlation_matrix(df)["productivity_score"].sort_values())
    make_charts(df)
    write_findings(df)


if __name__ == "__main__":
    main()
