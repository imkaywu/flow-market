"""
Test Script: Feature Computation

Tests computing all features for stocks.
Run with: python scripts/test_features.py
"""
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

import config
from data.prices import PriceFetcher
from features.volume import compute_volume_features, get_volume_score
from features.price import compute_price_features, get_momentum_score
from features.technical import compute_technical_features, get_technical_score
from features.sentiment import compute_sentiment_features, get_sentiment_score


def test_features():
    """Test feature computation."""
    print("\n" + "="*60)
    print("TEST: Feature Computation")
    print("="*60)
    
    # Fetch price data for a few symbols
    test_symbols = ["AAPL", "TSLA", "NVDA"]
    
    print(f"\nFetching price data for: {test_symbols}")
    print("-"*40)
    
    fetcher = PriceFetcher()
    price_data = fetcher.fetch_batch(test_symbols)
    
    # Compute features for each
    for symbol, pd_data in price_data.items():
        df = pd_data.df
        
        print(f"\n📊 {symbol}:")
        print(f"   Price: ${df['Close'].iloc[-1]:.2f}")
        
        # Volume features
        vol_feat = compute_volume_features(df)
        vol_score = get_volume_score(vol_feat)
        print(f"\n   Volume:")
        print(f"      Z-score: {vol_feat.z_score:.2f}")
        print(f"      Relative volume: {vol_feat.relative_volume:.2f}x")
        print(f"      Percentile: {vol_feat.volume_percentile:.0f}%")
        print(f"      Is midday: {vol_feat.is_midday}")
        print(f"      Score: {vol_score:.2f}")
        
        # Price features
        price_feat = compute_price_features(df)
        mom_score = get_momentum_score(price_feat)
        print(f"\n   Price:")
        print(f"      Returns 5m: {price_feat.returns_5m:.2f}%")
        print(f"      Returns 1h: {price_feat.returns_1h:.2f}%")
        print(f"      Returns 1d: {price_feat.returns_1d:.2f}%")
        print(f"      Volatility 1h: {price_feat.volatility_1h:.2f}%")
        print(f"      Is muted: {price_feat.is_muted}")
        print(f"      Momentum score: {mom_score:.2f}")
        
        # Technical features
        tech_feat = compute_technical_features(df)
        tech_score = get_technical_score(tech_feat)
        print(f"\n   Technical:")
        print(f"      RSI: {tech_feat.rsi_14:.1f}")
        print(f"      MACD: {tech_feat.macd:.4f}")
        print(f"      MACD histogram: {tech_feat.macd_histogram:.4f}")
        print(f"      SMA 20: ${tech_feat.sma_20:.2f}")
        print(f"      BB position: {tech_feat.bb_position:.1f}%")
        print(f"      Technical score: {tech_score:.2f}")
        
        print()
    
    return len(price_data) > 0


def test_all_features_combined():
    """Test computing all features at once."""
    print("\n" + "="*60)
    print("TEST: All Features Combined")
    print("="*60)
    
    test_symbols = ["AAPL", "TSLA"]
    
    print(f"\nComputing all features for: {test_symbols}")
    print("-"*40)
    
    fetcher = PriceFetcher()
    price_data = fetcher.fetch_batch(test_symbols)
    
    from signals.composite import compute_all_features
    
    for symbol, pd_data in price_data.items():
        df = pd_data.df
        features = compute_all_features(symbol, df)
        
        print(f"\n{symbol} - All Features Summary:")
        print(f"   Volume score: {get_volume_score(features.volume):.2f}")
        print(f"   Momentum score: {get_momentum_score(features.price):.2f}")
        print(f"   Technical score: {get_technical_score(features.technical):.2f}")
        print(f"   Sentiment score: {get_sentiment_score(features.sentiment):.2f}")
    
    return len(price_data) > 0


def main():
    """Run all tests."""
    print("\n🚀 FLOW MARKET - FEATURES TEST")
    print("="*60)
    
    # Test 1: Individual features
    success1 = test_features()
    
    # Test 2: Combined features
    success2 = test_all_features_combined()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ Feature Computation: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Combined Features: {'PASSED' if success2 else 'FAILED'}")
    
    if success1:
        print("\n🎉 Feature computation is working!")
        print("\nNext: Run python scripts/test_signals.py")
    
    return success1 and success2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
