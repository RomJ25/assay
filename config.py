"""Central configuration for Assay — value + quality stock screener."""

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
BATCH_SIZE = int(os.environ.get("ASSAY_BATCH_SIZE", 120))
BATCH_DELAY_SECONDS = int(os.environ.get("ASSAY_BATCH_DELAY", 3))
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

# Buy/hold spread (Novy-Marx & Velikov, "Assaying Anomalies", SSRN 4338007).
# Asymmetric thresholds: CB classification requires the BUY bar (default = HIGH);
# stocks with V/Q in [HIGH, BUY) but not ≥ BUY land in QUALITY GROWTH PREMIUM —
# a "hold" bucket in selective-sell mode. Setting BUY > HIGH cuts turnover by
# admitting fewer new positions while letting existing high-conviction names
# drift through the hold band before sale.
def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

BUY_VALUE_THRESHOLD = _env_int("ASSAY_BUY_VALUE_THRESHOLD", VALUE_HIGH_THRESHOLD)
BUY_QUALITY_THRESHOLD = _env_int("ASSAY_BUY_QUALITY_THRESHOLD", QUALITY_HIGH_THRESHOLD)
QUALITY_SINGLE_SOURCE_PENALTY = 0.8  # 20% discount for single-signal quality
MIN_PIOTROSKI_F = _env_int("ASSAY_MIN_PIOTROSKI_F", 6)  # Minimum raw F-Score (0-9) for conviction buy; below → WATCH LIST
def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")

RD_ADDBACK_ENABLED = _env_bool("ASSAY_RD_ADDBACK_ENABLED", True)  # Novy-Marx & Medhat 2025
SAFETY_ENABLED = _env_bool("ASSAY_SAFETY_ENABLED", True)  # AQR QMJ (Asness et al. 2019)
REVENUE_GATE_ENABLED = _env_bool("ASSAY_REVENUE_GATE_ENABLED", True)  # Chen et al. 2014

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

# ── Backtest ──────────────────────────────────────────────────────────
BACKTEST_DEFAULT_YEARS = 4
BACKTEST_FILING_LAG_DAYS = 75      # 60-day SEC deadline + 15-day buffer
BACKTEST_QUARTERS = [(3, 31), (6, 30), (9, 30), (12, 31)]
BACKTEST_PRICE_LOOKBACK_DAYS = 5   # max days backward to find trading day

# ── Momentum Gate ─────────────────────────────────────────────────────
MOMENTUM_LOOKBACK_MONTHS = 12
MOMENTUM_SKIP_MONTHS = 1           # skip most recent month (short-term reversal)
MOMENTUM_GATE_PERCENTILE = _env_int("ASSAY_MOMENTUM_GATE_PERCENTILE", 25)  # exclude bottom % momentum from RESEARCH CANDIDATE

# ── Transaction Costs ────────────────────────────────────────────────
TCOST_BPS_ROUNDTRIP = 10  # basis points per full rebalance (Frazzini et al. JFE: ~10 for S&P 500)

# ── Portfolio Construction ───────────────────────────────────────────
MIN_PORTFOLIO_SIZE = 0  # 0 = off (CB only); 30+ recommended for factor capture
# When CB has fewer picks than this, top WATCH LIST stocks (by conviction) backfill.

# ── Sector-Relative Scoring ──────────────────────────────────────────
def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default

SECTOR_RELATIVE_BLEND = _env_float("ASSAY_SECTOR_RELATIVE_BLEND", 0.3)  # when --sector-relative: 70% absolute + 30% within-sector by default
