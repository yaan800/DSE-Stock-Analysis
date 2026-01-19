import pandas as pd
import pandas_ta as ta

# -------------------------------
# DSE Data Handling
# -------------------------------
def get_dse_data(uploaded_file, sheet_name):
    """
    Read a sheet from the uploaded Excel file and return a structured DataFrame.
    Assumes sheet has 7 columns in order: Ticker, Date, Open, High, Low, Close, Volume (no header)
    """
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
        if df.shape[1] < 7:
            raise ValueError(f"Sheet {sheet_name} has fewer than 7 columns, skipping.")

        # Assign column names
        df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']

        # Convert numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # Sort by Ticker + Date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.sort_values(by=['Ticker', 'Date'], inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    except Exception as e:
        raise ValueError(f"Error processing Excel: {e}")


# -------------------------------
# Bollinger Bands
# -------------------------------
def bollinger_signal(df, length=20, std=2):
    """
    Calculate Bollinger Bands and generate buy/sell signals.
    """
    df = df.copy()
    df['BB_mid'] = df['Close'].rolling(length).mean()
    df['BB_std'] = df['Close'].rolling(length).std()
    df['BB_upper'] = df['BB_mid'] + std * df['BB_std']
    df['BB_lower'] = df['BB_mid'] - std * df['BB_std']

    # Buy signal: cross below lower band
    df['BB_buy'] = ((df['Close'].shift(1) > df['BB_lower'].shift(1)) & (df['Close'] < df['BB_lower']))
    # Sell signal: cross above upper band
    df['BB_sell'] = ((df['Close'].shift(1) < df['BB_upper'].shift(1)) & (df['Close'] > df['BB_upper']))

    df.drop(columns=['BB_std'], inplace=True)
    return df


# -------------------------------
# Minervini Stage 2 Screener
# -------------------------------
def minervini_stage2(df):
    """
    Screen for stocks matching Mike Minervini Stage 2 (Trend Template)
    """
    df = df.copy()
    # Calculate moving averages
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA150'] = df['Close'].rolling(150).mean()
    df['MA200'] = df['Close'].rolling(200).mean()

    # Calculate 52-week high/low
    df['52W_High'] = df['Close'].rolling(252).max()
    df['52W_Low'] = df['Close'].rolling(252).min()

    # Minervini Stage 2 conditions
    df['Stage2'] = (
        (df['Close'] > df['MA150']) &
        (df['Close'] > df['MA200']) &
        (df['MA150'] > df['MA200']) &
        (df['MA200'].diff(20) > 0) &   # 1 month uptrend
        (df['MA50'] > df['MA150']) &
        (df['MA50'] > df['MA200']) &
        ((df['Close'] - df['52W_Low']) / df['52W_Low'] >= 0.3) &
        ((df['52W_High'] - df['Close']) / df['52W_High'] <= 0.25)
    )
    return df


# -------------------------------
# Additional Indicators
# -------------------------------
def add_indicators(df):
    """
    Add RSI(14), MFI(14), EMA9/21 & EMA50/200
    """
    df = df.copy()
    df['RSI14'] = ta.rsi(df['Close'], length=14)
    df['MFI14'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
    df['EMA9'] = ta.ema(df['Close'], length=9)
    df['EMA21'] = ta.ema(df['Close'], length=21)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['EMA200'] = ta.ema(df['Close'], length=200)
    return df
