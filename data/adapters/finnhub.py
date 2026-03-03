"""
Finnhub Market Data Adapter

Market data via Finnhub API.
Supports US and HK markets with better rate limits than Yahoo.

Sign up at https://finnhub.io/ for free API key.

Usage:
    FINNHUB_API_KEY=your_key python scripts/test_finnhub.py
"""
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import finnhub
import pandas as pd

import config
from data.normalize import PriceData


class FinnhubFetcher:
    """
    Fetches market data from Finnhub.
    
    Provides:
    - US and HK stock data
    - Better rate limits than Yahoo (60 calls/min on free tier)
    - Candlestick, tickers, company info
    
    Environment variables:
    - FINNHUB_API_KEY: Your Finnhub API key
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Finnhub fetcher.
        
        Args:
            api_key: Finnhub API key (or set via FINNHUB_API_KEY env)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("FINNHUB_API_KEY", "")
        self.timeout = timeout
        self._client = None
        
        self.rate_limit_remaining = 60
        self.rate_limit_reset = datetime.now()
    
    @property
    def client(self) -> Optional[finnhub.Client]:
        """Lazy initialization of Finnhub client."""
        if self._client is None and self.api_key:
            self._client = finnhub.Client(api_key=self.api_key)
        return self._client
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def _check_rate_limit(self) -> bool:
        """Check if we can make a request."""
        if self.rate_limit_remaining <= 0:
            if datetime.now() >= self.rate_limit_reset:
                self.rate_limit_remaining = 60
                return True
            return False
        return True
    
    def fetch_candles(
        self,
        symbol: str,
        resolution: str = "5",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch candlestick data.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', '0700.HK')
            resolution: Candle resolution (1, 5, 15, 30, 60, D, W, M)
            start: Start datetime
            end: End datetime
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if not self.is_configured():
            print(f"  [WARN] Finnhub not configured. Set FINNHUB_API_KEY")
            return None
        
        if not self._check_rate_limit():
            wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                print(f"  [RATE LIMIT] Finnhub rate limited. Wait {wait_time:.0f}s")
                return None
        
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(days=1)
        
        try:
            data = self.client.stock_candles(
                symbol,
                resolution,
                int(start.timestamp()),
                int(end.timestamp())
            )
            
            self.rate_limit_remaining -= 1
            
            if data.get('s') == 'no_data':
                print(f"  [WARN] No data for {symbol}")
                return None
            
            if data.get('s') != 'ok':
                print(f"  [ERROR] API error for {symbol}: {data}")
                return None
            
            if not data.get('t'):
                print(f"  [WARN] No timestamp data for {symbol}")
                return None
            
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['t'], unit='s'),
                'Open': data['o'],
                'High': data['h'],
                'Low': data['l'],
                'Close': data['c'],
                'Volume': data['v']
            })
            
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except finnhub.FinnhubAPIException as e:
            if e.status_code == 403:
                print(f"  [ERROR] No access to candles for {symbol}. API key may not support this endpoint.")
            else:
                print(f"  [ERROR] Failed to fetch {symbol}: {e}")
            return None
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {symbol}: {e}")
            return None
    
    def fetch_single(
        self,
        symbol: str,
        resolution: str = "5"
    ) -> Optional[PriceData]:
        """
        Fetch data for a single symbol.
        
        Args:
            symbol: Stock symbol
            resolution: Resolution (5 = 5min, 60 = 1hr, D = daily)
            
        Returns:
            PriceData object or None
        """
        df = self.fetch_candles(symbol, resolution)
        
        if df is None or df.empty:
            return None
        
        return PriceData(
            symbol=symbol,
            df=df,
            last_updated=datetime.now(),
            period="1d",
            interval=f"{resolution}min"
        )
    
    def fetch_batch(
        self,
        symbols: List[str],
        resolution: str = "5"
    ) -> Dict[str, PriceData]:
        """
        Fetch data for multiple symbols.
        
        Note: Finnhub doesn't support batch, so we fetch sequentially.
        
        Args:
            symbols: List of stock symbols
            resolution: Resolution
            
        Returns:
            Dictionary mapping symbol -> PriceData
        """
        results = {}
        
        for symbol in symbols:
            price_data = self.fetch_single(symbol, resolution)
            
            if price_data:
                results[symbol] = price_data
            
            if not self._check_rate_limit():
                wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
                if wait_time > 0:
                    print(f"  [RATE LIMIT] Waiting {wait_time:.0f}s...")
                    time.sleep(wait_time)
            else:
                time.sleep(0.5)
        
        print(f"  -> Fetched {len(results)}/{len(symbols)} symbols via Finnhub")
        
        return results
    
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
        
        try:
            quote = self.client.quote(symbol)
            self.rate_limit_remaining -= 1
            return quote
            
        except finnhub.FinnhubAPIException as e:
            print(f"  [ERROR] Failed to get quote for {symbol}: {e}")
        except Exception as e:
            print(f"  [ERROR] Failed to get quote for {symbol}: {e}")
        
        return None
    
    def get_company_profile(self, symbol: str) -> Optional[dict]:
        """
        Get company profile information.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with company info
        """
        if not self.is_configured():
            return None
        
        try:
            profile = self.client.company_profile2(symbol)
            self.rate_limit_remaining -= 1
            
            if not profile:
                return None
            
            return profile
            
        except finnhub.FinnhubAPIException as e:
            print(f"  [ERROR] Failed to get profile for {symbol}: {e}")
        except Exception as e:
            print(f"  [ERROR] Failed to get profile for {symbol}: {e}")
        
        return None


def fetch_with_finnhub(
    symbols: List[str],
    api_key: Optional[str] = None,
    resolution: str = "5"
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to fetch prices via Finnhub.
    
    Args:
        symbols: List of stock symbols
        api_key: Finnhub API key
        resolution: Resolution (5 = 5min)
        
    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    fetcher = FinnhubFetcher(api_key=api_key)
    results = fetcher.fetch_batch(symbols, resolution=resolution)
    return {symbol: pd_data.df for symbol, pd_data in results.items()}
