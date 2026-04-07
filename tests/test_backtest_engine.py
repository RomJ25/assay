"""Unit tests for backtest engine."""

from datetime import date
from unittest.mock import patch

from data.providers.base import FinancialData
from backtest.engine import _screen_quarter, _generate_rebalance_dates
from backtest.cache import HistoricalCache
from backtest.snapshot_builder import build_snapshot


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
        ordinary_shares_number=[500e6, 510e6],
        free_cash_flow=[2e9, 1.8e9, 1.5e9, 1.2e9],
        operating_cash_flow=[3e9, 2.7e9, 2.3e9, 2e9],
        capital_expenditure=[-1e9, -0.9e9, -0.8e9, -0.8e9],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


def _make_raw_financials(revenue=10e9, oi=3e9, ni=2.5e9, eps=5.0):
    """Build raw financials cache entry."""
    years = ["2024-12-31", "2023-12-31", "2022-12-31", "2021-12-31"]
    return {
        "income": [
            {
                "asOfDate": y, "periodType": "12M",
                "TotalRevenue": revenue, "GrossProfit": revenue * 0.6,
                "OperatingIncome": oi, "NetIncome": ni, "DilutedEPS": eps,
                "EBITDA": oi * 1.1, "InterestExpense": 200e6,
                "TaxProvision": ni * 0.24, "PretaxIncome": ni * 1.24,
            }
            for y in years
        ],
        "balance": [
            {
                "asOfDate": y,
                "TotalAssets": 20e9, "CurrentAssets": 8e9,
                "CurrentLiabilities": 4e9, "TotalDebt": 5e9,
                "CashAndCashEquivalents": 3e9, "StockholdersEquity": 12e9,
                "RetainedEarnings": 8e9, "OrdinarySharesNumber": 500e6,
            }
            for y in years[:2]
        ],
        "cashflow": [
            {
                "asOfDate": y, "periodType": "12M",
                "FreeCashFlow": 2e9, "OperatingCashFlow": 3e9,
                "CapitalExpenditure": -1e9,
            }
            for y in years
        ],
    }


class TestGenerateRebalanceDates:
    def test_generates_quarterly_dates(self):
        with patch("backtest.engine.date") as mock_date:
            mock_date.today.return_value = date(2026, 4, 6)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            dates = _generate_rebalance_dates(2)

        assert all(isinstance(d, date) for d in dates)
        assert dates == sorted(dates)
        # 2 years back = 2024, quarters in 2024 + 2025 + Q1 2026
        # 2024: Q1-Q4 = 4, 2025: Q1-Q4 = 4, 2026: Q1 = 1 → 9 dates
        assert len(dates) >= 8

    def test_dates_are_quarter_ends(self):
        with patch("backtest.engine.date") as mock_date:
            mock_date.today.return_value = date(2026, 4, 6)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            dates = _generate_rebalance_dates(1)

        valid_month_days = {(3, 31), (6, 30), (9, 30), (12, 31)}
        for d in dates:
            assert (d.month, d.day) in valid_month_days


class TestScreenQuarter:
    def test_screens_with_mock_cache(self, tmp_path):
        """Verify screening pipeline works end-to-end on cached data."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")
        rebal_date = date(2025, 6, 30)

        # Set up 5 stocks with varying quality
        tickers = ["GOOD1", "GOOD2", "MED1", "MED2", "BAD1"]
        sp500_info = {}

        for i, ticker in enumerate(tickers):
            # Vary operating income to create score spread
            oi_mult = [1.0, 0.9, 0.5, 0.4, 0.1][i]
            raw = _make_raw_financials(oi=3e9 * oi_mult, ni=2.5e9 * oi_mult, eps=5.0 * oi_mult)
            cache.set_financials(ticker, raw)
            cache.set_prices([
                (ticker, rebal_date.isoformat(), 100.0, 100.0),
            ])
            sp500_info[ticker] = {
                "company_name": f"Company {ticker}",
                "sector": "Information Technology",
                "sub_industry": "Application Software",
            }

        qr = _screen_quarter(rebal_date, tickers, sp500_info, cache, False, False)
        cache.close()

        assert qr is not None
        assert qr.date == rebal_date
        assert qr.num_screened == 5
        assert len(qr.universe) == 5
        assert sum(qr.classifications.values()) > 0

    def test_exclude_financials(self, tmp_path):
        """The financial sector filter should exclude banks/REITs."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")
        rebal_date = date(2025, 6, 30)

        tickers = ["TECH", "BANK"]
        sp500_info = {
            "TECH": {"company_name": "Tech Co", "sector": "Information Technology", "sub_industry": "Software"},
            "BANK": {"company_name": "Big Bank", "sector": "Financials", "sub_industry": "Diversified Banks"},
        }

        # BANK has no operating income (like a real bank)
        tech_raw = _make_raw_financials(oi=3e9)
        bank_raw = _make_raw_financials(oi=0)
        # Zero out operating income for the bank
        for row in bank_raw["income"]:
            row["OperatingIncome"] = None

        cache.set_financials("TECH", tech_raw)
        cache.set_financials("BANK", bank_raw)
        for t in tickers:
            cache.set_prices([(t, rebal_date.isoformat(), 100.0, 100.0)])

        # Without filter: both included
        qr = _screen_quarter(rebal_date, tickers, sp500_info, cache, False, False)
        assert qr is not None
        assert "BANK" in qr.universe

        # With filter: bank excluded
        qr_filtered = _screen_quarter(rebal_date, tickers, sp500_info, cache, True, False)
        assert qr_filtered is not None
        assert "BANK" not in qr_filtered.universe
        assert "TECH" in qr_filtered.universe

        cache.close()

    def test_insufficient_data_returns_none(self, tmp_path):
        """Quarter with no usable data should return None."""
        cache = HistoricalCache(db_path=tmp_path / "test.db")
        rebal_date = date(2025, 6, 30)

        # No financials or prices cached
        qr = _screen_quarter(rebal_date, ["MISSING"], {"MISSING": {"company_name": "X", "sector": "Y", "sub_industry": "Z"}}, cache, False, False)
        cache.close()

        assert qr is None
