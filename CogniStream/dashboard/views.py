"""
CogniStream - dashboard pages (Power BI-style visuals).

Each page is a function  page_xxx(df)  that receives the FILTERED DataFrame.
All numbers come from src/kpis.py (single source of truth); dashboard/chart_data.py
only reshapes them and dashboard/charts.py only draws them.
"""
from pathlib import Path

import streamlit as st

import kpis
from dashboard import chart_data as cd
from dashboard import charts
from dashboard.powerbi_style import (
    LOAD_COLORS,
    METRIC_COLORS,
    NEUTRAL_GREY,
    empty_state,
    render_kpi_row,
    section,
    show,
    show_table,
    small_sample_note,
    style_summary_df,
    visual,
    warn_small_n,
)

ROOT = Path(__file__).resolve().parent.parent
LOAD_ORDER = kpis.LOAD_ORDER
CAUTION = (
    "Charts show associations in this dataset, not cause and effect. "
    "The formulas for productivity_score and cognitive_load_level are not provided, "
    "and the dataset's origin (real or synthetic) is not confirmed."
)


# ---------- helpers ----------
def read_text(name):
    path = ROOT / "reports" / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def _empty_guard(df):
    """Return True and show a message when the filtered frame is empty."""
    if df is None or df.empty:
        st.warning("No sessions match these filters. Clear or reset filters in the sidebar.")
        return True
    return False


@st.cache_data(show_spinner=False)
def _baseline():
    """KPIs for the FULL dataset - the reference for 'vs all sessions' context lines."""
    return kpis.overview_kpis(kpis.load_clean())


def _card(label, value, help_text, key, k, base, filtered, higher_is_better, accent, decimals=1):
    """One KPI card tuple with a 'vs all sessions' context line when filters are active."""
    delta, tone = (None, "neutral")
    if filtered:
        delta, tone = cd.compare_to_baseline(k[key], base[key], higher_is_better, decimals)
    return (label, value, help_text, delta, tone, accent)


# ---------- pages ----------
def page_overview(df):
    st.subheader("Overview")
    st.caption(CAUTION)
    if _empty_guard(df):
        return

    k = kpis.overview_kpis(df)
    if not k:
        st.warning("No KPI values available for the current filter.")
        return
    base = _baseline()
    filtered = len(df) < base["sessions"]

    M = METRIC_COLORS
    sessions_ctx = (f"{k['sessions'] / base['sessions']:.0%} of all sessions"
                    if filtered else "All sessions in the dataset")
    devs_ctx = (f"of {base['developers']} developers" if filtered else "All developers")
    render_kpi_row([
        ("Sessions", f"{k['sessions']:,}", "Number of work sessions in the current filter.",
         sessions_ctx, "neutral", NEUTRAL_GREY),
        ("Developers", f"{k['developers']}", "Distinct developer_id values.",
         devs_ctx, "neutral", NEUTRAL_GREY),
        _card("Avg Productivity Score", f"{k['avg_productivity_score']}",
              "Mean of productivity_score. Formula not provided in the dataset.",
              "avg_productivity_score", k, base, filtered, True, M["productivity"]),
        _card("Avg Focus (min)", f"{k['avg_focus_minutes']}",
              "Mean focus_duration_minutes per session.",
              "avg_focus_minutes", k, base, filtered, True, M["focus"]),
    ])
    render_kpi_row([
        _card("Avg Flow (min)", f"{k['avg_flow_minutes']}",
              "Mean flow_state_duration_minutes per session.",
              "avg_flow_minutes", k, base, filtered, True, M["flow"]),
        _card("Avg Interruptions", f"{k['avg_interruptions']}",
              "Mean interruption_count per session. Lower is better.",
              "avg_interruptions", k, base, filtered, False, M["interruptions"], decimals=2),
        _card("High Cognitive Load %", f"{k['pct_high_cognitive_load']}%",
              "Share of sessions labelled High in cognitive_load_level. Lower is better.",
              "pct_high_cognitive_load", k, base, filtered, False, LOAD_COLORS["High"]),
        _card("Flow share of focus %", f"{k['flow_share_of_focus_pct']}%",
              "Total flow minutes / total focus minutes x 100.",
              "flow_share_of_focus_pct", k, base, filtered, True, M["flow"]),
    ])

    section("Headline")
    with visual("Average productivity score", "Blue bar = current selection · navy tick = all sessions"):
        show(charts.productivity_bullet(k["avg_productivity_score"], base["avg_productivity_score"]),
             key="ov_bullet")

    section("Load and trend")
    left, right = st.columns([1, 1.6])
    with left:
        with visual("Cognitive load share", "Share of sessions by load level"):
            show(charts.load_donut(kpis.load_distribution(df)), key="ov_donut")
    with right:
        month = kpis.monthly_trend(df).rename_axis("month").reset_index()
        with visual("Average productivity by month",
                    "Marker size = sessions that month · hollow = fewer than 30 sessions"):
            if len(month) > 1:
                show(charts.monthly_trend(month, float(df["productivity_score"].mean())), key="ov_trend")
            else:
                empty_state("Only one month in the current filter, so no trend line is drawn.")

    section("Developers")
    with visual("Developer productivity ranking",
                "Only developers with enough sessions are ranked, so one lucky session cannot win"):
        c1, c2 = st.columns(2)
        with c1:
            which = st.radio("Show", ["Top 10", "Bottom 10"], horizontal=True, key="ov_dev_which")
        with c2:
            min_s = st.slider("Minimum sessions per developer", 3, 20, 5, key="ov_dev_min")
        ranked, eligible, total = cd.developer_ranking(
            df, min_sessions=min_s, top_n=10, ascending=(which == "Bottom 10"))
        st.caption(f"{eligible} of {total} developers have at least {min_s} sessions in the current filter.")
        if ranked.empty:
            empty_state(f"No developer has {min_s}+ sessions in the current filter. Lower the minimum.")
        else:
            show(charts.developer_lollipop(ranked, float(df["productivity_score"].mean())), key="ov_dev")


def page_productivity(df):
    st.subheader("Productivity Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    avg = float(df["productivity_score"].mean())

    section("Drivers of productivity")
    left, right = st.columns([1.5, 1])
    with left:
        with visual("Flow duration vs productivity",
                    "Bubble area = focus minutes · colour = cognitive load · navy line = binned average"):
            show(charts.bubble_scatter(
                df, "flow_state_duration_minutes", "productivity_score",
                "Flow duration (min)", "Productivity score", size_col="focus_duration_minutes"),
                key="prod_bubble")
    with right:
        bands = cd.band_summary(df)
        with visual("Productivity by interruption band", "Average score per interruptions-per-session band"):
            if bands.empty:
                empty_state("No interruption-band data for the current filter.")
            else:
                show(charts.interruption_lollipop(bands, avg), key="prod_band")
                small_sample_note(bool(bands["small"].any()))

    section("Who and what is more productive?")
    panels = []
    for title, col, order in [
        ("Task type", "task_type", None),
        ("Work mode", "work_mode", None),
        ("Experience level", "experience_level", cd.EXPERIENCE_ORDER),
        ("Task complexity", "task_complexity", cd.COMPLEXITY_ORDER),
    ]:
        g = cd.group_summary(df, col, order)
        if order is None:
            g = g.sort_values("avg_productivity", ascending=False).reset_index(drop=True)
        if not g.empty:
            panels.append((title, g))
    with visual("Average productivity by group",
                "Same x-scale in every panel · dotted line = selection average · n in each label"):
        if panels:
            show(charts.productivity_small_multiples(panels, avg), key="prod_multiples")
            small_sample_note(any(bool(g["small"].any()) for _, g in panels))
        else:
            empty_state("No group data for the current filter.")

    group = st.selectbox(
        "Summary matrix by:",
        ["task_type", "work_mode", "experience_level", "task_complexity"],
        key="prod_matrix_group",
    )
    st.markdown("**Summary matrix**")
    show_table(style_summary_df(kpis.summary_by(df, group)))

    section("How the measures relate")
    left, right = st.columns([1.2, 1])
    with left:
        corr = cd.correlation_lower(df)
        with visual("Correlation between measures (Spearman)",
                    "Association, not cause and effect · blue = positive, orange = negative"):
            if corr is None:
                empty_state("At least 3 sessions are needed for a correlation matrix.")
            else:
                show(charts.correlation_heatmap(corr), key="prod_corr")
    with right:
        with visual("Coding duration vs productivity",
                    "Colour = cognitive load · navy line = binned average"):
            show(charts.bubble_scatter(
                df, "coding_duration_minutes", "productivity_score",
                "Coding duration (min)", "Productivity score"),
                key="prod_coding")


def page_cognitive(df):
    st.subheader("Cognitive Load Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return

    dist = kpis.load_distribution(df)
    render_kpi_row([
        (f"{lvl} cognitive load", f"{dist.loc[lvl, 'percent']}%",
         f"{int(dist.loc[lvl, 'sessions']):,} sessions", None, "neutral", LOAD_COLORS[lvl])
        for lvl in LOAD_ORDER
    ])
    low_n = int((df["cognitive_load_level"] == "Low").sum())
    warn_small_n(low_n, "Low cognitive load")

    section("Distribution and complexity")
    left, right = st.columns(2)
    with left:
        with visual("Sessions by cognitive load", "Count and share of the filtered sessions"):
            show(charts.load_bars(dist), key="cog_bars")
    with right:
        pct, counts = cd.complexity_load_matrix(df)
        with visual("Task complexity \u00d7 cognitive load",
                    "Each row sums to 100% · n shown in every cell"):
            show(charts.complexity_load_heatmap(pct, counts), key="cog_heat")

    section("Distribution within each load level")
    measures = {
        "Interruptions": "interruption_count",
        "Context switches": "context_switch_count",
        "Focus duration (min)": "focus_duration_minutes",
        "Flow duration (min)": "flow_state_duration_minutes",
        "Productivity score": "productivity_score",
        "Meeting minutes": "meeting_minutes",
    }
    with visual("How a measure is distributed in each load level",
                "Violin when every group has 30+ sessions, otherwise box plot with every point"):
        label = st.selectbox("Measure", list(measures), key="cog_measure")
        col = measures[label]
        mode, _sizes = cd.distribution_mode(df, col)
        if mode == "none":
            empty_state("No data for this measure in the current filter.")
        else:
            if mode == "box":
                st.caption("At least one load level has fewer than 30 sessions, so box plots with "
                           "every point are shown instead of violins.")
            show(charts.load_distribution(df, col, label, mode), key="cog_dist")

    section("Compare load levels")
    summ = cd.load_summary(df)
    with visual("Focus, flow, interruptions and productivity by load level",
                "Each mini chart has its own scale because the units differ"):
        if summ.empty:
            empty_state("No load-level data for the current filter.")
        else:
            show(charts.load_comparison(summ), key="cog_compare")
            small_sample_note(bool(summ["small"].any()))

    st.markdown("**Averages by cognitive load level**")
    show_table(style_summary_df(kpis.summary_by(df, "cognitive_load_level")))


def page_flow(df):
    st.subheader("Flow-State Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return

    k = kpis.overview_kpis(df)
    base = _baseline()
    filtered = len(df) < base["sessions"]
    zero = int((df["flow_state_duration_minutes"] == 0).sum())
    items = [
        _card("Avg Flow (min)", f"{k['avg_flow_minutes']}", "Mean flow_state_duration_minutes.",
              "avg_flow_minutes", k, base, filtered, True, METRIC_COLORS["flow"]),
        ("Sessions with zero flow", f"{zero}",
         f"{zero / len(df):.1%} of sessions have flow_state_duration_minutes = 0.",
         None, "neutral", NEUTRAL_GREY),
    ]
    if len(df) > 2:
        rho = df[["flow_state_duration_minutes", "productivity_score"]].corr(method="spearman").iloc[0, 1]
        items.append((
            "Flow vs productivity (Spearman)", "n/a" if rho != rho else f"{round(rho, 2)}",
            "Association from -1 to +1. Does not prove cause and effect.",
            None, "neutral", METRIC_COLORS["productivity"],
        ))
    render_kpi_row(items)

    section("Flow and productivity")
    left, right = st.columns(2)
    with left:
        with visual("Flow duration vs productivity (density)",
                    "Colour = sessions per cell · orange line = binned average productivity"):
            show(charts.flow_density(df), key="flow_density")
    with right:
        bands = cd.band_summary(df)
        with visual("Interruptions: flow and productivity",
                    "Bars = avg flow (left axis) · line = avg productivity (right axis)"):
            if bands.empty:
                empty_state("No interruption-band data for the current filter.")
            else:
                show(charts.band_combo(bands), key="flow_bands")
                small_sample_note(bool(bands["small"].any()))

    section("Flow distribution and task types")
    left, right = st.columns(2)
    with left:
        with visual("Flow duration distribution", "Stacked by cognitive load · dashed line = median"):
            fig = charts.flow_histogram(df)
            if fig is None:
                empty_state("No session in the current filter has any flow time.")
            else:
                show(fig, key="flow_hist")
    with right:
        summ = cd.group_summary(df, "task_type")
        with visual("Average flow by task type", "Ranked high to low · dotted line = selection average"):
            if summ.empty:
                empty_state("No task-type data for the current filter.")
            else:
                show(charts.flow_task_dotplot(summ, float(df["flow_state_duration_minutes"].mean())),
                     key="flow_tasks")
                small_sample_note(bool(summ["small"].any()))


@st.cache_resource(show_spinner="Building the document index...")
def _get_retriever():
    from rag import retriever
    return retriever.load_or_build()


def _get_key():
    """Gemini key from .env / environment, or from Streamlit secrets."""
    import os
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


SAMPLE_QUESTIONS = [
    "What does flow-state duration mean in this project?",
    "How is productivity measured in the dataset?",
    "What factors are associated with higher cognitive load?",
    "Summarize the observed productivity patterns.",
    "Explain the data-quality issues.",
]


def page_ai_assistant(df):
    st.subheader("AI Assistant")
    st.caption(
        "Answers come from project documents and from numbers calculated with Pandas on the "
        "current sidebar filters. Raw rows are never sent to the AI model."
    )
    try:
        from rag import assistant
        retr = _get_retriever()
    except Exception as err:  # missing package, missing docs, ...
        st.error(f"The assistant could not start: {err}")
        st.info(
            "Check that scikit-learn is installed (pip install -r requirements.txt) and that "
            "the docs/ folder exists."
        )
        return

    key = _get_key()
    st.caption(
        f"Mode: {'Gemini (grounded)' if key else 'Offline (no API key)'}  |  "
        f"Retrieval: {retr.backend_name}, {retr.store}"
    )

    if "chat" not in st.session_state:
        st.session_state.chat = []

    cols = st.columns(len(SAMPLE_QUESTIONS))
    clicked = None
    for col, q in zip(cols, SAMPLE_QUESTIONS):
        if col.button(q, key=f"sample_{q}"):
            clicked = q

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for s in msg["sources"]:
                        score = f" (similarity {s['score']})" if s["score"] is not None else ""
                        st.markdown(f"**[{s['label']}]** {s['kind']}: {s['name']}{score}")

    typed = st.chat_input("Ask about flow-state, productivity, cognitive load or data quality")
    question = typed or clicked
    if question:
        st.session_state.chat.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    res = assistant.ask(question, df, retr, api_key=key)
                except Exception as err:
                    res = {"answer": f"Something went wrong: {err}", "sources": [], "note": None}
            st.markdown(res["answer"])
            if res.get("note"):
                st.caption(res["note"])
            if res["sources"]:
                with st.expander("Sources"):
                    for s in res["sources"]:
                        score = f" (similarity {s['score']})" if s["score"] is not None else ""
                        st.markdown(f"**[{s['label']}]** {s['kind']}: {s['name']}{score}")
        st.session_state.chat.append({
            "role": "assistant", "content": res["answer"], "sources": res["sources"],
        })

    if st.session_state.chat and st.button("Clear chat"):
        st.session_state.chat = []
        st.rerun()


def page_reports(df):
    st.subheader("Reports")
    st.markdown("**Downloads**")
    if df is not None and not df.empty:
        st.download_button(
            "Download filtered data (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name="filtered_developer_productivity.csv",
            mime="text/csv",
        )
    else:
        st.info("No filtered rows to download.")

    for label, name in [
        ("Data-quality report", "data_quality_report.md"),
        ("EDA findings", "eda_findings.md"),
    ]:
        text = read_text(name)
        if text is None:
            st.warning(f"{name} not found. Run src/cleaning.py and src/eda.py first.")
            continue
        st.download_button(
            f"Download {label} (.md)", text.encode("utf-8"),
            file_name=name, mime="text/markdown",
        )
        with st.expander(f"Preview: {label}"):
            st.markdown(text)
