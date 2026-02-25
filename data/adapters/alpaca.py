"""
Alpaca Market Data Adapter (using alpaca-py SDK)

Real-time US market data via Alpaca API.

Sign up at https://alpaca.markets/ for free API keys.

Usage:
    export ALPACA_API_KEY=your_key
    export ALPACA_SECRET_KEY=your_secret
    python scripts/test_alpaca.py
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd

from data.normalize import PriceData

# Try to import alpaca-py
try:
    from alpaca.data.enums import DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    HAS_ALPACA = True
except ImportError:
    HAS_ALPACA = False


class AlpacaFetcher:
    """Fetches market data from Alpaca using the official SDK."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.environ.get("ALPACA_API_KEY", "")
        self.secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self.timeout = timeout
        self.client = None
        
        if self.is_configured():
            try:
                self.client = StockHistoricalDataClient(
                    self.api_key, self.secret_key
                )
            except Exception as e:
                print(f"  [ERROR] Failed to initialize Alpaca client: {e}")
    
    def is_configured(self) -> bool:
        """Check if API keys are configured."""
        return bool(self.api_key and self.secret_key and HAS_ALPACA)
    
    def _get_timeframe(self, timeframe: str) -> TimeFrame:
        """Convert timeframe string to TimeFrame object."""
        tf_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "30Min": TimeFrame(30, TimeFrameUnit.Minute),
            "1H": TimeFrame(1, TimeFrameUnit.Hour),
            "1D": TimeFrame(1, TimeFrameUnit.Day),
        }
        return tf_map.get(timeframe, TimeFrame(5, TimeFrameUnit.Minute))
    
    def fetch_single(
        self,
        symbol: str,
        timeframe: str = "5Min",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> Optional[PriceData]:
        """Fetch bars for a single symbol."""
        if not self.is_configured():
            print(f"  [WARN] Alpaca not configured or alpaca-py not installed")
            return None
        
        if end is None:
            end = datetime.now(timezone.utc)
        if start is None:
            start = end - timedelta(days=1)
        
        try:
            tf = self._get_timeframe(timeframe)
            
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=tf,
                start=start,
                end=end,
                limit=limit,
                feed=DataFeed.IEX,  # Use IEX (free)
            )
            
            bars = self.client.get_stock_bars(request)
            df = bars.df
            
            if df is None or df.empty:
                print(f"  [WARN] No data for {symbol}")
                return None
            
            # Reset index and rename columns
            df = df.reset_index()
            
            # Standardize column names
            column_map = {
                'symbol': 'Symbol',
                'timestamp': 'timestamp',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
            }
            df = df.rename(columns=column_map)
            
            return PriceData(
                symbol=symbol,
                df=df,
                last_updated=datetime.now(),
                period=timeframe,
                interval=timeframe,
            )
            
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {symbol}: {e}")
            return None
    
    def fetch_batch(
        self, symbols: List[str], timeframe: str = "5Min", limit: int = 100
    ) -> Dict[str, PriceData]:
        """Fetch bars for multiple symbols."""
        if not self.is_configured():
            print(f"  [WARN] Alpaca not configured")
            return {}
        
        results = {}
        
        try:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=1)
            
            tf = self._get_timeframe(timeframe)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=tf,
                start=start,
                end=end,
                limit=limit,
                feed=DataFeed.IEX,  # Use IEX (free)
            )
            
            bars = self.client.get_stock_bars(request)
            
            if bars.df is None or bars.df.empty:
                print(f"  [WARN] No data returned")
                return {}
            
            df = bars.df
            
            # Handle MultiIndex (symbol, timestamp)
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0)
            
            # Standardize column names
            
            # Standardize column names
            column_map = {
                'symbol': 'Symbol',
                'timestamp': 'timestamp',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
            }
            df = df.rename(columns=column_map)
            
            # Process each symbol - use 'symbol' (lowercase) for filtering
            for symbol in symbols:
                try:
                    # Try both lowercase and capitalized column names
                    if 'symbol' in df.columns:
                        symbol_data = df[df['symbol'] == symbol].copy()
                    elif 'Symbol' in df.columns:
                        symbol_data = df[df['Symbol'] == symbol].copy()
                    else:
                        print(f"  [WARN] No 'symbol' column in data")
                        continue
                    
                    if symbol_data.empty:
                        print(f"  [WARN] No data for {symbol}")
                        continue
                    
                    symbol_data.reset_index(inplace=True)
                    
                    results[symbol] = PriceData(
                        symbol=symbol,
                        df=symbol_data,
                        last_updated=datetime.now(),
                        period=timeframe,
                        interval=timeframe,
                    )
                except Exception as e:
                    print(f"  [ERROR] Error processing {symbol}: {e}")
                    continue
            
            print(f"  -> Fetched {len(results)}/{len(symbols)} symbols via Alpaca")
            
        except Exception as e:
            print(f"  [ERROR] Batch fetch failed: {e}")
        
        return results
    
    def get_latest_quote(self, symbol: str) -> Optional[dict]:
        """Get latest quote for a symbol."""
        if not self.is_configured():
            return None
        
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self.client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                q = quotes[symbol]
                return {
                    'bid': q.bid_price,
                    'ask': q.ask_price,
                    'bid_size': q.bid_size,
                    'ask_size': q.ask_size,
                }
            
        except Exception as e:
            print(f"  [ERROR] Failed to get quote for {symbol}: {e}")
        
        return None


def fetch_with_alpaca(
    symbols: List[str],
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    timeframe: str = "5Min"
) -> Dict[str, pd.DataFrame]:
    """Convenience function to fetch prices via Alpaca."""
    fetcher = AlpacaFetcher(api_key=api_key, secret_key=secret_key)
    results = fetcher.fetch_batch(symbols, timeframe=timeframe)
    return {symbol: pd_data.df for symbol, pd_data in results.items()}
