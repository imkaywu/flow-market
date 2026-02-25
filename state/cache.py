from collections import defaultdict, deque

from data.normalize import Bar
from typing import Deque


class RollingCache:
    def __init__(self, max_bars: int = 500):
        self.data: dict[str, Deque[Bar]] = defaultdict(
            lambda: deque(maxlen=max_bars)
        )

    def add(self, bar: Bar):
        self.data[bar.symbol].append(bar)

    def get(self, symbol: str) -> list[Bar]:
        return list(self.data[symbol])

    def ready(self, symbol: str, min_bars: int = 30) -> bool:
        return len(self.data[symbol]) >= min_bars
