"""
Yahoo Finance Market Data Adapter

Market data via Yahoo Finance (yfinance).
Supports US and HK markets.

Note: Yahoo Finance has strict rate limits. Use delays between requests
or consider Finnhub/Alpaca for production use.

Usage:
    python scripts/test_yahoo.py
"""
import time
from datetime import datetime
from typing import List, Optional

import pandas as pd
import yfinance as yf
from yfinance import exceptions as yf_exceptions

from data.normalize import Bar, PriceData


class YahooAdapter:
    source = "yahoo"
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize Yahoo adapter.
        
        Args:
            max_retries: Max retry attempts on rate limit
            retry_delay: Delay between retries (seconds)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _download_with_retry(
        self, 
        symbol: str, 
        interval: str = "5m", 
        period: str = "1d",
        progress: bool = False
    ) -> Optional[pd.DataFrame]:
        """Download data with retry logic for rate limits."""
        for attempt in range(self.max_retries):
            try:
                df = yf.download(
                    symbol, 
                    interval=interval, 
                    period=period, 
                    progress=progress,
                    auto_adjust=True
                )
                
                if df.empty:
                    if attempt < self.max_retries - 1:
                        print(f"  [RETRY] Empty data for {symbol}, retrying...")
                        time.sleep(self.retry_delay)
                        continue
                    return None
                
                return df
                
            except yf_exceptions.YFRateLimitError as e:
                wait_time = self.retry_delay * (attempt + 1)
                print(f"  [RATE LIMIT] {symbol}: {e}")
                print(f"  [WAIT] Waiting {wait_time}s before retry ({attempt + 1}/{self.max_retries})...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"  [ERROR] Failed to fetch {symbol}: {e}")
                return None
        
        print(f"  [FAILED] Max retries exceeded for {symbol}")
        return None
    
    def fetch_latest_bar(
        self, 
        symbols: List[str], 
        interval: str = "5m", 
        period: str = "1d"
    ) -> List[Bar]:
        """Fetch latest bars for multiple symbols."""
        bars = []
        
        for i, symbol in enumerate(symbols):
            print(f"  Fetching {symbol}...")
            df = self._download_with_retry(symbol, interval, period)
            
            if df is None or df.empty:
                continue
            
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
            
            # Rate limit protection - delay between symbols
            if i < len(symbols) - 1:
                time.sleep(1)
        
        return bars
    
    def fetch_single(
        self, 
        symbol: str, 
        interval: str = "5m", 
        period: str = "1d"
    ) -> Optional[PriceData]:
        """Fetch data for a single symbol."""
        df = self._download_with_retry(symbol, interval, period)
        
        if df is None or df.empty:
            return None
        
        return PriceData(
            symbol=symbol,
            df=df,
            last_updated=datetime.now(),
            period=period,
            interval=interval
        )
    
    def fetch_batch(
        self, 
        symbols: List[str], 
        interval: str = "5m", 
        period: str = "1d"
    ) -> dict:
        """Fetch data for multiple symbols."""
        results = {}
        
        for symbol in symbols:
            price_data = self.fetch_single(symbol, interval, period)
            if price_data:
                results[symbol] = price_data
        
        return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    adapter = YahooAdapter()
    
    print("="*60)
    print("Yahoo Finance Data Fetch Test")
    print("="*60)
    
    # Test US stocks
    us_symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"\nFetching US: {us_symbols}")
    print("-"*40)
    bars_us = adapter.fetch_latest_bar(us_symbols)
    print(f"Fetched {len(bars_us)} bars from US stocks")
    
    # Test HK stocks  
    hk_symbols = ["0700.HK", "9988.HK"]
    print(f"\nFetching HK: {hk_symbols}")
    print("-"*40)
    bars_hk = adapter.fetch_latest_bar(hk_symbols)
    print(f"Fetched {len(bars_hk)} bars from HK stocks")
    
    print("\n" + "="*60)
    print("Results")
    print("="*60)
    
    if bars_us:
        print(f"\nUS Sample (last 3):")
        for bar in bars_us[-3:]:
            print(f"  {bar.symbol}: ${bar.close:.2f} (vol: {bar.volume:,})")
    
    if bars_hk:
        print(f"\nHK Sample (last 3):")
        for bar in bars_hk[-3:]:
            print(f"  {bar.symbol}: ${bar.close:.2f} (vol: {bar.volume:,})")
    
    if not bars_us and not bars_hk:
        print("\n[FAILED] No data fetched - likely rate limited")
        print("Try:")
        print("  1. Wait a few minutes before retrying")
        print("  2. Use Finnhub or Alpaca instead")
