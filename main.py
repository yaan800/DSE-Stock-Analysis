import streamlit as st
import pandas as pd
from utils import calculate_bollinger, check_minervini, prepare_data

st.set_page_config(page_title="DSE Stock Analysis - Option A", layout="wide")
st.title("📊 DSE Stock Analysis (Option A)")

# --- File upload ---
uploaded_file = st.file_uploader("Upload your Excel file with multiple sheets", type=["xlsx"])

if uploaded_file:
    try:
        # Read Excel in memory
        xls = pd.ExcelFile(uploaded_file)

        # Show available sheets
        sheet_list = xls.sheet_names
        selected_sheet = st.selectbox("Select Sheet (Date)", sheet_list)

        # Read the selected sheet without header
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=None)

        # Prepare data: add column names, numeric conversions
        df = prepare_data(df)

        st.subheader(f"Data from sheet: {selected_sheet}")
        st.dataframe(df)

        # --- Bollinger Bands ---
        bb_period = st.number_input("Bollinger Bands Period", min_value=5, max_value=100, value=20)
        bb_std = st.number_input("Bollinger Bands Std Dev", min_value=1.0, max_value=5.0, value=2.0, step=0.1)

        df_bb = calculate_bollinger(df.copy(), period=bb_period, std=bb_std)
        st.subheader("Bollinger Bands Calculated")
        st.dataframe(df_bb[['Ticker', 'Close', 'BB_Mid', 'BB_Upper', 'BB_Lower']])

        # --- Mike Minervini Conditions ---
        st.subheader("Mike Minervini Conditions")
        df_mm = check_minervini(df.copy())
        st.dataframe(df_mm[['Ticker', 'Close', '50MA', '150MA', '200MA', 'Minervini_Buy']])

    except Exception as e:
        st.error(f"Error processing Excel: {e}")
else:
    st.info("Please upload an Excel file to start.")
