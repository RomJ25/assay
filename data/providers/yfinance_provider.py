"""yfinance fallback provider — batch prices + individual financial statements."""

from __future__ import annotations

import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

from data.providers.base import DataProvider, FinancialData

logger = logging.getLogger(__name__)


def _safe(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def _extract_col(df, col: str, n: int = 4) -> list[float | None]:
    """Extract up to n values from a yfinance DataFrame (most recent first).

    yfinance returns DataFrames with dates as columns, metrics as index.
    """
    if df is None or df.empty or col not in df.index:
        return [None] * n
    row = df.loc[col]
    # Columns are dates, sorted newest-first by yfinance
    vals = [_safe(row.iloc[i]) if i < len(row) else None for i in range(n)]
    return vals


class YFinanceProvider(DataProvider):
    """Fallback provider using yfinance.

    Primary use: batch price downloads via yf.download().
    Secondary use: individual ticker data with full financial statements.
    """

    def fetch_prices(self, tickers: list[str]) -> dict[str, float]:
        """Batch download latest prices for all tickers."""
        logger.info(f"Fetching prices for {len(tickers)} tickers via yfinance...")
        try:
            df = yf.download(tickers, period="1d", threads=True, progress=False)
            if df.empty:
                logger.warning("yfinance returned empty price data")
                return {}

            prices = {}
            if "Close" in df.columns:
                if hasattr(df["Close"], "columns"):
                    for ticker in df["Close"].columns:
                        val = df["Close"][ticker].dropna()
                        if not val.empty:
                            prices[ticker] = float(val.iloc[-1])
                else:
                    if not df["Close"].dropna().empty:
                        prices[tickers[0]] = float(df["Close"].dropna().iloc[-1])

            logger.info(f"Got prices for {len(prices)}/{len(tickers)} tickers")
            return prices
        except Exception as e:
            logger.error(f"yfinance price download failed: {e}")
            return {}

    def fetch_financial_data(
        self, tickers: list[str], sp500_info: dict[str, dict]
    ) -> dict[str, FinancialData]:
        """Fetch individual ticker data with concurrent threads."""
        results = {}
        max_workers = min(8, len(tickers)) if tickers else 1

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._fetch_single, t, sp500_info): t
                for t in tickers
            }
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    fd = future.result(timeout=15)
                    if fd is not None:
                        results[ticker] = fd
                except Exception as e:
                    logger.warning(f"yfinance fallback failed for {ticker}: {e}")

        return results

    def _fetch_single(self, ticker: str, sp500_info: dict[str, dict]) -> FinancialData | None:
        """Fetch full data for one ticker via yfinance."""
        t = yf.Ticker(ticker)
        info = t.info
        if not info or not info.get("currentPrice"):
            return None

        sp = sp500_info.get(ticker, {})

        # Financial statements (yfinance uses dates as columns, metrics as rows)
        try:
            inc = t.financials  # annual income statement
        except Exception:
            inc = None
        try:
            bal = t.balance_sheet
        except Exception:
            bal = None
        try:
            cf = t.cashflow
        except Exception:
            cf = None

        return FinancialData(
            ticker=ticker,
            company_name=sp.get("company_name", info.get("shortName", "")),
            sector=sp.get("sector", info.get("sector", "")),
            sub_industry=sp.get("sub_industry", ""),
            current_price=info.get("currentPrice", 0),
            market_cap=info.get("marketCap", 0),
            beta=info.get("beta"),
            trailing_pe=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            price_to_book=info.get("priceToBook"),
            enterprise_value=info.get("enterpriseValue"),
            enterprise_to_ebitda=info.get("enterpriseToEbitda"),
            price_to_sales=info.get("priceToSalesTrailing12Months"),
            dividend_yield=info.get("dividendYield"),
            shares_outstanding=(
                info.get("marketCap", 0) / info.get("currentPrice", 1)
                if info.get("currentPrice") and info.get("marketCap")
                else 0
            ),
            # Income statement
            revenue=_extract_col(inc, "Total Revenue"),
            gross_profit=_extract_col(inc, "Gross Profit"),
            operating_income=_extract_col(inc, "Operating Income"),
            net_income=_extract_col(inc, "Net Income"),
            diluted_eps=_extract_col(inc, "Diluted EPS"),
            ebitda=_extract_col(inc, "EBITDA"),
            interest_expense=_extract_col(inc, "Interest Expense"),
            tax_provision=_extract_col(inc, "Tax Provision"),
            pretax_income=_extract_col(inc, "Pretax Income"),
            # Balance sheet
            total_assets=_extract_col(bal, "Total Assets", 2),
            current_assets=_extract_col(bal, "Current Assets", 2),
            current_liabilities=_extract_col(bal, "Current Liabilities", 2),
            total_debt=_extract_col(bal, "Total Debt", 2),
            cash_and_equivalents=_extract_col(bal, "Cash And Cash Equivalents", 2),
            stockholders_equity=_extract_col(bal, "Stockholders Equity", 2),
            retained_earnings=_extract_col(bal, "Retained Earnings", 2),
            ordinary_shares_number=_extract_col(bal, "Ordinary Shares Number", 2),
            # Cash flow
            free_cash_flow=_extract_col(cf, "Free Cash Flow"),
            operating_cash_flow=_extract_col(cf, "Operating Cash Flow"),
            capital_expenditure=_extract_col(cf, "Capital Expenditure"),

            analyst_target=info.get("targetMeanPrice"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
        )
