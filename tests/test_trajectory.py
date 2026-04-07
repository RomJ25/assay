"""Unit tests for trajectory score."""

from data.providers.base import FinancialData
from scoring.trajectory import compute_trajectory_scores


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
        ordinary_shares_number=[500e6, 500e6],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


class TestTrajectory:
    def test_improving_company_scores_high(self):
        """Company with improving ROA, GM, deleveraging, buybacks → high trajectory."""
        stocks = {
            "IMPROVING": _make_fd(
                ticker="IMPROVING",
                net_income=[3e9, 1e9],           # ROA improving
                gross_profit=[6e9, 4e9],          # GM improving
                total_debt=[3e9, 5e9],            # deleveraging
                ordinary_shares_number=[450e6, 500e6],  # buybacks
            ),
            "FLAT": _make_fd(ticker="FLAT"),
        }
        mom = {"IMPROVING": 70, "FLAT": 50}
        scores = compute_trajectory_scores(stocks, mom)
        assert scores["IMPROVING"] > scores["FLAT"]

    def test_deteriorating_company_scores_low(self):
        """Company with worsening fundamentals → low trajectory."""
        stocks = {
            "WORSENING": _make_fd(
                ticker="WORSENING",
                net_income=[1e9, 3e9],            # ROA worsening
                gross_profit=[4e9, 6e9],           # GM worsening
                total_debt=[8e9, 5e9],             # leveraging up
                ordinary_shares_number=[550e6, 500e6],  # dilution
            ),
            "FLAT": _make_fd(ticker="FLAT"),
        }
        mom = {"WORSENING": 30, "FLAT": 50}
        scores = compute_trajectory_scores(stocks, mom)
        assert scores["WORSENING"] < scores["FLAT"]

    def test_missing_data_partial_score(self):
        """Stock with some missing metrics should still get a score (via neutral 50)."""
        stocks = {
            "SPARSE": _make_fd(
                ticker="SPARSE",
                net_income=[None, None],
                gross_profit=[None, None],
                total_debt=[None, None],
                ordinary_shares_number=[None, None],
            ),
        }
        scores = compute_trajectory_scores(stocks, {})
        assert "SPARSE" in scores
        assert scores["SPARSE"] == 50.0  # all components neutral

    def test_momentum_contributes(self):
        """Two companies with identical fundamentals but different momentum → different trajectory."""
        fd_base = dict(
            net_income=[2.5e9, 2.2e9],
            total_assets=[20e9, 18e9],
            gross_profit=[6e9, 5.3e9],
            revenue=[10e9, 9e9],
            total_debt=[5e9, 5e9],
            ordinary_shares_number=[500e6, 500e6],
        )
        stocks = {
            "HIGH_MOM": _make_fd(ticker="HIGH_MOM", **fd_base),
            "LOW_MOM": _make_fd(ticker="LOW_MOM", **fd_base),
        }
        mom = {"HIGH_MOM": 90, "LOW_MOM": 10}
        scores = compute_trajectory_scores(stocks, mom)
        assert scores["HIGH_MOM"] > scores["LOW_MOM"]
