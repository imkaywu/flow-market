"""
Sentiment Signal

Rule #2: Detect news/price divergence - DON'T BOTHER
"""
from datetime import datetime
from typing import List, Optional

import pandas as pd

import config
from data.normalize import NewsItem, SentimentData, Signal
from features.sentiment import compute_sentiment_features, should_avoid, get_sentiment_score
from features.price import compute_price_features


def generate_sentiment_signal(
    symbol: str,
    df: pd.DataFrame,
    news_items: Optional[List[NewsItem]] = None,
    sentiment_data: Optional[SentimentData] = None
) -> Signal:
    """
    Generate sentiment-based signal.
    
    Kevin Xu's Rule #2: DON'T BOTHER when positive news exists but price doesn't move
    
    Args:
        symbol: Stock symbol
        df: DataFrame with OHLCV data
        news_items: Optional list of news items
        sentiment_data: Optional pre-computed sentiment data
        
    Returns:
        Signal object
    """
    # Compute sentiment features
    sentiment_features = compute_sentiment_features(news_items or [], sentiment_data)
    
    # Compute price features for price change
    price_features = compute_price_features(df)
    
    # Get sentiment score
    sentiment_score = get_sentiment_score(sentiment_features)
    
    # Check if we should avoid (positive news + muted price)
    is_avoid, avoid_reason = should_avoid(
        sentiment_features,
        price_features.returns_1h / 100  # Convert to decimal
    )
    
    if is_avoid:
        return Signal(
            symbol=symbol,
            recommendation="AVOID",
            score=0.0,
            sentiment_score=sentiment_score,
            reason=avoid_reason,
            is_avoid=True,
            timestamp=datetime.now()
        )
    
    # If there's positive sentiment, boost the score
    if sentiment_features.sentiment_score > 0.3 and sentiment_features.buzz_level > 0.3:
        return Signal(
            symbol=symbol,
            recommendation="WATCH",
            score=sentiment_score * 0.5,
            sentiment_score=sentiment_score,
            reason=f"Positive sentiment (score: {sentiment_features.sentiment_score:.2f}, "
                   f"buzz: {sentiment_features.buzz_level:.2f})",
            is_avoid=False,
            timestamp=datetime.now()
        )
    
    # No strong sentiment signal
    return Signal(
        symbol=symbol,
        recommendation="NO_SIGNAL",
        score=0.0,
        sentiment_score=sentiment_score,
        reason="No significant sentiment detected",
        is_avoid=False,
        timestamp=datetime.now()
    )
