"""Central configuration for Assay — S&P 500 value + quality screener."""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(os.environ.get("ASSAY_ROOT", os.environ.get("SCREENER_ROOT", Path(__file__).resolve().parent)))
RESULTS_DIR = Path(os.environ.get("ASSAY_RESULTS", os.environ.get("SCREENER_RESULTS", PROJECT_ROOT / "results")))
CACHE_DB_PATH = Path(os.environ.get("ASSAY_CACHE_DB", os.environ.get("SCREENER_CACHE_DB", PROJECT_ROOT / "storage" / "cache.db")))

# ── S&P 500 List ──────────────────────────────────────────────────────
SP500_WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SP500_CACHE_TTL_HOURS = 168  # 7 days

# ── Data Fetching ─────────────────────────────────────────────────────
FUNDAMENTALS_CACHE_TTL_HOURS = 168  # 7 days (financials update quarterly)
PRICE_CACHE_TTL_HOURS = 24  # 1 day
BATCH_SIZE = 85  # tickers per yahooquery batch
BATCH_DELAY_SECONDS = 5  # pause between batches to avoid 429s
YAHOOQUERY_MAX_WORKERS = 8
YAHOOQUERY_TIMEOUT = 10

# ── DCF Model (context only — not used for ranking) ──────────────────
RISK_FREE_RATE = 0.0431  # 10Y Treasury, FRED DGS10, April 2026
EQUITY_RISK_PREMIUM = 0.0423  # Damodaran implied ERP, Jan 2026
DEFAULT_TAX_RATE = 0.21  # US statutory corporate rate (fallback)
WACC_SAFETY_BUFFER = 0.005  # +0.5% added to calculated WACC for base case
DCF_PROJECTION_YEARS = 5
DCF_TERMINAL_GROWTH = 0.025  # 2.5% perpetual growth
DCF_MAX_GROWTH_RATE = 0.15  # cap historical growth at 15%
DCF_MIN_GROWTH_RATE = 0.0  # floor for base case
DCF_BULL_GROWTH_BONUS = 0.02
DCF_BEAR_WACC_PENALTY = 0.015
DCF_BEAR_GROWTH_PENALTY = 0.03

# ── Relative Model (context only) ────────────────────────────────────
PE_OUTLIER_MAX = 100
EVEBITDA_OUTLIER_MAX = 50

# ── Financial Sector Routing ─────────────────────────────────────────
# Sub-industries where DCF should be skipped
SKIP_DCF_SUBINDUSTRIES = {
    "Diversified Banks",
    "Regional Banks",
    "Investment Banking & Brokerage",
    "Life & Health Insurance",
    "Property & Casualty Insurance",
    "Reinsurance",
    "Multi-line Insurance",
    "Multi-Sector Holdings",
    "Asset Management & Custody Banks",
}

# ── Conviction Matrix Thresholds ─────────────────────────────────────
VALUE_HIGH_THRESHOLD = 70    # top 30% on value
VALUE_LOW_THRESHOLD = 40
QUALITY_HIGH_THRESHOLD = 70  # top 30% on quality
QUALITY_LOW_THRESHOLD = 40
QUALITY_SINGLE_SOURCE_PENALTY = 0.8  # 20% discount for single-signal quality

# ── Growth Model Thresholds (context display) ────────────────────────
REVENUE_CAGR_TIERS = [
    (0.15, 90),
    (0.10, 70),
    (0.05, 50),
    (0.00, 30),
]
PEG_TIERS = [
    (0.5, 90),
    (0.8, 70),
    (1.0, 50),
    (1.5, 30),
]
