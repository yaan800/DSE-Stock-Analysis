import pandas as pd
import numpy as np



# -------------------------------------------------
# Read Excel and build clean time-series per stock
# -------------------------------------------------
def load_excel_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)

    # First sheet = reference universe of desired stocks
    ref_sheet = xls.sheet_names[0]
    ref_df = pd.read_excel(xls, sheet_name=ref_sheet, header=None)
    desired_stocks = ref_df.iloc[:, 0].dropna().astype(str).str.strip().unique().tolist()

    all_rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)

        # Need at least 7 columns
        if df.shape[1] < 7:
            continue

        # Map columns correctly
        df = df[[0, 1, 2, 3, 4, 5, 6]].copy()
        df.columns = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]

        df["Ticker"] = df["Ticker"].astype(str).str.strip()
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        df = df[
            df["Ticker"].isin(desired_stocks) &
            df["Close"].notna()
        ]

        if df.empty:
            continue

        all_rows.append(df)

    if not all_rows:
        raise ValueError("No valid stock data found in Excel")

    full_df = pd.concat(all_rows, ignore_index=True)
    full_df = full_df.sort_values(["Ticker", "Date"])

    return full_df


# -------------------------------------------------
# Bollinger Bands (20)
# -------------------------------------------------
def add_bollinger(df, window=20):
    df = df.sort_values("Date").copy()
    df["BB_MID"] = df["Close"].rolling(window).mean()
    df["BB_STD"] = df["Close"].rolling(window).std()
    df["BB_UPPER"] = df["BB_MID"] + 2 * df["BB_STD"]
    df["BB_LOWER"] = df["BB_MID"] - 2 * df["BB_STD"]
    return df


# -------------------------------------------------
# Minervini Stage 2 (simplified & correct)
# -------------------------------------------------
def add_minervini_stage2(df):
    df = df.sort_values("Date").copy()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA150"] = df["Close"].rolling(150).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["Stage2"] = (
        (df["Close"] > df["MA50"]) &
        (df["MA50"] > df["MA150"]) &
        (df["MA150"] > df["MA200"])
    )
    return df
