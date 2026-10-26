"""
CogniStream - dashboard pages (Power BI-style visuals).

Each page is a function  page_xxx(df, baseline)  that receives the FILTERED DataFrame
(`df`) and the unfiltered one (`baseline`, used only for "vs all sessions" context).
All numbers come from src/kpis.py (single source of truth); all figures are built in
dashboard/charts.py from the filtered frame.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

import kpis
from dashboard import charts
from dashboard.palette import PURPLE
from dashboard.powerbi_style import (
    delta_context,
    get_theme,
    render_kpi_row,
    show,
    show_df,
    style_summary_df,
    visual,
    warn_small_groups,
    warn_small_n,
)

ROOT = Path(__file__).resolve().parent.parent
LOAD_ORDER = kpis.LOAD_ORDER
CAUTION = (
    "Charts show associations in this dataset, not cause and effect. "
    "The formulas for productivity_score and cognitive_load_level are not provided, "
    "and the dataset's origin (real or synthetic) is not confirmed."
)
SMALL_NOTE = (
    f"Hollow dots / faded bars = fewer than {kpis.SMALL_N} sessions (not reliable). "
    "Dotted orange line = mean of the selected sessions."
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


def _render_session_table(df, key="session_table"):
    """Searchable, sortable, paginated table for the current filtered session rows."""
    if df is None or df.empty:
        st.info("No rows available for this table.")
        return
    query = st.text_input("Search sessions", key=f"{key}_search", placeholder="Search any visible field...")
    shown = df.copy()
    if query and query.strip():
        query = query.strip().casefold()
        mask = shown.astype(str).apply(lambda col: col.str.casefold().str.contains(query, regex=False, na=False)).any(axis=1)
        shown = shown.loc[mask]
    page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1, key=f"{key}_size")
    pages = max(1, (len(shown) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=pages, value=1, step=1, key=f"{key}_page")
    start = (int(page) - 1) * page_size
    page_df = shown.iloc[start:start + page_size]
    st.caption(f"Showing {min(start + 1, len(shown)):,}–{min(start + len(page_df), len(shown)):,} of {len(shown):,} matching rows. Click a column header to sort.")
    number_config = {}
    for col in page_df.columns:
        if pd.api.types.is_float_dtype(page_df[col]):
            number_config[col] = st.column_config.NumberColumn(col, format="%.2f")
        elif pd.api.types.is_integer_dtype(page_df[col]):
            number_config[col] = st.column_config.NumberColumn(col, format="%d")
    st.dataframe(page_df, use_container_width=True, hide_index=True, height=420,
                 column_config=number_config or None)


def _pretty_name(col):
    return charts.PRETTY.get(col, col).lower()


def _is_filtered(df, baseline):
    return baseline is not None and len(df) != len(baseline)


def _kpi_context(df, baseline, k, base_k, key, higher_is_better=None, unit="", decimals=1):
    """(context, tone) for one KPI card, only when a filter is active."""
    if not _is_filtered(df, baseline) or not base_k or key not in k:
        return None, "neutral"
    deltas = kpis.compare_to_baseline(k, base_k)
    return delta_context(deltas.get(key), higher_is_better, unit, decimals)


# ---------- pages ----------
def page_overview(df, baseline=None):
    st.subheader("Overview")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    t = get_theme()

    k = kpis.overview_kpis(df)
    if not k:
        st.warning("No KPI values available for the current filter.")
        return
    base = baseline if baseline is not None else df
    base_k = kpis.overview_kpis(base)
    filtered = _is_filtered(df, baseline)

    pct_sessions = f"{k['sessions'] / base_k['sessions'] * 100:.1f}% of all sessions" if filtered \
        else "All sessions"
    dev_ctx = f"of {base_k['developers']} developers" if filtered else "All developers"

    def card(label, value, key, help_text, hib=None, unit="", dec=1):
        ctx, tone = _kpi_context(df, baseline, k, base_k, key, hib, unit, dec)
        return (label, value, help_text, ctx, tone)

    render_kpi_row([
        ("Sessions", f"{k['sessions']:,}", "Number of work sessions in the current filter.",
         pct_sessions, "neutral"),
        ("Developers", f"{k['developers']}", "Distinct developer_id values.", dev_ctx, "neutral"),
        card("Avg Productivity Score", f"{k['avg_productivity_score']}", "avg_productivity_score",
             "Mean of productivity_score. Formula not provided in the dataset.", True),
        card("Avg Focus (min)", f"{k['avg_focus_minutes']}", "avg_focus_minutes",
             "Mean focus_duration_minutes per session."),
    ])
    render_kpi_row([
        card("Avg Flow (min)", f"{k['avg_flow_minutes']}", "avg_flow_minutes",
             "Mean flow_state_duration_minutes per session.", True),
        card("Avg Interruptions", f"{k['avg_interruptions']}", "avg_interruptions",
             "Mean interruption_count per session. Lower is shown in green.", False, "", 2),
        card("High Cognitive Load %", f"{k['pct_high_cognitive_load']}%", "pct_high_cognitive_load",
             "Share of sessions labelled High in cognitive_load_level. Lower is shown in green.",
             False, " pp"),
        card("Flow share of focus %", f"{k['flow_share_of_focus_pct']}%", "flow_share_of_focus_pct",
             "Total flow minutes ÷ total focus minutes × 100.", True, " pp"),
    ])
    if filtered:
        st.caption("Context lines compare the current filter with all sessions "
                   "(pp = percentage points). Colours only show direction; they are not a verdict.")

    left, right = st.columns([3, 2])
    with left:
        with visual("Average productivity score", "Bullet gauge: bar = current filter, "
                    "orange tick = mean of all sessions"):
            ref = kpis.productivity_reference(base)
            show(charts.productivity_bullet(k["avg_productivity_score"], ref, t),
                 key="ov_bullet")
    with right:
        with visual("Cognitive load share"):
            show(charts.load_donut(kpis.load_distribution(df), t), key="ov_donut")
            low_n = int((df["cognitive_load_level"] == "Low").sum())
            if low_n < kpis.SMALL_N:
                st.caption(f"⚠ Low load has only {low_n} sessions in this filter.")

    with visual("Average productivity by month",
                "Line = average productivity, bars = sessions per month, "
                "hollow marker = month with few sessions"):
        month = kpis.monthly_trend(df).reset_index().rename(columns={"session_date": "month"})
        if len(month) > 1:
            show(charts.monthly_trend_chart(month, float(df["productivity_score"].mean()), t),
                 key="ov_trend")
        else:
            st.info("Only one month in the current filter, so no trend line is drawn.")

    left, right = st.columns(2)
    with left:
        with visual("Session volume by task type over time",
                    "Stacked area shows how monthly session volume is distributed across task types."):
            show(charts.monthly_task_area(df, t), key="ov_task_area")
    with right:
        with visual("Task type and work mode mix",
                    "Tile size = session count; colour = average productivity score."):
            show(charts.task_work_treemap(df, t), key="ov_task_treemap")

    left, right = st.columns(2)
    with left:
        with visual("Session share by task type",
                    "Simple part-to-whole view for the selected sessions."):
            show(charts.category_pie(df, "task_type", t), key="ov_task_pie")
    with right:
        with visual("Session details",
                    "Search, sort, and page through the sessions matching the current filters."):
            display_cols = [c for c in ["session_id", "session_date", "developer_id", "task_type",
                                         "work_mode", "productivity_score", "cognitive_load_level"]
                            if c in df.columns]
            _render_session_table(df[display_cols], key="overview_sessions")

    with visual("Developer productivity rank changes",
                "Ribbon-style ranking by month for the developers with the most sessions; rank 1 is highest."):
        show(charts.developer_ribbon(df, t), key="ov_ribbon")

    with visual("Developer productivity ranking",
                "Average productivity per developer; only developers with enough sessions are ranked"):
        c1, c2 = st.columns(2)
        min_sessions = c1.slider("Minimum sessions per developer", 1, 30,
                                 kpis.MIN_SESSIONS_DEVELOPER, key="ov_min_sessions")
        top_n = c2.slider("Developers shown", 3, 20, 10, key="ov_top_n")
        rank = kpis.developer_ranking(df, min_sessions=min_sessions, top_n=top_n)
        if rank.empty:
            st.info(f"No developer has {min_sessions}+ sessions in the current filter.")
        else:
            show(charts.developer_lollipop(rank, float(df["productivity_score"].mean()), t,
                                           min_sessions), key="ov_rank")
            st.caption(SMALL_NOTE + " Ranking differences between developers can be small; "
                       "sessions per developer are listed in the hover text.")

    with st.expander("Drill down: one developer's sessions"):
        devs = sorted(df["developer_id"].unique())
        pick = st.selectbox("Developer", ["(none selected)"] + devs, key="ov_drill_dev")
        if pick != "(none selected)":
            dev_df = df[df["developer_id"] == pick]
            show(charts.developer_session_chart(dev_df, t), key="ov_drill_chart")
            st.caption(f"{pick}: {len(dev_df)} sessions, average productivity "
                       f"{dev_df['productivity_score'].mean():.1f}.")
            if len(dev_df) < kpis.SMALL_N:
                st.caption("⚠ Few sessions for one developer: treat this as a description, "
                           "not as a reliable rating.")


def page_productivity(df, baseline=None):
    st.subheader("Productivity Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    t = get_theme()
    mean_prod = float(df["productivity_score"].mean())

    left, right = st.columns(2)
    with left:
        with visual("Flow duration vs productivity",
                    "Each bubble is a session; colour = cognitive load, size = focus minutes. "
                    "Click legend items to hide or isolate a load level"):
            rho = kpis.spearman(df, "flow_state_duration_minutes", "productivity_score")
            show(charts.load_scatter(df, "flow_state_duration_minutes", "productivity_score",
                                     t, rho=rho), key="pr_scatter")
    with right:
        with visual("Average productivity by interruption band",
                    "Sessions grouped by number of interruptions"):
            bands = kpis.interruption_bands(df).reset_index()
            bands = bands.rename(columns={bands.columns[0]: "interruption_band"})
            bands["interruption_band"] = bands["interruption_band"].astype(str)
            if bands.empty or bands["sessions"].sum() == 0:
                st.info("No interruption-band data for the current filter.")
            else:
                show(charts.dot_plot(bands, "interruption_band", "avg_productivity",
                                     "Avg productivity", t, order=kpis.BAND_LABELS,
                                     ref=mean_prod, x_title="Avg productivity score",
                                     height=360), key="pr_bands")
                warn_small_groups(bands.set_index("interruption_band"), "interruption bands")

    metric_label = st.selectbox("Compare groups by metric", list(charts.SUMMARY_METRICS),
                                key="pr_metric")
    metric_col = charts.SUMMARY_METRICS[metric_label]
    with visual(f"{metric_label} by task type, work mode and experience level",
                "Small multiples on one shared scale. " + SMALL_NOTE):
        groups = [("task_type", None), ("work_mode", kpis.WORK_MODE_ORDER),
                  ("experience_level", kpis.EXPERIENCE_ORDER)]
        ref = float(df[charts.METRIC_SOURCE[metric_col]].mean())
        show(charts.small_multiples(df, groups, metric_col, metric_label, t, ref=ref,
                                    fmt=".2f" if metric_col in ("avg_interruptions", "avg_context_switches")
                                    else ".1f"), key="pr_multiples")
        for col, _ in groups:
            warn_small_groups(kpis.summary_by(df, col), _pretty_name(col))

    with visual("Summary matrix", "Averages per group; colour scale per column"):
        group = st.selectbox("Group by", ["task_type", "work_mode", "experience_level",
                                          "task_complexity"], key="pr_group")
        summ = kpis.summary_by(df, group)
        if group in kpis.CATEGORY_ORDERS:
            summ = summ.reindex([c for c in kpis.CATEGORY_ORDERS[group] if c in summ.index])
        warn_small_groups(summ, _pretty_name(group))
        show_df(style_summary_df(summ))

    with visual("Correlation heatmap",
                "Spearman rank correlation of the numeric columns (lower triangle). "
                "Association only, not cause and effect"):
        if len(df) < 10:
            st.info("At least 10 sessions are needed for a meaningful correlation matrix.")
        else:
            show(charts.correlation_heatmap(kpis.correlation_matrix(df), t), key="pr_corr")
            if len(df) < kpis.SMALL_N:
                st.caption(f"⚠ Only {len(df)} sessions selected: correlations are unstable.")

    with visual("Coding duration vs productivity",
                "Bubble = session; colour = cognitive load, size = focus minutes"):
        rho = kpis.spearman(df, "coding_duration_minutes", "productivity_score")
        show(charts.load_scatter(df, "coding_duration_minutes", "productivity_score", t, rho=rho),
             key="pr_coding")


def page_cognitive(df, baseline=None):
    st.subheader("Cognitive Load Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    t = get_theme()

    low_n = int((df["cognitive_load_level"] == "Low").sum())
    warn_small_n(low_n, "Low cognitive load")

    left, right = st.columns(2)
    with left:
        with visual("Share of sessions by cognitive load"):
            show(charts.load_donut(kpis.load_distribution(df), t), key="cg_donut")
    with right:
        with visual("Task complexity vs cognitive load",
                    "% of each complexity's sessions in each load level (n and ⚠ for small cells)"):
            counts, pct = kpis.load_by_complexity(df)
            show(charts.load_complexity_heatmap(counts, pct, t), key="cg_heat")

    with visual("Distribution of a measure by cognitive load",
                "Box = middle 50 % of sessions, line = median, dashed line = mean, dots = outliers "
                "(outliers are real values, not errors)"):
        label = st.selectbox("Measure", list(charts.BOX_METRICS), key="cg_box_metric")
        fig, excluded = charts.load_box(df, charts.BOX_METRICS[label], label, t)
        if fig is None:
            st.info(f"No cognitive-load group has {charts.MIN_BOX_N}+ sessions, "
                    "so no box plot is drawn.")
        else:
            show(fig, key="cg_box")
        for lvl, n in excluded:
            st.caption(f"{lvl} left out of the box plot: {n} sessions "
                       f"(needs {charts.MIN_BOX_N}+).")
        small = [(lvl, int((df['cognitive_load_level'] == lvl).sum())) for lvl in LOAD_ORDER]
        small = [f"{lvl} (n={n})" for lvl, n in small if charts.MIN_BOX_N <= n < kpis.SMALL_N]
        if small:
            st.caption("⚠ Small groups shown but not reliable: " + ", ".join(small) + ".")

    summ = kpis.summary_by(df, "cognitive_load_level")
    with visual("Comparison by cognitive load",
                "Average focus, flow, interruptions and productivity per level (faded = few sessions)"):
        show(charts.load_comparison(summ, t), key="cg_compare")

    with visual("Averages by cognitive load level"):
        show_df(style_summary_df(summ.dropna(how="all")))

    with st.expander("Drill down: one cognitive-load level"):
        present = [lvl for lvl in LOAD_ORDER if (df["cognitive_load_level"] == lvl).any()]
        pick = st.selectbox("Cognitive-load level", present, key="cg_drill_level")
        sub = df[df["cognitive_load_level"] == pick]
        share = kpis.share_by(sub, "task_type").reset_index()
        share = share.rename(columns={share.columns[0]: "task_type"})
        st.caption(f"{pick} cognitive load: {len(sub)} sessions in this filter.")
        show(charts.dot_plot(share, "task_type", "percent", "Share of this level's sessions (%)",
                             t, x_title="% of this level's sessions"), key="cg_drill_chart")
        if len(sub) < kpis.SMALL_N:
            st.caption("⚠ Few sessions: treat shares as a description only.")


def page_flow(df, baseline=None):
    st.subheader("Flow-State Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    t = get_theme()

    zero = int((df["flow_state_duration_minutes"] == 0).sum())
    k = kpis.overview_kpis(df)
    base_k = kpis.overview_kpis(baseline) if baseline is not None else {}
    ctx, tone = _kpi_context(df, baseline, k, base_k, "avg_flow_minutes", True)
    items = [
        ("Avg Flow (min)", f"{k.get('avg_flow_minutes', round(df['flow_state_duration_minutes'].mean(), 1))}",
         "Mean flow_state_duration_minutes.", ctx, tone),
        ("Sessions with zero flow", f"{zero}", "Sessions where flow_state_duration_minutes is 0.",
         f"{zero / len(df) * 100:.1f}% of selected sessions", "neutral"),
    ]
    rho = kpis.spearman(df, "flow_state_duration_minutes", "productivity_score")
    if rho is not None:
        items.append((
            "Flow vs productivity (Spearman)", f"{rho}",
            "Association from -1 to +1. Does not prove cause and effect.",
            "association only", "neutral",
        ))
    render_kpi_row(items)

    left, right = st.columns(2)
    with left:
        with visual("Flow duration vs productivity",
                    "Bubble = session; colour = cognitive load, size = focus minutes"):
            show(charts.load_scatter(df, "flow_state_duration_minutes", "productivity_score",
                                     t, rho=rho), key="fl_scatter")
    with right:
        with visual("Flow duration distribution",
                    "Sessions per 5-minute bin, stacked by cognitive load"):
            show(charts.flow_histogram(df, t), key="fl_hist")

    left, right = st.columns(2)
    with left:
        with visual("Average flow by task type", "Ranked high to low. " + SMALL_NOTE):
            summ = kpis.summary_by(df, "task_type").reset_index()
            show(charts.dot_plot(summ, "task_type", "avg_flow", "Avg flow (min)", t,
                                 ref=float(df["flow_state_duration_minutes"].mean()),
                                 x_title="Avg flow (min)", color=PURPLE), key="fl_task")
            warn_small_groups(kpis.summary_by(df, "task_type"), "task types")
    with right:
        with visual("Interruption bands: flow and zero-flow sessions",
                    "Sessions grouped by number of interruptions"):
            bands = kpis.flow_by_band(df)
            if bands.empty:
                st.info("No interruption-band data for the current filter.")
            else:
                show(charts.band_comparison(bands, t), key="fl_bands")
                warn_small_groups(bands, "interruption bands")


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


def page_ai_assistant(df, baseline=None):
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


def page_reports(df, baseline=None):
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

    if df is not None and not df.empty:
        with st.expander("Explore filtered sessions", expanded=False):
            st.caption("The table contains only rows matching the sidebar filters.")
            _render_session_table(df, key="reports_sessions")

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
