"""Quality scoring via Piotroski F-Score + Profitability + Safety.

Three academically proven signals:
- Piotroski F-Score: 13.4% annual outperformance (1976-1996)
- Profitability: (GP + R&D) / Assets (Novy-Marx 2013, Medhat 2025), ROA fallback
- Safety: low beta + low leverage (AQR QMJ, Asness et al. 2019)

When safety is enabled: 40% Piotroski + 40% Profitability + 20% Safety
When safety is disabled: 50% Piotroski + 50% Profitability (original)
"""

from __future__ import annotations

from config import QUALITY_SINGLE_SOURCE_PENALTY, RD_ADDBACK_ENABLED, SAFETY_ENABLED
from data.providers.base import FinancialData
from quality.piotroski import PiotroskiModel


def compute_safety_scores(
    all_data: dict[str, FinancialData],
) -> dict[str, float]:
    """Compute safety scores (0-100) from beta and leverage.

    AQR QMJ (Asness, Frazzini & Pedersen 2019): safety dimension has positive
    crisis convexity and 55-66 bps/month alpha. Low-beta + low-leverage stocks
    within value have better risk-adjusted returns.

    Components (equal weight):
    - Inverse beta percentile: lower beta = higher safety score
    - Inverse leverage percentile: lower debt/assets = higher safety score

    Missing beta (common in backtest) → neutral 50th percentile for that component.
    """
    betas: dict[str, float] = {}
    leverages: dict[str, float] = {}

    for ticker, fd in all_data.items():
        # Beta
        if fd.beta is not None and fd.beta > 0:
            betas[ticker] = fd.beta

        # Leverage = total_debt / total_assets
        debt = fd.get("total_debt", 0)
        assets = fd.get("total_assets", 0)
        if debt is not None and assets is not None and assets > 0:
            leverages[ticker] = (debt or 0) / assets

    # Inverse-percentile rank beta (lower = safer = higher score)
    beta_scores: dict[str, float] = {}
    if betas:
        sorted_beta = sorted(betas, key=betas.get)  # ascending: lowest beta first
        n = len(sorted_beta)
        beta_scores = {t: round((n - i) / n * 100, 1) for i, t in enumerate(sorted_beta)}

    # Inverse-percentile rank leverage (lower = safer = higher score)
    lev_scores: dict[str, float] = {}
    if leverages:
        sorted_lev = sorted(leverages, key=leverages.get)  # ascending: lowest leverage first
        n = len(sorted_lev)
        lev_scores = {t: round((n - i) / n * 100, 1) for i, t in enumerate(sorted_lev)}

    # Composite: 50% beta + 50% leverage (neutral 50 for missing components)
    safety_scores: dict[str, float] = {}
    all_tickers = set(beta_scores.keys()) | set(lev_scores.keys())
    for ticker in all_tickers:
        b = beta_scores.get(ticker, 50.0)  # neutral if no beta (common in backtest)
        l = lev_scores.get(ticker, 50.0)
        safety_scores[ticker] = round((b + l) / 2, 1)

    return safety_scores


def compute_quality_scores(
    all_data: dict[str, FinancialData],
) -> tuple[dict[str, float], dict[str, int], dict[str, float], dict[str, dict]]:
    """Compute quality scores from Piotroski + Profitability (+ Safety if enabled).

    Returns:
        quality_scores: {ticker: 0-100 score}
        piotroski_raw: {ticker: 0-9 raw F-Score}
        profitability_ratios: {ticker: profitability ratio used}
        piotroski_breakdowns: {ticker: breakdown dict with per-criterion detail}
    """
    piotroski = PiotroskiModel()

    # Piotroski F-Score (0-100 normalized) with per-criterion breakdown
    pio_scores: dict[str, float] = {}
    pio_raw: dict[str, int] = {}
    pio_breakdowns: dict[str, dict] = {}
    for ticker, fd in all_data.items():
        score, breakdown = piotroski.calculate_detailed(fd)
        if score is not None:
            pio_scores[ticker] = score
            pio_raw[ticker] = round(score * 9 / 100)
            pio_breakdowns[ticker] = breakdown

    # Profitability = GP/Assets (with optional R&D add-back per Novy-Marx 2025)
    # ROA fallback for banks that don't report Gross Profit
    profitability_ratios: dict[str, float] = {}
    for ticker, fd in all_data.items():
        gp = fd.get("gross_profit", 0)
        ni = fd.get("net_income", 0)
        assets = fd.get("total_assets", 0)

        if not assets or assets <= 0:
            continue

        if gp is not None:
            numerator = gp
            if RD_ADDBACK_ENABLED:
                rd = fd.get("research_development", 0)
                if rd is not None and rd > 0:
                    numerator = gp + rd
            profitability_ratios[ticker] = numerator / assets
        elif ni is not None:
            profitability_ratios[ticker] = ni / assets

    # Percentile rank by profitability (highest = best)
    if profitability_ratios:
        sorted_prof = sorted(profitability_ratios, key=profitability_ratios.get, reverse=True)
        n = len(sorted_prof)
        prof_scores = {t: round((n - i) / n * 100, 1) for i, t in enumerate(sorted_prof)}
    else:
        prof_scores = {}

    # Safety scores (if enabled)
    safety_scores = compute_safety_scores(all_data) if SAFETY_ENABLED else {}

    # Composite quality score
    # With safety: 40% Piotroski + 40% Profitability + 20% Safety
    # Without safety: 50% Piotroski + 50% Profitability
    quality_scores: dict[str, float] = {}
    for ticker in all_data:
        p = pio_scores.get(ticker)
        g = prof_scores.get(ticker)
        s = safety_scores.get(ticker) if SAFETY_ENABLED else None

        if SAFETY_ENABLED and p is not None and g is not None:
            s_val = s if s is not None else 50.0  # neutral safety if missing
            quality_scores[ticker] = round(0.4 * p + 0.4 * g + 0.2 * s_val, 1)
        elif p is not None and g is not None:
            quality_scores[ticker] = round((p + g) / 2, 1)
        elif p is not None:
            quality_scores[ticker] = round(p * QUALITY_SINGLE_SOURCE_PENALTY, 1)
        elif g is not None:
            quality_scores[ticker] = round(g * QUALITY_SINGLE_SOURCE_PENALTY, 1)

    return quality_scores, pio_raw, profitability_ratios, pio_breakdowns
