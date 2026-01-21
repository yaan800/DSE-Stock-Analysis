import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="DSE Pro Stock Analyzer",
    layout="wide"
)

BB_WINDOW = 20
BB_STD = 2

# =========================
# LOAD EXCEL
# =========================
@st.cache_data
def load_excel_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    frames = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        if df.shape[1] < 7:
            continue

        df = df.iloc[:, :7]
        df.columns = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]

        df["Ticker"] = df["Ticker"].astype(str).str.strip()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        for c in ["Open", "High", "Low", "Close", "Volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.dropna(subset=["Ticker", "Date", "Close"])
        frames.append(df)

    if not frames:
        st.error("No valid stock data found.")
        st.stop()

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["Ticker", "Date"])
    return df

# =========================
# INDICATORS
# =========================
def add_indicators(df):
    df = df.sort_values("Date").copy()

    # Bollinger Bands
    ma = df["Close"].rolling(BB_WINDOW).mean()
    std = df["Close"].rolling(BB_WINDOW).std(ddof=0)

    df["BB_MID"] = ma
    df["BB_UPPER"] = ma + BB_STD * std
    df["BB_LOWER"] = ma - BB_STD * std

    # BB Width
    df["BB_WIDTH"] = (df["BB_UPPER"] - df["BB_LOWER"]) / df["BB_MID"]

    # BB Squeeze (lowest 10% of last 120 days)
    df["BB_SQUEEZE"] = (
        df["BB_WIDTH"]
        <= df["BB_WIDTH"]
        .rolling(120, min_periods=50)
        .quantile(0.10)
    )

    # Touch lower band
    df["TOUCH_LOWER_BB"] = df["Low"] <= df["BB_LOWER"]

    # BB Expansion
    df["BB_EXPANSION"] = df["BB_WIDTH"] > df["BB_WIDTH"].shift(1) * 1.3

    # BB Breakout (after squeeze)
    df["BB_BREAKOUT"] = (
        df["BB_EXPANSION"]
        & (df["Close"] > df["BB_UPPER"])
        & df["BB_SQUEEZE"].shift(1)
    )

    # Moving Averages
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA150"] = df["Close"].rolling(150).mean()
    df["MA200"] = df["Close"].rolling(200).mean()

    # Stage 2
    df["STAGE2"] = (
        (df["Close"] > df["MA50"]) &
        (df["MA50"] > df["MA150"]) &
        (df["MA150"] > df["MA200"])
    )

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
# TRUE IBD RS (1–99)
# =========================
data["RET_252"] = data.groupby("Ticker")["Close"].pct_change(252)

latest = (
    data.sort_values("Date")
    .groupby("Ticker")
    .tail(1)
    .copy()
)

latest["RS_RATING"] = (
    latest["RET_252"]
    .rank(pct=True)
    .mul(99)
    .round()
)

# =========================
# SCANNER
# =========================
st.markdown("---")
st.subheader("🔍 Smart Scanner (Latest Day)")

c1, c2, c3, c4 = st.columns(4)

with c1:
    f_squeeze = st.checkbox("BB Squeeze")

with c2:
    f_touch = st.checkbox("Touch Lower BB")

with c3:
    f_breakout = st.checkbox("BB Expansion Breakout")

with c4:
    f_rs90 = st.checkbox("RS ≥ 90")

scan = latest.copy()

if f_squeeze:
    scan = scan[scan["BB_SQUEEZE"]]

if f_touch:
    scan = scan[scan["TOUCH_LOWER_BB"]]

if f_breakout:
    scan = scan[scan["BB_BREAKOUT"]]

if f_rs90:
    scan = scan[scan["RS_RATING"] >= 90]

st.markdown(f"### 📋 Stocks Found: {len(scan)}")

if scan.empty:
    st.warning("No stocks match your filters.")
    st.stop()

display_cols = [
    "Ticker", "Close",
    "RS_RATING",
    "BB_SQUEEZE",
    "TOUCH_LOWER_BB",
    "BB_BREAKOUT",
    "STAGE2"
]

st.dataframe(
    scan[display_cols].sort_values("Ticker"),
    use_container_width=True
)

# =========================
# CLICK → CHART
# =========================
selected_stock = st.selectbox(
    "📌 Select stock to view chart",
    scan["Ticker"].unique()
)

# =========================
# CHART
# =========================
st.markdown("---")
st.subheader(f"📈 {selected_stock}")

df = data[data["Ticker"] == selected_stock].dropna(subset=["BB_MID"])

fig = go.Figure()

# Candles (clean)
fig.add_trace(go.Candlestick(
    x=df["Date"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    line=dict(width=0.7),
    whiskerwidth=0.4,
    increasing_line_color="#00ff99",
    decreasing_line_color="#ff4d4d",
    name="Price"
))

# Bollinger Bands
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["BB_UPPER"],
    line=dict(color="rgba(255,255,255,0.35)", width=1),
    name="BB Upper"
))
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["BB_MID"],
    line=dict(color="rgba(255,255,255,0.6)", width=1, dash="dot"),
    name="BB Mid"
))
fig.add_trace(go.Scatter(
    x=df["Date"], y=df["BB_LOWER"],
    line=dict(color="rgba(255,255,255,0.35)", width=1),
    name="BB Lower"
))

# Moving averages
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA50"], name="MA50"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA150"], name="MA150"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA200"], name="MA200"))

# BB Breakout markers
bo = df[df["BB_BREAKOUT"]]
fig.add_trace(go.Scatter(
    x=bo["Date"],
    y=bo["Close"],
    mode="markers",
    marker=dict(size=10, color="cyan"),
    name="BB Breakout"
))

fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)
