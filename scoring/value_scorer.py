"""Value scoring via Earnings Yield (EBIT/EV) percentile ranking.

Based on Tobias Carlisle's Acquirer's Multiple research:
17.9% CAGR over 44 years (1973-2017) using just EV/EBIT ranking.

No assumptions about growth, WACC, or terminal value — uses actual
reported operating income relative to total enterprise cost.
"""

from __future__ import annotations

from data.providers.base import FinancialData


def compute_value_scores(all_data: dict[str, FinancialData]) -> dict[str, float]:
    """Rank all stocks by earnings yield. Highest yield = score 100, lowest = 0.

    Earnings Yield = Operating Income (EBIT) / Enterprise Value
    Higher yield = cheaper stock = better value

    Also computes FCF Yield as secondary signal.
    """
    earnings_yields = {}
    fcf_yields = {}

    for ticker, fd in all_data.items():
        oi = fd.get("operating_income", 0)
        fcf = fd.get("free_cash_flow", 0)

        # Enterprise Value: use Yahoo's if available, else compute from components
        ev = fd.enterprise_value
        if not ev or ev <= 0:
            debt = fd.get("total_debt", 0) or 0
            cash = fd.get("cash_and_equivalents", 0) or 0
            if fd.market_cap > 0:
                ev = fd.market_cap + debt - cash

        if oi and oi > 0 and ev and ev > 0:
            earnings_yields[ticker] = oi / ev
        elif fd.trailing_pe and fd.trailing_pe > 0:
            # Fallback for financials: banks don't report Operating Income,
            # so use 1/PE (net earnings yield) as proxy
            earnings_yields[ticker] = 1.0 / fd.trailing_pe

        if fcf and fcf > 0 and ev and ev > 0:
            fcf_yields[ticker] = fcf / ev

    if not earnings_yields:
        return {}

    # Percentile rank by earnings yield (highest = best)
    sorted_by_ey = sorted(earnings_yields, key=earnings_yields.get, reverse=True)
    n = len(sorted_by_ey)
    ey_ranks = {t: (n - i) / n * 100 for i, t in enumerate(sorted_by_ey)}

    # Percentile rank by FCF yield
    sorted_by_fcf = sorted(fcf_yields, key=fcf_yields.get, reverse=True)
    m = len(sorted_by_fcf)
    fcf_ranks = {t: (m - i) / m * 100 for i, t in enumerate(sorted_by_fcf)}

    # Composite: 70% earnings yield rank + 30% FCF yield rank
    scores = {}
    for ticker in earnings_yields:
        ey_score = ey_ranks.get(ticker, 50)
        fcf_score = fcf_ranks.get(ticker, 50)
        scores[ticker] = round(0.7 * ey_score + 0.3 * fcf_score, 1)

    return scores


def get_yield_metrics(fd: FinancialData) -> dict:
    """Get the actual yield values for display (not ranking)."""
    oi = fd.get("operating_income", 0)
    ev = fd.enterprise_value
    fcf = fd.get("free_cash_flow", 0)
    mktcap = fd.market_cap

    if not ev or ev <= 0:
        debt = fd.get("total_debt", 0) or 0
        cash = fd.get("cash_and_equivalents", 0) or 0
        if mktcap > 0:
            ev = mktcap + debt - cash

    return {
        "earnings_yield": (oi / ev * 100) if oi and ev and ev > 0 else None,
        "fcf_yield": (fcf / ev * 100) if fcf and ev and ev > 0 else None,
        "fcf_yield_mktcap": (fcf / mktcap * 100) if fcf and mktcap and mktcap > 0 else None,
    }
