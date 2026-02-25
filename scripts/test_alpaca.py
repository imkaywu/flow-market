"""
Test Script: Alpaca Data Fetching

Tests fetching real-time US market data via Alpaca.

Get free API keys at https://alpaca.markets/

Usage:
    # Option 1: Set environment variables
    export ALPACA_API_KEY=your_key
    export ALPACA_SECRET_KEY=your_secret
    python scripts/test_alpaca.py

    # Option 2: Create config_local.py with your keys
    # (see config_example.py)
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

# Try to import local config
try:
    import config_local as local_config
    # Override with local config if available
    if local_config.ALPACA_API_KEY:
        os.environ["ALPACA_API_KEY"] = local_config.ALPACA_API_KEY
    if local_config.ALPACA_SECRET_KEY:
        os.environ["ALPACA_SECRET_KEY"] = local_config.ALPACA_SECRET_KEY
except ImportError:
    pass

from data.adapters.alpaca import AlpacaFetcher


def test_alpaca_config():
    """Test if Alpaca is configured."""
    print("\n" + "="*60)
    print("TEST: Alpaca Configuration")
    print("="*60)
    
    api_key = os.environ.get("ALPACA_API_KEY", "")
    secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
    
    print(f"\nAPI Key configured: {bool(api_key)}")
    print(f"Secret Key configured: {bool(secret_key)}")
    
    fetcher = AlpacaFetcher()
    
    if not fetcher.is_configured():
        print("\n⚠️  Alpaca not configured!")
        print("   Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        print("   Or copy config_example.py to config_local.py and add your keys")
        return False
    
    print("\n✅ Alpaca is configured!")
    return True


def test_alpaca_fetch():
    """Test fetching data from Alpaca."""
    print("\n" + "="*60)
    print("TEST: Alpaca Data Fetching")
    print("="*60)
    
    fetcher = AlpacaFetcher()
    
    if not fetcher.is_configured():
        print("❌ Alpaca not configured. Skipping test.")
        return False
    
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print(f"\nFetching: {test_symbols}")
    print("-"*40)
    
    results = fetcher.fetch_batch(test_symbols)
    
    print(f"\n✅ Successfully fetched {len(results)}/{len(test_symbols)} symbols")
    
    for symbol, pd_data in results.items():
        df = pd_data.df
        print(f"\n📈 {symbol}:")
        print(f"   Bars: {len(df)}")
        print(f"   Latest: ${df['Close'].iloc[-1]:.2f}")
        print(f"   Volume: {df['Volume'].iloc[-1]:,}")
    
    return len(results) > 0


def test_quote():
    """Test getting quotes."""
    print("\n" + "="*60)
    print("TEST: Alpaca Quote")
    print("="*60)
    
    fetcher = AlpacaFetcher()
    
    if not fetcher.is_configured():
        print("❌ Alpaca not configured. Skipping test.")
        return False
    
    quote = fetcher.get_latest_quote("AAPL")
    
    if quote:
        print(f"\n✅ AAPL Quote:")
        print(f"   Bid: ${quote.get('bp', 'N/A')}")
        print(f"   Ask: ${quote.get('ap', 'N/A')}")
        print(f"   Last: ${quote.get('c', 'N/A')}")
        return True
    
    return False


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - ALPACA TEST")
    print("="*60)
    
    # Test configuration
    if not test_alpaca_config():
        print("\n" + "="*60)
        print("RESULTS: Alpaca not configured")
        print("="*60)
        print("\nTo configure Alpaca:")
        print("1. Sign up at https://alpaca.markets/")
        print("2. Get your API keys from the dashboard")
        print("3. Create config_local.py with your keys (see config_example.py)")
        return False
    
    # Test fetching
    success1 = test_alpaca_fetch()
    
    # Test quote
    success2 = test_quote()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ Data Fetch: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Quote: {'PASSED' if success2 else 'FAILED'}")
    
    if success1:
        print("\n🎉 Alpaca is working!")
        print("\nNow you can use Alpaca for US market data!")
    
    return success1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
