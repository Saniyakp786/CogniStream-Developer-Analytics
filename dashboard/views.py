"""
CogniStream - Phase 3: dashboard pages (Power BI–style visuals).

Each page is a function  page_xxx(df)  that receives the FILTERED DataFrame.
All numbers come from src/kpis.py (single source of truth).
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import kpis
from dashboard.powerbi_style import (
    LOAD_COLORS,
    PBI_PALETTE,
    apply_layout,
    get_theme,
    render_kpi_row,
    show,
    style_summary_df,
    warn_small_n,
)

ROOT = Path(__file__).resolve().parent.parent
LOAD_ORDER = kpis.LOAD_ORDER
BAND_ORDER = ["0-1", "2-3", "4-5", "6+"]
CAUTION = (
    "Charts show associations in this dataset, not cause and effect. "
    "The formulas for productivity_score and cognitive_load_level are not provided, "
    "and the dataset's origin (real or synthetic) is not confirmed."
)


# ---------- helpers ----------
def add_band(df):
    out = df.copy()
    out["interruption_band"] = pd.cut(
        out["interruption_count"], bins=[-1, 1, 3, 5, 1000], labels=BAND_ORDER
    )
    return out


def read_text(name):
    path = ROOT / "reports" / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def _empty_guard(df):
    """Return True and show a message when the filtered frame is empty."""
    if df is None or df.empty:
        st.warning("No sessions match these filters. Clear or reset filters in the sidebar.")
        return True
    return False


def _clustered_column(summ, x_col, y_col, title, hover_extra=None):
    """Clustered column chart with data labels (1 decimal)."""
    hover = hover_extra or ["sessions"]
    fig = px.bar(
        summ, x=x_col, y=y_col, text=y_col,
        color_discrete_sequence=PBI_PALETTE,
        hover_data=hover,
        title=title,
    )
    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y:.1f}}<extra></extra>",
    )
    fig.update_layout(showlegend=False, uniformtext_minsize=8, uniformtext_mode="hide")
    return fig


def _top_developers(df, min_sessions=5, top_n=10):
    """Top N developers by avg productivity (need at least min_sessions)."""
    g = (
        df.groupby("developer_id")
        .agg(
            sessions=("session_id", "count"),
            avg_productivity=("productivity_score", "mean"),
        )
        .reset_index()
    )
    g = g[g["sessions"] >= min_sessions].sort_values("avg_productivity", ascending=False)
    return g.head(top_n).round(2)


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

    # Power BI card visuals (from overview_kpis only)
    render_kpi_row([
        ("Sessions", f"{k['sessions']:,}", "Number of work sessions in the current filter."),
        ("Developers", f"{k['developers']}", "Distinct developer_id values."),
        ("Avg Productivity Score", f"{k['avg_productivity_score']}",
         "Mean of productivity_score. Formula not provided in the dataset."),
        ("Avg Focus (min)", f"{k['avg_focus_minutes']}", "Mean focus_duration_minutes per session."),
    ])
    render_kpi_row([
        ("Avg Flow (min)", f"{k['avg_flow_minutes']}", "Mean flow_state_duration_minutes per session."),
        ("Avg Interruptions", f"{k['avg_interruptions']}", "Mean interruption_count per session."),
        ("High Cognitive Load %", f"{k['pct_high_cognitive_load']}%",
         "Share of sessions labelled High in cognitive_load_level."),
        ("Flow share of focus %", f"{k['flow_share_of_focus_pct']}%",
         "Total flow minutes ÷ total focus minutes × 100."),
    ])

    # Gauge for Avg Productivity Score (0–100)
    left, right = st.columns([1, 2])
    with left:
        t = get_theme()
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=k["avg_productivity_score"],
            number={"font": {"size": 36, "family": "Segoe UI, Arial, sans-serif"}},
            title={"text": "Avg Productivity Score", "font": {"size": 13}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#118DFF"},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "rgba(214, 69, 80, 0.2)"},
                    {"range": [40, 70], "color": "rgba(242, 200, 17, 0.2)"},
                    {"range": [70, 100], "color": "rgba(43, 168, 74, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": "#12239E", "width": 2},
                    "thickness": 0.75,
                    "value": k["avg_productivity_score"],
                },
            },
        ))
        apply_layout(gauge, title=None)
        gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=10))
        show(gauge)

    with right:
        dist = kpis.load_distribution(df).rename_axis("cognitive_load_level").reset_index()
        fig = px.pie(
            dist, names="cognitive_load_level", values="sessions",
            color="cognitive_load_level", color_discrete_map=LOAD_COLORS,
            category_orders={"cognitive_load_level": LOAD_ORDER}, hole=0.55,
            title="Cognitive load share",
        )
        fig.update_traces(
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Sessions: %{value}<br>Share: %{percent}<extra></extra>",
        )
        show(fig, title="Cognitive load share")

    # Monthly trend: line + markers + area fill
    month = kpis.monthly_trend(df).reset_index().rename(columns={"session_date": "month"})
    if len(month) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=month["month"], y=month["avg_productivity"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#118DFF", width=2),
            marker=dict(size=7, color="#12239E"),
            name="Avg productivity",
            customdata=month[["sessions", "avg_flow", "avg_interruptions"]],
            hovertemplate=(
                "<b>%{x}</b><br>Avg productivity: %{y:.2f}"
                "<br>Sessions: %{customdata[0]}"
                "<br>Avg flow (min): %{customdata[1]:.2f}"
                "<br>Avg interruptions: %{customdata[2]:.2f}<extra></extra>"
            ),
        ))
        show(fig, title="Average productivity by month")
    else:
        st.info("Only one month in the current filter, so no trend line is drawn.")

    # Top 10 developers
    top = _top_developers(df)
    if not top.empty:
        fig = px.bar(
            top.sort_values("avg_productivity"),
            x="avg_productivity", y="developer_id", orientation="h",
            text="avg_productivity",
            color_discrete_sequence=["#118DFF"],
            hover_data=["sessions"],
            title="Top 10 developers by avg productivity (≥5 sessions)",
        )
        fig.update_traces(
            texttemplate="%{text:.1f}", textposition="outside",
            hovertemplate="<b>%{y}</b><br>Avg productivity: %{x:.1f}<br>Sessions: %{customdata[0]}<extra></extra>",
        )
        show(fig, title="Top 10 developers by avg productivity (≥5 sessions)")
    else:
        st.info("Not enough developers with ≥5 sessions for a top-10 chart.")


def page_productivity(df):
    st.subheader("Productivity Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    df = add_band(df)

    left, right = st.columns(2)
    with left:
        # Bubble: flow vs productivity, colour = cognitive load, size ~ focus
        size_col = df["focus_duration_minutes"].clip(lower=1)
        fig = px.scatter(
            df, x="flow_state_duration_minutes", y="productivity_score",
            color="cognitive_load_level", color_discrete_map=LOAD_COLORS,
            category_orders={"cognitive_load_level": LOAD_ORDER},
            size=size_col, size_max=28, opacity=0.75,
            hover_data=["developer_id", "task_type", "interruption_count", "focus_duration_minutes"],
            title="Flow vs productivity (bubble = focus minutes)",
            labels={
                "flow_state_duration_minutes": "Flow duration (min)",
                "productivity_score": "Productivity score",
            },
        )
        fig.update_traces(
            hovertemplate=(
                "Flow: %{x:.1f} min<br>Productivity: %{y:.1f}"
                "<br>Developer: %{customdata[0]}<br>Task: %{customdata[1]}"
                "<br>Interruptions: %{customdata[2]}<br>Focus: %{customdata[3]:.1f} min"
                "<extra></extra>"
            ),
        )
        show(fig, title="Flow vs productivity (bubble = focus minutes)")

    with right:
        # Interruption bands – clustered columns of avg productivity
        bands = kpis.interruption_bands(df).reindex(BAND_ORDER).dropna(how="all").reset_index()
        bands = bands.rename(columns={bands.columns[0]: "interruption_band"})
        if bands.empty or bands["sessions"].sum() == 0:
            st.info("No interruption-band data for the current filter.")
        else:
            for _, row in bands.iterrows():
                if row["sessions"] < 30:
                    warn_small_n(int(row["sessions"]), f"band {row['interruption_band']}")
            fig = _clustered_column(
                bands, "interruption_band", "avg_productivity",
                "Avg productivity by interruption band",
                hover_extra=["sessions", "avg_flow"],
            )
            show(fig, title="Avg productivity by interruption band")

    group = st.selectbox(
        "Compare average productivity by:",
        ["task_type", "work_mode", "experience_level", "task_complexity"],
    )
    summ = kpis.summary_by(df, group).reset_index()
    # Flag small groups
    for _, row in summ.iterrows():
        if row["sessions"] < 30:
            warn_small_n(int(row["sessions"]), f"{group} = {row[group]}")

    fig = _clustered_column(
        summ, group, "avg_productivity",
        f"Average productivity by {group}",
        hover_extra=["sessions", "avg_focus", "avg_flow"],
    )
    show(fig, title=f"Average productivity by {group}")

    st.markdown("**Summary matrix**")
    st.dataframe(style_summary_df(summ.set_index(group)), use_container_width=True)

    fig = px.scatter(
        df, x="coding_duration_minutes", y="productivity_score",
        color_discrete_sequence=[PBI_PALETTE[0]], opacity=0.65,
        hover_data=["developer_id", "task_type"],
        labels={
            "coding_duration_minutes": "Coding duration (min)",
            "productivity_score": "Productivity score",
        },
        title="Coding duration vs productivity",
    )
    fig.update_traces(
        hovertemplate="Coding: %{x:.1f} min<br>Productivity: %{y:.1f}"
                      "<br>Developer: %{customdata[0]}<br>Task: %{customdata[1]}<extra></extra>",
    )
    show(fig, title="Coding duration vs productivity")


def page_cognitive(df):
    st.subheader("Cognitive Load Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    df = add_band(df)

    low_n = int((df["cognitive_load_level"] == "Low").sum())
    warn_small_n(low_n, "Low cognitive load")

    left, right = st.columns(2)
    with left:
        dist = kpis.load_distribution(df).rename_axis("cognitive_load_level").reset_index()
        fig = px.pie(
            dist, names="cognitive_load_level", values="sessions",
            color="cognitive_load_level", color_discrete_map=LOAD_COLORS,
            category_orders={"cognitive_load_level": LOAD_ORDER}, hole=0.55,
            title="Share of sessions by cognitive load",
        )
        fig.update_traces(
            textposition="inside", textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Sessions: %{value}<br>Share: %{percent}<extra></extra>",
        )
        show(fig, title="Share of sessions by cognitive load")

    with right:
        fig = px.box(
            df, x="cognitive_load_level", y="interruption_count",
            color="cognitive_load_level", color_discrete_map=LOAD_COLORS,
            category_orders={"cognitive_load_level": LOAD_ORDER},
            title="Interruptions by cognitive load",
            labels={"interruption_count": "Interruptions", "cognitive_load_level": "Cognitive load"},
        )
        fig.update_layout(showlegend=False)
        fig.update_traces(hovertemplate="Load: %{x}<br>Interruptions: %{y}<extra></extra>")
        show(fig, title="Interruptions by cognitive load")

    left, right = st.columns(2)
    with left:
        fig = px.box(
            df, x="cognitive_load_level", y="context_switch_count",
            color="cognitive_load_level", color_discrete_map=LOAD_COLORS,
            category_orders={"cognitive_load_level": LOAD_ORDER},
            title="Context switches by cognitive load",
            labels={"context_switch_count": "Context switches", "cognitive_load_level": "Cognitive load"},
        )
        fig.update_layout(showlegend=False)
        show(fig, title="Context switches by cognitive load")

    with right:
        # Matrix: task_complexity × cognitive_load (% of sessions) via Styler
        ct = (
            pd.crosstab(df["task_complexity"], df["cognitive_load_level"], normalize="index") * 100
        )
        ct = ct.reindex(index=["Low", "Medium", "High"], columns=LOAD_ORDER).fillna(0).round(1)
        st.markdown("**Task complexity × cognitive load (% of sessions)**")
        try:
            styled = ct.style.background_gradient(cmap="Blues", axis=None).format("{:.1f}%")
            st.dataframe(styled, use_container_width=True)
        except Exception:
            st.dataframe(ct, use_container_width=True)

    st.markdown("**Averages by cognitive load level**")
    summ = kpis.summary_by(df, "cognitive_load_level")
    st.dataframe(style_summary_df(summ), use_container_width=True)


def page_flow(df):
    st.subheader("Flow-State Analysis")
    st.caption(CAUTION)
    if _empty_guard(df):
        return
    df = add_band(df)

    zero = int((df["flow_state_duration_minutes"] == 0).sum())
    k = kpis.overview_kpis(df)
    items = [
        ("Avg Flow (min)", f"{k.get('avg_flow_minutes', round(df['flow_state_duration_minutes'].mean(), 1))}",
         "Mean flow_state_duration_minutes."),
        ("Sessions with zero flow", f"{zero}", "Sessions where flow_state_duration_minutes is 0."),
    ]
    if len(df) > 2:
        rho = df[["flow_state_duration_minutes", "productivity_score"]].corr(method="spearman").iloc[0, 1]
        items.append((
            "Flow vs productivity (Spearman)", f"{round(rho, 2)}",
            "Association from -1 to +1. Does not prove cause and effect.",
        ))
    render_kpi_row(items)

    left, right = st.columns(2)
    with left:
        size_col = df["focus_duration_minutes"].clip(lower=1)
        fig = px.scatter(
            df, x="flow_state_duration_minutes", y="productivity_score",
            color="cognitive_load_level", color_discrete_map=LOAD_COLORS,
            category_orders={"cognitive_load_level": LOAD_ORDER},
            size=size_col, size_max=28, opacity=0.75,
            hover_data=["developer_id", "task_type"],
            labels={
                "flow_state_duration_minutes": "Flow duration (min)",
                "productivity_score": "Productivity score",
            },
            title="Flow duration vs productivity",
        )
        fig.update_traces(
            hovertemplate="Flow: %{x:.1f} min<br>Productivity: %{y:.1f}"
                          "<br>Developer: %{customdata[0]}<br>Task: %{customdata[1]}<extra></extra>",
        )
        show(fig, title="Flow duration vs productivity")

    with right:
        bands = kpis.interruption_bands(df).reindex(BAND_ORDER).dropna(how="all").reset_index()
        bands = bands.rename(columns={bands.columns[0]: "interruption_band"})
        if bands.empty:
            st.info("No interruption-band data for the current filter.")
        else:
            fig = px.box(
                df, x="interruption_band", y="flow_state_duration_minutes",
                category_orders={"interruption_band": BAND_ORDER},
                color_discrete_sequence=[PBI_PALETTE[0]],
                title="Flow duration by interruption band",
                labels={
                    "flow_state_duration_minutes": "Flow duration (min)",
                    "interruption_band": "Interruptions",
                },
            )
            show(fig, title="Flow duration by interruption band")

    left, right = st.columns(2)
    with left:
        fig = px.histogram(
            df, x="flow_state_duration_minutes", nbins=25,
            color_discrete_sequence=[PBI_PALETTE[2]],
            labels={"flow_state_duration_minutes": "Flow duration (min)"},
            title="Flow duration distribution",
        )
        fig.update_traces(hovertemplate="Flow (min): %{x}<br>Sessions: %{y}<extra></extra>")
        show(fig, title="Flow duration distribution")

    with right:
        summ = kpis.summary_by(df, "task_type").reset_index()
        for _, row in summ.iterrows():
            if row["sessions"] < 30:
                warn_small_n(int(row["sessions"]), f"task_type = {row['task_type']}")
        fig = _clustered_column(
            summ, "task_type", "avg_flow",
            "Average flow minutes by task type",
            hover_extra=["sessions"],
        )
        show(fig, title="Average flow minutes by task type")


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
