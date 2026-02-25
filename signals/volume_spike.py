"""
Volume Spike Signal

Rule #1: Detect mid-day volume spikes - PAY ATTENTION
"""
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

import config
from data.normalize import VolumeFeatures, Signal
from features.volume import compute_volume_features, detect_volume_spike, get_volume_score


def generate_volume_spike_signal(
    symbol: str,
    df: pd.DataFrame,
    require_midday: bool = True
) -> Signal:
    """
    Generate volume spike signal.
    
    Kevin Xu's Rule #1: PAY ATTENTION when there's a mid-day volume spike
    
    Args:
        symbol: Stock symbol
        df: DataFrame with OHLCV data
        require_midday: Only signal during mid-day hours
        
    Returns:
        Signal object
    """
    # Compute volume features
    volume_features = compute_volume_features(df)
    
    # Check if volume spike detected
    has_spike = detect_volume_spike(volume_features)
    
    # Get score
    volume_score = get_volume_score(volume_features)
    
    # Determine recommendation
    if not has_spike:
        return Signal(
            symbol=symbol,
            recommendation="NO_SIGNAL",
            score=0.0,
            volume_score=volume_score,
            reason="No volume spike detected",
            is_attention=False,
            timestamp=datetime.now()
        )
    
    # Check mid-day requirement
    if require_midday and not volume_features.is_midday:
        return Signal(
            symbol=symbol,
            recommendation="NO_SIGNAL",
            score=volume_score * 0.5,  # Reduce score for non-midday
            volume_score=volume_score,
            reason=f"Volume spike detected but outside mid-day (is_midday={volume_features.is_midday})",
            is_attention=False,
            timestamp=datetime.now()
        )
    
    # Strong volume spike during mid-day
    recommendation = "STRONG_BUY" if volume_score > 0.7 else "BUY"
    
    reason = (
        f"Volume spike detected: "
        f"z={volume_features.z_score:.1f}, "
        f"rel_vol={volume_features.relative_volume:.1f}x, "
        f"percentile={volume_features.volume_percentile:.0f}%"
    )
    
    return Signal(
        symbol=symbol,
        recommendation=recommendation,
        score=volume_score,
        volume_score=volume_score,
        reason=reason,
        is_attention=True,
        timestamp=datetime.now()
    )
