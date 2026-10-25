"""
CogniStream - Streamlit app (Power BI–style report layout).

Run from the project root:
    streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import kpis  # noqa: E402
from dashboard import views  # noqa: E402
from dashboard.powerbi_style import inject_css  # noqa: E402

st.set_page_config(
    page_title="CogniStream | Power BI–style Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme toggle (Light = Power BI Service, Dark = dark report) ----------
if "pbi_theme" not in st.session_state:
    st.session_state.pbi_theme = "Light"

st.sidebar.markdown("### CogniStream")
st.sidebar.caption("Developer Flow-State & Cognitive Load Analytics")
theme = st.sidebar.radio(
    "Theme",
    ["Light", "Dark"],
    index=0 if st.session_state.pbi_theme == "Light" else 1,
    horizontal=True,
    help="Light ≈ Power BI Service canvas; Dark ≈ dark report theme.",
)
st.session_state.pbi_theme = theme
inject_css(theme)


@st.cache_data(show_spinner="Loading cleaned dataset...")
def get_data():
    return kpis.load_clean()


try:
    df_all = get_data()
except FileNotFoundError as err:
    st.error(f"{err}")
    st.stop()
except Exception as err:  # noqa: BLE001
    st.error(f"Could not load the dataset: {err}")
    st.stop()

# ---------- Filters pane (Power BI–like slicers) ----------
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="pbi-filters-header">Filters</div>', unsafe_allow_html=True)
st.sidebar.caption("Empty selection = all values (like Power BI slicers).")

# Defaults stored so Reset can clear them
FILTER_KEYS = {
    "f_experience": [],
    "f_work_mode": [],
    "f_task_type": [],
    "f_complexity": [],
    "f_dates": None,  # set after we know min/max
}

dmin, dmax = df_all["session_date"].min().date(), df_all["session_date"].max().date()
if "f_dates" not in st.session_state or st.session_state.f_dates is None:
    st.session_state.f_dates = (dmin, dmax)
for key, default in FILTER_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.sidebar.button("Reset filters", use_container_width=True):
    st.session_state.f_experience = []
    st.session_state.f_work_mode = []
    st.session_state.f_task_type = []
    st.session_state.f_complexity = []
    st.session_state.f_dates = (dmin, dmax)
    st.rerun()

experience = st.sidebar.multiselect(
    "Experience level",
    options=sorted(df_all["experience_level"].unique()),
    key="f_experience",
)
work_mode = st.sidebar.multiselect(
    "Work mode",
    options=sorted(df_all["work_mode"].unique()),
    key="f_work_mode",
)
task_type = st.sidebar.multiselect(
    "Task type",
    options=sorted(df_all["task_type"].unique()),
    key="f_task_type",
)
complexity = st.sidebar.multiselect(
    "Task complexity",
    options=["Low", "Medium", "High"],
    key="f_complexity",
)
dates = st.sidebar.date_input(
    "Date range",
    min_value=dmin,
    max_value=dmax,
    key="f_dates",
)
date_range = tuple(dates) if isinstance(dates, (tuple, list)) and len(dates) == 2 else None
if date_range is None:
    st.sidebar.info("Pick both a start and an end date.")

filtered = kpis.apply_filters(df_all, experience, work_mode, task_type, complexity, date_range)
st.sidebar.markdown(
    f'<p class="pbi-session-count">Showing <b>{len(filtered):,}</b> of '
    f'<b>{len(df_all):,}</b> sessions</p>',
    unsafe_allow_html=True,
)

# ---------- Report page tabs (like Power BI report pages) ----------
PAGES = [
    ("Overview", views.page_overview),
    ("Productivity Analysis", views.page_productivity),
    ("Cognitive Load Analysis", views.page_cognitive),
    ("Flow-State Analysis", views.page_flow),
    ("AI Assistant", views.page_ai_assistant),
    ("Reports", views.page_reports),
]

st.markdown("## CogniStream Report")
tabs = st.tabs([name for name, _ in PAGES])

if filtered.empty:
    st.warning("No sessions match these filters. Use **Reset filters** in the sidebar.")
else:
    for tab, (name, fn) in zip(tabs, PAGES):
        with tab:
            fn(filtered)
