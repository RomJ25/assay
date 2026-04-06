"""Quality scoring via Piotroski F-Score + Profitability ranking.

Two academically proven signals:
- Piotroski F-Score: 13.4% annual outperformance (1976-1996)
- Profitability: Gross Profit / Assets (Novy-Marx 2013), with ROA fallback
  for financials that don't report Gross Profit

Combined: "Cheap + Profitable stocks dramatically outperform Cheap + Unprofitable"
"""

from __future__ import annotations

from config import QUALITY_SINGLE_SOURCE_PENALTY
from data.providers.base import FinancialData
from quality.piotroski import PiotroskiModel


def compute_quality_scores(
    all_data: dict[str, FinancialData],
) -> tuple[dict[str, float], dict[str, int], dict[str, float]]:
    """Compute quality scores from Piotroski + Profitability.

    Profitability = Gross Profit / Total Assets (Novy-Marx factor).
    For stocks without Gross Profit (banks), falls back to ROA (Net Income / Assets).

    Returns:
        quality_scores: {ticker: 0-100 score}
        piotroski_raw: {ticker: 0-9 raw F-Score}
        profitability_ratios: {ticker: profitability ratio used}
    """
    piotroski = PiotroskiModel()

    # Piotroski F-Score (0-100 normalized)
    pio_scores: dict[str, float] = {}
    pio_raw: dict[str, int] = {}
    for ticker, fd in all_data.items():
        score = piotroski.calculate(fd)
        if score is not None:
            pio_scores[ticker] = score
            pio_raw[ticker] = piotroski.raw_score(fd)

    # Profitability = GP/Assets, with ROA fallback for banks
    profitability_ratios: dict[str, float] = {}
    for ticker, fd in all_data.items():
        gp = fd.get("gross_profit", 0)
        ni = fd.get("net_income", 0)
        assets = fd.get("total_assets", 0)

        if not assets or assets <= 0:
            continue

        if gp and gp > 0:
            # Primary: Gross Profitability (Novy-Marx)
            profitability_ratios[ticker] = gp / assets
        elif ni and ni > 0:
            # Fallback: ROA for banks/financials that don't report Gross Profit
            profitability_ratios[ticker] = ni / assets

    # Percentile rank by profitability (highest = best)
    if profitability_ratios:
        sorted_prof = sorted(profitability_ratios, key=profitability_ratios.get, reverse=True)
        n = len(sorted_prof)
        prof_scores = {t: round((n - i) / n * 100, 1) for i, t in enumerate(sorted_prof)}
    else:
        prof_scores = {}

    # Composite: 50% Piotroski + 50% Profitability rank
    # Single-source scores are penalized to avoid inflation from less data
    quality_scores: dict[str, float] = {}
    for ticker in all_data:
        p = pio_scores.get(ticker)
        g = prof_scores.get(ticker)
        if p is not None and g is not None:
            quality_scores[ticker] = round((p + g) / 2, 1)
        elif p is not None:
            quality_scores[ticker] = round(p * QUALITY_SINGLE_SOURCE_PENALTY, 1)
        elif g is not None:
            quality_scores[ticker] = round(g * QUALITY_SINGLE_SOURCE_PENALTY, 1)

    return quality_scores, pio_raw, profitability_ratios
