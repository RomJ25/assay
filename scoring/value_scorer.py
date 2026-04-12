"""Value scoring via Earnings Yield (EBIT/EV) percentile ranking.

Based on Tobias Carlisle's Acquirer's Multiple research:
17.9% CAGR over 44 years (1973-2017) using just EV/EBIT ranking.

No assumptions about growth, WACC, or terminal value — uses actual
reported operating income relative to total enterprise cost.
"""

from __future__ import annotations

from collections import defaultdict

from config import SECTOR_RELATIVE_BLEND
from data.providers.base import FinancialData

MIN_SECTOR_SIZE = 3  # sectors below this fall back to 100% absolute


def compute_value_scores(
    all_data: dict[str, FinancialData],
    sector_relative: bool = False,
) -> dict[str, float]:
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

        if oi is not None and ev is not None and ev > 0:
            ey = oi / ev
            # ADR currency guard: Yahoo reports financials in local currency
            # (TWD, CNY, DKK) but price/market_cap in USD, making EBIT/EV
            # meaningless. PE is currency-neutral (Yahoo converts EPS for ADRs).
            # If EBIT/EV diverges from 1/PE by >3x, use 1/PE instead.
            if fd.trailing_pe and fd.trailing_pe > 0 and ey > 0:
                pe_yield = 1.0 / fd.trailing_pe
                if ey / pe_yield > 3.0:
                    ey = pe_yield
            earnings_yields[ticker] = ey
        elif fd.trailing_pe and fd.trailing_pe > 0:
            # Fallback for financials: banks don't report Operating Income (oi is None),
            # so use 1/PE (net earnings yield) as proxy
            earnings_yields[ticker] = 1.0 / fd.trailing_pe

        if fcf is not None and ev is not None and ev > 0:
            fcf_y = fcf / ev
            # Same ADR currency guard for FCF yield
            if fd.trailing_pe and fd.trailing_pe > 0 and fcf_y > 0:
                pe_yield = 1.0 / fd.trailing_pe
                if fcf_y / pe_yield > 3.0:
                    fcf_y = pe_yield * 0.8  # FCF typically ~80% of net income
            fcf_yields[ticker] = fcf_y

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
    absolute_scores = {}
    for ticker in earnings_yields:
        ey_score = ey_ranks.get(ticker, 50)
        fcf_score = fcf_ranks.get(ticker, 50)
        absolute_scores[ticker] = round(0.7 * ey_score + 0.3 * fcf_score, 1)

    if not sector_relative:
        return absolute_scores

    # Sector-relative: rank within sector, then blend with absolute
    sector_groups: dict[str, list[str]] = defaultdict(list)
    for ticker in earnings_yields:
        sector = all_data[ticker].sector or "Unknown"
        sector_groups[sector].append(ticker)

    sector_scores: dict[str, float] = {}
    for sector, tickers_in_sector in sector_groups.items():
        if len(tickers_in_sector) < MIN_SECTOR_SIZE:
            # Too few stocks — use absolute score as sector score
            for t in tickers_in_sector:
                sector_scores[t] = absolute_scores[t]
            continue
        sorted_sector = sorted(tickers_in_sector, key=lambda t: earnings_yields[t], reverse=True)
        ns = len(sorted_sector)
        for i, t in enumerate(sorted_sector):
            sector_scores[t] = round((ns - i) / ns * 100, 1)

    blend = SECTOR_RELATIVE_BLEND
    blended = {}
    for ticker in absolute_scores:
        sp = sector_scores.get(ticker, absolute_scores[ticker])
        blended[ticker] = round((1 - blend) * absolute_scores[ticker] + blend * sp, 1)

    return blended


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

    ey = None
    if oi is not None and ev is not None and ev > 0:
        ey = oi / ev * 100
        # ADR currency guard (same logic as scoring)
        if fd.trailing_pe and fd.trailing_pe > 0 and ey > 0:
            pe_yield_pct = 100.0 / fd.trailing_pe
            if ey / pe_yield_pct > 3.0:
                ey = pe_yield_pct
    elif fd.trailing_pe and fd.trailing_pe > 0:
        # Fallback for financials without operating income (same as scoring)
        ey = 100.0 / fd.trailing_pe

    fcf_y = None
    if fcf is not None and ev is not None and ev > 0:
        fcf_y = fcf / ev * 100
        if fd.trailing_pe and fd.trailing_pe > 0 and fcf_y > 0:
            pe_yield_pct = 100.0 / fd.trailing_pe
            if fcf_y / pe_yield_pct > 3.0:
                fcf_y = pe_yield_pct * 0.8

    return {
        "earnings_yield": ey,
        "fcf_yield": fcf_y,
        "fcf_yield_mktcap": (fcf / mktcap * 100) if fcf is not None and mktcap is not None and mktcap > 0 else None,
    }
