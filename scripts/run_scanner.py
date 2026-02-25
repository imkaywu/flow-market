"""
Run Scanner - Main Entry Point

Runs the complete market scanner with continuous monitoring.
Run with: python scripts/run_scanner.py

Options:
    python scripts/run_scanner.py              # Run with defaults
    python scripts/run_scanner.py --once       # Run once and exit
    python scripts/run_scanner.py --iter 3     # Run 3 iterations
    python scripts/run_scanner.py --us-only    # US stocks only
    python scripts/run_scanner.py --hk-only    # HK stocks only
"""
import sys
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

import config
from scanner import Scanner


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Flow Market Scanner - Real-time market monitoring"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (no continuous scanning)"
    )
    
    parser.add_argument(
        "--iter", "--iterations",
        type=int,
        default=None,
        help="Number of iterations (default: infinite)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=config.SCAN_TIER_1_INTERVAL,
        help=f"Scan interval in minutes (default: {config.SCAN_TIER_1_INTERVAL})"
    )
    
    parser.add_argument(
        "--us-only",
        action="store_true",
        help="Scan US stocks only"
    )
    
    parser.add_argument(
        "--hk-only",
        action="store_true",
        help="Scan HK stocks only"
    )
    
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Specific symbols to scan"
    )
    
    parser.add_argument(
        "--watchlist",
        type=str,
        default="./watchlist.json",
        help="Watchlist file path (default: ./watchlist.json)"
    )
    
    return parser.parse_args()


def main():
    """Run the scanner."""
    args = parse_args()
    
    print("\n" + "="*60)
    print("🚀 FLOW MARKET SCANNER")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    # Determine symbols to scan
    if args.symbols:
        symbols = args.symbols
        print(f"Custom symbols: {symbols}")
    elif args.us_only:
        symbols = config.US_TIER_1
        print(f"US Tier 1: {len(symbols)} stocks")
    elif args.hk_only:
        symbols = config.HK_TIER_1
        print(f"HK Tier 1: {len(symbols)} stocks")
    else:
        symbols = config.US_TIER_1 + config.HK_TIER_1
        print(f"All Tier 1: {len(symbols)} stocks")
        print(f"   US: {len(config.US_TIER_1)}")
        print(f"   HK: {len(config.HK_TIER_1)}")
    
    print(f"Scan interval: {args.interval} minutes")
    print(f"Watchlist file: {args.watchlist}")
    
    if args.once:
        print("Mode: Run once")
    elif args.iter:
        print(f"Mode: {args.iter} iterations")
    else:
        print("Mode: Continuous (Ctrl+C to stop)")
    
    print("="*60 + "\n")
    
    # Create scanner
    scanner = Scanner(
        symbols=symbols,
        interval_minutes=args.interval,
        watchlist_file=args.watchlist
    )
    
    # Run
    if args.once:
        # Run once
        signals = scanner.scan_once()
        scanner._print_top_signals(signals)
        
        print(f"\n✅ Scan complete!")
        print(f"   Signals: {len(signals)}")
        print(f"   Watchlist: {len(scanner.watchlist)} items")
        
    elif args.iter:
        # Run specific iterations
        scanner.run(max_iterations=args.iter)
        
    else:
        # Run continuously
        scanner.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Scanner stopped.")
        sys.exit(0)
