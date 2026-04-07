"""Unit tests for quality scoring — Piotroski + Profitability."""

from data.providers.base import FinancialData
from quality.growth import GrowthModel
from quality.piotroski import PiotroskiModel
from scoring.quality_scorer import compute_quality_scores
from scoring.conviction import conviction_score, classify, confidence_level, apply_min_fscore


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


    def test_roa_improving_from_negative(self):
        """NI going from -500M to -200M is improving ROA — criterion 3 should pass."""
        pio = PiotroskiModel()
        fd = _make_fd(net_income=[-200e6, -500e6, -300e6, -100e6],
                      total_assets=[10e9, 10e9])
        _, breakdown = pio.calculate_detailed(fd)
        assert breakdown["criteria"]["roa_improving"]["pass"] is True

    def test_roa_worsening_from_negative(self):
        """NI going from -200M to -500M is worsening ROA — criterion 3 should fail."""
        pio = PiotroskiModel()
        fd = _make_fd(net_income=[-500e6, -200e6, -100e6, -50e6],
                      total_assets=[10e9, 10e9])
        _, breakdown = pio.calculate_detailed(fd)
        assert breakdown["criteria"]["roa_improving"]["pass"] is False

    def test_gross_margin_improving_from_negative(self):
        """GP going from -200M to +50M with stable revenue — criterion 8 should pass."""
        pio = PiotroskiModel()
        fd = _make_fd(gross_profit=[50e6, -200e6, -100e6, 0],
                      revenue=[2e9, 2e9, 2e9, 2e9])
        _, breakdown = pio.calculate_detailed(fd)
        assert breakdown["criteria"]["gross_margin_up"]["pass"] is True


class TestQualityScorer:
    def test_higher_profitability_ranks_higher(self):
        stocks = {
            "HIGH_GP": _make_fd(ticker="HIGH_GP", gross_profit=[8e9], total_assets=[10e9, 9e9]),
            "LOW_GP": _make_fd(ticker="LOW_GP", gross_profit=[1e9], total_assets=[10e9, 9e9]),
        }
        qs, _, _, _ = compute_quality_scores(stocks)
        assert qs["HIGH_GP"] > qs["LOW_GP"]

    def test_roa_fallback_for_banks(self):
        stocks = {
            "BANK": _make_fd(ticker="BANK", gross_profit=[None]*4, net_income=[2e9, 1.8e9, 1.5e9, 1.2e9],
                             total_assets=[100e9, 90e9]),
        }
        qs, _, prof, _ = compute_quality_scores(stocks)
        assert "BANK" in qs  # should get quality score via ROA fallback
        assert "BANK" in prof  # should have profitability ratio

    def test_both_missing_no_crash(self):
        stocks = {
            "EMPTY": _make_fd(ticker="EMPTY", gross_profit=[None]*4, net_income=[None]*4),
        }
        qs, _, _, _ = compute_quality_scores(stocks)
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
        qs, _, _, _ = compute_quality_scores(stocks)
        # SINGLE gets only Piotroski, penalized by 0.8x
        if "SINGLE" in qs and "DUAL" in qs:
            assert qs["DUAL"] > qs["SINGLE"]


    def test_negative_gp_ranks_low(self):
        """Negative GP is a real signal (bad), not missing — it ranks at the bottom."""
        stocks = {
            "GOOD": _make_fd(ticker="GOOD", gross_profit=[6e9], total_assets=[20e9, 18e9]),
            "BAD": _make_fd(ticker="BAD", gross_profit=[-100e6], total_assets=[10e9, 9e9]),
        }
        qs, _, prof, _ = compute_quality_scores(stocks)
        assert "BAD" in prof  # negative GP is scored, not excluded
        assert prof["BAD"] < 0  # ratio is negative
        assert qs["GOOD"] > qs["BAD"]

    def test_negative_ni_roa_ranks_low(self):
        """Negative NI via ROA fallback should rank low, not vanish."""
        stocks = {
            "LOSS": _make_fd(ticker="LOSS", gross_profit=[None] * 4,
                             net_income=[-50e6], total_assets=[5e9, 4.5e9]),
            "PROFIT": _make_fd(ticker="PROFIT", gross_profit=[3e9],
                               total_assets=[10e9, 9e9]),
        }
        qs, _, prof, _ = compute_quality_scores(stocks)
        assert "LOSS" in prof
        assert prof["LOSS"] < 0

    def test_none_gp_and_none_ni_excluded(self):
        """Truly missing GP and NI (both None) → excluded from profitability."""
        stocks = {
            "MISSING": _make_fd(ticker="MISSING", gross_profit=[None] * 4,
                                net_income=[None] * 4, total_assets=[10e9, 9e9]),
        }
        _, _, prof, _ = compute_quality_scores(stocks)
        assert "MISSING" not in prof


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


class TestPiotroskiBreakdown:
    def test_calculate_detailed_returns_all_criteria(self):
        """Breakdown should contain all 9 criteria with 'pass' booleans."""
        pio = PiotroskiModel()
        fd = _make_fd()
        score, breakdown = pio.calculate_detailed(fd)
        assert score is not None
        criteria = breakdown["criteria"]
        assert len(criteria) == 9
        expected_keys = {
            "net_income_positive", "ocf_positive", "roa_improving",
            "accruals_quality", "debt_ratio_decreasing", "current_ratio_up",
            "no_dilution", "gross_margin_up", "asset_turnover_up",
        }
        assert set(criteria.keys()) == expected_keys
        for c in criteria.values():
            assert "pass" in c
            assert isinstance(c["pass"], bool)

    def test_breakdown_sum_matches_raw_score(self):
        """Sum of passing criteria must equal the raw score."""
        pio = PiotroskiModel()
        fd = _make_fd()
        score, breakdown = pio.calculate_detailed(fd)
        passes = sum(1 for c in breakdown["criteria"].values() if c["pass"])
        assert passes == breakdown["raw_score"]
        assert round((passes / 9) * 100, 1) == score

    def test_breakdown_with_missing_data(self):
        """Missing data should produce all-False criteria, not crash."""
        pio = PiotroskiModel()
        fd = _make_fd(
            net_income=[None]*4, operating_cash_flow=[None]*4,
            total_assets=[None]*2, total_debt=[None]*2,
            current_assets=[None]*2, current_liabilities=[None]*2,
            ordinary_shares_number=[None]*2,
            gross_profit=[None]*4, revenue=[None]*4,
        )
        score, breakdown = pio.calculate_detailed(fd)
        assert score == 0.0
        assert breakdown["raw_score"] == 0

    def test_calculate_wrapper_matches_detailed(self):
        """calculate() must return the same score as calculate_detailed()[0]."""
        pio = PiotroskiModel()
        fd = _make_fd()
        assert pio.calculate(fd) == pio.calculate_detailed(fd)[0]


class TestConfidenceLevel:
    def test_high_confidence(self):
        assert confidence_level(90, 90) == "HIGH"
        assert confidence_level(85, 86) == "HIGH"

    def test_moderate_confidence(self):
        assert confidence_level(78, 78) == "MODERATE"
        assert confidence_level(75, 80) == "MODERATE"

    def test_low_confidence(self):
        assert confidence_level(71, 71) == "LOW"
        assert confidence_level(70, 95) == "LOW"

    def test_none_input(self):
        assert confidence_level(None, 80) is None
        assert confidence_level(80, None) is None


class TestMinFScoreGate:
    def test_downgrades_low_fscore(self):
        """F=5 with MIN_F=6 should downgrade CONVICTION BUY to WATCH LIST."""
        assert apply_min_fscore("CONVICTION BUY", 5) == "WATCH LIST"
        assert apply_min_fscore("CONVICTION BUY", 4) == "WATCH LIST"

    def test_keeps_high_fscore(self):
        """F=6+ should stay as CONVICTION BUY."""
        assert apply_min_fscore("CONVICTION BUY", 6) == "CONVICTION BUY"
        assert apply_min_fscore("CONVICTION BUY", 9) == "CONVICTION BUY"

    def test_only_affects_conviction_buy(self):
        """Other classifications should not be changed regardless of F-Score."""
        assert apply_min_fscore("VALUE TRAP", 2) == "VALUE TRAP"
        assert apply_min_fscore("WATCH LIST", 3) == "WATCH LIST"
        assert apply_min_fscore("HOLD", 1) == "HOLD"

    def test_boundary(self):
        """F-Score exactly at minimum (6) should pass."""
        assert apply_min_fscore("CONVICTION BUY", 6) == "CONVICTION BUY"


class TestExcludeFinancials:
    def test_keeps_fintech_with_oi(self):
        """Financials WITH operating income (PYPL-like) should be kept."""
        from main import _include_stock
        fd = _make_fd(sector="Financials", operating_income=[3e9, 2.5e9])
        assert _include_stock(fd) is True

    def test_removes_bank_without_oi(self):
        """Financials WITHOUT operating income (bank-like) should be excluded."""
        from main import _include_stock
        fd = _make_fd(sector="Financials", operating_income=[None, None])
        assert _include_stock(fd) is False

    def test_removes_reit(self):
        """Real Estate should always be excluded."""
        from main import _include_stock
        fd = _make_fd(sector="Real Estate", operating_income=[1e9, 0.9e9])
        assert _include_stock(fd) is False

    def test_keeps_non_financial(self):
        """Non-financial sectors should always be kept."""
        from main import _include_stock
        fd = _make_fd(sector="Information Technology")
        assert _include_stock(fd) is True
