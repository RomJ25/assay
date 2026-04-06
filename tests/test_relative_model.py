"""Unit tests for relative valuation model."""

from data.providers.base import FinancialData
from models.relative import RelativeModel


def _make_fd(**overrides) -> FinancialData:
    defaults = dict(
        ticker="TEST", company_name="Test Corp", sector="Technology",
        sub_industry="Software",
        current_price=100.0, market_cap=50e9,
        trailing_pe=20.0, enterprise_to_ebitda=15.0, price_to_sales=5.0,
        revenue=[10e9, 9e9, 8e9, 7e9],
        net_income=[2e9, 1.8e9, 1.5e9, 1.2e9],
        diluted_eps=[5.0, 4.4, 3.8, 3.2],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


class TestSectorMedians:
    def test_minimum_stocks_for_median(self):
        """Need at least 3 stocks in sector for meaningful median."""
        model = RelativeModel()
        stocks = {
            "A": _make_fd(ticker="A", trailing_pe=15.0),
            "B": _make_fd(ticker="B", trailing_pe=20.0),
        }
        model.compute_sector_medians(stocks)
        medians = model._sector_medians.get("Technology", {})
        # Only 2 stocks — PE median should be None
        assert medians.get("pe") is None

    def test_three_stocks_gives_median(self):
        model = RelativeModel()
        stocks = {
            "A": _make_fd(ticker="A", trailing_pe=10.0),
            "B": _make_fd(ticker="B", trailing_pe=20.0),
            "C": _make_fd(ticker="C", trailing_pe=30.0),
        }
        model.compute_sector_medians(stocks)
        medians = model._sector_medians["Technology"]
        assert medians["pe"] == 20.0

    def test_outlier_pe_excluded(self):
        """PE > 100 should be excluded from median calculation."""
        model = RelativeModel()
        stocks = {
            "A": _make_fd(ticker="A", trailing_pe=10.0),
            "B": _make_fd(ticker="B", trailing_pe=20.0),
            "C": _make_fd(ticker="C", trailing_pe=30.0),
            "D": _make_fd(ticker="D", trailing_pe=500.0),  # outlier
        }
        model.compute_sector_medians(stocks)
        medians = model._sector_medians["Technology"]
        assert medians["pe"] == 20.0  # median of [10, 20, 30], D excluded


class TestRelativeCalculation:
    def test_cheap_stock_positive_discount(self):
        model = RelativeModel()
        stocks = {
            "A": _make_fd(ticker="A", trailing_pe=10.0),
            "B": _make_fd(ticker="B", trailing_pe=20.0),
            "C": _make_fd(ticker="C", trailing_pe=30.0),
        }
        model.compute_sector_medians(stocks)
        result = model.calculate(stocks["A"])
        assert result.intrinsic_value is not None
        assert result.details.get("pe_discount", 0) > 0  # cheaper than median

    def test_expensive_stock_negative_discount(self):
        model = RelativeModel()
        stocks = {
            "A": _make_fd(ticker="A", trailing_pe=10.0),
            "B": _make_fd(ticker="B", trailing_pe=20.0),
            "C": _make_fd(ticker="C", trailing_pe=30.0),
        }
        model.compute_sector_medians(stocks)
        result = model.calculate(stocks["C"])
        assert result.details.get("pe_discount", 0) < 0  # more expensive than median

    def test_no_sector_medians_skipped(self):
        model = RelativeModel()
        # Don't compute medians
        fd = _make_fd(sector="Unknown")
        result = model.calculate(fd)
        assert result.intrinsic_value is None
        assert result.details.get("skipped") == "no_sector_medians"


class TestPegRatio:
    def test_peg_with_positive_growth(self):
        model = RelativeModel()
        fd = _make_fd(trailing_pe=20.0, diluted_eps=[5.0, 4.0, 3.0, 2.0])
        peg = model._calculate_peg(fd)
        assert peg is not None and peg > 0

    def test_peg_no_growth_returns_none(self):
        """Zero or negative growth -> PEG not meaningful."""
        model = RelativeModel()
        fd = _make_fd(trailing_pe=20.0, diluted_eps=[3.0, 4.0, 5.0, 6.0])  # declining
        peg = model._calculate_peg(fd)
        assert peg is None

    def test_peg_no_pe_returns_none(self):
        model = RelativeModel()
        fd = _make_fd(trailing_pe=None)
        peg = model._calculate_peg(fd)
        assert peg is None
