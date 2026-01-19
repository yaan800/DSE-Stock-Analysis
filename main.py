import streamlit as st
import pandas as pd

from utils import (
    load_excel_data,
    add_bollinger,
    add_minervini_stage2
)

st.set_page_config(page_title="DSE Stock Analyzer", layout="wide")

st.title("📊 DSE Stock Analysis – Option A")

uploaded_file = st.file_uploader(
    "Upload Excel file (multiple date sheets)",
    type=["xlsx"]
)

if uploaded_file:
    try:
        data = load_excel_data(uploaded_file)
    except Exception as e:
        st.error(f"Error processing Excel: {e}")
        st.stop()

    stock_list = sorted(data["Ticker"].unique().tolist())

    selected_stock = st.selectbox(
        "Select Stock",
        stock_list
    )

    stock_df = data[data["Ticker"] == selected_stock].copy()
    stock_df = add_bollinger(stock_df)
    stock_df = add_minervini_stage2(stock_df)

    st.subheader(f"📈 {selected_stock}")

    st.dataframe(
        stock_df.sort_values("Date", ascending=False),
        use_container_width=True
    )

    st.line_chart(
        stock_df.set_index("Date")[["Close", "BB_UPPER", "BB_LOWER"]],
        use_container_width=True
    )

    latest = stock_df.dropna().iloc[-1] if not stock_df.dropna().empty else None

    if latest is not None:
        st.markdown("### 🔍 Latest Signals")
        st.write({
            "Close": latest["Close"],
            "Above BB Mid": latest["Close"] > latest["BB_MID"],
            "Stage 2": bool(latest["Stage2"])
        })
