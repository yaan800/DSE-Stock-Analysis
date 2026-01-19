import pandas as pd
from io import BytesIO

def get_dse_data(file) -> tuple[dict, list]:
    """
    Reads an uploaded Excel or CSV file with DSE data (no headers)
    and returns a dictionary of DataFrames for each ticker/sector row.
    
    file: Uploaded file object from Streamlit
    Returns: (all_data, tickers_list)
    """
    # Detect file type
    if str(file).endswith(".csv"):
        df = pd.read_csv(file, header=None)
    else:
        df = pd.read_excel(file, header=None)

    all_data = {}
    tickers_list = []

    for idx, row in df.iterrows():
        # First column is ticker/sector name
        name = str(row[0]).strip()
        if not name:
            continue

        # The next columns: date, open, high, low, close, volume
        try:
            # Convert numeric columns safely
            date = pd.to_datetime(row[1])
            o = float(row[2])
            h = float(row[3])
            l = float(row[4])
            c = float(row[5])
            v = float(row[6])
        except (ValueError, IndexError):
            # Skip rows like "IT Sector", "Bank", "DSEX", etc.
            continue

        # Save as single-row DataFrame
        all_data[name] = pd.DataFrame({
            'Date': [date],
            'Open': [o],
            'High': [h],
            'Low': [l],
            'Close': [c],
            'Volume': [v]
        })
        tickers_list.append(name)

    if not all_data:
        raise ValueError("No valid ticker/stock rows found in uploaded file!")

    return all_data, tickers_list
