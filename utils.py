import pandas as pd
import pandas_ta as ta


def get_dse_data(tickers):
    all_data = {}
    for t in tickers:
        df = DSE.get_historical(t, period='1y')  # daily OHLCV
        all_data[t] = df
    return all_data

def minervini_stage2(df):
    close = df['close']
    ma50 = close.rolling(50).mean()
    ma150 = close.rolling(150).mean()
    ma200 = close.rolling(200).mean()
    low52 = close[-252:].min()
    latest = close.iloc[-1]
    cond = (latest > ma150.iloc[-1]) and (latest > ma200.iloc[-1]) and \
           (ma50.iloc[-1] > ma150.iloc[-1]) and (latest > 1.3 * low52)
    return cond

def bollinger_signal(df):
    bb = ta.bbands(df['close'], length=20, std=2)
    last = df.iloc[-1]
    return last['close'] < bb['BBL_20_2.0'].iloc[-1]

def relative_strength(df, index_df):
    stock_return = df['close'].pct_change(252).iloc[-1]*0.4 + df['close'].pct_change(63).iloc[-1]*0.6
    index_return = index_df['close'].pct_change(252).iloc[-1]*0.4 + index_df['close'].pct_change(63).iloc[-1]*0.6
    return stock_return / index_return
