import streamlit as st
from utils import get_dse_data, bollinger_signal, minervini_stage2, add_indicators

st.set_page_config(page_title="DSE Stock Analysis", layout="wide")
st.title("DSE Stock Analysis - Option A")

# ---------------------------
# Upload Excel
# ---------------------------
uploaded_file = st.file_uploader("Upload your full Excel file (all sheets)", type=["xlsx"])

if uploaded_file:
    # List available sheets
    xls = pd.ExcelFile(uploaded_file)
    sheet_list = xls.sheet_names
    selected_sheet = st.selectbox("Select Sheet (Date)", sheet_list)

    try:
        df = get_dse_data(uploaded_file, selected_sheet)

        st.subheader(f"Data Preview: {selected_sheet}")
        st.dataframe(df.head(10))

        # ---------------------------
        # Bollinger Bands
        # ---------------------------
        df_bb = bollinger_signal(df)
        st.subheader("Bollinger Band Signals")
        st.dataframe(df_bb[['Ticker', 'Date', 'Close', 'BB_lower', 'BB_upper', 'BB_buy', 'BB_sell']].tail(10))

        # ---------------------------
        # Minervini Stage 2
        # ---------------------------
        df_stage2 = minervini_stage2(df)
        st.subheader("Minervini Stage 2 Screener")
        st.dataframe(df_stage2[['Ticker', 'Date', 'Close', 'MA50', 'MA150', 'MA200', 'Stage2']].tail(10))

        # ---------------------------
        # Additional Indicators
        # ---------------------------
        df_ind = add_indicators(df)
        st.subheader("Additional Indicators (RSI, MFI, EMA)")
        st.dataframe(df_ind[['Ticker', 'Date', 'RSI14', 'MFI14', 'EMA9', 'EMA21', 'EMA50', 'EMA200']].tail(10))

    except Exception as e:
        st.error(f"Error processing sheet: {e}")
