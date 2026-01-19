import pandas as pd
import pandas_ta as ta
import numpy as np

# -----------------------------
# Load Excel & Filter Desired Stocks
# -----------------------------
def load_excel_data_filtered(uploaded_file, sheet_name):
    """
    Loads a sheet from Excel, keeps only stocks in the first sheet.
    Handles missing rows/cells and ensures correct columns.
    """
    # Read first sheet to get desired stock list
    xls = pd.ExcelFile(uploaded_file)
    first_sheet = xls.sheet_names[0]
    desired_df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=None, usecols="A")
    desired_stocks = desired_df.iloc[:, 0].dropna().tolist()

    # Read target sheet
    df = pd.read_excel(
        uploaded_file,
        sheet_name=sheet_name,
        header=None,
        usecols="A:G"  # enforce Ticker, Date, Open, High, Low, Close, Volume
    )
    df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']

    # Filter only desired stocks
    df = df[df['Ticker'].isin(desired_stocks)].reset_index(drop=True)

    # Ensure numeric columns are correct
    for col in ['Open','High','Low','Close','Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# -----------------------------
# Bollinger Bands
# -----------------------------
def add_bollinger(df, length=20, std=2):
    """
    Adds Bollinger Bands columns to the dataframe.
    """
    df['BB_MA'] = df['Close'].rolling(length).mean()
    df['BB_Upper'] = df['BB_MA'] + std * df['Close'].rolling(length).std()
    df['BB_Lower'] = df['BB_MA'] - std * df['Close'].rolling(length).std()
    return df

def bollinger_lower_touch(df):
    """
    Returns stocks touching or below the lower Bollinger Band.
    """
    df_touch = df[(df['Close'] <= df['BB_Lower'])]
    return df_touch[['Ticker','Date','Close','BB_Lower']]

# -----------------------------
# Minervini Stage 2
# -----------------------------
def add_minervini_stage2(df):
    """
    Adds a column Stage2 = True if stock passes simplified Minervini rules:
    - Close > 150MA & 200MA
    - 50MA > 150MA
    - Price at least 30% above 52-week low
    - Price within 25% of 52-week high
    """
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA150'] = df['Close'].rolling(150).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    df['52W_Low'] = df['Close'].rolling(252).min()  # approx 1 year
    df['52W_High'] = df['Close'].rolling(252).max()

    conditions = (
        (df['Close'] > df['MA150']) &
        (df['Close'] > df['MA200']) &
        (df['MA50'] > df['MA150']) &
        (df['Close'] > df['52W_Low']*1.3) &
        (df['Close'] > df['52W_High']*0.75)
    )

    df['Stage2'] = conditions
    return df
