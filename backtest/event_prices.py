"""Daily price fetcher for event-window analysis.

Fetches daily close prices from yfinance for a specific date range.
Separate from HistoricalCache to avoid polluting the backtest's quarterly price data.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_event_prices(
    tickers: list[str],
    start_date: date,
    end_date: date,
) -> dict[str, dict[str, tuple[float, float]]]:
    """Fetch daily prices for tickers during an event window.

    Args:
        tickers: List of ticker symbols.
        start_date: First date of the window.
        end_date: Last date of the window (inclusive).

    Returns:
        {ticker: {date_str: (close, adj_close)}} for each trading day in the window.
    """
    # yfinance end date is exclusive, so add 1 day
    end_str = (end_date + timedelta(days=1)).isoformat()
    start_str = start_date.isoformat()

    # Bulk download
    ticker_str = " ".join(tickers)
    df = yf.download(ticker_str, start=start_str, end=end_str, auto_adjust=False, progress=False)

    if df.empty:
        logger.warning(f"No price data returned for {start_date} to {end_date}")
        return {}

    results: dict[str, dict[str, tuple[float, float]]] = {}

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                close_series = df["Close"]
                adj_series = df["Adj Close"]
            else:
                close_series = df["Close"][ticker]
                adj_series = df["Adj Close"][ticker]

            ticker_prices = {}
            for idx in close_series.index:
                date_str = idx.strftime("%Y-%m-%d")
                c = float(close_series[idx])
                a = float(adj_series[idx])
                if c > 0 and a > 0:
                    ticker_prices[date_str] = (c, a)

            if ticker_prices:
                results[ticker] = ticker_prices
        except (KeyError, TypeError):
            continue

    logger.info(f"Fetched event prices for {len(results)}/{len(tickers)} tickers ({start_date} to {end_date})")
    return results
