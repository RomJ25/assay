"""Case study analysis engine — full classification replay and component effectiveness tests."""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from datetime import date

from backtest.cache import HistoricalCache
from backtest.engine import (
    FullQuarterSnapshot,
    StockDetail,
    _compute_backtest_momentum,
    _screen_quarter_full,
)

logger = logging.getLogger(__name__)


# ── Data structures ────────────────────────────────────────────────────────


@dataclass
class BucketStats:
    bucket: str
    n: int
    mean_return: float
    median_return: float
    pct_positive: float
    individual_returns: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class QuarterAnalysis:
    """Full analysis for one quarter: snapshot + returns."""
    snapshot: FullQuarterSnapshot
    next_date: date
    bucket_stats: dict[str, BucketStats]
    spy_return: float | None
    universe_mean: float | None


# ── Core replay ────────────────────────────────────────────────────────────


def replay_screen_at_date(
    rebal_date: date,
    cache: HistoricalCache,
    exclude_financials: bool = True,
) -> FullQuarterSnapshot | None:
    """Replay the full screener at a historical date using cached data.

    Returns FullQuarterSnapshot with all stocks' classifications and gate tracking.
    """
    sp500 = cache.get_sp500()
    if not sp500:
        logger.error("No S&P 500 data in cache")
        return None

    info = {e["ticker"]: e for e in sp500}
    tickers = list(info.keys())

    return _screen_quarter_full(rebal_date, tickers, info, cache, exclude_financials, verbose=False)


# ── Return computation ─────────────────────────────────────────────────────


def compute_stock_returns(
    tickers: list[str],
    start_date: date,
    end_date: date,
    cache: HistoricalCache,
) -> dict[str, float]:
    """Compute per-stock returns between two dates using cached prices."""
    returns = {}
    for ticker in tickers:
        start_data = cache.get_price(ticker, start_date.isoformat())
        end_data = cache.get_price(ticker, end_date.isoformat())
        if start_data is None or end_data is None:
            continue
        _, adj_start = start_data
        _, adj_end = end_data
        if adj_start > 0:
            returns[ticker] = (adj_end - adj_start) / adj_start
    return returns


def compute_stock_returns_from_event_prices(
    tickers: list[str],
    start_date_str: str,
    end_date_str: str,
    event_prices: dict[str, dict[str, tuple[float, float]]],
) -> dict[str, float]:
    """Compute per-stock returns from event price data."""
    returns = {}
    for ticker in tickers:
        prices = event_prices.get(ticker)
        if not prices:
            continue
        start_price = prices.get(start_date_str)
        end_price = prices.get(end_date_str)
        if start_price is None or end_price is None:
            continue
        _, adj_start = start_price
        _, adj_end = end_price
        if adj_start > 0:
            returns[ticker] = (adj_end - adj_start) / adj_start
    return returns


# ── Test 1: Classification gradient ────────────────────────────────────────


BUCKET_ORDER = [
    "CONVICTION BUY", "QUALITY GROWTH PREMIUM", "WATCH LIST",
    "HOLD", "OVERVALUED QUALITY", "OVERVALUED", "VALUE TRAP", "AVOID",
]


def compute_bucket_returns(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
) -> dict[str, BucketStats]:
    """Compute per-bucket return statistics."""
    bucket_rets: dict[str, list[tuple[str, float]]] = {}

    for sd in snapshot.stock_details:
        ret = returns.get(sd.ticker)
        if ret is None:
            continue
        bucket = sd.final_classification
        if bucket not in bucket_rets:
            bucket_rets[bucket] = []
        bucket_rets[bucket].append((sd.ticker, ret))

    stats = {}
    for bucket in BUCKET_ORDER:
        items = bucket_rets.get(bucket, [])
        if not items:
            stats[bucket] = BucketStats(bucket=bucket, n=0, mean_return=0, median_return=0, pct_positive=0)
            continue
        rets = [r for _, r in items]
        stats[bucket] = BucketStats(
            bucket=bucket,
            n=len(rets),
            mean_return=sum(rets) / len(rets),
            median_return=statistics.median(rets),
            pct_positive=sum(1 for r in rets if r > 0) / len(rets) * 100,
            individual_returns=items,
        )

    return stats


def test_gradient_monotonicity(bucket_stats: dict[str, BucketStats]) -> dict:
    """Check if CB > WL > HOLD > AVOID ordering holds."""
    key_buckets = ["CONVICTION BUY", "WATCH LIST", "HOLD", "AVOID"]
    returns = {}
    for b in key_buckets:
        s = bucket_stats.get(b)
        returns[b] = s.mean_return if s and s.n > 0 else None

    cb = returns.get("CONVICTION BUY")
    wl = returns.get("WATCH LIST")
    hold = returns.get("HOLD")
    avoid = returns.get("AVOID")

    monotonic = (
        cb is not None and avoid is not None
        and cb > (wl or float("-inf"))
        and (wl or float("-inf")) > (hold or float("-inf"))
        and (hold or float("-inf")) > (avoid or float("-inf"))
    )

    cb_beat_avoid = cb is not None and avoid is not None and cb > avoid

    return {
        "monotonic": monotonic,
        "cb_beat_avoid": cb_beat_avoid,
        "cb_return": cb,
        "wl_return": wl,
        "hold_return": hold,
        "avoid_return": avoid,
        "cb_vs_avoid_spread": (cb - avoid) if cb is not None and avoid is not None else None,
    }


# ── Test 2 & 3: Gate effectiveness ────────────────────────────────────────


def test_gate_effectiveness(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
    gate: str,  # "f_gate" or "momentum_gate"
) -> dict:
    """Compare returns of gate survivors vs gate victims."""
    survivors = []
    victims = []

    for sd in snapshot.stock_details:
        ret = returns.get(sd.ticker)
        if ret is None:
            continue

        if gate == "f_gate":
            if sd.final_classification == "CONVICTION BUY":
                survivors.append((sd.ticker, ret))
            elif sd.f_gate_fired:
                victims.append((sd.ticker, ret, sd.value_score, sd.quality_score, sd.piotroski_f))
        elif gate == "momentum_gate":
            if sd.final_classification == "CONVICTION BUY":
                survivors.append((sd.ticker, ret))
            elif sd.momentum_gate_fired:
                victims.append((sd.ticker, ret, sd.value_score, sd.quality_score, sd.piotroski_f))

    surv_mean = sum(r for _, r in survivors) / len(survivors) if survivors else None
    vict_rets = [r for _, r, *_ in victims]
    vict_mean = sum(vict_rets) / len(vict_rets) if vict_rets else None

    return {
        "gate": gate,
        "n_survivors": len(survivors),
        "n_victims": len(victims),
        "survivor_mean": surv_mean,
        "victim_mean": vict_mean,
        "delta": (vict_mean - surv_mean) if surv_mean is not None and vict_mean is not None else None,
        "victim_details": [(t, r) for t, r, *_ in victims],
    }


# ── Test 4: Confidence gradient ───────────────────────────────────────────


def test_confidence_gradient(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
) -> dict:
    """Test if HIGH > MODERATE > LOW within CONVICTION BUY."""
    tiers: dict[str, list[float]] = {"HIGH": [], "MODERATE": [], "LOW": []}

    for sd in snapshot.stock_details:
        if sd.final_classification != "CONVICTION BUY":
            continue
        ret = returns.get(sd.ticker)
        if ret is None or sd.confidence is None:
            continue
        tiers[sd.confidence].append(ret)

    result = {}
    for tier in ["HIGH", "MODERATE", "LOW"]:
        rets = tiers[tier]
        result[tier] = {
            "n": len(rets),
            "mean": sum(rets) / len(rets) if rets else None,
        }

    h = result["HIGH"]["mean"]
    m = result["MODERATE"]["mean"]
    low = result["LOW"]["mean"]

    monotonic = (
        h is not None and m is not None and low is not None
        and h > m > low
    )

    return {"tiers": result, "monotonic": monotonic}


# ── Test 5: VALUE TRAP validation ─────────────────────────────────────────


def test_value_traps(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
) -> dict:
    """Compare VALUE TRAP returns to CB and universe."""
    vt_rets = []
    cb_rets = []
    all_rets = []

    for sd in snapshot.stock_details:
        ret = returns.get(sd.ticker)
        if ret is None:
            continue
        all_rets.append(ret)
        if sd.final_classification == "VALUE TRAP":
            vt_rets.append((sd.ticker, ret, sd.sector))
        elif sd.final_classification == "CONVICTION BUY":
            cb_rets.append(ret)

    vt_mean = sum(r for _, r, _ in vt_rets) / len(vt_rets) if vt_rets else None
    cb_mean = sum(cb_rets) / len(cb_rets) if cb_rets else None
    univ_mean = sum(all_rets) / len(all_rets) if all_rets else None

    return {
        "n_traps": len(vt_rets),
        "vt_mean": vt_mean,
        "cb_mean": cb_mean,
        "universe_mean": univ_mean,
        "vt_vs_cb": (vt_mean - cb_mean) if vt_mean is not None and cb_mean is not None else None,
        "traps_underperform": vt_mean is not None and cb_mean is not None and vt_mean < cb_mean,
    }


# ── Test 7: Asymmetry ────────────────────────────────────────────────────


def test_asymmetry(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
    universe_mean: float,
) -> list[dict]:
    """Compute per-stock excess returns for CB picks over universe mean."""
    excess = []
    for sd in snapshot.stock_details:
        if sd.final_classification != "CONVICTION BUY":
            continue
        ret = returns.get(sd.ticker)
        if ret is None:
            continue
        excess.append({
            "ticker": sd.ticker,
            "return": ret,
            "excess": ret - universe_mean,
        })
    return excess


# ── Test 8: Sector-neutralized returns ────────────────────────────────────


def test_sector_neutralized(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
) -> dict:
    """Compare CB picks to their own sector mean (not universe mean)."""
    # Compute sector means
    sector_rets: dict[str, list[float]] = {}
    for sd in snapshot.stock_details:
        ret = returns.get(sd.ticker)
        if ret is None:
            continue
        if sd.sector not in sector_rets:
            sector_rets[sd.sector] = []
        sector_rets[sd.sector].append(ret)

    sector_means = {s: sum(r) / len(r) for s, r in sector_rets.items() if r}

    # Compute sector-neutralized excess for CB picks
    cb_excess = []
    for sd in snapshot.stock_details:
        if sd.final_classification != "CONVICTION BUY":
            continue
        ret = returns.get(sd.ticker)
        if ret is None:
            continue
        sector_mean = sector_means.get(sd.sector)
        if sector_mean is None:
            continue
        cb_excess.append({
            "ticker": sd.ticker,
            "sector": sd.sector,
            "return": ret,
            "sector_mean": sector_mean,
            "excess_vs_sector": ret - sector_mean,
        })

    if not cb_excess:
        return {"n": 0, "mean_excess_vs_sector": None}

    mean_excess = sum(e["excess_vs_sector"] for e in cb_excess) / len(cb_excess)
    return {
        "n": len(cb_excess),
        "mean_excess_vs_sector": mean_excess,
        "stock_selection_positive": mean_excess > 0,
        "details": cb_excess,
    }


# ── Test 9: Repeat-pick persistence ──────────────────────────────────────


def test_repeat_picks(
    snapshots_with_returns: list[tuple[FullQuarterSnapshot, dict[str, float]]],
) -> dict:
    """Compare returns of repeat picks vs new entries across quarters."""
    prev_cb = set()
    returning_rets = []
    new_rets = []

    for snapshot, returns in snapshots_with_returns:
        current_cb = set()
        for sd in snapshot.stock_details:
            if sd.final_classification != "CONVICTION BUY":
                continue
            current_cb.add(sd.ticker)
            ret = returns.get(sd.ticker)
            if ret is None:
                continue
            if sd.ticker in prev_cb:
                returning_rets.append(ret)
            else:
                new_rets.append(ret)
        prev_cb = current_cb

    ret_mean = sum(returning_rets) / len(returning_rets) if returning_rets else None
    new_mean = sum(new_rets) / len(new_rets) if new_rets else None

    return {
        "n_returning": len(returning_rets),
        "n_new": len(new_rets),
        "returning_mean": ret_mean,
        "new_mean": new_mean,
        "delta": (ret_mean - new_mean) if ret_mean is not None and new_mean is not None else None,
    }


# ── Test 10: Conviction ordering ─────────────────────────────────────────


def test_conviction_ordering(
    snapshot: FullQuarterSnapshot,
    returns: dict[str, float],
) -> dict:
    """Test if higher conviction_score predicts higher returns within CB."""
    pairs = []
    for sd in snapshot.stock_details:
        if sd.final_classification != "CONVICTION BUY":
            continue
        ret = returns.get(sd.ticker)
        if ret is None:
            continue
        pairs.append((sd.conviction_score, ret))

    if len(pairs) < 3:
        return {"n": len(pairs), "rank_correlation": None, "insufficient_data": True}

    # Kendall's tau-a: count concordant vs discordant pairs over ALL pairs
    concordant = 0
    discordant = 0
    n = len(pairs)
    for i in range(n):
        for j in range(i + 1, n):
            conv_diff = pairs[i][0] - pairs[j][0]
            ret_diff = pairs[i][1] - pairs[j][1]
            if conv_diff * ret_diff > 0:
                concordant += 1
            elif conv_diff * ret_diff < 0:
                discordant += 1

    total_pairs = n * (n - 1) // 2  # C(n, 2) — all possible pairs
    tau = (concordant - discordant) / total_pairs if total_pairs > 0 else 0

    return {
        "n": len(pairs),
        "kendall_tau": round(tau, 3),
        "concordant": concordant,
        "discordant": discordant,
        "positive_correlation": tau > 0,
        "insufficient_data": False,
    }
