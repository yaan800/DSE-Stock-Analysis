import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import smtplib
from email.message import EmailMessage
from apscheduler.schedulers.background import BackgroundScheduler

from utils import get_dse_data, minervini_stage2, bollinger_signal, relative_strength

# ---------------------------
# User Settings
# ---------------------------
EMAIL = "yaan800@gmail.com"
EMAIL_PASSWORD = "uroygabwlhyxzcaw"  # Your Gmail App Password

# Example DSE tickers (add more later)
tickers = ["GP", "RBLC", "BATBC"]
index_ticker = "DSEX"

# ---------------------------
# Fetch Data
# ---------------------------
st.title("Dhaka Stock Exchange Dashboard (Live Signals)")

st.write("Fetching latest market data...")
all_data = get_dse_data(tickers)
index_data = get_dse_data([index_ticker])[index_ticker]

# ---------------------------
# Analyze Signals
# ---------------------------
summary = []
for t in tickers:
    df = all_data[t]
    stage2 = minervini_stage2(df)
    bb_signal = bollinger_signal(df)
    rs = relative_strength(df, index_data)
    summary.append({
        "Ticker": t,
        "Stage 2": stage2,
        "Bollinger Buy": bb_signal,
        "RS Rank": round(rs, 2)
    })

summary_df = pd.DataFrame(summary)
st.dataframe(summary_df)

# ---------------------------
# Email Alert Function
# ---------------------------
def send_email(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg.set_content(body)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ---------------------------
# Scheduled Volume Alerts
# ---------------------------
def volume_alert_job():
    alerts = []
    for t in tickers:
        df = all_data[t]
        current_vol = df['volume'].iloc[-1]
        prev_vol = df['volume'].iloc[-2]
        if current_vol > 0.8 * prev_vol:
            alerts.append(f"{t}: Volume {current_vol} > 80% of yesterday")
    if alerts:
        send_email("DSE Volume Alerts", "\n".join(alerts))

scheduler = BackgroundScheduler(timezone="Asia/Dhaka")
for hour in [11, 12, 13, 14]:
    scheduler.add_job(volume_alert_job, 'cron', hour=hour, minute=0)
scheduler.start()

st.success("Volume alert schedule set: 11AM, 12PM, 1PM, 2PM (BD Time)")
