def filter_universe(symbols, meta):
    """
    meta: dict[symbol] -> {price, market_cap, avg_volume)
    """

    return [
        s
        for s in symbols
        if meta[s]["price"] > 5 and meta[s]["avg_volume"] > 1_000_000
    ]
