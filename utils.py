import pandas as pd
import streamlit as st

def read_excel_safely(file):
    """
    Reads all sheets from an Excel file safely.
    Skips sheets that cause errors.
    Returns a dictionary of {sheet_name: DataFrame}.
    """
    try:
        xls = pd.ExcelFile(file, engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
        return {}

    all_sheets = {}
    for sheet_name in xls.sheet_names:
        try:
            # Read sheet without headers
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None, engine='openpyxl')
            all_sheets[sheet_name] = df
        except Exception as e:
            st.warning(f"Skipped sheet '{sheet_name}' due to error: {e}")
            continue

    return all_sheets


def process_sheet(df):
    """
    Processes a single sheet into a structured DataFrame.
    Assumes columns: Name, Date, Open, High, Low, Close, Volume
    """
    if df.shape[1] < 7:
        # Not enough columns
        st.warning("Sheet has fewer than 7 columns, skipping.")
        return None

    df = df.iloc[:, :7]  # Only first 7 columns
    df.columns = ['Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']

    # Convert numeric columns
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert Date column
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)

    return df
