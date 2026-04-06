"""CSV and JSON report generation."""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path

from config import RESULTS_DIR

logger = logging.getLogger(__name__)

_CSV_COLUMNS = [
    "date", "ticker", "company", "sector", "price",
    "value_score", "quality_score", "conviction_score", "classification",
    "earnings_yield", "fcf_yield",
    "piotroski_f", "gross_profitability", "growth_score",
    "analyst_target", "analyst_upside", "pct_from_52w_high",
    "dcf_bear", "dcf_base", "dcf_bull",
    "revenue_cagr_3yr", "gross_margin",
    "pe_ratio", "ev_ebitda", "dividend_yield", "beta", "market_cap",
]


def save_csv(today: date, results: list[dict]):
    """Save results to CSV."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"screen_{today.isoformat()}.csv"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            row["date"] = today.isoformat()
            writer.writerow(row)

    logger.info(f"CSV saved: {path}")
    return path


def save_json(today: date, results: list[dict]):
    """Save results to JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"screen_{today.isoformat()}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"JSON saved: {path}")
    return path
