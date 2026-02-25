"""
Test Script: Signal Generation

Tests generating trading signals.
Run with: python scripts/test_signals.py
"""
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

import config
from data.prices import PriceFetcher
from data.news import NewsFetcher, analyze_sentiment
from signals.composite import generate_composite_signal, generate_signals_for_batch


def test_signal_generation():
    """Test signal generation."""
    print("\n" + "="*60)
    print("TEST: Signal Generation")
    print("="*60)
    
    # Use a small set
    test_symbols = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT"]
    
    print(f"\nGenerating signals for: {test_symbols}")
    print("-"*40)
    
    # Fetch data
    print("\nFetching price data...")
    price_fetcher = PriceFetcher()
    price_data = price_fetcher.fetch_batch(test_symbols)
    
    print("Fetching news data...")
    news_fetcher = NewsFetcher()
    news_data = news_fetcher.fetch_batch(test_symbols)
    
    # Analyze sentiment
    sentiment_data = {}
    for symbol, news_items in news_data.items():
        if news_items:
            sentiment_data[symbol] = analyze_sentiment(news_items, symbol)
    
    # Generate signals
    print("\nGenerating signals...")
    signals = generate_signals_for_batch(price_data, news_data, sentiment_data)
    
    # Print signals
    print(f"\n📊 Generated {len(signals)} signals\n")
    
    for signal in signals:
        emoji = {
            "STRONG_BUY": "🚀",
            "BUY": "💰",
            "WATCH": "👀",
            "AVOID": "❌",
            "NO_SIGNAL": "⚪"
        }.get(signal.recommendation, "⚪")
        
        print(f"{emoji} {signal.symbol:8} | {signal.recommendation:12} | Score: {signal.score:.2f}")
        print(f"   Reason: {signal.reason}")
        
        if signal.is_attention:
            print(f"   ⚡ ATTENTION: Volume spike detected!")
        
        if signal.is_avoid:
            print(f"   ⚠️  AVOID: Positive news but muted price!")
        
        print()
    
    # Score breakdown
    print("-"*40)
    print("Score Breakdown:")
    for signal in signals:
        print(f"   {signal.symbol:8} | vol: {signal.volume_score:.2f} | "
              f"mom: {signal.momentum_score:.2f} | "
              f"tech: {signal.technical_score:.2f} | "
              f"sent: {signal.sentiment_score:.2f}")
    
    return len(signals) > 0


def test_kevin_xu_rules():
    """Test Kevin Xu's specific rules."""
    print("\n" + "="*60)
    print("TEST: Kevin Xu's Strategy Rules")
    print("="*60)
    
    test_symbols = ["AAPL", "TSLA"]
    
    print("\nTesting specific scenarios:")
    print("-"*40)
    
    price_fetcher = PriceFetcher()
    news_fetcher = NewsFetcher()
    
    for symbol in test_symbols:
        price_data = price_fetcher.fetch_single(symbol)
        news_items = news_fetcher.fetch_single(symbol)
        
        if price_data:
            signal = generate_composite_signal(
                symbol,
                price_data.df,
                news_items or [],
                analyze_sentiment(news_items, symbol) if news_items else None
            )
            
            print(f"\n{symbol}:")
            print(f"   Recommendation: {signal.recommendation}")
            print(f"   Score: {signal.score:.3f}")
            print(f"   Is ATTENTION (Rule #1): {signal.is_attention}")
            print(f"   Is AVOID (Rule #2): {signal.is_avoid}")
            print(f"   Price: ${signal.price:.2f}")
            print(f"   Price change: {signal.price_change_pct:.2f}%")
    
    return True


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - SIGNALS TEST")
    print("="*60)
    
    # Test 1: Signal generation
    success1 = test_signal_generation()
    
    # Test 2: Kevin Xu rules
    success2 = test_kevin_xu_rules()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ Signal Generation: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Kevin Xu Rules: {'PASSED' if success2 else 'FAILED'}")
    
    if success1:
        print("\n🎉 Signal generation is working!")
        print("\nNext: Run python scripts/run_scanner.py to start continuous scanning")
    
    return success1 and success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
