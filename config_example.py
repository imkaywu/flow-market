"""
Configuration file for API keys and settings.

Copy this file to config_local.py and fill in your API keys:

    cp config_example.py config_local.py

Then edit config_local.py with your keys.

NOTE: config_local.py is in .gitignore - your keys are safe!
"""
import os

# ============================================================================
# API KEYS - Copy to config_local.py and fill in your keys
# ============================================================================

# Alpaca API Keys (US Stocks - Real-time)
# Get free keys at: https://alpaca.markets/
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_USE_PAPER = True  # Set to False for live trading

# Finnhub API Keys (US + HK Stocks)
# Get free key at: https://finnhub.io/
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# Alpha Vantage API Keys (US Stocks)
# Get free key at: https://www.alphavantage.co/support/#api-key
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "")

# NewsAPI (optional - for more news sources)
# Get free key at: https://newsapi.org/
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")


# ============================================================================
# Override settings from config.py
# ============================================================================

# Uncomment and modify as needed:
# US_TIER_1 = ["AAPL", "MSFT", "GOOGL", ...]
# HK_TIER_1 = ["0700.HK", "9988.HK", ...]
# SCAN_TIER_1_INTERVAL = 5
