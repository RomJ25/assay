"""Primary data provider using yahooquery (API-based, batch, async)."""

from __future__ import annotations

import logging
import math
import time
from typing import Any

import pandas as pd
from yahooquery import Ticker

from config import (
    YAHOOQUERY_MAX_WORKERS,
    YAHOOQUERY_TIMEOUT,
)
from data.providers.base import DataProvider, FinancialData

logger = logging.getLogger(__name__)

# PascalCase fields from financial statement DataFrames
_INCOME_FIELDS = [
    "TotalRevenue", "GrossProfit", "OperatingIncome", "NetIncome",
    "DilutedEPS", "EBITDA", "TaxProvision", "PretaxIncome", "InterestExpense",
]
_BALANCE_FIELDS = [
    "TotalAssets", "CurrentAssets", "CurrentLiabilities", "TotalDebt",
    "CashAndCashEquivalents", "StockholdersEquity", "RetainedEarnings",
    "OrdinarySharesNumber",
]
_CASHFLOW_FIELDS = [
    "FreeCashFlow", "OperatingCashFlow", "CapitalExpenditure",
]


def _safe_float(val: Any) -> float | None:
    """Convert a value to float, returning None for NaN/None/errors."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def _col_list(df: pd.DataFrame, col: str, n: int = 4) -> list[float | None]:
    """Extract up to n values from a DataFrame column (most recent first)."""
    if col not in df.columns:
        return [None] * n
    vals = [_safe_float(v) for v in df[col].head(n).tolist()]
    return vals + [None] * (n - len(vals))


def _get_dict_val(data: dict | str, key: str) -> Any:
    """Safely get a value from a dict that might be a string error message."""
    if not isinstance(data, dict):
        return None
    val = data.get(key)
    if isinstance(val, str) and val.startswith("No fundamentals"):
        return None
    return _safe_float(val) if val is not None else None


class YahooQueryProvider(DataProvider):
    """Primary provider using yahooquery."""

    def fetch_prices(self, tickers: list[str]) -> dict[str, float]:
        """Fetch prices — delegates to yfinance batch for efficiency."""
        # yahooquery's price fetching is per-ticker; yfinance batch is faster
        from data.providers.yfinance_provider import YFinanceProvider
        return YFinanceProvider().fetch_prices(tickers)

    def fetch_financial_data(
        self, tickers: list[str], sp500_info: dict[str, dict]
    ) -> dict[str, FinancialData]:
        """Fetch fundamental data for a batch of tickers."""
        if not tickers:
            return {}

        logger.info(f"Fetching fundamentals for {len(tickers)} tickers via yahooquery...")

        t = Ticker(
            tickers,
            asynchronous=True,
            max_workers=YAHOOQUERY_MAX_WORKERS,
            progress=False,
            timeout=YAHOOQUERY_TIMEOUT,
        )

        # Fetch all data endpoints with delays to avoid rate limiting
        def _fetch_with_retry(fn, name, default, retries=2):
            for attempt in range(retries):
                try:
                    result = fn()
                    if isinstance(result, str) and ("error" in result.lower() or "too many" in result.lower()):
                        logger.warning(f"{name} returned error string: {result[:100]}")
                        if attempt < retries - 1:
                            time.sleep(3)
                            continue
                        return default
                    return result
                except Exception as e:
                    logger.warning(f"{name} attempt {attempt+1} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(3)
            return default

        income_df = _fetch_with_retry(lambda: t.income_statement(frequency="a", trailing=True), "income_statement", pd.DataFrame())
        time.sleep(1)
        balance_df = _fetch_with_retry(lambda: t.balance_sheet(frequency="a"), "balance_sheet", pd.DataFrame())
        time.sleep(1)
        cashflow_df = _fetch_with_retry(lambda: t.cash_flow(frequency="a", trailing=True), "cash_flow", pd.DataFrame())
        time.sleep(1)

        summary = _fetch_with_retry(lambda: t.summary_detail, "summary_detail", {})
        time.sleep(1)
        key_stats = _fetch_with_retry(lambda: t.key_stats, "key_stats", {})
        time.sleep(1)

        try:
            fin_data = t.financial_data
        except Exception as e:
            logger.error(f"financial_data failed: {e}")
            fin_data = {}

        # Map each ticker to FinancialData
        results = {}
        for ticker in tickers:
            try:
                fd = self._map_ticker(
                    ticker, income_df, balance_df, cashflow_df,
                    summary, key_stats, fin_data, sp500_info,
                )
                if fd is not None:
                    results[ticker] = fd
            except Exception as e:
                logger.warning(f"Failed to map {ticker}: {e}")

        logger.info(f"Mapped {len(results)}/{len(tickers)} tickers successfully")
        return results

    def _map_ticker(
        self,
        ticker: str,
        income_df: pd.DataFrame,
        balance_df: pd.DataFrame,
        cashflow_df: pd.DataFrame,
        summary: dict,
        key_stats: dict,
        fin_data: dict,
        sp500_info: dict[str, dict],
    ) -> FinancialData | None:
        """Map yahooquery data for a single ticker to FinancialData."""

        sp = sp500_info.get(ticker, {})
        if not sp:
            return None

        # Get dict data for this ticker
        summ = summary.get(ticker, {}) if isinstance(summary, dict) else {}
        kstats = key_stats.get(ticker, {}) if isinstance(key_stats, dict) else {}
        fdata = fin_data.get(ticker, {}) if isinstance(fin_data, dict) else {}

        # Skip if summary is an error string (e.g., rate limited)
        if isinstance(summ, str):
            logger.warning(f"{ticker}: summary_detail returned error: {summ[:80]}")
            return None
        if isinstance(kstats, str):
            logger.warning(f"{ticker}: key_stats returned error: {kstats[:80]}")
            return None
        if isinstance(fdata, str):
            logger.warning(f"{ticker}: financial_data returned error: {fdata[:80]}")
            return None

        # Get price
        price = _get_dict_val(fdata, "currentPrice")
        if price is None or price == 0:
            price = _get_dict_val(summ, "previousClose")
        if price is None or price == 0:
            logger.warning(f"{ticker}: no price available")
            return None

        # Extract financial statement DataFrames for this ticker
        inc = self._filter_ticker_df(income_df, ticker, annual_only=True)
        bal = self._filter_ticker_df(balance_df, ticker, annual_only=False)
        cf = self._filter_ticker_df(cashflow_df, ticker, annual_only=True)

        # Compute shares from market_cap / price — more reliable than key_stats
        # because key_stats.sharesOutstanding can report only one share class
        # for dual-class stocks (GOOGL, META, BRK, V — off by 15-108%)
        mktcap = _get_dict_val(summ, "marketCap") or 0
        shares = mktcap / price if price > 0 and mktcap > 0 else 0

        return FinancialData(
            ticker=ticker,
            company_name=sp.get("company_name", ""),
            sector=sp.get("sector", ""),
            sub_industry=sp.get("sub_industry", ""),

            current_price=price,
            market_cap=_get_dict_val(summ, "marketCap") or 0,
            beta=_get_dict_val(summ, "beta"),

            trailing_pe=_get_dict_val(summ, "trailingPE"),
            forward_pe=_get_dict_val(summ, "forwardPE"),
            price_to_book=_get_dict_val(kstats, "priceToBook"),
            enterprise_value=_get_dict_val(kstats, "enterpriseValue"),
            enterprise_to_ebitda=_get_dict_val(kstats, "enterpriseToEbitda"),
            price_to_sales=_get_dict_val(summ, "priceToSalesTrailing12Months"),
            dividend_yield=_get_dict_val(summ, "dividendYield"),
            shares_outstanding=shares,

            revenue=_col_list(inc, "TotalRevenue"),
            gross_profit=_col_list(inc, "GrossProfit"),
            operating_income=_col_list(inc, "OperatingIncome"),
            net_income=_col_list(inc, "NetIncome"),
            diluted_eps=_col_list(inc, "DilutedEPS"),
            ebitda=_col_list(inc, "EBITDA"),
            interest_expense=_col_list(inc, "InterestExpense"),
            tax_provision=_col_list(inc, "TaxProvision"),
            pretax_income=_col_list(inc, "PretaxIncome"),

            total_assets=_col_list(bal, "TotalAssets", 2),
            current_assets=_col_list(bal, "CurrentAssets", 2),
            current_liabilities=_col_list(bal, "CurrentLiabilities", 2),
            total_debt=_col_list(bal, "TotalDebt", 2),
            cash_and_equivalents=_col_list(bal, "CashAndCashEquivalents", 2),
            stockholders_equity=_col_list(bal, "StockholdersEquity", 2),
            retained_earnings=_col_list(bal, "RetainedEarnings", 2),
            ordinary_shares_number=_col_list(bal, "OrdinarySharesNumber", 2),

            free_cash_flow=_col_list(cf, "FreeCashFlow"),
            operating_cash_flow=_col_list(cf, "OperatingCashFlow"),
            capital_expenditure=_col_list(cf, "CapitalExpenditure"),

            analyst_target=_get_dict_val(fdata, "targetMeanPrice"),
            fifty_two_week_high=_get_dict_val(summ, "fiftyTwoWeekHigh"),
        )

    @staticmethod
    def _filter_ticker_df(
        df: pd.DataFrame, ticker: str, annual_only: bool = True
    ) -> pd.DataFrame:
        """Extract rows for a specific ticker, sorted most-recent first."""
        if df is None or isinstance(df, str) or df.empty:
            return pd.DataFrame()

        try:
            filtered = df

            # Filter by ticker — handle various index/column arrangements
            if isinstance(df.index, pd.MultiIndex):
                level_values = df.index.get_level_values(0)
                if ticker in level_values:
                    filtered = df.loc[ticker]
                else:
                    return pd.DataFrame()
            elif df.index.name == "symbol" or (hasattr(df.index, 'names') and 'symbol' in (df.index.names or [])):
                # Single Index named 'symbol'
                filtered = df[df.index == ticker]
            elif "symbol" in df.columns:
                filtered = df[df["symbol"] == ticker]

            # Filter for annual data if requested
            if annual_only and "periodType" in filtered.columns:
                filtered = filtered[filtered["periodType"] == "12M"]

            # Sort by date descending (most recent first)
            if "asOfDate" in filtered.columns:
                filtered = filtered.sort_values("asOfDate", ascending=False)

            return filtered.reset_index(drop=True)
        except Exception as e:
            logger.debug(f"Failed to filter DataFrame for {ticker}: {e}")
            return pd.DataFrame()
