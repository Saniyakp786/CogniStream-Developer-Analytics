"""
Shared Power BI–style helpers for CogniStream charts and cards.

Used by app.py (CSS + theme toggle) and dashboard/views.py (Plotly).
"""
from contextlib import contextmanager

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from dashboard.palette import (  # noqa: F401  (re-exported for dashboard/views.py)
    BAD,
    FONT_FAMILY,
    GOOD,
    LOAD_COLORS,
    PBI_PALETTE,
    THEMES,
)


def _register_templates():
    """Register custom Plotly templates once (safe to call many times)."""
    for name, key in (("pbi_light", "Light"), ("pbi_dark", "Dark")):
        t = THEMES[key]
        pio.templates[name] = go.layout.Template(
            layout=go.Layout(
                font=dict(family=FONT_FAMILY, size=12, color=t["text"]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                colorway=PBI_PALETTE,
                title=dict(
                    font=dict(size=14, color=t["text"], family=FONT_FAMILY),
                    x=0, xanchor="left",
                ),
                legend=dict(
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11, color=t["muted"]),
                ),
                xaxis=dict(
                    showgrid=True, gridcolor=t["grid"], gridwidth=0.5,
                    zeroline=False, showline=False,
                    title_font=dict(size=11, color=t["muted"]),
                    tickfont=dict(size=11, color=t["muted"]),
                ),
                yaxis=dict(
                    showgrid=True, gridcolor=t["grid"], gridwidth=0.5,
                    zeroline=False, showline=False,
                    title_font=dict(size=11, color=t["muted"]),
                    tickfont=dict(size=11, color=t["muted"]),
                ),
                margin=dict(l=40, r=20, t=48, b=40),
                hoverlabel=dict(font=dict(family=FONT_FAMILY, size=12)),
            )
        )


_register_templates()


def get_theme_name():
    """Current theme from session state (default Light)."""
    return st.session_state.get("pbi_theme", "Light")


def get_theme():
    return THEMES[get_theme_name()]


def inject_css(theme_name=None):
    """Inject Power BI–like CSS for cards, tabs, sidebar filters, fonts."""
    name = theme_name or get_theme_name()
    t = THEMES[name]
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
        }}
        .stApp {{
            background-color: {t["bg"]};
            color: {t["text"]};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {t["sidebar_bg"]};
            border-right: 1px solid {t["card_border"]};
        }}
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] label {{
            color: {t["text"]};
        }}
        /* Power BI card tiles */
        .pbi-card {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 4px;
            box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.08), 0 0.3px 0.9px rgba(0,0,0,0.06);
            padding: 14px 16px 12px 16px;
            min-height: 92px;
            margin-bottom: 8px;
        }}
        .pbi-card-title {{
            font-size: 12px;
            color: {t["muted"]};
            margin: 0 0 6px 0;
            font-weight: 400;
            letter-spacing: 0.01em;
        }}
        .pbi-card-value {{
            font-size: 28px;
            font-weight: 600;
            color: {t["text"]};
            margin: 0;
            line-height: 1.15;
        }}
        .pbi-card-help {{
            font-size: 11px;
            color: {t["muted"]};
            margin-top: 4px;
        }}
        /* Chart / visual containers */
        .pbi-visual {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 4px;
            box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.08), 0 0.3px 0.9px rgba(0,0,0,0.06);
            padding: 8px 10px 4px 10px;
            margin-bottom: 12px;
        }}
        .pbi-visual-title {{
            font-size: 13px;
            font-weight: 600;
            color: {t["text"]};
            margin: 4px 0 2px 4px;
            text-align: left;
        }}
        /* Hide default Streamlit metric chrome when we use custom cards */
        div[data-testid="stMetric"] {{
            background: {t["card_bg"]};
            border: 1px solid {t["card_border"]};
            border-radius: 4px;
            box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.08);
            padding: 12px 14px;
        }}
        /* Tab bar ~ report pages */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            border-bottom: 1px solid {t["card_border"]};
            background: {t["card_bg"]};
        }}
        .stTabs [data-baseweb="tab"] {{
            font-family: {FONT_FAMILY};
            font-size: 13px;
            padding: 10px 18px;
            color: {t["muted"]};
        }}
        .stTabs [aria-selected="true"] {{
            color: {t["text"]} !important;
            border-bottom: 2px solid #118DFF !important;
            font-weight: 600;
        }}
        /* Filters pane header */
        .pbi-filters-header {{
            font-size: 14px;
            font-weight: 600;
            color: {t["text"]};
            margin-bottom: 4px;
        }}
        .pbi-session-count {{
            font-size: 12px;
            color: {t["muted"]};
        }}
        h1, h2, h3 {{
            font-family: {FONT_FAMILY} !important;
            color: {t["text"]} !important;
        }}
        .pbi-card-delta {{
            font-size: 12px;
            font-weight: 600;
            margin-top: 2px;
        }}
        .pbi-card-delta.good {{ color: {GOOD}; }}
        .pbi-card-delta.bad {{ color: {BAD}; }}
        .pbi-card-delta.neutral {{ color: {t["muted"]}; font-weight: 400; }}
        .pbi-visual-sub {{
            font-size: 11px;
            color: {t["muted"]};
            margin: 0 0 2px 4px;
        }}
        .pbi-filter-chips {{
            font-size: 12px;
            color: {t["muted"]};
            margin: 2px 0 10px 0;
        }}
        .pbi-filter-chips b {{ color: {t["text"]}; }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: {t["card_border"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_layout(fig, title=None):
    """Apply the active Power BI Plotly template + left-aligned small title."""
    t = get_theme()
    updates = dict(
        template=t["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color=t["text"]),
        title=dict(
            text=title or "",
            font=dict(size=14, color=t["text"], family=FONT_FAMILY),
            x=0, xanchor="left",
        ) if title else None,
    )
    # Drop None title so we don't wipe an existing one incorrectly
    if updates["title"] is None:
        del updates["title"]
    # Only set a default margin when the chart builder did not choose one
    if fig.layout.margin.l is None:
        updates["margin"] = dict(l=40, r=20, t=48 if title else 24, b=40)
    fig.update_layout(**updates)
    return fig


PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    # the lasso / box-select tools do nothing in this app, so they are not offered
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def show(fig, title=None, key=None):
    """Draw a Plotly chart full-width (works on old and new Streamlit).

    theme=None keeps OUR Plotly template (fonts, grid, colours) instead of Streamlit's.
    """
    apply_layout(fig, title=title)
    try:
        st.plotly_chart(fig, width="stretch", theme=None, key=key, config=PLOT_CONFIG)
    except TypeError:  # older Streamlit
        st.plotly_chart(fig, use_container_width=True, theme=None, key=key, config=PLOT_CONFIG)


@contextmanager
def visual(title, subtitle=None):
    """A Power BI-style visual tile: bordered box with a title (and optional grey subtitle)."""
    try:
        box = st.container(border=True)
    except TypeError:  # older Streamlit has no bordered container
        box = st.container()
    with box:
        st.markdown(f'<div class="pbi-visual-title">{title}</div>', unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<div class="pbi-visual-sub">{subtitle}</div>', unsafe_allow_html=True)
        yield


def show_df(data, **kwargs):
    """st.dataframe at full width on both old and new Streamlit."""
    try:
        st.dataframe(data, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(data, use_container_width=True, **kwargs)


def kpi_html(label, value, help_text="", context=None, tone="neutral"):
    """HTML for one Power BI card visual: grey title, large number, optional context line.

    context: short text such as "+2.2 vs all sessions". tone: good | bad | neutral (colours the context).
    """
    tip = f'<div class="pbi-card-help" title="{help_text}">ⓘ {help_text}</div>' if help_text else ""
    ctx = f'<div class="pbi-card-delta {tone}">{context}</div>' if context else ""
    return (
        f'<div class="pbi-card">'
        f'<div class="pbi-card-title">{label}</div>'
        f'<div class="pbi-card-value">{value}</div>'
        f'{ctx}{tip}</div>'
    )


def render_kpi_row(items):
    """
    items: list of (label, value, help_text) or (label, value, help_text, context, tone)
    Renders in equal columns.
    """
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.markdown(kpi_html(*item), unsafe_allow_html=True)


def delta_context(delta, higher_is_better=None, unit="", decimals=1, suffix="vs all sessions"):
    """Build (context_text, tone) for a KPI card from a difference to the all-session baseline.

    higher_is_better: True / False colours the change green / red; None keeps it grey.
    """
    if delta is None:
        return None, "neutral"
    if abs(delta) < 10 ** (-decimals) / 2:
        return f"= {suffix}", "neutral"
    arrow = "▲" if delta > 0 else "▼"
    tone = "neutral"
    if higher_is_better is not None:
        tone = "good" if (delta > 0) == higher_is_better else "bad"
    return f"{arrow} {delta:+.{decimals}f}{unit} {suffix}", tone


def style_summary_df(df):
    """Conditional colour scale on numeric summary tables (matrix look)."""
    try:
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            return df
        return df.style.background_gradient(cmap="Blues", subset=numeric.columns).format(precision=2)
    except Exception:
        return df


def warn_small_n(n, label, threshold=30):
    """Warn when a group has fewer than threshold sessions."""
    if n < threshold:
        st.warning(
            f"Only **{n}** sessions for **{label}** in the current filter "
            f"(below {threshold}). Averages for this group are not reliable."
        )


def warn_small_groups(summ, label, n_col="sessions", threshold=30):
    """One compact warning that lists every group below the threshold (instead of one per group)."""
    small = summ[summ[n_col] < threshold]
    if small.empty:
        return
    parts = ", ".join(f"{idx} (n={int(n)})" for idx, n in zip(small.index, small[n_col]))
    st.caption(
        f"⚠ Small samples in **{label}**: {parts}. Fewer than {threshold} sessions, "
        "so these averages are not reliable evidence (hollow dots / faded bars)."
    )
