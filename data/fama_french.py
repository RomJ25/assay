"""Fama-French factor and portfolio data from Kenneth French's Data Library.

Provides 60+ years of monthly returns for:
- 5-factor model (Mkt-RF, SMB, HML, RMW, CMA, RF)
- 32 portfolios sorted by Size × Book-to-Market × Operating Profitability

Portfolio [32] (BIG × HiBM × HiOP) is the academic equivalent of
Assay's CONVICTION BUY: large-cap, cheap, profitable stocks.

Source: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
Data: CRSP universe (survivorship-free, peer-reviewed)
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).parent.parent / "storage"

_FACTORS_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)

_PORTFOLIOS_32_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "32_Portfolios_ME_BEME_OP_2x4x4_CSV.zip"
)


def _download_zip_csv(url: str, cache_name: str) -> str:
    """Download a zip file from French's library, extract the CSV, cache it."""
    cache_path = _CACHE_DIR / cache_name
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    logger.info(f"Downloading {cache_name} from Kenneth French Data Library...")
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(r.content))
    csv_text = z.read(z.namelist()[0]).decode("utf-8")
    cache_path.write_text(csv_text, encoding="utf-8")
    logger.info(f"Cached to {cache_path}")
    return csv_text


def _parse_monthly_section(text: str, header_marker: str = None) -> pd.DataFrame:
    """Parse monthly returns from a French CSV (skip header text, find numeric data)."""
    lines = text.strip().split("\n")

    # Find the first line that starts with a 6-digit date (YYYYMM)
    data_lines = []
    header = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        parts = [p.strip() for p in stripped.split(",")]
        if parts[0] and len(parts[0]) == 6 and parts[0].isdigit():
            if header is None and i > 0:
                # The line before the first data line is the header
                for j in range(i - 1, -1, -1):
                    candidate = lines[j].strip()
                    if candidate and "," in candidate:
                        header = [c.strip() for c in candidate.split(",")]
                        break
            data_lines.append(parts)
        elif data_lines:
            # We've left the monthly section (hit annual or footer)
            if len(parts[0]) == 4 and parts[0].isdigit():
                break  # Annual section starts

    if not data_lines or not header:
        return pd.DataFrame()

    # Build DataFrame
    df = pd.DataFrame(data_lines, columns=header[:len(data_lines[0])])
    date_col = df.columns[0]
    df = df.rename(columns={date_col: "date"})

    # Convert to numeric
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse date
    df["year"] = df["date"].str[:4].astype(int)
    df["month"] = df["date"].str[4:6].astype(int)

    return df


def download_factors() -> pd.DataFrame:
    """Download Fama-French 5-factor monthly returns.

    Returns DataFrame with columns: date, year, month, Mkt-RF, SMB, HML, RMW, CMA, RF
    All values in percentage points (e.g., 1.5 = 1.5%).
    """
    text = _download_zip_csv(_FACTORS_URL, "ff_5_factors.csv")
    return _parse_monthly_section(text)


def download_portfolios_32() -> pd.DataFrame:
    """Download 32 portfolios sorted by Size × B/M × OP (monthly returns).

    Column [32] "BIG HiBM HiOP" is the academic CONVICTION BUY equivalent.
    Returns in percentage points.
    """
    text = _download_zip_csv(_PORTFOLIOS_32_URL, "ff_32_portfolios.csv")
    return _parse_monthly_section(text)


def compute_long_term_returns(
    start_year: int = 2014,
    end_year: int = 2026,
) -> dict:
    """Compute cumulative returns for the long-term case study.

    Returns dict with:
        - factors: annual HML, RMW, Market returns
        - portfolio: annual BIG×HiBM×HiOP returns
        - cumulative: growth of $100 for each series
    """
    factors = download_factors()
    portfolios = download_portfolios_32()

    if factors.empty or portfolios.empty:
        return {}

    # Filter to date range
    factors = factors[(factors["year"] >= start_year) & (factors["year"] <= end_year)].copy()

    # Find the target portfolio column
    target_col = None
    for col in portfolios.columns:
        if "BIG" in str(col) and "HiBM" in str(col) and "HiOP" in str(col):
            target_col = col
            break

    if target_col is None:
        # Fallback: last column is typically BIG HiBM HiOP
        target_col = portfolios.columns[-3] if len(portfolios.columns) > 3 else portfolios.columns[-1]
        logger.warning(f"Could not find BIG HiBM HiOP column, using {target_col}")

    portfolios = portfolios[(portfolios["year"] >= start_year) & (portfolios["year"] <= end_year)].copy()

    # Compute annual returns from monthly
    annual_data = []
    for year in range(start_year, end_year + 1):
        year_factors = factors[factors["year"] == year]
        year_ports = portfolios[portfolios["year"] == year]

        if year_factors.empty:
            continue

        # Compound monthly returns to annual
        mkt_annual = ((1 + (year_factors["Mkt-RF"] + year_factors["RF"]) / 100).prod() - 1) * 100
        hml_annual = ((1 + year_factors["HML"] / 100).prod() - 1) * 100
        rmw_annual = ((1 + year_factors["RMW"] / 100).prod() - 1) * 100
        rf_annual = ((1 + year_factors["RF"] / 100).prod() - 1) * 100

        port_annual = None
        if not year_ports.empty and target_col in year_ports.columns:
            port_annual = ((1 + year_ports[target_col] / 100).prod() - 1) * 100

        annual_data.append({
            "year": year,
            "market": round(float(mkt_annual), 2),
            "hml": round(float(hml_annual), 2),
            "rmw": round(float(rmw_annual), 2),
            "rf": round(float(rf_annual), 2),
            "vq_portfolio": round(float(port_annual), 2) if port_annual is not None else None,
        })

    # Compute cumulative growth of $100
    cumulative = {"market": 100.0, "hml": 100.0, "rmw": 100.0, "vq_portfolio": 100.0}
    for row in annual_data:
        cumulative["market"] *= (1 + row["market"] / 100)
        cumulative["hml"] *= (1 + row["hml"] / 100)
        cumulative["rmw"] *= (1 + row["rmw"] / 100)
        if row["vq_portfolio"] is not None:
            cumulative["vq_portfolio"] *= (1 + row["vq_portfolio"] / 100)
        row["cum_market"] = round(cumulative["market"], 1)
        row["cum_vq"] = round(cumulative["vq_portfolio"], 1)

    return {
        "annual": annual_data,
        "start_year": start_year,
        "end_year": end_year,
        "final_market": round(cumulative["market"], 1),
        "final_vq_portfolio": round(cumulative["vq_portfolio"], 1),
        "target_column": target_col,
    }
