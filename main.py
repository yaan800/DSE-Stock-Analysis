import streamlit as st
from utils import get_dse_data

st.set_page_config(page_title="DSE Stock Loader", layout="wide")
st.title("📈 DSE Stock Analysis App")

uploaded_file = st.file_uploader("Upload your DSE Excel/CSV file", type=["xlsx","csv"])

if uploaded_file is not None:
    try:
        with st.spinner("Processing file..."):
            all_data, tickers_list = get_dse_data(uploaded_file)
        st.success(f"✅ Successfully loaded {len(tickers_list)} tickers!")

        # Show first 10 tickers as a table
        st.subheader("Sample Data (First 10 Tickers)")
        for ticker in tickers_list[:10]:
            st.write(f"**{ticker}**")
            st.dataframe(all_data[ticker])

        # Optional: Select ticker to see details
        selected = st.selectbox("Select a ticker to view full data", tickers_list)
        st.dataframe(all_data[selected])

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload a file to continue.")
