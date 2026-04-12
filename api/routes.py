"""API routes for the Assay web interface."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import RESULTS_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


def _load_stocks(path: Path) -> list[dict]:
    """Load stock list from a screen JSON file (handles both old and new format)."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict) and "stocks" in raw:
        return raw["stocks"]
    return raw  # legacy bare list


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

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to read screen data: {e}")

    # Support both old format (bare list) and new format (dict with metadata)
    if isinstance(raw, dict) and "stocks" in raw:
        return {
            "universe": raw.get("universe_description", raw.get("universe", "Unknown")),
            "date": raw.get("date", path.stem.replace("screen_", "")),
            "screened": raw.get("screened", len(raw["stocks"])),
            "stocks": raw["stocks"],
        }

    # Legacy format: bare list of stocks
    date_str = path.stem.replace("screen_", "")
    return {
        "universe": "S&P 500",
        "date": date_str,
        "screened": len(raw),
        "stocks": raw,
    }


@router.get("/screen/diff")
async def get_screen_diff():
    """Compare the latest screen to the previous one."""
    files = sorted(RESULTS_DIR.glob("screen_*.json"), reverse=True)
    if len(files) < 2:
        raise HTTPException(status_code=404, detail="Need at least 2 screens to compute diff.")

    current = _load_stocks(files[0])
    previous = _load_stocks(files[1])

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

    stocks = _load_stocks(path)

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

    stocks = _load_stocks(path)

    ticker_upper = ticker.upper()
    stock = next((s for s in stocks if s["ticker"] == ticker_upper), None)
    if stock is None:
        raise HTTPException(status_code=404, detail=f"{ticker_upper} not found.")

    sector = stock.get("sector")
    peers = [s for s in stocks if s.get("sector") == sector]
    peers.sort(key=lambda s: s.get("conviction_score") or 0, reverse=True)

    return {"ticker": ticker_upper, "sector": sector, "peers": peers}


@router.get("/stock/{ticker}/history")
async def get_stock_history(ticker: str):
    """Return a stock's scores across all backtest quarters."""
    import csv

    _, detail_path = _find_latest_backtest()
    if detail_path is None:
        raise HTTPException(status_code=404, detail="No backtest detail data found.")

    ticker_upper = ticker.upper()
    history = []

    with open(detail_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("ticker") == ticker_upper:
                history.append({
                    "quarter": row["quarter"],
                    "value_score": float(row["value_score"]) if row.get("value_score") else None,
                    "quality_score": float(row["quality_score"]) if row.get("quality_score") else None,
                    "piotroski_f": int(row["piotroski_f"]) if row.get("piotroski_f") else None,
                    "momentum_pct": float(row["momentum_pct"]) if row.get("momentum_pct") else None,
                    "sector": row.get("sector", ""),
                })

    # Also check all screen JSONs for the current and recent classifications
    for screen_path in sorted(RESULTS_DIR.glob("screen_*.json"), reverse=True)[:5]:
        if screen_path.stat().st_size < 10000:
            continue
        stocks = _load_stocks(screen_path)
        screen_date = screen_path.stem.replace("screen_", "")
        match = next((s for s in stocks if s["ticker"] == ticker_upper), None)
        if match:
            # Only add if we don't already have this date from backtest
            if not any(h["quarter"] == screen_date for h in history):
                history.append({
                    "quarter": screen_date,
                    "value_score": match.get("value_score"),
                    "quality_score": match.get("quality_score"),
                    "piotroski_f": match.get("piotroski_f"),
                    "momentum_pct": None,
                    "sector": match.get("sector", ""),
                    "classification": match.get("classification"),
                    "confidence": match.get("confidence"),
                })

    history.sort(key=lambda h: h["quarter"])

    return {"ticker": ticker_upper, "history": history}


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

    stocks = _load_stocks(path)

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


@router.get("/logo/{ticker}")
async def get_logo(ticker: str):
    """Proxy logo from companiesmarketcap.com with local caching."""
    import requests
    from fastapi.responses import Response as FastResponse

    ticker_upper = ticker.upper()
    # Ticker overrides for edge cases
    overrides = {"GOOGL": "GOOG", "BRK.B": "BRK-B"}
    logo_ticker = overrides.get(ticker_upper, ticker_upper)

    cache_dir = Path(__file__).parent.parent / "storage" / "logos"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{ticker_upper}.webp"

    # Return from cache
    if cache_path.exists():
        return FastResponse(content=cache_path.read_bytes(), media_type="image/webp",
                           headers={"Cache-Control": "public, max-age=2592000"})

    # Fetch from source
    try:
        url = f"https://companiesmarketcap.com/img/company-logos/64/{logo_ticker}.webp"
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            cache_path.write_bytes(r.content)
            return FastResponse(content=r.content, media_type="image/webp",
                               headers={"Cache-Control": "public, max-age=2592000"})
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Logo not available")


class ScreenConfig(BaseModel):
    include_financials: bool = False
    sector_relative: bool = False
    refresh: bool = False


_run_lock = threading.Lock()
_run_status: dict = {"running": False, "phase": "", "progress": 0}


@router.post("/screen/run")
async def run_screen(config: ScreenConfig):
    """Run the screener. Returns SSE stream with progress updates."""
    with _run_lock:
        if _run_status["running"]:
            raise HTTPException(status_code=409, detail="Screener is already running.")
        _run_status["running"] = True

    async def event_stream():
        _run_status["phase"] = "Starting..."
        _run_status["progress"] = 0

        def send_event(phase: str, progress: int):
            _run_status["phase"] = phase
            _run_status["progress"] = progress

        def run_in_thread():
            try:
                send_event("Importing screener...", 5)
                import os
                from main import run_screener
                universe = os.environ.get("ASSAY_UNIVERSE", "sp500")
                send_event(f"Running screener ({universe})...", 10)
                run_screener(
                    include_financials=config.include_financials,
                    sector_relative=config.sector_relative,
                    refresh=config.refresh,
                    universe_name=universe,
                )
                send_event("Complete", 100)
            except Exception as e:
                send_event(f"Error: {e}", -1)
                logger.error(f"Screener run failed: {e}", exc_info=True)
            finally:
                _run_status["running"] = False

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        # Stream progress events
        while thread.is_alive():
            yield f"data: {json.dumps({'phase': _run_status['phase'], 'progress': _run_status['progress']})}\n\n"
            await asyncio.sleep(1)

        # Final event
        yield f"data: {json.dumps({'phase': _run_status['phase'], 'progress': _run_status['progress'], 'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/screen/status")
async def screen_status():
    """Check if the screener is currently running."""
    return _run_status


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
