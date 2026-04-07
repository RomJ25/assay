"""Data quality pre-filters."""

from __future__ import annotations

from data.providers.base import FinancialData


def passes_data_quality(data: FinancialData) -> bool:
    """Check if a stock has enough data for meaningful screening."""
    return data.has_minimum_data


def include_stock(d: FinancialData) -> bool:
    """Check if a stock should be included when --exclude-financials is active.

    Excludes Real Estate (REITs have distorted metrics) and Financials
    that lack operating income (banks/insurance using 1/PE fallback).
    Keeps fintech/payment companies (PYPL, MA, V) that report normal EBIT.
    """
    if d.sector == "Real Estate":
        return False
    if d.sector != "Financials":
        return True
    oi = d.get("operating_income", 0)
    return oi is not None and oi > 0
