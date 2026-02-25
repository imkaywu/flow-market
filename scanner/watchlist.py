"""
Watchlist Management

Manages the ranked watchlist of top N stocks.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path

import config
from data.normalize import Signal, WatchlistItem


class Watchlist:
    """
    Manages the ranked watchlist.
    
    Keeps track of top N stocks with signals.
    """
    
    def __init__(
        self,
        max_size: int = config.TOP_N_WATCHLIST,
        expiry_hours: int = config.WATCHLIST_EXPIRY_HOURS
    ):
        self.max_size = max_size
        self.expiry_hours = expiry_hours
        self.items: Dict[str, WatchlistItem] = {}
    
    def add(self, signal: Signal) -> None:
        """
        Add a signal to the watchlist.
        
        Args:
            signal: Signal object
        """
        # Skip AVOID signals
        if signal.recommendation == "AVOID":
            return
        
        # Skip NO_SIGNAL
        if signal.recommendation == "NO_SIGNAL" or signal.score < config.ALERT_MIN_SCORE:
            return
        
        # Create watchlist item
        item = WatchlistItem(
            symbol=signal.symbol,
            score=signal.score,
            recommendation=signal.recommendation,
            price=signal.price,
            price_change_pct=signal.price_change_pct / 100,  # Convert to decimal
            volume=signal.volume,
            volume_spike=signal.is_attention,
            sentiment_score=signal.sentiment_score,
            added_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.items[signal.symbol] = item
    
    def update(self, signals: List[Signal]) -> None:
        """
        Update watchlist with new signals.
        
        Args:
            signals: List of Signal objects
        """
        # Add all signals
        for signal in signals:
            self.add(signal)
        
        # Remove expired items
        self._cleanup_expired()
        
        # Keep only top N by score
        self._trim_to_top_n()
    
    def _cleanup_expired(self) -> None:
        """Remove items older than expiry hours."""
        cutoff = datetime.now() - timedelta(hours=self.expiry_hours)
        
        expired = [
            symbol for symbol, item in self.items.items()
            if item.last_updated < cutoff
        ]
        
        for symbol in expired:
            del self.items[symbol]
    
    def _trim_to_top_n(self) -> None:
        """Keep only top N items by score."""
        if len(self.items) <= self.max_size:
            return
        
        # Sort by score
        sorted_items = sorted(
            self.items.items(),
            key=lambda x: x[1].score,
            reverse=True
        )
        
        # Keep top N
        self.items = dict(sorted_items[:self.max_size])
    
    def get_all(self) -> List[WatchlistItem]:
        """
        Get all watchlist items sorted by score.
        
        Returns:
            List of WatchlistItem objects
        """
        items = list(self.items.values())
        items.sort(key=lambda x: x.score, reverse=True)
        return items
    
    def get_top_n(self, n: Optional[int] = None) -> List[WatchlistItem]:
        """
        Get top N items.
        
        Args:
            n: Number of items (default: max_size)
            
        Returns:
            List of WatchlistItem objects
        """
        items = self.get_all()
        return items[:n] if n else items
    
    def get_by_symbol(self, symbol: str) -> Optional[WatchlistItem]:
        """Get item by symbol."""
        return self.items.get(symbol)
    
    def clear(self) -> None:
        """Clear the watchlist."""
        self.items.clear()
    
    def to_list(self) -> List[dict]:
        """Convert to list of dictionaries."""
        return [item.to_dict() for item in self.get_all()]
    
    def save(self, filepath: str) -> None:
        """Save watchlist to file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "items": self.to_list()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str) -> bool:
        """Load watchlist from file."""
        if not Path(filepath).exists():
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Clear current
            self.items.clear()
            
            # Load items
            for item_data in data.get('items', []):
                item = WatchlistItem(
                    symbol=item_data['symbol'],
                    score=item_data['score'],
                    recommendation=item_data['recommendation'],
                    price=item_data['price'],
                    price_change_pct=item_data['price_change_pct'],
                    volume=item_data['volume'],
                    volume_spike=item_data['volume_spike'],
                    sentiment_score=item_data['sentiment_score'],
                    added_at=datetime.fromisoformat(item_data['added_at']),
                    last_updated=datetime.fromisoformat(item_data['last_updated'])
                )
                self.items[item.symbol] = item
            
            return True
            
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            return False
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __repr__(self) -> str:
        return f"Watchlist(items={len(self.items)}, max={self.max_size})"
