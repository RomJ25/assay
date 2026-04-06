"""Fetch and cache the S&P 500 constituent list from Wikipedia."""

from __future__ import annotations

import io
import logging

import pandas as pd
import requests

from config import SP500_WIKIPEDIA_URL

logger = logging.getLogger(__name__)


def fetch_sp500_list() -> pd.DataFrame:
    """Fetch S&P 500 constituents from Wikipedia.

    Returns DataFrame with columns: ticker, company_name, sector, sub_industry.
    Tickers have dots replaced with hyphens for Yahoo Finance compatibility.
    """
    logger.info("Fetching S&P 500 list from Wikipedia...")
    resp = requests.get(SP500_WIKIPEDIA_URL, headers={"User-Agent": "SP500Screener/1.0"}, timeout=15)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text))
    if not tables:
        raise ValueError("No tables found on Wikipedia S&P 500 page")
    df = tables[0]  # First table is current constituents

    # Validate expected columns
    expected_cols = {"Symbol", "Security", "GICS Sector", "GICS Sub-Industry"}
    if not expected_cols.issubset(set(df.columns)):
        raise ValueError(
            f"Wikipedia table columns changed. Expected {expected_cols}, "
            f"got {set(df.columns)}"
        )

    result = pd.DataFrame({
        "ticker": df["Symbol"].str.replace(".", "-", regex=False),
        "company_name": df["Security"],
        "sector": df["GICS Sector"],
        "sub_industry": df["GICS Sub-Industry"],
    })

    logger.info(f"Loaded {len(result)} S&P 500 constituents")
    return result


def sp500_info_dict(df: pd.DataFrame) -> dict[str, dict]:
    """Convert S&P 500 DataFrame to a dict keyed by ticker.

    Returns: {ticker: {company_name, sector, sub_industry}}
    """
    return {
        row["ticker"]: {
            "company_name": row["company_name"],
            "sector": row["sector"],
            "sub_industry": row["sub_industry"],
        }
        for _, row in df.iterrows()
    }
