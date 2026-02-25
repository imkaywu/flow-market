"""
Unified Market Data Provider

Provides a unified API for fetching market data from multiple sources.
Automatically falls back to alternative sources if one fails.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

import config
from data.normalize import PriceData

# Import adapters
from data.adapters.alpaca import AlpacaFetcher
from data.adapters.finnhub import FinnhubFetcher


class MarketDataProvider:
    """
    Unified market data provider with automatic source selection.
    
    Priority order:
    1. Alpaca (US only, real-time with API keys)
    2. Finnhub (US + HK, better rate limits)
    3. Yahoo Finance (fallback, rate limited)
    """
    
    def __init__(
        self,
        prefer_source: str = "auto",
        alpaca_api_key: Optional[str] = None,
        alpaca_secret_key: Optional[str] = None,
        finnhub_api_key: Optional[str] = None
    ):
        """
        Initialize market data provider.
        
        Args:
            prefer_source: Preferred source ('alpaca', 'finnhub', 'yahoo', 'auto')
            alpaca_api_key: Alpaca API key
            alpaca_secret_key: Alpaca secret key
            finnhub_api_key: Finnhub API key
        """
        self.prefer_source = prefer_source
        
        # Initialize adapters
        self.alpaca = AlpacaFetcher(
            api_key=alpaca_api_key,
            secret_key=alpaca_secret_key
        )
        
        self.finnhub = FinnhubFetcher(api_key=finnhub_api_key)
        
        # Track which sources are available
        self._sources_configured = {
            'alpaca': self.alpaca.is_configured(),
            'finnhub': self.finnhub.is_configured(),
            'yahoo': True  # Always available (but rate limited)
        }
        
        print(f"[INFO] Market Data Provider initialized:")
        print(f"       Alpaca: {'✓ configured' if self._sources_configured['alpaca'] else '✗ not configured'}")
        print(f"       Finnhub: {'✓ configured' if self._sources_configured['finnhub'] else '✗ not configured'}")
        print(f"       Yahoo: ✓ available (rate limited)")
    
    def fetch_us_stocks(
        self,
        symbols: List[str],
        source: str = "auto"
    ) -> Dict[str, PriceData]:
        """
        Fetch US stock data.
        
        Args:
            symbols: List of US stock symbols
            source: Preferred source ('alpaca', 'finnhub', 'yahoo', 'auto')
            
        Returns:
            Dictionary mapping symbol -> PriceData
        """
        if source == "auto":
            # Auto-select best available source
            if self._sources_configured['alpaca']:
                source = 'alpaca'
            elif self._sources_configured['finnhub']:
                source = 'finnhub'
            else:
                source = 'yahoo'
        
        print(f"[INFO] Fetching {len(symbols)} US stocks via {source}...")
        
        if source == 'alpaca' and self._sources_configured['alpaca']:
            return self.alpaca.fetch_batch(symbols)
        
        if source == 'finnhub' and self._sources_configured['finnhub']:
            return self.finnhub.fetch_batch(symbols)
        
        # Fallback to Yahoo
        return self._fetch_yahoo(symbols)
    
    def fetch_hk_stocks(
        self,
        symbols: List[str],
        source: str = "auto"
    ) -> Dict[str, PriceData]:
        """
        Fetch HK stock data.
        
        Args:
            symbols: List of HK stock symbols
            source: Preferred source (only 'finnhub' or 'yahoo' for HK)
            
        Returns:
            Dictionary mapping symbol -> PriceData
        """
        if source == "auto":
            if self._sources_configured['finnhub']:
                source = 'finnhub'
            else:
                source = 'yahoo'
        
        print(f"[INFO] Fetching {len(symbols)} HK stocks via {source}...")
        
        if source == 'finnhub' and self._sources_configured['finnhub']:
            return self.finnhub.fetch_batch(symbols)
        
        # Fallback to Yahoo
        return self._fetch_yahoo(symbols)
    
    def fetch_all(
        self,
        us_symbols: Optional[List[str]] = None,
        hk_symbols: Optional[List[str]] = None,
        source: str = "auto"
    ) -> Dict[str, PriceData]:
        """
        Fetch all stocks (US + HK).
        
        Args:
            us_symbols: List of US symbols
            hk_symbols: List of HK symbols
            source: Preferred source
            
        Returns:
            Dictionary mapping symbol -> PriceData
        """
        results = {}
        
        if us_symbols:
            us_results = self.fetch_us_stocks(us_symbols, source)
            results.update(us_results)
        
        if hk_symbols:
            hk_results = self.fetch_hk_stocks(hk_symbols, source)
            results.update(hk_results)
        
        return results
    
    def _fetch_yahoo(self, symbols: List[str]) -> Dict[str, PriceData]:
        """Fetch via Yahoo Finance (fallback)."""
        from data.prices import PriceFetcher
        
        fetcher = PriceFetcher()
        return fetcher.fetch_batch(symbols)


def get_provider(
    prefer_source: str = "auto",
    alpaca_api_key: Optional[str] = None,
    alpaca_secret_key: Optional[str] = None,
    finnhub_api_key: Optional[str] = None
) -> MarketDataProvider:
    """
    Get a configured market data provider.
    
    Args:
        prefer_source: Preferred source
        alpaca_api_key: Alpaca API key
        alpaca_secret_key: Alpaca secret key  
        finnhub_api_key: Finnhub API key
        
    Returns:
        MarketDataProvider instance
    """
    # Try env variables if not provided
    alpaca_key = alpaca_api_key or os.environ.get("ALPACA_API_KEY")
    alpaca_secret = alpaca_secret_key or os.environ.get("ALPACA_SECRET_KEY")
    finnhub_key = finnhub_api_key or os.environ.get("FINNHUB_API_KEY")
    
    return MarketDataProvider(
        prefer_source=prefer_source,
        alpaca_api_key=alpaca_key,
        alpaca_secret_key=alpaca_secret,
        finnhub_api_key=finnhub_key
    )
