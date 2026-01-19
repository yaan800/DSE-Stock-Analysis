import streamlit as st
import pandas as pd

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except:
    PLOTLY_AVAILABLE = False

from utils import (
    load_excel_data,
    add_bollinger,
    add_minervini_stage2,
    to_weekly
)

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="DSE Stock Analyzer", layout="wide")
st.title("📊 DSE Stock Analyzer")

# -------------------------------------------------
# Upload
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel file (multiple date sheets)",
    type=["xlsx"]
)

if not uploaded_file:
    st.info("Upload Excel file to begin.")
    st.stop()

# -------------------------------------------------
# Load Data
# -------------------------------------------------
data = load_excel_data(uploaded_file)

# -------------------------------------------------
# Timeframe Toggle
# -------------------------------------------------
timeframe = st.radio(
    "Timeframe",
    ["Daily", "Weekly"],
    horizontal=True
)

if timeframe == "Weekly":
    data = (
        data
        .groupby("Ticker", group_keys=False)
        .apply(to_weekly)
    )

# -------------------------------------------------
# Indicators
# -------------------------------------------------
data = data.groupby("Ticker", group_keys=False).apply(add_bollinger)
data = data.groupby("Ticker", group_keys=False).apply(add_minervini_stage2)

# =================================================
# 📈 SINGLE STOCK VIEW
# =================================================
st.subheader("📈 Stock Chart")

stock = st.selectbox(
    "Select Stock",
    sorted(data["Ticker"].unique())
)

stock_df = data[data["Ticker"] == stock].copy()
stock_df = stock_df.tail(120)  # performance

# ---------------- Candlestick (Nice Version)
if PLOTLY_AVAILABLE:
    fig = go.Figure()

    fig.add_candlestick(
        x=stock_df["Date"],
        open=stock_df["Open"],
        high=stock_df["High"],
        low=stock_df["Low"],
        close=stock_df["Close"],
        increasing=dict(
            line=dict(color="#26a69a", width=1.5),
            fillcolor="#26a69a"
        ),
        decreasing=dict(
            line=dict(color="#ef5350", width=1.5),
            fillcolor="#ef5350"
        ),
        whiskerwidth=0.6,
        name="Price"
    )

    fig.add_trace(go.Scatter(
        x=stock_df["Date"],
        y=stock_df["BB_UPPER"],
        line=dict(color="gray", width=1, dash="dot"),
        name="BB Upper"
    ))

    fig.add_trace(go.Scatter(
        x=stock_df["Date"],
        y=stock_df["BB_LOWER"],
        line=dict(color="gray", width=1, dash="dot"),
        name="BB Lower"
    ))

    fig.update_layout(
        height=520,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.line_chart(
        stock_df.set_index("Date")[["Close", "BB_UPPER", "BB_LOWER"]],
        use_container_width=True
    )

st.divider()

# =================================================
# 📉 BOLLINGER BAND SCANNER (CLEAR & EXPLAINED)
# =================================================
st.subheader("📉 Bollinger Band Pullback Scanner")

st.markdown(
    """
**What this scanner shows:**

✔ Stocks that **EITHER**
- Crossed **below** Lower Bollinger Band *(panic / shakeout)*  
- OR are **near touching** Lower Band *(pullback zone)*  

✔ **Every row shown meets your selected conditions**
"""
)

col1, col2, col3 = st.columns(3)

with col1:
    cond_cross = st.checkbox("Crossed Below Lower Band", value=True)

with col2:
    cond_near = st.checkbox("Near Lower Band", value=True)

with col3:
    threshold = st.slider(
        "Near Band Threshold (%)",
        0.5, 5.0, 1.0
    ) / 100

scan = data.copy()

# ---- Previous values
scan["Prev_Close"] = scan.groupby("Ticker")["Close"].shift(1)
scan["Prev_BB"] = scan.groupby("Ticker")["BB_LOWER"].shift(1)

conditions = []
signals = []

if cond_cross:
    cross_cond = (
        (scan["Prev_Close"] > scan["Prev_BB"]) &
        (scan["Close"] < scan["BB_LOWER"])
    )
    conditions.append(cross_cond)
    signals.append(("Cross Below BB", cross_cond))

if cond_near:
    near_cond = scan["Close"] <= scan["BB_LOWER"] * (1 + threshold)
    conditions.append(near_cond)
    signals.append(("Near Lower BB", near_cond))

if conditions:
    final = conditions[0]
    for c in conditions[1:]:
        final |= c

    scan = scan[final]

# ---- Assign signal text
scan["Signal"] = "—"
for name, cond in signals:
    scan.loc[cond, "Signal"] = name

scan = (
    scan
    .sort_values("Date", ascending=False)
    .groupby("Ticker")
    .head(1)
)

# -------------------------------------------------
# Table
# -------------------------------------------------
if scan.empty:
    st.warning("No stocks met the selected conditions.")
else:
    st.success(f"{len(scan)} stocks met your criteria")

    selection = st.dataframe(
        scan[
            ["Ticker", "Date", "Close", "BB_LOWER", "Signal", "Stage2"]
        ],
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun"
    )

    # -------------------------------------------------
    # Click → Chart
    # -------------------------------------------------
    if selection and selection["selection"]["rows"]:
        idx = selection["selection"]["rows"][0]
        click_stock = scan.iloc[idx]["Ticker"]

        st.subheader(f"📊 {click_stock} – Signal Chart")

        df_click = data[data["Ticker"] == click_stock].tail(120)

        if PLOTLY_AVAILABLE:
            fig2 = go.Figure()
            fig2.add_candlestick(
                x=df_click["Date"],
                open=df_click["Open"],
                high=df_click["High"],
                low=df_click["Low"],
                close=df_click["Close"],
                increasing=dict(line=dict(color="#26a69a")),
                decreasing=dict(line=dict(color="#ef5350")),
            )
            fig2.add_trace(go.Scatter(
                x=df_click["Date"],
                y=df_click["BB_LOWER"],
                name="BB Lower",
                line=dict(color="gray", dash="dot")
            ))
            fig2.update_layout(
                height=450,
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig2, use_container_width=True)
