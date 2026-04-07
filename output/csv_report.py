"""CSV and JSON report generation."""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path

from config import RESULTS_DIR

logger = logging.getLogger(__name__)

_CRITERION_KEYS = [
    "pio_1_ni", "pio_2_ocf", "pio_3_roa", "pio_4_accruals",
    "pio_5_debt", "pio_6_current", "pio_7_dilution",
    "pio_8_margin", "pio_9_turnover",
]

_CRITERION_MAP = [
    "net_income_positive", "ocf_positive", "roa_improving", "accruals_quality",
    "debt_ratio_decreasing", "current_ratio_up", "no_dilution",
    "gross_margin_up", "asset_turnover_up",
]

_CSV_COLUMNS = [
    "date", "ticker", "company", "sector", "price",
    "opportunity_score", "trajectory_score",
    "value_score", "quality_score", "conviction_score", "classification", "confidence",
    "earnings_yield", "fcf_yield",
    "piotroski_f", "gross_profitability", "growth_score",
    *_CRITERION_KEYS,
    "analyst_target", "analyst_upside", "pct_from_52w_high",
    "dcf_bear", "dcf_base", "dcf_bull",
    "revenue_cagr_3yr", "gross_margin",
    "pe_ratio", "ev_ebitda", "dividend_yield", "beta", "market_cap",
]


def _flatten_breakdown(row: dict) -> dict:
    """Extract Piotroski criterion pass/fail booleans into flat CSV columns."""
    bd = row.get("piotroski_breakdown", {})
    criteria = bd.get("criteria", {})
    for csv_key, criterion_key in zip(_CRITERION_KEYS, _CRITERION_MAP):
        c = criteria.get(criterion_key, {})
        row[csv_key] = c.get("pass", "")
    return row


def save_csv(today: date, results: list[dict]):
    """Save results to CSV."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"screen_{today.isoformat()}.csv"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            row["date"] = today.isoformat()
            _flatten_breakdown(row)
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
