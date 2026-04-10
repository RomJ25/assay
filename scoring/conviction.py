"""2D Conviction Matrix — combines Value Score and Quality+Growth Score."""

from __future__ import annotations

import math

from config import (
    MIN_PIOTROSKI_F,
    QUALITY_HIGH_THRESHOLD,
    QUALITY_LOW_THRESHOLD,
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
    """Downgrade CONVICTION BUY to WATCH LIST if raw F-Score is below minimum.

    Piotroski's paper compared F >= 8 ("high") vs F <= 1 ("low") within high-B/M
    stocks and reported a 13.4% long-only excess return. The F >= 6 gate here is a
    pragmatic long-only choice for the 500-name large-cap universe, not a claim from
    the paper. See docs/DESIGN_DECISIONS.md for the full rationale.
    """
    if classification == "CONVICTION BUY" and piotroski_f < MIN_PIOTROSKI_F:
        return "WATCH LIST"
    return classification


def classify(value_score: float | None, quality_score: float | None) -> str:
    """Classify stock into conviction matrix bucket."""
    if value_score is None or quality_score is None:
        return "INSUFFICIENT DATA"

    v_high = value_score >= VALUE_HIGH_THRESHOLD
    v_mid = VALUE_LOW_THRESHOLD <= value_score < VALUE_HIGH_THRESHOLD
    v_low = value_score < VALUE_LOW_THRESHOLD

    q_high = quality_score >= QUALITY_HIGH_THRESHOLD
    q_mid = QUALITY_LOW_THRESHOLD <= quality_score < QUALITY_HIGH_THRESHOLD
    q_low = quality_score < QUALITY_LOW_THRESHOLD

    if v_high and q_high:
        return "CONVICTION BUY"
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
