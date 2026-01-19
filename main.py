import streamlit as st
import pandas as pd
from utils import (
    load_excel_data_filtered,
    add_bollinger,
    bollinger_lower_touch,
    add_minervini_stage2
)

# -----------------------------
# App Title
# -----------------------------
st.title("DSE Stock Analysis - Option A")
st.write("Upload your Excel file containing all DSE stock data (first sheet = desired stocks).")

# -----------------------------
# Upload Excel
# -----------------------------
uploaded_file = st.file_uploader("Upload DSE Excel file", type=["xls","xlsx"])

if uploaded_file:
    try:
        # Load all sheet names
        xls = pd.ExcelFile(uploaded_file)
        sheet_list = xls.sheet_names

        # First sheet = desired stocks
        desired_stocks_df = pd.read_excel(uploaded_file, sheet_name=sheet_list[0], header=None, usecols="A")
        desired_stocks = desired_stocks_df.iloc[:,0].dropna().tolist()
        st.write(f"Desired Stocks ({len(desired_stocks)}):")
        st.write(desired_stocks)

        # Select sheet to analyze
        selected_sheet = st.selectbox("Select Sheet (Date) for analysis", sheet_list[1:])

        # Load only desired stocks from selected sheet
        sheet_df = load_excel_data_filtered(uploaded_file, selected_sheet, desired_stocks)

        st.subheader(f"Data from sheet: {selected_sheet}")
        st.dataframe(sheet_df)

        # -----------------------------
        # Bollinger Bands
        # -----------------------------
        sheet_df = add_bollinger(sheet_df)
        st.subheader("Dataset with Bollinger Bands")
        st.dataframe(sheet_df)

        # -----------------------------
        # Minervini Stage 2
        # -----------------------------
        sheet_df = add_minervini_stage2(sheet_df)
        minervini_stocks = sheet_df[sheet_df["Stage2"]==True]
        st.subheader("Stocks Passing Minervini Stage 2")
        st.dataframe(minervini_stocks)

        # -----------------------------
        # Stocks Touching / Below Lower Bollinger Band
        # -----------------------------
        df_touching_lower = bollinger_lower_touch(sheet_df)
        st.subheader("Stocks Touching / Below Lower Bollinger Band")
        st.dataframe(df_touching_lower)

    except Exception as e:
        st.error(f"Error processing Excel: {e}")
