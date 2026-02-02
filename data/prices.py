def fetch_latest_bars(symbols, last_timestamp):
    """
    Fetch bars AFTER last_timestamp
    """
    bars = {}
    for s in symbols:
        bars[s] = api.get_intraday(s, start=last_timestamp)
        return bars
