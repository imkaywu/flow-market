"""
Sentiment Features

Computes sentiment-based features from news data.
"""
from datetime import datetime
from typing import List, Optional

import pandas as pd
import numpy as np

import config
from data.normalize import NewsItem, SentimentData, SentimentFeatures


def compute_sentiment_features(
    news_items: List[NewsItem],
    sentiment_data: Optional[SentimentData] = None
) -> SentimentFeatures:
    """
    Compute sentiment features from news items.
    
    Args:
        news_items: List of NewsItem objects
        sentiment_data: Optional pre-computed SentimentData
        
    Returns:
        SentimentFeatures object
    """
    if not news_items:
        return SentimentFeatures(
            sentiment_score=0.0,
            buzz_level=0.0,
            sentiment_momentum=0.0,
            news_count=0,
            positive_ratio=0.0,
            negative_ratio=0.0
        )
    
    # Use provided sentiment data or compute fresh
    if sentiment_data is None:
        sentiment_data = _analyze_news_sentiment(news_items)
    
    # Extract features
    sentiment_score = sentiment_data.overall_sentiment
    buzz_level = sentiment_data.buzz_level
    sentiment_momentum = sentiment_data.sentiment_momentum
    news_count = sentiment_data.news_count
    positive_ratio = sentiment_data.positive_ratio
    negative_ratio = sentiment_data.negative_ratio
    
    return SentimentFeatures(
        sentiment_score=round(sentiment_score, 3),
        buzz_level=round(buzz_level, 3),
        sentiment_momentum=round(sentiment_momentum, 3),
        news_count=news_count,
        positive_ratio=round(positive_ratio, 3),
        negative_ratio=round(negative_ratio, 3)
    )


def _analyze_news_sentiment(news_items: List[NewsItem]) -> SentimentData:
    """
    Analyze sentiment from news items.
    
    Args:
        news_items: List of NewsItem objects
        
    Returns:
        SentimentData object
    """
    if not news_items:
        return SentimentData(
            symbol="",
            overall_sentiment=0.0,
            news_count=0,
            positive_ratio=0.0,
            negative_ratio=0.0,
            sentiment_momentum=0.0,
            buzz_level=0.0,
            last_updated=datetime.now()
        )
    
    # Get all sentiment scores
    sentiments = [item.sentiment_score for item in news_items]
    overall = sum(sentiments) / len(sentiments)
    
    # Count positive/negative
    positive = sum(1 for s in sentiments if s > 0.1)
    negative = sum(1 for s in sentiments if s < -0.1)
    neutral = len(sentiments) - positive - negative
    
    total = len(sentiments)
    positive_ratio = positive / total if total > 0 else 0.0
    negative_ratio = negative / total if total > 0 else 0.0
    
    # Calculate momentum
    cutoff = datetime.now().timestamp() - (config.NEWS_LOOKBACK_HOURS * 3600 / 2)
    recent = [item.sentiment_score for item in news_items if item.timestamp.timestamp() > cutoff]
    older = [item.sentiment_score for item in news_items if item.timestamp.timestamp() <= cutoff]
    
    if recent and older:
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        momentum = recent_avg - older_avg
    else:
        momentum = 0.0
    
    # Buzz level
    buzz_level = min(len(news_items) / 20, 1.0)
    
    # Get symbol (first item)
    symbol = news_items[0].symbol or ""
    
    return SentimentData(
        symbol=symbol,
        overall_sentiment=overall,
        news_count=len(news_items),
        positive_ratio=positive_ratio,
        negative_ratio=negative_ratio,
        sentiment_momentum=momentum,
        buzz_level=buzz_level,
        last_updated=datetime.now()
    )


def get_sentiment_score(features: SentimentFeatures) -> float:
    """
    Get sentiment score (0.0 to 1.0).
    
    Args:
        features: SentimentFeatures object
        
    Returns:
        Score from 0.0 to 1.0
    """
    # Neutral baseline is 0.5
    # Positive sentiment > 0.3 = bullish (score > 0.5)
    # Negative sentiment < -0.3 = bearish (score < 0.5)
    
    # Sentiment component
    sentiment_component = (features.sentiment_score + 1) / 2  # -1 to 1 -> 0 to 1
    
    # Buzz component (more news = higher confidence)
    buzz_component = features.buzz_level
    
    # Momentum component (improving sentiment = bullish)
    momentum_component = (features.sentiment_momentum + 1) / 2
    
    # Weighted average
    score = (
        sentiment_component * 0.5 +
        buzz_component * 0.3 +
        momentum_component * 0.2
    )
    
    return round(score, 3)


def should_avoid(
    features: SentimentFeatures,
    price_change_pct: float,
    news_score_threshold: float = config.NEWS_SCORE_THRESHOLD,
    price_threshold: float = config.MUTED_PRICE_THRESHOLD
) -> tuple[bool, str]:
    """
    Determine if we should avoid this setup.
    
    Kevin Xu's Rule #2: Positive news but price isn't moving = AVOID
    
    Args:
        features: SentimentFeatures
        price_change_pct: Recent price change (e.g., 0.01 = 1%)
        news_score_threshold: Minimum news score to consider "high"
        price_threshold: Maximum price change to consider "muted"
        
    Returns:
        (should_avoid, reason)
    """
    # Check if there's significant positive sentiment
    has_positive_news = (
        features.sentiment_score > 0.3 and
        features.buzz_level > 0.3 and
        features.news_count >= config.MIN_NEWS_COUNT
    )
    
    # Check if price is muted
    price_is_muted = abs(price_change_pct) < price_threshold
    
    if has_positive_news and price_is_muted:
        return True, (
            f"Positive sentiment (score: {features.sentiment_score:.2f}, "
            f"buzz: {features.buzz_level:.2f}) but price muted "
            f"({price_change_pct*100:.2f}%). Market not responding."
        )
    
    return False, ""
