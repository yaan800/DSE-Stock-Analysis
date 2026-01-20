import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from scipy.signal import find_peaks

st.set_page_config(layout="wide", page_title="DSE Pro Stock Analyzer Pro")

# =========================
# PARAMETERS
# =========================
BB_WINDOW = 20
BB_STD = 2

# =========================
# LOAD EXCEL
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
        df = df.iloc[:, 0:7]
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
        st.error("No valid stock data found.")
        st.stop()

    full_df = pd.concat(all_rows, ignore_index=True)
    full_df = full_df.sort_values(["Ticker", "Date"])
    return full_df

# =========================
# INDICATORS
# =========================
def add_indicators(df):
    df = df.sort_values("Date").copy()
    
    # Bollinger Bands
    ma = df["Close"].rolling(BB_WINDOW, min_periods=BB_WINDOW).mean()
    std = df["Close"].rolling(BB_WINDOW, min_periods=BB_WINDOW).std(ddof=0)
    df["BB_MID"] = ma
    df["BB_UPPER"] = ma + BB_STD * std
    df["BB_LOWER"] = ma - BB_STD * std
    
    # Moving averages for Stage 2
    df["MA50"] = df["Close"].rolling(50, min_periods=50).mean()
    df["MA150"] = df["Close"].rolling(150, min_periods=150).mean()
    df["MA200"] = df["Close"].rolling(200, min_periods=200).mean()
    df["Stage2"] = (
        (df["Close"] > df["MA50"]) &
        (df["MA50"] > df["MA150"]) &
        (df["MA150"] > df["MA200"])
    )
    
    # Volume expansion & Pocket Pivot
    df["VOL_AVG20"] = df["Volume"].rolling(20, min_periods=20).mean()
    df["VolumeExpansion"] = df["Volume"] > df["VOL_AVG20"] * 1.5
    df["PocketPivot"] = (
        (df["Close"] > df["MA50"]) &
        (df["Volume"] > df["VOL_AVG20"] * 1.2) &
        (df["Close"].pct_change() < 0.03)
    )

    # Breakout: 20-day high
    df["HH20"] = df["Close"].rolling(20, min_periods=20).max()
    df["Breakout"] = df["Close"] >= df["HH20"]

    # Relative Strength (RS%) 3-month & 6-month
    df["RS_3M"] = df["Close"].pct_change(63)
    df["RS_6M"] = df["Close"].pct_change(126)

    # VCP Pattern detection (simplified)
    close = df["Close"].values
    peaks, _ = find_peaks(close, distance=5)
    troughs, _ = find_peaks(-close, distance=5)
    df["VCP"] = False
    if len(peaks) >= 3 and len(troughs) >= 3:
        df["VCP"].iloc[-1] = True

    return df

# =========================
# UI
# =========================
st.title("🚀 DSE Pro Stock Analyzer Pro")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file is None:
    st.stop()

data = load_excel_data(uploaded_file)
data = data.groupby("Ticker", group_keys=False).apply(add_indicators)

# =========================
# LATEST DAY SCANNER
# =========================
latest = data.groupby("Ticker").tail(1)

st.markdown("---")
st.subheader("🔍 Smart Scanner")

# Filters
c1, c2, c3, c4 = st.columns(4)
with c1:
    bb_mode = st.selectbox("Bollinger", ["Any", "Below Lower", "Near Lower"])
with c2:
    require_stage2 = st.checkbox("Require Stage 2")
with c3:
    require_breakout = st.checkbox("Require Breakout")
with c4:
    require_pocket = st.checkbox("Require Pocket Pivot")

scan = latest.copy()

if bb_mode == "Below Lower":
    scan = scan[scan["Close"] < scan["BB_LOWER"]]
elif bb_mode == "Near Lower":
    scan = scan[(scan["Close"] >= scan["BB_LOWER"]) & (scan["Close"] <= scan["BB_LOWER"]*1.01)]
if require_stage2:
    scan = scan[scan["Stage2"]]
if require_breakout:
    scan = scan[scan["Breakout"]]
if require_pocket:
    scan = scan[scan["PocketPivot"]]

# Auto-ranking: combine RS, Stage2, Breakout, Pocket Pivot
scan["Score"] = (
    scan["Stage2"].astype(int)*3 +
    scan["Breakout"].astype(int)*2 +
    scan["PocketPivot"].astype(int)*2 +
    scan["RS_3M"].fillna(0)*3
)
scan = scan.sort_values("Score", ascending=False)

st.markdown(f"### 📋 Stocks Found: {len(scan)}")
if len(scan) == 0:
    st.warning("No stocks match your filters.")
    st.stop()

# =========================
# AGGrid Table
# =========================
show_cols = ["Ticker", "Close", "Stage2", "Breakout", "PocketPivot", "RS_3M", "Score"]
gb = GridOptionsBuilder.from_dataframe(scan[show_cols])
gb.configure_selection("single")
grid_options = gb.build()

grid_response = AgGrid(
    scan[show_cols],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme="streamlit"
)

selected_row = grid_response["selected_rows"]
if selected_row:
    selected_stock = selected_row[0]["Ticker"]
else:
    selected_stock = scan.iloc[0]["Ticker"]

# =========================
# CHART
# =========================
st.markdown("---")
st.subheader(f"📈 {selected_stock} Chart")

stock_df = data[data["Ticker"] == selected_stock].sort_values("Date")

fig = go.Figure()
# Candlestick
fig.add_trace(go.Candlestick(
    x=stock_df["Date"],
    open=stock_df["Open"],
    high=stock_df["High"],
    low=stock_df["Low"],
    close=stock_df["Close"],
    increasing_line_color="#00ff88",
    decreasing_line_color="#ff4d4d",
    line=dict(width=0.8),
    whiskerwidth=0.5,
    name="Price"
))
# Bollinger Bands
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_UPPER"], name="BB Upper", line=dict(color="yellow")))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_MID"], name="BB Mid", line=dict(color="white")))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_LOWER"], name="BB Lower", line=dict(color="yellow")))

# Moving averages
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["MA50"], name="MA50", line=dict(color="cyan", dash="dash")))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["MA150"], name="MA150", line=dict(color="orange", dash="dash")))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["MA200"], name="MA200", line=dict(color="magenta", dash="dash")))

fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# =========================
# PORTFOLIO BACKTEST
# =========================
st.markdown("---")
st.subheader("💰 Portfolio Backtest")

capital = 100000
top_n = min(5, len(scan))
investment_per_stock = capital / top_n

portfolio_values = pd.Series(0, index=stock_df["Date"])
for ticker in scan.head(top_n)["Ticker"]:
    s = data[data["Ticker"]==ticker].sort_values("Date")
    s = s.set_index("Date")["Close"]
    s = s / s.iloc[0] * investment_per_stock
    portfolio_values = portfolio_values.add(s, fill_value=0)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=portfolio_values.index, y=portfolio_values.values, name="Portfolio Value", line=dict(color="lime")))
fig2.update_layout(height=400, template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)
