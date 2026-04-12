"""SQLite cache with TTL for financial data and S&P 500 list."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from config import (
    CACHE_DB_PATH,
    FUNDAMENTALS_CACHE_TTL_HOURS,
    PRICE_CACHE_TTL_HOURS,
    SP500_CACHE_TTL_HOURS,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """UTC now, returns naive datetime for SQLite string comparison compatibility."""
    return datetime.now(UTC).replace(tzinfo=None)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS ticker_cache (
    ticker TEXT NOT NULL,
    data_type TEXT NOT NULL,
    data_json TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'yahooquery',
    fetched_at TEXT NOT NULL,
    ttl_hours INTEGER NOT NULL DEFAULT 168,
    PRIMARY KEY (ticker, data_type)
);

CREATE TABLE IF NOT EXISTS price_cache (
    ticker TEXT PRIMARY KEY,
    price REAL NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sp500_cache (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    sub_industry TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS momentum_cache (
    ticker TEXT PRIMARY KEY,
    momentum REAL NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ticker_cache_lookup
    ON ticker_cache (ticker, data_type, fetched_at);
CREATE INDEX IF NOT EXISTS idx_price_cache_fetched
    ON price_cache (fetched_at);
CREATE INDEX IF NOT EXISTS idx_sp500_cache_fetched
    ON sp500_cache (fetched_at);
CREATE INDEX IF NOT EXISTS idx_momentum_cache_fetched
    ON momentum_cache (fetched_at);
"""


class Cache:
    """SQLite-backed cache with TTL expiry."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or CACHE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA cache_size=-64000")  # 64MB page cache
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.executescript(_SCHEMA)
        self._evict_stale()

    def close(self):
        self._conn.close()

    def _evict_stale(self):
        """Remove entries older than 2x TTL to prevent unbounded growth."""
        for table, ttl_h in [
            ("ticker_cache", FUNDAMENTALS_CACHE_TTL_HOURS * 2),
            ("price_cache", PRICE_CACHE_TTL_HOURS * 2),
            ("momentum_cache", PRICE_CACHE_TTL_HOURS * 2),
        ]:
            cutoff = (_utcnow() - timedelta(hours=ttl_h)).isoformat()
            self._conn.execute(f"DELETE FROM {table} WHERE fetched_at < ?", (cutoff,))
        self._conn.commit()

    # ── S&P 500 list ──────────────────────────────────────────────────

    def get_sp500(self) -> pd.DataFrame | None:
        """Return cached S&P 500 list if fresh, else None."""
        cutoff = (_utcnow() - timedelta(hours=SP500_CACHE_TTL_HOURS)).isoformat()
        rows = self._conn.execute(
            "SELECT ticker, company_name, sector, sub_industry FROM sp500_cache "
            "WHERE fetched_at > ?",
            (cutoff,),
        ).fetchall()
        if not rows:
            return None
        return pd.DataFrame(rows, columns=["ticker", "company_name", "sector", "sub_industry"])

    def set_sp500(self, df: pd.DataFrame):
        """Cache S&P 500 list."""
        now = _utcnow().isoformat()
        self._conn.execute("DELETE FROM sp500_cache")
        self._conn.executemany(
            "INSERT INTO sp500_cache (ticker, company_name, sector, sub_industry, fetched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [(r["ticker"], r["company_name"], r["sector"], r["sub_industry"], now) for _, r in df.iterrows()],
        )
        self._conn.commit()

    # ── Fundamental data ──────────────────────────────────────────────

    def get_fundamentals(self, ticker: str, data_type: str) -> str | None:
        """Return cached fundamental data JSON string if fresh, else None."""
        cutoff = (_utcnow() - timedelta(hours=FUNDAMENTALS_CACHE_TTL_HOURS)).isoformat()
        row = self._conn.execute(
            "SELECT data_json FROM ticker_cache "
            "WHERE ticker = ? AND data_type = ? AND fetched_at > ?",
            (ticker, data_type, cutoff),
        ).fetchone()
        if row is None:
            return None
        return row[0]

    def set_fundamentals(self, ticker: str, data_type: str, data_json: str, provider: str = "yahooquery"):
        """Cache fundamental data as JSON string."""
        now = _utcnow().isoformat()
        self._conn.execute(
            "INSERT OR REPLACE INTO ticker_cache "
            "(ticker, data_type, data_json, provider, fetched_at, ttl_hours) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ticker, data_type, data_json, provider, now, FUNDAMENTALS_CACHE_TTL_HOURS),
        )
        self._conn.commit()

    def set_fundamentals_batch(self, items: list[tuple[str, str, str]], provider: str = "yahooquery"):
        """Cache multiple fundamental data entries in one transaction.

        Args:
            items: List of (ticker, data_type, data_json) tuples.
        """
        now = _utcnow().isoformat()
        self._conn.executemany(
            "INSERT OR REPLACE INTO ticker_cache "
            "(ticker, data_type, data_json, provider, fetched_at, ttl_hours) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(t, dt, dj, provider, now, FUNDAMENTALS_CACHE_TTL_HOURS) for t, dt, dj in items],
        )
        self._conn.commit()

    # ── Prices ────────────────────────────────────────────────────────

    def get_prices(self) -> dict[str, float]:
        """Return all cached prices that are still fresh."""
        cutoff = (_utcnow() - timedelta(hours=PRICE_CACHE_TTL_HOURS)).isoformat()
        rows = self._conn.execute(
            "SELECT ticker, price FROM price_cache WHERE fetched_at > ?",
            (cutoff,),
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def set_prices(self, prices: dict[str, float]):
        """Cache prices."""
        now = _utcnow().isoformat()
        self._conn.executemany(
            "INSERT OR REPLACE INTO price_cache (ticker, price, fetched_at) VALUES (?, ?, ?)",
            [(t, p, now) for t, p in prices.items()],
        )
        self._conn.commit()

    # ── Momentum ──────────────────────────────────────────────────────

    def get_momentum(self) -> dict[str, float]:
        """Return all cached momentum values that are still fresh."""
        cutoff = (_utcnow() - timedelta(hours=PRICE_CACHE_TTL_HOURS)).isoformat()
        rows = self._conn.execute(
            "SELECT ticker, momentum FROM momentum_cache WHERE fetched_at > ?",
            (cutoff,),
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def set_momentum(self, momentum: dict[str, float]):
        """Cache momentum values."""
        now = _utcnow().isoformat()
        self._conn.executemany(
            "INSERT OR REPLACE INTO momentum_cache (ticker, momentum, fetched_at) VALUES (?, ?, ?)",
            [(t, m, now) for t, m in momentum.items()],
        )
        self._conn.commit()

    # ── Stale check ───────────────────────────────────────────────────

    def get_stale_tickers(self, tickers: list[str], data_type: str = "income_statement") -> list[str]:
        """Return tickers whose cached data is stale or missing."""
        cutoff = (_utcnow() - timedelta(hours=FUNDAMENTALS_CACHE_TTL_HOURS)).isoformat()
        cached = self._conn.execute(
            "SELECT ticker FROM ticker_cache "
            "WHERE data_type = ? AND fetched_at > ?",
            (data_type, cutoff),
        ).fetchall()
        cached_set = {r[0] for r in cached}
        return [t for t in tickers if t not in cached_set]
