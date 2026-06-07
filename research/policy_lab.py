"""Policy lab for testing portfolio construction rules.

The goal of this module is not to discover a perfectly tuned rule on the current
sample. It is a small, repeatable harness for comparing pre-declared rules
against the equal-weight universe benchmark with visible uncertainty.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Callable

from backtest.engine import FullQuarterSnapshot, StockDetail
from backtest.stats import AlphaStats, alpha_stats


@dataclass(frozen=True)
class Policy:
    """A portfolio construction rule."""

    name: str
    description: str
    selector: Callable[[FullQuarterSnapshot], list[str]]


@dataclass(frozen=True)
class PolicyQuarter:
    """One quarter of policy results."""

    date: date
    next_date: date
    picks: list[str]
    portfolio_return: float
    universe_return: float
    excess_return: float
    turnover: float | None
    unknown_sector_picks: int
    unknown_sector_pick_rate: float


@dataclass(frozen=True)
class PolicyResult:
    """Aggregate result for a policy."""

    policy: Policy
    quarters: list[PolicyQuarter]
    alpha: AlphaStats
    total_return: float
    universe_total_return: float
    cagr: float
    universe_cagr: float
    cagr_alpha: float
    max_drawdown: float
    hit_rate: float
    avg_picks: float
    avg_turnover: float
    avg_unknown_sector_picks: float
    avg_unknown_sector_pick_rate: float


def default_policies() -> list[Policy]:
    """Return pre-declared policies to evaluate.

    These are intentionally coarse. If a rule needs precise weights to look
    good, it is probably a backtest artifact.
    """
    return [
        Policy(
            name="current_cb",
            description="Current production RESEARCH CANDIDATE list after gates.",
            selector=lambda snap: [
                sd.ticker
                for sd in sorted(snap.stock_details, key=_conviction_key, reverse=True)
                if sd.final_classification == "RESEARCH CANDIDATE"
            ],
        ),
        Policy(
            name="raw_vq_no_gates",
            description="Raw V>=70 and Q>=70 before F-score, revenue, and momentum gates.",
            selector=lambda snap: [
                sd.ticker
                for sd in sorted(snap.stock_details, key=_conviction_key, reverse=True)
                if sd.raw_classification == "RESEARCH CANDIDATE"
            ],
        ),
        Policy(
            name="diversified_vq_top30",
            description="Top 30 by min(Value, Quality), requiring both scores >= 60.",
            selector=lambda snap: _top_n(
                snap.stock_details,
                n=30,
                score_fn=lambda sd: min(sd.value_score, sd.quality_score),
                predicate=lambda sd: sd.value_score >= 60 and sd.quality_score >= 60,
            ),
        ),
        Policy(
            name="vq_momentum_top30",
            description="Top 30 by V/Q plus positive 12-1 momentum; no F-score hard gate.",
            selector=lambda snap: _top_n(
                snap.stock_details,
                n=30,
                score_fn=lambda sd: _vq_momentum_score(sd),
                predicate=lambda sd: (
                    sd.value_score >= 55
                    and sd.quality_score >= 55
                    and (sd.momentum_pct is None or sd.momentum_pct >= 40)
                ),
            ),
        ),
        Policy(
            name="sector_capped_vq_mom",
            description="Same V/Q/momentum score, 30 names, max 5 per sector.",
            selector=lambda snap: _sector_capped_top_n(
                snap.stock_details,
                n=30,
                max_per_sector=5,
                score_fn=lambda sd: _vq_momentum_score(sd),
                predicate=lambda sd: (
                    sd.value_score >= 55
                    and sd.quality_score >= 55
                    and (sd.momentum_pct is None or sd.momentum_pct >= 40)
                ),
            ),
        ),
    ]


def evaluate_policy(
    policy: Policy,
    snapshots: list[tuple[FullQuarterSnapshot, date]],
    returns_by_quarter: dict[tuple[date, date], dict[str, float]],
    *,
    num_tests: int = 1,
) -> PolicyResult:
    """Evaluate one policy from snapshots and per-stock returns."""
    quarters: list[PolicyQuarter] = []
    portfolio_value = 1.0
    universe_value = 1.0
    value_path = [portfolio_value]
    prev_picks: set[str] | None = None
    turnovers: list[float] = []

    for snapshot, next_date in snapshots:
        returns = returns_by_quarter.get((snapshot.date, next_date), {})
        universe_returns = [
            returns[sd.ticker]
            for sd in snapshot.stock_details
            if sd.ticker in returns
        ]
        if not universe_returns:
            continue

        picks = [t for t in policy.selector(snapshot) if t in returns]
        pick_returns = [returns[t] for t in picks]
        portfolio_return = sum(pick_returns) / len(pick_returns) if pick_returns else 0.0
        universe_return = sum(universe_returns) / len(universe_returns)
        details_by_ticker = {sd.ticker: sd for sd in snapshot.stock_details}
        unknown_sector_picks = sum(
            1
            for ticker in picks
            if _is_unknown_sector(details_by_ticker[ticker].sector)
        )
        unknown_sector_pick_rate = unknown_sector_picks / len(picks) if picks else 0.0

        current = set(picks)
        turnover = None
        if prev_picks is not None:
            denom = len(prev_picks | current)
            turnover = len(prev_picks ^ current) / denom if denom else 0.0
            turnovers.append(turnover)
        prev_picks = current

        portfolio_value *= 1.0 + portfolio_return
        universe_value *= 1.0 + universe_return
        value_path.append(portfolio_value)

        quarters.append(
            PolicyQuarter(
                date=snapshot.date,
                next_date=next_date,
                picks=picks,
                portfolio_return=portfolio_return,
                universe_return=universe_return,
                excess_return=portfolio_return - universe_return,
                turnover=turnover,
                unknown_sector_picks=unknown_sector_picks,
                unknown_sector_pick_rate=unknown_sector_pick_rate,
            )
        )

    if len(quarters) < 2:
        raise ValueError(f"Policy {policy.name} produced too few quarters")

    excess = [q.excess_return for q in quarters]
    years = len(quarters) / 4.0

    return PolicyResult(
        policy=policy,
        quarters=quarters,
        alpha=alpha_stats(excess, num_tests=num_tests),
        total_return=portfolio_value - 1.0,
        universe_total_return=universe_value - 1.0,
        cagr=_cagr(portfolio_value, years),
        universe_cagr=_cagr(universe_value, years),
        cagr_alpha=_cagr(portfolio_value, years) - _cagr(universe_value, years),
        max_drawdown=_max_drawdown(value_path),
        hit_rate=sum(1 for q in quarters if q.excess_return > 0) / len(quarters),
        avg_picks=sum(len(q.picks) for q in quarters) / len(quarters),
        avg_turnover=sum(turnovers) / len(turnovers) if turnovers else 0.0,
        avg_unknown_sector_picks=sum(q.unknown_sector_picks for q in quarters) / len(quarters),
        avg_unknown_sector_pick_rate=sum(q.unknown_sector_pick_rate for q in quarters) / len(quarters),
    )


def evaluate_policies(
    policies: list[Policy],
    snapshots: list[tuple[FullQuarterSnapshot, date]],
    returns_by_quarter: dict[tuple[date, date], dict[str, float]],
) -> list[PolicyResult]:
    """Evaluate policies as one multiple-test family."""
    return [
        evaluate_policy(
            policy,
            snapshots,
            returns_by_quarter,
            num_tests=len(policies),
        )
        for policy in policies
    ]


def capital_ready(result: PolicyResult) -> tuple[bool, list[str]]:
    """Return whether a result clears a deliberately strict capital-readiness bar."""
    reasons: list[str] = []
    if result.alpha.n < 30:
        reasons.append(f"only {result.alpha.n} quarters; need 30+")
    if not result.alpha.bonferroni_significant:
        reasons.append("excess return is not Bonferroni-significant")
    if result.cagr_alpha < 0.03:
        reasons.append(f"CAGR alpha {result.cagr_alpha * 100:+.1f}% is below +3.0%")
    if result.hit_rate < 0.55:
        reasons.append(f"hit rate {result.hit_rate * 100:.0f}% is below 55%")
    if result.avg_picks < 25:
        reasons.append(f"average picks {result.avg_picks:.1f} is below 25")
    return (not reasons, reasons)


def _top_n(
    details: list[StockDetail],
    *,
    n: int,
    score_fn: Callable[[StockDetail], float],
    predicate: Callable[[StockDetail], bool],
) -> list[str]:
    ranked = sorted(
        (sd for sd in details if predicate(sd)),
        key=score_fn,
        reverse=True,
    )
    return [sd.ticker for sd in ranked[:n]]


def _sector_capped_top_n(
    details: list[StockDetail],
    *,
    n: int,
    max_per_sector: int,
    score_fn: Callable[[StockDetail], float],
    predicate: Callable[[StockDetail], bool],
) -> list[str]:
    ranked = sorted(
        (sd for sd in details if predicate(sd)),
        key=score_fn,
        reverse=True,
    )
    counts: dict[str, int] = {}
    picks: list[str] = []
    for sd in ranked:
        sector = sd.sector or "Unknown"
        if counts.get(sector, 0) >= max_per_sector:
            continue
        picks.append(sd.ticker)
        counts[sector] = counts.get(sector, 0) + 1
        if len(picks) >= n:
            break
    return picks


def _vq_momentum_score(sd: StockDetail) -> float:
    momentum = sd.momentum_pct if sd.momentum_pct is not None else 50.0
    balance = min(sd.value_score, sd.quality_score)
    return 0.35 * sd.value_score + 0.30 * sd.quality_score + 0.20 * momentum + 0.15 * balance


def _is_unknown_sector(sector: object) -> bool:
    if sector is None:
        return True
    return str(sector).strip().lower() in {"", "unknown", "nan", "none", "null", "n/a"}


def _conviction_key(sd: StockDetail) -> tuple[float, float, str]:
    return (sd.conviction_score, sd.momentum_pct or 0.0, sd.ticker)


def _cagr(final_value: float, years: float) -> float:
    if years <= 0 or final_value <= 0:
        return 0.0
    return final_value ** (1.0 / years) - 1.0


def _max_drawdown(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    peak = values[0]
    max_dd = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)
    return -max_dd
