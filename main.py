import streamlit as st
import pandas as pd
import io
from utils import prepare_data, bollinger_signal, minervini_stage2, add_technical_indicators

st.set_page_config(page_title="DSE Stock Analysis", layout="wide")
st.title("📊 DSE Stock Analysis - Technical Analysis Tool")

# -----------------------------
# Upload Excel File
# -----------------------------
uploaded_file = st.file_uploader("Upload your DSE Excel file", type=["xlsx"])
if uploaded_file:
    try:
        in_memory_file = io.BytesIO(uploaded_file.read())
        xls = pd.ExcelFile(in_memory_file)
        sheet_list = xls.sheet_names
        
        selected_sheet = st.selectbox("Select Sheet (Date)", sheet_list)
        df_raw = pd.read_excel(in_memory_file, sheet_name=selected_sheet, header=None)
        
        # Prepare Data
        df = prepare_data(df_raw)
        
        # Show Raw & Cleaned Data
        st.subheader("✅ Cleaned Stock Data")
        st.dataframe(df)
        
        # Bollinger Bands
        df = bollinger_signal(df)
        
        # Minervini Stage 2
        df = minervini_stage2(df)
        
        # Additional Indicators
        df = add_technical_indicators(df)
        
        st.subheader("📈 Technical Indicators and Signals")
        st.dataframe(df[['Ticker', 'Close', 'Volume', 'BB_lower', 'BB_signal', 'MA50', 'MA150', 'MA200', 'Stage2', 'RSI14', 'EMA9', 'EMA21', 'EMA50', 'EMA200']])
        
        # Optional: Save signals to CSV
        if st.button("Save Signals to CSV"):
            df.to_csv("dse_signals.csv", index=False)
            st.success("Signals saved as dse_signals.csv")
        
    except Exception as e:
        st.error(f"Error processing Excel: {e}")
