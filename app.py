
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(
    page_title="PJM Load — Dark Dashboard",
    page_icon="⚡",
    layout="wide"
)

@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0, engine="openpyxl")
    # Normalize time columns
    # Prefer 'interval_start_local' if present, fallback to first datetime-like column
    time_col_candidates = [c for c in df.columns if "interval" in c and "start" in c and "local" in c]
    if len(time_col_candidates) == 0:
        # try any column that looks like datetime
        for c in df.columns:
            try:
                pd.to_datetime(df[c])
                time_col_candidates.append(c)
            except Exception:
                pass
    time_col = time_col_candidates[0] if time_col_candidates else df.columns[0]
    df["timestamp"] = pd.to_datetime(df[time_col])
    df = df.sort_values("timestamp").reset_index(drop=True)
    # Numeric columns (zones)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Try to keep 'load' and other zone columns
    return df, numeric_cols

df, numeric_cols = load_data("data/PJM-ZONE-WISE-LOAD-DATA.xlsx")

# -------------- Header --------------
st.markdown("### ⚡ PJM Zone-wise Load — Dark Insight Dashboard")
st.markdown(
    "Simple, visual, and student-friendly. Explore electricity demand across PJM regions over time."
)

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    st.caption("Tip: Select a smaller time window for faster charts.")
    # Time range
    min_t, max_t = df["timestamp"].min(), df["timestamp"].max()
    default_start = max_t - pd.Timedelta(days=3)
    start, end = st.slider(
        "Time Range",
        min_value=min_t.to_pydatetime(),
        max_value=max_t.to_pydatetime(),
        value=(default_start.to_pydatetime(), max_t.to_pydatetime()),
        format="YYYY-MM-DD HH:mm",
    )
    # Zone selection
    # Keep only a subset by default: the 'pjm_rto' (total) plus a few regions if present
    default_zones = [c for c in ["pjm_rto", "pjm_eastern_region", "pjm_western_region", "pjm_southern_region", "dom"] if c in numeric_cols]
    selected_zones = st.multiselect(
        "Pick zones to visualize",
        options=numeric_cols,
        default=default_zones if default_zones else numeric_cols[:5],
    )
    # Resample
    resample_rule = st.selectbox(
        "Resample (average)",
        options=["5T", "15T", "30T", "1H", "6H", "1D"],
        index=3,
        help="Group data into bigger time buckets to smooth the lines."
    )

# Filter time
mask = (df["timestamp"] >= pd.Timestamp(start)) & (df["timestamp"] <= pd.Timestamp(end))
view = df.loc[mask].copy()

# Resample
view = view.set_index("timestamp").resample(resample_rule).mean(numeric_only=True).reset_index()

# -------------- KPI Cards --------------
kpi_cols = st.columns(4)
def kpi_card(col, label, value, suffix=""):
    col.markdown(
        f"""
        <div style="background:#0F172A;border:1px solid #1F2A44;padding:16px;border-radius:16px">
            <div style="opacity:.8;font-size:14px">{label}</div>
            <div style="font-size:28px;font-weight:700;margin-top:4px">{value}{suffix}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Compute KPIs for 'pjm_rto' if present, else use overall mean of selected zones
def series_for_kpis(df_view: pd.DataFrame) -> pd.Series:
    target = None
    if "pjm_rto" in df_view.columns:
        target = df_view["pjm_rto"]
    elif selected_zones:
        target = df_view[selected_zones].sum(axis=1)
    else:
        target = df_view[numeric_cols].sum(axis=1)
    return target

target = series_for_kpis(view)
if not target.empty:
    kpi_card(kpi_cols[0], "Peak Load", f"{target.max():,.0f}", " MW")
    kpi_card(kpi_cols[1], "Lowest Load", f"{target.min():,.0f}", " MW")
    kpi_card(kpi_cols[2], "Average Load", f"{target.mean():,.0f}", " MW")
    # Simple percent change from first to last
    pct = np.nan
    if len(target) >= 2 and target.iloc[0] != 0:
        pct = ((target.iloc[-1] - target.iloc[0]) / abs(target.iloc[0])) * 100
    kpi_card(kpi_cols[3], "Change (Start→End)", f"{pct:,.1f}%", "")

st.markdown("---")

# -------------- Main Charts --------------
left, right = st.columns([2, 1])

# Line chart for selected zones
with left:
    st.subheader("Trend Over Time")
    if selected_zones:
        melted = view.melt(id_vars="timestamp", value_vars=selected_zones, var_name="Zone", value_name="Load (MW)")
        fig = px.line(
            melted,
            x="timestamp",
            y="Load (MW)",
            color="Zone",
            markers=False,
            title="Electricity Load by Zone",
        )
        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=40, b=10),
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pick at least one zone in the sidebar.")

# Top/Bottom zones (by average within window)
with right:
    st.subheader("Top & Bottom Zones (Avg)")
    zone_means = view[numeric_cols].mean(numeric_only=True).sort_values(ascending=False)
    top_n = st.slider("How many to show", 3, 10, 5)
    top_df = zone_means.head(top_n).reset_index()
    top_df.columns = ["Zone", "Avg Load (MW)"]
    bottom_df = zone_means.tail(top_n).reset_index()
    bottom_df.columns = ["Zone", "Avg Load (MW)"]
    fig_bar_top = px.bar(top_df, x="Avg Load (MW)", y="Zone", orientation="h", title="Top Zones")
    fig_bar_top.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_bar_top, use_container_width=True)
    fig_bar_bottom = px.bar(bottom_df.sort_values("Avg Load (MW)"), x="Avg Load (MW)", y="Zone", orientation="h", title="Bottom Zones")
    fig_bar_bottom.update_layout(template="plotly_dark", height=280, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_bar_bottom, use_container_width=True)

st.markdown("---")

# -------------- Daily patterns --------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Daily Average (Which day is highest?)")
    day = view.set_index("timestamp").resample("1D").mean(numeric_only=True).reset_index()
    if "pjm_rto" in day.columns:
        ycol = "pjm_rto"
    else:
        ycol = selected_zones[0] if selected_zones else numeric_cols[0]
    fig_day = px.bar(day, x="timestamp", y=ycol, title=f"Daily Average Load — {ycol}")
    fig_day.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_day, use_container_width=True)

with col2:
    st.subheader("Hourly Pattern (Typical day shape)")
    # Compute average by clock hour
    tmp = view.copy()
    tmp["hour"] = pd.to_datetime(tmp["timestamp"]).dt.hour
    if "pjm_rto" in tmp.columns:
        ycol2 = "pjm_rto"
    else:
        ycol2 = selected_zones[0] if selected_zones else numeric_cols[0]
    hourly = tmp.groupby("hour")[ycol2].mean().reset_index()
    fig_hour = px.line(hourly, x="hour", y=ycol2, markers=True, title=f"Average by Hour — {ycol2}")
    fig_hour.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_hour, use_container_width=True)

# -------------- Simple explanations (student-friendly) --------------
with st.expander("Open: What am I looking at? (for students)", expanded=False):
    st.markdown(
        """
**Electricity load** is how much power people are using right now.  
- **Line chart:** how load changes with time.
- **Top/Bottom:** which zones use more/less power on average.
- **Daily average:** which days are heavier.
- **Hourly pattern:** what a typical day looks like (e.g., mornings vs evenings).

**Tips to explore:**
- Change the time range to focus on a specific week.
- Select different zones to compare them.
- Use the *Resample* option to smooth out the line (e.g., 1 hour or 1 day).
"""
    )

st.caption("Built with ❤️ using Streamlit + Plotly")
