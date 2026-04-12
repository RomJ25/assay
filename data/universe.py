"""Multi-universe support — screen stocks from any market.

Provides a pluggable universe registry so the screener can work with
S&P 500, Russell 1000, TASE (Israel), or custom ticker lists.

Usage:
    universe = get_universe("sp500")     # default
    universe = get_universe("tase")      # Israeli stocks
    universe = get_universe("sp500+tase") # combined
    tickers, info = universe.fetch()
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd
import requests

logger = logging.getLogger(__name__)


@dataclass
class Universe:
    """A screenable stock universe."""
    name: str
    description: str
    currency: str
    fetch: Callable[[], tuple[list[str], dict[str, dict]]]
    historical: Callable | None = None  # point-in-time membership for backtest


# ── S&P 500 ────────────────────────────────────────────────────────────


def _fetch_sp500() -> tuple[list[str], dict[str, dict]]:
    """Fetch S&P 500 from existing sp500.py module."""
    from data.sp500 import fetch_sp500_list, sp500_info_dict
    df = fetch_sp500_list()
    info = sp500_info_dict(df)
    tickers = list(info.keys())
    return tickers, info


# ── TASE (Tel Aviv Stock Exchange) ─────────────────────────────────────


_TASE_WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/TA-125_Index"


def _fetch_tase() -> tuple[list[str], dict[str, dict]]:
    """Fetch TA-125 constituents from Wikipedia.

    Returns tickers with .TA suffix for yfinance compatibility.
    Wikipedia TA-125 table has columns: Name, Symbol, Market Cap, Weight, Sector, Comments
    """
    logger.info("Fetching TA-125 list from Wikipedia...")

    try:
        resp = requests.get(_TASE_WIKIPEDIA_URL, headers={"User-Agent": "Assay/1.0"}, timeout=15)
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))

        # Table 1 has the constituents (126 rows with Name, Symbol, Market Cap, Weight, Sector)
        df = None
        for table in tables:
            if len(table) > 50 and any("symbol" in str(c).lower() for c in table.columns):
                df = table
                break

        if df is None:
            logger.warning("Could not find TA-125 table. Using fallback.")
            return _fetch_tase_fallback()

    except Exception as e:
        logger.warning(f"Wikipedia fetch failed: {e}. Using fallback.")
        return _fetch_tase_fallback()

    tickers = []
    info = {}

    for _, row in df.iterrows():
        raw_symbol = str(row.get("Symbol", "")).strip()
        name = str(row.get("Name", "")).strip()
        sector = str(row.get("Sector", "Unknown")).strip()

        if not raw_symbol or raw_symbol == "nan":
            continue

        # Skip dual-listed London tickers (DEDR.L, ISRA.L, RATI.L — don't work as .L.TA)
        if ".L" in raw_symbol:
            logger.debug(f"Skipping London dual-listing: {raw_symbol}")
            continue

        # Add .TA suffix for yfinance
        ticker = f"{raw_symbol}.TA"

        tickers.append(ticker)
        info[ticker] = {
            "company_name": name if name != "nan" else raw_symbol,
            "sector": sector if sector != "nan" else "Unknown",
            "sub_industry": "Unknown",
        }

    logger.info(f"Loaded {len(tickers)} TASE constituents (skipped London dual-listings)")
    return tickers, info


def _fetch_tase_fallback() -> tuple[list[str], dict[str, dict]]:
    """Hardcoded TA-35 major stocks as fallback."""
    stocks = [
        ("TEVA.TA", "Teva Pharmaceutical", "Healthcare"),
        ("NICE.TA", "NICE Ltd", "Technology"),
        ("ICL.TA", "ICL Group", "Basic Materials"),
        ("LUMI.TA", "Bank Leumi", "Financial Services"),
        ("POLI.TA", "Bank Hapoalim", "Financial Services"),
        ("DSCT.TA", "Discount Bank", "Financial Services"),
        ("BEZQ.TA", "Bezeq", "Communication Services"),
        ("CEL.TA", "Cellcom", "Communication Services"),
        ("ESLT.TA", "Elbit Systems", "Industrials"),
        ("ENLT.TA", "Energix", "Utilities"),
        ("AZRG.TA", "Azrieli Group", "Real Estate"),
        ("MGDL.TA", "Migdal Insurance", "Financial Services"),
        ("MZTF.TA", "Mizrahi Tefahot Bank", "Financial Services"),
        ("ORA.TA", "Ormat Technologies", "Utilities"),
        ("PHOE.TA", "Phoenix Holdings", "Financial Services"),
        ("ILCO.TA", "Israel Corp", "Industrials"),
        ("AMOT.TA", "Amot Investments", "Real Estate"),
        ("ELAL.TA", "El Al Airlines", "Industrials"),
        ("FTAL.TA", "Fattal Holdings", "Consumer Discretionary"),
        ("SHPG.TA", "Shapir Engineering", "Industrials"),
    ]
    tickers = [t for t, _, _ in stocks]
    info = {t: {"company_name": n, "sector": s, "sub_industry": "Unknown"} for t, n, s in stocks}
    logger.info(f"Using fallback TASE list: {len(tickers)} stocks")
    return tickers, info


# ── TASE All (complete TASE listing via Twelve Data) ───────────────────


_TWELVE_DATA_TASE_URL = "https://api.twelvedata.com/stocks?exchange=XTAE"


def _fetch_tase_all() -> tuple[list[str], dict[str, dict]]:
    """Fetch ALL TASE-listed stocks from Twelve Data (free API, no key).

    Returns ~500 stocks (vs ~125 for TA-125 index only).
    Includes small/mid caps available on Interactive Brokers Israel.
    Stocks without sufficient data will be filtered by Assay's quality checks.
    """
    logger.info("Fetching complete TASE listing from Twelve Data...")

    try:
        r = requests.get(_TWELVE_DATA_TASE_URL, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        logger.warning(f"Twelve Data fetch failed: {e}. Falling back to TA-125.")
        return _fetch_tase()

    tickers = []
    info = {}

    for stock in data:
        symbol = stock.get("symbol", "").strip()
        name = stock.get("name", "").strip()
        stock_type = stock.get("type", "")

        # Only common stocks and REITs (skip bond series, LPs)
        if stock_type not in ("Common Stock", "REIT"):
            continue

        # Skip bond series (symbols like TEVA.B1, ICL.B13)
        if "." in symbol:
            continue

        # Skip pure numeric tickers (usually bonds/derivatives)
        if symbol.isdigit():
            continue

        if not symbol:
            continue

        ticker = f"{symbol}.TA"
        tickers.append(ticker)
        info[ticker] = {
            "company_name": name if name else symbol,
            "sector": "Unknown",  # Twelve Data doesn't provide sector
            "sub_industry": "Unknown",
        }

    # Enrich with TA-125 sector data where available
    try:
        ta125_tickers, ta125_info = _fetch_tase()
        for t, i in ta125_info.items():
            if t in info and i.get("sector", "Unknown") != "Unknown":
                info[t]["sector"] = i["sector"]
                info[t]["company_name"] = i["company_name"]
    except Exception:
        pass  # TA-125 enrichment is optional

    logger.info(f"Loaded {len(tickers)} TASE stocks (all Interactive Brokers Israel)")
    return tickers, info


# ── US All (all NYSE + NASDAQ stocks via Twelve Data) ────────────────


_TWELVE_DATA_US_EXCHANGES = ["NYSE", "NASDAQ"]
_TWELVE_DATA_US_TYPES = ["Common Stock", "American Depositary Receipt", "REIT"]


def _fetch_us_all() -> tuple[list[str], dict[str, dict]]:
    """Fetch ALL US-listed stocks from Twelve Data (free API, no key).

    Covers NYSE + NASDAQ (~6,200+ stocks). Includes everything available
    on Interactive Brokers US: common stocks, ADRs (BABA, TSM, NVO), REITs.
    SPACs and shells without financials will be filtered by data quality checks.
    REITs are included in the fetch but excluded by default in scoring
    (pass --include-financials to keep them).
    """
    logger.info("Fetching complete US stock listing from Twelve Data...")

    tickers = []
    info = {}
    seen = set()

    for exchange in _TWELVE_DATA_US_EXCHANGES:
        for stock_type in _TWELVE_DATA_US_TYPES:
            try:
                url = f"https://api.twelvedata.com/stocks?exchange={exchange}&type={stock_type}"
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                data = r.json().get("data", [])
            except Exception as e:
                logger.warning(f"Twelve Data fetch failed for {exchange}/{stock_type}: {e}")
                continue

            added = 0
            for stock in data:
                symbol = stock.get("symbol", "").strip()
                name = stock.get("name", "").strip()

                if not symbol:
                    continue

                # Handle dot-symbols: warrants, units, rights, preferreds → skip
                # Share classes (BRK.B, BF.A) → convert dot to hyphen for Yahoo
                if "." in symbol:
                    suffix = symbol.split(".")[-1]
                    if suffix in ("WT", "WTA", "UN", "RI", "RT") or ".PR." in symbol:
                        continue
                    symbol = symbol.replace(".", "-")

                if symbol in seen:
                    continue
                seen.add(symbol)

                tickers.append(symbol)
                info[symbol] = {
                    "company_name": name if name else symbol,
                    "sector": "Unknown",
                    "sub_industry": "Unknown",
                }
                added += 1

            logger.info(f"  {exchange} {stock_type}: {len(data)} raw → {added} added")

    # Enrich S&P 500 members with sector data
    try:
        sp500_tickers, sp500_info = _fetch_sp500()
        for t, i in sp500_info.items():
            if t in info:
                info[t]["sector"] = i.get("sector", "Unknown")
                info[t]["sub_industry"] = i.get("sub_industry", "Unknown")
                info[t]["company_name"] = i.get("company_name", info[t]["company_name"])
    except Exception:
        pass  # S&P 500 enrichment is optional

    logger.info(f"Loaded {len(tickers)} US stocks (NYSE + NASDAQ, all Interactive Brokers US)")
    return tickers, info


# ── Custom Ticker List ─────────────────────────────────────────────────


def _make_custom_fetcher(ticker_list: list[str]) -> Callable:
    """Create a fetcher for a user-provided ticker list."""
    def fetch():
        info = {}
        for t in ticker_list:
            info[t] = {
                "company_name": t,
                "sector": "Unknown",
                "sub_industry": "Unknown",
            }
        return ticker_list, info
    return fetch


# ── Combined Universe ──────────────────────────────────────────────────


def _make_combined_fetcher(*universes: Universe) -> Callable:
    """Create a fetcher that merges multiple universes."""
    def fetch():
        all_tickers = []
        all_info = {}
        for u in universes:
            tickers, info = u.fetch()
            all_tickers.extend(tickers)
            all_info.update(info)
        # Deduplicate
        seen = set()
        unique = []
        for t in all_tickers:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique, all_info
    return fetch


# ── Universe Registry ──────────────────────────────────────────────────


def _sp500_historical():
    """Import lazily to avoid circular imports."""
    from data.sp500_historical import get_sp500_at_date
    return get_sp500_at_date


UNIVERSES: dict[str, Universe] = {
    "sp500": Universe(
        name="sp500",
        description="S&P 500 (USA)",
        currency="USD",
        fetch=_fetch_sp500,
        historical=None,  # set lazily
    ),
    "tase": Universe(
        name="tase",
        description="TASE TA-125 (Israel)",
        currency="ILS",
        fetch=_fetch_tase,
    ),
    "tase_all": Universe(
        name="tase_all",
        description="TASE All Stocks (Israel, ~500)",
        currency="ILS",
        fetch=_fetch_tase_all,
    ),
    "us_all": Universe(
        name="us_all",
        description="All US Stocks (NYSE + NASDAQ, ~6,200)",
        currency="USD",
        fetch=_fetch_us_all,
    ),
}


def get_universe(name: str, custom_tickers: list[str] | None = None) -> Universe:
    """Get a universe by name.

    Supports:
        - "sp500" — S&P 500
        - "us_all" — all NYSE + NASDAQ stocks (~6,200, incl. ADRs + REITs)
        - "tase" — Tel Aviv Stock Exchange TA-125
        - "tase_all" — all TASE stocks (~500)
        - "sp500+tase" — combined
        - "custom" — requires custom_tickers list
    """
    if name == "custom" and custom_tickers:
        return Universe(
            name="custom",
            description=f"Custom ({len(custom_tickers)} tickers)",
            currency="Mixed",
            fetch=_make_custom_fetcher(custom_tickers),
        )

    # Handle combined universes: "sp500+tase"
    if "+" in name:
        parts = name.split("+")
        universes = []
        for p in parts:
            p = p.strip()
            if p not in UNIVERSES:
                raise ValueError(f"Unknown universe: {p}. Available: {list(UNIVERSES.keys())}")
            universes.append(UNIVERSES[p])

        combined_desc = " + ".join(u.description for u in universes)
        return Universe(
            name=name,
            description=combined_desc,
            currency="Mixed",
            fetch=_make_combined_fetcher(*universes),
        )

    if name not in UNIVERSES:
        raise ValueError(f"Unknown universe: {name}. Available: {list(UNIVERSES.keys())}")

    universe = UNIVERSES[name]

    # Lazily set historical for sp500
    if name == "sp500" and universe.historical is None:
        universe.historical = _sp500_historical()

    return universe
