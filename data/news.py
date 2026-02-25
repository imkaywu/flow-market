"""
News Data Fetching

Fetches news from Yahoo Finance and provides sentiment analysis.
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf
import pandas as pd

import config
from data.normalize import NewsItem, SentimentData


class NewsFetcher:
    """
    Fetches news from Yahoo Finance.
    
    Provides basic sentiment analysis based on keywords.
    """
    
    # Positive keywords
    POSITIVE_WORDS = {
        'bullish', 'surge', 'rally', 'breakout', 'gain', 'gains', 'profit',
        'profits', 'beat', 'strong', 'growth', 'upgrade', 'buy', 'calls',
        'moon', 'rocket', '🚀', 'higher', 'up', 'rising', 'soar', 'skyrocket',
        'breakthrough', 'record', 'best', 'outperform', 'exceed', 'growth'
    }
    
    # Negative keywords
    NEGATIVE_WORDS = {
        'bearish', 'crash', 'dump', 'tank', 'plunge', 'drop', 'fall', 'loss',
        'losses', 'miss', 'weak', 'decline', 'downgrade', 'sell', 'short',
        'puts', 'bear', '🐻', 'lawsuit', 'investigation', 'recall', 'delay',
        'bankruptcy', 'layoff', 'fired', 'scandal', 'fraud', 'lower', 'down',
        'warning', 'concern', 'risk', 'cut', 'cuts', 'warning', 'miss'
    }
    
    def __init__(
        self,
        lookback_hours: int = config.NEWS_LOOKBACK_HOURS,
        max_items: int = config.NEWS_MAX_ITEMS,
        request_delay: float = config.REQUEST_DELAY_SECONDS
    ):
        self.lookback_hours = lookback_hours
        self.max_items = max_items
        self.request_delay = request_delay
    
    def _analyze_sentiment(self, text: str) -> tuple[float, float]:
        """
        Analyze sentiment of text.
        
        Returns:
            (sentiment_score, relevance_score)
            - sentiment_score: -1.0 (negative) to 1.0 (positive)
            - relevance_score: 0.0 to 1.0
        """
        text_lower = text.lower()
        words = set(text_lower.split())
        
        positive_hits = len(words & self.POSITIVE_WORDS)
        negative_hits = len(words & self.NEGATIVE_WORDS)
        
        # Calculate sentiment
        total = positive_hits + negative_hits
        if total == 0:
            sentiment = 0.0
        else:
            sentiment = (positive_hits - negative_hits) / total
        
        # Relevance based on keyword density
        relevance = min(total / max(len(words) * 0.1, 1), 1.0)
        
        return sentiment, relevance
    
    def fetch_single(self, symbol: str) -> List[NewsItem]:
        """
        Fetch news for a single symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of NewsItem objects
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            cutoff = datetime.now() - timedelta(hours=self.lookback_hours)
            items = []
            
            for item in news[:self.max_items]:
                # Parse timestamp
                pub_date = item.get('providerPublishTime')
                if pub_date:
                    timestamp = datetime.fromtimestamp(pub_date)
                else:
                    timestamp = datetime.now()
                
                # Skip old news
                if timestamp < cutoff:
                    continue
                
                # Extract content
                title = item.get('title', '')
                summary = item.get('summary', '')
                content = f"{title} {summary}"
                
                # Analyze sentiment
                sentiment, relevance = self._analyze_sentiment(content)
                
                news_item = NewsItem(
                    symbol=symbol,
                    timestamp=timestamp,
                    title=title,
                    content=summary,
                    source='yahoo',
                    url=item.get('link'),
                    sentiment_score=sentiment,
                    relevance_score=relevance
                )
                
                items.append(news_item)
            
            return items
            
        except Exception as e:
            print(f"  [ERROR] Failed to fetch news for {symbol}: {e}")
            return []
    
    def fetch_batch(self, symbols: list[str]) -> Dict[str, List[NewsItem]]:
        """
        Fetch news for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol -> List[NewsItem]
        """
        results = {}
        
        # Initial delay to avoid rate limiting
        if symbols:
            print(f"  Waiting {self.request_delay}s before fetching news...")
            time.sleep(self.request_delay)
        
        for symbol in symbols:
            news_items = self.fetch_single(symbol)
            if news_items:
                results[symbol] = news_items
            time.sleep(self.request_delay)
        
        return results
    
    def fetch_all(self, symbols: list[str]) -> List[NewsItem]:
        """
        Fetch all news and return as flat list.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of all NewsItem objects
        """
        news_by_symbol = self.fetch_batch(symbols)
        
        all_news = []
        for items in news_by_symbol.values():
            all_news.extend(items)
        
        # Sort by timestamp (newest first)
        all_news.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_news


def analyze_sentiment(news_items: List[NewsItem], symbol: str) -> SentimentData:
    """
    Analyze sentiment from a list of news items.
    
    Args:
        news_items: List of NewsItem objects
        symbol: Stock symbol
        
    Returns:
        SentimentData object
    """
    if not news_items:
        return SentimentData(
            symbol=symbol,
            overall_sentiment=0.0,
            news_count=0,
            positive_ratio=0.0,
            negative_ratio=0.0,
            sentiment_momentum=0.0,
            buzz_level=0.0,
            last_updated=datetime.now()
        )
    
    sentiments = [item.sentiment_score for item in news_items]
    overall = sum(sentiments) / len(sentiments)
    
    positive = sum(1 for s in sentiments if s > 0.1)
    negative = sum(1 for s in sentiments if s < -0.1)
    neutral = len(sentiments) - positive - negative
    
    total = len(sentiments)
    positive_ratio = positive / total
    negative_ratio = negative / total
    
    # Calculate momentum (recent vs older)
    cutoff = datetime.now() - timedelta(hours=config.NEWS_LOOKBACK_HOURS / 2)
    recent = [item.sentiment_score for item in news_items if item.timestamp > cutoff]
    older = [item.sentiment_score for item in news_items if item.timestamp <= cutoff]
    
    if recent and older:
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        momentum = recent_avg - older_avg
    else:
        momentum = 0.0
    
    # Buzz level (normalized mention count)
    buzz_level = min(len(news_items) / 20, 1.0)
    
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


def fetch_news(symbols: list[str], hours: int = config.NEWS_LOOKBACK_HOURS) -> Dict[str, List[NewsItem]]:
    """
    Convenience function to fetch news for multiple symbols.
    
    Args:
        symbols: List of stock symbols
        hours: Hours to look back
        
    Returns:
        Dictionary mapping symbol -> List[NewsItem]
    """
    fetcher = NewsFetcher(lookback_hours=hours)
    return fetcher.fetch_batch(symbols)


def get_sentiment_features(symbols: list[str]) -> Dict[str, SentimentData]:
    """
    Get sentiment features for multiple symbols.
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Dictionary mapping symbol -> SentimentData
    """
    news = fetch_news(symbols)
    
    return {
        symbol: analyze_sentiment(items, symbol)
        for symbol, items in news.items()
    }
