import streamlit as st
import pandas as pd

from utils import (
    load_excel_data,
    add_bollinger,
    add_minervini_stage2
)

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="DSE Stock Analyzer",
    layout="wide"
)

st.title("📊 DSE Stock Analyzer (Bollinger + Minervini)")

# -------------------------------------------------
# File upload
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel file (multiple date sheets)",
    type=["xlsx"]
)

if uploaded_file:

    # -------------------------------------------------
    # Load & clean data
    # -------------------------------------------------
    try:
        data = load_excel_data(uploaded_file)
    except Exception as e:
        st.error(f"Error processing Excel file: {e}")
        st.stop()

    # -------------------------------------------------
    # GLOBAL INDICATORS (per stock)
    # -------------------------------------------------
    data = (
        data
        .groupby("Ticker", group_keys=False)
        .apply(add_bollinger)
    )

    data = (
        data
        .groupby("Ticker", group_keys=False)
        .apply(add_minervini_stage2)
    )

    # -------------------------------------------------
    # LOWER BOLLINGER BAND SCANNER
    # -------------------------------------------------
    st.subheader("📉 Bollinger Lower Band Scanner")

    threshold = 0.01  # 1% above lower band

    bb_mask = data["Close"] <= data["BB_LOWER"] * (1 + threshold)

    bb_buy_stocks = (
        data[bb_mask]
        .sort_values("Date", ascending=False)
        .groupby("Ticker")
        .head(1)
    )

    if not bb_buy_stocks.empty:
        st.dataframe(
            bb_buy_stocks[
                ["Ticker", "Date", "Close", "BB_LOWER", "Volume", "Stage2"]
            ],
            use_container_width=True
        )
    else:
        st.write("No stocks near the lower Bollinger Band.")

    st.divider()

    # -------------------------------------------------
    # SINGLE STOCK ANALYSIS
    # -------------------------------------------------
    stock_list = sorted(data["Ticker"].unique())

    selected_stock = st.selectbox(
        "📌 Select Stock",
        stock_list
    )

    stock_df = data[data["Ticker"] == selected_stock].copy()

    st.subheader(f"📈 {selected_stock} – Price & Bollinger Bands")

    st.line_chart(
        stock_df.set_index("Date")[["Close", "BB_UPPER", "BB_LOWER"]],
        use_container_width=True
    )

    st.subheader("📄 Data Table")
    st.dataframe(
        stock_df.sort_values("Date", ascending=False),
        use_container_width=True
    )

    # -------------------------------------------------
    # LATEST SIGNALS
    # -------------------------------------------------
    latest = stock_df.dropna().iloc[-1] if not stock_df.dropna().empty else None

    if latest is not None:
        st.subheader("🔍 Latest Signals")

        col1, col2, col3 = st.columns(3)

        col1.metric("Close", round(latest["Close"], 2))
        col2.metric(
            "Above BB Mid",
            "YES" if latest["Close"] > latest["BB_MID"] else "NO"
        )
        col3.metric(
            "Minervini Stage 2",
            "YES" if latest["Stage2"] else "NO"
        )

else:
    st.info("📤 Upload an Excel file to start analysis.")
