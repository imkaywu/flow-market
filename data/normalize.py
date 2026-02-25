"""
Data Normalization - Core Data Structures

Defines all data structures used throughout the application.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class Bar:
    """Represents a single price bar (candle)."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "unknown"


@dataclass
class NewsItem:
    """Represents a news article or social media post."""
    symbol: Optional[str]  # Can be None for market-wide news
    timestamp: datetime
    title: str
    content: str
    source: str  # e.g., 'yahoo', 'reddit', 'newsapi'
    url: Optional[str] = None
    sentiment_score: float = 0.0  # -1.0 to 1.0
    relevance_score: float = 0.0  # 0.0 to 1.0


@dataclass
class SentimentData:
    """Aggregated sentiment data for a symbol."""
    symbol: str
    overall_sentiment: float  # -1.0 to 1.0
    news_count: int
    positive_ratio: float  # 0.0 to 1.0
    negative_ratio: float  # 0.0 to 1.0
    sentiment_momentum: float  # Change in sentiment over time
    buzz_level: float  # 0.0 to 1.0 (volume of mentions)
    last_updated: datetime


@dataclass
class PriceData:
    """Processed price data for a symbol."""
    symbol: str
    df: Any  # pandas DataFrame with OHLCV data
    last_updated: datetime
    period: str = "1d"
    interval: str = "5m"


@dataclass
class VolumeFeatures:
    """Volume-based features."""
    z_score: float
    relative_volume: float
    volume_percentile: float
    volume_change_pct: float
    is_midday: bool


@dataclass
class PriceFeatures:
    """Price-based features."""
    returns_5m: float
    returns_1h: float
    returns_1d: float
    volatility_5m: float
    volatility_1h: float
    volatility_1d: float
    price_change_pct: float
    is_muted: bool


@dataclass
class TechnicalFeatures:
    """Technical indicator features."""
    rsi_14: float
    macd: float
    macd_signal: float
    macd_histogram: float
    sma_20: float
    sma_50: float
    sma_200: float
    ema_12: float
    ema_26: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: float  # 0-100%
    atr: float


@dataclass
class SentimentFeatures:
    """Sentiment-based features."""
    sentiment_score: float
    buzz_level: float
    sentiment_momentum: float
    news_count: int
    positive_ratio: float
    negative_ratio: float


@dataclass
class AllFeatures:
    """Combined features for a symbol."""
    symbol: str
    volume: VolumeFeatures
    price: PriceFeatures
    technical: TechnicalFeatures
    sentiment: SentimentFeatures
    last_updated: datetime


@dataclass
class Signal:
    """Trading signal for a symbol."""
    symbol: str
    recommendation: str  # STRONG_BUY, BUY, WATCH, AVOID, NO_SIGNAL
    score: float  # 0.0 to 1.0
    
    # Signal components
    volume_score: float = 0.0
    momentum_score: float = 0.0
    technical_score: float = 0.0
    sentiment_score: float = 0.0
    
    # Details
    reason: str = ""
    is_attention: bool = False  # Rule #1: Volume spike
    is_avoid: bool = False     # Rule #2: News/price divergence
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    price: float = 0.0
    volume: float = 0.0
    price_change_pct: float = 0.0
    
    # Features (optional, for debugging)
    features: Optional[AllFeatures] = None


@dataclass
class WatchlistItem:
    """An item in the watchlist."""
    symbol: str
    score: float
    recommendation: str
    price: float
    price_change_pct: float
    volume: float
    volume_spike: bool
    sentiment_score: float
    added_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "score": round(self.score, 3),
            "recommendation": self.recommendation,
            "price": round(self.price, 2),
            "price_change_pct": round(self.price_change_pct * 100, 2),
            "volume": int(self.volume),
            "volume_spike": self.volume_spike,
            "sentiment_score": round(self.sentiment_score, 3),
            "added_at": self.added_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
