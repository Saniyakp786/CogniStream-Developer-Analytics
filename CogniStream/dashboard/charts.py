"""
CogniStream - advanced Plotly figure builders (Power BI-inspired).

Every function takes already-prepared data (see dashboard/chart_data.py) and
returns a plotly Figure. No Streamlit calls here, so views.py stays in charge
of layout, filters and empty states.

Design rules used throughout
  * Cognitive load always uses LOAD_COLORS (green / amber / red) - nothing else does.
  * Each measure keeps its own colour on every page (METRIC_COLORS).
  * Hollow markers / hatched bars mean "fewer than SMALL_N sessions".
  * Hover text always shows the sample size (n).
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard import chart_data as cd
from dashboard.powerbi_style import (
    BAD,
    FONT_FAMILY,
    GOOD,
    LOAD_COLORS,
    METRIC_COLORS,
    NAVY,
    ORANGE,
    PRIMARY,
    PURPLE,
    apply_layout,
    get_theme,
    hex_to_rgba,
)

LOAD_ORDER = cd.LOAD_ORDER
BAND_ORDER = cd.BAND_ORDER
SMALL_N = cd.SMALL_N


# ---------- shared helpers ----------
def _base(fig, height=320, legend=False, margin=None):
    """Common look: theme template, hover label, horizontal legend above the plot."""
    t = get_theme()
    apply_layout(fig)
    fig.update_layout(
        height=height,
        showlegend=legend,
        margin=margin or dict(l=52, r=24, t=28, b=48),
        hoverlabel=dict(
            bgcolor=t["card_bg"], bordercolor=t["card_border"],
            font=dict(family=FONT_FAMILY, size=12, color=t["text"]),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=t["muted"]),
        ),
    )
    return fig


def _marker_fills(color, small, card_bg):
    """Solid fill normally; card-coloured (hollow look) for small samples."""
    return [card_bg if s else color for s in small]


def _padded_range(values, pad=0.15, lo=None, hi=None):
    v = [x for x in values if x is not None and not np.isnan(x)]
    if not v:
        return None
    a, b = min(v), max(v)
    span = (b - a) or max(abs(b), 1.0)
    a, b = a - span * pad, b + span * pad
    if lo is not None:
        a = max(lo, a)
    if hi is not None:
        b = min(hi, b)
    return [a, b]


# ---------- Overview ----------
def productivity_bullet(value, baseline):
    """
    Bullet-style gauge: blue bar = current average, navy tick = all-sessions average.
    The track is neutral grey on purpose - the score's formula is not provided, so
    no good/bad thresholds are invented.
    """
    t = get_theme()
    fig = go.Figure(go.Indicator(
        mode="number+gauge+delta",
        value=float(value),
        number=dict(font=dict(size=30, color=t["text"]), valueformat=".1f"),
        delta=dict(
            reference=float(baseline), valueformat=".1f",
            increasing=dict(color=GOOD), decreasing=dict(color=BAD),
            font=dict(size=14),
        ),
        title=dict(
            text="<b>Avg productivity</b><br><span style='font-size:11px'>tick = all sessions</span>",
            font=dict(size=13, color=t["text"]),
        ),
        gauge=dict(
            shape="bullet",
            axis=dict(range=[0, 100], tickfont=dict(size=10, color=t["muted"]), tickcolor=t["muted"]),
            bar=dict(color=PRIMARY, thickness=0.55),
            bgcolor=hex_to_rgba(t["muted"], 0.18),
            borderwidth=0,
            threshold=dict(line=dict(color=NAVY, width=3), thickness=0.9, value=float(baseline)),
        ),
        domain=dict(x=[0.22, 1.0], y=[0.2, 0.85]),
    ))
    return _base(fig, height=130, margin=dict(l=10, r=24, t=10, b=10))


def load_donut(dist):
    """
    Donut of cognitive-load share. `dist` = kpis.load_distribution(df)
    (index Low/Medium/High; columns sessions, percent). Total sits in the hole.
    """
    t = get_theme()
    d = dist[dist["sessions"] > 0]
    total = int(d["sessions"].sum())
    fig = go.Figure(go.Pie(
        labels=list(d.index), values=list(d["sessions"]),
        hole=0.64, sort=False, direction="clockwise",
        marker=dict(colors=[LOAD_COLORS[i] for i in d.index], line=dict(color=t["card_bg"], width=3)),
        textinfo="label+percent", textposition="outside",
        textfont=dict(size=12, color=t["text"]),
        hovertemplate="<b>%{label}</b><br>%{value:,} sessions<br>%{percent}<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<span style='font-size:22px'><b>{total:,}</b></span><br><span style='font-size:11px'>sessions</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(color=t["text"], family=FONT_FAMILY),
    )
    return _base(fig, height=310, margin=dict(l=24, r=24, t=24, b=24))


def monthly_trend(month, baseline_avg):
    """
    Monthly average productivity. Marker AREA = sessions in that month, hollow marker =
    a thin month (< SMALL_N sessions). Dotted line = average across the whole selection.
    `month` columns: month, sessions, avg_productivity, avg_flow, avg_interruptions.
    """
    t = get_theme()
    small = (month["sessions"] < SMALL_N).tolist()
    sizes = month["sessions"].clip(lower=1)
    fig = go.Figure(go.Scatter(
        x=month["month"], y=month["avg_productivity"],
        mode="lines+markers",
        line=dict(color=PRIMARY, width=2.5, shape="spline", smoothing=0.5),
        marker=dict(
            size=sizes, sizemode="area", sizeref=2.0 * float(sizes.max()) / (22.0 ** 2), sizemin=6,
            color=_marker_fills(PRIMARY, small, t["card_bg"]),
            line=dict(color=PRIMARY, width=2),
        ),
        customdata=month[["sessions", "avg_flow", "avg_interruptions"]].to_numpy(),
        hovertemplate=(
            "<b>%{x}</b><br>Avg productivity: %{y:.1f}"
            "<br>Sessions: %{customdata[0]}"
            "<br>Avg flow: %{customdata[1]:.1f} min"
            "<br>Avg interruptions: %{customdata[2]:.2f}<extra></extra>"
        ),
        name="Avg productivity",
    ))
    fig.add_hline(
        y=baseline_avg, line_dash="dot", line_color=t["muted"], line_width=1,
        annotation_text=f"Selection avg {baseline_avg:.1f}", annotation_position="bottom right",
        annotation_font=dict(size=10, color=t["muted"]),
    )
    fig.update_yaxes(title_text="Avg productivity", range=_padded_range(
        list(month["avg_productivity"]) + [baseline_avg], pad=0.35, lo=0, hi=100))
    fig.update_xaxes(title_text=None, type="category", showgrid=False)
    return _base(fig, height=310)


def developer_lollipop(ranked, baseline_avg):
    """
    Ranked horizontal lollipop of developers by average productivity.
    `ranked` is already filtered by the minimum-session rule and sorted best-first
    (or worst-first); the first row is drawn at the top.
    """
    t = get_theme()
    ids = ranked["developer_id"].tolist()
    vals = ranked["avg_productivity"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=vals, y=ids, orientation="h", width=0.07,
        marker=dict(color=hex_to_rgba(PRIMARY, 0.45)), hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=vals, y=ids, mode="markers+text",
        text=[f"{v:.1f}" for v in vals], textposition="middle right",
        textfont=dict(size=11, color=t["text"]),
        marker=dict(size=13, color=PRIMARY, line=dict(color=t["card_bg"], width=2)),
        customdata=ranked[["sessions", "avg_flow", "avg_interruptions"]].to_numpy(),
        hovertemplate=(
            "<b>%{y}</b><br>Avg productivity: %{x:.1f}"
            "<br>Sessions: %{customdata[0]}"
            "<br>Avg flow: %{customdata[1]:.1f} min"
            "<br>Avg interruptions: %{customdata[2]:.2f}<extra></extra>"
        ),
        showlegend=False,
    ))
    fig.add_vline(
        x=baseline_avg, line_dash="dot", line_color=t["muted"], line_width=1,
        annotation_text=f"Selection avg {baseline_avg:.1f}", annotation_position="top",
        annotation_font=dict(size=10, color=t["muted"]),
    )
    fig.update_xaxes(range=[0, max(vals + [baseline_avg]) * 1.18], title_text="Avg productivity score")
    fig.update_yaxes(autorange="reversed", title_text=None, showgrid=False)
    return _base(fig, height=max(280, 70 + 30 * len(ids)), margin=dict(l=70, r=24, t=34, b=44))


# ---------- Productivity ----------
def bubble_scatter(df, x, y, x_title, y_title, size_col=None, trend=True):
    """
    Scatter / bubble coloured by cognitive load (semantic colours).
    Bubble area = size_col (omit for equal dots). The navy line is the average of y inside
    10 equal-count bins of x, so the overall shape is visible through the overplotting.
    Click a legend entry to hide / isolate a load level.
    """
    t = get_theme()
    fig = go.Figure()
    if size_col:
        all_sizes = df[size_col].clip(lower=1)
        sizeref = 2.0 * float(all_sizes.max()) / (24.0 ** 2)
    for level in LOAD_ORDER:
        sub = df[df["cognitive_load_level"] == level]
        if sub.empty:
            continue
        marker = dict(color=LOAD_COLORS[level], opacity=0.72, line=dict(color=t["card_bg"], width=0.6))
        if size_col:
            marker.update(size=sub[size_col].clip(lower=1), sizemode="area", sizeref=sizeref, sizemin=4)
        else:
            marker.update(size=8)
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub[y], mode="markers", name=f"{level} load (n={len(sub)})",
            marker=marker,
            customdata=sub[["developer_id", "task_type", "interruption_count",
                            "focus_duration_minutes"]].to_numpy(),
            hovertemplate=(
                f"<b>{level} cognitive load</b><br>{x_title}: %{{x:.1f}}<br>{y_title}: %{{y:.1f}}"
                "<br>Developer: %{customdata[0]}<br>Task: %{customdata[1]}"
                "<br>Interruptions: %{customdata[2]}"
                "<br>Focus: %{customdata[3]:.1f} min<extra></extra>"
            ),
        ))
    if trend:
        b = cd.binned_trend(df, x, y)
        if b is not None:
            fig.add_trace(go.Scatter(
                x=b["bx"], y=b["by"], mode="lines+markers", name="Binned average",
                line=dict(color=NAVY, width=2.5), marker=dict(size=6, color=NAVY),
                hovertemplate=f"Around {x_title} %{{x:.0f}}<br>Avg {y_title}: %{{y:.1f}}<extra></extra>",
            ))
    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title, range=[0, 105])
    return _base(fig, height=380, legend=True, margin=dict(l=52, r=24, t=44, b=48))


def interruption_lollipop(bands, baseline_avg):
    """Vertical lollipop: average productivity per interruption band (hollow = small n)."""
    t = get_theme()
    small = bands["small"].tolist()
    vals = bands["avg_productivity"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bands["interruption_band"], y=vals, width=0.06,
        marker=dict(color=hex_to_rgba(METRIC_COLORS["productivity"], 0.45)),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=bands["interruption_band"], y=vals, mode="markers+text",
        text=[f"{v:.1f}" for v in vals], textposition="top center",
        textfont=dict(size=11, color=t["text"]),
        marker=dict(size=16, color=_marker_fills(PRIMARY, small, t["card_bg"]),
                    line=dict(color=PRIMARY, width=2.5)),
        customdata=bands[["sessions", "avg_flow"]].to_numpy(),
        hovertemplate=(
            "<b>%{x} interruptions</b><br>Avg productivity: %{y:.1f}"
            "<br>Sessions: %{customdata[0]}"
            "<br>Avg flow: %{customdata[1]:.1f} min<extra></extra>"
        ),
        showlegend=False,
    ))
    fig.add_hline(
        y=baseline_avg, line_dash="dot", line_color=t["muted"], line_width=1,
        annotation_text=f"Selection avg {baseline_avg:.1f}", annotation_position="bottom right",
        annotation_font=dict(size=10, color=t["muted"]),
    )
    fig.update_xaxes(title_text="Interruptions per session", type="category",
                     categoryorder="array", categoryarray=BAND_ORDER, showgrid=False)
    fig.update_yaxes(title_text="Avg productivity", range=[0, max(vals + [baseline_avg]) * 1.25])
    return _base(fig, height=380)


def _dot_rows(fig, frame, value_col, color, hover_name, row=None, col=None):
    """Lollipop rows on a horizontal category axis (used by the dot-plot builders)."""
    t = get_theme()
    labels = frame["label"].tolist()
    vals = frame[value_col].tolist()
    fig.add_trace(go.Bar(
        x=vals, y=labels, orientation="h", width=0.06,
        marker=dict(color=hex_to_rgba(color, 0.4)), hoverinfo="skip", showlegend=False,
    ), row=row, col=col)
    fig.add_trace(go.Scatter(
        x=vals, y=labels, mode="markers",
        marker=dict(size=13, color=_marker_fills(color, frame["small"].tolist(), t["card_bg"]),
                    line=dict(color=color, width=2.5)),
        customdata=frame[["sessions", "avg_focus", "avg_flow"]].to_numpy(),
        hovertemplate=(
            f"<b>%{{y}}</b><br>{hover_name}: %{{x:.1f}}"
            "<br>Sessions: %{customdata[0]}"
            "<br>Avg focus: %{customdata[1]:.1f} min"
            "<br>Avg flow: %{customdata[2]:.1f} min<extra></extra>"
        ),
        showlegend=False,
    ), row=row, col=col)


def productivity_small_multiples(panels, overall_avg):
    """
    2x2 small multiples: average productivity by task type / work mode / experience /
    complexity on ONE shared x-scale so the panels can be compared. Labels carry n.
    `panels` = list of (title, frame from chart_data.group_summary), max 4.
    """
    t = get_theme()
    titles = [p[0] for p in panels]
    fig = make_subplots(rows=2, cols=2, subplot_titles=titles,
                        horizontal_spacing=0.16, vertical_spacing=0.2)
    top = max(max(f["avg_productivity"]) for _, f in panels)
    for i, (_, frame) in enumerate(panels):
        r, c = divmod(i, 2)
        _dot_rows(fig, frame, "avg_productivity", METRIC_COLORS["productivity"],
                  "Avg productivity", row=r + 1, col=c + 1)
        fig.add_vline(x=overall_avg, line_dash="dot", line_color=t["muted"], line_width=1,
                      row=r + 1, col=c + 1)
        fig.update_yaxes(autorange="reversed", showgrid=False, row=r + 1, col=c + 1)
        fig.update_xaxes(range=[0, top * 1.12], row=r + 1, col=c + 1)
    fig.update_annotations(font=dict(size=12, color=t["text"], family=FONT_FAMILY))
    return _base(fig, height=560, margin=dict(l=130, r=24, t=44, b=40))


def correlation_heatmap(corr):
    """
    Lower-triangle Spearman heatmap. Diverging scale: orange = negative, blue = positive,
    centre = card colour so near-zero cells fade into the background.
    """
    t = get_theme()
    labels = list(corr.columns)
    z = corr.to_numpy(dtype=float)
    fig = go.Figure(go.Heatmap(
        z=z, x=labels, y=labels, zmin=-1, zmax=1, hoverongaps=False,
        colorscale=[[0.0, ORANGE], [0.5, t["card_bg"]], [1.0, PRIMARY]],
        xgap=2, ygap=2,
        colorbar=dict(title=dict(text="Spearman", font=dict(size=11, color=t["muted"])),
                      thickness=10, len=0.85, tickfont=dict(size=10, color=t["muted"])),
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Spearman: %{z:.2f}<extra></extra>",
    ))
    for i, yl in enumerate(labels):
        for j, xl in enumerate(labels):
            v = z[i, j]
            if np.isnan(v):
                continue
            fig.add_annotation(
                x=xl, y=yl, text=f"{v:.2f}", showarrow=False,
                font=dict(size=10, color="#FFFFFF" if abs(v) > 0.5 else t["text"]),
            )
    fig.update_xaxes(showgrid=False, tickangle=-40, side="bottom")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return _base(fig, height=520, margin=dict(l=100, r=24, t=16, b=100))


# ---------- Cognitive load ----------
def load_bars(dist):
    """Horizontal bars of sessions per load level, labelled with count and share."""
    t = get_theme()
    d = dist[dist["sessions"] > 0]
    levels = list(d.index)
    labels = [
        f"{int(s):,}  ({p:.1f}%)" + ("  \u26A0 small sample" if s < SMALL_N else "")
        for s, p in zip(d["sessions"], d["percent"])
    ]
    fig = go.Figure(go.Bar(
        x=list(d["sessions"]), y=levels, orientation="h",
        marker=dict(color=[LOAD_COLORS[l] for l in levels]),
        text=labels, textposition="outside", cliponaxis=False,
        textfont=dict(size=12, color=t["text"]),
        hovertemplate="<b>%{y} load</b><br>%{x:,} sessions<extra></extra>",
    ))
    fig.update_xaxes(range=[0, float(d["sessions"].max()) * 1.45], title_text="Sessions", showgrid=False)
    fig.update_yaxes(autorange="reversed", title_text=None, showgrid=False,
                     categoryorder="array", categoryarray=levels)
    fig.update_layout(bargap=0.35)
    return _base(fig, height=300, margin=dict(l=70, r=24, t=16, b=44))


def complexity_load_heatmap(pct, counts):
    """
    Task complexity (rows) x cognitive load (columns). Colour and the big number are the
    row percentage (each row sums to 100%); n is shown underneath so thin rows are obvious.
    """
    t = get_theme()
    z = pct.to_numpy(dtype=float)
    fig = go.Figure(go.Heatmap(
        z=z, x=list(pct.columns), y=list(pct.index), zmin=0, zmax=100, hoverongaps=False,
        colorscale=[[0.0, t["card_bg"]], [1.0, PRIMARY]], xgap=3, ygap=3,
        colorbar=dict(title=dict(text="% of row", font=dict(size=11, color=t["muted"])),
                      thickness=10, len=0.85, tickfont=dict(size=10, color=t["muted"])),
        customdata=counts.to_numpy(),
        hovertemplate=("Complexity: <b>%{y}</b><br>Load: <b>%{x}</b>"
                       "<br>%{z:.1f}% of this complexity level<br>Sessions: %{customdata}<extra></extra>"),
    ))
    for i, yl in enumerate(pct.index):
        for j, xl in enumerate(pct.columns):
            v = z[i, j]
            if np.isnan(v):
                continue
            fig.add_annotation(
                x=xl, y=yl, showarrow=False,
                text=f"<b>{v:.0f}%</b><br><span style='font-size:10px'>n={int(counts.iloc[i, j])}</span>",
                font=dict(size=13, color="#FFFFFF" if v > 55 else t["text"]),
            )
    fig.update_xaxes(title_text="Cognitive load level", showgrid=False, side="bottom")
    fig.update_yaxes(title_text="Task complexity", showgrid=False, autorange="reversed")
    return _base(fig, height=300, margin=dict(l=80, r=24, t=16, b=56))


def load_distribution(df, column, label, mode):
    """
    Distribution of one numeric measure per cognitive-load level.
    mode 'violin' = shape + inner box (all groups large enough);
    mode 'box'    = box + every point (at least one group is small).
    """
    names = []
    fig = go.Figure()
    for level in LOAD_ORDER:
        vals = df.loc[df["cognitive_load_level"] == level, column].dropna()
        if vals.empty:
            continue
        name = f"{level} (n={len(vals)})"
        names.append(name)
        color = LOAD_COLORS[level]
        if mode == "violin":
            fig.add_trace(go.Violin(
                y=vals, name=name, line_color=color, fillcolor=hex_to_rgba(color, 0.35),
                box_visible=True, meanline_visible=True, points=False, spanmode="hard",
                hoverinfo="y+name",
            ))
        else:
            fig.add_trace(go.Box(
                y=vals, name=name, line_color=color,
                fillcolor=hex_to_rgba(color, 0.3), boxpoints="all", jitter=0.4, pointpos=0,
                marker=dict(size=4, opacity=0.6, color=color), boxmean=True,
            ))
    fig.update_xaxes(categoryorder="array", categoryarray=names, showgrid=False,
                     title_text="Cognitive load level")
    fig.update_yaxes(title_text=label)
    return _base(fig, height=360, margin=dict(l=60, r=24, t=16, b=48))


def load_comparison(summary):
    """
    One mini bar chart per measure, each with its own y-scale (the units differ), bars
    coloured by load level. Hatched bars = fewer than SMALL_N sessions.
    `summary` = chart_data.load_summary(df).
    """
    t = get_theme()
    measures = [
        ("avg_productivity", "Productivity score"),
        ("avg_focus", "Focus (min)"),
        ("avg_flow", "Flow (min)"),
        ("avg_interruptions", "Interruptions"),
    ]
    fig = make_subplots(rows=1, cols=4, subplot_titles=[m[1] for m in measures],
                        horizontal_spacing=0.07)
    levels = summary["cognitive_load_level"].tolist()
    colors = [LOAD_COLORS[l] for l in levels]
    patterns = ["/" if s else "" for s in summary["small"]]
    for i, (col, title) in enumerate(measures, start=1):
        vals = summary[col].tolist()
        fig.add_trace(go.Bar(
            x=levels, y=vals,
            marker=dict(color=colors, pattern=dict(shape=patterns, fgcolor=t["card_bg"])),
            text=vals, texttemplate="%{y:.1f}", textposition="outside", cliponaxis=False,
            textfont=dict(size=11, color=t["text"]),
            customdata=summary[["sessions"]].to_numpy(),
            hovertemplate=(f"<b>%{{x}} load</b><br>{title}: %{{y:.1f}}"
                           "<br>Sessions: %{customdata[0]}<extra></extra>"),
            showlegend=False,
        ), row=1, col=i)
        fig.update_yaxes(range=[0, max(vals) * 1.28], showgrid=False, showticklabels=False,
                         row=1, col=i)
        fig.update_xaxes(categoryorder="array", categoryarray=LOAD_ORDER, showgrid=False,
                         row=1, col=i)
    fig.update_annotations(font=dict(size=12, color=t["text"], family=FONT_FAMILY))
    fig.update_layout(bargap=0.3)
    return _base(fig, height=320, margin=dict(l=24, r=24, t=44, b=40))


# ---------- Flow state ----------
def flow_histogram(df):
    """
    Flow-duration histogram stacked by cognitive load (shared bin edges so the stack is
    exact). Dashed line = median. Returns None when no session has any flow.
    """
    t = get_theme()
    max_flow = float(df["flow_state_duration_minutes"].max())
    if max_flow <= 0:
        return None
    size = max(max_flow / 25.0, 1e-6)
    fig = go.Figure()
    for level in LOAD_ORDER:
        sub = df.loc[df["cognitive_load_level"] == level, "flow_state_duration_minutes"]
        if sub.empty:
            continue
        fig.add_trace(go.Histogram(
            x=sub, name=f"{level} load", marker=dict(color=LOAD_COLORS[level]),
            xbins=dict(start=0, end=max_flow + size, size=size),
            hovertemplate=f"<b>{level} load</b><br>Flow %{{x}} min<br>Sessions: %{{y}}<extra></extra>",
        ))
    median = float(df["flow_state_duration_minutes"].median())
    fig.add_vline(
        x=median, line_dash="dash", line_color=t["text"], line_width=1.2,
        annotation_text=f"Median {median:.0f} min", annotation_position="top right",
        annotation_font=dict(size=10, color=t["text"]),
    )
    fig.update_layout(barmode="stack", bargap=0.04)
    fig.update_xaxes(title_text="Flow duration (min)")
    fig.update_yaxes(title_text="Sessions")
    return _base(fig, height=360, legend=True, margin=dict(l=52, r=24, t=44, b=48))


def flow_density(df):
    """
    Flow vs productivity as a 2-D density (sessions per cell) instead of dots: a different
    view from the bubble chart on the Productivity page, and it stays readable when many
    sessions overlap. Orange line = average productivity within 10 equal-count flow bins.
    """
    t = get_theme()
    fig = go.Figure(go.Histogram2d(
        x=df["flow_state_duration_minutes"], y=df["productivity_score"],
        nbinsx=20, nbinsy=20, xgap=1, ygap=1, histfunc="count",
        colorscale=[[0.0, hex_to_rgba(PRIMARY, 0.06)], [0.5, PRIMARY], [1.0, NAVY]],
        colorbar=dict(title=dict(text="Sessions", font=dict(size=11, color=t["muted"])),
                      thickness=10, len=0.85, tickfont=dict(size=10, color=t["muted"])),
        hovertemplate="Flow %{x} min<br>Productivity %{y}<br>Sessions: %{z}<extra></extra>",
    ))
    b = cd.binned_trend(df, "flow_state_duration_minutes", "productivity_score")
    if b is not None:
        fig.add_trace(go.Scatter(
            x=b["bx"], y=b["by"], mode="lines+markers", name="Binned average",
            line=dict(color=ORANGE, width=3), marker=dict(size=7, color=ORANGE,
                                                          line=dict(color="#FFFFFF", width=1)),
            hovertemplate="Around %{x:.0f} min flow<br>Avg productivity: %{y:.1f}<extra></extra>",
        ))
    fig.update_xaxes(title_text="Flow duration (min)", showgrid=False)
    fig.update_yaxes(title_text="Productivity score", showgrid=False)
    return _base(fig, height=380, legend=b is not None, margin=dict(l=52, r=24, t=34, b=48))


def flow_task_dotplot(summary, overall_avg):
    """Average flow minutes by task type, ranked high to low, n in the label."""
    t = get_theme()
    frame = summary.sort_values("avg_flow", ascending=False).reset_index(drop=True)
    fig = go.Figure()
    _dot_rows(fig, frame, "avg_flow", METRIC_COLORS["flow"], "Avg flow (min)")
    fig.add_vline(
        x=overall_avg, line_dash="dot", line_color=t["muted"], line_width=1,
        annotation_text=f"Selection avg {overall_avg:.1f}", annotation_position="top",
        annotation_font=dict(size=10, color=t["muted"]),
    )
    fig.update_xaxes(range=[0, float(frame["avg_flow"].max()) * 1.15], title_text="Avg flow (min)")
    fig.update_yaxes(autorange="reversed", showgrid=False, title_text=None)
    return _base(fig, height=max(300, 90 + 40 * len(frame)), margin=dict(l=170, r=24, t=34, b=44))


def band_combo(bands):
    """
    Interruption bands: bars = average flow minutes (left axis), line = average
    productivity (right axis). Hatched bars / hollow markers = fewer than SMALL_N sessions.
    """
    t = get_theme()
    small = bands["small"].tolist()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=bands["interruption_band"], y=bands["avg_flow"], name="Avg flow (min)",
        marker=dict(color=METRIC_COLORS["flow"],
                    pattern=dict(shape=["/" if s else "" for s in small], fgcolor=t["card_bg"])),
        text=bands["avg_flow"], texttemplate="%{y:.1f}", textposition="inside",
        textfont=dict(size=11, color="#FFFFFF"),
        customdata=bands[["sessions"]].to_numpy(),
        hovertemplate="<b>%{x} interruptions</b><br>Avg flow: %{y:.1f} min"
                      "<br>Sessions: %{customdata[0]}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=bands["interruption_band"], y=bands["avg_productivity"], name="Avg productivity",
        mode="lines+markers+text", text=bands["avg_productivity"], texttemplate="%{y:.1f}",
        textposition="top center", textfont=dict(size=11, color=PRIMARY),
        line=dict(color=PRIMARY, width=2.5),
        marker=dict(size=11, color=_marker_fills(PRIMARY, small, t["card_bg"]),
                    line=dict(color=PRIMARY, width=2.5)),
        customdata=bands[["sessions"]].to_numpy(),
        hovertemplate="<b>%{x} interruptions</b><br>Avg productivity: %{y:.1f}"
                      "<br>Sessions: %{customdata[0]}<extra></extra>",
    ), secondary_y=True)
    fig.update_xaxes(title_text="Interruptions per session", type="category",
                     categoryorder="array", categoryarray=BAND_ORDER, showgrid=False)
    fig.update_yaxes(title_text="Avg flow (min)", showgrid=True, secondary_y=False,
                     range=[0, float(bands["avg_flow"].max()) * 1.3])
    fig.update_yaxes(title_text="Avg productivity", showgrid=False, secondary_y=True,
                     range=[0, float(bands["avg_productivity"].max()) * 1.3])
    fig.update_layout(bargap=0.35)
    return _base(fig, height=380, legend=True, margin=dict(l=56, r=56, t=44, b=48))
