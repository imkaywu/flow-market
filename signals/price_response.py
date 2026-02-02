def muted_prices(df, lookback=6):
    returns = df["close"].pct_change(lookback).iloc[-1]
    return abs(returns) < 0.005
