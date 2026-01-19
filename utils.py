import pandas as pd
import streamlit as st

# -------------------------------
# Excel Processing Functions
# -------------------------------

def read_excel_safely(file):
    """Read all sheets from Excel safely."""
    try:
        xls = pd.ExcelFile(file, engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
        return {}

    all_sheets = {}
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None, engine='openpyxl')
            all_sheets[sheet_name] = df
        except Exception as e:
            st.warning(f"Skipped sheet '{sheet_name}' due to error: {e}")
            continue
    return all_sheets


def process_sheet(df):
    """Process a single sheet into structured DataFrame"""
    if df.shape[1] < 7:
        st.warning("Sheet has fewer than 7 columns, skipping.")
        return None

    df = df.iloc[:, :7]
    df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']

    # Convert numeric columns
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert Date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)

    return df


def merge_today_data(historical_df, today_file):
    """Merge today’s Excel/CSV with historical data"""
    ext = today_file.name.split('.')[-1]
    if ext == 'csv':
        today_df = pd.read_csv(today_file, header=None)
    else:
        today_df = pd.read_excel(today_file, header=None, engine='openpyxl')

    if today_df.shape[1] < 7:
        st.error("Today's file must have at least 7 columns: Ticker, Date, Open, High, Low, Close, Volume")
        return historical_df

    today_df.columns = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        today_df[col] = pd.to_numeric(today_df[col], errors='coerce')
    today_df['Date'] = pd.to_datetime(today_df['Date'], errors='coerce', dayfirst=True)

    merged = pd.concat([historical_df, today_df], ignore_index=True)
    return merged
