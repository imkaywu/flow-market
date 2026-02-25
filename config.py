"""
Flow Market Scanner Configuration

Comprehensive settings for US and HK stock market scanning.
"""

# ============================================================================
# STOCK UNIVERSE - TIERED APPROACH
# ============================================================================

# Tier 1: Core Watch (processed every 5 minutes) - High priority
# These are high-liquidity stocks with good volume
US_TIER_1 = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "TSLA", "AVGO", "ORCL",
    "CRM", "ADBE", "NFLX", "INTC", "QCOM", "TXN", "AMAT", "MU", "LRCX", "KLAC",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "BLK", "SCHW", "C",
    # Healthcare
    "UNH", "JNJ", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "DHR", "BMY",
    # Consumer
    "WMT", "PG", "KO", "PEP", "COST", "HD", "NKE", "MCD", "SBUX", "TGT",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO",
    # Growth/Cloud
    "COIN", "PLTR", "SNOW", "DDOG", "CRWD", "NET", "ZM", "DOCU", "OKTA", "SPLK",
]

HK_TIER_1 = [
    "0700.HK",  # Tencent
    "9988.HK",  # Alibaba
    "3690.HK",  # Meituan
    "1024.HK",  # Kuaishou
    "9618.HK",  # JD.com
    "2319.HK",  # Mengniu Dairy
    "1918.HK",  # China Resources Land
    "0669.HK",  # China Everbright
    "2388.HK",  # BOC Hong Kong
    "0005.HK",  # HSBC
    "0939.HK",  # China Construction Bank
    "1398.HK",  # ICBC
    "3988.HK",  # Bank of China
    "0883.HK",  # China Gas
    "1109.HK",  # China Land
]

# Tier 2: Extended Watch (processed every 30 minutes) - Medium priority
# Add more stocks here as needed
US_TIER_2 = [
    # ETFs
    "SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLP", "XLI",
    # More Tech
    "UBER", "LYFT", "DASH", "ABNB", "PINS", "SNAP", "MSTR", "RIVN", "LCID", "NIO",
    # More Finance
    "AXP", "USB", "PNC", "TFC", "COF", "AIG", "MET", "PRU", "AFL", "TRV",
    # More Healthcare
    "CVS", "CI", "HUM", "MCK", "CAH", "ABC", "MCK", "ISRG", "SYK", "MDT",
    # More Consumer
    "DIS", "CMCSA", "T", "VZ", "TMUS", "CHWY", "ETSY", "ROST", "TJX", "DLTR",
]

HK_TIER_2 = [
    "1919.HK",  # China Everbright
    "1088.HK",  # China Shenhua
    "1177.HK",  # Sino Biopharm
    "2269.HK",  # WuXi Biologics
    "6033.HK",  # China CITIC
    "0018.HK",  # China Gas Holdings
    "0330.HK",  # China Jiujiang
    "1339.HK",  # China People Insurance
    "2628.HK",  # China Life
    "6837.HK",  # Haitong Securities
]

# All stocks combined (for reference)
ALL_US_STOCKS = US_TIER_1 + US_TIER_2
ALL_HK_STOCKS = HK_TIER_1 + HK_TIER_2
ALL_STOCKS = ALL_US_STOCKS + ALL_HK_STOCKS


# ============================================================================
# FETCH SETTINGS
# ============================================================================

# Price data
PRICE_PERIOD = "1d"           # yfinance period (1d, 5d, 1mo, etc.)
PRICE_INTERVAL = "5m"        # yfinance interval (1m, 5m, 15m, 1h, etc.)

# News data
NEWS_LOOKBACK_HOURS = 24      # How far back to fetch news
NEWS_MAX_ITEMS = 50           # Max news items per stock

# Fetch intervals (minutes)
SCAN_TIER_1_INTERVAL = 5     # Core watch interval
SCAN_TIER_2_INTERVAL = 30    # Extended watch interval


# ============================================================================
# FILTERS
# ============================================================================

# Price filters
MIN_PRICE = 5.0               # Minimum stock price ($)
MAX_PRICE = 50000.0           # Maximum stock price ($)

# Volume filters
MIN_AVG_VOLUME = 1_000_000    # Minimum average daily volume
MIN_RELATIVE_VOLUME = 0.5     # Minimum relative volume (vs 20-day avg)

# Market cap filters (optional)
MIN_MARKET_CAP = 1_000_000_000  # $1B minimum


# ============================================================================
# SIGNAL THRESHOLDS
# ============================================================================

# Volume spike detection
VOLUME_Z_THRESHOLD = 2.5          # Z-score threshold (std deviations)
RELATIVE_VOLUME_THRESHOLD = 2.0   # Relative volume (x times avg)
VOLUME_PERCENTILE_THRESHOLD = 80  # Volume percentile (0-100)

# Price movement detection
MUTED_PRICE_THRESHOLD = 0.005     # 0.5% - what counts as "muted"
BREAKOUT_THRESHOLD = 0.02        # 2% - what counts as breakout

# Sentiment detection
NEWS_SCORE_THRESHOLD = 0.7       # "High" news activity threshold
SENTIMENT_THRESHOLD = 0.3         # Positive sentiment threshold
MIN_NEWS_COUNT = 3                # Minimum news items for sentiment

# Mid-day detection (avoid open/close noise)
MARKET_OPEN_BUFFER_MIN = 30       # Minutes after open to start
MARKET_CLOSE_BUFFER_MIN = 30     # Minutes before close to stop


# ============================================================================
# SCANNER SETTINGS
# ============================================================================

# Watchlist
TOP_N_WATCHLIST = 20              # Number of stocks in watchlist
WATCHLIST_EXPIRY_HOURS = 24       # How long to keep stocks in watchlist

# Scoring weights (for composite score)
WEIGHT_VOLUME_SPIKE = 0.35        # Weight for volume signal
WEIGHT_PRICE_MOMENTUM = 0.25      # Weight for price momentum
WEIGHT_TECHNICAL = 0.20           # Weight for technical indicators
WEIGHT_SENTIMENT = 0.20           # Weight for sentiment

# Alert settings
ALERT_MIN_SCORE = 0.5             # Minimum score to generate alert
ENABLE_NOTIFICATIONS = False      # Enable email/SMS notifications


# ============================================================================
# DATA STORAGE (for future use)
# ============================================================================

# Storage settings
DATA_DIR = "./data_store"         # Local data directory
CACHE_TTL_HOURS = 24              # Cache time-to-live
MAX_HISTORY_DAYS = 30              # Days of history to keep

# Enable caching
ENABLE_PRICE_CACHE = True
ENABLE_NEWS_CACHE = True
ENABLE_FEATURE_CACHE = True


# ============================================================================
# RUNTIME SETTINGS
# ============================================================================

# Logging
LOG_LEVEL = "INFO"                 # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = False               # Log to file as well

# Parallel fetching (for future scale)
ENABLE_PARALLEL_FETCH = False     # Multi-threaded fetching
MAX_WORKERS = 10                  # Number of parallel workers

# Timeouts
FETCH_TIMEOUT_SECONDS = 10        # Timeout for each API call
REQUEST_DELAY_SECONDS = 2.0        # Delay between requests (Yahoo Finance rate limit)
MAX_RETRIES = 3                   # Max retries for failed requests
RETRY_DELAY_BASE = 5              # Base delay for retries (seconds)


# ============================================================================
# MARKET HOURS (US Eastern Time)
# ============================================================================

# US Market Hours
US_MARKET_OPEN = "09:30"          # US market open
US_MARKET_CLOSE = "16:00"         # US market close

# HK Market Hours
HK_MARKET_OPEN = "09:30"          # HK market open
HK_MARKET_CLOSE = "16:00"         # HK market close (lunch break: 12:00-13:00)

# Weekend handling
MARKET_DAYS = [0, 1, 2, 3, 4]     # Monday=0, Friday=4
