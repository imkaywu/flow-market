"""
Composite Signal

Combines all signals into a final trading recommendation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd

import config
from data.normalize import Signal, NewsItem, SentimentData, AllFeatures
from features.volume import compute_volume_features, get_volume_score
from features.price import compute_price_features, get_momentum_score
from features.technical import compute_technical_features, get_technical_score
from features.sentiment import compute_sentiment_features, get_sentiment_score, should_avoid
from signals.volume_spike import generate_volume_spike_signal
from signals.sentiment_signal import generate_sentiment_signal


def compute_all_features(
    symbol: str,
    df: pd.DataFrame,
    news_items: Optional[List[NewsItem]] = None,
    sentiment_data: Optional[SentimentData] = None
) -> AllFeatures:
    """
    Compute all features for a symbol.
    
    Args:
        symbol: Stock symbol
        df: DataFrame with OHLCV data
        news_items: Optional list of news items
        sentiment_data: Optional pre-computed sentiment data
        
    Returns:
        AllFeatures object
    """
    volume_features = compute_volume_features(df)
    price_features = compute_price_features(df)
    technical_features = compute_technical_features(df)
    sentiment_features = compute_sentiment_features(news_items, sentiment_data)
    
    return AllFeatures(
        symbol=symbol,
        volume=volume_features,
        price=price_features,
        technical=technical_features,
        sentiment=sentiment_features,
        last_updated=datetime.now()
    )


def generate_composite_signal(
    symbol: str,
    df: pd.DataFrame,
    news_items: Optional[List[NewsItem]] = None,
    sentiment_data: Optional[SentimentData] = None
) -> Signal:
    """
    Generate composite signal combining all indicators.
    
    Kevin Xu's Strategy:
    - Rule #1: Volume spike + mid-day = PAY ATTENTION
    - Rule #2: Positive news + muted price = DON'T BOTHER
    
    Args:
        symbol: Stock symbol
        df: DataFrame with OHLCV data
        news_items: Optional list of news items
        sentiment_data: Optional pre-computed sentiment data
        
    Returns:
        Signal object with composite score
    """
    # Compute all features
    features = compute_all_features(symbol, df, news_items, sentiment_data)
    
    # Get individual scores
    volume_score = get_volume_score(features.volume)
    momentum_score = get_momentum_score(features.price)
    technical_score = get_technical_score(features.technical)
    sentiment_score = get_sentiment_score(features.sentiment)
    
    # Check Rule #2: DON'T BOTHER
    is_avoid, avoid_reason = should_avoid(
        features.sentiment,
        features.price.returns_1h / 100  # Convert to decimal
    )
    
    if is_avoid:
        return Signal(
            symbol=symbol,
            recommendation="AVOID",
            score=0.0,
            volume_score=volume_score,
            momentum_score=momentum_score,
            technical_score=technical_score,
            sentiment_score=sentiment_score,
            reason=avoid_reason,
            is_attention=False,
            is_avoid=True,
            price=features.price.returns_1d,
            price_change_pct=features.price.returns_1h,
            timestamp=datetime.now(),
            features=features
        )
    
    # Calculate composite score with weights
    composite_score = (
        volume_score * config.WEIGHT_VOLUME_SPIKE +
        momentum_score * config.WEIGHT_PRICE_MOMENTUM +
        technical_score * config.WEIGHT_TECHNICAL +
        sentiment_score * config.WEIGHT_SENTIMENT
    )
    
    # Determine recommendation based on score
    if composite_score >= 0.8:
        recommendation = "STRONG_BUY"
    elif composite_score >= 0.6:
        recommendation = "BUY"
    elif composite_score >= 0.4:
        recommendation = "WATCH"
    else:
        recommendation = "NO_SIGNAL"
    
    # Build reason
    reasons = []
    if volume_score > 0.5:
        reasons.append(f"vol={volume_score:.2f}")
    if momentum_score > 0.5:
        reasons.append(f"mom={momentum_score:.2f}")
    if technical_score > 0.6:
        reasons.append(f"tech={technical_score:.2f}")
    if sentiment_score > 0.5:
        reasons.append(f"sent={sentiment_score:.2f}")
    
    reason = f"score={composite_score:.2f} ({', '.join(reasons)})" if reasons else "No strong signals"
    
    # Get current price and volume
    current_price = float(df['Close'].iloc[-1]) if len(df) > 0 else 0.0
    current_volume = int(df['Volume'].iloc[-1]) if len(df) > 0 else 0
    
    return Signal(
        symbol=symbol,
        recommendation=recommendation,
        score=round(composite_score, 3),
        volume_score=volume_score,
        momentum_score=momentum_score,
        technical_score=technical_score,
        sentiment_score=sentiment_score,
        reason=reason,
        is_attention=volume_score > 0.5,
        is_avoid=False,
        price=current_price,
        volume=current_volume,
        price_change_pct=features.price.returns_1h,
        timestamp=datetime.now(),
        features=features
    )


def generate_signals_for_batch(
    price_data: Dict[str, pd.DataFrame],
    news_data: Dict[str, List[NewsItem]],
    sentiment_data: Dict[str, SentimentData]
) -> List[Signal]:
    """
    Generate signals for a batch of symbols.
    
    Args:
        price_data: Dictionary of symbol -> DataFrame
        news_data: Dictionary of symbol -> List[NewsItem]
        sentiment_data: Dictionary of symbol -> SentimentData
        
    Returns:
        List of Signal objects
    """
    signals = []
    
    for symbol, df in price_data.items():
        if df is None or len(df) < 10:
            continue
        
        news_items = news_data.get(symbol, [])
        sent_data = sentiment_data.get(symbol)
        
        signal = generate_composite_signal(symbol, df, news_items, sent_data)
        signals.append(signal)
    
    # Sort by score descending
    signals.sort(key=lambda s: s.score, reverse=True)
    
    return signals
