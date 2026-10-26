"""
CogniStream - Power BI-style Plotly chart builders.

Every function takes the FILTERED DataFrame (or a summary calculated from it by
src/kpis.py) plus the active theme dictionary `t` (see dashboard/palette.py) and
returns a plotly Figure. Nothing here imports Streamlit, so the figures can be
tested without running the app.

Rules followed by all charts:
- numbers come from src/kpis.py (no second copy of the formulas),
- cognitive-load colours are always LOAD_COLORS and the order is Low, Medium, High,
- groups with fewer than kpis.SMALL_N sessions are drawn hollow / faded and the
  hover text says the sample is small,
- charts describe association only; none of them claim cause and effect.
"""
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import kpis
from dashboard.palette import (
    BAD,
    FONT_FAMILY,
    GOOD,
    LOAD_COLORS,
    NAVY,
    ORANGE,
    PRIMARY,
)

LOAD_ORDER = kpis.LOAD_ORDER
SMALL_N = kpis.SMALL_N
MIN_BOX_N = 10  # a box plot needs at least this many sessions in a group

PRETTY = {
    "productivity_score": "Productivity score",
    "coding_duration_minutes": "Coding (min)",
    "focus_duration_minutes": "Focus (min)",
    "flow_state_duration_minutes": "Flow (min)",
    "interruption_count": "Interruptions",
    "context_switch_count": "Context switches",
    "break_duration_minutes": "Break (min)",
    "meeting_minutes": "Meetings (min)",
    "tasks_completed": "Tasks completed",
    "bug_count": "Bugs",
    "task_type": "Task type",
    "work_mode": "Work mode",
    "experience_level": "Experience level",
    "task_complexity": "Task complexity",
    "cognitive_load_level": "Cognitive load",
    "interruption_band": "Interruptions per session",
}

# metric label shown to the user -> column name produced by kpis.summary_by
SUMMARY_METRICS = {
    "Avg productivity score": "avg_productivity",
    "Avg flow (min)": "avg_flow",
    "Avg focus (min)": "avg_focus",
    "Avg interruptions": "avg_interruptions",
    "Avg context switches": "avg_context_switches",
}

# summary column -> the raw column whose mean is drawn as the dotted reference line
METRIC_SOURCE = {
    "avg_productivity": "productivity_score",
    "avg_flow": "flow_state_duration_minutes",
    "avg_focus": "focus_duration_minutes",
    "avg_interruptions": "interruption_count",
    "avg_context_switches": "context_switch_count",
}

# numeric columns that can be compared across cognitive-load levels
BOX_METRICS = {
    "Interruptions": "interruption_count",
    "Context switches": "context_switch_count",
    "Focus (min)": "focus_duration_minutes",
    "Flow (min)": "flow_state_duration_minutes",
    "Productivity score": "productivity_score",
}


# ---------------------------------------------------------------- helpers
def _hover(t):
    return dict(
        bgcolor=t["card_bg"],
        bordercolor=t["card_border"],
        font=dict(family=FONT_FAMILY, size=12, color=t["text"]),
    )


def _finish(fig, t, height, **layout):
    """Common layout: height, hover label style, horizontal legend above the plot."""
    fig.update_layout(
        height=height,
        hoverlabel=_hover(t),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        **layout,
    )
    return fig


def _small_flag(n):
    return f"<br>⚠ only {int(n)} sessions: not reliable" if n < SMALL_N else ""


def empty_figure(message, t, height=240):
    """Placeholder shown instead of a chart when there is nothing to draw."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(size=13, color=t["muted"]),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _finish(fig, t, height, margin=dict(l=10, r=10, t=10, b=10))


def _text_on(z_abs, t, threshold=0.6):
    """Readable annotation colour on a heatmap cell."""
    return "#FFFFFF" if z_abs >= threshold else t["text"]


# ---------------------------------------------------------------- overview
def productivity_bullet(value, ref, t):
    """Bullet gauge for the average productivity score.

    value: average of the current filter.  ref: kpis.productivity_reference(all sessions).
    Grey-blue bands show the quartiles of ALL sessions; the dark tick is the all-session mean.
    """
    delta = round(value - ref["mean"], 1) if ref else 0
    steps = []
    if ref:
        edges = [ref["min"], ref["q1"], ref["median"], ref["q3"], ref["max"]]
        shades = ["#D6E8FA", "#B4D4F5", "#8FBCEE", "#6AA5E6"]
        steps = [dict(range=[edges[i], edges[i + 1]], color=shades[i]) for i in range(4)]
    mode = "number+gauge+delta" if delta else "number+gauge"
    fig = go.Figure(go.Indicator(
        mode=mode,
        value=value,
        number=dict(valueformat=".1f", font=dict(size=34, family=FONT_FAMILY)),
        delta=dict(reference=ref["mean"] if ref else value, valueformat="+.1f",
                   increasing=dict(color=GOOD), decreasing=dict(color=BAD)),
        title=dict(text="Avg productivity score<br>"
                        "<span style='font-size:11px'>bands = quartiles of all sessions</span>",
                   font=dict(size=13)),
        gauge=dict(
            shape="bullet",
            axis=dict(range=[0, 100], tickwidth=1),
            bar=dict(color=NAVY, thickness=0.45),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=steps,
            threshold=dict(line=dict(color=ORANGE, width=3), thickness=0.8,
                           value=ref["mean"] if ref else value),
        ),
    ))
    return _finish(fig, t, 190, margin=dict(l=20, r=30, t=50, b=20))


def load_donut(dist, t):
    """Donut of cognitive-load share. dist = kpis.load_distribution(df) (index Low/Medium/High)."""
    d = dist.reindex(LOAD_ORDER).fillna(0)
    total = int(d["sessions"].sum())
    fig = go.Figure(go.Pie(
        labels=list(d.index),
        values=d["sessions"].astype(int).tolist(),
        sort=False,
        direction="clockwise",
        hole=0.62,
        marker=dict(colors=[LOAD_COLORS[k] for k in d.index],
                    line=dict(color=t["card_bg"], width=2)),
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="<b>%{label} cognitive load</b><br>Sessions: %{value:,}"
                      "<br>Share: %{percent}<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{total:,}</b><br><span style='font-size:11px'>sessions</span>",
        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(size=22, color=t["text"]),
    )
    fig.update_layout(showlegend=False)
    return _finish(fig, t, 300, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)


def monthly_trend_chart(month, overall_mean, t):
    """Sessions (bars) + average productivity (line with markers) per month.

    month: DataFrame with columns month, sessions, avg_productivity, avg_flow, avg_interruptions.
    Months with fewer than SMALL_N sessions get hollow markers.
    """
    m = month.copy()
    m["month_start"] = pd.to_datetime(m["month"].astype(str) + "-01")
    small = m["sessions"] < SMALL_N
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # bars on the primary axis (drawn first), the line on the secondary axis (drawn on top)
    fig.add_trace(go.Bar(
        x=m["month_start"], y=m["sessions"], name="Sessions",
        marker=dict(color=PRIMARY, opacity=0.22),
        hovertemplate="<b>%{x|%b %Y}</b><br>Sessions: %{y:,}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=m["month_start"], y=m["avg_productivity"], name="Avg productivity",
        mode="lines+markers+text",
        text=[f"{v:.1f}" for v in m["avg_productivity"]],
        textposition="top center",
        textfont=dict(size=10, color=t["muted"]),
        line=dict(color=PRIMARY, width=2.5),
        marker=dict(size=9, color=[t["card_bg"] if s else NAVY for s in small],
                    line=dict(color=NAVY, width=2)),
        customdata=np.column_stack([
            m["sessions"], m["avg_flow"], m["avg_interruptions"],
            ["<br>⚠ small sample (< %d sessions)" % SMALL_N if s else "" for s in small],
        ]),
        hovertemplate=(
            "<b>%{x|%b %Y}</b><br>Avg productivity: %{y:.1f}"
            "<br>Sessions: %{customdata[0]}"
            "<br>Avg flow (min): %{customdata[1]:.1f}"
            "<br>Avg interruptions: %{customdata[2]:.2f}%{customdata[3]}<extra></extra>"
        ),
    ), secondary_y=True)
    if overall_mean is not None and len(m) > 1:
        fig.add_trace(go.Scatter(
            x=[m["month_start"].iloc[0], m["month_start"].iloc[-1]],
            y=[overall_mean, overall_mean],
            name="Mean of selected sessions", mode="lines",
            line=dict(color=ORANGE, width=1.5, dash="dot"),
            hovertemplate="Mean of selected sessions: %{y:.1f}<extra></extra>",
        ), secondary_y=True)
    fig.update_xaxes(tickformat="%b %Y", showgrid=False)
    fig.update_yaxes(title_text="Sessions", secondary_y=False, side="right",
                     showgrid=False, rangemode="tozero",
                     range=[0, max(1, float(m["sessions"].max())) * 3])
    fig.update_yaxes(title_text="Avg productivity score", secondary_y=True, side="left",
                     showgrid=True)
    return _finish(fig, t, 340, margin=dict(l=50, r=50, t=40, b=40), bargap=0.45)


def _lollipop_segments(cats, vals):
    xs, ys = [], []
    for c, v in zip(cats, vals):
        xs += [0, v, None]
        ys += [c, c, None]
    return xs, ys


def _add_lollipop(fig, cats, vals, ns, t, color, hover_label, row=None, col=None,
                  ref=None, fmt=".1f", name=None, show_ref_legend=False):
    """Draw horizontal stems + dots. Hollow dot = small sample. Optional dashed reference line."""
    cats, vals, ns = list(cats), [float(v) for v in vals], [int(n) for n in ns]
    kw = dict(row=row, col=col) if row else {}
    xs, ys = _lollipop_segments(cats, vals)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", line=dict(color=color, width=2.5),
        hoverinfo="skip", showlegend=False,
    ), **kw)
    flags = [_small_flag(n) for n in ns]
    fig.add_trace(go.Scatter(
        x=vals, y=cats, mode="markers+text", name=name or hover_label,
        text=[format(v, fmt) for v in vals], textposition="middle right",
        textfont=dict(size=11, color=t["text"]),
        marker=dict(size=14, color=[t["card_bg"] if n < SMALL_N else color for n in ns],
                    line=dict(color=color, width=2.5)),
        customdata=np.column_stack([ns, flags]) if cats else None,
        hovertemplate=f"<b>%{{y}}</b><br>{hover_label}: %{{x:{fmt}}}"
                      "<br>Sessions: %{customdata[0]:,}%{customdata[1]}<extra></extra>",
        showlegend=False,
    ), **kw)
    if ref is not None and cats:
        fig.add_trace(go.Scatter(
            x=[ref, ref], y=[cats[0], cats[-1]], mode="lines",
            line=dict(color=ORANGE, width=1.5, dash="dot"),
            name="Mean of selected sessions", showlegend=show_ref_legend,
            hovertemplate=f"Mean of selected sessions: {ref:{fmt}}<extra></extra>",
        ), **kw)


def developer_lollipop(rank, overall_mean, t, min_sessions):
    """Ranked lollipop of developers. rank = kpis.developer_ranking(...) (best first)."""
    cats = list(rank["developer_id"])
    fig = go.Figure()
    _add_lollipop(fig, cats, rank["avg_productivity"], rank["sessions"], t, PRIMARY,
                  "Avg productivity", ref=overall_mean, show_ref_legend=True)
    xmax = float(rank["avg_productivity"].max()) * 1.15
    fig.update_xaxes(title_text="Avg productivity score", range=[0, max(xmax, 10)])
    fig.update_yaxes(categoryorder="array", categoryarray=cats[::-1], showgrid=False,
                     title_text=f"Developer (≥ {min_sessions} sessions)")
    return _finish(fig, t, 90 + 30 * len(cats), margin=dict(l=70, r=40, t=40, b=40))


def developer_session_chart(dev_df, t):
    """One developer's sessions over time; dot colour = cognitive load of that session."""
    d = dev_df.sort_values(["session_date", "start_time"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["session_date"], y=d["productivity_score"], mode="lines",
        line=dict(color=t["grid"], width=1.5), hoverinfo="skip", showlegend=False,
    ))
    for lvl in LOAD_ORDER:
        s = d[d["cognitive_load_level"] == lvl]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["session_date"], y=s["productivity_score"], mode="markers", name=lvl,
            marker=dict(size=10, color=LOAD_COLORS[lvl], line=dict(color=t["card_bg"], width=1)),
            customdata=s[["task_type", "flow_state_duration_minutes", "interruption_count"]].to_numpy(),
            hovertemplate=("<b>%{x|%d %b %Y}</b><br>Productivity: %{y:.1f}"
                           f"<br>Cognitive load: {lvl}"
                           "<br>Task: %{customdata[0]}<br>Flow: %{customdata[1]:.1f} min"
                           "<br>Interruptions: %{customdata[2]}<extra></extra>"),
        ))
    fig.update_xaxes(title_text="Session date")
    fig.update_yaxes(title_text="Productivity score")
    fig.update_layout(legend_title_text="Cognitive load")
    return _finish(fig, t, 300, margin=dict(l=50, r=20, t=40, b=40))


# ---------------------------------------------------------------- scatter / bubble
def load_scatter(df, x_col, y_col, t, size_col="focus_duration_minutes", rho=None):
    """Bubble chart coloured by cognitive load. Bubble area ~ size_col. rho: Spearman to annotate."""
    size = df[size_col].clip(lower=1)
    sizeref = 2.0 * float(size.max()) / (24.0 ** 2)
    fig = go.Figure()
    for lvl in LOAD_ORDER:
        s = df[df["cognitive_load_level"] == lvl]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s[x_col], y=s[y_col], mode="markers", name=f"{lvl} (n={len(s)})",
            legendgroup=lvl,
            marker=dict(
                color=LOAD_COLORS[lvl], opacity=0.72,
                size=s[size_col].clip(lower=1), sizemode="area", sizeref=sizeref, sizemin=4,
                line=dict(color=t["card_bg"], width=0.6),
            ),
            customdata=s[["developer_id", "task_type", "task_complexity",
                          "interruption_count", size_col]].to_numpy(),
            hovertemplate=(
                f"<b>{lvl} cognitive load</b><br>"
                f"{PRETTY.get(x_col, x_col)}: %{{x:.1f}}<br>{PRETTY.get(y_col, y_col)}: %{{y:.1f}}"
                "<br>Developer: %{customdata[0]}<br>Task: %{customdata[1]} "
                "(%{customdata[2]} complexity)<br>Interruptions: %{customdata[3]}"
                f"<br>{PRETTY.get(size_col, size_col)}: %{{customdata[4]:.1f}}<extra></extra>"
            ),
        ))
    if rho is not None:
        fig.add_annotation(
            text=f"Spearman ρ = {rho:.2f}  (n = {len(df):,})<br>"
                 "<span style='font-size:10px'>association only, not cause and effect</span>",
            x=0.01, y=0.99, xref="paper", yref="paper", xanchor="left", yanchor="top",
            showarrow=False, align="left", font=dict(size=12, color=t["muted"]),
            bgcolor=t["card_bg"], bordercolor=t["card_border"], borderwidth=1, borderpad=6,
        )
    fig.update_xaxes(title_text=PRETTY.get(x_col, x_col), rangemode="tozero")
    fig.update_yaxes(title_text=PRETTY.get(y_col, y_col))
    fig.update_layout(legend_title_text="Cognitive load (click to hide / isolate)")
    return _finish(fig, t, 420, margin=dict(l=50, r=20, t=50, b=45))


# ---------------------------------------------------------------- dot plots
def dot_plot(summ, cat_col, value_col, hover_label, t, order=None, ref=None, color=PRIMARY,
             height=None, x_title=None, fmt=".1f"):
    """Lollipop/dot plot of one metric per category.

    summ: DataFrame with the category in `cat_col` (a column) plus `sessions` and `value_col`.
    order: fixed category order (ordinal fields). If None the categories are ranked high to low.
    """
    s = summ.dropna(subset=[value_col]).copy()
    if order:
        s[cat_col] = pd.Categorical(s[cat_col], categories=order, ordered=True)
        s = s.sort_values(cat_col)
    else:
        s = s.sort_values(value_col, ascending=False)
    cats = [str(c) for c in s[cat_col]]
    fig = go.Figure()
    _add_lollipop(fig, cats, s[value_col], s["sessions"], t, color, hover_label,
                  ref=ref, fmt=fmt, show_ref_legend=ref is not None)
    top = float(s[value_col].max()) if len(s) else 1.0
    fig.update_xaxes(title_text=x_title or hover_label, range=[0, max(top * 1.18, 1)])
    fig.update_yaxes(categoryorder="array", categoryarray=cats[::-1], showgrid=False,
                     title_text=PRETTY.get(cat_col, cat_col))
    h = height or max(220, 80 + 38 * len(cats))
    return _finish(fig, t, h, margin=dict(l=70, r=40, t=40, b=45))


def small_multiples(df, groups, metric_col, hover_label, t, ref=None, fmt=".1f"):
    """One dot-plot panel per grouping column, all panels on the same x scale.

    groups: list of (column, fixed_order_or_None) e.g. [("task_type", None), ("work_mode", [...])].
    metric_col: a column produced by kpis.summary_by (avg_productivity, avg_flow, ...).
    """
    tables = []
    for col, order in groups:
        summ = kpis.summary_by(df, col).reset_index()
        summ = summ.dropna(subset=[metric_col])
        if order:
            summ[col] = pd.Categorical(summ[col], categories=order, ordered=True)
            summ = summ.sort_values(col)
        else:
            summ = summ.sort_values(metric_col, ascending=False)
        tables.append((col, summ))
    if not tables or all(s.empty for _, s in tables):
        return empty_figure("No data for the current filter.", t)
    widths = [max(len(s), 2) for _, s in tables]
    fig = make_subplots(
        rows=1, cols=len(tables), column_widths=[w / sum(widths) for w in widths],
        subplot_titles=[PRETTY.get(c, c) for c, _ in tables], horizontal_spacing=0.14,
    )
    xmax = max(float(s[metric_col].max()) for _, s in tables if not s.empty)
    for i, (col, summ) in enumerate(tables, start=1):
        cats = [str(c) for c in summ[col]]
        _add_lollipop(fig, cats, summ[metric_col], summ["sessions"], t, PRIMARY, hover_label,
                      row=1, col=i, ref=ref, fmt=fmt, show_ref_legend=(i == 1 and ref is not None))
        fig.update_yaxes(categoryorder="array", categoryarray=cats[::-1], showgrid=False,
                         row=1, col=i)
        fig.update_xaxes(range=[0, max(xmax * 1.2, 1)], title_text=hover_label, row=1, col=i)
    fig.update_annotations(font=dict(size=12, color=t["text"]))
    longest = max(len(s) for _, s in tables)
    return _finish(fig, t, max(280, 120 + 36 * longest), margin=dict(l=70, r=30, t=70, b=50))


def band_comparison(bands, t):
    """Interruption-band comparison: avg flow and share of zero-flow sessions per band.

    bands = kpis.flow_by_band(df) (index = interruption band).
    """
    b = bands.reset_index().rename(columns={bands.index.name or "index": "interruption_band"})
    b["interruption_band"] = b["interruption_band"].astype(str)
    cats = list(b["interruption_band"])
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.08,
                        subplot_titles=["Avg flow (min)", "Sessions with zero flow (%)"])
    _add_lollipop(fig, cats, b["avg_flow"], b["sessions"], t, PRIMARY, "Avg flow (min)",
                  row=1, col=1)
    _add_lollipop(fig, cats, b["pct_zero_flow"], b["sessions"], t, ORANGE,
                  "Sessions with zero flow (%)", row=1, col=2)
    fig.update_yaxes(categoryorder="array", categoryarray=cats[::-1], showgrid=False,
                     title_text="Interruptions per session", row=1, col=1)
    fig.update_xaxes(range=[0, max(float(b["avg_flow"].max()) * 1.2, 1)], row=1, col=1)
    fig.update_xaxes(range=[0, max(float(b["pct_zero_flow"].max()) * 1.3, 5)], row=1, col=2)
    fig.update_annotations(font=dict(size=12, color=t["text"]))
    return _finish(fig, t, max(260, 110 + 44 * len(cats)), margin=dict(l=70, r=30, t=60, b=45))


# ---------------------------------------------------------------- heatmaps
def correlation_heatmap(corr, t, method="Spearman"):
    """Lower-triangle correlation heatmap. corr = kpis.correlation_matrix(df)."""
    cols = list(corr.columns)
    labels = [PRETTY.get(c, c) for c in cols]
    z = corr.to_numpy(dtype=float)
    masked = np.where(np.tril(np.ones_like(z, dtype=bool)), z, np.nan)
    fig = go.Figure(go.Heatmap(
        z=masked, x=labels, y=labels, zmin=-1, zmax=1, zmid=0, xgap=2, ygap=2,
        colorscale=[[0.0, ORANGE], [0.5, t["card_bg"]], [1.0, PRIMARY]],
        hoverongaps=False,
        hovertemplate="%{y} vs %{x}<br>" + method + " ρ = %{z:.2f}<extra></extra>",
        colorbar=dict(title=dict(text=f"{method} ρ", side="right"), thickness=12, len=0.8,
                      tickvals=[-1, -0.5, 0, 0.5, 1]),
    ))
    for i in range(len(cols)):
        for j in range(i + 1):
            v = z[i, j]
            if np.isnan(v):
                continue
            fig.add_annotation(x=labels[j], y=labels[i], text=f"{v:.2f}", showarrow=False,
                               font=dict(size=11, color=_text_on(abs(v), t, 0.62)))
    fig.update_xaxes(tickangle=-40, showgrid=False, side="bottom")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return _finish(fig, t, 520, margin=dict(l=110, r=20, t=20, b=110))


def load_complexity_heatmap(counts, percent, t):
    """Task complexity (rows) x cognitive load (columns), % of the row. From kpis.load_by_complexity."""
    xs = list(percent.columns)
    ys = list(percent.index)
    totals = counts.sum(axis=1)
    z = percent.to_numpy(dtype=float)
    zmasked = np.where((totals.to_numpy() > 0)[:, None], z, np.nan)
    fig = go.Figure(go.Heatmap(
        z=zmasked, x=xs, y=ys, zmin=0, zmax=100, xgap=3, ygap=3,
        colorscale=[[0.0, t["card_bg"]], [1.0, PRIMARY]],
        customdata=counts.to_numpy(),
        hoverongaps=False,
        hovertemplate=("Complexity: <b>%{y}</b><br>Cognitive load: <b>%{x}</b>"
                       "<br>Share of that complexity: %{z:.1f}%<br>Sessions: %{customdata}"
                       "<extra></extra>"),
        colorbar=dict(title=dict(text="% of row", side="right"), thickness=12, len=0.8),
    ))
    for i, cx in enumerate(ys):
        for j, lv in enumerate(xs):
            n = int(counts.iloc[i, j])
            if totals.iloc[i] == 0:
                txt = "—"
            else:
                warn = " ⚠" if n < SMALL_N else ""
                txt = f"{z[i, j]:.1f}%<br><span style='font-size:10px'>n={n}{warn}</span>"
            fig.add_annotation(x=lv, y=cx, text=txt, showarrow=False,
                               font=dict(size=12, color=_text_on(z[i, j] / 100.0, t, 0.5)))
    fig.update_xaxes(title_text="Cognitive load", showgrid=False, side="bottom",
                     categoryorder="array", categoryarray=xs)
    fig.update_yaxes(title_text="Task complexity", autorange="reversed", showgrid=False,
                     categoryorder="array", categoryarray=ys)
    return _finish(fig, t, 300, margin=dict(l=90, r=20, t=20, b=60))


# ---------------------------------------------------------------- cognitive-load charts
def load_box(df, metric_col, metric_label, t):
    """Box plot of a numeric column per cognitive-load level (+ mean marker).

    Groups with fewer than MIN_BOX_N sessions are left out. Returns (figure, excluded_levels).
    The figure is None when no group has enough sessions.
    """
    fig = go.Figure()
    excluded = []
    for lvl in LOAD_ORDER:
        vals = df.loc[df["cognitive_load_level"] == lvl, metric_col].dropna()
        if len(vals) < MIN_BOX_N:
            excluded.append((lvl, len(vals)))
            continue
        fig.add_trace(go.Box(
            y=vals, name=f"{lvl}<br>n={len(vals)}", marker=dict(color=LOAD_COLORS[lvl], size=4),
            line=dict(color=LOAD_COLORS[lvl], width=1.8), fillcolor="rgba(0,0,0,0)",
            boxmean=True, boxpoints="outliers", jitter=0.3,
        ))
    if not fig.data:
        return None, excluded
    fig.update_yaxes(title_text=metric_label)
    fig.update_xaxes(title_text="Cognitive load (dashed line = mean)")
    fig.update_layout(showlegend=False)
    return _finish(fig, t, 360, margin=dict(l=55, r=20, t=30, b=55), showlegend=False), excluded


def load_comparison(summ, t):
    """Four small bar charts comparing cognitive-load levels. summ = kpis.summary_by(df, 'cognitive_load_level')."""
    panels = [
        ("avg_focus", "Avg focus (min)"),
        ("avg_flow", "Avg flow (min)"),
        ("avg_interruptions", "Avg interruptions"),
        ("avg_productivity", "Avg productivity score"),
    ]
    s = summ.reindex(LOAD_ORDER)
    ns = s["sessions"].fillna(0).astype(int).tolist()
    ticks = [f"{lvl}<br>n={n}" for lvl, n in zip(LOAD_ORDER, ns)]
    fig = make_subplots(rows=1, cols=4, subplot_titles=[p[1] for p in panels],
                        horizontal_spacing=0.07)
    for i, (col, label) in enumerate(panels, start=1):
        vals = s[col].tolist()
        fig.add_trace(go.Bar(
            x=ticks, y=[None if pd.isna(v) else v for v in vals],
            marker=dict(color=[LOAD_COLORS[l] for l in LOAD_ORDER],
                        opacity=[0.45 if n < SMALL_N else 1.0 for n in ns]),
            text=["" if pd.isna(v) else f"{v:.1f}" for v in vals], textposition="outside",
            customdata=np.column_stack([ns, [_small_flag(n) for n in ns]]),
            hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.2f}}"
                          "<br>Sessions: %{customdata[0]:,}%{customdata[1]}<extra></extra>",
            showlegend=False, cliponaxis=False,
        ), row=1, col=i)
        top = max([v for v in vals if not pd.isna(v)] or [1])
        fig.update_yaxes(range=[0, top * 1.25], showgrid=True, row=1, col=i)
    fig.update_annotations(font=dict(size=12, color=t["text"]))
    return _finish(fig, t, 340, margin=dict(l=40, r=20, t=60, b=60), bargap=0.35)


# ---------------------------------------------------------------- flow
def flow_histogram(df, t, bin_size=5):
    """Flow-duration histogram, stacked by cognitive load, with a median marker."""
    col = "flow_state_duration_minutes"
    end = math.ceil(float(df[col].max()) / bin_size) * bin_size + bin_size
    fig = go.Figure()
    for lvl in LOAD_ORDER:
        s = df.loc[df["cognitive_load_level"] == lvl, col]
        if s.empty:
            continue
        fig.add_trace(go.Histogram(
            x=s, name=f"{lvl} (n={len(s)})", marker=dict(color=LOAD_COLORS[lvl]),
            xbins=dict(start=0, end=end, size=bin_size), legendgroup=lvl,
            hovertemplate=(f"<b>{lvl} cognitive load</b><br>Flow: %{{x}} min (bin)"
                           "<br>Sessions: %{y}<extra></extra>"),
        ))
    median = float(df[col].median())
    fig.add_vline(x=median, line=dict(color=t["muted"], width=1.5, dash="dash"),
                  annotation_text=f"Median {median:.1f} min", annotation_position="top right",
                  annotation_font=dict(size=11, color=t["muted"]))
    fig.update_xaxes(title_text=f"Flow duration (min, {bin_size}-min bins)")
    fig.update_yaxes(title_text="Sessions")
    fig.update_layout(barmode="stack", bargap=0.05, legend_title_text="Cognitive load")
    return _finish(fig, t, 340, margin=dict(l=50, r=20, t=50, b=45), barmode="stack")


def monthly_task_area(df, t):
    """Stacked area of session volume by task type over valid calendar months."""
    cols = ["session_date", "task_type", "session_id"]
    data = df[cols].dropna(subset=["session_date", "task_type"]).copy()
    if data.empty:
        return empty_figure("No valid date and task-type data for this selection", t, 280)
    data["month"] = pd.to_datetime(data["session_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    data = data.dropna(subset=["month"])
    grouped = data.groupby(["month", "task_type"], observed=True).size().rename("sessions").reset_index()
    pivot = grouped.pivot(index="month", columns="task_type", values="sessions").fillna(0).sort_index()
    fig = go.Figure()
    for category in pivot.columns:
        fig.add_trace(go.Scatter(
            x=pivot.index, y=pivot[category], name=str(category), mode="lines",
            stackgroup="sessions", line=dict(width=0.8),
            hovertemplate="<b>%{x|%b %Y}</b><br>Task type: " + str(category) +
                          "<br>Sessions: %{y:,}<extra></extra>",
        ))
    fig.update_xaxes(title_text="Month", tickformat="%b %Y", showgrid=False)
    fig.update_yaxes(title_text="Sessions", rangemode="tozero")
    return _finish(fig, t, 330, margin=dict(l=48, r=20, t=44, b=45), hovermode="x unified")


def task_work_treemap(df, t):
    """Hierarchical task type → work mode treemap sized by sessions and coloured by mean productivity."""
    data = df.dropna(subset=["task_type", "work_mode", "session_id", "productivity_score"])
    if data.empty:
        return empty_figure("No task type / work mode data for this selection", t, 300)
    grouped = data.groupby(["task_type", "work_mode"], observed=True).agg(
        sessions=("session_id", "count"), avg_productivity=("productivity_score", "mean")
    ).reset_index()
    grouped["avg_productivity"] = grouped["avg_productivity"].round(1)
    fig = px.treemap(
        grouped, path=[px.Constant("All sessions"), "task_type", "work_mode"],
        values="sessions", color="avg_productivity", color_continuous_scale="Blues",
        custom_data=["sessions", "avg_productivity"],
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{value} sessions",
        hovertemplate="<b>%{parent}</b><br>Work mode / group: %{label}"
                      "<br>Sessions: %{customdata[0]:,}"
                      "<br>Avg productivity: %{customdata[1]:.1f}<extra></extra>",
        marker=dict(line=dict(width=1, color=t["card_bg"])),
        pathbar=dict(visible=True),
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Avg productivity"))
    return _finish(fig, t, 360, margin=dict(l=8, r=8, t=35, b=8))


def developer_ribbon(df, t, top_n=6):
    """Bump/ribbon-style rank chart of developer average productivity by month.

    Developers are selected by total sessions; ranks are calculated only from available
    developer-month groups. Rank 1 is the highest mean productivity.
    """
    data = df.dropna(subset=["session_date", "developer_id", "productivity_score"]).copy()
    if data.empty:
        return empty_figure("No date, developer, and productivity data for this selection", t, 300)
    data["month"] = pd.to_datetime(data["session_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    data = data.dropna(subset=["month"])
    if data["month"].nunique() < 2:
        return empty_figure("At least two months are needed to compare ranking changes", t, 300)
    selected = data["developer_id"].value_counts().head(top_n).index
    data = data[data["developer_id"].isin(selected)]
    monthly = data.groupby(["month", "developer_id"], observed=True).agg(
        avg_productivity=("productivity_score", "mean"), sessions=("session_id", "count")
    ).reset_index()
    monthly["rank"] = monthly.groupby("month")["avg_productivity"].rank(method="min", ascending=False)
    fig = go.Figure()
    for dev, g in monthly.groupby("developer_id", observed=True):
        g = g.sort_values("month")
        fig.add_trace(go.Scatter(
            x=g["month"], y=g["rank"], mode="lines+markers", name=str(dev),
            line=dict(width=2), marker=dict(size=7),
            customdata=np.column_stack([g["avg_productivity"], g["sessions"]]),
            connectgaps=False,
            hovertemplate="<b>" + str(dev) + "</b><br>%{x|%b %Y}<br>Rank: %{y:.0f}"
                          "<br>Avg productivity: %{customdata[0]:.1f}"
                          "<br>Sessions: %{customdata[1]:.0f}<extra></extra>",
        ))
    fig.update_yaxes(title_text="Rank (1 = highest)", autorange="reversed", dtick=1)
    fig.update_xaxes(title_text="Month", tickformat="%b %Y", showgrid=False)
    return _finish(fig, t, 340, margin=dict(l=48, r=20, t=44, b=42), hovermode="x unified")


def category_pie(df, category_col, t, title=None):
    """Simple proportion pie for a categorical field, based only on filtered rows."""
    if category_col not in df.columns or df.empty:
        return empty_figure("No categorical data available for this selection", t, 280)
    counts = df[category_col].dropna().astype(str).value_counts().sort_values(ascending=False)
    if counts.empty:
        return empty_figure("No category values available for this selection", t, 280)
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(), values=counts.values.tolist(), sort=False,
        hole=0, textinfo="label+percent", textposition="inside",
        marker=dict(line=dict(color=t["card_bg"], width=2)),
        hovertemplate="<b>%{label}</b><br>Sessions: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    if title:
        fig.update_layout(title=dict(text=title, x=0, xanchor="left"))
    return _finish(fig, t, 320, margin=dict(l=12, r=12, t=42, b=12), showlegend=True)
