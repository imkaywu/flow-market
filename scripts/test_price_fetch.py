"""
Test Script: Price Data Fetching

Tests fetching real-time price data from Yahoo Finance.
Run with: python scripts/test_price_fetch.py

NOTE: Yahoo Finance has rate limits. If you get rate limited, wait a few minutes
and try again. The code now includes retry logic with exponential backoff.
"""
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

import config
from data.prices import PriceFetcher, fetch_prices


def test_fetch_prices():
    """Test price fetching for US and HK stocks."""
    print("\n" + "="*60)
    print("TEST: Price Data Fetching (Yahoo Finance)")
    print("="*60)
    
    # Use a single symbol to avoid rate limiting
    test_symbols = ["AAPL"]
    
    print(f"\nSymbols to fetch: {test_symbols}")
    print(f"Period: {config.PRICE_PERIOD}")
    print(f"Interval: {config.PRICE_INTERVAL}")
    print(f"\nFetching at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*40)
    
    # Initialize fetcher
    fetcher = PriceFetcher(
        period=config.PRICE_PERIOD,
        interval=config.PRICE_INTERVAL
    )
    
    # Fetch prices
    results = fetcher.fetch_batch(test_symbols)
    
    # Print results
    print(f"\n✅ Successfully fetched {len(results)}/{len(test_symbols)} symbols\n")
    
    for symbol, price_data in results.items():
        df = price_data.df
        print(f"📈 {symbol}:")
        print(f"   Bars: {len(df)}")
        print(f"   Latest: ${df['Close'].iloc[-1]:.2f}")
        print(f"   Volume: {df['Volume'].iloc[-1]:,}")
        print(f"   Time: {df.iloc[-1].get('Datetime', df.index[-1])}")
        print()
    
    # Summary
    print("-"*40)
    print(f"Total: {len(results)} stocks fetched successfully")
    print(f"Failed: {len(test_symbols) - len(results)} symbols")
    
    return len(results) > 0


def test_fetch_all_tier1():
    """Test fetching all Tier 1 stocks."""
    print("\n" + "="*60)
    print("TEST: Fetch All Tier 1 Stocks")
    print("="*60)
    
    all_tier1 = config.US_TIER_1 + config.HK_TIER_1
    print(f"\nTotal Tier 1 stocks: {len(all_tier1)}")
    print(f"   US: {len(config.US_TIER_1)}")
    print(f"   HK: {len(config.HK_TIER_1)}")
    
    # This might take a while, so just test a few
    print("\nFetching a sample...")
    
    fetcher = PriceFetcher()
    results = fetcher.fetch_batch(all_tier1[:10])
    
    print(f"\n✅ Sample fetch: {len(results)}/10 successful")
    
    return len(results) > 0


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - PRICE FETCH TEST")
    print("="*60)
    print("NOTE: Yahoo Finance has rate limits. If rate limited, wait and retry.")
    
    # Test 1: Basic price fetch
    success1 = test_fetch_prices()
    
    # Wait between tests to avoid rate limiting
    if success1:
        print("\n⏳ Waiting 10 seconds before next test...")
        time.sleep(10)
    
    # Test 2: Full tier
    success2 = test_fetch_all_tier1()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ Price Fetch: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Full Tier: {'PASSED' if success2 else 'FAILED'}")
    
    if success1:
        print("\n🎉 Price fetching is working!")
        print("\nNext: Run python scripts/test_news_fetch.py")
    else:
        print("\n❌ Price fetching failed. Check your internet connection.")
    
    return success1 and success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
