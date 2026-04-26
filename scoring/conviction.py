"""2D Conviction Matrix — combines Value Score and Quality+Growth Score."""

from __future__ import annotations

import math

from config import (
    BUY_QUALITY_THRESHOLD,
    BUY_VALUE_THRESHOLD,
    MIN_PIOTROSKI_F,
    QUALITY_HIGH_THRESHOLD,
    QUALITY_LOW_THRESHOLD,
    REVENUE_GATE_ENABLED,
    VALUE_HIGH_THRESHOLD,
    VALUE_LOW_THRESHOLD,
)


def conviction_score(value_score: float | None, quality_score: float | None) -> float | None:
    """Geometric mean of value and quality scores.

    Ensures both dimensions must be high for a high conviction score.
    """
    if value_score is None or quality_score is None:
        return None
    if value_score <= 0 or quality_score <= 0:
        return 0.0
    return round(math.sqrt(value_score * quality_score), 1)


def confidence_level(value_score: float | None, quality_score: float | None) -> str | None:
    """Rate conviction buy confidence based on margin above thresholds.

    HIGH:     both scores >= 85 (15+ pts above threshold)
    MODERATE: both scores >= 75 (5+ pts above threshold)
    LOW:      at least one score barely above 70
    """
    if value_score is None or quality_score is None:
        return None
    margin = min(value_score - VALUE_HIGH_THRESHOLD,
                 quality_score - QUALITY_HIGH_THRESHOLD)
    if margin >= 15:
        return "HIGH"
    if margin >= 5:
        return "MODERATE"
    return "LOW"


def apply_min_fscore(classification: str, piotroski_f: int) -> str:
    """Downgrade RESEARCH CANDIDATE to WATCH LIST if raw F-Score is below minimum.

    Piotroski's paper compared F >= 8 ("high") vs F <= 1 ("low") within high-B/M
    stocks and reported a 13.4% long-only excess return. The F >= 6 gate here is a
    pragmatic long-only choice for the 500-name large-cap universe, not a claim from
    the paper. See docs/DESIGN_DECISIONS.md for the full rationale.
    """
    if classification == "RESEARCH CANDIDATE" and piotroski_f < MIN_PIOTROSKI_F:
        return "WATCH LIST"
    return classification


def apply_revenue_gate(classification: str, revenue: list[float | None] | None) -> tuple[str, bool]:
    """Downgrade RESEARCH CANDIDATE to WATCH LIST if revenue declined 2+ consecutive years.

    Chen, Chen, Hsin & Lee (2014): revenue momentum carries exclusive predictive
    information beyond earnings and price momentum. Persistent revenue decline
    (2+ consecutive years) is the clearest value trap signal.

    Returns: (classification, gate_fired)
    """
    if not REVENUE_GATE_ENABLED:
        return classification, False
    if classification != "RESEARCH CANDIDATE":
        return classification, False
    if not revenue or len(revenue) < 3:
        return classification, False  # insufficient data, don't penalize

    r0, r1, r2 = revenue[0], revenue[1], revenue[2]

    # Need valid positive values for all 3 years
    if r0 is None or r1 is None or r2 is None:
        return classification, False
    if r0 <= 0 or r1 <= 0 or r2 <= 0:
        return classification, False

    # Revenue declined in both of the last 2 years
    if r0 < r1 and r1 < r2:
        return "WATCH LIST", True

    return classification, False


def classify(value_score: float | None, quality_score: float | None) -> str:
    """Classify stock into conviction matrix bucket.

    The buy/hold spread (audit §6.5 / Novy-Marx & Velikov 2023) is implemented
    here: RESEARCH CANDIDATE requires the BUY thresholds (env-overridable, default =
    VALUE_HIGH_THRESHOLD / QUALITY_HIGH_THRESHOLD for backwards compatibility).
    When BUY thresholds exceed HIGH thresholds, stocks in the [HIGH, BUY)
    interval on both dimensions land in QUALITY GROWTH PREMIUM — a "hold"
    bucket in selective-sell mode. Existing CB names drift through this band
    before sale, while new entries require the stricter BUY bar.
    """
    if value_score is None or quality_score is None:
        return "INSUFFICIENT DATA"

    v_buy = value_score >= BUY_VALUE_THRESHOLD
    q_buy = quality_score >= BUY_QUALITY_THRESHOLD

    v_high = value_score >= VALUE_HIGH_THRESHOLD
    v_mid = VALUE_LOW_THRESHOLD <= value_score < VALUE_HIGH_THRESHOLD
    v_low = value_score < VALUE_LOW_THRESHOLD

    q_high = quality_score >= QUALITY_HIGH_THRESHOLD
    q_mid = QUALITY_LOW_THRESHOLD <= quality_score < QUALITY_HIGH_THRESHOLD
    q_low = quality_score < QUALITY_LOW_THRESHOLD

    # CB requires the (possibly-stricter) BUY thresholds.
    if v_buy and q_buy:
        return "RESEARCH CANDIDATE"
    # Stocks meeting HIGH on both but not BUY → "hold" bucket (QGP) so selective
    # sell continues to hold them. Naming is QUALITY GROWTH PREMIUM because that
    # bucket already holds the "high quality, not-quite-cheap-enough" semantic.
    if v_high and q_high:
        return "QUALITY GROWTH PREMIUM"
    if v_high and q_low:
        return "VALUE TRAP"
    if v_high and q_mid:
        return "WATCH LIST"
    if v_mid and q_high:
        return "QUALITY GROWTH PREMIUM"
    if v_mid and q_mid:
        return "HOLD"
    if v_low and q_high:
        return "OVERVALUED QUALITY"
    if v_low and q_mid:
        return "OVERVALUED"
    # v_low + q_low OR v_mid + q_low
    return "AVOID"
