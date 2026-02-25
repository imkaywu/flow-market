"""
Technical Indicators

Computes technical indicators: RSI, MACD, SMA, EMA, Bollinger Bands, ATR.
"""
from typing import Optional

import pandas as pd
import numpy as np

from data.normalize import TechnicalFeatures


def compute_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Compute Relative Strength Index.
    
    Args:
        prices: Series of prices
        period: RSI period (default 14)
        
    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral
    
    # Calculate price changes
    deltas = prices.diff()
    
    # Separate gains and losses
    gains = deltas.where(deltas > 0, 0)
    losses = -deltas.where(deltas < 0, 0)
    
    # Calculate average gain and loss
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0


def compute_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> tuple[float, float, float]:
    """
    Compute MACD.
    
    Args:
        prices: Series of prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        (macd, signal_line, histogram)
    """
    if len(prices) < slow + signal:
        return 0.0, 0.0, 0.0
    
    # Calculate EMAs
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    # MACD line
    macd = ema_fast - ema_slow
    
    # Signal line
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    
    # Histogram
    histogram = macd - signal_line
    
    return (
        float(macd.iloc[-1]),
        float(signal_line.iloc[-1]),
        float(histogram.iloc[-1])
    )


def compute_sma(prices: pd.Series, period: int) -> float:
    """
    Compute Simple Moving Average.
    
    Args:
        prices: Series of prices
        period: SMA period
        
    Returns:
        SMA value
    """
    if len(prices) < period:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
    
    return float(prices.rolling(window=period).mean().iloc[-1])


def compute_ema(prices: pd.Series, period: int) -> float:
    """
    Compute Exponential Moving Average.
    
    Args:
        prices: Series of prices
        period: EMA period
        
    Returns:
        EMA value
    """
    if len(prices) < period:
        return float(prices.iloc[-1]) if len(prices) > 0 else 0.0
    
    return float(prices.ewm(span=period, adjust=False).mean().iloc[-1])


def compute_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> tuple[float, float, float]:
    """
    Compute Bollinger Bands.
    
    Args:
        prices: Series of prices
        period: BB period
        num_std: Number of standard deviations
        
    Returns:
        (upper_band, middle_band, lower_band)
    """
    if len(prices) < period:
        middle = float(prices.iloc[-1]) if len(prices) > 0 else 0.0
        return middle, middle, middle
    
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    
    return (
        float(upper.iloc[-1]),
        float(sma.iloc[-1]),
        float(lower.iloc[-1])
    )


def compute_bb_position(
    prices: pd.Series,
    upper: float,
    middle: float,
    lower: float
) -> float:
    """
    Compute Bollinger Band position (0-100%).
    
    Args:
        prices: Series of prices
        upper: Upper band
        middle: Middle band (SMA)
        lower: Lower band
        
    Returns:
        Position (0-100)
    """
    if upper == lower:
        return 50.0
    
    current = float(prices.iloc[-1])
    position = (current - lower) / (upper - lower) * 100
    
    return round(max(0, min(100, position)), 1)


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """
    Compute Average True Range.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
        
    Returns:
        ATR value
    """
    if len(high) < 2:
        return 0.0
    
    # True Range = max(H-L, |H-PC|, |L-PC|)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    if len(true_range) < period:
        return float(true_range.mean())
    
    atr = true_range.rolling(window=period).mean()
    
    return float(atr.iloc[-1]) if not np.isnan(atr.iloc[-1]) else 0.0


def compute_technical_features(df: pd.DataFrame) -> TechnicalFeatures:
    """
    Compute all technical indicators.
    
    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns
        
    Returns:
        TechnicalFeatures object
    """
    if df is None or len(df) < 50:
        return TechnicalFeatures(
            rsi_14=50.0,
            macd=0.0,
            macd_signal=0.0,
            macd_histogram=0.0,
            sma_20=0.0,
            sma_50=0.0,
            sma_200=0.0,
            ema_12=0.0,
            ema_26=0.0,
            bb_upper=0.0,
            bb_middle=0.0,
            bb_lower=0.0,
            bb_position=50.0,
            atr=0.0
        )
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    # RSI
    rsi = compute_rsi(close, 14)
    
    # MACD
    macd, macd_signal, macd_hist = compute_macd(close)
    
    # SMAs
    sma_20 = compute_sma(close, 20)
    sma_50 = compute_sma(close, 50) if len(close) >= 50 else sma_20
    sma_200 = compute_sma(close, 200) if len(close) >= 200 else sma_50
    
    # EMAs
    ema_12 = compute_ema(close, 12)
    ema_26 = compute_ema(close, 26)
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = compute_bollinger_bands(close)
    bb_position = compute_bb_position(close, bb_upper, bb_middle, bb_lower)
    
    # ATR
    atr = compute_atr(high, low, close)
    
    return TechnicalFeatures(
        rsi_14=round(rsi, 1),
        macd=round(macd, 4),
        macd_signal=round(macd_signal, 4),
        macd_histogram=round(macd_hist, 4),
        sma_20=round(sma_20, 2),
        sma_50=round(sma_50, 2),
        sma_200=round(sma_200, 2),
        ema_12=round(ema_12, 2),
        ema_26=round(ema_26, 2),
        bb_upper=round(bb_upper, 2),
        bb_middle=round(bb_middle, 2),
        bb_lower=round(bb_lower, 2),
        bb_position=round(bb_position, 1),
        atr=round(atr, 4)
    )


def get_technical_score(features: TechnicalFeatures) -> float:
    """
    Get technical score (0.0 to 1.0).
    
    Based on multiple bullish/bearish indicators.
    
    Args:
        features: TechnicalFeatures object
        
    Returns:
        Score from 0.0 to 1.0
    """
    score = 0.0
    count = 0
    
    # RSI (0-100, 50 neutral)
    # Bullish: <30 or >70
    if features.rsi_14 < 30:
        score += (30 - features.rsi_14) / 30  # Oversold = bullish
    elif features.rsi_14 > 70:
        score += (features.rsi_14 - 70) / 30  # Overbought = potential reversal
    count += 1
    
    # MACD histogram (positive = bullish)
    if features.macd_histogram > 0:
        score += min(features.macd_histogram * 10, 1.0)
    else:
        score += max(features.macd_histogram * 10, -1.0)
    count += 1
    
    # Price above SMAs (bullish)
    # This would need price comparison, simplified here
    if features.sma_20 > features.sma_50:
        score += 0.5  # Short-term > long-term = bullish
    count += 1
    
    # BB position
    if features.bb_position < 20:  # Near lower band
        score += (20 - features.bb_position) / 20
    elif features.bb_position > 80:  # Near upper band
        score -= (features.bb_position - 80) / 20
    count += 1
    
    # Normalize to 0-1
    final_score = (score / count + 1) / 2
    
    return round(max(0, min(1, final_score)), 3)
