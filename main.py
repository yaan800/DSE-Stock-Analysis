import streamlit as st
from utils import read_excel_safely, process_sheet, merge_today_data
import pandas as pd

st.set_page_config(page_title="DSE Excel Upload Analyzer", layout="wide")
st.title("📊 DSE Stock Analysis – Excel Upload Version")

# -------------------
# Step 1: Upload Historical Data
# -------------------
historical_file = st.file_uploader("Upload Historical Excel File", type="xlsx")
all_data = pd.DataFrame()

if historical_file:
    all_sheets = read_excel_safely(historical_file)
    if all_sheets:
        st.success(f"Found {len(all_sheets)} sheets in historical file.")

        # Preview first sheet
        first_sheet = list(all_sheets.keys())[0]
        df_first = process_sheet(all_sheets[first_sheet])
        if df_first is not None:
            st.subheader(f"Preview of first sheet: {first_sheet}")
            st.dataframe(df_first.head(20))
            all_data = pd.concat([process_sheet(df) for df in all_sheets.values() if process_sheet(df) is not None], ignore_index=True)

# -------------------
# Step 2: Upload Today's Data
# -------------------
today_file = st.file_uploader("Upload Today's Excel/CSV", type=['xlsx','csv'])
if today_file and not all_data.empty:
    all_data = merge_today_data(all_data, today_file)
    st.success("Merged today's data with historical data!")

if not all_data.empty:
    st.subheader("Combined Dataset Preview")
    st.dataframe(all_data.head(50))
