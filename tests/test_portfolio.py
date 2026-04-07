"""Unit tests for backtest portfolio simulation."""

import math
from datetime import date

from backtest.portfolio import (
    _cagr,
    _max_drawdown,
    _sharpe,
    BacktestMetrics,
    simulate_portfolio,
)
from backtest.cache import HistoricalCache


# ── Pure math tests ──────────────────────────────────────────────────────

class TestCAGR:
    def test_known_value(self):
        # $1 → $2 in 3 years = 26% CAGR
        result = _cagr(2.0, 3.0)
        assert abs(result - 0.2599) < 0.001

    def test_no_growth(self):
        assert _cagr(1.0, 5.0) == 0.0

    def test_loss(self):
        # $1 → $0.5 in 2 years = -29.3% CAGR
        result = _cagr(0.5, 2.0)
        assert result < 0

    def test_zero_years(self):
        assert _cagr(2.0, 0.0) == 0.0


class TestMaxDrawdown:
    def test_no_drawdown(self):
        values = [1.0, 1.1, 1.2, 1.3]
        assert _max_drawdown(values) == 0.0

    def test_known_drawdown(self):
        # Peak at 1.5, trough at 1.0 → 33.3% drawdown
        values = [1.0, 1.5, 1.0, 1.2]
        dd = _max_drawdown(values)
        assert abs(dd - (-1/3)) < 0.001

    def test_single_point(self):
        assert _max_drawdown([1.0]) == 0.0

    def test_recovery_doesnt_erase_drawdown(self):
        values = [1.0, 2.0, 1.0, 3.0]
        dd = _max_drawdown(values)
        assert abs(dd - (-0.5)) < 0.001  # 2.0 → 1.0 = 50%


class TestSharpe:
    def test_zero_volatility(self):
        # All same returns → std=0 → sharpe=0
        assert _sharpe([0.05, 0.05, 0.05, 0.05]) == 0.0

    def test_positive_sharpe(self):
        # High consistent returns should give positive Sharpe
        returns = [0.10, 0.08, 0.12, 0.09, 0.11, 0.10, 0.08, 0.12]
        result = _sharpe(returns)
        assert result > 0

    def test_empty_returns(self):
        assert _sharpe([]) == 0.0

    def test_single_return(self):
        assert _sharpe([0.05]) == 0.0


# ── Portfolio simulation with mock cache ─────────────────────────────────

class TestSimulatePortfolio:
    def test_basic_simulation(self, tmp_path):
        """Test end-to-end portfolio simulation with synthetic data."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")

        # Set up prices for 3 rebalance dates
        # All tickers: 10% return per quarter
        dates = [date(2024, 3, 31), date(2024, 6, 30), date(2024, 9, 30)]
        prices = []
        for ticker in ["A", "B", "C", "SPY"]:
            for i, d in enumerate(dates):
                close = 100.0 * (1.1 ** i)
                adj = close  # no dividends in test
                prices.append((ticker, d.isoformat(), close, adj))
        cache.set_prices(prices)

        picks = [
            (dates[0], ["A", "B"]),
            (dates[1], ["B", "C"]),
        ]
        universe = [
            (dates[0], ["A", "B", "C"]),
            (dates[1], ["A", "B", "C"]),
        ]

        records, metrics = simulate_portfolio(picks, universe, cache, dates)
        cache.close()

        # With uniform 10% returns, portfolio == universe == SPY
        assert len(records) == 2
        assert metrics.total_quarters == 2
        assert metrics.avg_picks_per_quarter == 2.0

    def test_selection_alpha_is_difference(self, tmp_path):
        """Selection alpha = portfolio CAGR - universe CAGR."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")

        dates = [date(2024, 3, 31), date(2024, 6, 30), date(2024, 9, 30)]
        # Pick A outperforms: 20% return. B and C: 5% return. SPY: 10%.
        prices = []
        for i, d in enumerate(dates):
            prices.append(("A", d.isoformat(), 100 * (1.2 ** i), 100 * (1.2 ** i)))
            prices.append(("B", d.isoformat(), 100 * (1.05 ** i), 100 * (1.05 ** i)))
            prices.append(("C", d.isoformat(), 100 * (1.05 ** i), 100 * (1.05 ** i)))
            prices.append(("SPY", d.isoformat(), 100 * (1.10 ** i), 100 * (1.10 ** i)))
        cache.set_prices(prices)

        picks = [(dates[0], ["A"]), (dates[1], ["A"])]
        universe = [(dates[0], ["A", "B", "C"]), (dates[1], ["A", "B", "C"])]

        records, metrics = simulate_portfolio(picks, universe, cache, dates)
        cache.close()

        # Portfolio (A only) should outperform universe (A+B+C)
        assert metrics.selection_alpha > 0
        assert abs(metrics.selection_alpha - (metrics.cagr - metrics.universe_cagr)) < 0.001

    def test_missing_prices_handled(self, tmp_path):
        """Stocks without prices should be excluded, not crash."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")

        dates = [date(2024, 3, 31), date(2024, 6, 30)]
        # Only A and SPY have prices; B does not
        prices = [
            ("A", dates[0].isoformat(), 100.0, 100.0),
            ("A", dates[1].isoformat(), 110.0, 110.0),
            ("SPY", dates[0].isoformat(), 100.0, 100.0),
            ("SPY", dates[1].isoformat(), 105.0, 105.0),
        ]
        cache.set_prices(prices)

        picks = [(dates[0], ["A", "B"])]
        universe = [(dates[0], ["A", "B"])]

        records, metrics = simulate_portfolio(picks, universe, cache, dates)
        cache.close()

        # Should compute returns using only A
        assert len(records) == 1
        assert records[0]["portfolio_return"] == 10.0  # A: 100 → 110

    def test_turnover_calculation(self, tmp_path):
        """Turnover = symmetric difference / union."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")

        dates = [date(2024, 3, 31), date(2024, 6, 30), date(2024, 9, 30), date(2024, 12, 31)]
        prices = []
        for ticker in ["A", "B", "C", "D", "SPY"]:
            for i, d in enumerate(dates):
                prices.append((ticker, d.isoformat(), 100 * (1.05 ** i), 100 * (1.05 ** i)))
        cache.set_prices(prices)

        # Q1: [A, B], Q2: [B, C], Q3: [C, D]
        picks = [
            (dates[0], ["A", "B"]),
            (dates[1], ["B", "C"]),
            (dates[2], ["C", "D"]),
        ]
        universe = [
            (dates[0], ["A", "B", "C", "D"]),
            (dates[1], ["A", "B", "C", "D"]),
            (dates[2], ["A", "B", "C", "D"]),
        ]

        records, metrics = simulate_portfolio(picks, universe, cache, dates)
        cache.close()

        # Q1→Q2: sym_diff={A,C}, union={A,B,C} → 2/3 = 66.7%
        # Q2→Q3: sym_diff={B,D}, union={B,C,D} → 2/3 = 66.7%
        assert metrics.avg_turnover > 60

        # Verify per-record turnover: Q1=None, Q2=66.7%, Q3=66.7%
        assert records[0]["turnover"] is None
        assert records[1]["turnover"] is not None
        assert abs(records[1]["turnover"] - 66.7) < 0.1
        assert records[2]["turnover"] is not None
        assert abs(records[2]["turnover"] - 66.7) < 0.1
