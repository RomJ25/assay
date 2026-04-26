"""Unit tests for momentum scoring and gate."""

from scoring.momentum_scorer import (
    compute_momentum,
    compute_momentum_percentiles,
    apply_momentum_gate,
)


class TestComputeMomentum:
    def test_basic_12_1_return(self):
        """12-1 month return: uses first price to second-to-last price."""
        # 13 monthly prices: index 0 = 12m ago, index 12 = now
        prices = [100.0] * 11 + [120.0, 125.0]  # 120 is 1m ago, 125 is now
        result = compute_momentum({"AAPL": prices})
        # Should use price[0]=100 to price[-2]=120 → +20%
        assert abs(result["AAPL"] - 0.20) < 0.001

    def test_skip_most_recent_month(self):
        """The most recent month (index -1) should NOT affect momentum."""
        prices_a = [100.0] * 11 + [120.0, 200.0]  # now=200 (big jump)
        prices_b = [100.0] * 11 + [120.0, 50.0]   # now=50 (big crash)
        result_a = compute_momentum({"A": prices_a})
        result_b = compute_momentum({"B": prices_b})
        # Both should give same momentum (100 → 120 = +20%)
        assert abs(result_a["A"] - result_b["B"]) < 0.001

    def test_negative_momentum(self):
        prices = [100.0] * 11 + [80.0, 75.0]
        result = compute_momentum({"TEST": prices})
        assert result["TEST"] < 0  # -20%

    def test_insufficient_data(self):
        result = compute_momentum({"TEST": [100.0]})
        assert "TEST" not in result

    def test_zero_start_price(self):
        result = compute_momentum({"TEST": [0.0, 100.0, 110.0]})
        assert "TEST" not in result

    def test_fewer_than_13_months(self):
        """With fewer months, uses last price instead of skip-month."""
        prices = [100.0, 110.0, 120.0]  # only 3 months
        result = compute_momentum({"TEST": prices})
        # len < 13 → uses prices[-1] = 120, start = 100 → +20%
        assert abs(result["TEST"] - 0.20) < 0.001


class TestMomentumPercentiles:
    def test_ranking(self):
        momentum = {"A": -0.10, "B": 0.0, "C": 0.10, "D": 0.20}
        pcts = compute_momentum_percentiles(momentum)
        assert pcts["A"] < pcts["B"] < pcts["C"] < pcts["D"]
        assert pcts["A"] == 25.0   # bottom quartile
        assert pcts["D"] == 100.0  # top

    def test_empty(self):
        assert compute_momentum_percentiles({}) == {}


class TestMomentumGate:
    def test_gates_bottom_quartile(self):
        """Bottom 25% momentum should be downgraded."""
        assert apply_momentum_gate("RESEARCH CANDIDATE", 20.0) == "WATCH LIST"
        assert apply_momentum_gate("RESEARCH CANDIDATE", 25.0) == "WATCH LIST"

    def test_passes_above_threshold(self):
        assert apply_momentum_gate("RESEARCH CANDIDATE", 26.0) == "RESEARCH CANDIDATE"
        assert apply_momentum_gate("RESEARCH CANDIDATE", 50.0) == "RESEARCH CANDIDATE"
        assert apply_momentum_gate("RESEARCH CANDIDATE", 100.0) == "RESEARCH CANDIDATE"

    def test_only_affects_conviction_buy(self):
        assert apply_momentum_gate("VALUE TRAP", 10.0) == "VALUE TRAP"
        assert apply_momentum_gate("WATCH LIST", 5.0) == "WATCH LIST"
        assert apply_momentum_gate("HOLD", 15.0) == "HOLD"

    def test_none_momentum_passes(self):
        """Missing momentum data should not block."""
        assert apply_momentum_gate("RESEARCH CANDIDATE", None) == "RESEARCH CANDIDATE"
