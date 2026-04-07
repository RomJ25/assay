"""Trajectory score — fundamental momentum + price momentum tie-breaker.

Captures "improving fundamentals + not collapsing price trend" to reduce
value-trap risk and prioritize improving names within the same conviction bucket.

Not used for ranking or classification — only for ordering within CONVICTION BUY.
"""

from __future__ import annotations

from data.providers.base import FinancialData

# Fundamental trajectory weights (sum to 1.0)
_W_ROA = 0.35
_W_GM = 0.25
_W_LEV = 0.25
_W_SHR = 0.15

# Overall trajectory: fundamental vs price momentum
_W_FUNDAMENTAL = 0.70
_W_MOMENTUM = 0.30

_NEUTRAL = 50.0  # default percentile for missing components


def compute_trajectory_scores(
    all_data: dict[str, FinancialData],
    momentum_pcts: dict[str, float],
) -> dict[str, float]:
    """Compute trajectory scores (0-100) for all stocks.

    Returns {ticker: trajectory_score} where higher = more improving.
    """
    # Step 1: compute raw deltas for each fundamental
    delta_roa: dict[str, float] = {}
    delta_gm: dict[str, float] = {}
    delta_lev: dict[str, float] = {}
    delta_shr: dict[str, float] = {}

    for ticker, fd in all_data.items():
        ni_0 = fd.get("net_income", 0)
        ni_1 = fd.get("net_income", 1)
        a_0 = fd.get("total_assets", 0)
        a_1 = fd.get("total_assets", 1)
        if all(v is not None for v in [ni_0, ni_1, a_0, a_1]) and a_0 > 0 and a_1 > 0:
            delta_roa[ticker] = ni_0 / a_0 - ni_1 / a_1

        gp_0 = fd.get("gross_profit", 0)
        gp_1 = fd.get("gross_profit", 1)
        rev_0 = fd.get("revenue", 0)
        rev_1 = fd.get("revenue", 1)
        if all(v is not None for v in [gp_0, gp_1, rev_0, rev_1]) and rev_0 > 0 and rev_1 > 0:
            delta_gm[ticker] = gp_0 / rev_0 - gp_1 / rev_1

        d_0 = fd.get("total_debt", 0)
        d_1 = fd.get("total_debt", 1)
        if all(v is not None for v in [d_0, d_1, a_0, a_1]) and a_0 > 0 and a_1 > 0:
            # Positive = deleveraging (good)
            delta_lev[ticker] = d_1 / a_1 - d_0 / a_0

        s_0 = fd.get("ordinary_shares_number", 0)
        s_1 = fd.get("ordinary_shares_number", 1)
        if s_0 is not None and s_1 is not None and s_1 > 0:
            # Positive = buybacks (good)
            delta_shr[ticker] = -(s_0 / s_1 - 1)

    # Step 2: percentile-rank each delta (higher = better)
    roa_pcts = _percentile_rank(delta_roa)
    gm_pcts = _percentile_rank(delta_gm)
    lev_pcts = _percentile_rank(delta_lev)
    shr_pcts = _percentile_rank(delta_shr)

    # Step 3: compute trajectory for each stock
    all_tickers = set(all_data.keys())
    scores: dict[str, float] = {}
    for ticker in all_tickers:
        ft = (
            _W_ROA * roa_pcts.get(ticker, _NEUTRAL)
            + _W_GM * gm_pcts.get(ticker, _NEUTRAL)
            + _W_LEV * lev_pcts.get(ticker, _NEUTRAL)
            + _W_SHR * shr_pcts.get(ticker, _NEUTRAL)
        )
        mom = momentum_pcts.get(ticker, _NEUTRAL)
        scores[ticker] = round(_W_FUNDAMENTAL * ft + _W_MOMENTUM * mom, 1)

    return scores


def _percentile_rank(values: dict[str, float]) -> dict[str, float]:
    """Percentile-rank a dict of values (highest = 100)."""
    if not values:
        return {}
    sorted_tickers = sorted(values, key=values.get, reverse=True)
    n = len(sorted_tickers)
    return {t: round((n - i) / n * 100, 1) for i, t in enumerate(sorted_tickers)}
