import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide", page_title="DSE Bollinger Scanner Pro")

BB_WINDOW = 20
BB_STD = 2


# =========================
# LOAD EXCEL (ROBUST)
# =========================
@st.cache_data
def load_excel(file):
    xls = pd.ExcelFile(file)
    all_data = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)

        if df.shape[1] < 7:
            continue

        df = df.iloc[:, :7]
        df.columns = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]

        df["Ticker"] = df["Ticker"].astype(str).str.strip()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["Date", "Close"], inplace=True)
        df.sort_values("Date", inplace=True)

        all_data.append(df)

    return pd.concat(all_data, ignore_index=True)


# =========================
# BOLLINGER BANDS
# =========================
def add_bollinger(df):
    df = df.copy()
    df["BB_MID"] = df["Close"].rolling(BB_WINDOW).mean()
    df["BB_STD"] = df["Close"].rolling(BB_WINDOW).std()
    df["BB_UPPER"] = df["BB_MID"] + BB_STD * df["BB_STD"]
    df["BB_LOWER"] = df["BB_MID"] - BB_STD * df["BB_STD"]
    return df


# =========================
# SCANNER (LATEST DAY ONLY)
# =========================
def bollinger_scanner(data, mode):
    rows = []

    for ticker, df in data.groupby("Ticker"):
        if len(df) < BB_WINDOW:
            continue

        df = add_bollinger(df)
        latest = df.iloc[-1]

        low = latest["Low"]
        close = latest["Close"]
        bb_lower = latest["BB_LOWER"]

        signal = None

        if mode == "Touch / Below Lower Band":
            if low <= bb_lower:
                signal = "LOW Touch Lower Band"

        elif mode == "Near Lower Band (1%)":
            if low <= bb_lower * 1.01:
                signal = "LOW Near Lower Band"

        if signal:
            rows.append({
                "Ticker": ticker,
                "Date": latest["Date"].date(),
                "Low": round(low, 2),
                "Close": round(close, 2),
                "BB_Lower": round(bb_lower, 2),
                "Signal": signal
            })

    return pd.DataFrame(rows)


# =========================
# UI
# =========================
st.title("📊 DSE Bollinger Band Scanner (LOW-Based)")

uploaded_file = st.file_uploader("Upload DSE Excel File", type=["xlsx"])

if uploaded_file:
    data = load_excel(uploaded_file)

    # -------------------------
    # UPPER: CHART
    # -------------------------
    st.subheader("📈 Candlestick Chart")

    tickers = sorted(data["Ticker"].unique())
    selected_stock = st.selectbox("Select Stock", tickers)

    stock_df = data[data["Ticker"] == selected_stock].copy()
    stock_df = add_bollinger(stock_df)

    fig = go.Figure()

    # Clean OHLC (better wicks)
    fig.add_trace(go.Ohlc(
        x=stock_df["Date"],
        open=stock_df["Open"],
        high=stock_df["High"],
        low=stock_df["Low"],
        close=stock_df["Close"],
        increasing_line_color="#00ff88",
        decreasing_line_color="#ff4d4d",
        line_width=1,
        name="Price"
    ))

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=stock_df["Date"], y=stock_df["BB_UPPER"],
        line=dict(width=1), name="BB Upper"
    ))
    fig.add_trace(go.Scatter(
        x=stock_df["Date"], y=stock_df["BB_MID"],
        line=dict(width=1), name="BB Mid"
    ))
    fig.add_trace(go.Scatter(
        x=stock_df["Date"], y=stock_df["BB_LOWER"],
        line=dict(width=1), name="BB Lower"
    ))

    fig.update_layout(
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # LOWER: SCANNER
    # -------------------------
    st.subheader("🔍 Bollinger Band Scanner (Latest LOW Only)")

    scan_mode = st.selectbox(
        "Scanner Condition",
        [
            "Touch / Below Lower Band",
            "Near Lower Band (1%)"
        ]
    )

    scan_df = bollinger_scanner(data, scan_mode)

    if scan_df.empty:
        st.info("No stocks matched the condition today.")
    else:
        gb = GridOptionsBuilder.from_dataframe(scan_df)
        gb.configure_selection("single", use_checkbox=False)
        gb.configure_default_column(filter=True, sortable=True)
        grid = AgGrid(
            scan_df,
            gridOptions=gb.build(),
            height=300,
            theme="streamlit"
        )

        # Click → auto-load chart
        if grid["selected_rows"]:
            clicked = grid["selected_rows"][0]["Ticker"]
            st.experimental_set_query_params(ticker=clicked)
