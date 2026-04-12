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
    TCOST_BPS_ROUNDTRIP,
)
from backtest.cache import HistoricalCache
from backtest.historical_fetcher import fetch_historical_data
from backtest.snapshot_builder import build_snapshot
from backtest.portfolio import simulate_portfolio, simulate_selective_sell, BacktestMetrics
from backtest.report import print_backtest_report, save_backtest_csv
from data.sp500 import fetch_sp500_list, sp500_info_dict
from scoring.value_scorer import compute_value_scores
from scoring.quality_scorer import compute_quality_scores
from scoring.conviction import conviction_score, classify, apply_min_fscore, confidence_level
from scoring.momentum_scorer import compute_momentum_percentiles, apply_momentum_gate
from scoring.filters import passes_data_quality, include_stock

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class StockDetail:
    """Per-stock scoring and classification data for case study analysis."""
    ticker: str
    sector: str
    value_score: float
    quality_score: float
    conviction_score: float
    piotroski_f: int
    momentum_pct: float | None
    raw_classification: str       # From classify() before any gates
    final_classification: str     # After F-gate and momentum gate
    f_gate_fired: bool            # True if F-gate downgraded from CB
    momentum_gate_fired: bool     # True if momentum gate downgraded from CB
    confidence: str | None        # HIGH/MOD/LOW for final CB only


@dataclass
class FullQuarterSnapshot:
    """Complete classification data for all stocks at a rebalance date."""
    date: date
    stock_details: list[StockDetail]
    classifications: dict[str, int] = field(default_factory=dict)
    num_screened: int = 0


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
    top_n_metrics: dict[int, BacktestMetrics] | None = None
    selective_sell_metrics: BacktestMetrics | None = None
    selective_sell_returns: list[dict] | None = None


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
    include_financials: bool = False,
    verbose: bool = False,
    tcost_bps: int = TCOST_BPS_ROUNDTRIP,
    survivorship_free: bool = False,
    universe_name: str = "sp500",
) -> BacktestResult:
    """Run the full backtest pipeline.

    Args:
        survivorship_free: If True, use point-in-time constituents
            for each quarter instead of the current list. Only supported
            for sp500 (requires historical membership data).
        universe_name: Which universe to backtest (sp500, tase, etc.)
    """
    start_time = time.time()

    from data.universe import get_universe
    universe = get_universe(universe_name)

    bias_label = "survivorship-free" if survivorship_free else "current list"
    console.print(f"\n[bold blue]Assay Backtest — {universe.description} Value + Quality[/bold blue]")
    console.print(f"Period: {years} years | Rebalancing: quarterly | Filing lag: {BACKTEST_FILING_LAG_DAYS} days")
    console.print(f"Universe: {universe.description} ({bias_label})\n")

    # Step 1: Generate rebalance dates
    rebalance_dates = _generate_rebalance_dates(years)
    console.print(f"Rebalance dates: {len(rebalance_dates)} quarters ({rebalance_dates[0]} to {rebalance_dates[-1]})")

    # Step 2: Get stock universe
    console.print(f"[dim]Fetching {universe.description} list...[/dim]")
    tickers, info = universe.fetch()

    if survivorship_free and universe.historical:
        from data.sp500_historical import get_all_historical_tickers

        # Get ALL tickers that were ever in the universe during the backtest period
        all_historical = get_all_historical_tickers(rebalance_dates[0], rebalance_dates[-1])
        tickers = list(all_historical | set(info.keys()))
        console.print(f"[green]Survivorship-free: {len(tickers)} tickers ({len(all_historical - set(info.keys()))} historical-only)[/green]")

        for t in tickers:
            if t not in info:
                info[t] = {"company_name": t, "sector": "Unknown", "sub_industry": "Unknown"}
    elif survivorship_free and not universe.historical:
        console.print(f"[yellow]Survivorship-free not available for {universe.description} — using current list[/yellow]")

    sp500_entries = [
        {"ticker": t, "company_name": v.get("company_name", t), "sector": v.get("sector", "Unknown"), "sub_industry": v.get("sub_industry", "Unknown")}
        for t, v in info.items()
    ]

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
        quarterly_classifications = []  # list of (date, {ticker: classification}) for selective sell

        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Screening quarters...", total=len(rebalance_dates))

            for rebal_date in rebalance_dates:
                # Point-in-time universe if available
                if survivorship_free and universe.historical:
                    pit_tickers = universe.historical(rebal_date)
                    pit_info = {t: info.get(t, {"company_name": t, "sector": "Unknown", "sub_industry": "Unknown"}) for t in pit_tickers}
                else:
                    pit_tickers = tickers
                    pit_info = info

                # Use full replay to get ALL classifications (for selective sell)
                full = _screen_quarter_full(rebal_date, pit_tickers, pit_info, cache, not include_financials, verbose)
                if full is not None:
                    # Extract CB picks for backward-compatible quarterly rebalance
                    picks = [(sd.conviction_score, sd.ticker) for sd in full.stock_details
                             if sd.final_classification == "CONVICTION BUY"]
                    picks.sort(reverse=True)
                    sorted_tickers = [t for _, t in picks]
                    universe = [sd.ticker for sd in full.stock_details]

                    qr = QuarterResult(
                        date=rebal_date,
                        picks=sorted_tickers,
                        universe=universe,
                        num_screened=full.num_screened,
                        classifications=full.classifications,
                        pick_details=[{
                            "ticker": sd.ticker, "sector": sd.sector,
                            "value_score": sd.value_score, "quality_score": sd.quality_score,
                            "piotroski_f": sd.piotroski_f,
                            "momentum_pct": sd.momentum_pct if sd.momentum_pct is not None else 0.0,
                        } for sd in full.stock_details if sd.final_classification == "CONVICTION BUY"],
                    )
                    # Sort pick_details by conviction
                    ticker_order = {t: i for i, t in enumerate(sorted_tickers)}
                    qr.pick_details.sort(key=lambda p: ticker_order.get(p["ticker"], 999))

                    quarter_results.append(qr)
                    quarterly_picks.append((rebal_date, sorted_tickers))
                    quarterly_universe.append((rebal_date, universe))
                    quarterly_classifications.append((rebal_date, {
                        sd.ticker: sd.final_classification for sd in full.stock_details
                    }))
                progress.advance(task)

        if not quarter_results:
            console.print("[red]No quarters produced results.[/red]")
            cache.close()
            return None

        # Step 5: Portfolio simulation (full portfolio)
        console.print("[dim]Simulating portfolio...[/dim]")
        returns, metrics = simulate_portfolio(
            quarterly_picks, quarterly_universe, cache, rebalance_dates,
            tcost_bps=tcost_bps,
        )

        # Step 5b: Selective sell simulation (hold unless HOLD/VT/AVOID)
        console.print("[dim]Simulating selective-sell strategy...[/dim]")
        ss_returns, ss_metrics = simulate_selective_sell(
            quarterly_classifications, quarterly_universe, cache, rebalance_dates,
            tcost_bps=tcost_bps,
        )

        # Print comparison
        console.print(f"\n[bold]STRATEGY COMPARISON[/bold]")
        console.print(f"  {'Quarterly rebalance:':30s} CAGR {metrics.cagr*100:+.1f}%  Alpha {metrics.selection_alpha*100:+.1f}%  Avg {metrics.avg_picks_per_quarter:.0f} picks")
        console.print(f"  {'Selective sell (recommended):':30s} CAGR {ss_metrics.cagr*100:+.1f}%  Alpha {ss_metrics.selection_alpha*100:+.1f}%  Avg {ss_metrics.avg_picks_per_quarter:.0f} picks")
        delta = ss_metrics.cagr - metrics.cagr
        console.print(f"  {'Selective sell advantage:':30s} [{'green' if delta > 0 else 'red'}]{delta*100:+.1f}%/yr[/{'green' if delta > 0 else 'red'}]")

        # Step 5c: Top-N simulations (picks are already sorted by conviction)
        top_n_metrics = {}
        for n in (1, 3, 5):
            top_n_picks = [(d, picks[:n]) for d, picks in quarterly_picks]
            _, m = simulate_portfolio(
                top_n_picks, quarterly_universe, cache, rebalance_dates,
                tcost_bps=tcost_bps,
            )
            top_n_metrics[n] = m

        result = BacktestResult(
            quarters=quarter_results,
            portfolio_returns=returns,
            metrics=metrics,
            effective_start=quarter_results[0].date,
            effective_end=quarter_results[-1].date,
            top_n_metrics=top_n_metrics,
            selective_sell_metrics=ss_metrics,
            selective_sell_returns=ss_returns,
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


def _screen_quarter_full(
    rebal_date: date,
    tickers: list[str],
    sp500_info: dict[str, dict],
    cache: HistoricalCache,
    exclude_financials: bool,
    verbose: bool,
) -> FullQuarterSnapshot | None:
    """Run the screening pipeline and return ALL stocks' classifications with gate tracking."""
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

    momentum_raw = _compute_backtest_momentum(list(filtered.keys()), rebal_date, cache)
    momentum_pcts = compute_momentum_percentiles(momentum_raw)

    # Classify ALL stocks with gate tracking
    classifications = {}
    stock_details = []

    for t in filtered:
        v = value_scores.get(t)
        q = quality_scores.get(t)
        if v is None or q is None:
            continue

        raw_cl = classify(v, q)
        pf = piotroski_raw.get(t, 0)
        post_f = apply_min_fscore(raw_cl, pf)
        final = apply_momentum_gate(post_f, momentum_pcts.get(t))

        classifications[final] = classifications.get(final, 0) + 1

        conv = conviction_score(v, q) or 0.0
        conf = confidence_level(v, q) if final == "CONVICTION BUY" else None
        mom = momentum_pcts.get(t)

        stock_details.append(StockDetail(
            ticker=t,
            sector=filtered[t].sector,
            value_score=round(v, 1),
            quality_score=round(q, 1),
            conviction_score=round(conv, 1),
            piotroski_f=pf,
            momentum_pct=round(mom, 1) if mom is not None else None,
            raw_classification=raw_cl,
            final_classification=final,
            f_gate_fired=(raw_cl == "CONVICTION BUY" and raw_cl != post_f),
            momentum_gate_fired=(post_f == "CONVICTION BUY" and post_f != final),
            confidence=conf,
        ))

    if verbose:
        cb_count = classifications.get("CONVICTION BUY", 0)
        logger.info(f"{rebal_date}: {len(stock_details)} screened, {cb_count} picks, {classifications}")

    return FullQuarterSnapshot(
        date=rebal_date,
        stock_details=stock_details,
        classifications=classifications,
        num_screened=len(stock_details),
    )


def _screen_quarter(
    rebal_date: date,
    tickers: list[str],
    sp500_info: dict[str, dict],
    cache: HistoricalCache,
    exclude_financials: bool,
    verbose: bool,
) -> QuarterResult | None:
    """Run the screening pipeline for a single quarter.

    Delegates to _screen_quarter_full() and extracts CB picks for backward compatibility.
    """
    full = _screen_quarter_full(rebal_date, tickers, sp500_info, cache, exclude_financials, verbose)
    if full is None:
        return None

    # Extract CB picks sorted by conviction (highest first)
    picks = []
    pick_details = []
    universe = []

    for sd in full.stock_details:
        universe.append(sd.ticker)
        if sd.final_classification == "CONVICTION BUY":
            picks.append((sd.conviction_score, sd.ticker))
            pick_details.append({
                "ticker": sd.ticker,
                "sector": sd.sector,
                "value_score": sd.value_score,
                "quality_score": sd.quality_score,
                "piotroski_f": sd.piotroski_f,
                "momentum_pct": sd.momentum_pct if sd.momentum_pct is not None else 0.0,
            })

    picks.sort(reverse=True)
    sorted_tickers = [t for _, t in picks]

    ticker_order = {t: i for i, t in enumerate(sorted_tickers)}
    pick_details.sort(key=lambda p: ticker_order.get(p["ticker"], 999))

    return QuarterResult(
        date=rebal_date,
        picks=sorted_tickers,
        universe=universe,
        num_screened=full.num_screened,
        classifications=full.classifications,
        pick_details=pick_details,
    )
