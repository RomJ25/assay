"""Data fetch orchestrator — batching, caching, throttling, fallback."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict

from data.cache import Cache
from data.providers.base import FinancialData
from data.providers.yahooquery_provider import YahooQueryProvider
from data.providers.yfinance_provider import YFinanceProvider
from data.sp500 import fetch_sp500_list, sp500_info_dict
from config import BATCH_DELAY_SECONDS, BATCH_SIZE

logger = logging.getLogger(__name__)


def _serialize_fd(fd: FinancialData) -> str:
    """Serialize FinancialData to JSON for caching."""
    return json.dumps(asdict(fd), default=str)


def _deserialize_fd(data_json: str) -> FinancialData:
    """Deserialize FinancialData from cached JSON."""
    d = json.loads(data_json)
    return FinancialData(**d)


class DataFetcher:
    """Orchestrates data fetching with caching, batching, and fallback."""

    def __init__(self, force_refresh: bool = False):
        self.cache = Cache()
        self.primary = YahooQueryProvider()
        self.fallback = YFinanceProvider()
        self.force_refresh = force_refresh

    def get_sp500(self) -> tuple[list[str], dict[str, dict]]:
        """Get S&P 500 ticker list and info dict (cached)."""
        df = None if self.force_refresh else self.cache.get_sp500()
        if df is None:
            df = fetch_sp500_list()
            self.cache.set_sp500(df)

        tickers = df["ticker"].tolist()
        info = sp500_info_dict(df)
        return tickers, info

    def fetch_all(self, tickers: list[str], sp500_info: dict[str, dict]) -> dict[str, FinancialData]:
        """Fetch financial data for all tickers with caching and batching.

        Steps:
        1. Fetch prices (batch, fast)
        2. Load cached tickers, find stale ones
        3. Fetch stale tickers in batches via yahooquery
        4. Fall back to yfinance for failures
        5. Cache new data, merge prices, return all
        """
        # Step 1: Prices
        prices = self._fetch_prices(tickers)

        # Step 2: Load from cache + find stale
        all_data: dict[str, FinancialData] = {}

        if self.force_refresh:
            stale = list(tickers)
            logger.info("Force refresh: bypassing cache for all tickers")
        else:
            stale = []
            for ticker in tickers:
                cached = self.cache.get_fundamentals(ticker, "financial_data")
                if cached is not None:
                    try:
                        fd = _deserialize_fd(cached)
                        all_data[ticker] = fd
                    except Exception:
                        stale.append(ticker)
                else:
                    stale.append(ticker)

        logger.info(f"Cache status: {len(all_data)} cached, {len(stale)} need refresh")

        # Step 3: Fetch stale in batches
        failed_tickers: list[str] = []

        if stale:
            batches = [stale[i:i + BATCH_SIZE] for i in range(0, len(stale), BATCH_SIZE)]
            for i, batch in enumerate(batches, 1):
                logger.info(f"Batch {i}/{len(batches)}: fetching {len(batch)} tickers...")
                batch_data = self.primary.fetch_financial_data(batch, sp500_info)

                # If entire batch failed (0 results), retry once after delay.
                # Yahoo's "Invalid Crumb" error affects the first batch in a session.
                if len(batch_data) == 0 and len(batch) > 1:
                    logger.warning(f"Batch {i} failed completely — retrying after {BATCH_DELAY_SECONDS}s...")
                    time.sleep(BATCH_DELAY_SECONDS)
                    batch_data = self.primary.fetch_financial_data(batch, sp500_info)

                # Cache successful results (batch commit for performance)
                cache_items = []
                for ticker, fd in batch_data.items():
                    cache_items.append((ticker, "financial_data", _serialize_fd(fd)))
                    all_data[ticker] = fd
                if cache_items:
                    self.cache.set_fundamentals_batch(cache_items)

                batch_failed = [t for t in batch if t not in batch_data]
                failed_tickers.extend(batch_failed)

                if i < len(batches):
                    logger.debug(f"Waiting {BATCH_DELAY_SECONDS}s before next batch...")
                    time.sleep(BATCH_DELAY_SECONDS)

        # Step 4: yfinance fallback for failures
        if failed_tickers:
            logger.info(f"Trying yfinance fallback for {len(failed_tickers)} failed tickers...")
            fallback_data = self.fallback.fetch_financial_data(failed_tickers, sp500_info)

            for ticker, fd in fallback_data.items():
                self.cache.set_fundamentals(ticker, "financial_data", _serialize_fd(fd))
                all_data[ticker] = fd

            still_failed = [t for t in failed_tickers if t not in fallback_data]
            if still_failed:
                logger.warning(f"Could not fetch data for {len(still_failed)} tickers: {still_failed[:10]}...")

        # Step 5: Merge fresh prices and update market_cap
        # Trust shares_outstanding (from Yahoo's reported value) and recompute
        # market_cap = shares × new_price. This correctly handles normal price
        # moves. For stock splits, shares may be temporarily stale until the
        # next cache refresh, but the error is bounded.
        for ticker, fd in all_data.items():
            if ticker in prices:
                fd.current_price = prices[ticker]
                if fd.shares_outstanding > 0 and fd.current_price > 0:
                    fd.market_cap = fd.shares_outstanding * fd.current_price
                elif fd.market_cap > 0 and fd.current_price > 0:
                    # Fallback: derive shares from cached market_cap
                    fd.shares_outstanding = fd.market_cap / fd.current_price

        # Step 6: Compute 12-1 month momentum (cached, 24h TTL)
        all_tickers = list(all_data.keys())
        if self.force_refresh:
            cached_momentum = {}
        else:
            cached_momentum = self.cache.get_momentum()
        missing_momentum = [t for t in all_tickers if t not in cached_momentum]

        if missing_momentum:
            logger.info(f"Computing momentum for {len(missing_momentum)} tickers ({len(cached_momentum)} cached)...")
            fresh_momentum = self._compute_momentum(missing_momentum)
            if fresh_momentum:
                self.cache.set_momentum(fresh_momentum)
                cached_momentum.update(fresh_momentum)
        else:
            logger.info(f"Momentum: all {len(cached_momentum)} tickers cached")

        for ticker, fd in all_data.items():
            fd.momentum_12m = cached_momentum.get(ticker)

        total = len(all_data)
        skipped = len(tickers) - total
        logger.info(f"Data fetch complete: {total}/{len(tickers)} tickers ({skipped} skipped)")

        return all_data

    def _fetch_prices(self, tickers: list[str]) -> dict[str, float]:
        """Fetch prices with cache."""
        if self.force_refresh:
            cached_prices = {}
            missing = list(tickers)
        else:
            cached_prices = self.cache.get_prices()
            missing = [t for t in tickers if t not in cached_prices]

        if missing:
            logger.info(f"Fetching prices for {len(missing)} tickers...")
            fresh_prices = self.fallback.fetch_prices(missing)
            if fresh_prices:
                self.cache.set_prices(fresh_prices)
                cached_prices.update(fresh_prices)

        return cached_prices

    def _compute_momentum(self, tickers: list[str]) -> dict[str, float]:
        """Compute 12-1 month momentum from yfinance historical prices.

        Downloads in batches of 500 to avoid silent drops in yfinance
        when downloading thousands of tickers at once.
        """
        import yfinance as yf
        from datetime import datetime, timedelta
        from scoring.momentum_scorer import compute_momentum

        MOMENTUM_BATCH = 500
        end = datetime.now()
        start = end - timedelta(days=400)  # ~13 months of data
        start_str = start.strftime("%Y-%m-%d")

        price_histories = {}
        batches = [tickers[i:i + MOMENTUM_BATCH] for i in range(0, len(tickers), MOMENTUM_BATCH)]

        for i, batch in enumerate(batches, 1):
            try:
                df = yf.download(batch, start=start_str,
                                 auto_adjust=True, threads=True, progress=False)
                if df.empty:
                    continue

                close = df["Close"] if "Close" in df.columns else df
                monthly = close.resample("ME").last()

                for t in batch:
                    try:
                        if hasattr(monthly, "columns") and t in monthly.columns:
                            col = monthly[t]
                        elif len(batch) == 1:
                            col = monthly.squeeze() if hasattr(monthly, "squeeze") else monthly
                        else:
                            continue
                        vals = col.dropna().values.tolist()
                        if len(vals) >= 2:
                            price_histories[t] = [float(v) for v in vals[-13:]]
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Momentum batch {i}/{len(batches)} failed: {e}")

        return compute_momentum(price_histories)

    def close(self):
        self.cache.close()
