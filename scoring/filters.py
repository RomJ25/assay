"""Data quality pre-filters."""

from __future__ import annotations

from data.providers.base import FinancialData


def passes_data_quality(data: FinancialData) -> bool:
    """Check if a stock has enough data for meaningful screening."""
    return data.has_minimum_data
