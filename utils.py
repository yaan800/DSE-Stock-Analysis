import pandas as pd
import numpy as np

# -------------------------------------------------
# Load Excel (multiple sheets → clean dataframe)
# -------------------------------------------------
def load_excel_data(uploaded_file):

    xls = pd.ExcelFile(uploaded_file)

    # First sheet contains desired stock universe
    ref_df = pd.read_excel(xls, sheet_name=0, header=None)
    desired_stocks = (
        ref_df.iloc[:, 0]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    all_rows = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)

        if df.shape[1] < 7:
            continue

        df = df.iloc[:, :7]
        df.columns = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]

        df["Ticker"] = df["Ticker"].astype(str).str.strip()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce")

        df = df[
            df["Ticker"].isin(desired_stocks) &
            df["Date"].notna() &
            df["Close"].notna()
        ]

        if not df.empty:
            all_rows.append(df)

    if not all_rows:
        raise ValueError("No valid stock data found in Excel.")

    full_df = pd.concat(all_rows, ignore_index=True)
    full_df = full_df.sort_values(["Ticker", "Date"])

    return full_df


# -------------------------------------------------
# Bollinger Bands (20)
# -------------------------------------------------
def add_bollinger(df, window=20):
    df = df.sort_values("Date").copy()

    # Use close only
    close = df["Close"]

    mid = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std(ddof=0)

    df["BB_MID"] = mid
    df["BB_UPPER"] = mid + 2 * std
    df["BB_LOWER"] = mid - 2 * std

    return df



# -------------------------------------------------
# Minervini Stage 2 (Simplified)
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


def to_weekly(df):
    df = df.sort_values("Date").copy()

    weekly = (
        df.set_index("Date")
        .resample("W-FRI")
        .agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        })
        .dropna()
        .reset_index()
    )

    weekly["Ticker"] = df["Ticker"].iloc[0]
    return weekly
