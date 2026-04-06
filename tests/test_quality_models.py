"""Unit tests for quality scoring — Piotroski + Profitability."""

from data.providers.base import FinancialData
from quality.growth import GrowthModel
from quality.piotroski import PiotroskiModel
from scoring.quality_scorer import compute_quality_scores
from scoring.conviction import conviction_score, classify


def _make_fd(**overrides) -> FinancialData:
    defaults = dict(
        ticker="TEST", company_name="Test Corp", sector="Information Technology",
        sub_industry="Application Software",
        current_price=100.0, market_cap=50e9, beta=1.0,
        trailing_pe=20.0, forward_pe=18.0, price_to_book=3.0,
        enterprise_value=55e9, enterprise_to_ebitda=15.0, price_to_sales=5.0,
        dividend_yield=0.02, shares_outstanding=500e6,
        revenue=[10e9, 9e9, 8e9, 7e9],
        gross_profit=[6e9, 5.3e9, 4.6e9, 4e9],
        operating_income=[3e9, 2.7e9, 2.3e9, 2e9],
        net_income=[2.5e9, 2.2e9, 1.9e9, 1.6e9],
        diluted_eps=[5.0, 4.4, 3.8, 3.2],
        ebitda=[3.5e9, 3.1e9, 2.7e9, 2.3e9],
        interest_expense=[200e6, 200e6, 200e6, 200e6],
        tax_provision=[600e6, 530e6, 460e6, 390e6],
        pretax_income=[3.1e9, 2.73e9, 2.36e9, 1.99e9],
        total_assets=[20e9, 18e9],
        current_assets=[8e9, 7e9],
        current_liabilities=[4e9, 3.5e9],
        total_debt=[5e9, 5e9],
        cash_and_equivalents=[3e9, 2.5e9],
        stockholders_equity=[12e9, 10e9],
        retained_earnings=[8e9, 6.5e9],
        ordinary_shares_number=[500e6, 510e6],  # slight buyback
        free_cash_flow=[2e9, 1.8e9, 1.5e9, 1.2e9],
        operating_cash_flow=[3e9, 2.7e9, 2.3e9, 2e9],
        capital_expenditure=[-1e9, -0.9e9, -0.8e9, -0.8e9],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


class TestPiotroskiModel:
    def test_healthy_company_scores_high(self):
        fd = _make_fd()
        pio = PiotroskiModel()
        score = pio.calculate(fd)
        assert score is not None and score >= 50

    def test_raw_score_0_to_9(self):
        fd = _make_fd()
        pio = PiotroskiModel()
        raw = pio.raw_score(fd)
        assert 0 <= raw <= 9

    def test_dilution_detected(self):
        """Shares increased -> criterion 7 should fail, lowering score."""
        pio = PiotroskiModel()
        no_dilution = _make_fd(ordinary_shares_number=[500e6, 510e6])
        diluted = _make_fd(ordinary_shares_number=[600e6, 500e6])
        assert pio.raw_score(no_dilution) > pio.raw_score(diluted)

    def test_buyback_rewarded(self):
        """Shares decreased -> criterion 7 should pass, giving higher score than missing data."""
        pio = PiotroskiModel()
        buyback = _make_fd(ordinary_shares_number=[480e6, 500e6])
        no_data = _make_fd(ordinary_shares_number=[None, None])
        assert pio.raw_score(buyback) > pio.raw_score(no_data)


class TestQualityScorer:
    def test_higher_profitability_ranks_higher(self):
        stocks = {
            "HIGH_GP": _make_fd(ticker="HIGH_GP", gross_profit=[8e9], total_assets=[10e9, 9e9]),
            "LOW_GP": _make_fd(ticker="LOW_GP", gross_profit=[1e9], total_assets=[10e9, 9e9]),
        }
        qs, _, _ = compute_quality_scores(stocks)
        assert qs["HIGH_GP"] > qs["LOW_GP"]

    def test_roa_fallback_for_banks(self):
        stocks = {
            "BANK": _make_fd(ticker="BANK", gross_profit=[None]*4, net_income=[2e9, 1.8e9, 1.5e9, 1.2e9],
                             total_assets=[100e9, 90e9]),
        }
        qs, _, prof = compute_quality_scores(stocks)
        assert "BANK" in qs  # should get quality score via ROA fallback
        assert "BANK" in prof  # should have profitability ratio

    def test_both_missing_no_crash(self):
        stocks = {
            "EMPTY": _make_fd(ticker="EMPTY", gross_profit=[None]*4, net_income=[None]*4),
        }
        qs, _, _ = compute_quality_scores(stocks)
        # Should still get a Piotroski-only score or None, but not crash

    def test_single_source_penalized(self):
        """Single-source quality score should be lower than dual-source with similar inputs."""
        # DUAL has both Piotroski data and gross profit -> gets composite
        # SINGLE has no gross profit data -> gets penalized Piotroski-only
        stocks = {
            "DUAL": _make_fd(ticker="DUAL"),
            "SINGLE": _make_fd(ticker="SINGLE", gross_profit=[None]*4, net_income=[None]*4,
                               total_assets=[None]*2),
        }
        qs, _, _ = compute_quality_scores(stocks)
        # SINGLE gets only Piotroski, penalized by 0.8x
        if "SINGLE" in qs and "DUAL" in qs:
            assert qs["DUAL"] > qs["SINGLE"]


class TestConviction:
    def test_conviction_buy(self):
        assert classify(75, 75) == "CONVICTION BUY"

    def test_value_trap(self):
        assert classify(75, 30) == "VALUE TRAP"

    def test_overvalued_quality(self):
        assert classify(20, 80) == "OVERVALUED QUALITY"

    def test_hold(self):
        assert classify(50, 50) == "HOLD"

    def test_avoid(self):
        assert classify(30, 30) == "AVOID"

    def test_geometric_mean(self):
        assert conviction_score(80, 80) == 80.0
        assert conviction_score(100, 0) == 0.0
        assert conviction_score(None, 80) is None


class TestGrowthModel:
    def test_healthy_company(self):
        """Default fixture has growing revenue, EPS, margins -> score ~82."""
        gm = GrowthModel()
        fd = _make_fd()
        score = gm.calculate(fd)
        assert score is not None
        assert 70 <= score <= 95

    def test_declining_lower_than_growing(self):
        """Declining company should score lower."""
        gm = GrowthModel()
        growing = _make_fd()
        declining = _make_fd(
            revenue=[7e9, 8e9, 9e9, 10e9],
            diluted_eps=[3.2, 3.8, 4.4, 5.0],
            free_cash_flow=[1.2e9, 1.5e9, 1.8e9, 2e9],
        )
        assert gm.calculate(growing) > gm.calculate(declining)

    def test_minimal_data_still_computes(self):
        """Even with sparse data, profitability sub-score keeps it from None."""
        gm = GrowthModel()
        fd = _make_fd(
            revenue=[None]*4, diluted_eps=[None]*4,
            free_cash_flow=[None]*4, trailing_pe=None,
            gross_profit=[None]*4, operating_income=[None]*4,
            net_income=[None]*4,
        )
        score = gm.calculate(fd)
        # Profitability's neutral 25 survives even with no real data
        assert score is not None
        assert score < 50
