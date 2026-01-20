import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================
# OPTIONAL AGGRID
# =========================
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    USE_AGGRID = True
except Exception:
    USE_AGGRID = False

st.set_page_config(layout="wide", page_title="DSE Pro Stock Analyzer")

# =========================
# CONSTANTS
# =========================
BB_WINDOW = 20
BB_STD = 2
LOOKBACK_YEARS = 2

# =========================
# LOAD DATA (CACHED)
# =========================
@st.cache_data
def load_excel(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    dfs = []

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
        dfs.append(df)

    data = pd.concat(dfs, ignore_index=True)
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=365 * LOOKBACK_YEARS)
    data = data[data["Date"] >= cutoff]
    return data.sort_values(["Ticker", "Date"])

# =========================
# INDICATORS (FAST, VECTORIZED)
# =========================
@st.cache_data
def compute_indicators(df):
    g = df.groupby("Ticker", group_keys=False)

    df["MA50"] = g["Close"].transform(lambda x: x.rolling(50).mean())
    df["MA150"] = g["Close"].transform(lambda x: x.rolling(150).mean())
    df["MA200"] = g["Close"].transform(lambda x: x.rolling(200).mean())

    ma20 = g["Close"].transform(lambda x: x.rolling(20).mean())
    std20 = g["Close"].transform(lambda x: x.rolling(20).std(ddof=0))

    df["BB_UPPER"] = ma20 + BB_STD * std20
    df["BB_MID"] = ma20
    df["BB_LOWER"] = ma20 - BB_STD * std20

    df["Stage2"] = (
        (df["Close"] > df["MA50"]) &
        (df["MA50"] > df["MA150"]) &
        (df["MA150"] > df["MA200"])
    )

    df["VOL_AVG20"] = g["Volume"].transform(lambda x: x.rolling(20).mean())
    df["PocketPivot"] = (
        (df["Close"] > df["MA50"]) &
        (df["Volume"] > df["VOL_AVG20"] * 1.2)
    )

    # ✅ BREAKOUT = 20-day highest close
    df["HH20"] = g["Close"].transform(lambda x: x.rolling(20).max())
    df["Breakout"] = df["Close"] >= df["HH20"]

    # RS (3 months)
    df["RS_63"] = g["Close"].transform(lambda x: x.pct_change(63))

    return df

# =========================
# UI
# =========================
st.title("📊 DSE Pro Stock Analyzer")

uploaded = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded is None:
    st.stop()

data = compute_indicators(load_excel(uploaded))

# =========================
# SCANNER (LATEST DAY)
# =========================
latest = data.sort_values("Date").groupby("Ticker").tail(1).copy()

st.markdown("---")
st.subheader("🔍 Stock Scanner (Latest Day)")

c1, c2, c3 = st.columns(3)
with c1:
    require_stage2 = st.checkbox("Stage 2 Only")
with c2:
    require_breakout = st.checkbox("Breakout Only")
with c3:
    require_pp = st.checkbox("Pocket Pivot Only")

scan = latest.copy()
if require_stage2:
    scan = scan[scan["Stage2"]]
if require_breakout:
    scan = scan[scan["Breakout"]]
if require_pp:
    scan = scan[scan["PocketPivot"]]

scan["Score"] = (
    scan["Stage2"].astype(int) * 3 +
    scan["Breakout"].astype(int) * 2 +
    scan["PocketPivot"].astype(int) * 2 +
    scan["RS_63"].rank(ascending=False)
)

scan = scan.sort_values("Score", ascending=False)

st.write(f"### 📋 Stocks Found: {len(scan)}")
if scan.empty:
    st.stop()

# =========================
# STOCK SELECTION (CLICK → CHART)
# =========================
cols = ["Ticker", "Close", "Stage2", "Breakout", "PocketPivot", "RS_63", "Score"]

if USE_AGGRID:
    gb = GridOptionsBuilder.from_dataframe(scan[cols])
    gb.configure_selection("single", use_checkbox=False)
    grid = AgGrid(
        scan[cols],
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        height=300
    )

    rows = grid.get("selected_rows", [])
    if rows and len(rows) > 0:
        selected_stock = rows[0]["Ticker"]
    else:
        selected_stock = scan.iloc[0]["Ticker"]
else:
    selected_stock = st.selectbox("Select stock", scan["Ticker"].tolist())

# =========================
# CHART
# =========================
st.markdown("---")
st.subheader(f"📈 {selected_stock}")

df = data[data["Ticker"] == selected_stock]

fig = go.Figure()

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

fig.add_trace(go.Scatter(x=df["Date"], y=df["MA50"], name="MA50"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA150"], name="MA150"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["MA200"], name="MA200"))

fig.update_layout(
    height=650,
    xaxis_rangeslider_visible=False,
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

