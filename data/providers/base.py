"""FinancialData dataclass and abstract DataProvider interface.

FinancialData is the single interface between the data layer and all models.
All providers normalize their output into this structure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FinancialData:
    """All data needed by all 8 models (3 value + 5 quality/growth).

    Lists are ordered [latest_year, year-1, year-2, year-3].
    None values indicate missing data — models handle gracefully.
    """

    ticker: str
    company_name: str
    sector: str  # GICS Sector from Wikipedia
    sub_industry: str  # GICS Sub-Industry from Wikipedia (for DCF routing)

    # ── Price data (from summary_detail / financial_data) ──────────────
    current_price: float
    market_cap: float
    beta: float | None = None

    # ── Valuation multiples (from summary_detail / key_stats) ─────────
    trailing_pe: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    enterprise_value: float | None = None
    enterprise_to_ebitda: float | None = None
    price_to_sales: float | None = None
    dividend_yield: float | None = None
    shares_outstanding: float = 0.0

    # ── Income statement — [latest, year-1, year-2, year-3] ───────────
    revenue: list[float | None] = field(default_factory=lambda: [None] * 4)
    gross_profit: list[float | None] = field(default_factory=lambda: [None] * 4)
    operating_income: list[float | None] = field(default_factory=lambda: [None] * 4)
    net_income: list[float | None] = field(default_factory=lambda: [None] * 4)
    diluted_eps: list[float | None] = field(default_factory=lambda: [None] * 4)
    ebitda: list[float | None] = field(default_factory=lambda: [None] * 4)
    interest_expense: list[float | None] = field(default_factory=lambda: [None] * 4)
    tax_provision: list[float | None] = field(default_factory=lambda: [None] * 4)
    pretax_income: list[float | None] = field(default_factory=lambda: [None] * 4)

    # ── Balance sheet — [latest, year-1] ──────────────────────────────
    total_assets: list[float | None] = field(default_factory=lambda: [None] * 2)
    current_assets: list[float | None] = field(default_factory=lambda: [None] * 2)
    current_liabilities: list[float | None] = field(default_factory=lambda: [None] * 2)
    total_debt: list[float | None] = field(default_factory=lambda: [None] * 2)
    cash_and_equivalents: list[float | None] = field(default_factory=lambda: [None] * 2)
    stockholders_equity: list[float | None] = field(default_factory=lambda: [None] * 2)
    retained_earnings: list[float | None] = field(default_factory=lambda: [None] * 2)
    ordinary_shares_number: list[float | None] = field(default_factory=lambda: [None] * 2)

    # ── Cash flow — [latest, year-1, year-2, year-3] ──────────────────
    free_cash_flow: list[float | None] = field(default_factory=lambda: [None] * 4)
    operating_cash_flow: list[float | None] = field(default_factory=lambda: [None] * 4)
    capital_expenditure: list[float | None] = field(default_factory=lambda: [None] * 4)

    # ── Context data (for display, not scoring) ────────────────────────
    analyst_target: float | None = None  # targetMeanPrice from Yahoo
    fifty_two_week_high: float | None = None  # 52-week high price
    current_quarter_estimate: float | None = None
    momentum_12m: float | None = None  # 12-1 month price return (decimal)

    def __post_init__(self):
        """Fill gaps where derived values can be computed from available data."""
        # Fill missing EPS from NI / shares (yahooquery sometimes omits DilutedEPS)
        if self.shares_outstanding > 0:
            for i in range(len(self.diluted_eps)):
                if self.diluted_eps[i] is None and i < len(self.net_income) and self.net_income[i] is not None:
                    self.diluted_eps[i] = self.net_income[i] / self.shares_outstanding

    # ── Helpers ───────────────────────────────────────────────────────

    def get(self, field_name: str, year: int = 0) -> float | None:
        """Safely get a value from a list field by year index.

        year=0 is latest, year=1 is prior year, etc.
        """
        val = getattr(self, field_name, None)
        if val is None:
            return None
        if isinstance(val, list):
            if year < len(val):
                return val[year]
            return None
        return val

    @property
    def effective_tax_rate(self) -> float | None:
        """Calculate effective tax rate from TaxProvision / PretaxIncome."""
        tax = self.get("tax_provision", 0)
        pretax = self.get("pretax_income", 0)
        if tax is None or pretax is None or pretax == 0:
            return None
        rate = tax / pretax
        if rate < 0 or rate > 0.5:  # sanity check
            return None
        return rate

    @property
    def total_liabilities(self) -> float | None:
        """TotalAssets - StockholdersEquity."""
        assets = self.get("total_assets", 0)
        equity = self.get("stockholders_equity", 0)
        if assets is None or equity is None:
            return None
        return assets - equity

    @property
    def book_value_per_share(self) -> float | None:
        """StockholdersEquity / SharesOutstanding."""
        equity = self.get("stockholders_equity", 0)
        if equity is None or self.shares_outstanding <= 0:
            return None
        return equity / self.shares_outstanding

    @property
    def has_minimum_data(self) -> bool:
        """Check if we have enough data to run at least 2 models."""
        return (
            self.current_price > 0
            and self.revenue[0] is not None
            and self.revenue[0] > 0
            and self.net_income[0] is not None
        )


class DataProvider(ABC):
    """Abstract base for data providers (yahooquery, yfinance, etc.)."""

    @abstractmethod
    def fetch_financial_data(
        self, tickers: list[str], sp500_info: dict[str, dict]
    ) -> dict[str, FinancialData]:
        """Fetch and normalize financial data for a list of tickers.

        Args:
            tickers: List of ticker symbols.
            sp500_info: Dict mapping ticker → {company_name, sector, sub_industry}.

        Returns:
            Dict mapping ticker → FinancialData. Missing tickers omitted.
        """
        ...

    @abstractmethod
    def fetch_prices(self, tickers: list[str]) -> dict[str, float]:
        """Fetch current prices for all tickers.

        Returns:
            Dict mapping ticker → current price.
        """
        ...
