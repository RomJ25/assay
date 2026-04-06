"""Unit tests for the SQLite cache layer."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from data.cache import Cache


def _make_cache(tmp_path: Path) -> Cache:
    """Create a Cache backed by a temp file."""
    return Cache(db_path=tmp_path / "test_cache.db")


class TestFundamentalsCache:
    def test_round_trip(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.set_fundamentals("AAPL", "income_statement", '{"revenue": 100}')
        result = cache.get_fundamentals("AAPL", "income_statement")
        assert result == '{"revenue": 100}'
        cache.close()

    def test_ttl_expiry_returns_none(self, tmp_path):
        cache = _make_cache(tmp_path)
        # Insert with a very old fetched_at
        old_time = (datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=500)).isoformat()
        cache._conn.execute(
            "INSERT OR REPLACE INTO ticker_cache "
            "(ticker, data_type, data_json, provider, fetched_at, ttl_hours) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("AAPL", "income_statement", '{"revenue": 100}', "test", old_time, 168),
        )
        cache._conn.commit()
        result = cache.get_fundamentals("AAPL", "income_statement")
        assert result is None
        cache.close()

    def test_different_data_types_independent(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.set_fundamentals("AAPL", "income_statement", '{"revenue": 100}')
        cache.set_fundamentals("AAPL", "balance_sheet", '{"assets": 200}')
        assert cache.get_fundamentals("AAPL", "income_statement") == '{"revenue": 100}'
        assert cache.get_fundamentals("AAPL", "balance_sheet") == '{"assets": 200}'
        cache.close()


class TestPriceCache:
    def test_round_trip(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.set_prices({"AAPL": 150.0, "MSFT": 300.0})
        prices = cache.get_prices()
        assert prices["AAPL"] == 150.0
        assert prices["MSFT"] == 300.0
        cache.close()


class TestStaleTickers:
    def test_all_stale_when_empty(self, tmp_path):
        cache = _make_cache(tmp_path)
        stale = cache.get_stale_tickers(["AAPL", "MSFT"])
        assert stale == ["AAPL", "MSFT"]
        cache.close()

    def test_fresh_not_stale(self, tmp_path):
        cache = _make_cache(tmp_path)
        cache.set_fundamentals("AAPL", "income_statement", '{"data": 1}')
        stale = cache.get_stale_tickers(["AAPL", "MSFT"])
        assert stale == ["MSFT"]
        cache.close()


class TestEviction:
    def test_old_entries_evicted(self, tmp_path):
        cache = _make_cache(tmp_path)
        # Insert very old data (older than 2x TTL)
        old_time = (datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=500)).isoformat()
        cache._conn.execute(
            "INSERT INTO ticker_cache "
            "(ticker, data_type, data_json, provider, fetched_at, ttl_hours) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("OLD", "income_statement", '{}', "test", old_time, 168),
        )
        cache._conn.commit()

        # Re-init triggers eviction
        cache2 = Cache(db_path=tmp_path / "test_cache.db")
        row = cache2._conn.execute(
            "SELECT * FROM ticker_cache WHERE ticker = 'OLD'"
        ).fetchone()
        assert row is None
        cache.close()
        cache2.close()
