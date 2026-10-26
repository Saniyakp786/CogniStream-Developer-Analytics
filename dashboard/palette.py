"""
Colour and theme tokens for CogniStream (no Streamlit import, so charts can use it in tests).

These values match powerbi/theme.json, so the Streamlit report and the
Power BI Desktop report use the same colours.
"""

# Brand colours requested for the report
PRIMARY = "#118DFF"   # primary blue
NAVY = "#12239E"      # navy
PURPLE = "#744EC2"    # purple
ORANGE = "#E66C37"    # orange

# Power BI default colour palette (in order) - same as powerbi/theme.json dataColors
PBI_PALETTE = [
    "#118DFF",  # primary blue
    "#12239E",  # navy
    "#744EC2",  # purple
    "#E66C37",  # orange
    "#E044A7",  # magenta
    "#6B007B",  # dark purple
    "#D9B300",  # gold
    "#D64550",  # red
]

# Semantic colours for cognitive load. Always use these for the load dimension.
LOAD_COLORS = {
    "Low": "#2BA84A",
    "Medium": "#F2C811",
    "High": "#D64550",
}
GOOD = LOAD_COLORS["Low"]
BAD = LOAD_COLORS["High"]

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
