#!/usr/bin/env python3
"""Backfill historical prices for IWB (Russell 1000) constituents missing from cache.

Audit §6.4 / §4e.2: the existing Russell 1000 backtest in `DESIGN_DECISIONS.md`
line 638-640 was generated under cache state where only ~505 distinct tickers
had historical prices — essentially S&P 500 with a $3B market-cap filter, not
a real Russell 1000. This script downloads the canonical IWB constituents
(iShares Russell 1000 ETF holdings, fetched April 2026), identifies tickers
missing from `historical_prices`, and backfills via yfinance.

Methodology:
- Source: iShares IWB holdings CSV at /tmp/iwb.csv (must be pre-fetched).
- Backfill window: 2010-01-01 to today (covers 4-year backtest + 5-year beta).
- Date alignment: for each existing cache date (taken from SPY series),
  find the trading day closest to that date for the new ticker and store its
  adj_close. Falls back to the same-day close if available.
- Inserts (close, adj_close) pairs via HistoricalCache.set_prices().

Run-time estimate: ~5-10 minutes for ~500 tickers (yfinance batch).
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backtest.cache import HistoricalCache  # noqa: E402

IWB_CSV = Path("/tmp/iwb.csv")
START_DATE = "2010-01-01"
BENCHMARK = "SPY"
BATCH_SIZE = 50  # tickers per yfinance.download() call


def parse_iwb_tickers(path: Path) -> list[str]:
    with open(path) as f:
        rows = list(csv.reader(f))
    hdr_idx = next(i for i, r in enumerate(rows) if r and r[0] == "Ticker")
    tickers = []
    for r in rows[hdr_idx + 1:]:
        if len(r) <= 11:
            continue
        if r[3] != "Equity":
            continue
        if r[11] != "USD":
            continue
        symbol = r[0].replace(".", "-").strip()
        if symbol == "-" or not symbol:
            continue
        tickers.append(symbol)
    return tickers


def find_missing(tickers: list[str], cache: HistoricalCache) -> list[str]:
    cached = set()
    rows = cache._conn.execute("SELECT DISTINCT ticker FROM historical_prices").fetchall()
    for r in rows:
        cached.add(r[0])
    return [t for t in tickers if t not in cached]


def get_target_dates(cache: HistoricalCache) -> list[str]:
    """Use SPY's cached dates as the canonical target schedule."""
    rows = cache._conn.execute(
        "SELECT DISTINCT as_of_date FROM historical_prices WHERE ticker=? ORDER BY as_of_date",
        (BENCHMARK,),
    ).fetchall()
    return [r[0] for r in rows]


def backfill_ticker(ticker: str, target_dates: list[str], df: pd.DataFrame) -> list[tuple[str, str, float, float]]:
    """Given a daily price DataFrame for a single ticker, snap to target dates."""
    if df is None or df.empty:
        return []
    # df has DatetimeIndex; columns include 'Close' and 'Adj Close'
    rows: list[tuple[str, str, float, float]] = []
    df = df.dropna(how="all")
    if df.empty:
        return []
    df = df.sort_index()
    # Build a quick numpy-friendly date series
    dates = df.index.normalize()
    for target in target_dates:
        ts = pd.Timestamp(target)
        # Find the trading day on-or-before target (max 7 days back)
        mask = (dates <= ts) & (dates >= (ts - pd.Timedelta(days=7)))
        candidates = df.loc[mask]
        if candidates.empty:
            continue
        closest = candidates.iloc[-1]
        try:
            close = float(closest["Close"]) if "Close" in closest.index else None
        except (TypeError, ValueError):
            close = None
        try:
            adj_close = float(closest["Adj Close"]) if "Adj Close" in closest.index else close
        except (TypeError, ValueError):
            adj_close = close
        if close is None or adj_close is None:
            continue
        if not (close > 0 and adj_close > 0):
            continue
        rows.append((ticker, target, close, adj_close))
    return rows


def main():
    if not IWB_CSV.exists():
        print(f"Missing {IWB_CSV} — fetch IWB holdings first.")
        sys.exit(1)

    cache = HistoricalCache()
    iwb = parse_iwb_tickers(IWB_CSV)
    missing = find_missing(iwb, cache)
    target_dates = get_target_dates(cache)

    print(f"IWB tickers in CSV:     {len(iwb)}")
    print(f"Already in price cache: {len(iwb) - len(missing)}")
    print(f"To backfill:            {len(missing)}")
    print(f"Target dates per ticker: {len(target_dates)}  (from {target_dates[0]} to {target_dates[-1]})")
    print()

    success = 0
    fail = 0
    inserted_total = 0
    end_date = date.today().isoformat()

    # Process in batches
    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i:i + BATCH_SIZE]
        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch)} tickers ({batch[0]}..{batch[-1]})", flush=True)
        try:
            df_batch = yf.download(
                batch,
                start=START_DATE,
                end=end_date,
                progress=False,
                auto_adjust=False,
                group_by="ticker",
                threads=True,
            )
        except Exception as e:
            print(f"    Batch download failed: {e}")
            fail += len(batch)
            continue

        for ticker in batch:
            try:
                if isinstance(df_batch.columns, pd.MultiIndex):
                    if ticker not in df_batch.columns.get_level_values(0):
                        fail += 1
                        continue
                    sub = df_batch[ticker]
                else:
                    sub = df_batch  # single-ticker case
                rows = backfill_ticker(ticker, target_dates, sub)
                if not rows:
                    fail += 1
                    continue
                cache.set_prices(rows)
                inserted_total += len(rows)
                success += 1
            except Exception as e:
                fail += 1
                print(f"    {ticker}: {e}")
                continue

        # Be polite to yfinance
        time.sleep(0.5)

    print()
    print(f"Backfill complete. Success: {success}, Failed: {fail}, Rows inserted: {inserted_total}")

    # Verify
    new_count = cache._conn.execute(
        "SELECT COUNT(DISTINCT ticker) FROM historical_prices"
    ).fetchone()[0]
    print(f"historical_prices now contains {new_count} distinct tickers")


if __name__ == "__main__":
    main()
