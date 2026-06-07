"""Historical beta computation for backtest snapshots.

The historical-price cache stores prices on quarter-ends + one date per month
preceding each quarter (used for momentum lookback). This means we can compute
quarterly returns reliably back to the cache start date.

Methodology (locked, do not tune post-hoc per audit §6.3 / Experiment E2 risk note):

- **Window:** trailing 20 quarterly returns (5 calendar years).
- **Returns:** log returns of adjusted-close prices on quarter-end dates.
- **Benchmark:** SPY (cap-weighted US large-cap proxy).
- **Estimator:** ordinary least squares — beta = cov(r_t, r_b) / var(r_b).
- **Minimum sample:** 12 quarterly returns (3 years) — below that, return None
  rather than emit a noisy estimate.

This is "quarterly beta," not the academic standard "monthly beta" — forced by
the cache cadence. With 20 observations and a 5-year window, quarterly beta
estimates are noisier but unbiased relative to monthly. For the Safety A/B test
(Experiment E2) the question is comparative: same methodology applied across
all stocks at each rebalance date.
"""

from __future__ import annotations

import math
from datetime import date

from backtest.cache import HistoricalCache

# Lock methodology constants here so the experiment is reproducible.
LOOKBACK_QUARTERS = 20
MIN_OBSERVATIONS = 12
BENCHMARK = "SPY"

# Quarter-end (month, day) tuples that we accept as valid sample points.
_QUARTER_ENDS = {(3, 31), (6, 30), (9, 30), (12, 31)}


def _is_quarter_end(date_str: str) -> bool:
    parts = date_str.split("-")
    if len(parts) != 3:
        return False
    try:
        m, d = int(parts[1]), int(parts[2])
    except ValueError:
        return False
    return (m, d) in _QUARTER_ENDS


# Module-level cache for benchmark series so we don't re-query SQLite for SPY
# once per stock per quarter (8000+ redundant lookups otherwise).
_benchmark_series: dict[str, dict[str, tuple[float, float]]] = {}


def _get_benchmark_series(cache: HistoricalCache, benchmark: str) -> dict[str, tuple[float, float]]:
    if benchmark not in _benchmark_series:
        _benchmark_series[benchmark] = cache.get_prices_for_ticker(benchmark)
    return _benchmark_series[benchmark]


def reset_benchmark_cache() -> None:
    """Clear the module-level benchmark cache (for tests / repeated runs)."""
    _benchmark_series.clear()


def compute_historical_beta(
    ticker: str,
    as_of: date,
    cache: HistoricalCache,
    benchmark: str = BENCHMARK,
    lookback_quarters: int = LOOKBACK_QUARTERS,
    min_observations: int = MIN_OBSERVATIONS,
) -> float | None:
    """Quarterly OLS beta vs benchmark over a trailing window.

    Returns None when fewer than `min_observations` quarterly returns can be
    constructed from cached prices on or before `as_of`.
    """
    bench_prices = _get_benchmark_series(cache, benchmark)
    if not bench_prices:
        return None
    ticker_prices = cache.get_prices_for_ticker(ticker)
    if not ticker_prices:
        return None

    cutoff = as_of.isoformat()
    common_dates = sorted(
        d for d in ticker_prices
        if d in bench_prices and _is_quarter_end(d) and d <= cutoff
    )
    common_dates = common_dates[-(lookback_quarters + 1):]
    if len(common_dates) < min_observations + 1:
        return None

    t_returns: list[float] = []
    b_returns: list[float] = []
    for prev, cur in zip(common_dates[:-1], common_dates[1:]):
        # adj_close at index 1 of the (close, adj_close) tuple
        prev_t = ticker_prices[prev][1]
        cur_t = ticker_prices[cur][1]
        prev_b = bench_prices[prev][1]
        cur_b = bench_prices[cur][1]
        if prev_t is None or cur_t is None or prev_b is None or cur_b is None:
            continue
        if prev_t <= 0 or prev_b <= 0 or cur_t <= 0 or cur_b <= 0:
            continue
        t_returns.append(math.log(cur_t / prev_t))
        b_returns.append(math.log(cur_b / prev_b))

    n = len(b_returns)
    if n < min_observations:
        return None

    mean_b = sum(b_returns) / n
    mean_t = sum(t_returns) / n
    cov = sum((b - mean_b) * (t - mean_t) for b, t in zip(b_returns, t_returns)) / (n - 1)
    var_b = sum((b - mean_b) ** 2 for b in b_returns) / (n - 1)
    if var_b <= 0:
        return None
    return cov / var_b
