import pandas as pd

def get_dse_data(file_path):
    """
    Reads a DSE file (Excel/CSV/text), handles missing headers,
    filters out indices/sectors, and returns clean OHLCV data per ticker.
    
    Args:
        file_path (str): Path to Excel/CSV file.
    
    Returns:
        all_data (dict): Dictionary with ticker as key and DataFrame as value.
        ticker_list (list): List of valid tickers.
    """
    # Try reading Excel first, then CSV fallback
    try:
        df = pd.read_excel(file_path, header=None)
    except Exception:
        df = pd.read_csv(file_path, header=None, sep='\t', engine='python')

    # Assign columns (adjust if more than 7 columns)
    col_count = df.shape[1]
    if col_count >= 7:
        df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'] + [f'Extra_{i}' for i in range(7, col_count)]
    else:
        df.columns = [f'Col_{i+1}' for i in range(col_count)]

    # Convert numeric columns safely
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where Close is NaN (these are sectors/indices/mutual funds)
    df_clean = df[df['Close'].notna()].copy()

    if df_clean.empty:
        raise ValueError("No valid ticker rows found with numeric OHLCV data.")

    # Standardize Date column
    if 'Date' in df_clean.columns:
        df_clean['Date'] = pd.to_datetime(df_clean['Date'], errors='coerce')

    # Create dictionary per ticker
    tickers = df_clean['Ticker'].unique()
    all_data = {t: df_clean[df_clean['Ticker']==t].copy() for t in tickers}

    return all_data, tickers
