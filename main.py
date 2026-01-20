import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="DSE Pro Stock Analyzer")

BB_WINDOW = 20
BB_STD = 2

# =========================
# LOAD YOUR EXACT EXCEL FORMAT
# =========================
def load_excel_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)

    all_rows = []

    for sheet in xls.sheet_names:
        if sheet.lower().startswith("stock"):
            continue

        df = pd.read_excel(xls, sheet_name=sheet, header=None)

        if df.shape[1] < 7:
            continue

        df = df.iloc[:, 0:7].copy()
        df.columns = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]

        df["Ticker"] = df["Ticker"].astype(str).str.strip()
        df["Open"] = pd.to_numeric(df["Open"], errors="coerce")
        df["High"] = pd.to_numeric(df["High"], errors="coerce")
        df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df = df[df["Ticker"].notna() & df["Close"].notna() & df["Date"].notna()]

        if not df.empty:
            all_rows.append(df)

    if not all_rows:
        st.error("No valid stock data found in Excel.")
        st.stop()

    full_df = pd.concat(all_rows, ignore_index=True)
    full_df = full_df.sort_values(["Ticker", "Date"])

    return full_df

# =========================
# INDICATORS
# =========================
def add_indicators(df):
    df = df.sort_values("Date").copy()

    # Bollinger
    ma = df["Close"].rolling(BB_WINDOW, min_periods=BB_WINDOW).mean()
    std = df["Close"].rolling(BB_WINDOW, min_periods=BB_WINDOW).std(ddof=0)

    df["BB_MID"] = ma
    df["BB_UPPER"] = ma + BB_STD * std
    df["BB_LOWER"] = ma - BB_STD * std

    # Moving averages for Stage 2
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA150"] = df["Close"].rolling(150).mean()
    df["MA200"] = df["Close"].rolling(200).mean()

    df["Stage2"] = (
        (df["Close"] > df["MA50"]) &
        (df["MA50"] > df["MA150"]) &
        (df["MA150"] > df["MA200"])
    )

    # Volume expansion
    df["VOL_AVG20"] = df["Volume"].rolling(20).mean()
    df["VolumeExpansion"] = df["Volume"] > df["VOL_AVG20"] * 1.5

    # Breakout: 20-day high
    df["HH20"] = df["Close"].rolling(20).max()
    df["Breakout"] = df["Close"] >= df["HH20"]

    return df

# =========================
# UI
# =========================
st.title("📊 DSE Professional Stock Analyzer")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is None:
    st.stop()

data = load_excel_data(uploaded_file)
data = data.groupby("Ticker", group_keys=False).apply(add_indicators)

# =========================
# USE ONLY LATEST DAY PER STOCK
# =========================
latest = (
    data
    .sort_values("Date")
    .groupby("Ticker")
    .tail(1)
    .copy()
)

# =========================
# ===== SCANNER AREA (BOTTOM LOGIC FIRST) ===
# =========================
st.markdown("---")
st.subheader("🔍 Smart Scanner (Latest Day Only)")

c1, c2, c3 = st.columns(3)

with c1:
    bb_mode = st.selectbox("Bollinger Condition", [
        "Any",
        "Below Lower Band",
        "Near Lower Band (1%)"
    ])

with c2:
    require_stage2 = st.checkbox("Require Stage 2")

with c3:
    require_breakout = st.checkbox("Require Breakout")

scan = latest.copy()

# ---- Apply BB filter ----
if bb_mode == "Below Lower Band":
    scan = scan[scan["Close"] < scan["BB_LOWER"]]
elif bb_mode == "Near Lower Band (1%)":
    scan = scan[
        (scan["Close"] >= scan["BB_LOWER"]) &
        (scan["Close"] <= scan["BB_LOWER"] * 1.01)
    ]

# ---- Apply Stage 2 ----
if require_stage2:
    scan = scan[scan["Stage2"] == True]

# ---- Apply Breakout ----
if require_breakout:
    scan = scan[scan["Breakout"] == True]

st.markdown(f"### 📋 Stocks Found: {len(scan)}")

if len(scan) == 0:
    st.warning("No stocks match your filter.")
    st.stop()

show_cols = ["Ticker", "Close", "Stage2", "VolumeExpansion", "Breakout"]
st.dataframe(scan[show_cols].sort_values("Ticker"), use_container_width=True)

# =========================
# SELECT FROM SCANNER
# =========================
selected_stock = st.selectbox(
    "📌 Select a stock from scanner to view chart",
    scan["Ticker"].unique()
)

# =========================
# ===== CHART AREA (TOP DISPLAYED HERE) =====
# =========================
st.markdown("---")
st.subheader("📈 Stock Chart")

stock_df = data[data["Ticker"] == selected_stock].sort_values("Date")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=stock_df["Date"],
    open=stock_df["Open"],
    high=stock_df["High"],
    low=stock_df["Low"],
    close=stock_df["Close"],
    increasing_line_color="#00ff88",
    decreasing_line_color="#ff4d4d",
    increasing_fillcolor="#00ff88",
    decreasing_fillcolor="#ff4d4d",
    line_width=1.4,
    name="Price"
))

# Bollinger
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_UPPER"], name="BB Upper"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_MID"], name="BB Mid"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_LOWER"], name="BB Lower"))

fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    title=f"{selected_stock} — Professional Chart",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

