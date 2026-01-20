import streamlit as st
import pandas as pd

# ------------------------------
# Try Plotly
# ------------------------------
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

# ------------------------------
# Page config
# ------------------------------
st.set_page_config(page_title="DSE Stock Analyzer", layout="wide")
st.title("📊 DSE Stock Analyzer")

# ------------------------------
# Upload
# ------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel file (multiple date sheets)",
    type=["xlsx"]
)

if not uploaded_file:
    st.info("Upload Excel file to begin.")
    st.stop()

# ------------------------------
# Load data
# ------------------------------
data = load_excel_data(uploaded_file)

# ------------------------------
# Timeframe
# ------------------------------
timeframe = st.radio("Timeframe", ["Daily", "Weekly"], horizontal=True)

if timeframe == "Weekly":
    data = data.groupby("Ticker", group_keys=False).apply(to_weekly)

# ------------------------------
# Indicators
# ------------------------------
data = data.groupby("Ticker", group_keys=False).apply(add_bollinger)
data = data.groupby("Ticker", group_keys=False).apply(add_minervini_stage2)

# =====================================================
# 📈 SINGLE STOCK VIEW
# =====================================================
st.subheader("📈 Stock Chart")

stock = st.selectbox("Select Stock", sorted(data["Ticker"].unique()))

stock_df = data[data["Ticker"] == stock].copy().tail(120)

if PLOTLY_AVAILABLE:
    fig = go.Figure()

    fig.add_candlestick(
        x=stock_df["Date"],
        open=stock_df["Open"],
        high=stock_df["High"],
        low=stock_df["Low"],
        close=stock_df["Close"],
        increasing=dict(line=dict(color="#26a69a"), fillcolor="#26a69a"),
        decreasing=dict(line=dict(color="#ef5350"), fillcolor="#ef5350"),
        whiskerwidth=0.6,
        name="Price"
    )

    fig.add_trace(go.Scatter(
        x=stock_df["Date"], y=stock_df["BB_UPPER"],
        line=dict(color="gray", dash="dot"), name="BB Upper"
    ))

    fig.add_trace(go.Scatter(
        x=stock_df["Date"], y=stock_df["BB_LOWER"],
        line=dict(color="gray", dash="dot"), name="BB Lower"
    ))

    fig.update_layout(
        height=520,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.line_chart(
        stock_df.set_index("Date")[["Close", "BB_UPPER", "BB_LOWER"]],
        use_container_width=True
    )

st.divider()

# =====================================================
# 📉 BOLLINGER BAND SCANNER
# =====================================================
st.subheader("📉 Bollinger Band Pullback Scanner")

st.markdown("""
**This table shows ONLY stocks that meet your conditions:**

• Crossed **below** Lower Bollinger Band (panic / shakeout)  
• OR **near touching** Lower Band (pullback zone)
""")

col1, col2, col3 = st.columns(3)

with col1:
    cond_cross = st.checkbox("Crossed Below Lower Band", value=True)

with col2:
    cond_near = st.checkbox("Near Lower Band", value=True)

with col3:
    threshold = st.slider("Near Band Threshold (%)", 0.5, 5.0, 1.0) / 100

# ------------------------------
# Build scanner safely
# ------------------------------
scan = data.copy()

scan["Prev_Close"] = scan.groupby("Ticker")["Close"].shift(1)
scan["Prev_BB"] = scan.groupby("Ticker")["BB_LOWER"].shift(1)

scan["Cross_Below"] = (
    (scan["Prev_Close"] > scan["Prev_BB"]) &
    (scan["Close"] < scan["BB_LOWER"])
)

scan["Near_Lower"] = (
    scan["Close"] <= scan["BB_LOWER"] * (1 + threshold)
)

scan["Signal"] = ""

if cond_cross:
    scan.loc[scan["Cross_Below"], "Signal"] += "Cross Below BB | "

if cond_near:
    scan.loc[scan["Near_Lower"], "Signal"] += "Near Lower BB | "

# Keep only signaled rows
scan = scan[scan["Signal"] != ""]
# --- Use ONLY latest candle per stock
scan = (
    data
    .sort_values("Date")
    .groupby("Ticker")
    .tail(1)
    .copy()
)


# ------------------------------
# Display table
# ------------------------------
if scan.empty:
    st.warning("No stocks met your conditions.")
else:
    st.success(f"{len(scan)} stocks matched your rules.")

    selection = st.dataframe(
        scan[["Ticker", "Date", "Close", "BB_LOWER", "Signal", "Stage2"]],
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun"
    )

    # ------------------------------
    # Click → chart
    # ------------------------------
    if selection and selection["selection"]["rows"]:
        idx = selection["selection"]["rows"][0]
        clicked = scan.iloc[idx]["Ticker"]

        st.subheader(f"📊 {clicked} – Signal Chart")

        dfc = data[data["Ticker"] == clicked].tail(120)

        if PLOTLY_AVAILABLE:
            fig2 = go.Figure()
            fig2.add_candlestick(
                x=dfc["Date"],
                open=dfc["Open"],
                high=dfc["High"],
                low=dfc["Low"],
                close=dfc["Close"],
                increasing=dict(line=dict(color="#26a69a")),
                decreasing=dict(line=dict(color="#ef5350")),
            )
            fig2.add_trace(go.Scatter(
                x=dfc["Date"], y=dfc["BB_LOWER"],
                line=dict(color="gray", dash="dot"),
                name="BB Lower"
            ))
            fig2.update_layout(
                height=450,
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig2, use_container_width=True)
