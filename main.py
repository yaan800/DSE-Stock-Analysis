import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler
from utils import get_dse_data, minervini_stage2, bollinger_signal, rel_strength, send_volume_alert

st.set_page_config(page_title="DSE Stock Analysis", layout="wide")
st.title("📊 DSE Stock Analysis Dashboard")

# ---------------------------
# Upload Excel
# ---------------------------
uploaded_file = st.file_uploader("Upload your DSE OHLCV Excel sheet", type=["xlsx", "xls", "csv"])

if uploaded_file:
    all_data = get_dse_data(uploaded_file)
    tickers = list(all_data.keys())
    st.sidebar.write(f"✅ Loaded {len(tickers)} tickers")

    # ---------------------------
    # Show Dashboard
    # ---------------------------
    st.subheader("Ticker Data Preview (first 5 tickers)")
    for t in tickers[:5]:
        st.write(f"### {t}")
        st.dataframe(all_data[t].tail())

    st.subheader("Signals Preview (first 5 tickers)")
    for t in tickers[:5]:
        st.write(f"{t} Minervini Stage 2:", minervini_stage2(all_data[t]))
        st.write(f"{t} Bollinger Signal:", bollinger_signal(all_data[t]))
        st.write(f"{t} Relative Strength:", rel_strength(all_data[t]))

    # ---------------------------
    # Scheduler for Volume Alerts
    # ---------------------------
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: send_volume_alert(all_data),
        'cron',
        hour=[11,12,13,14],
        minute=0,
        timezone='Asia/Dhaka'
    )
    scheduler.start()
    st.success("✅ Volume alert scheduler is running (11 AM, 12 PM, 1 PM, 2 PM BD Time)")
else:
    st.info("Please upload an Excel sheet to start analysis.")
