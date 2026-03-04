"""
Test Script: Yahoo Finance Data Fetching

Tests fetching market data via Yahoo Finance.

Note: Yahoo Finance has been blocking yfinance requests since 2025.
If you see YFRateLimitError, your IP may be blocked.

Usage:
    python scripts/test_yahoo.py
"""
import sys
import time

sys.path.insert(0, '.')

from data.adapters.yahoo import YahooAdapter


def test_yahoo_config():
    """Test if Yahoo adapter is configured."""
    print("\n" + "="*60)
    print("TEST: Yahoo Finance Configuration")
    print("="*60)
    
    adapter = YahooAdapter()
    print(f"Adapter initialized: OK")
    print(f"Max retries: {adapter.max_retries}")
    print(f"Retry delay: {adapter.retry_delay}s")
    
    return True


def test_yahoo_fetch():
    """Test fetching data from Yahoo Finance."""
    print("\n" + "="*60)
    print("TEST: Yahoo Finance Data Fetching")
    print("="*60)
    
    adapter = YahooAdapter(max_retries=2, retry_delay=1.0)
    
    success = False
    
    # Test US symbols
    us_symbols = ["AAPL", "MSFT"]
    
    print(f"\nFetching US: {us_symbols}")
    print("-"*40)
    
    try:
        bars_us = adapter.fetch_latest_bar(us_symbols)
        print(f"\n✅ US: {len(bars_us)} bars fetched")
        
        if bars_us:
            success = True
            print(f"\n  Sample US data:")
            for bar in bars_us[-3:]:
                print(f"    {bar.symbol}: ${bar.close:.2f}")
    except Exception as e:
        print(f"\n❌ US fetch failed: {e}")
    
    # Test HK symbols
    hk_symbols = ["0700.HK", "9988.HK"]
    
    print(f"\n{'='*60}")
    print(f"Fetching HK: {hk_symbols}")
    print("-"*40)
    
    try:
        bars_hk = adapter.fetch_latest_bar(hk_symbols)
        print(f"\n✅ HK: {len(bars_hk)} bars fetched")
        
        if bars_hk:
            success = True
            print(f"\n  Sample HK data:")
            for bar in bars_hk[-3:]:
                print(f"    {bar.symbol}: ${bar.close:.2f}")
    except Exception as e:
        print(f"\n❌ HK fetch failed: {e}")
    
    return success


def test_alternative():
    """Test alternatives if Yahoo is blocked."""
    print("\n" + "="*60)
    print("ALTERNATIVES (if Yahoo is blocked)")
    print("="*60)
    
    print("""
Since Yahoo Finance started blocking yfinance in 2025, here are alternatives:

1. Finnhub (US + HK stocks, free tier)
   - Sign up: https://finnhub.io/
   - Run: python scripts/test_finnhub.py

2. Alpaca (US stocks, free tier)
   - Sign up: https://alpaca.markets/
   - Check your config for API keys

3. Polygon.io (US stocks, free tier)
   - Sign up: https://polygon.io/

4. Use VPN to change your IP address

5. Wait - Yahoo rate limits may reset after some time (hours to days)
""")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FLOW MARKET - YAHOO FINANCE TEST")
    print("="*60)
    
    # Test configuration
    test_yahoo_config()
    
    # Test fetching
    success = test_yahoo_fetch()
    
    # Show alternatives if failed
    if not success:
        test_alternative()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    if success:
        print("✅ Yahoo Finance is working!")
    else:
        print("❌ Yahoo Finance is blocked/rate-limited")
        print("\nSee alternatives above or try Finnhub:")
        print("  python scripts/test_finnhub.py")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
