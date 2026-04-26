"""Data-quality grade — red/yellow/green for a FinancialData snapshot.

The grade summarizes whether the underlying fundamentals can be trusted for
research-candidate classification:

  red    — required field missing; downstream models will produce noisy or
           non-comparable scores.
  yellow — fallback provider was used OR the latest annual filing is more than
           ~1 quarter (95 days) old. Scoring still runs, but the user should
           treat the result as research input only.
  green  — primary provider, latest filing within the most recent quarter.

This is deliberately simple: the goal is to make the trust caveat *visible*
on every research candidate, not to encode a full provenance audit graph.
"""

from __future__ import annotations

from dataclasses import dataclass

from data.providers.base import FinancialData

YELLOW_FISCAL_AGE_THRESHOLD_DAYS = 95  # > 1 quarter past the latest fiscal year-end


@dataclass(frozen=True)
class DataQualityReport:
    """Compact result that downstream consumers can render as a chip/badge."""

    grade: str  # "red" | "yellow" | "green"
    warnings: tuple[str, ...]  # ordered, human-readable

    @property
    def is_red(self) -> bool:
        return self.grade == "red"

    @property
    def is_yellow(self) -> bool:
        return self.grade == "yellow"

    @property
    def is_green(self) -> bool:
        return self.grade == "green"


def grade_data_quality(fd: FinancialData) -> DataQualityReport:
    """Compute a red/yellow/green grade for a FinancialData snapshot."""
    warnings: list[str] = []

    # Red: missing required fields downstream models depend on.
    if fd.current_price <= 0:
        warnings.append("missing current_price")
    if not fd.revenue or fd.revenue[0] is None or fd.revenue[0] <= 0:
        warnings.append("missing latest revenue")
    if not fd.net_income or fd.net_income[0] is None:
        warnings.append("missing latest net_income")
    if warnings:
        return DataQualityReport(grade="red", warnings=tuple(warnings))

    # Yellow: trust caveats. Stop at the first match — yellow is a single signal,
    # the warnings list still surfaces every reason for transparency.
    if fd.fallback_used or fd.data_source == "yfinance_fallback":
        warnings.append("yfinance fallback used (yahooquery primary failed)")
    if fd.fiscal_age_days is not None and fd.fiscal_age_days > YELLOW_FISCAL_AGE_THRESHOLD_DAYS:
        warnings.append(
            f"latest annual filing is {fd.fiscal_age_days} days old "
            f"(>{YELLOW_FISCAL_AGE_THRESHOLD_DAYS}d threshold)"
        )

    if warnings:
        return DataQualityReport(grade="yellow", warnings=tuple(warnings))
    return DataQualityReport(grade="green", warnings=())
