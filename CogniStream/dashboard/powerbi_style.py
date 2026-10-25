"""
Shared Power BI-style helpers for CogniStream charts and cards.

Used by app.py (CSS + theme toggle), dashboard/views.py (pages) and
dashboard/charts.py (Plotly figure builders).
"""
from contextlib import contextmanager
from html import escape

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------- Colour system ----------
PRIMARY = "#118DFF"   # Power BI blue
NAVY = "#12239E"
PURPLE = "#744EC2"
ORANGE = "#E66C37"
NEUTRAL_GREY = "#8A8886"

# Semantic colours. Green/amber/red are RESERVED for cognitive load
# (Low / Medium / High) and for good/bad deltas. Never use them as decoration.
GOOD = "#2BA84A"
BAD = "#D64550"
LOAD_COLORS = {
    "Low": GOOD,
    "Medium": "#F2C811",
    "High": BAD,
}

# One colour per measure, used the same way on every page.
METRIC_COLORS = {
    "productivity": PRIMARY,
    "focus": NAVY,
    "flow": PURPLE,
    "interruptions": ORANGE,
}

# Power BI default colour palette (in order) - matches powerbi/theme.json
PBI_PALETTE = [
    "#118DFF",  # blue
    "#12239E",  # dark blue
    "#E66C37",  # orange
    "#6B007B",  # purple
    "#E044A7",  # magenta
    "#744EC2",  # violet
    "#D9B300",  # gold
    "#D64550",  # red
]

FONT_FAMILY = "Segoe UI, Arial, sans-serif"

# Light = Power BI Service canvas; Dark = dark report
THEMES = {
    "Light": {
        "bg": "#F3F2F1",
        "card_bg": "#FFFFFF",
        "card_border": "#E1DFDD",
        "text": "#252423",
        "muted": "#605E5C",
        "grid": "#E1DFDD",
        "plotly_template": "pbi_light",
        "sidebar_bg": "#F3F2F1",
    },
    "Dark": {
        "bg": "#0E1117",
        "card_bg": "#1A1F2B",
        "card_border": "#2A3142",
        "text": "#E6EAF2",
        "muted": "#A0A8B8",
        "grid": "#2A3142",
        "plotly_template": "pbi_dark",
        "sidebar_bg": "#161B22",
    },
}

# Modebar: keep only the useful buttons, export PNG at 2x.
PLOT_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def hex_to_rgba(hex_color, alpha=1.0):
    """'#118DFF', 0.3 -> 'rgba(17,141,255,0.3)' (for soft fills and stems)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


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
    """Inject Power BI-like CSS for cards, tabs, sidebar filters, fonts."""
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
            min-height: 112px;
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
        .pbi-card-delta {{
            font-size: 12px;
            font-weight: 600;
            margin-top: 4px;
        }}
        .pbi-delta-good {{ color: {GOOD}; }}
        .pbi-delta-bad {{ color: {BAD}; }}
        .pbi-delta-neutral {{ color: {t["muted"]}; font-weight: 400; }}
        .pbi-card-help {{
            font-size: 11px;
            color: {t["muted"]};
            margin-top: 4px;
        }}
        /* Chart / visual headers (the chart sits inside st.container(border=True)) */
        .pbi-visual-title {{
            font-size: 13px;
            font-weight: 600;
            color: {t["text"]};
            margin: 2px 0 0 2px;
            text-align: left;
        }}
        .pbi-visual-sub {{
            font-size: 11px;
            color: {t["muted"]};
            margin: 0 0 2px 2px;
        }}
        .pbi-section {{
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {t["muted"]};
            margin: 18px 0 6px 2px;
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
            border-bottom: 2px solid {PRIMARY} !important;
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_layout(fig, title=None, margin=True):
    """
    Apply the active Power BI Plotly template + left-aligned small title.
    margin=False keeps whatever margin the chart builder already set.
    """
    t = get_theme()
    updates = dict(
        template=t["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color=t["text"]),
    )
    if margin:
        updates["margin"] = dict(l=40, r=20, t=48 if title else 24, b=40)
    if title:
        updates["title"] = dict(
            text=title,
            font=dict(size=14, color=t["text"], family=FONT_FAMILY),
            x=0, xanchor="left",
        )
    fig.update_layout(**updates)
    return fig


def show(fig, title=None, key=None):
    """
    Draw a Plotly chart full-width (works on old and new Streamlit).
    theme=None so OUR template is used instead of Streamlit's own chart theme.
    """
    apply_layout(fig, title=title, margin=False)
    extra = {"key": key} if key else {}
    try:
        st.plotly_chart(fig, width="stretch", theme=None, config=PLOT_CONFIG, **extra)
    except TypeError:  # older Streamlit
        st.plotly_chart(fig, use_container_width=True, theme=None, config=PLOT_CONFIG, **extra)


def show_table(data):
    """st.dataframe full-width on old and new Streamlit."""
    try:
        st.dataframe(data, width="stretch")
    except TypeError:
        st.dataframe(data, use_container_width=True)


# ---------- Cards and containers ----------
def kpi_html(label, value, help_text="", delta=None, tone="neutral", accent=None):
    """
    HTML for one Power BI card visual: small grey title, large number,
    optional context line (delta) and a coloured accent bar on the left.
    """
    accent = accent or PRIMARY
    tip = (
        f'<div class="pbi-card-help" title="{escape(help_text, quote=True)}">'
        f'\u24D8 {escape(help_text)}</div>'
        if help_text else ""
    )
    delta_html = (
        f'<div class="pbi-card-delta pbi-delta-{tone}">{escape(delta)}</div>' if delta else ""
    )
    return (
        f'<div class="pbi-card" style="border-left:4px solid {accent};">'
        f'<div class="pbi-card-title">{escape(label)}</div>'
        f'<div class="pbi-card-value">{value}</div>'
        f'{delta_html}{tip}</div>'
    )


def render_kpi_row(items):
    """
    items: list of tuples  (label, value, help_text[, delta, tone, accent])
    Renders in equal columns.
    """
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.markdown(kpi_html(*item), unsafe_allow_html=True)


@contextmanager
def visual(title, subtitle=None):
    """A bordered 'visual' tile with a title (+ optional subtitle) above the chart."""
    try:
        box = st.container(border=True)
    except TypeError:  # Streamlit < 1.29 has no bordered containers
        box = st.container()
    with box:
        html = f'<div class="pbi-visual-title">{escape(title)}</div>'
        if subtitle:
            html += f'<div class="pbi-visual-sub">{escape(subtitle)}</div>'
        st.markdown(html, unsafe_allow_html=True)
        yield


def section(title):
    """Small uppercase section label between rows of visuals."""
    st.markdown(f'<div class="pbi-section">{escape(title)}</div>', unsafe_allow_html=True)


def empty_state(message):
    st.info(message)


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


def small_sample_note(any_small, threshold=30):
    """One consolidated caption instead of a warning per group."""
    if any_small:
        st.caption(
            f"Hollow markers / hatched bars = groups with fewer than {threshold} sessions. "
            "Treat those averages as indicative only."
        )
