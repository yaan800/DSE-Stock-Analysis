import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import (
    load_excel_data,
    add_bollinger,
    add_minervini_stage2
)

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="DSE Stock Analyzer", layout="wide")
st.title("📊 DSE Stock Analyzer")

# -------------------------------------------------
# File upload
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel file (multiple date sheets)",
    type=["xlsx"]
)

if uploaded_file:

    # -------------------------------------------------
    # Load data
    # -------------------------------------------------
    try:
        data = load_excel_data(uploaded_file)
    except Exception as e:
        st.error(e)
        st.stop()

    # -------------------------------------------------
    # Indicators (per stock)
    # -------------------------------------------------
    data = data.groupby("Ticker", group_keys=False).apply(add_bollinger)
    data = data.groupby("Ticker", group_keys=False).apply(add_minervini_stage2)

    # =================================================
    # 🔹 SINGLE STOCK VIEW
    # =================================================
    st.subheader("📈 Single Stock Analysis")

    stock_list = sorted(data["Ticker"].unique())
    selected_stock = st.selectbox("Select Stock", stock_list)

    stock_df = data[data["Ticker"] == selected_stock].copy()

    # ---- Candlestick
    fig = go.Figure()

    fig.add_candlestick(
        x=stock_df["Date"],
        open=stock_df["Open"],
        high=stock_df["High"],
        low=stock_df["Low"],
        close=stock_df["Close"],
        name="Price"
    )

    fig.add_trace(go.Scatter(
        x=stock_df["Date"],
        y=stock_df["BB_UPPER"],
        line=dict(width=1),
        name="BB Upper"
    ))

    fig.add_trace(go.Scatter(
        x=stock_df["Date"],
        y=stock_df["BB_LOWER"],
        line=dict(width=1),
        name="BB Lower"
    ))

    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        stock_df.sort_values("Date", ascending=False),
        use_container_width=True
    )

    st.divider()

    # =================================================
    # 🔹 BOLLINGER SCANNER (BOTTOM)
    # =================================================
    st.subheader("📉 Bollinger Band Scanner")

    col1, col2, col3 = st.columns(3)

    with col1:
        show_cross_down = st.checkbox("Crossed BELOW Lower Band", value=True)

    with col2:
        show_near_band = st.checkbox("Near Lower Band", value=True)

    with col3:
        threshold = st.slider(
            "Near Band Threshold (%)",
            min_value=0.1,
            max_value=5.0,
            value=1.0
        ) / 100

    scan_df = data.copy()

    # -------------------------------------------------
    # Conditions
    # -------------------------------------------------
    conditions = []

    if show_near_band:
        conditions.append(
            scan_df["Close"] <= scan_df["BB_LOWER"] * (1 + threshold)
        )

    if show_cross_down:
        scan_df["Prev_Close"] = scan_df.groupby("Ticker")["Close"].shift(1)
        scan_df["Prev_BB"] = scan_df.groupby("Ticker")["BB_LOWER"].shift(1)

        conditions.append(
            (scan_df["Prev_Close"] > scan_df["Prev_BB"]) &
            (scan_df["Close"] < scan_df["BB_LOWER"])
        )

    if conditions:
        final_condition = conditions[0]
        for c in conditions[1:]:
            final_condition &= c

        scan_df = scan_df[final_condition]

    # Latest signal per stock
    scan_df = (
        scan_df
        .sort_values("Date", ascending=False)
        .groupby("Ticker")
        .head(1)
    )

    # -------------------------------------------------
    # Interactive table
    # -------------------------------------------------
    if scan_df.empty:
        st.warning("No stocks matched your criteria.")
    else:
        st.info("👉 Click a row to see candlestick chart below")

        selection = st.dataframe(
            scan_df[
                ["Ticker", "Date", "Close", "BB_LOWER", "Volume", "Stage2"]
            ],
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun"
        )

        # -------------------------------------------------
        # Click → Chart
        # -------------------------------------------------
        if selection and selection["selection"]["rows"]:
            row_idx = selection["selection"]["rows"][0]
            clicked_stock = scan_df.iloc[row_idx]["Ticker"]

            st.subheader(f"📊 {clicked_stock} – Scanner Chart")

            df_click = data[data["Ticker"] == clicked_stock]

            fig2 = go.Figure()

            fig2.add_candlestick(
                x=df_click["Date"],
                open=df_click["Open"],
                high=df_click["High"],
                low=df_click["Low"],
                close=df_click["Close"]
            )

            fig2.add_trace(go.Scatter(
                x=df_click["Date"],
                y=df_click["BB_LOWER"],
                name="BB Lower",
                line=dict(width=1)
            ))

            fig2.update_layout(
                height=450,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Upload Excel file to begin.")
