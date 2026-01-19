import pandas as pd
import pandas_ta as ta
from email.message import EmailMessage
import smtplib
from datetime import datetime

# ---------------------------
# DSE Data Functions
# ---------------------------

def get_dse_data(uploaded_file):
    """
    Reads uploaded Excel with columns:
    Ticker | Date | Open | High | Low | Close | Volume
    """
    df = pd.read_excel(uploaded_file)
    tickers = df['Ticker'].unique()
    all_data = {t: df[df['Ticker']==t].copy() for t in tickers}
    return all_data

# ---------------------------
# Minervini Stage 2 Placeholder
# ---------------------------
def minervini_stage2(df):
    """Return True if Stage 2 conditions are met (placeholder)"""
    return False

# ---------------------------
# Bollinger Band Placeholder
# ---------------------------
def bollinger_signal(df):
    """Return 'buy', 'sell', or 'hold' (placeholder)"""
    return 'hold'

# ---------------------------
# Relative Strength Placeholder
# ---------------------------
def rel_strength(df):
    """Return RS score (placeholder)"""
    return 0.0

# ---------------------------
# Email Volume Alerts
# ---------------------------
def send_volume_alert(all_data, email="yaan800@gmail.com", app_password="uroy gabw lhyx zcaw"):
    """
    Sends email for tickers where current volume exceeds thresholds
    """
    thresholds = [0.5, 0.8, 1.0]
    alerts = []

    for ticker, df in all_data.items():
        if df.empty or 'Volume' not in df.columns:
            continue
        prev_vol = df['Volume'].iloc[-2]  # previous day's total
        current_vol = df['Volume'].iloc[-1]  # latest value
        for t in thresholds:
            if current_vol >= t * prev_vol:
                alerts.append(f"{ticker} reached {int(t*100)}% of yesterday's volume")

    if alerts:
        msg = EmailMessage()
        msg['Subject'] = f"DSE Volume Alerts {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg['From'] = email
        msg['To'] = email
        msg.set_content("\n".join(alerts))

        # Send email via Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email, app_password)
            smtp.send_message(msg)
