import pandas as pd

def get_dse_data(file) -> tuple[dict, list]:
    """
    Reads an uploaded Excel file with multiple sheets (dates) and no headers.
    Returns a nested dictionary: {ticker: {date: DataFrame}}
    
    file: Uploaded Excel file object
    Returns: (all_data, tickers_list)
    """
    xls = pd.ExcelFile(file)
    all_data = {}
    tickers_set = set()

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        except Exception:
            continue

        for idx, row in df.iterrows():
            name = str(row[0]).strip()
            if not name:
                continue

            # Convert numeric columns safely
            try:
                date = pd.to_datetime(row[1])
                o = float(row[2])
                h = float(row[3])
                l = float(row[4])
                c = float(row[5])
                v = float(row[6])
            except (ValueError, IndexError):
                continue  # skip sectors/aggregate rows

            # Create single-row DataFrame
            df_row = pd.DataFrame({
                'Date': [date],
                'Open': [o],
                'High': [h],
                'Low': [l],
                'Close': [c],
                'Volume': [v]
            })

            # Initialize ticker in dictionary if needed
            if name not in all_data:
                all_data[name] = {}
            all_data[name][sheet_name] = df_row
            tickers_set.add(name)

    if not all_data:
        raise ValueError("No valid ticker rows found across all sheets!")

    tickers_list = sorted(list(tickers_set))
    return all_data, tickers_list
