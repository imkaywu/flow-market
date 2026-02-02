import time

from config import SLEEP_SECONDS
from state.cache import RollingCache
from utils import filter_universe

cache = RollingCache()
last_timestamp = None


def scanner_loop(symbols, meta):
    global last_timestamp

    symbols = filter_universe(symbols)

    while market_is_open():
        bars = fetch_latest_bars(symbols, last_timestamp)

        for symbol, new_bars in bars.items():
            cache.update(symbol, new_bars)
            df = cache.get(symbol)

            if len(df) < 50:
                continue

            score = composite_score(df, news_score=get_news_score(symbol))

            if score > 0.6:
                update_watchlist(symbol, score)

            last_timestamp = current_timestamp()
            time.sleep(SLEEP_SECONDS)
