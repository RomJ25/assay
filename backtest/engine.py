"""Backtest engine — quarterly replay of the screening pipeline."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date

from rich.console import Console
from rich.progress import Progress

from config import (
    BACKTEST_DEFAULT_YEARS,
    BACKTEST_FILING_LAG_DAYS,
    BACKTEST_QUARTERS,
)
from backtest.cache import HistoricalCache
from backtest.historical_fetcher import fetch_historical_data
from backtest.snapshot_builder import build_snapshot
from backtest.portfolio import simulate_portfolio, BacktestMetrics
from backtest.report import print_backtest_report, save_backtest_csv
from data.sp500 import fetch_sp500_list, sp500_info_dict
from scoring.value_scorer import compute_value_scores
from scoring.quality_scorer import compute_quality_scores
from scoring.conviction import conviction_score, classify, apply_min_fscore
from scoring.momentum_scorer import compute_momentum_percentiles, apply_momentum_gate
from scoring.filters import passes_data_quality, include_stock

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class QuarterResult:
    date: date
    picks: list[str]  # CONVICTION BUY tickers
    universe: list[str]  # ALL screened tickers (for benchmark)
    num_screened: int
    classifications: dict[str, int] = field(default_factory=dict)
    pick_details: list[dict] = field(default_factory=list)  # per-stock scoring data


@dataclass
class BacktestResult:
    quarters: list[QuarterResult]
    portfolio_returns: list[dict]  # per-quarter return records
    metrics: BacktestMetrics
    effective_start: date
    effective_end: date


_include_stock = include_stock  # local alias


def _generate_rebalance_dates(years: int) -> list[date]:
    """Generate quarterly rebalance dates going back `years` from now."""
    today = date.today()
    dates = []

    # Go back the specified number of years
    start_year = today.year - years
    for year in range(start_year, today.year + 1):
        for month, day in BACKTEST_QUARTERS:
            d = date(year, month, day)
            if d < today:
                dates.append(d)

    dates.sort()
    return dates


def run_backtest(
    years: int = BACKTEST_DEFAULT_YEARS,
    exclude_financials: bool = False,
    verbose: bool = False,
) -> BacktestResult:
    """Run the full backtest pipeline."""
    start_time = time.time()

    console.print(f"\n[bold blue]Assay Backtest — S&P 500 Value + Quality[/bold blue]")
    console.print(f"Period: {years} years | Rebalancing: quarterly | Filing lag: {BACKTEST_FILING_LAG_DAYS} days\n")

    # Step 1: Get current S&P 500 list (survivorship bias acknowledged)
    console.print("[dim]Fetching S&P 500 list...[/dim]")
    sp500_df = fetch_sp500_list()
    info = sp500_info_dict(sp500_df)
    tickers = list(info.keys())
    sp500_entries = [
        {"ticker": t, "company_name": v["company_name"], "sector": v["sector"], "sub_industry": v["sub_industry"]}
        for t, v in info.items()
    ]

    # Step 2: Generate rebalance dates + momentum lookback dates
    rebalance_dates = _generate_rebalance_dates(years)
    console.print(f"Rebalance dates: {len(rebalance_dates)} quarters ({rebalance_dates[0]} to {rebalance_dates[-1]})")

    # Add momentum lookback dates (12m and 1m before each rebalance) for price fetching
    from dateutil.relativedelta import relativedelta
    momentum_dates = set()
    for d in rebalance_dates:
        momentum_dates.add(d - relativedelta(months=12))
        momentum_dates.add(d - relativedelta(months=1))
    all_price_dates = sorted(set(rebalance_dates) | momentum_dates)

    # Step 3: Fetch all historical data
    cache = HistoricalCache()
    try:
        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Fetching historical data...", total=None)
            fetch_historical_data(tickers, sp500_entries, cache, all_price_dates)
            progress.update(task, completed=True)

        # Step 4: Replay screener for each quarter
        quarter_results = []
        quarterly_picks = []   # list of (date, [tickers])
        quarterly_universe = []  # list of (date, [tickers])

        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Screening quarters...", total=len(rebalance_dates))

            for rebal_date in rebalance_dates:
                qr = _screen_quarter(rebal_date, tickers, info, cache, exclude_financials, verbose)
                if qr is not None:
                    quarter_results.append(qr)
                    quarterly_picks.append((rebal_date, qr.picks))
                    quarterly_universe.append((rebal_date, qr.universe))
                progress.advance(task)

        if not quarter_results:
            console.print("[red]No quarters produced results.[/red]")
            cache.close()
            return None

        # Step 5: Portfolio simulation
        console.print("[dim]Simulating portfolio...[/dim]")
        returns, metrics = simulate_portfolio(
            quarterly_picks, quarterly_universe, cache, rebalance_dates,
        )

        result = BacktestResult(
            quarters=quarter_results,
            portfolio_returns=returns,
            metrics=metrics,
            effective_start=quarter_results[0].date,
            effective_end=quarter_results[-1].date,
        )

        elapsed = time.time() - start_time
        console.print(f"\nBacktest complete in {elapsed:.1f}s\n")

        # Step 6: Output
        print_backtest_report(result)
        save_backtest_csv(result)

        return result
    finally:
        cache.close()


def _compute_backtest_momentum(
    tickers: list[str],
    rebal_date: date,
    cache: HistoricalCache,
) -> dict[str, float]:
    """Compute 12-1 month momentum from cached adj close prices.

    Uses the rebalance date ~12 months ago as start and ~1 month before
    current rebalance as end (skip-month).
    """
    from dateutil.relativedelta import relativedelta

    start_date = rebal_date - relativedelta(months=12)
    skip_date = rebal_date - relativedelta(months=1)

    results = {}
    for ticker in tickers:
        start_price = cache.get_price(ticker, start_date.isoformat())
        end_price = cache.get_price(ticker, skip_date.isoformat())

        if start_price is None or end_price is None:
            # Fall back to current rebal date prices if skip-month not cached
            end_price = cache.get_price(ticker, rebal_date.isoformat())
            if start_price is None or end_price is None:
                continue

        _, adj_start = start_price
        _, adj_end = end_price
        if adj_start > 0:
            results[ticker] = (adj_end - adj_start) / adj_start

    return results


def _screen_quarter(
    rebal_date: date,
    tickers: list[str],
    sp500_info: dict[str, dict],
    cache: HistoricalCache,
    exclude_financials: bool,
    verbose: bool,
) -> QuarterResult | None:
    """Run the screening pipeline for a single quarter."""
    # Build snapshots
    snapshots = {}
    for ticker in tickers:
        raw = cache.get_financials(ticker)
        if raw is None:
            continue

        price_data = cache.get_price(ticker, rebal_date.isoformat())
        if price_data is None:
            continue
        close_price, _ = price_data

        sp_entry = sp500_info.get(ticker, {})
        fd = build_snapshot(ticker, rebal_date, raw, close_price, sp_entry)
        if fd is not None:
            snapshots[ticker] = fd

    if not snapshots:
        logger.warning(f"{rebal_date}: no snapshots built")
        return None

    # Apply data quality filter
    filtered = {t: fd for t, fd in snapshots.items() if passes_data_quality(fd)}

    # Apply financial sector filter
    if exclude_financials:
        filtered = {t: fd for t, fd in filtered.items() if _include_stock(fd)}

    if not filtered:
        logger.warning(f"{rebal_date}: no stocks passed filters")
        return None

    # Score
    value_scores = compute_value_scores(filtered)
    quality_scores, piotroski_raw, _, _ = compute_quality_scores(filtered)

    # Momentum: compute 12-1 month return from cached rebalance date prices
    # Use the rebalance date ~12 months ago and ~1 month ago as approximations
    momentum_raw = _compute_backtest_momentum(list(filtered.keys()), rebal_date, cache)
    momentum_pcts = compute_momentum_percentiles(momentum_raw)

    # Classify
    classifications = {}
    picks = []
    pick_details = []
    universe = list(filtered.keys())

    for t in filtered:
        v = value_scores.get(t)
        q = quality_scores.get(t)
        if v is None or q is None:
            continue

        cl = classify(v, q)
        pf = piotroski_raw.get(t, 0)
        cl = apply_min_fscore(cl, pf)
        cl = apply_momentum_gate(cl, momentum_pcts.get(t))

        classifications[cl] = classifications.get(cl, 0) + 1
        if cl == "CONVICTION BUY":
            picks.append(t)
            pick_details.append({
                "ticker": t,
                "sector": filtered[t].sector,
                "value_score": round(v, 1),
                "quality_score": round(q, 1),
                "piotroski_f": pf,
                "momentum_pct": round(momentum_pcts.get(t, 0), 1),
            })

    if verbose:
        logger.info(f"{rebal_date}: {len(filtered)} screened, {len(picks)} picks, {classifications}")

    return QuarterResult(
        date=rebal_date,
        picks=picks,
        universe=universe,
        num_screened=len(filtered),
        classifications=classifications,
        pick_details=pick_details,
    )
