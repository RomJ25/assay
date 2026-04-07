"""Opportunity Score — definitive ranking that combines all signals.

Synthesizes conviction, trajectory, FCF strength, financial health, and
external validation into a single 0-100 score. Higher = better opportunity.

Components (all 0-100, then weighted):
  40% Conviction Score  — core value x quality signal
  25% Trajectory Score  — fundamental improvement + price momentum
  15% FCF Yield Rank    — cash generation validates the earnings
  10% F-Score Quality   — Piotroski financial health (0-9 normalized)
  10% Analyst Alignment — external validation of the thesis
"""

from __future__ import annotations


def compute_opportunity_scores(
    results: list[dict],
    trajectory_scores: dict[str, float],
) -> dict[str, float]:
    """Compute opportunity scores for all stocks.

    Returns {ticker: 0-100 score} where higher = better opportunity.
    """
    if not results:
        return {}

    # Collect FCF yields and analyst upsides for percentile ranking
    fcf_yields = {}
    analyst_upsides = {}
    for r in results:
        t = r["ticker"]
        if r.get("fcf_yield") is not None:
            fcf_yields[t] = r["fcf_yield"]
        if r.get("analyst_upside") is not None:
            analyst_upsides[t] = r["analyst_upside"]

    fcf_pcts = _percentile_rank(fcf_yields)
    analyst_pcts = _percentile_rank(analyst_upsides)

    scores = {}
    for r in results:
        t = r["ticker"]

        conv = r.get("conviction_score")
        if conv is None:
            continue

        traj = trajectory_scores.get(t, 50.0)
        fcf_p = fcf_pcts.get(t, 50.0)
        f_norm = (r.get("piotroski_f", 0) / 9) * 100
        analyst_p = analyst_pcts.get(t, 50.0)

        opp = (
            0.40 * conv
            + 0.25 * traj
            + 0.15 * fcf_p
            + 0.10 * f_norm
            + 0.10 * analyst_p
        )
        scores[t] = round(opp, 1)

    return scores


def _percentile_rank(values: dict[str, float]) -> dict[str, float]:
    """Percentile-rank a dict of values (highest = 100)."""
    if not values:
        return {}
    sorted_tickers = sorted(values, key=values.get, reverse=True)
    n = len(sorted_tickers)
    return {t: round((n - i) / n * 100, 1) for i, t in enumerate(sorted_tickers)}
