"""Unit tests for backtest snapshot builder."""

from datetime import date

from backtest.snapshot_builder import build_snapshot, _filter_statements, _extract_field


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_income_row(as_of: str, **overrides):
    """Build a fake income statement record."""
    row = {
        "asOfDate": as_of,
        "periodType": "12M",
        "TotalRevenue": 10e9,
        "GrossProfit": 6e9,
        "OperatingIncome": 3e9,
        "NetIncome": 2.5e9,
        "DilutedEPS": 5.0,
        "EBITDA": 3.5e9,
        "InterestExpense": 200e6,
        "TaxProvision": 600e6,
        "PretaxIncome": 3.1e9,
    }
    row.update(overrides)
    return row


def _make_balance_row(as_of: str, **overrides):
    row = {
        "asOfDate": as_of,
        "TotalAssets": 20e9,
        "CurrentAssets": 8e9,
        "CurrentLiabilities": 4e9,
        "TotalDebt": 5e9,
        "CashAndCashEquivalents": 3e9,
        "StockholdersEquity": 12e9,
        "RetainedEarnings": 8e9,
        "OrdinarySharesNumber": 500e6,
    }
    row.update(overrides)
    return row


def _make_cashflow_row(as_of: str, **overrides):
    row = {
        "asOfDate": as_of,
        "periodType": "12M",
        "FreeCashFlow": 2e9,
        "OperatingCashFlow": 3e9,
        "CapitalExpenditure": -1e9,
    }
    row.update(overrides)
    return row


def _make_raw_financials(years=None):
    """Build a complete set of raw financials with default years."""
    if years is None:
        years = ["2024-12-31", "2023-12-31", "2022-12-31", "2021-12-31"]
    return {
        "income": [_make_income_row(y) for y in years],
        "balance": [_make_balance_row(y) for y in years[:2]],
        "cashflow": [_make_cashflow_row(y) for y in years],
    }


SP500_ENTRY = {"company_name": "Test Corp", "sector": "Technology", "sub_industry": "Software"}


# ── Filing lag tests ─────────────────────────────────────────────────────

class TestFilingLag:
    def test_statement_too_recent_excluded(self):
        """Statement filed after the rebalance date (with lag) should be excluded."""
        # rebalance on 2025-03-31, filing lag 75 days → cutoff 2025-01-15
        # statement from 2024-12-31 → 2024-12-31 <= 2025-01-15 ✓ (included)
        # statement from 2025-01-20 → 2025-01-20 > 2025-01-15 ✗ (excluded)
        rows = [
            {"asOfDate": "2025-01-20", "periodType": "12M", "TotalRevenue": 99e9},
            {"asOfDate": "2024-12-31", "periodType": "12M", "TotalRevenue": 10e9},
        ]
        cutoff = date(2025, 1, 15)
        filtered = _filter_statements(rows, cutoff, annual_only=True)
        assert len(filtered) == 1
        assert filtered[0]["TotalRevenue"] == 10e9

    def test_all_statements_too_recent(self):
        """If all statements are too recent, return empty list."""
        rows = [{"asOfDate": "2025-06-30", "periodType": "12M", "TotalRevenue": 10e9}]
        cutoff = date(2025, 1, 15)
        filtered = _filter_statements(rows, cutoff, annual_only=True)
        assert len(filtered) == 0

    def test_sorted_most_recent_first(self):
        """Statements should be sorted newest-to-oldest."""
        rows = [
            {"asOfDate": "2022-12-31", "periodType": "12M", "TotalRevenue": 7e9},
            {"asOfDate": "2024-12-31", "periodType": "12M", "TotalRevenue": 10e9},
            {"asOfDate": "2023-12-31", "periodType": "12M", "TotalRevenue": 9e9},
        ]
        cutoff = date(2025, 6, 30)
        filtered = _filter_statements(rows, cutoff, annual_only=True)
        assert len(filtered) == 3
        assert filtered[0]["TotalRevenue"] == 10e9
        assert filtered[1]["TotalRevenue"] == 9e9
        assert filtered[2]["TotalRevenue"] == 7e9

    def test_ttm_rows_excluded_when_annual_only(self):
        """TTM (trailing) rows should be filtered out when annual_only=True."""
        rows = [
            {"asOfDate": "2024-09-30", "periodType": "TTM", "TotalRevenue": 11e9},
            {"asOfDate": "2024-12-31", "periodType": "12M", "TotalRevenue": 10e9},
        ]
        cutoff = date(2025, 6, 30)
        filtered = _filter_statements(rows, cutoff, annual_only=True)
        assert len(filtered) == 1
        assert filtered[0]["TotalRevenue"] == 10e9


# ── Snapshot construction tests ──────────────────────────────────────────

class TestBuildSnapshot:
    def test_basic_snapshot(self):
        """Build a snapshot with complete data."""
        raw = _make_raw_financials()
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 100.0, SP500_ENTRY)
        assert fd is not None
        assert fd.ticker == "TEST"
        assert fd.current_price == 100.0
        assert fd.revenue[0] == 10e9

    def test_market_cap_from_price_and_shares(self):
        """Market cap should be price × shares from balance sheet."""
        raw = _make_raw_financials()
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 200.0, SP500_ENTRY)
        assert fd.market_cap == 200.0 * 500e6

    def test_enterprise_value_reconstruction(self):
        """EV = market_cap + total_debt - cash."""
        raw = _make_raw_financials()
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 100.0, SP500_ENTRY)
        expected_mktcap = 100.0 * 500e6
        expected_ev = expected_mktcap + 5e9 - 3e9
        assert fd.enterprise_value == expected_ev

    def test_trailing_pe_from_historical_price_and_eps(self):
        """PE = price / EPS."""
        raw = _make_raw_financials()
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 100.0, SP500_ENTRY)
        assert fd.trailing_pe == 100.0 / 5.0  # 20.0

    def test_none_when_no_income_data(self):
        """Return None when no income statements available."""
        raw = {"income": [], "balance": [], "cashflow": []}
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 100.0, SP500_ENTRY)
        assert fd is None

    def test_none_when_zero_price(self):
        """Return None when price is 0."""
        raw = _make_raw_financials()
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 0.0, SP500_ENTRY)
        assert fd is None

    def test_none_when_revenue_missing(self):
        """Return None when latest revenue is None."""
        raw = _make_raw_financials()
        raw["income"][0]["TotalRevenue"] = None
        # Remove other income rows so first available has None revenue
        raw["income"] = [raw["income"][0]]
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 100.0, SP500_ENTRY)
        assert fd is None

    def test_context_fields_are_none(self):
        """Analyst target, 52-week high, etc. should be None for historical."""
        raw = _make_raw_financials()
        fd = build_snapshot("TEST", date(2025, 6, 30), raw, 100.0, SP500_ENTRY)
        assert fd.analyst_target is None
        assert fd.fifty_two_week_high is None
        assert fd.beta is None
        assert fd.forward_pe is None

    def test_non_december_fiscal_year(self):
        """Companies with non-December FY should work (filing lag handles it)."""
        # Apple: FY ends Sep 30
        years = ["2024-09-30", "2023-09-30", "2022-09-30", "2021-09-30"]
        raw = _make_raw_financials(years)
        # Rebalance Dec 31, 2024: Sep 30 + 75 = Dec 14 <= Dec 31 → available
        fd = build_snapshot("AAPL", date(2024, 12, 31), raw, 150.0, SP500_ENTRY)
        assert fd is not None
        assert fd.revenue[0] == 10e9


# ── Field extraction tests ───────────────────────────────────────────────

class TestExtractField:
    def test_extracts_up_to_n_values(self):
        rows = [{"val": 10.0}, {"val": 20.0}, {"val": 30.0}]
        result = _extract_field(rows, "val", 4)
        assert result == [10.0, 20.0, 30.0, None]

    def test_pads_with_none(self):
        rows = [{"val": 5.0}]
        result = _extract_field(rows, "val", 3)
        assert result == [5.0, None, None]

    def test_missing_field_returns_none(self):
        rows = [{"other": 5.0}]
        result = _extract_field(rows, "val", 2)
        assert result == [None, None]

    def test_nan_converted_to_none(self):
        rows = [{"val": float("nan")}]
        result = _extract_field(rows, "val", 1)
        assert result == [None]
