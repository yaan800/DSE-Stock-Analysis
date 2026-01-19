import pandas as pd
import pandas_ta as ta

# -------------------------------
# Excel Processing Functions
# -------------------------------

def read_excel_safely(file):
    """Read all sheets from Excel safely."""
    try:
        xls = pd.ExcelFile(file, engine='openpyxl')
    except Exception as e:
        return {}, f"Failed to read Excel: {e}"

    all_sheets = {}
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None, engine='openpyxl')
            all_sheets[sheet_name] = df
        except Exception as e:
            continue
    return all_sheets, None


def process_sheet(df):
    """Process sheet into structured DataFrame"""
    if df.shape[1] < 7:
        return None  # sheet too short
    df = df.iloc[:, :7]  # take first 7 columns only
    df.columns = ['Ticker','Date','Open','High','Low','Close','Volume']

    # Convert numeric columns
    for col in ['Open','High','Low','Close','Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)

    return df


# -------------------------------
# Technical Calculations
# -------------------------------

def bollinger_signal(df, length=20, std=2):
    """
    Calculate Bollinger Bands and generate signals when price crosses the bands.
    - df: DataFrame with at least 'Close'
    - length: rolling period
    - std: number of standard deviations
    Returns df with new columns:
        - BB_mid, BB_upper, BB_lower
        - BB_signal (True if Close crosses below lower band)
    """
    df = df.copy()

    # Rolling mean and std
    df['BB_mid'] = df['Close'].rolling(length).mean()
    df['BB_std'] = df['Close'].rolling(length).std()
    df['BB_upper'] = df['BB_mid'] + std * df['BB_std']
    df['BB_lower'] = df['BB_mid'] - std * df['BB_std']

    # Cross below lower band
    df['BB_signal'] = False
    # We only trigger signal when previous close was above lower band and current close is below
    df.loc[(df['Close'].shift(1) > df['BB_lower'].shift(1)) & (df['Close'] < df['BB_lower']), 'BB_signal'] = True

    # Optional: Cross above upper band (sell signal)
    df['BB_sell_signal'] = False
    df.loc[(df['Close'].shift(1) < df['BB_upper'].shift(1)) & (df['Close'] > df['BB_upper']), 'BB_sell_signal'] = True

    # Drop temporary std column
    df.drop(columns=['BB_std'], inplace=True)

    return df

def minervini_stage2(df):
    """Add Mike Minervini Stage 2 Filter"""
    df = df.copy()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA150'] = df['Close'].rolling(150).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    df['52W_low'] = df['Close'].rolling(252).min()
    df['52W_high'] = df['Close'].rolling(252).max()

    df['Stage2'] = (
        (df['Close'] > df['MA150']) &
        (df['Close'] > df['MA200']) &
        (df['MA150'] > df['MA200']) &
        (df['MA50'] > df['MA150']) &
        (df['Close'] > 1.3*df['52W_low']) &
        (df['Close'] <= 1.25*df['52W_high'])
    )
    return df
