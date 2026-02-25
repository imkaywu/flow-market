"""
Price Features

Computes price-based features for trading signals.
"""
from datetime import datetime

import pandas as pd
import numpy as np

import config
from data.normalize import PriceFeatures


def compute_price_features(
    df: pd.DataFrame,
    muted_threshold: float = config.MUTED_PRICE_THRESHOLD
) -> PriceFeatures:
    """
    Compute price-based features.
    
    Args:
        df: DataFrame with 'Close' column
        muted_threshold: Threshold for muted price (e.g., 0.005 = 0.5%)
        
    Returns:
        PriceFeatures object
    """
    if df is None or len(df) < 2:
        return PriceFeatures(
            returns_5m=0.0,
            returns_1h=0.0,
            returns_1d=0.0,
            volatility_5m=0.0,
            volatility_1h=0.0,
            volatility_1d=0.0,
            price_change_pct=0.0,
            is_muted=True
        )
    
    closes = df['Close'].values
    n = len(closes)
    
    # Current price
    current_price = closes[-1]
    
    # Returns over different periods
    # 5m return (5 bars ago = ~25 min)
    lookback_5m = min(5, n - 1)
    returns_5m = (closes[-1] - closes[-lookback_5m]) / closes[-lookback_5m] if lookback_5m > 0 else 0.0
    
    # 1h return (12 bars ago = ~60 min)
    lookback_1h = min(12, n - 1)
    returns_1h = (closes[-1] - closes[-lookback_1h]) / closes[-lookback_1h] if lookback_1h > 0 else 0.0
    
    # 1d return (full period)
    returns_1d = (closes[-1] - closes[0]) / closes[0] if n > 1 else 0.0
    
    # Volatility over different periods
    # 5m volatility (last 5 bars)
    lookback_5m_vol = min(5, n)
    returns_5m_arr = np.diff(closes[-lookback_5m_vol:]) / closes[-lookback_5m_vol:-1]
    volatility_5m = np.std(returns_5m_arr) if len(returns_5m_arr) > 0 else 0.0
    
    # 1h volatility (last 12 bars)
    lookback_1h_vol = min(12, n)
    returns_1h_arr = np.diff(closes[-lookback_1h_vol:]) / closes[-lookback_1h_vol:-1]
    volatility_1h = np.std(returns_1h_arr) if len(returns_1h_arr) > 0 else 0.0
    
    # 1d volatility (all bars)
    returns_arr = np.diff(closes) / closes[:-1]
    volatility_1d = np.std(returns_arr) if len(returns_arr) > 0 else 0.0
    
    # Price change percentage (latest vs previous)
    if n >= 2 and closes[-2] > 0:
        price_change_pct = (closes[-1] - closes[-2]) / closes[-2]
    else:
        price_change_pct = 0.0
    
    # Is muted?
    is_muted = abs(returns_1h) < muted_threshold
    
    return PriceFeatures(
        returns_5m=round(returns_5m * 100, 3),
        returns_1h=round(returns_1h * 100, 3),
        returns_1d=round(returns_1d * 100, 3),
        volatility_5m=round(volatility_5m * 100, 3),
        volatility_1h=round(volatility_1h * 100, 3),
        volatility_1d=round(volatility_1d * 100, 3),
        price_change_pct=round(price_change_pct * 100, 3),
        is_muted=is_muted
    )


def get_momentum_score(features: PriceFeatures) -> float:
    """
    Get momentum score (0.0 to 1.0).
    
    Args:
        features: PriceFeatures object
        
    Returns:
        Score from 0.0 to 1.0 based on momentum
    """
    # Strongest momentum in either direction gets higher score
    momentum = abs(features.returns_1h)
    
    # Normalize (cap at 5% = 1.0)
    score = min(momentum / 5.0, 1.0)
    
    return round(score, 3)


def detect_breakout(
    features: PriceFeatures,
    threshold: float = config.BREAKOUT_THRESHOLD
) -> str:
    """
    Detect if price is breaking out.
    
    Args:
        features: PriceFeatures object
        threshold: Breakout threshold (e.g., 0.02 = 2%)
        
    Returns:
        'up', 'down', or 'none'
    """
    if features.returns_1h > threshold:
        return 'up'
    elif features.returns_1h < -threshold:
        return 'down'
    else:
        return 'none'
