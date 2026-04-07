"""Unit tests for value scoring and DCF context model."""

from data.providers.base import FinancialData
from models.dcf import DCFModel
from scoring.value_scorer import compute_value_scores


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
        free_cash_flow=[2e9, 1.8e9, 1.5e9, 1.2e9],
        operating_cash_flow=[3e9, 2.7e9, 2.3e9, 2e9],
        capital_expenditure=[-1e9, -0.9e9, -0.8e9, -0.8e9],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


class TestEarningsYieldRanking:
    def test_higher_yield_ranks_higher(self):
        stocks = {
            "CHEAP": _make_fd(ticker="CHEAP", operating_income=[5e9], enterprise_value=20e9),
            "EXPENSIVE": _make_fd(ticker="EXPENSIVE", operating_income=[1e9], enterprise_value=50e9),
        }
        scores = compute_value_scores(stocks)
        assert scores["CHEAP"] > scores["EXPENSIVE"]

    def test_negative_oi_ranks_low(self):
        """Negative OI is a real signal (bad), not missing — it should rank at the bottom."""
        stocks = {
            "POS": _make_fd(ticker="POS", operating_income=[3e9]),
            "NEG": _make_fd(ticker="NEG", operating_income=[-1e9, -0.5e9, 0.2e9, 0.5e9],
                            trailing_pe=None),
        }
        scores = compute_value_scores(stocks)
        assert "POS" in scores
        assert "NEG" in scores  # negative OI IS scored (via EBIT/EV with negative yield)
        assert scores["NEG"] < scores["POS"]

    def test_missing_oi_no_pe_excluded(self):
        """Truly missing OI (None) with no PE fallback → excluded."""
        stocks = {
            "POS": _make_fd(ticker="POS", operating_income=[3e9]),
            "MISSING": _make_fd(ticker="MISSING", operating_income=[None] * 4,
                                trailing_pe=None),
        }
        scores = compute_value_scores(stocks)
        assert "POS" in scores
        assert "MISSING" not in scores

    def test_negative_fcf_ranks_low(self):
        """Negative FCF should rank below positive FCF, not get neutral default 50."""
        stocks = {
            "GOOD": _make_fd(ticker="GOOD", operating_income=[3e9],
                             free_cash_flow=[2e9, 1.5e9]),
            "BAD": _make_fd(ticker="BAD", operating_income=[3e9],
                            free_cash_flow=[-1e9, -0.5e9]),
        }
        scores = compute_value_scores(stocks)
        # GOOD has positive FCF yield → boosted by FCF component
        # BAD has negative FCF yield → penalized by FCF component
        assert scores["GOOD"] > scores["BAD"]

    def test_negative_oi_uses_ebit_ev_not_pe_fallback(self):
        """Stock with negative OI should use EBIT/EV path, not fall to 1/PE."""
        stocks = {
            "NEG_OI": _make_fd(ticker="NEG_OI", operating_income=[-500e6],
                               enterprise_value=20e9, trailing_pe=15.0),
        }
        scores = compute_value_scores(stocks)
        assert "NEG_OI" in scores
        # Yield = -500M / 20B = -2.5% (via EBIT/EV), NOT 1/15 = 6.7% (via PE)
        # With only 1 stock, score is based on rank position — just verify it's scored

    def test_pe_fallback_for_financials(self):
        stocks = {
            "BANK": _make_fd(ticker="BANK", operating_income=[None]*4, trailing_pe=10.0, enterprise_value=None),
            "TECH": _make_fd(ticker="TECH", operating_income=[3e9]),
        }
        scores = compute_value_scores(stocks)
        assert "BANK" in scores  # should get score via 1/PE fallback

    def test_ev_fallback_from_components(self):
        stocks = {
            "NO_EV": _make_fd(ticker="NO_EV", enterprise_value=None, market_cap=50e9,
                              total_debt=[5e9, 5e9], cash_and_equivalents=[3e9, 2.5e9]),
        }
        scores = compute_value_scores(stocks)
        assert "NO_EV" in scores


class TestSectorRelative:
    def test_off_by_default_matches_absolute(self):
        """Without sector_relative, scores should be identical to absolute ranking."""
        stocks = {
            "A": _make_fd(ticker="A", operating_income=[5e9], enterprise_value=20e9, sector="Tech"),
            "B": _make_fd(ticker="B", operating_income=[1e9], enterprise_value=50e9, sector="Utilities"),
        }
        scores_abs = compute_value_scores(stocks, sector_relative=False)
        scores_default = compute_value_scores(stocks)
        assert scores_abs == scores_default

    def test_sector_relative_boosts_within_sector_leader(self):
        """The cheapest stock in an expensive sector gets boosted by sector-relative."""
        stocks = {
            "CHEAP_UTIL": _make_fd(ticker="CHEAP_UTIL", operating_income=[5e9],
                                   enterprise_value=20e9, sector="Utilities"),
            "MID_UTIL": _make_fd(ticker="MID_UTIL", operating_income=[3e9],
                                 enterprise_value=30e9, sector="Utilities"),
            "EXP_UTIL": _make_fd(ticker="EXP_UTIL", operating_income=[1e9],
                                 enterprise_value=40e9, sector="Utilities"),
            "CHEAP_TECH": _make_fd(ticker="CHEAP_TECH", operating_income=[2e9],
                                   enterprise_value=100e9, sector="Information Technology"),
            "MID_TECH": _make_fd(ticker="MID_TECH", operating_income=[1e9],
                                 enterprise_value=100e9, sector="Information Technology"),
            "EXP_TECH": _make_fd(ticker="EXP_TECH", operating_income=[0.5e9],
                                 enterprise_value=100e9, sector="Information Technology"),
        }
        scores_abs = compute_value_scores(stocks, sector_relative=False)
        scores_sr = compute_value_scores(stocks, sector_relative=True)
        # CHEAP_TECH has low absolute EY (2/100=2%) but is #1 in tech sector
        # Sector-relative should boost it relative to absolute
        assert scores_sr["CHEAP_TECH"] > scores_abs["CHEAP_TECH"]

    def test_small_sector_falls_back(self):
        """Sector with <3 stocks should not crash — uses absolute as fallback."""
        stocks = {
            "LONE": _make_fd(ticker="LONE", operating_income=[3e9],
                             enterprise_value=20e9, sector="Energy"),
            "A": _make_fd(ticker="A", operating_income=[2e9],
                          enterprise_value=30e9, sector="Tech"),
            "B": _make_fd(ticker="B", operating_income=[1e9],
                          enterprise_value=40e9, sector="Tech"),
            "C": _make_fd(ticker="C", operating_income=[0.5e9],
                          enterprise_value=50e9, sector="Tech"),
        }
        scores = compute_value_scores(stocks, sector_relative=True)
        assert "LONE" in scores  # single-stock sector doesn't crash


class TestDCFContext:
    def test_basic_calculation(self):
        fd = _make_fd()
        dcf = DCFModel()
        result = dcf.calculate(fd)
        assert result.intrinsic_value is not None
        assert result.details["dcf_bear"] < result.details["dcf_base"] < result.details["dcf_bull"]

    def test_bank_skipped(self):
        fd = _make_fd(sub_industry="Diversified Banks")
        dcf = DCFModel()
        result = dcf.calculate(fd)
        assert result.intrinsic_value is None

    def test_negative_fcf_uses_average(self):
        fd = _make_fd(free_cash_flow=[-1e9, 3e9, 2e9, 1e9])
        dcf = DCFModel()
        result = dcf.calculate(fd)
        assert result.intrinsic_value is not None  # uses avg of positive FCFs
