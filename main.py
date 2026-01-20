import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="DSE Bollinger Scanner")

BB_WINDOW = 20
BB_STD = 2

# =========================
# LOAD YOUR EXACT EXCEL FORMAT
# =========================
def load_excel_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)

    all_rows = []

    for sheet in xls.sheet_names:
        # Skip the stock name reference sheet
        if sheet.lower().startswith("stock"):
            continue

        df = pd.read_excel(xls, sheet_name=sheet, header=None)

        # Must have at least 7 columns
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
# BOLLINGER
# =========================
def add_bollinger(df, window=20, std_mult=2):
    df = df.sort_values("Date").copy()

    ma = df["Close"].rolling(window=window, min_periods=window).mean()
    std = df["Close"].rolling(window=window, min_periods=window).std(ddof=0)

    df["BB_MID"] = ma
    df["BB_UPPER"] = ma + std_mult * std
    df["BB_LOWER"] = ma - std_mult * std

    return df

# =========================
# UI
# =========================
st.title("📉 DSE Bollinger Band Scanner (Latest Day Only)")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is None:
    st.info("Please upload your Excel file")
    st.stop()

data = load_excel_data(uploaded_file)

# Add Bollinger per stock
data = data.groupby("Ticker", group_keys=False).apply(add_bollinger)

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.header("Scanner Condition")

mode = st.sidebar.selectbox(
    "Select condition",
    [
        "Close below Lower Band",
        "Close near Lower Band (within 1%)"
    ]
)

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
# SCAN
# =========================
if mode == "Close below Lower Band":
    scan = latest[latest["Close"] < latest["BB_LOWER"]]

elif mode == "Close near Lower Band (within 1%)":
    scan = latest[
        (latest["Close"] >= latest["BB_LOWER"]) &
        (latest["Close"] <= latest["BB_LOWER"] * 1.01)
    ]

# =========================
# TABLE
# =========================
st.subheader(f"📊 Stocks Matching Today: {len(scan)}")

if len(scan) == 0:
    st.warning("No stocks match today's condition.")
    st.stop()

show_cols = ["Ticker", "Date", "Close", "BB_LOWER", "BB_MID", "BB_UPPER"]
st.dataframe(scan[show_cols].reset_index(drop=True), use_container_width=True)

# =========================
# SELECT STOCK
# =========================
st.subheader("📈 View Chart")

selected = st.selectbox("Select Stock", scan["Ticker"].unique())

# =========================
# CHART
# =========================
stock_df = data[data["Ticker"] == selected].sort_values("Date")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=stock_df["Date"],
    open=stock_df["Open"],
    high=stock_df["High"],
    low=stock_df["Low"],
    close=stock_df["Close"],
    increasing_line_width=1.4,
    decreasing_line_width=1.4,
    name="Price"
))

fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_UPPER"], name="BB Upper"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_MID"], name="BB Mid"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_LOWER"], name="BB Lower"))

fig.update_layout(
    height=600,
    xaxis_rangeslider_visible=False,
    title=f"{selected} - Candlestick with Bollinger Bands"
)

st.plotly_chart(fig, use_container_width=True)
