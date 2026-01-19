import pandas as pd
import pandas_ta as ta
from datetime import datetime

# -----------------------------
# Data Cleaning and Preparation
# -----------------------------
def prepare_data(df):
    """
    Cleans and formats raw Excel sheet data.
    Keeps only valid OHLCV rows and converts numeric columns.
    """
    # Only keep rows with at least 7 columns
    df = df.dropna(thresh=7)
    
    # Assign column names
    df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    # Convert numeric columns
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with invalid numeric data
    df = df.dropna(subset=['Close', 'Volume'])
    df = df[(df['Close'] > 0) & (df['Volume'] > 0)]
    
    # Convert Date column
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    except:
        df['Date'] = pd.Timestamp.today()
    
    df = df.reset_index(drop=True)
    return df

# -----------------------------
# Bollinger Bands
# -----------------------------
def bollinger_signal(df, length=20, std=2):
    """
    Adds Bollinger Bands to dataframe and returns Buy signals.
    """
    df['BB_upper'] = df['Close'].rolling(length).mean() + std * df['Close'].rolling(length).std()
    df['BB_lower'] = df['Close'].rolling(length).mean() - std * df['Close'].rolling(length).std()
    df['BB_signal'] = df['Close'] < df['BB_lower']  # True = Buy signal
    return df

# -----------------------------
# Minervini Stage 2 Screener
# -----------------------------
def minervini_stage2(df):
    """
    Filters dataframe for Stage 2 Trend Template:
    Price > 150 & 200 day MA
    50 day MA > 150 & 200 day MA
    Price at least 30% above 52-week low
    """
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA150'] = df['Close'].rolling(150).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    df['52w_low'] = df['Close'].rolling(252).min()
    df['52w_high'] = df['Close'].rolling(252).max()
    
    df['Stage2'] = (
        (df['Close'] > df['MA150']) &
        (df['Close'] > df['MA200']) &
        (df['MA50'] > df['MA150']) &
        (df['MA50'] > df['MA200']) &
        (df['Close'] > 1.3 * df['52w_low'])
    )
    
    return df

# -----------------------------
# RSI and EMA Crossovers
# -----------------------------
def add_technical_indicators(df):
    df['RSI14'] = ta.rsi(df['Close'], length=14)
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['EMA200'] = ta.ema(df['Close'], length=200)
    return df
