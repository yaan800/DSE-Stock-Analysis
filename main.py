import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from scipy.signal import find_peaks

st.set_page_config(layout="wide", page_title="DSE Pro Stock Analyzer")

# =========================
# SETTINGS
# =========================
BB_WINDOW = 20
BB_STD = 2

# =========================
# LOAD EXCEL DATA
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
        for col in ["Open","High","Low","Close","Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df = df[df["Ticker"].notna() & df["Close"].notna() & df["Date"].notna()]
        if not df.empty:
            all_rows.append(df)

    if not all_rows:
        st.error("No valid stock data found in Excel.")
        st.stop()

    full_df = pd.concat(all_rows, ignore_index=True).sort_values(["Ticker","Date"])
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

    # Volume expansion / Pocket Pivot
    df["VOL_AVG20"] = df["Volume"].rolling(20).mean()
    df["VolumeExpansion"] = df["Volume"] > df["VOL_AVG20"] * 1.5
    df["PocketPivot"] = (
        (df["Close"] > df["MA50"]) &
        (df["Volume"] > df["VOL_AVG20"] * 1.2) &
        (df["Close"].pct_change() < 0.03)
    )

    # Breakout: 20-day high
    df["HH20"] = df["Close"].rolling(20, min_periods=20).max()
    df["Breakout"] = df["Close"] >= df["HH20"]

    # Relative Strength (RS Rating) 3-month
    df["RS_63"] = df["Close"].pct_change(63)

    # Basic VCP detection (contraction peaks)
    df['PeakHighs'], _ = find_peaks(df['Close'], distance=5)
    df['VCP'] = False
    if len(df['PeakHighs']) > 2:
        # If high peaks are contracting
        highs = df['Close'].iloc[df['PeakHighs']]
        df.loc[df.index[df['PeakHighs'][-1]], 'VCP'] = highs.diff().iloc[-1] < 0

    return df

# =========================
# APP HEADER
# =========================
st.title("📊 DSE Pro Stock Analyzer - Professional Edition")
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file is None:
    st.stop()

data = load_excel_data(uploaded_file)
data = data.groupby("Ticker", group_keys=False).apply(add_indicators)

# =========================
# SCANNER (LATEST DAY)
# =========================
latest = data.sort_values("Date").groupby("Ticker").tail(1).copy()
st.markdown("---")
st.subheader("🔍 Smart Scanner (Latest Day Only)")

c1, c2, c3, c4 = st.columns(4)
with c1:
    bb_mode = st.selectbox("Bollinger Condition", ["Any","Below Lower Band","Near Lower Band (1%)"])
with c2:
    require_stage2 = st.checkbox("Require Stage 2")
with c3:
    require_breakout = st.checkbox("Require Breakout")
with c4:
    require_pp = st.checkbox("Require Pocket Pivot")

scan = latest.copy()
if bb_mode == "Below Lower Band":
    scan = scan[scan["Close"] < scan["BB_LOWER"]]
elif bb_mode == "Near Lower Band (1%)":
    scan = scan[(scan["Close"] >= scan["BB_LOWER"]) & (scan["Close"] <= scan["BB_LOWER"]*1.01)]
if require_stage2:
    scan = scan[scan["Stage2"]==True]
if require_breakout:
    scan = scan[scan["Breakout"]==True]
if require_pp:
    scan = scan[scan["PocketPivot"]==True]

# Auto ranking system
scan['Score'] = (
    scan['Stage2'].astype(int)*3 +
    scan['Breakout'].astype(int)*2 +
    scan['PocketPivot'].astype(int)*2 +
    scan['RS_63'].rank(ascending=False)
)
scan = scan.sort_values('Score', ascending=False)

st.markdown(f"### 📋 Stocks Found: {len(scan)}")
if len(scan)==0:
    st.warning("No stocks match your filter.")
    st.stop()

# =========================
# JS-STYLE TABLE
# =========================
show_cols = ["Ticker","Close","Stage2","VolumeExpansion","PocketPivot","Breakout","RS_63","Score"]
gb = GridOptionsBuilder.from_dataframe(scan[show_cols])
gb.configure_selection('single')
grid_options = gb.build()
grid_response = AgGrid(scan[show_cols], gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED)
selected_row = grid_response['selected_rows']
if selected_row:
    selected_stock = selected_row[0]['Ticker']
else:
    selected_stock = scan.iloc[0]['Ticker']

# =========================
# STOCK CHART
# =========================
st.markdown("---")
st.subheader(f"📈 {selected_stock} Chart")
stock_df = data[data["Ticker"]==selected_stock].sort_values("Date")

fig = go.Figure()
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
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_UPPER"], name="BB Upper"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_MID"], name="BB Mid"))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["BB_LOWER"], name="BB Lower"))
# MAs
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["MA50"], name="MA50", line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["MA150"], name="MA150", line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=stock_df["Date"], y=stock_df["MA200"], name="MA200", line=dict(dash='dash')))
# Pocket Pivot markers
pp_days = stock_df[stock_df['PocketPivot']==True]
fig.add_trace(go.Scatter(x=pp_days['Date'], y=pp_days['Close'], mode='markers', marker=dict(color='yellow', size=10), name='Pocket Pivot'))

fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# =========================
# PORTFOLIO BACKTEST (TOP N)
# =========================
st.markdown("---")
st.subheader("💼 Portfolio Backtest (Top Ranked Stocks)")
capital = st.number_input("Starting Capital", value=100000, step=1000)
n_stocks = st.slider("Top N Stocks to Include", 1, min(10,len(scan)), value=5)

portfolio = scan.head(n_stocks).copy()
portfolio['Investment'] = capital / n_stocks

# Compute returns
returns = []
for ticker in portfolio['Ticker']:
    df = data[data['Ticker']==ticker].sort_values("Date")
    ret = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
    returns.append(ret)
portfolio['Return'] = returns
portfolio['PortfolioValue'] = portfolio['Investment'] * (1 + portfolio['Return'])
total_portfolio_value = portfolio['PortfolioValue'].sum()
st.write(portfolio[['Ticker','Return','PortfolioValue']])
st.metric("Total Portfolio Value", f"{total_portfolio_value:,.2f} BDT")
