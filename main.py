import streamlit as st
from utils import read_excel_safely, process_sheet, bollinger_signal, minervini_stage2

st.set_page_config(page_title="DSE Excel Analyzer", layout="wide")
st.title("📊 DSE Stock Analysis – Excel Upload Version")

# -------------------
# Step 1: Upload Excel
# -------------------
uploaded_file = st.file_uploader("Upload Historical Excel File", type="xlsx")

all_sheets = {}
if uploaded_file:
    all_sheets, error = read_excel_safely(uploaded_file)
    if error:
        st.error(error)
    elif all_sheets:
        st.success(f"Found {len(all_sheets)} sheets.")
        sheet_names = list(all_sheets.keys())

        # -------------------
        # Step 2: Choose Sheet
        # -------------------
        selected_sheet = st.selectbox("Select a sheet to view", sheet_names)
        df = process_sheet(all_sheets[selected_sheet])
        if df is None:
            st.warning("Selected sheet has too few columns or invalid format.")
        else:
            st.subheader(f"Preview – {selected_sheet}")
            st.dataframe(df.tail(50))

            # -------------------
            # Step 3: Calculations
            # -------------------
            if st.checkbox("Apply Bollinger Band Signals"):
                df = bollinger_signal(df)
                st.subheader("Bollinger Band Signals")
                st.dataframe(df[['Ticker','Date','Close','BB_upper','BB_lower','BB_signal']].tail(50))

            if st.checkbox("Apply Minervini Stage 2 Filter"):
                df = minervini_stage2(df)
                st.subheader("Stage 2 Signals")
                st.dataframe(df[['Ticker','Date','Close','Stage2']].tail(50))
