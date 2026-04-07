"""Build FinancialData snapshots from historical data for a given date."""

from __future__ import annotations

import logging
import math
from datetime import date, timedelta

from config import BACKTEST_FILING_LAG_DAYS
from data.providers.base import FinancialData

logger = logging.getLogger(__name__)


def _safe_float(val) -> float | None:
    """Convert a value to float, returning None for NaN/None/errors."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def build_snapshot(
    ticker: str,
    as_of_date: date,
    raw_financials: dict,
    close_price: float,
    sp500_entry: dict,
) -> FinancialData | None:
    """Build a FinancialData snapshot for a ticker at a historical date.

    Args:
        ticker: Stock ticker symbol.
        as_of_date: The rebalance date we're building for.
        raw_financials: Cached dict with 'income', 'balance', 'cashflow' keys,
                        each a list of dicts with 'asOfDate' and financial fields.
        close_price: Historical close price on the rebalance date.
        sp500_entry: Dict with company_name, sector, sub_industry.

    Returns:
        FinancialData or None if insufficient data.
    """
    if not raw_financials or close_price <= 0:
        return None

    filing_cutoff = as_of_date - timedelta(days=BACKTEST_FILING_LAG_DAYS)

    # Filter and sort statements by availability (most recent first)
    income_rows = _filter_statements(raw_financials.get("income", []), filing_cutoff, annual_only=True)
    balance_rows = _filter_statements(raw_financials.get("balance", []), filing_cutoff, annual_only=False)
    cashflow_rows = _filter_statements(raw_financials.get("cashflow", []), filing_cutoff, annual_only=True)

    # Need at least 1 income statement year
    if not income_rows:
        return None

    # Extract field lists (most recent first, matching existing convention)
    revenue = _extract_field(income_rows, "TotalRevenue", 4)
    net_income = _extract_field(income_rows, "NetIncome", 4)

    # Minimum data: need revenue and net income for latest year
    if revenue[0] is None or net_income[0] is None:
        return None

    # Shares from balance sheet (Yahoo pre-adjusts for splits)
    shares_list = _extract_field(balance_rows, "OrdinarySharesNumber", 2)
    shares = shares_list[0] if shares_list[0] is not None else 0.0

    # Reconstruct market-dependent fields from historical price
    market_cap = close_price * shares if shares > 0 else 0.0

    # Reconstruct EV from components
    total_debt_list = _extract_field(balance_rows, "TotalDebt", 2)
    cash_list = _extract_field(balance_rows, "CashAndCashEquivalents", 2)
    debt_val = total_debt_list[0] or 0.0
    cash_val = cash_list[0] or 0.0
    enterprise_value = market_cap + debt_val - cash_val if market_cap > 0 else None

    # EPS (Yahoo pre-adjusts for splits)
    eps_list = _extract_field(income_rows, "DilutedEPS", 4)

    # Trailing P/E from historical price and latest EPS
    trailing_pe = None
    if eps_list[0] is not None and eps_list[0] > 0:
        trailing_pe = close_price / eps_list[0]

    return FinancialData(
        ticker=ticker,
        company_name=sp500_entry.get("company_name", ""),
        sector=sp500_entry.get("sector", ""),
        sub_industry=sp500_entry.get("sub_industry", ""),

        current_price=close_price,
        market_cap=market_cap,
        shares_outstanding=shares,
        enterprise_value=enterprise_value,
        trailing_pe=trailing_pe,

        # These are unavailable historically — set to None
        beta=None,
        forward_pe=None,
        price_to_book=None,
        enterprise_to_ebitda=None,
        price_to_sales=None,
        dividend_yield=None,
        analyst_target=None,
        fifty_two_week_high=None,

        # Income statement
        revenue=revenue,
        gross_profit=_extract_field(income_rows, "GrossProfit", 4),
        operating_income=_extract_field(income_rows, "OperatingIncome", 4),
        net_income=net_income,
        diluted_eps=eps_list,
        ebitda=_extract_field(income_rows, "EBITDA", 4),
        interest_expense=_extract_field(income_rows, "InterestExpense", 4),
        tax_provision=_extract_field(income_rows, "TaxProvision", 4),
        pretax_income=_extract_field(income_rows, "PretaxIncome", 4),

        # Balance sheet
        total_assets=_extract_field(balance_rows, "TotalAssets", 2),
        current_assets=_extract_field(balance_rows, "CurrentAssets", 2),
        current_liabilities=_extract_field(balance_rows, "CurrentLiabilities", 2),
        total_debt=total_debt_list,
        cash_and_equivalents=cash_list,
        stockholders_equity=_extract_field(balance_rows, "StockholdersEquity", 2),
        retained_earnings=_extract_field(balance_rows, "RetainedEarnings", 2),
        ordinary_shares_number=shares_list,

        # Cash flow
        free_cash_flow=_extract_field(cashflow_rows, "FreeCashFlow", 4),
        operating_cash_flow=_extract_field(cashflow_rows, "OperatingCashFlow", 4),
        capital_expenditure=_extract_field(cashflow_rows, "CapitalExpenditure", 4),
    )


def _filter_statements(
    rows: list[dict],
    filing_cutoff: date,
    annual_only: bool = True,
) -> list[dict]:
    """Filter statement rows by filing availability and sort most-recent first.

    A statement is available if its asOfDate <= filing_cutoff (i.e., the company
    had enough time to file it before the rebalance date).
    """
    available = []
    for row in rows:
        as_of = row.get("asOfDate")
        if as_of is None:
            continue

        # Parse date string
        try:
            if isinstance(as_of, str):
                row_date = date.fromisoformat(as_of[:10])
            else:
                row_date = as_of
        except (ValueError, TypeError):
            continue

        # Filing lag filter
        if row_date > filing_cutoff:
            continue

        # Annual-only filter
        if annual_only:
            period_type = row.get("periodType")
            if period_type is not None and period_type != "12M":
                continue

        available.append((row_date, row))

    # Sort most recent first
    available.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in available]


def _extract_field(rows: list[dict], field_name: str, n: int) -> list[float | None]:
    """Extract up to n values from filtered rows (most recent first)."""
    vals = []
    for row in rows[:n]:
        vals.append(_safe_float(row.get(field_name)))
    # Pad with None if fewer rows than n
    return vals + [None] * (n - len(vals))
