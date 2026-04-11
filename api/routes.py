"""API routes for the Assay web interface."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from config import RESULTS_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


def _find_latest_screen() -> Path | None:
    """Find the most recent full screen JSON file (skip single-ticker runs)."""
    for path in sorted(RESULTS_DIR.glob("screen_*.json"), reverse=True):
        # Skip tiny files that are single-ticker runs
        if path.stat().st_size > 10000:  # Full screens are >100KB
            return path
    return None


def _find_latest_backtest() -> tuple[Path | None, Path | None]:
    """Find the most recent backtest CSV and detail CSV."""
    summaries = sorted(RESULTS_DIR.glob("backtest_[0-9]*.csv"), reverse=True)
    details = sorted(RESULTS_DIR.glob("backtest_detail_*.csv"), reverse=True)
    return (summaries[0] if summaries else None, details[0] if details else None)


@router.get("/screen")
async def get_screen():
    """Return the latest screen results."""
    path = _find_latest_screen()
    if path is None:
        raise HTTPException(status_code=404, detail="No screen data found. Run the screener first.")

    with open(path) as f:
        stocks = json.load(f)

    # Extract date from filename
    date_str = path.stem.replace("screen_", "")

    return {
        "universe": "S&P 500",
        "date": date_str,
        "screened": len(stocks),
        "stocks": stocks,
    }


@router.get("/screen/diff")
async def get_screen_diff():
    """Compare the latest screen to the previous one."""
    files = sorted(RESULTS_DIR.glob("screen_*.json"), reverse=True)
    if len(files) < 2:
        raise HTTPException(status_code=404, detail="Need at least 2 screens to compute diff.")

    with open(files[0]) as f:
        current = json.load(f)
    with open(files[1]) as f:
        previous = json.load(f)

    current_date = files[0].stem.replace("screen_", "")
    previous_date = files[1].stem.replace("screen_", "")

    current_cb = {s["ticker"]: s for s in current if s.get("classification") == "CONVICTION BUY"}
    previous_cb = {s["ticker"]: s for s in previous if s.get("classification") == "CONVICTION BUY"}

    new_picks = []
    for t, s in current_cb.items():
        if t not in previous_cb:
            new_picks.append(s)

    dropped_picks = []
    for t, s in previous_cb.items():
        if t not in current_cb:
            # Find the stock in current screen to see its new classification
            current_stock = next((cs for cs in current if cs["ticker"] == t), None)
            entry = {**s, "previous_classification": "CONVICTION BUY"}
            if current_stock:
                entry["new_classification"] = current_stock.get("classification")
            dropped_picks.append(entry)

    changed_scores = []
    for t in current_cb:
        if t in previous_cb:
            curr = current_cb[t]
            prev = previous_cb[t]
            if (curr.get("value_score") != prev.get("value_score") or
                    curr.get("quality_score") != prev.get("quality_score")):
                changed_scores.append({
                    "ticker": t,
                    "company": curr.get("company"),
                    "current": {"value": curr.get("value_score"), "quality": curr.get("quality_score"),
                                "conviction": curr.get("conviction_score")},
                    "previous": {"value": prev.get("value_score"), "quality": prev.get("quality_score"),
                                 "conviction": prev.get("conviction_score")},
                })

    return {
        "current_date": current_date,
        "previous_date": previous_date,
        "new_picks": new_picks,
        "dropped_picks": dropped_picks,
        "changed_scores": changed_scores,
    }


@router.get("/stock/{ticker}")
async def get_stock(ticker: str):
    """Return detailed data for a single stock from the latest screen."""
    path = _find_latest_screen()
    if path is None:
        raise HTTPException(status_code=404, detail="No screen data found.")

    with open(path) as f:
        stocks = json.load(f)

    ticker_upper = ticker.upper()
    stock = next((s for s in stocks if s["ticker"] == ticker_upper), None)
    if stock is None:
        raise HTTPException(status_code=404, detail=f"{ticker_upper} not found in latest screen.")

    return stock


@router.get("/stock/{ticker}/peers")
async def get_stock_peers(ticker: str):
    """Return sector peers for a stock."""
    path = _find_latest_screen()
    if path is None:
        raise HTTPException(status_code=404, detail="No screen data found.")

    with open(path) as f:
        stocks = json.load(f)

    ticker_upper = ticker.upper()
    stock = next((s for s in stocks if s["ticker"] == ticker_upper), None)
    if stock is None:
        raise HTTPException(status_code=404, detail=f"{ticker_upper} not found.")

    sector = stock.get("sector")
    peers = [s for s in stocks if s.get("sector") == sector]
    peers.sort(key=lambda s: s.get("conviction_score") or 0, reverse=True)

    return {"ticker": ticker_upper, "sector": sector, "peers": peers}


@router.get("/backtest")
async def get_backtest():
    """Return the latest backtest results."""
    import csv

    summary_path, detail_path = _find_latest_backtest()
    if summary_path is None:
        raise HTTPException(status_code=404, detail="No backtest data found. Run the backtest first.")

    # Parse summary CSV
    with open(summary_path) as f:
        reader = csv.DictReader(f)
        quarters = []
        for row in reader:
            quarters.append({k: _parse_num(v) for k, v in row.items()})

    # Parse detail CSV
    picks = []
    if detail_path:
        with open(detail_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                picks.append({k: _parse_num(v) for k, v in row.items()})

    date_str = summary_path.stem.replace("backtest_", "")

    return {
        "date": date_str,
        "quarters": quarters,
        "picks": picks,
    }


@router.get("/search")
async def search_stocks(q: str = ""):
    """Fuzzy search stocks by ticker or company name."""
    if not q or len(q) < 1:
        return {"results": []}

    path = _find_latest_screen()
    if path is None:
        return {"results": []}

    with open(path) as f:
        stocks = json.load(f)

    q_lower = q.lower()
    results = []
    for s in stocks:
        ticker = s.get("ticker", "").lower()
        company = s.get("company", "").lower()
        if q_lower in ticker or q_lower in company:
            results.append({
                "ticker": s["ticker"],
                "company": s.get("company"),
                "classification": s.get("classification"),
                "value_score": s.get("value_score"),
                "quality_score": s.get("quality_score"),
                "conviction_score": s.get("conviction_score"),
                "confidence": s.get("confidence"),
            })

    # Sort: exact ticker match first, then by conviction score
    results.sort(key=lambda r: (
        0 if r["ticker"].lower() == q_lower else 1,
        -(r.get("conviction_score") or 0),
    ))

    return {"results": results[:20]}


def _parse_num(val: str) -> str | float | int | None:
    """Parse a CSV value to its appropriate type."""
    if val == "" or val is None:
        return None
    try:
        if "." in val:
            return float(val)
        return int(val)
    except (ValueError, TypeError):
        return val
