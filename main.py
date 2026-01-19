import streamlit as st
from utils import get_dse_data

st.set_page_config(page_title="DSE Multi-Sheet Loader", layout="wide")
st.title("📈 DSE Multi-Day Stock Analysis App")

uploaded_file = st.file_uploader("Upload your multi-sheet Excel file", type=["xlsx"])

if uploaded_file is not None:
    try:
        with st.spinner("Processing all sheets..."):
            all_data, tickers_list = get_dse_data(uploaded_file)
        st.success(f"✅ Loaded {len(tickers_list)} tickers across {len(all_data[tickers_list[0]])} sheets each!")

        # Sample view: first ticker and first sheet
        sample_ticker = tickers_list[0]
        sample_sheet = list(all_data[sample_ticker].keys())[0]
        st.subheader(f"Sample Data: {sample_ticker} | Sheet: {sample_sheet}")
        st.dataframe(all_data[sample_ticker][sample_sheet])

        # Ticker selector
        selected_ticker = st.selectbox("Select a ticker", tickers_list)
        selected_sheet = st.selectbox(
            "Select a date/sheet",
            list(all_data[selected_ticker].keys())
        )
        st.dataframe(all_data[selected_ticker][selected_sheet])

    except Exception as e:
        st.error(f"Error processing Excel: {e}")
else:
    st.info("Please upload an Excel file to continue.")
