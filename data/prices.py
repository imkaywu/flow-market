"""
Price Data Fetching

Unified API for fetching price data from Yahoo Finance.
Supports US and HK markets.
"""
import time
from datetime import datetime, time as dt_time
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf
import pandas as pd

import config
from data.normalize import Bar, PriceData


class PriceFetcher:
    """
    Fetches price data from Yahoo Finance.
    
    Supports both US and HK markets.
    """
    
    def __init__(
        self,
        period: str = config.PRICE_PERIOD,
        interval: str = config.PRICE_INTERVAL,
        max_workers: int = 1,
        request_delay: float = config.REQUEST_DELAY_SECONDS
    ):
        """
        Initialize price fetcher.
        
        Args:
            period: yfinance period (1d, 5d, 1mo, etc.)
            interval: yfinance interval (1m, 5m, 15m, 1h, etc.)
            max_workers: Number of parallel workers (1 = sequential)
            request_delay: Delay between requests in seconds
        """
        self.period = period
        self.interval = interval
        self.max_workers = max_workers
        self.request_delay = request_delay
    
    def fetch_single(self, symbol: str) -> Optional[PriceData]:
        """
        Fetch price data for a single symbol with retry logic.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL' or '0700.HK')
            
        Returns:
            PriceData object or None if fetch failed
        """
        last_error = None
        
        for attempt in range(config.MAX_RETRIES):
            try:
                df = yf.download(
                    symbol,
                    period=self.period,
                    interval=self.interval,
                    progress=False,
                    auto_adjust=True
                )
                
                if df.empty:
                    print(f"  [WARN] No data for {symbol}")
                    return None
                
                # Reset index to get timestamp as column
                df = df.reset_index()
                
                # Handle multi-index columns from yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
                
                return PriceData(
                    symbol=symbol,
                    df=df,
                    last_updated=datetime.now(),
                    period=self.period,
                    interval=self.interval
                )
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check if rate limited
                if "rate" in error_str.lower() or "429" in error_str:
                    wait_time = config.RETRY_DELAY_BASE * (2 ** attempt)
                    print(f"  [RATE LIMIT] {symbol}: Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  [ERROR] Failed to fetch {symbol}: {e}")
                    return None
        
        print(f"  [ERROR] Failed to fetch {symbol} after {config.MAX_RETRIES} attempts: {last_error}")
        return None
    
    def fetch_batch(self, symbols: list[str]) -> Dict[str, PriceData]:
        """
        Fetch price data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol -> PriceData
        """
        results = {}
        
        # Initial delay to avoid rate limiting on batch start
        if symbols:
            print(f"  Waiting {self.request_delay}s before fetching...")
            time.sleep(self.request_delay)
        
        if self.max_workers > 1:
            # Parallel fetching
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.fetch_single, symbol): symbol
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        price_data = future.result()
                        if price_data:
                            results[symbol] = price_data
                        time.sleep(self.request_delay)
                    except Exception as e:
                        print(f"  [ERROR] {symbol}: {e}")
        else:
            # Sequential fetching
            for symbol in symbols:
                price_data = self.fetch_single(symbol)
                if price_data:
                    results[symbol] = price_data
                time.sleep(self.request_delay)
        
        return results
    
    def fetch_all_tier1(self) -> Dict[str, PriceData]:
        """Fetch all Tier 1 stocks (US + HK)."""
        all_tier1 = config.US_TIER_1 + config.HK_TIER_1
        return self.fetch_batch(all_tier1)


def fetch_prices(
    symbols: list[str],
    period: str = config.PRICE_PERIOD,
    interval: str = config.PRICE_INTERVAL,
    max_workers: int = 1
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to fetch prices for multiple symbols.
    
    Args:
        symbols: List of stock symbols
        period: yfinance period
        interval: yfinance interval
        max_workers: Number of parallel workers
        
    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    fetcher = PriceFetcher(
        period=period,
        interval=interval,
        max_workers=max_workers
    )
    
    results = fetcher.fetch_batch(symbols)
    
    # Convert PriceData to DataFrames
    return {symbol: pd_data.df for symbol, pd_data in results.items()}


def is_market_open() -> bool:
    """
    Check if US or HK market is currently open.
    
    Returns:
        True if either market is open
    """
    now = datetime.now()
    current_time = now.time()
    
    # Check US market hours (Mon-Fri, 9:30 AM - 4:00 PM ET)
    us_market_open = dt_time(9, 30)
    us_market_close = dt_time(16, 0)
    
    # Check HK market hours (Mon-Fri, 9:30 AM - 4:00 PM HKT, with lunch break)
    hk_market_open = dt_time(9, 30)
    hk_market_close = dt_time(16, 0)
    
    # Weekend check
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check US market
    us_open = us_market_open <= current_time <= us_market_close
    
    # Check HK market (simplified - no lunch break check)
    hk_open = hk_market_open <= current_time <= hk_market_close
    
    return us_open or hk_open


def get_latest_bar(price_data: PriceData) -> Optional[Bar]:
    """
    Get the most recent bar from PriceData.
    
    Args:
        price_data: PriceData object
        
    Returns:
        Bar object or None
    """
    if price_data.df is None or price_data.df.empty:
        return None
    
    df = price_data.df
    last_row = df.iloc[-1]
    
    # Handle both datetime and string timestamps
    timestamp = last_row.get('Datetime')
    if timestamp is None:
        timestamp = last_row.get('Date')
    if timestamp is None:
        timestamp = df.index[-1]
    
    return Bar(
        symbol=price_data.symbol,
        timestamp=pd.Timestamp(timestamp).to_pydatetime(),
        open=float(last_row.get('Open', 0)),
        high=float(last_row.get('High', 0)),
        low=float(last_row.get('Low', 0)),
        close=float(last_row.get('Close', 0)),
        volume=int(last_row.get('Volume', 0)),
        source="yahoo"
    )
