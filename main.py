import streamlit as st
import pandas as pd
from utils import load_excel_data, add_bollinger, bollinger_lower_touch, add_minervini_stage2

# -----------------------------
# Streamlit App Title
# -----------------------------
st.title("DSE Stock Analysis - Option A")
st.write("Upload your Excel file containing all DSE stock data.")

# -----------------------------
# Excel Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload DSE Excel file", type=["xls","xlsx"])

if uploaded_file:
    try:
        # Load data from all sheets
        full_df = load_excel_data(uploaded_file)

        # Show list of sheets for reference
        xls = pd.ExcelFile(uploaded_file)
        sheet_list = xls.sheet_names
        st.write(f"Found sheets: {sheet_list}")
        selected_sheet = st.selectbox("Select Sheet to view", sheet_list)
        
        # Read only the selected sheet
        sheet_df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=None)
        sheet_df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']

        st.subheader(f"Data from sheet: {selected_sheet}")
        st.dataframe(sheet_df)

        # -----------------------------
        # Bollinger Bands
        # -----------------------------
        sheet_df = add_bollinger(sheet_df)

        st.subheader("Full Dataset with Bollinger Bands")
        st.dataframe(sheet_df)

        # -----------------------------
        # Minervini Stage 2
        # -----------------------------
        sheet_df = add_minervini_stage2(sheet_df)

        st.subheader("Stocks Passing Minervini Stage 2 Conditions")
        minervini_stocks = sheet_df[sheet_df["Stage2"]==True]
        st.dataframe(minervini_stocks)

        # -----------------------------
        # Stocks Touching / Below Lower Bollinger Band
        # -----------------------------
        df_touching_lower = bollinger_lower_touch(sheet_df)
        st.subheader("Stocks Touching / Below Lower Bollinger Band")
        st.dataframe(df_touching_lower)

    except Exception as e:
        st.error(f"Error processing Excel: {e}")
