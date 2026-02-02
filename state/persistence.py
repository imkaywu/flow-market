from datetime import datetime

watchlist = {}


def update_watchlist(symbol, score):
    now = datetime.utcnow()
    watchlist[symbol] = {
        "score": score,
        "first_seen": watchlist.get(symbol, {}).get("first_seen", now),
        "last_seen": now,
    }
