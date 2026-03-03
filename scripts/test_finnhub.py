"""
Test Script: Finnhub Data Fetching

Tests fetching market data via Finnhub API.

Get free API key at https://finnhub.io/

Usage:
    # Option 1: Create config_local.py with your keys (see config_example.py)
    # Option 2: Set environment variable
    export FINNHUB_API_KEY=your_key
    python scripts/test_finnhub.py
"""
import sys
import os
from datetime import datetime

import pandas as pd

# Add parent directory to path
sys.path.insert(0, '.')

# Try to import local config
try:
    import config_local as local_config
    # Override with local config if available
    if hasattr(local_config, 'FINNHUB_API_KEY') and local_config.FINNHUB_API_KEY:
        os.environ["FINNHUB_API_KEY"] = local_config.FINNHUB_API_KEY
except ImportError:
    pass

from data.adapters.finnhub import FinnhubFetcher


def test_finnhub_config():
    """Test if Finnhub is configured."""
    print("\n" + "="*60)
    print("TEST: Finnhub Configuration")
    print("="*60)
    
    fetcher = FinnhubFetcher()
    
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    
    print(f"\nAPI Key configured: {bool(api_key)}")
    
    if not fetcher.is_configured():
        print("\n⚠️  Finnhub not configured!")
        print("   Set environment variable:")
        print("   export FINNHUB_API_KEY=your_key")
        print("\n   Get free key at: https://finnhub.io/")
        return False
    
    print("\n✅ Finnhub is configured!")
    return True


def test_finnhub_fetch():
    """Test fetching data from Finnhub."""
    print("\n" + "="*60)
    print("TEST: Finnhub Data Fetching")
    print("="*60)
    
    fetcher = FinnhubFetcher()
    
    if not fetcher.is_configured():
        print("❌ Finnhub not configured. Skipping test.")
        return False
    
    us_success = False
    hk_success = False
    
    # Test US symbols
    us_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print(f"\nFetching US: {us_symbols}")
    print("-"*40)
    
    try:
        us_results = fetcher.fetch_batch(us_symbols)
        us_success = len(us_results) > 0
    except Exception as e:
        print(f"  [ERROR] US fetch failed: {e}")
        us_results = {}
    
    print(f"\n✅ US: {len(us_results)}/{len(us_symbols)} symbols")
    
    for symbol, pd_data in us_results.items():
        df = pd_data.df
        print(f"\n📈 {symbol}:")
        print(f"   Bars: {len(df)}")
        if not df.empty:
            print(f"   Latest: ${df['Close'].iloc[-1]:.2f}")
            print(f"   Volume: {df['Volume'].iloc[-1]:,}")
    
    # Test HK symbols
    hk_symbols = ["0700.HK", "9988.HK"]
    
    print(f"\n{'='*60}")
    print(f"Fetching HK: {hk_symbols}")
    print("-"*40)
    
    try:
        hk_results = fetcher.fetch_batch(hk_symbols)
        hk_success = len(hk_results) > 0
    except Exception as e:
        print(f"  [ERROR] HK fetch failed: {e}")
        hk_results = {}
    
    print(f"\n✅ HK: {len(hk_results)}/{len(hk_symbols)} symbols")
    
    for symbol, pd_data in hk_results.items():
        df = pd_data.df
        print(f"\n📈 {symbol}:")
        print(f"   Bars: {len(df)}")
        if not df.empty:
            print(f"   Latest: ${df['Close'].iloc[-1]:.2f}")
    
    return us_success or hk_success


def test_quote():
    """Test getting quotes."""
    print("\n" + "="*60)
    print("TEST: Finnhub Quote")
    print("="*60)
    
    fetcher = FinnhubFetcher()
    
    if not fetcher.is_configured():
        print("❌ Finnhub not configured. Skipping test.")
        return False
    
    quote = fetcher.get_quote("AAPL")
    
    if quote:
        print(f"\n✅ AAPL Quote:")
        print(f"   Current: ${quote.get('c', 'N/A')}")
        print(f"   High: ${quote.get('h', 'N/A')}")
        print(f"   Low: ${quote.get('l', 'N/A')}")
        print(f"   Open: ${quote.get('o', 'N/A')}")
        print(f"   Previous Close: ${quote.get('pc', 'N/A')}")
        return True
    
    return False


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - FINNHUB TEST")
    print("="*60)
    
    # Test configuration
    if not test_finnhub_config():
        print("\n" + "="*60)
        print("RESULTS: Finnhub not configured")
        print("="*60)
        print("\nTo configure Finnhub:")
        print("1. Sign up at https://finnhub.io/")
        print("2. Get your free API key")
        print("3. Set environment variable and re-run")
        return False
    
    # Test fetching
    success1 = test_finnhub_fetch()
    
    # Test quote
    success2 = test_quote()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ Data Fetch: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Quote: {'PASSED' if success2 else 'FAILED'}")
    
    if success1:
        print("\n🎉 Finnhub is working!")
        print("\nNow you can use Finnhub for US + HK market data!")
    
    return success1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
