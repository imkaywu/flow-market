"""
Alpha Vantage Market Data Adapter

Market data via Alpha Vantage API.
Supports US stocks with free tier (25 requests/day).

Sign up for free API key at https://www.alphavantage.co/support/#api-key

Usage:
    ALPHAVANTAGE_API_KEY=your_key python scripts/test_alphavantage.py
"""
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from alpha_vantage.timeseries import TimeSeries

from data.normalize import PriceData


class AlphaVantageFetcher:
    """
    Fetches market data from Alpha Vantage.
    
    Provides:
    - US stock data (real-time and historical)
    - 25 API calls/day on free tier
    - Intraday and daily candles
    
    Environment variables:
    - ALPHAVANTAGE_API_KEY: Your Alpha Vantage API key
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        output_format: str = "pandas"
    ):
        """
        Initialize Alpha Vantage fetcher.
        
        Args:
            api_key: Alpha Vantage API key (or set via ALPHAVANTAGE_API_KEY env)
            output_format: Output format ('pandas' or 'json')
        """
        self.api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY", "")
        self.output_format = output_format
        self._client = None
        
        self.rate_limit_remaining = 25
        self.rate_limit_reset = datetime.now()
    
    @property
    def client(self) -> Optional[TimeSeries]:
        """Lazy initialization of Alpha Vantage client."""
        if self._client is None and self.api_key:
            self._client = TimeSeries(key=self.api_key, output_format=self.output_format)
        return self._client
    
    def get_quote(self, symbol: str) -> Optional[dict]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with price info or None
        """
        if not self.is_configured():
            return None
        
        if self.rate_limit_remaining <= 0:
            print(f"  [RATE LIMIT] No more API calls available")
            return None
        
        try:
            df, _ = self.client.get_intraday(symbol=symbol, interval="1min", outputsize="compact")
            self.rate_limit_remaining -= 1
            
            if df is None or df.empty:
                return None
            
            latest = df.iloc[-1]
            return {
                'symbol': symbol,
                'price': float(latest['4. close']),
                'open': float(latest['1. open']),
                'high': float(latest['2. high']),
                'low': float(latest['3. low']),
                'volume': int(latest['5. volume']),
            }
            
        except Exception as e:
            print(f"  [ERROR] Failed to get quote for {symbol}: {e}")
        
        return None
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def fetch_candles(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: str = "compact"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch candlestick data.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'IBM')
            interval: Candle interval (1min, 5min, 15min, 30min, 60min)
            outputsize: Data size ('compact' = 100 days, 'full' = full history)
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if not self.is_configured():
            print(f"  [WARN] Alpha Vantage not configured. Set ALPHAVANTAGE_API_KEY")
            return None
        
        if self.rate_limit_remaining <= 0:
            print(f"  [RATE LIMIT] Alpha Vantage rate limited. 25 requests/day on free tier.")
            return None
        
        try:
            df, meta = self.client.get_intraday(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )
            
            self.rate_limit_remaining -= 1
            
            if df is None or df.empty:
                print(f"  [WARN] No data for {symbol}")
                return None
            
            df = df.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            })
            
            df.index = pd.to_datetime(df.index)
            df.index.name = 'timestamp'
            
            return df
            
        except Exception as e:
            error_msg = str(e)
            if "API call frequency" in error_msg:
                print(f"  [RATE LIMIT] Alpha Vantage rate limit exceeded")
                self.rate_limit_remaining = 0
            else:
                print(f"  [ERROR] Failed to fetch {symbol}: {e}")
            return None
    
    def fetch_daily(
        self,
        symbol: str,
        outputsize: str = "compact"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch daily candlestick data.
        
        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)
            
        Returns:
            DataFrame with daily OHLCV data
        """
        if not self.is_configured():
            print(f"  [WARN] Alpha Vantage not configured. Set ALPHAVANTAGE_API_KEY")
            return None
        
        try:
            df, meta = self.client.get_daily(symbol=symbol, outputsize=outputsize)
            
            self.rate_limit_remaining -= 1
            
            if df is None or df.empty:
                print(f"  [WARN] No daily data for {symbol}")
                return None
            
            df = df.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            })
            
            df.index = pd.to_datetime(df.index)
            df.index.name = 'timestamp'
            
            return df
            
        except Exception as e:
            print(f"  [ERROR] Failed to fetch daily {symbol}: {e}")
            return None
    
    def fetch_single(
        self,
        symbol: str,
        interval: str = "5min"
    ) -> Optional[PriceData]:
        """
        Fetch data for a single symbol.
        
        Args:
            symbol: Stock symbol
            interval: Interval (5min, 1h, daily)
            
        Returns:
            PriceData object or None
        """
        if interval == "daily":
            df = self.fetch_daily(symbol)
        else:
            df = self.fetch_candles(symbol, interval=interval)
        
        if df is None or df.empty:
            return None
        
        return PriceData(
            symbol=symbol,
            df=df,
            last_updated=datetime.now(),
            period="1d" if interval == "daily" else "1d",
            interval=interval
        )
    
    def fetch_batch(
        self,
        symbols: List[str],
        interval: str = "5min"
    ) -> Dict[str, PriceData]:
        """
        Fetch data for multiple symbols.
        
        Note: Alpha Vantage doesn't support batch, so we fetch sequentially.
        Free tier: 25 calls/day
        
        Args:
            symbols: List of stock symbols
            interval: Interval
            
        Returns:
            Dictionary mapping symbol -> PriceData
        """
        results = {}
        
        for symbol in symbols:
            if self.rate_limit_remaining <= 0:
                print(f"  [RATE LIMIT] No more API calls available")
                break
            
            price_data = self.fetch_single(symbol, interval)
            
            if price_data:
                results[symbol] = price_data
            
            time.sleep(12)
        
        print(f"  -> Fetched {len(results)}/{len(symbols)} symbols via Alpha Vantage")
        
        return results


def fetch_with_alphavantage(
    symbols: List[str],
    api_key: Optional[str] = None,
    interval: str = "5min"
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to fetch prices via Alpha Vantage.
    
    Args:
        symbols: List of stock symbols
        api_key: Alpha Vantage API key
        interval: Interval (5min, 1h, daily)
        
    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    fetcher = AlphaVantageFetcher(api_key=api_key)
    results = fetcher.fetch_batch(symbols, interval=interval)
    return {symbol: pd_data.df for symbol, pd_data in results.items()}
