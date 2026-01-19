import pandas as pd
import pandas_ta as ta
import streamlit as st
from utils import load_excel_data_filtered, add_bollinger, bollinger_lower_touch, add_minervini_stage2

st.set_page_config(page_title="DSE Stock Analysis Option A", layout="wide")
st.title("DSE Stock Analysis - Option A")

# -------------------------------
# Upload Excel
# -------------------------------
uploaded_file = st.file_uploader("Upload DSE Excel file", type=["xls", "xlsx"])
if uploaded_file:
    try:
        # Show all sheets in the Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        st.sidebar.subheader("Sheets in file")
        selected_sheet = st.sidebar.selectbox("Select sheet to analyze", sheet_names[1:])  # skip first sheet (desired stocks)

        # Load data for selected sheet, automatically filtered by desired stocks from first sheet
        full_df = load_excel_data_filtered(uploaded_file, selected_sheet)

        # -------------------------------
        # Calculate Bollinger Bands
        # -------------------------------
        full_df = add_bollinger(full_df)

        # -------------------------------
        # Minervini Stage 2 Screener
        # -------------------------------
        full_df = add_minervini_stage2(full_df)

        # -------------------------------
        # Display Full Data
        # -------------------------------
        st.subheader("Full Data")
        st.dataframe(full_df)

        # -------------------------------
        # Stocks touching or below Lower Bollinger Band
        # -------------------------------
        df_touching_lower = bollinger_lower_touch(full_df)
        st.subheader("Stocks Touching / Below Lower Bollinger Band")
        st.dataframe(df_touching_lower)

    except Exception as e:
        st.error(f"Error processing Excel: {e}")
