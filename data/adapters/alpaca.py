from data.normalize import Bar

from alpaca.data.live import StockDataStream


class AlpacaAdapter:
    source = "alpaca"

    def __init__(self, api_key, secret):
        self.stream = StockDataStream(api_key, secret)

    def subscribe(self, symbols, on_bar):
        for symbol in symbols:
            self.stream.subscribe_bars(
                lambda bar: on_bar(
                    Bar(
                        symbol=bar.symbol,
                        timestamp=bar.timestamp,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                        source=self.source,
                    )
                ),
                symbol,
            )

        self.stream.run()
