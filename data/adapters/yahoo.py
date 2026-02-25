import yfinance as yf
from data.normalize import Bar


class YahooAdapter:
    source = "yahoo"

    def fetch_latest_bar(self, symbols, interval="5m", period="1d"):
        bars = []
        for symbol in symbols:
            df = yf.download(
                symbol, interval=interval, period=period, progress=False
            )

            for ts, row in df.iterrows():
                bars.append(
                    Bar(
                        symbol=symbol,
                        timestamp=ts.to_pydatetime(),
                        open=row["Open"],
                        high=row["High"],
                        low=row["Low"],
                        close=row["Close"],
                        volume=row["Volume"],
                        source=self.source,
                    )
                )
        return bars


if __name__ == "__main__":
    adapter = YahooAdapter()
    symbols_us = ["AAPL", "NVDA"]
    symbols_hk = ["0700.HK", "9988.HK"]
    bars_us = adapter.fetch_latest_bar(symbols_us)
    bars_hk = adapter.fetch_latest_bar(symbols_hk)

    print(f"US: \n{bars_us}\n HK: \n{bars_hk}")
