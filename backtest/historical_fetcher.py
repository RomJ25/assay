"""Fetch and cache historical financial data for backtesting."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import pandas as pd
import yfinance as yf
from yahooquery import Ticker

from config import (
    BATCH_DELAY_SECONDS,
    BATCH_SIZE,
    BACKTEST_PRICE_LOOKBACK_DAYS,
    YAHOOQUERY_MAX_WORKERS,
    YAHOOQUERY_TIMEOUT,
)
from backtest.cache import HistoricalCache

logger = logging.getLogger(__name__)


def fetch_historical_data(
    tickers: list[str],
    sp500_info: list[dict],
    cache: HistoricalCache,
    rebalance_dates: list[date],
) -> None:
    """Populate cache with all data needed for backtesting.

    Three-phase fetch:
    1. Financials via yahooquery (batch)
    2. Prices via yfinance (single bulk download)
    3. Splits via yfinance (threaded per-ticker)
    """
    # Cache S&P 500 list
    if cache.get_sp500() is None:
        cache.set_sp500(sp500_info)
        logger.info(f"Cached S&P 500 list ({len(sp500_info)} tickers)")

    _fetch_financials(tickers, cache)
    _fetch_prices(tickers, rebalance_dates, cache)
    _fetch_splits(tickers, cache)


def _fetch_financials(tickers: list[str], cache: HistoricalCache) -> None:
    """Fetch raw financial statements via yahooquery and cache as JSON."""
    cached = cache.get_all_cached_financial_tickers()
    missing = [t for t in tickers if t not in cached]

    if not missing:
        logger.info("All financials cached")
        return

    logger.info(f"Fetching financials for {len(missing)} tickers...")
    batches = [missing[i:i + BATCH_SIZE] for i in range(0, len(missing), BATCH_SIZE)]

    for i, batch in enumerate(batches, 1):
        logger.info(f"Financials batch {i}/{len(batches)}: {len(batch)} tickers...")
        try:
            data = _fetch_financials_batch(batch)
            for ticker, raw in data.items():
                cache.set_financials(ticker, raw)
            logger.info(f"  Cached {len(data)}/{len(batch)} tickers")
        except Exception as e:
            logger.error(f"  Batch {i} failed: {e}")

        if i < len(batches):
            time.sleep(BATCH_DELAY_SECONDS)


def _fetch_financials_batch(batch: list[str]) -> dict[str, dict]:
    """Fetch one batch of tickers via yahooquery, return raw data as dicts."""
    t = Ticker(
        batch,
        asynchronous=True,
        max_workers=YAHOOQUERY_MAX_WORKERS,
        progress=False,
        timeout=YAHOOQUERY_TIMEOUT,
    )

    def _get(fn, name):
        try:
            result = fn()
            if isinstance(result, str):
                logger.warning(f"{name} returned error: {result[:100]}")
                return pd.DataFrame()
            return result
        except Exception as e:
            logger.warning(f"{name} failed: {e}")
            return pd.DataFrame()

    income_df = _get(lambda: t.income_statement(frequency="a", trailing=True), "income_statement")
    time.sleep(1)
    balance_df = _get(lambda: t.balance_sheet(frequency="a"), "balance_sheet")
    time.sleep(1)
    cashflow_df = _get(lambda: t.cash_flow(frequency="a", trailing=True), "cash_flow")

    results = {}
    for ticker in batch:
        inc_rows = _df_to_records(income_df, ticker)
        bal_rows = _df_to_records(balance_df, ticker)
        cf_rows = _df_to_records(cashflow_df, ticker)

        if not inc_rows and not bal_rows:
            continue

        results[ticker] = {
            "income": inc_rows,
            "balance": bal_rows,
            "cashflow": cf_rows,
        }

    return results


def _df_to_records(df: pd.DataFrame, ticker: str) -> list[dict]:
    """Extract rows for a ticker from a yahooquery DataFrame as list of dicts.

    Preserves asOfDate and periodType for later filtering.
    """
    if df is None or isinstance(df, str) or df.empty:
        return []

    try:
        # Filter to this ticker
        if isinstance(df.index, pd.MultiIndex):
            level_values = df.index.get_level_values(0)
            if ticker in level_values:
                filtered = df.loc[ticker]
            else:
                return []
        elif "symbol" in df.columns:
            filtered = df[df["symbol"] == ticker]
        elif df.index.name == "symbol":
            filtered = df[df.index == ticker]
        else:
            return []

        # Convert to list of dicts, preserving all columns
        records = filtered.reset_index(drop=True).to_dict("records")

        # Convert Timestamps to ISO strings for JSON serialization
        for record in records:
            for key, val in record.items():
                if isinstance(val, pd.Timestamp):
                    record[key] = val.isoformat()

        return records
    except Exception as e:
        logger.debug(f"Failed to extract {ticker} records: {e}")
        return []


def _fetch_prices(
    tickers: list[str],
    rebalance_dates: list[date],
    cache: HistoricalCache,
) -> None:
    """Fetch historical prices for all tickers + SPY via yfinance bulk download."""
    # Check which dates need prices
    dates_needed = []
    for d in rebalance_dates:
        if not cache.has_prices_for_date(d.isoformat()):
            dates_needed.append(d)

    if not dates_needed:
        logger.info("All prices cached")
        return

    all_symbols = list(set(tickers + ["SPY"]))
    logger.info(f"Downloading prices for {len(all_symbols)} symbols (10y history)...")

    try:
        df = yf.download(
            all_symbols,
            period="10y",
            auto_adjust=False,
            threads=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"Price download failed: {e}")
        return

    if df.empty:
        logger.warning("Price download returned empty DataFrame")
        return

    # Extract prices for each rebalance date
    rows_to_cache = []
    for rebal_date in rebalance_dates:
        date_prices = _extract_prices_near_date(df, all_symbols, rebal_date)
        for ticker, (close, adj_close) in date_prices.items():
            rows_to_cache.append((ticker, rebal_date.isoformat(), close, adj_close))

    if rows_to_cache:
        cache.set_prices(rows_to_cache)
        logger.info(f"Cached {len(rows_to_cache)} price entries across {len(rebalance_dates)} dates")


def _extract_prices_near_date(
    df: pd.DataFrame,
    symbols: list[str],
    target_date: date,
) -> dict[str, tuple[float, float]]:
    """Find the nearest trading day price on or before target_date.

    Returns {ticker: (close, adj_close)}.
    """
    target = pd.Timestamp(target_date)
    lookback = pd.Timestamp(target_date) - pd.Timedelta(days=BACKTEST_PRICE_LOOKBACK_DAYS)

    # Filter to the lookback window
    mask = (df.index >= lookback) & (df.index <= target)
    window = df.loc[mask]

    if window.empty:
        return {}

    prices = {}
    multi_ticker = len(symbols) > 1 and isinstance(df.columns, pd.MultiIndex)

    for ticker in symbols:
        try:
            if multi_ticker:
                close_col = ("Close", ticker)
                adj_col = ("Adj Close", ticker)
                if close_col not in df.columns or adj_col not in df.columns:
                    continue
                close_series = window[close_col].dropna()
                adj_series = window[adj_col].dropna()
            else:
                close_series = window["Close"].dropna()
                adj_series = window["Adj Close"].dropna()

            if close_series.empty or adj_series.empty:
                continue

            # Take the latest available date in the window
            close_val = float(close_series.iloc[-1])
            adj_val = float(adj_series.iloc[-1])

            if close_val > 0 and adj_val > 0:
                prices[ticker] = (close_val, adj_val)
        except Exception:
            continue

    return prices


def _fetch_splits(tickers: list[str], cache: HistoricalCache) -> None:
    """Fetch split history per ticker via yfinance (threaded)."""
    cached = cache.get_all_cached_split_tickers()
    missing = [t for t in tickers if t not in cached]

    if not missing:
        logger.info("All splits cached")
        return

    logger.info(f"Fetching splits for {len(missing)} tickers...")

    def _get_splits(ticker: str) -> tuple[str, dict]:
        try:
            t = yf.Ticker(ticker)
            splits = t.splits
            if splits is not None and not splits.empty:
                # Convert to {date_str: ratio}
                split_dict = {
                    idx.isoformat(): float(val)
                    for idx, val in splits.items()
                    if float(val) != 0
                }
                return ticker, split_dict
            return ticker, {}
        except Exception:
            return ticker, {}

    max_workers = min(16, len(missing))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_get_splits, t): t for t in missing}
        done = 0
        for future in as_completed(futures):
            ticker, splits = future.result()
            cache.set_splits(ticker, splits)
            done += 1
            if done % 100 == 0:
                logger.info(f"  Splits: {done}/{len(missing)} cached")

    logger.info(f"Cached splits for {len(missing)} tickers")
