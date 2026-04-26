"""Momentum scoring and gate — 12-1 month price momentum.

Based on Jegadeesh & Titman (1993): 12-month lookback, skip most recent
month to avoid short-term reversal noise. Used as a NEGATIVE FILTER, not
a scoring dimension — Research Affiliates (2024) showed +2.8%/yr improvement
from excluding bottom-quartile momentum in a 32-year long-only study.
"""

from __future__ import annotations

from config import MOMENTUM_GATE_PERCENTILE


def compute_momentum(price_histories: dict[str, list[float]]) -> dict[str, float]:
    """Compute 12-1 month momentum for each ticker.

    Args:
        price_histories: {ticker: [price_12m_ago, price_11m_ago, ..., price_1m_ago, price_now]}
                         List of ~13 monthly prices, oldest first.

    Returns:
        {ticker: momentum_return} as a decimal (0.10 = +10%).
    """
    results = {}
    for ticker, prices in price_histories.items():
        if len(prices) < 2:
            continue
        # Skip the most recent month: use prices[0] (12m ago) to prices[-2] (1m ago)
        start = prices[0]
        end = prices[-2] if len(prices) >= 13 else prices[-1]
        if start is not None and end is not None and start > 0:
            results[ticker] = (end - start) / start
    return results


def compute_momentum_percentiles(momentum: dict[str, float]) -> dict[str, float]:
    """Rank momentum values as percentiles (0-100)."""
    if not momentum:
        return {}
    sorted_tickers = sorted(momentum, key=momentum.get)
    n = len(sorted_tickers)
    return {t: (i + 1) / n * 100 for i, t in enumerate(sorted_tickers)}


def apply_momentum_gate(classification: str, momentum_percentile: float | None) -> str:
    """Downgrade RESEARCH CANDIDATE to WATCH LIST if momentum is in bottom quartile.

    Research Affiliates (2024): excluding bottom-quartile momentum from value
    picks improved returns by +2.8%/yr over 32 years (long-only, US large-cap).
    """
    if classification != "RESEARCH CANDIDATE":
        return classification
    if momentum_percentile is None:
        return classification
    if momentum_percentile <= MOMENTUM_GATE_PERCENTILE:
        return "WATCH LIST"
    return classification
