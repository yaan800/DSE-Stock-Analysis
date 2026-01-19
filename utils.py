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
    Reads uploaded Excel without headers.
    Assigns default column names based on number of columns.
    """
    df = pd.read_excel(uploaded_file, header=None)  # no header in file

    # Generate default column names
    col_count = df.shape[1]
    default_cols = []
    if col_count >= 7:
        default_cols = ['Ticker','Date','Open','High','Low','Close','Volume']
        # Add extra columns if exist
        for i in range(7, col_count):
            default_cols.append(f'Extra_{i-6}')
    else:
        # If less than 7 columns, name them generically
        default_cols = [f'Col_{i+1}' for i in range(col_count)]

    df.columns = default_cols

    # Ensure Ticker column exists
    if 'Ticker' not in df.columns:
        df.rename(columns={df.columns[0]: 'Ticker'}, inplace=True)

    # Strip strings just in case
    df['Ticker'] = df['Ticker'].astype(str).str.strip()

    tickers = df['Ticker'].unique()
    all_data = {t: df[df['Ticker']==t].copy() for t in tickers}

    return all_data, 'Ticker'



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
