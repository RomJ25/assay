"""Historical data cache — no TTL, immutable financial data."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from config import CACHE_DB_PATH

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS historical_financials (
    ticker TEXT PRIMARY KEY,
    data_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_prices (
    ticker TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    close_price REAL NOT NULL,
    adj_close_price REAL NOT NULL,
    PRIMARY KEY (ticker, as_of_date)
);

CREATE TABLE IF NOT EXISTS historical_splits (
    ticker TEXT PRIMARY KEY,
    splits_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_sp500 (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    sub_industry TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hist_prices_date
    ON historical_prices (as_of_date);
"""


class HistoricalCache:
    """SQLite cache for historical backtest data. No TTL — data is immutable."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or CACHE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        self._conn.close()

    # ── S&P 500 snapshot ────────────────────────────────────────────────

    def get_sp500(self) -> list[dict] | None:
        """Return cached S&P 500 list or None if empty."""
        rows = self._conn.execute(
            "SELECT ticker, company_name, sector, sub_industry FROM historical_sp500"
        ).fetchall()
        if not rows:
            return None
        return [
            {"ticker": r[0], "company_name": r[1], "sector": r[2], "sub_industry": r[3]}
            for r in rows
        ]

    def set_sp500(self, entries: list[dict]):
        """Cache S&P 500 list."""
        now = _utcnow()
        self._conn.execute("DELETE FROM historical_sp500")
        self._conn.executemany(
            "INSERT INTO historical_sp500 (ticker, company_name, sector, sub_industry, fetched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [(e["ticker"], e["company_name"], e["sector"], e["sub_industry"], now) for e in entries],
        )
        self._conn.commit()

    # ── Financials ──────────────────────────────────────────────────────

    def get_financials(self, ticker: str) -> dict | None:
        """Return raw financial statement data as dict, or None."""
        row = self._conn.execute(
            "SELECT data_json FROM historical_financials WHERE ticker = ?",
            (ticker,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set_financials(self, ticker: str, data: dict):
        """Cache raw financial statements as JSON."""
        self._conn.execute(
            "INSERT OR REPLACE INTO historical_financials (ticker, data_json, fetched_at) "
            "VALUES (?, ?, ?)",
            (ticker, json.dumps(data, default=str), _utcnow()),
        )
        self._conn.commit()

    def get_all_cached_financial_tickers(self) -> set[str]:
        """Return set of tickers that have cached financials."""
        rows = self._conn.execute("SELECT ticker FROM historical_financials").fetchall()
        return {r[0] for r in rows}

    # ── Prices ──────────────────────────────────────────────────────────

    def get_price(self, ticker: str, as_of_date: str) -> tuple[float, float] | None:
        """Return (close, adj_close) for a ticker on a date, or None."""
        row = self._conn.execute(
            "SELECT close_price, adj_close_price FROM historical_prices "
            "WHERE ticker = ? AND as_of_date = ?",
            (ticker, as_of_date),
        ).fetchone()
        if row is None:
            return None
        return (row[0], row[1])

    def set_prices(self, rows: list[tuple[str, str, float, float]]):
        """Bulk insert prices: [(ticker, as_of_date, close, adj_close), ...]."""
        self._conn.executemany(
            "INSERT OR REPLACE INTO historical_prices "
            "(ticker, as_of_date, close_price, adj_close_price) VALUES (?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()

    def get_prices_for_ticker(self, ticker: str) -> dict[str, tuple[float, float]]:
        """Return {date_str: (close, adj_close)} for all cached dates."""
        rows = self._conn.execute(
            "SELECT as_of_date, close_price, adj_close_price FROM historical_prices "
            "WHERE ticker = ?",
            (ticker,),
        ).fetchall()
        return {r[0]: (r[1], r[2]) for r in rows}

    def has_prices_for_date(self, as_of_date: str) -> bool:
        """Check if any prices exist for a given date."""
        row = self._conn.execute(
            "SELECT 1 FROM historical_prices WHERE as_of_date = ? LIMIT 1",
            (as_of_date,),
        ).fetchone()
        return row is not None

    # ── Splits ──────────────────────────────────────────────────────────

    def get_splits(self, ticker: str) -> dict | None:
        """Return splits as {date_str: ratio} or None."""
        row = self._conn.execute(
            "SELECT splits_json FROM historical_splits WHERE ticker = ?",
            (ticker,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def set_splits(self, ticker: str, splits: dict):
        """Cache split history."""
        self._conn.execute(
            "INSERT OR REPLACE INTO historical_splits (ticker, splits_json, fetched_at) "
            "VALUES (?, ?, ?)",
            (ticker, json.dumps(splits, default=str), _utcnow()),
        )
        self._conn.commit()

    def get_all_cached_split_tickers(self) -> set[str]:
        """Return set of tickers that have cached splits."""
        rows = self._conn.execute("SELECT ticker FROM historical_splits").fetchall()
        return {r[0] for r in rows}
