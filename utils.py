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
    """Add Bollinger Bands and buy/sell signals"""
    df = df.copy()
    df['BB_upper'] = df['Close'].rolling(length).mean() + std*df['Close'].rolling(length).std()
    df['BB_lower'] = df['Close'].rolling(length).mean() - std*df['Close'].rolling(length).std()
    df['BB_signal'] = df['Close'] < df['BB_lower']
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
