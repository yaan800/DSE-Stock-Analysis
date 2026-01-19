import streamlit as st
from utils import read_excel_safely, process_sheet

st.set_page_config(page_title="DSE Multi-Sheet Analyzer", layout="wide")
st.title("📊 DSE Multi-Sheet Excel Analyzer")

uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx'])

if uploaded_file:
    st.info("Reading Excel file...")
    all_sheets = read_excel_safely(uploaded_file)

    if not all_sheets:
        st.error("No valid sheets found in the Excel file.")
    else:
        st.success(f"Found {len(all_sheets)} sheets.")

        sheet_to_view = st.selectbox("Select a sheet to preview", list(all_sheets.keys()))

        if sheet_to_view:
            df_raw = all_sheets[sheet_to_view]
            df_processed = process_sheet(df_raw)

            if df_processed is not None:
                st.subheader(f"Preview of '{sheet_to_view}'")
                st.dataframe(df_processed.head(20))

                # Basic statistics
                st.subheader("Summary Statistics")
                st.write(df_processed.describe())
            else:
                st.warning("Could not process this sheet.")
