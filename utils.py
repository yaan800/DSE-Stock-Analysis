import pandas as pd

# --- Prepare raw sheet data ---
def prepare_data(df):
    # Ensure at least 7 columns
    if df.shape[1] < 7:
        raise ValueError("Sheet has fewer than 7 columns, skipping.")

    # Assign column names
    df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']

    # Convert numeric columns
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert Date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    return df

# --- Bollinger Bands ---
def calculate_bollinger(df, period=20, std=2):
    df['BB_Mid'] = df['Close'].rolling(period).mean()
    df['BB_Std'] = df['Close'].rolling(period).std()
    df['BB_Upper'] = df['BB_Mid'] + std * df['BB_Std']
    df['BB_Lower'] = df['BB_Mid'] - std * df['BB_Std']
    df.drop(columns=['BB_Std'], inplace=True)
    return df

# --- Moving Averages ---
def calculate_ma(df):
    df['50MA'] = df['Close'].rolling(50).mean()
    df['150MA'] = df['Close'].rolling(150).mean()
    df['200MA'] = df['Close'].rolling(200).mean()
    return df

# --- Mike Minervini Conditions ---
def check_minervini(df):
    df = calculate_ma(df)
    # Condition: 50MA > 150MA > 200MA AND Close > 50MA
    df['Minervini_Buy'] = (
        (df['50MA'] > df['150MA']) &
        (df['150MA'] > df['200MA']) &
        (df['Close'] > df['50MA'])
    )
    return df
