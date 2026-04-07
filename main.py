"""Assay — S&P 500 Value + Quality Stock Screener.

Tests every stock for value (Earnings Yield) and quality (Piotroski F-Score
+ Gross Profitability), separating conviction buys from value traps.

Based on academically proven quant strategies:
- Carlisle's Acquirer's Multiple (EV/EBIT): 17.9% CAGR over 44 years
- Piotroski F-Score: 13.4% annual outperformance over 20 years
- Novy-Marx Gross Profitability: equal power to book-to-market ratio
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import date

from rich.console import Console
from rich.progress import Progress

from data.fetcher import DataFetcher
from models.dcf import DCFModel
from models.relative import RelativeModel
from quality.growth import GrowthModel
from scoring.value_scorer import compute_value_scores, get_yield_metrics
from scoring.quality_scorer import compute_quality_scores
from scoring.conviction import conviction_score, classify, confidence_level, apply_min_fscore
from scoring.momentum_scorer import compute_momentum_percentiles, apply_momentum_gate
from scoring.filters import passes_data_quality, include_stock
from output.console_report import print_report
from output.csv_report import save_csv, save_json

console = Console()
logger = logging.getLogger("assay")


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


_include_stock = include_stock  # backward compat alias


def run_screener(ticker: str | None = None, top_n: int = 20, verbose: bool = False,
                 refresh: bool = False, wide: bool = False, breakdown: bool = False,
                 include_financials: bool = False):
    """Main screener pipeline."""
    setup_logging(verbose)
    today = date.today()
    start_time = time.time()

    console.print(f"\n[bold blue]Assay — S&P 500 Value + Quality[/bold blue]")

    # Step 1: Fetch S&P 500 list
    fetcher = DataFetcher(force_refresh=refresh)
    tickers, sp500_info = fetcher.get_sp500()

    single_ticker = None
    if ticker:
        single_ticker = ticker.upper().replace(".", "-")
        if single_ticker not in sp500_info:
            console.print(f"[red]{single_ticker} not found in S&P 500[/red]")
            return
        console.print(f"Single stock mode: {single_ticker}")
    else:
        console.print(f"Loaded {len(tickers)} S&P 500 constituents")

    # Step 2: Fetch data (always full universe for accurate percentile ranking)
    all_data = fetcher.fetch_all(tickers, sp500_info)
    console.print(f"Fetched data for {len(all_data)} stocks")

    if not all_data:
        console.print("[red]No data fetched. Check internet connection.[/red]")
        return

    # Filter for data quality
    screened = {t: d for t, d in all_data.items() if passes_data_quality(d)}
    console.print(f"Passed quality filter: {len(screened)}/{len(all_data)}")

    if not include_financials:
        before = len(screened)
        screened = {t: d for t, d in screened.items() if _include_stock(d)}
        console.print(f"Excluded financials/RE: {before - len(screened)} removed, {len(screened)} remaining")

    # Step 3: RANK by earnings yield (value dimension)
    value_scores = compute_value_scores(screened)

    # Step 4: Score quality (Piotroski + Gross Profitability)
    quality_scores, piotroski_raw, gp_ratios, pio_breakdowns = compute_quality_scores(screened)

    # Step 5: DCF + Relative as supplementary context (not for ranking)
    dcf_model = DCFModel()
    relative_model = RelativeModel()
    relative_model.compute_sector_medians(screened)
    growth_model = GrowthModel()

    # Step 5b: Momentum gate
    momentum_raw = {t: d.momentum_12m for t, d in screened.items() if d.momentum_12m is not None}
    momentum_pcts = compute_momentum_percentiles(momentum_raw)

    # Step 6: Build results
    results = []
    with Progress(transient=True) as progress:
        task = progress.add_task("Screening...", total=len(screened))
        for t, d in screened.items():
            v_score = value_scores.get(t)
            q_score = quality_scores.get(t)
            conv = conviction_score(v_score, q_score)
            cl = classify(v_score, q_score)
            cl = apply_min_fscore(cl, piotroski_raw.get(t, 0))
            cl = apply_momentum_gate(cl, momentum_pcts.get(t))
            conf = confidence_level(v_score, q_score) if cl == "CONVICTION BUY" else None

            # Yield metrics
            yields = get_yield_metrics(d)

            # Context: DCF (supplementary, not scoring)
            dcf_r = dcf_model.calculate(d)
            dcf_details = dcf_r.details if dcf_r else {}

            # Context: Relative (supplementary)
            relative_model.calculate(d)

            # Context: Growth score (supplementary)
            growth_score = growth_model.calculate(d)

            # Context: Growth metrics
            rev = d.revenue
            valid_rev = [v for v in rev if v is not None and v > 0]
            rev_cagr = ((valid_rev[0] / valid_rev[-1]) ** (1 / (len(valid_rev) - 1)) - 1) if len(valid_rev) >= 2 else None

            # Gross profitability
            gp_ratio = gp_ratios.get(t)

            # Analyst context
            analyst_upside = None
            if d.analyst_target and d.current_price > 0:
                analyst_upside = (d.analyst_target - d.current_price) / d.current_price * 100

            # 52-week high context
            pct_from_high = None
            if d.fifty_two_week_high and d.current_price > 0:
                pct_from_high = (d.current_price - d.fifty_two_week_high) / d.fifty_two_week_high * 100

            results.append({
                "ticker": t,
                "company": d.company_name,
                "sector": d.sector,
                "price": d.current_price,
                "value_score": v_score,
                "quality_score": q_score,
                "conviction_score": conv,
                "classification": cl,
                "confidence": conf,
                # Value metrics (the actual ranking signals)
                "earnings_yield": yields.get("earnings_yield"),
                "fcf_yield": yields.get("fcf_yield"),
                # Quality metrics
                "piotroski_f": piotroski_raw.get(t, 0),
                "gross_profitability": gp_ratio,
                "growth_score": growth_score,
                # Piotroski criterion breakdown
                "piotroski_breakdown": pio_breakdowns.get(t, {}),
                # Context (supplementary, not scoring)
                "dcf_bear": dcf_details.get("dcf_bear"),
                "dcf_base": dcf_details.get("dcf_base"),
                "dcf_bull": dcf_details.get("dcf_bull"),
                "analyst_target": d.analyst_target,
                "analyst_upside": analyst_upside,
                "pct_from_52w_high": pct_from_high,
                # Additional context
                "revenue_cagr_3yr": rev_cagr,
                "gross_margin": (d.gross_profit[0] / d.revenue[0]) if d.gross_profit[0] and d.revenue[0] else None,
                "pe_ratio": d.trailing_pe,
                "ev_ebitda": d.enterprise_to_ebitda,
                "dividend_yield": d.dividend_yield,
                "beta": d.beta,
                "market_cap": d.market_cap,
                "momentum_12m": d.momentum_12m,
            })
            progress.advance(task)

    elapsed = time.time() - start_time
    console.print(f"\nScreened {len(results)} stocks in {elapsed:.1f}s")

    # Single-stock mode: filter to just the requested ticker after scoring
    if single_ticker:
        results = [r for r in results if r["ticker"] == single_ticker]

    if not results:
        console.print("[yellow]No stocks passed filters.[/yellow]")
        return

    # Step 7: Output
    print_report(today, results, top_n=top_n, wide=wide, breakdown=breakdown,
                 include_financials=include_financials)
    csv_path = save_csv(today, results)
    save_json(today, results)

    console.print(f"\n[green]Reports saved to {csv_path.parent}/[/green]")
    fetcher.close()


def main():
    parser = argparse.ArgumentParser(
        description="Assay — S&P 500 Value + Quality Stock Screener"
    )
    parser.add_argument("--ticker", "-t", help="Screen a single ticker (e.g., AAPL)")
    parser.add_argument("--top", type=int, default=20, help="Show top N results (default: 20)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--refresh", action="store_true", help="Bypass cache, fetch fresh data")
    parser.add_argument("--wide", action="store_true", help="Wide table with extra columns")
    parser.add_argument("--breakdown", action="store_true", help="Show Piotroski criterion breakdown")
    parser.add_argument("--include-financials", action="store_true",
                        help="Include banks, insurance, and REITs (excluded by default)")
    parser.add_argument("--backtest", action="store_true",
                        help="Run historical backtest instead of live screen")
    parser.add_argument("--backtest-years", type=int, default=4,
                        help="Years to backtest (default: 4)")
    args = parser.parse_args()

    if args.backtest:
        setup_logging(args.verbose)
        from backtest.engine import run_backtest
        run_backtest(years=args.backtest_years,
                     include_financials=args.include_financials,
                     verbose=args.verbose)
    else:
        run_screener(ticker=args.ticker, top_n=args.top, verbose=args.verbose,
                     refresh=args.refresh, wide=args.wide, breakdown=args.breakdown,
                     include_financials=args.include_financials)


if __name__ == "__main__":
    main()
