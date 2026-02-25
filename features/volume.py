"""
Volume Features

Computes volume-based features for trading signals.
"""
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

import config
from data.normalize import VolumeFeatures


def is_midday() -> bool:
    """
    Check if current time is during mid-day (avoid open/close noise).
    
    Returns:
        True if between 10:00 AM and 3:30 PM
    """
    now = datetime.now()
    current_time = now.time()
    
    # 10:00 AM to 3:30 PM
    start = datetime.now().replace(hour=10, minute=0, second=0).time()
    end = datetime.now().replace(hour=15, minute=30, second=0).time()
    
    return start <= current_time <= end


def compute_volume_features(
    df: pd.DataFrame,
    lookback_periods: int = 20
) -> VolumeFeatures:
    """
    Compute volume-based features.
    
    Args:
        df: DataFrame with 'Volume' column
        lookback_periods: Number of periods for comparison
        
    Returns:
        VolumeFeatures object
    """
    if df is None or len(df) < 10:
        return VolumeFeatures(
            z_score=0.0,
            relative_volume=1.0,
            volume_percentile=50.0,
            volume_change_pct=0.0,
            is_midday=is_midday()
        )
    
    volumes = df['Volume'].values
    
    # Latest volume
    current_volume = volumes[-1]
    
    # Previous volumes (excluding latest)
    previous_volumes = volumes[:-1]
    
    if len(previous_volumes) < 2:
        return VolumeFeatures(
            z_score=0.0,
            relative_volume=1.0,
            volume_percentile=50.0,
            volume_change_pct=0.0,
            is_midday=is_midday()
        )
    
    # Mean and std of previous volumes
    mean_vol = np.mean(previous_volumes)
    std_vol = np.std(previous_volumes)
    
    # Z-score
    if std_vol > 0:
        z_score = (current_volume - mean_vol) / std_vol
    else:
        z_score = 0.0
    
    # Relative volume
    if mean_vol > 0:
        relative_volume = current_volume / mean_vol
    else:
        relative_volume = 1.0
    
    # Volume percentile
    if len(previous_volumes) > 0:
        volume_percentile = (current_volume >= previous_volumes).mean() * 100
    else:
        volume_percentile = 50.0
    
    # Volume change percentage
    if len(volumes) >= 2 and volumes[-2] > 0:
        volume_change_pct = (current_volume - volumes[-2]) / volumes[-2]
    else:
        volume_change_pct = 0.0
    
    return VolumeFeatures(
        z_score=round(z_score, 2),
        relative_volume=round(relative_volume, 2),
        volume_percentile=round(volume_percentile, 1),
        volume_change_pct=round(volume_change_pct * 100, 2),
        is_midday=is_midday()
    )


def detect_volume_spike(
    features: VolumeFeatures,
    z_threshold: float = config.VOLUME_Z_THRESHOLD,
    rel_vol_threshold: float = config.RELATIVE_VOLUME_THRESHOLD,
    percentile_threshold: float = config.VOLUME_PERCENTILE_THRESHOLD
) -> bool:
    """
    Detect if there's a significant volume spike.
    
    Args:
        features: VolumeFeatures object
        z_threshold: Z-score threshold
        rel_vol_threshold: Relative volume threshold
        percentile_threshold: Volume percentile threshold
        
    Returns:
        True if volume spike detected
    """
    return (
        features.z_score > z_threshold or
        features.relative_volume > rel_vol_threshold or
        features.volume_percentile > percentile_threshold
    )


def get_volume_score(features: VolumeFeatures) -> float:
    """
    Get volume score (0.0 to 1.0).
    
    Args:
        features: VolumeFeatures object
        
    Returns:
        Score from 0.0 to 1.0
    """
    # Normalize z-score (cap at 5)
    z_score_norm = min(max(features.z_score / 5, 0), 1)
    
    # Normalize relative volume (cap at 4x)
    rel_vol_norm = min(max((features.relative_volume - 1) / 3, 0), 1)
    
    # Normalize percentile
    percentile_norm = features.volume_percentile / 100
    
    # Weighted average
    score = z_score_norm * 0.4 + rel_vol_norm * 0.4 + percentile_norm * 0.2
    
    return round(score, 3)
