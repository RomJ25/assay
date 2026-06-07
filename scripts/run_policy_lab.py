#!/usr/bin/env python3
"""Run exploratory portfolio-policy tests.

This is a research harness, not a parameter optimizer. The policies are
pre-declared in research/policy_lab.py and reported with uncertainty bands.
Any attractive result here still needs a longer, point-in-time data set and
future walk-forward validation before capital deployment.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from dateutil.relativedelta import relativedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backtest.cache import HistoricalCache  # noqa: E402
from backtest.engine import _generate_rebalance_dates, _screen_quarter_full  # noqa: E402
from backtest.historical_fetcher import fetch_historical_data  # noqa: E402
from data.sp500_historical import get_all_historical_tickers  # noqa: E402
from data.universe import (  # noqa: E402
    _enrich_info_with_sector_profiles,
    _get_r1000_cache,
    _is_unknown,
    _set_r1000_cache,
    get_universe,
)
from research.policy_lab import capital_ready, default_policies, evaluate_policies  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Assay policy lab")
    parser.add_argument("--years", type=int, default=4, help="Backtest years, default 4")
    parser.add_argument("--universe", default="sp500", help="sp500 or russell1000")
    parser.add_argument("--output-dir", default="results", help="Directory for CSV output")
    parser.add_argument("--no-write", action="store_true", help="Print only, do not write CSV")
    parser.add_argument(
        "--refresh-universe",
        action="store_true",
        help="For russell1000, rebuild the current proxy instead of using the cached proxy",
    )
    parser.add_argument(
        "--skip-sector-enrichment",
        action="store_true",
        help="For russell1000, skip Yahoo profile sector enrichment",
    )
    args = parser.parse_args()

    universe = get_universe(args.universe)
    rebalance_dates = _generate_rebalance_dates(args.years)
    if len(rebalance_dates) < 3:
        raise SystemExit("Need at least 3 rebalance dates")

    print(f"\nAssay Policy Lab - {universe.description}")
    print(f"Period: {rebalance_dates[0]} to {rebalance_dates[-1]} ({len(rebalance_dates) - 1} return quarters)")
    print("Mode: point-in-time membership when available; exploratory, not capital-ready.\n")

    tickers, info = fetch_policy_universe(
        args.universe,
        universe,
        refresh_universe=args.refresh_universe,
        skip_sector_enrichment=args.skip_sector_enrichment,
    )
    if args.universe == "sp500":
        historical = get_all_historical_tickers(rebalance_dates[0], rebalance_dates[-1])
        tickers = sorted(historical | set(info.keys()))
        for ticker in tickers:
            info.setdefault(ticker, {"company_name": ticker, "sector": "Unknown", "sub_industry": "Unknown"})

    sp_entries = [
        {
            "ticker": ticker,
            "company_name": row.get("company_name", ticker),
            "sector": row.get("sector", "Unknown"),
            "sub_industry": row.get("sub_industry", "Unknown"),
        }
        for ticker, row in info.items()
    ]

    price_dates = set(rebalance_dates)
    for d in rebalance_dates:
        price_dates.add(d - relativedelta(months=12))
        price_dates.add(d - relativedelta(months=1))

    cache = HistoricalCache()
    try:
        fetch_historical_data(tickers, sp_entries, cache, sorted(price_dates))

        snapshots = []
        returns_by_quarter = {}
        usable_rebalance_dates = rebalance_dates[:-1]
        for rebal_date, next_date in zip(rebalance_dates, rebalance_dates[1:]):
            if universe.historical:
                pit_tickers = sorted(universe.historical(rebal_date))
                pit_info = {
                    ticker: info.get(ticker, {"company_name": ticker, "sector": "Unknown", "sub_industry": "Unknown"})
                    for ticker in pit_tickers
                }
                if args.universe == "russell1000" and not args.skip_sector_enrichment:
                    enriched = _enrich_info_with_sector_profiles(pit_info, pit_tickers)
                    if enriched:
                        info.update({ticker: pit_info[ticker] for ticker in pit_tickers if ticker in pit_info})
            else:
                pit_tickers = tickers
                pit_info = info

            snapshot = _screen_quarter_full(
                rebal_date,
                pit_tickers,
                pit_info,
                cache,
                exclude_financials=True,
                verbose=False,
            )
            if snapshot is None:
                print(f"  {rebal_date}: skipped, no snapshot")
                continue
            snapshots.append((snapshot, next_date))
            unknown_sector = sum(1 for sd in snapshot.stock_details if _is_unknown(sd.sector))

            quarter_returns = {}
            for sd in snapshot.stock_details:
                ret = _ticker_return(sd.ticker, rebal_date, next_date, cache)
                if ret is not None:
                    quarter_returns[sd.ticker] = ret
            returns_by_quarter[(rebal_date, next_date)] = quarter_returns
            print(
                f"  {rebal_date}: {snapshot.num_screened} screened, "
                f"{snapshot.classifications.get('RESEARCH CANDIDATE', 0)} current CB, "
                f"{unknown_sector} unknown sector, "
                f"{len(quarter_returns)} returnable"
            )

        policies = default_policies()
        results = evaluate_policies(policies, snapshots, returns_by_quarter)
    finally:
        cache.close()

    print_results(results)

    if not args.no_write:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"policy_lab_{args.universe}_{date.today().isoformat()}.csv"
        write_results_csv(results, out_path)
        print(f"\nCSV saved to {out_path}")

    print("\nCapital rule: if every policy says NOT READY, do not put serious money behind it.")
    return 0


def fetch_policy_universe(universe_name, universe, *, refresh_universe: bool, skip_sector_enrichment: bool):
    """Fetch a universe for research without forcing slow Russell rebuilds."""
    if universe_name != "russell1000":
        return universe.fetch()

    if not refresh_universe:
        cached = _get_r1000_cache(max_age_hours=None)
        if cached is not None:
            tickers, info = cached
            print(
                f"Using cached Russell 1000 proxy ({len(tickers)} tickers). "
                "Pass --refresh-universe to rebuild membership."
            )
            if not skip_sector_enrichment:
                enriched = _enrich_info_with_sector_profiles(info, tickers)
                if enriched:
                    _set_r1000_cache(tickers, info)
                    print(f"Enriched sector metadata for {enriched} cached Russell names.")
            return tickers, info

    tickers, info = universe.fetch()
    if not skip_sector_enrichment:
        enriched = _enrich_info_with_sector_profiles(info, tickers)
        if enriched:
            _set_r1000_cache(tickers, info)
            print(f"Enriched sector metadata for {enriched} Russell names.")
    return tickers, info


def print_results(results) -> None:
    print("\nPolicy results vs equal-weight screened universe")
    print(
        f"{'Policy':<24} {'CAGR':>8} {'EW':>8} {'Alpha':>8} {'AnnMean':>9} "
        f"{'CI low':>9} {'CI high':>9} {'t':>6} {'Hit':>6} {'Picks':>7} {'Turn':>7} {'Ready':>8}"
    )
    print("-" * 124)
    for result in results:
        ready, reasons = capital_ready(result)
        print(
            f"{result.policy.name:<24} "
            f"{result.cagr * 100:>7.2f}% "
            f"{result.universe_cagr * 100:>7.2f}% "
            f"{result.cagr_alpha * 100:>+7.2f}% "
            f"{result.alpha.mean * 4 * 100:>+8.2f}% "
            f"{result.alpha.ci_low * 4 * 100:>+8.2f}% "
            f"{result.alpha.ci_high * 4 * 100:>+8.2f}% "
            f"{result.alpha.t_stat:>+5.2f} "
            f"{result.hit_rate * 100:>5.0f}% "
            f"{result.avg_picks:>6.1f} "
            f"{result.avg_turnover * 100:>6.1f}% "
            f"{'YES' if ready else 'NO':>8}"
        )
        if reasons:
            print(f"  -> {result.policy.description}")
            print(f"     Not ready: {'; '.join(reasons)}")


def write_results_csv(results, path: Path) -> None:
    fields = [
        "policy",
        "description",
        "quarters",
        "cagr",
        "universe_cagr",
        "cagr_alpha",
        "annualized_mean_excess",
        "annualized_ci_low",
        "annualized_ci_high",
        "t_stat",
        "raw_significant",
        "bonferroni_significant",
        "hit_rate",
        "avg_picks",
        "avg_turnover",
        "avg_unknown_sector_picks",
        "avg_unknown_sector_pick_rate",
        "capital_ready",
        "not_ready_reasons",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for result in results:
            ready, reasons = capital_ready(result)
            writer.writerow(
                {
                    "policy": result.policy.name,
                    "description": result.policy.description,
                    "quarters": result.alpha.n,
                    "cagr": result.cagr,
                    "universe_cagr": result.universe_cagr,
                    "cagr_alpha": result.cagr_alpha,
                    "annualized_mean_excess": result.alpha.mean * 4,
                    "annualized_ci_low": result.alpha.ci_low * 4,
                    "annualized_ci_high": result.alpha.ci_high * 4,
                    "t_stat": result.alpha.t_stat,
                    "raw_significant": result.alpha.significant_at_05,
                    "bonferroni_significant": result.alpha.bonferroni_significant,
                    "hit_rate": result.hit_rate,
                    "avg_picks": result.avg_picks,
                    "avg_turnover": result.avg_turnover,
                    "avg_unknown_sector_picks": result.avg_unknown_sector_picks,
                    "avg_unknown_sector_pick_rate": result.avg_unknown_sector_pick_rate,
                    "capital_ready": ready,
                    "not_ready_reasons": "; ".join(reasons),
                }
            )


def _ticker_return(ticker: str, start: date, end: date, cache: HistoricalCache) -> float | None:
    start_data = cache.get_price(ticker, start.isoformat())
    if start_data is None:
        return None
    _, adj_start = start_data
    if adj_start <= 0:
        return None

    end_data = cache.get_price(ticker, end.isoformat())
    if end_data is None:
        return 0.0
    _, adj_end = end_data
    return (adj_end - adj_start) / adj_start


if __name__ == "__main__":
    raise SystemExit(main())
