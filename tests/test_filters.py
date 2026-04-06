"""Unit tests for data quality filters."""

from data.providers.base import FinancialData


def _make_fd(**overrides) -> FinancialData:
    defaults = dict(
        ticker="TEST", company_name="Test Corp", sector="Technology",
        sub_industry="Software",
        current_price=100.0, market_cap=50e9,
        revenue=[10e9, 9e9, 8e9, 7e9],
        net_income=[2e9, 1.8e9, 1.5e9, 1.2e9],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


class TestHasMinimumData:
    def test_valid_data_passes(self):
        fd = _make_fd()
        assert fd.has_minimum_data is True

    def test_zero_price_fails(self):
        fd = _make_fd(current_price=0.0)
        assert fd.has_minimum_data is False

    def test_none_revenue_fails(self):
        fd = _make_fd(revenue=[None, 9e9, 8e9, 7e9])
        assert fd.has_minimum_data is False

    def test_negative_revenue_fails(self):
        fd = _make_fd(revenue=[-1e9, 9e9, 8e9, 7e9])
        assert fd.has_minimum_data is False

    def test_none_net_income_fails(self):
        fd = _make_fd(net_income=[None, 1.8e9, 1.5e9, 1.2e9])
        assert fd.has_minimum_data is False

    def test_negative_net_income_allowed(self):
        """Net income can be negative (cyclical companies)."""
        fd = _make_fd(net_income=[-500e6, 1.8e9, 1.5e9, 1.2e9])
        assert fd.has_minimum_data is True
