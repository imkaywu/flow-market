"""
Test Script: News Data Fetching

Tests fetching news and sentiment analysis.
Run with: python scripts/test_news_fetch.py
"""
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

import config
from data.news import NewsFetcher, fetch_news, analyze_sentiment


def test_fetch_news():
    """Test news fetching for stocks."""
    print("\n" + "="*60)
    print("TEST: News Data Fetching")
    print("="*60)
    
    # Use a small subset for testing
    test_symbols = config.US_TIER_1[:5] + config.HK_TIER_1[:3]
    
    print(f"\nSymbols to fetch news: {test_symbols}")
    print(f"Lookback: {config.NEWS_LOOKBACK_HOURS} hours")
    print(f"\nFetching at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*40)
    
    # Initialize fetcher
    fetcher = NewsFetcher(lookback_hours=config.NEWS_LOOKBACK_HOURS)
    
    # Fetch news
    results = fetcher.fetch_batch(test_symbols)
    
    # Print results
    print(f"\n✅ Got news for {len(results)}/{len(test_symbols)} symbols\n")
    
    total_news = 0
    for symbol, news_items in results.items():
        print(f"📰 {symbol}:")
        print(f"   News count: {len(news_items)}")
        
        if news_items:
            # Show sentiment summary
            sentiment = analyze_sentiment(news_items, symbol)
            print(f"   Sentiment: {sentiment.overall_sentiment:+.2f}")
            print(f"   Positive: {sentiment.positive_ratio:.0%}")
            print(f"   Negative: {sentiment.negative_ratio:.0%}")
            
            # Show latest news title
            latest = news_items[0]
            print(f"   Latest: {latest.title[:60]}...")
        
        total_news += len(news_items)
        print()
    
    # Summary
    print("-"*40)
    print(f"Total news items: {total_news}")
    print(f"Symbols with news: {len(results)}")
    
    return len(results) > 0


def test_sentiment_analysis():
    """Test sentiment analysis."""
    print("\n" + "="*60)
    print("TEST: Sentiment Analysis")
    print("="*60)
    
    # Fetch news for a few symbols
    test_symbols = ["AAPL", "TSLA", "NVDA"]
    
    print(f"\nAnalyzing sentiment for: {test_symbols}")
    print("-"*40)
    
    fetcher = NewsFetcher()
    
    for symbol in test_symbols:
        news_items = fetcher.fetch_single(symbol)
        
        if news_items:
            sentiment = analyze_sentiment(news_items, symbol)
            
            emoji = "🟢" if sentiment.overall_sentiment > 0.1 else "🔴" if sentiment.overall_sentiment < -0.1 else "⚪"
            
            print(f"\n{emoji} {symbol}:")
            print(f"   Overall sentiment: {sentiment.overall_sentiment:+.2f}")
            print(f"   News count: {sentiment.news_count}")
            print(f"   Positive ratio: {sentiment.positive_ratio:.0%}")
            print(f"   Buzz level: {sentiment.buzz_level:.2f}")
            print(f"   Momentum: {sentiment.sentiment_momentum:+.2f}")
        else:
            print(f"\n⚪ {symbol}: No news found")
    
    return True


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - NEWS FETCH TEST")
    print("="*60)
    
    # Test 1: News fetch
    success1 = test_fetch_news()
    
    # Test 2: Sentiment analysis
    success2 = test_sentiment_analysis()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ News Fetch: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Sentiment Analysis: {'PASSED' if success2 else 'FAILED'}")
    
    if success1:
        print("\n🎉 News fetching is working!")
        print("\nNext: Run python scripts/test_features.py")
    else:
        print("\n⚠️ No news data available (may be normal for some symbols)")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
