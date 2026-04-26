"""Fetch deep historical financials from SEC EDGAR (free, 15+ years).

Yahoo Finance only provides ~4 years of annual statements. SEC EDGAR
provides XBRL data from all 10-K/10-Q filings, going back to 2008+
for most S&P 500 companies.

The data is converted to yahooquery-compatible format so the existing
snapshot_builder.py works without changes.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date as dt
from datetime import date

import requests

logger = logging.getLogger(__name__)

_SEC_HEADERS = {"User-Agent": "Assay Stock Screener research@assay.dev"}
_SEC_RATE_LIMIT = 0.12  # SEC allows 10 req/sec; we use ~8/sec to be safe

# Map yahooquery field names → SEC EDGAR XBRL concept names (ordered by priority)
_INCOME_CONCEPTS = {
    "TotalRevenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ],
    "GrossProfit": ["GrossProfit"],
    "_CostOfRevenue": [  # Internal: used to compute GrossProfit when not directly available
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfGoodsSold",
    ],
    "OperatingIncome": ["OperatingIncomeLoss"],
    "NetIncome": ["NetIncomeLoss"],
    "DilutedEPS": ["EarningsPerShareDiluted"],
    "EBITDA": [],  # Not directly in XBRL; computed if possible
    "InterestExpense": ["InterestExpense", "InterestExpenseDebt"],
    "TaxProvision": ["IncomeTaxExpenseBenefit"],
    "PretaxIncome": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ],
}

_BALANCE_CONCEPTS = {
    "TotalAssets": ["Assets"],
    "CurrentAssets": ["AssetsCurrent"],
    "CurrentLiabilities": ["LiabilitiesCurrent"],
    "TotalDebt": [
        "LongTermDebtAndCapitalLeaseObligations",
        "LongTermDebt",
        "LongTermDebtNoncurrent",
    ],
    "CashAndCashEquivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
    ],
    "StockholdersEquity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "RetainedEarnings": ["RetainedEarningsAccumulatedDeficit"],
    "OrdinarySharesNumber": [
        "CommonStockSharesOutstanding",
        "EntityCommonStockSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
}

_CASHFLOW_CONCEPTS = {
    "OperatingCashFlow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "NetCashProvidedByOperatingActivities",
    ],
    "CapitalExpenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "FreeCashFlow": [],  # Computed: operating - capex
}


def fetch_cik_mapping() -> dict[str, str]:
    """Fetch ticker → CIK mapping from SEC.

    Returns: {ticker: CIK_padded_to_10_digits}
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=_SEC_HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()

    mapping = {}
    for entry in data.values():
        ticker = entry.get("ticker", "").upper()
        cik = str(entry.get("cik_str", "")).zfill(10)
        if ticker and cik:
            mapping[ticker] = cik

    logger.info(f"Loaded {len(mapping)} ticker→CIK mappings from SEC")
    return mapping


def fetch_edgar_financials(
    tickers: list[str],
    cik_map: dict[str, str],
    max_workers: int = 8,
) -> dict[str, dict]:
    """Fetch historical financials from SEC EDGAR for multiple tickers.

    Returns data in yahooquery-compatible format:
    {ticker: {"income": [...], "balance": [...], "cashflow": [...]}}
    """
    results = {}
    to_fetch = [(t, cik_map[t]) for t in tickers if t in cik_map]
    skipped = len(tickers) - len(to_fetch)
    if skipped:
        logger.info(f"Skipping {skipped} tickers without CIK mapping")

    logger.info(f"Fetching EDGAR financials for {len(to_fetch)} tickers...")

    # Use threads but respect SEC rate limit
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, (ticker, cik) in enumerate(to_fetch):
            future = executor.submit(_fetch_single_edgar, ticker, cik)
            futures[future] = ticker
            # Stagger submissions to respect rate limit
            if i > 0 and i % max_workers == 0:
                time.sleep(_SEC_RATE_LIMIT * max_workers)

        done = 0
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                data = future.result()
                if data is not None:
                    results[ticker] = data
            except Exception as e:
                logger.debug(f"EDGAR fetch failed for {ticker}: {e}")
            done += 1
            if done % 100 == 0:
                logger.info(f"  EDGAR: {done}/{len(to_fetch)} fetched ({len(results)} success)")

    logger.info(f"EDGAR: fetched {len(results)}/{len(to_fetch)} tickers")
    return results


def _fetch_single_edgar(ticker: str, cik: str) -> dict | None:
    """Fetch and convert EDGAR company facts for one ticker."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        r = requests.get(url, headers=_SEC_HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception:
        return None

    gaap = data.get("facts", {}).get("us-gaap", {})
    if not gaap:
        return None

    income_rows = _build_statement_rows(gaap, _INCOME_CONCEPTS, "income")
    balance_rows = _build_statement_rows(gaap, _BALANCE_CONCEPTS, "balance")
    cashflow_rows = _build_statement_rows(gaap, _CASHFLOW_CONCEPTS, "cashflow")

    # Compute derived fields
    _compute_gross_profit(income_rows)
    _compute_free_cash_flow(cashflow_rows)

    # Remove internal fields
    for row in income_rows:
        row.pop("_CostOfRevenue", None)

    if not income_rows:
        return None

    return {
        "income": income_rows,
        "balance": balance_rows,
        "cashflow": cashflow_rows,
    }


def _build_statement_rows(
    gaap: dict,
    concept_map: dict[str, list[str]],
    statement_type: str,
) -> list[dict]:
    """Build yahooquery-compatible rows from EDGAR XBRL data.

    Groups facts by fiscal year end date and returns one row per year.
    Each row also carries `filed_date` — the earliest filing date observed
    for that fiscal-year-end across all concepts. This lets backtests use
    the true point-in-time when statements became publicly available
    rather than a period-end-plus-lag proxy.
    """
    # Collect all annual facts by date
    date_facts: dict[str, dict] = {}
    # Track earliest filed-date per end_date (first time this period's data
    # was publicly available — conservative point-in-time choice).
    date_filed: dict[str, str] = {}

    for field_name, xbrl_concepts in concept_map.items():
        for concept in xbrl_concepts:
            if concept not in gaap:
                continue

            # Try USD first, then specialized units
            entries = gaap[concept].get("units", {}).get("USD", [])
            if not entries:
                entries = gaap[concept].get("units", {}).get("USD/shares", [])
            if not entries:
                entries = gaap[concept].get("units", {}).get("shares", [])

            # Filter to annual 10-K filings, full fiscal year only.
            # fp=FY is unreliable — quarterly figures are sometimes tagged FY.
            # Use actual period length: end - start >= 300 days.
            for entry in entries:
                if entry.get("form") != "10-K":
                    continue

                end_date = entry.get("end", "")
                start_date = entry.get("start", "")
                if not end_date:
                    continue

                # Verify this is actually a full-year figure
                if start_date:
                    try:
                        days = (dt.fromisoformat(end_date) - dt.fromisoformat(start_date)).days
                        if days < 300:  # quarterly or semi-annual, not full year
                            continue
                    except ValueError:
                        continue

                if end_date not in date_facts:
                    date_facts[end_date] = {}

                # Higher-priority concepts win; lower-priority fills gaps
                if field_name not in date_facts[end_date]:
                    date_facts[end_date][field_name] = entry.get("val")

                # Track earliest filed date observed for this fiscal year-end
                filed = entry.get("filed")
                if filed:
                    prior = date_filed.get(end_date)
                    if prior is None or filed < prior:
                        date_filed[end_date] = filed

    # Convert to yahooquery-compatible row format
    rows = []
    for end_date in sorted(date_facts.keys()):
        facts = date_facts[end_date]
        if not facts:
            continue

        row = {
            "asOfDate": f"{end_date}T00:00:00",
            "periodType": "12M",
        }
        if end_date in date_filed:
            row["filed_date"] = date_filed[end_date]
        row.update(facts)
        rows.append(row)

    return rows


def _compute_gross_profit(income_rows: list[dict]) -> None:
    """Add GrossProfit = TotalRevenue - CostOfRevenue when not directly available."""
    for row in income_rows:
        if row.get("GrossProfit") is not None:
            continue
        rev = row.get("TotalRevenue")
        cogs = row.get("_CostOfRevenue")
        if rev is not None and cogs is not None:
            row["GrossProfit"] = rev - cogs


def _compute_free_cash_flow(cashflow_rows: list[dict]) -> None:
    """Add FreeCashFlow = OperatingCashFlow - CapitalExpenditure to each row."""
    for row in cashflow_rows:
        ocf = row.get("OperatingCashFlow")
        capex = row.get("CapitalExpenditure")
        if ocf is not None and capex is not None:
            # CapEx from EDGAR is positive (payment), FCF = OCF - CapEx
            row["FreeCashFlow"] = ocf - abs(capex)
