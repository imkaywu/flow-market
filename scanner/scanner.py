"""
Market Scanner

Main scanning loop that monitors the market and generates watchlist.
"""
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable

import pandas as pd

import config
from data.normalize import Signal, NewsItem, SentimentData
from data.prices import PriceFetcher, is_market_open
from data.news import NewsFetcher, analyze_sentiment
from signals.composite import generate_composite_signal, generate_signals_for_batch
from scanner.watchlist import Watchlist


class Scanner:
    """
    Main market scanner.
    
    Fetches data, generates signals, and maintains watchlist.
    """
    
    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        interval_minutes: int = config.SCAN_TIER_1_INTERVAL,
        watchlist_file: Optional[str] = None,
        on_signal: Optional[Callable[[Signal], None]] = None
    ):
        """
        Initialize scanner.
        
        Args:
            symbols: List of stock symbols to scan (default: config.TIER_1)
            interval_minutes: Scan interval in minutes
            watchlist_file: Optional file to save/load watchlist
            on_signal: Optional callback for each signal
        """
        self.symbols = symbols or (config.US_TIER_1 + config.HK_TIER_1)
        self.interval_minutes = interval_minutes
        self.watchlist_file = watchlist_file
        self.on_signal = on_signal
        
        # Data fetchers
        self.price_fetcher = PriceFetcher()
        self.news_fetcher = NewsFetcher()
        
        # Watchlist
        self.watchlist = Watchlist()
        
        # State
        self.is_running = False
        self.last_scan_time: Optional[datetime] = None
        
        # Load existing watchlist if file provided
        if watchlist_file:
            self.watchlist.load(watchlist_file)
    
    def fetch_all_data(self) -> tuple:
        """
        Fetch price and news data for all symbols.
        
        Returns:
            (price_data, news_data, sentiment_data)
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching price data for {len(self.symbols)} symbols...")
        
        # Fetch prices
        price_results = self.price_fetcher.fetch_batch(self.symbols)
        
        print(f"  -> Got price data for {len(price_results)} symbols")
        
        # Fetch news (for symbols with price data)
        news_symbols = list(price_results.keys())
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching news for {len(news_symbols)} symbols...")
        
        news_results = self.news_fetcher.fetch_batch(news_symbols)
        
        print(f"  -> Got news for {len(news_results)} symbols")
        
        # Analyze sentiment
        sentiment_results = {}
        for symbol, news_items in news_results.items():
            if news_items:
                sentiment_results[symbol] = analyze_sentiment(news_items, symbol)
        
        return price_results, news_results, sentiment_results
    
    def scan_once(self) -> List[Signal]:
        """
        Run one scan cycle.
        
        Returns:
            List of generated signals
        """
        # Fetch data
        price_data, news_data, sentiment_data = self.fetch_all_data()
        
        # Generate signals
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating signals...")
        
        signals = generate_signals_for_batch(price_data, news_data, sentiment_data)
        
        print(f"  -> Generated {len(signals)} signals")
        
        # Update watchlist
        self.watchlist.update(signals)
        
        # Save watchlist
        if self.watchlist_file:
            self.watchlist.save(self.watchlist_file)
        
        # Callback
        if self.on_signal:
            for signal in signals:
                self.on_signal(signal)
        
        self.last_scan_time = datetime.now()
        
        return signals
    
    def run(self, max_iterations: Optional[int] = None) -> None:
        """
        Run scanner continuously.
        
        Args:
            max_iterations: Optional max number of iterations (None = infinite)
        """
        self.is_running = True
        iteration = 0
        
        print(f"\n{'='*60}")
        print(f"🚀 Scanner started - monitoring {len(self.symbols)} symbols")
        print(f"   Interval: {self.interval_minutes} minutes")
        print(f"   Market open: {is_market_open()}")
        print(f"{'='*60}\n")
        
        try:
            while self.is_running:
                iteration += 1
                
                # Check if market is open
                if not is_market_open():
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Market closed. Waiting...")
                    time.sleep(60)  # Check again in 1 minute
                    continue
                
                # Run scan
                signals = self.scan_once()
                
                # Print top signals
                self._print_top_signals(signals)
                
                # Check if done
                if max_iterations and iteration >= max_iterations:
                    print(f"\nCompleted {max_iterations} iterations. Stopping.")
                    break
                
                # Wait for next iteration
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Waiting {self.interval_minutes} minutes...")
                time.sleep(self.interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\nScanner stopped by user.")
        
        finally:
            self.is_running = False
    
    def _print_top_signals(self, signals: List[Signal], n: int = 10) -> None:
        """Print top N signals."""
        if not signals:
            print("\n  No significant signals.")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 TOP {min(n, len(signals))} SIGNALS")
        print(f"{'='*60}")
        
        for i, signal in enumerate(signals[:n], 1):
            emoji = {
                "STRONG_BUY": "🚀",
                "BUY": "💰",
                "WATCH": "👀",
                "AVOID": "❌",
                "NO_SIGNAL": "⚪"
            }.get(signal.recommendation, "⚪")
            
            print(f"  {i:2}. {emoji} {signal.symbol:8} | {signal.recommendation:12} | "
                  f"score: {signal.score:.2f} | {signal.reason[:50]}")
        
        print(f"{'='*60}\n")
    
    def get_watchlist(self) -> List[Dict]:
        """Get current watchlist."""
        return self.watchlist.to_list()
    
    def stop(self) -> None:
        """Stop the scanner."""
        self.is_running = False


def run_scanner(
    symbols: Optional[List[str]] = None,
    interval: int = config.SCAN_TIER_1_INTERVAL,
    watchlist_file: str = "./watchlist.json",
    max_iterations: Optional[int] = None
) -> None:
    """
    Convenience function to run the scanner.
    
    Args:
        symbols: List of symbols (default: Tier 1)
        interval: Scan interval in minutes
        watchlist_file: File to save watchlist
        max_iterations: Max iterations (None = infinite)
    """
    scanner = Scanner(
        symbols=symbols,
        interval_minutes=interval,
        watchlist_file=watchlist_file
    )
    
    scanner.run(max_iterations=max_iterations)
