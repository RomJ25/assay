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
    """
    logger.info("Fetching TA-125 list from Wikipedia...")

    try:
        resp = requests.get(_TASE_WIKIPEDIA_URL, headers={"User-Agent": "Assay/1.0"}, timeout=15)
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))

        # Find the constituents table (has 'Ticker' or 'Symbol' column)
        df = None
        for table in tables:
            cols_lower = [c.lower() for c in table.columns]
            if any("ticker" in c or "symbol" in c for c in cols_lower):
                df = table
                break

        if df is None:
            # Fallback: use the largest table
            df = max(tables, key=len)
            logger.warning("Could not find ticker column, using largest table")

    except Exception as e:
        logger.warning(f"Wikipedia fetch failed: {e}. Using hardcoded TA-35 list.")
        return _fetch_tase_fallback()

    # Try to extract tickers and company names
    ticker_col = None
    name_col = None
    sector_col = None

    for col in df.columns:
        cl = str(col).lower()
        if "ticker" in cl or "symbol" in cl:
            ticker_col = col
        elif "company" in cl or "name" in cl or "security" in cl:
            name_col = col
        elif "sector" in cl or "industry" in cl:
            sector_col = col

    if ticker_col is None:
        logger.warning("No ticker column found. Using fallback.")
        return _fetch_tase_fallback()

    tickers = []
    info = {}

    for _, row in df.iterrows():
        raw_ticker = str(row[ticker_col]).strip()
        if not raw_ticker or raw_ticker == "nan":
            continue

        # Add .TA suffix if not present
        ticker = raw_ticker if raw_ticker.endswith(".TA") else f"{raw_ticker}.TA"

        company = str(row[name_col]).strip() if name_col else ticker.replace(".TA", "")
        sector = str(row[sector_col]).strip() if sector_col else "Unknown"

        tickers.append(ticker)
        info[ticker] = {
            "company_name": company,
            "sector": sector if sector != "nan" else "Unknown",
            "sub_industry": "Unknown",
        }

    logger.info(f"Loaded {len(tickers)} TASE constituents")
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
}


def get_universe(name: str, custom_tickers: list[str] | None = None) -> Universe:
    """Get a universe by name.

    Supports:
        - "sp500" — S&P 500
        - "tase" — Tel Aviv Stock Exchange TA-125
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
