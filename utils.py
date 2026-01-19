import pandas as pd
import pandas_ta as ta
from email.message import EmailMessage
import smtplib
from datetime import datetime

# ---------------------------
# Read Excel & Prepare Data
# ---------------------------
def get_dse_data(uploaded_file):
    """
    Reads uploaded Excel with columns like:
    Ticker | Date | Open | High | Low | Close | Volume
    Automatically detects ticker column (case-insensitive, strips spaces)
    """
    df = pd.read_excel(uploaded_file)

    # Force all column names to string and strip spaces
    df.columns = df.columns.astype(str).str.strip()

    # Detect Ticker column
    ticker_col = None
    for col in df.columns:
        if str(col).lower() == 'ticker':  # ensure col is string
            ticker_col = col
            break
    if ticker_col is None:
        raise ValueError("Uploaded Excel must have a 'Ticker' column!")

    tickers = df[ticker_col].unique()
    all_data = {t: df[df[ticker_col]==t].copy() for t in tickers}
    return all_data, ticker_col

# ---------------------------
# Minervini Stage 2 Placeholder
# ---------------------------
def minervini_stage2(df):
    """Return True if Stage 2 conditions are met (placeholder)"""
    # Real logic can be added here later
    return False

# ---------------------------
# Bollinger Band Placeholder
# ---------------------------
def bollinger_signal(df):
    """Return 'buy', 'sell', or 'hold' (placeholder)"""
    # Real logic can be added here later
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
def send_volume_alert(all_data, ticker_col, email="yaan800@gmail.com", app_password="uroy gabw lhyx zcaw"):
    """
    Sends email for tickers where current volume exceeds thresholds
    """
    thresholds = [0.5, 0.8, 1.0]  # 50%, 80%, 100%
    alerts = []

    for ticker, df in all_data.items():
        if df.empty or 'Volume' not in df.columns:
            continue
        if len(df) < 2:
            continue  # Need at least 2 days for previous volume
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
