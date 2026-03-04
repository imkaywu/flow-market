"""
Test Script: Alpha Vantage Data Fetching

Tests fetching market data via Alpha Vantage API.

Get free API key at https://www.alphavantage.co/support/#api-key

Usage:
    # Option 1: Set environment variable
    export ALPHAVANTAGE_API_KEY=your_key
    python scripts/test_alphavantage.py
    
    # Option 2: Create config_local.py with your key
"""
import sys
import os

sys.path.insert(0, '.')

try:
    import config_local as local_config
    if hasattr(local_config, 'ALPHAVANTAGE_API_KEY') and local_config.ALPHAVANTAGE_API_KEY:
        os.environ["ALPHAVANTAGE_API_KEY"] = local_config.ALPHAVANTAGE_API_KEY
except ImportError:
    pass

from data.adapters.alphavantage import AlphaVantageFetcher


def test_alphavantage_config():
    """Test if Alpha Vantage is configured."""
    print("\n" + "="*60)
    print("TEST: Alpha Vantage Configuration")
    print("="*60)
    
    fetcher = AlphaVantageFetcher()
    
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "")
    
    print(f"\nAPI Key configured: {bool(api_key)}")
    print(f"API Key (first 5 chars): {api_key[:5] if api_key else 'None'}...")
    
    if not fetcher.is_configured():
        print("\n⚠️  Alpha Vantage not configured!")
        print("   Set environment variable:")
        print("   export ALPHAVANTAGE_API_KEY=your_key")
        print("\n   Get free key at: https://www.alphavantage.co/support/#api-key")
        return False
    
    print("\n✅ Alpha Vantage is configured!")
    print(f"Rate limit remaining: {fetcher.rate_limit_remaining}/25 (free tier)")
    return True


def test_alphavantage_quote():
    """Test getting quote."""
    print("\n" + "="*60)
    print("TEST: Alpha Vantage Quote")
    print("="*60)
    
    fetcher = AlphaVantageFetcher()
    
    if not fetcher.is_configured():
        print("❌ Alpha Vantage not configured. Skipping test.")
        return False
    
    symbol = "IBM"
    print(f"\nFetching quote for {symbol}...")
    
    quote = fetcher.get_quote(symbol)
    
    if quote:
        print(f"\n✅ {symbol} Quote:")
        print(f"   Price: ${quote.get('price', 'N/A')}")
        print(f"   Open: ${quote.get('open', 'N/A')}")
        print(f"   High: ${quote.get('high', 'N/A')}")
        print(f"   Low: ${quote.get('low', 'N/A')}")
        print(f"   Volume: {quote.get('volume', 'N/A'):,}")
        print(f"   Previous Close: ${quote.get('previous_close', 'N/A')}")
        print(f"\n   Rate limit remaining: {fetcher.rate_limit_remaining}/25")
        return True
    
    return False


def test_alphavantage_candles():
    """Test fetching candles."""
    print("\n" + "="*60)
    print("TEST: Alpha Vantage Candles")
    print("="*60)
    
    fetcher = AlphaVantageFetcher()
    
    if not fetcher.is_configured():
        print("❌ Alpha Vantage not configured. Skipping test.")
        return False
    
    symbols = ["IBM", "AAPL"]
    success = False
    
    for symbol in symbols:
        if fetcher.rate_limit_remaining <= 0:
            print("\n⚠️  Rate limit reached")
            break
        
        print(f"\nFetching {symbol} (5min interval)...")
        
        df = fetcher.fetch_candles(symbol, interval="5min")
        
        if df is not None and not df.empty:
            print(f"   ✅ {symbol}: {len(df)} bars")
            print(f"   Latest: ${df['Close'].iloc[-1]:.2f}")
            print(f"   Volume: {df['Volume'].iloc[-1]:,}")
            success = True
        else:
            print(f"   ❌ {symbol}: No data")
    
    print(f"\nRate limit remaining: {fetcher.rate_limit_remaining}/25")
    return success


def test_alphavantage_daily():
    """Test fetching daily data."""
    print("\n" + "="*60)
    print("TEST: Alpha Vantage Daily Data")
    print("="*60)
    
    fetcher = AlphaVantageFetcher()
    
    if not fetcher.is_configured():
        print("❌ Alpha Vantage not configured. Skipping test.")
        return False
    
    symbol = "IBM"
    print(f"\nFetching daily data for {symbol}...")
    
    df = fetcher.fetch_daily(symbol, outputsize="compact")
    
    if df is not None and not df.empty:
        print(f"\n✅ {symbol} Daily: {len(df)} days")
        print(f"   Latest: ${df['Close'].iloc[-1]:.2f}")
        print(f"   Volume: {df['Volume'].iloc[-1]:,}")
        print(f"\n   Rate limit remaining: {fetcher.rate_limit_remaining}/25")
        return True
    
    return False


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - ALPHA VANTAGE TEST")
    print("="*60)
    
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "")
    is_demo = api_key.lower() == "demo"
    
    if is_demo:
        print("\n⚠️  Using DEMO key - limited to IBM only")
        print("   Get free key at: https://www.alphavantage.co/support/#api-key")
    
    if not test_alphavantage_config():
        print("\n" + "="*60)
        print("RESULTS: Alpha Vantage not configured")
        print("="*60)
        print("\nTo configure Alpha Vantage:")
        print("1. Sign up at https://www.alphavantage.co/")
        print("2. Get your free API key")
        print("3. Set environment variable and re-run")
        return False
    
    results = []
    
    results.append(("Quote", test_alphavantage_quote()))
    
    if not is_demo:
        results.append(("Candles", test_alphavantage_candles()))
        results.append(("Daily", test_alphavantage_daily()))
    else:
        print("\n" + "="*60)
        print("SKIPPED: Candles & Daily tests (demo key)")
        print("="*60)
        print("Get a free API key to test all features:")
        print("https://www.alphavantage.co/support/#api-key")
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {name}: {status}")
    
    success = any(p for _, p in results)
    
    if success:
        print("\n🎉 Alpha Vantage is working!")
        print("\nNote: Free tier = 25 API calls/day")
        print("Use 'daily' interval for end-of-day data to save calls")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
