"""Point-in-time S&P 500 constituent data — eliminates survivorship bias.

Uses the fja05680/sp500 GitHub dataset which tracks daily S&P 500 membership
changes from 1996 to present. For each backtest rebalance date, returns the
ACTUAL stocks that were in the index at that time — not today's list.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from io import StringIO
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).parent.parent / "storage" / "sp500_historical.csv"
_SOURCE_URL = (
    "https://raw.githubusercontent.com/fja05680/sp500/master/"
    "S%26P%20500%20Historical%20Components%20%26%20Changes(01-17-2026).csv"
)


def _ensure_data() -> list[dict]:
    """Download and cache the historical constituents CSV."""
    if _CACHE_PATH.exists():
        with open(_CACHE_PATH, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    logger.info("Downloading historical S&P 500 constituent data...")
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(_SOURCE_URL, timeout=30)
    r.raise_for_status()

    _CACHE_PATH.write_text(r.text, encoding="utf-8")
    logger.info(f"Cached to {_CACHE_PATH}")

    return list(csv.DictReader(StringIO(r.text)))


def get_sp500_at_date(as_of: date) -> list[str]:
    """Return the S&P 500 constituent tickers as of a specific date.

    Finds the closest date on or before `as_of` in the historical dataset
    and returns that day's constituent list.

    Args:
        as_of: The date to look up.

    Returns:
        List of ticker symbols that were in the S&P 500 on that date.
    """
    rows = _ensure_data()
    as_of_str = as_of.isoformat()

    # Find the closest date on or before as_of
    valid_rows = [r for r in rows if r["date"] <= as_of_str]
    if not valid_rows:
        logger.warning(f"No historical data available for {as_of}")
        return []

    # Take the most recent date
    closest = max(valid_rows, key=lambda r: r["date"])
    tickers = [t.strip() for t in closest["tickers"].split(",") if t.strip()]

    logger.info(
        f"S&P 500 at {as_of} (data from {closest['date']}): "
        f"{len(tickers)} constituents"
    )
    return tickers


def get_all_historical_tickers(start_date: date, end_date: date) -> set[str]:
    """Return ALL tickers that were ever in the S&P 500 between two dates.

    This is the full universe needed for an unbiased backtest — includes
    stocks that were later removed.

    Args:
        start_date: Beginning of the backtest period.
        end_date: End of the backtest period.

    Returns:
        Set of all ticker symbols that appeared in the S&P 500 during the period.
    """
    rows = _ensure_data()
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    all_tickers: set[str] = set()
    for row in rows:
        if start_str <= row["date"] <= end_str:
            tickers = [t.strip() for t in row["tickers"].split(",") if t.strip()]
            all_tickers.update(tickers)

    logger.info(
        f"Historical universe {start_date} to {end_date}: "
        f"{len(all_tickers)} unique tickers"
    )
    return all_tickers
