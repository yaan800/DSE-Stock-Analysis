import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="DSE Stock Analyzer")

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
st.title("📊 DSE Stock Analyzer")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is None:
    st.stop()

data = load_excel_data(uploaded_file)
data = data.groupby("Ticker", group_keys=False).apply(add_bollinger)

# =========================
# ======= TOP SECTION =====
# =========================

st.subheader("📈 Stock Chart")

stock_list = sorted(data["Ticker"].unique())
selected_stock = st.selectbox("Select Stock", stock_list)

stock_df = data[data["Ticker"] == selected_stock].sort_values("Date")

# ---- Chart ----
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=stock_df["Date"],
    open=stock_df["Open"],
    high=stock_df["High"],
    low=stock_df["Low"],
    close=stock_df["Close"],
    increasing_line_width=1.6,
    decreasing_line_width=1.6,
    name="Price"
))

fig.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["BB_UPPER"],
    name="BB Upper", line=dict(width=1)
))

fig.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["BB_MID"],
    name="BB Mid", line=dict(width=1)
))

fig.add_trace(go.Scatter(
    x=stock_df["Date"], y=stock_df["BB_LOWER"],
    name="BB Lower", line=dict(width=1)
))

fig.update_layout(
    height=600,
    xaxis_rangeslider_visible=False,
    title=f"{selected_stock} — Candlestick with Bollinger Bands"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# ===== SCANNER SECTION ===
# =========================

st.markdown("---")
st.subheader("🔍 Bollinger Band Scanner (Latest Day Only)")

# ---- Filters ----
c1, c2 = st.columns(2)

with c1:
    mode = st.selectbox(
        "Scan Condition",
        [
            "Close below Lower Band",
            "Close near Lower Band (within 1%)"
        ]
    )

with c2:
    near_pct = st.number_input("Near % (for 2nd option)", value=1.0, step=0.1)

# =========================
# ONLY LATEST DAY PER STOCK
# =========================
latest = (
    data
    .sort_values("Date")
    .groupby("Ticker")
    .tail(1)
    .copy()
)

# =========================
# SCAN LOGIC
# =========================
if mode == "Close below Lower Band":
    scan = latest[latest["Close"] < latest["BB_LOWER"]]

else:
    scan = latest[
        (latest["Close"] >= latest["BB_LOWER"]) &
        (latest["Close"] <= latest["BB_LOWER"] * (1 + near_pct / 100))
    ]

# =========================
# RESULT TABLE
# =========================
st.markdown(f"### 📋 Stocks Matching Today: {len(scan)}")

if len(scan) == 0:
    st.warning("No stocks match the condition today.")
else:
    show_cols = ["Ticker", "Date", "Close", "BB_LOWER", "BB_MID", "BB_UPPER", "Volume"]
    st.dataframe(scan[show_cols].sort_values("Ticker"), use_container_width=True)
