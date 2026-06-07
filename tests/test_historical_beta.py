"""Tests for backtest.historical_beta — locks methodology against accidental changes."""

from __future__ import annotations

import math
import sqlite3
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from backtest.cache import HistoricalCache
from backtest import historical_beta


@pytest.fixture
def cache():
    """Build a temp cache populated with synthetic quarter-end prices."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)

    # Patch CACHE_DB_PATH so HistoricalCache uses our temp file
    with patch("backtest.cache.CACHE_DB_PATH", db_path):
        c = HistoricalCache(db_path=db_path)
        yield c
        c.close()
    db_path.unlink(missing_ok=True)
    historical_beta.reset_benchmark_cache()


def _populate_quarter_ends(cache: HistoricalCache, ticker: str, prices: list[float], start_year: int = 2018):
    """Insert prices on consecutive quarter-end dates starting from start_year-Q1."""
    rows = []
    qtr_dates = [(3, 31), (6, 30), (9, 30), (12, 31)]
    year = start_year
    qi = 0
    for p in prices:
        m, d = qtr_dates[qi % 4]
        date_str = f"{year}-{m:02d}-{d:02d}"
        rows.append((ticker, date_str, p, p))  # close = adj_close for tests
        qi += 1
        if qi % 4 == 0:
            year += 1
    cache.set_prices(rows)


def test_perfect_market_proxy_has_beta_one(cache):
    """A ticker that moves identically to SPY should have beta = 1.0."""
    spy_prices = [100.0 * (1.05 ** i) for i in range(25)]  # 5% per quarter
    _populate_quarter_ends(cache, "SPY", spy_prices)
    _populate_quarter_ends(cache, "TEST", spy_prices)  # identical
    historical_beta.reset_benchmark_cache()

    beta = historical_beta.compute_historical_beta("TEST", date(2024, 12, 31), cache)
    assert beta is not None
    assert abs(beta - 1.0) < 1e-6


def test_double_market_movement_has_beta_two(cache):
    """A ticker whose log-returns are 2x SPY's should have beta = 2.0."""
    spy_prices = [100.0]
    test_prices = [100.0]
    # Inject varied quarterly returns to create a real distribution
    qtr_returns = [0.05, -0.03, 0.08, -0.02, 0.04, -0.06, 0.10, -0.04, 0.03, -0.01,
                   0.07, -0.05, 0.06, -0.02, 0.08, -0.03, 0.05, -0.04, 0.09, -0.01,
                   0.04, -0.06, 0.07, -0.02]
    for r in qtr_returns:
        spy_prices.append(spy_prices[-1] * math.exp(r))
        test_prices.append(test_prices[-1] * math.exp(2 * r))
    _populate_quarter_ends(cache, "SPY", spy_prices)
    _populate_quarter_ends(cache, "TEST", test_prices)
    historical_beta.reset_benchmark_cache()

    beta = historical_beta.compute_historical_beta("TEST", date(2024, 12, 31), cache)
    assert beta is not None
    assert abs(beta - 2.0) < 1e-6


def test_returns_none_when_insufficient_history(cache):
    """Fewer than MIN_OBSERVATIONS quarters of overlapping data → None."""
    short_series = [100.0 * (1.05 ** i) for i in range(5)]  # only 4 returns
    _populate_quarter_ends(cache, "SPY", short_series)
    _populate_quarter_ends(cache, "TEST", short_series)
    historical_beta.reset_benchmark_cache()

    beta = historical_beta.compute_historical_beta("TEST", date(2018, 12, 31), cache)
    assert beta is None


def test_returns_none_when_ticker_absent(cache):
    spy_prices = [100.0 * (1.05 ** i) for i in range(25)]
    _populate_quarter_ends(cache, "SPY", spy_prices)
    historical_beta.reset_benchmark_cache()
    assert historical_beta.compute_historical_beta("MISSING", date(2024, 12, 31), cache) is None


def test_returns_none_when_benchmark_absent(cache):
    """No SPY in cache → can't compute beta."""
    test_prices = [100.0 * (1.05 ** i) for i in range(25)]
    _populate_quarter_ends(cache, "TEST", test_prices)
    historical_beta.reset_benchmark_cache()
    assert historical_beta.compute_historical_beta("TEST", date(2024, 12, 31), cache) is None
