from collections import defaultdict

import pandas as pd


class RollingCache:
    def __init__(self):
        self.data = defaultdict(pd.DataFrame)

    def update(self, symbol, new_bars):
        self.data[symbol] = (
            pd.concat([self.data[symbol], new_bars])
            .drop_duplicates("datetime")
            .tail(5000)
        )

    def get(self, symbol):
        return self.data[symbol]
