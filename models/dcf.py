"""Discounted Cash Flow (DCF) model with bear/base/bull range.

Produces 3 estimates: bear, base, bull. Score is based on base case.
"""

from __future__ import annotations

import logging

from config import (
    DCF_BEAR_GROWTH_PENALTY,
    DCF_BEAR_WACC_PENALTY,
    DCF_BULL_GROWTH_BONUS,
    DCF_MAX_GROWTH_RATE,
    DCF_MIN_GROWTH_RATE,
    DCF_PROJECTION_YEARS,
    DCF_TERMINAL_GROWTH,
    DEFAULT_TAX_RATE,
    EQUITY_RISK_PREMIUM,
    RISK_FREE_RATE,
    SKIP_DCF_SUBINDUSTRIES,
    WACC_SAFETY_BUFFER,
)
from data.providers.base import FinancialData
from models.base import ValuationModel, ValuationResult

logger = logging.getLogger(__name__)


def _cagr(latest: float, earliest: float, years: int) -> float | None:
    """Calculate compound annual growth rate."""
    if earliest is None or latest is None or earliest == 0 or years <= 0:
        return None
    if earliest < 0 and latest < 0:
        return None
    if earliest < 0 or latest < 0:
        return None
    ratio = latest / earliest
    if ratio <= 0:
        return None
    return ratio ** (1 / years) - 1


class DCFModel(ValuationModel):
    """Discounted Cash Flow valuation with bear/base/bull scenarios."""

    @property
    def name(self) -> str:
        return "dcf"

    def calculate(self, data: FinancialData) -> ValuationResult:
        # Skip for bank/insurance sub-industries
        if data.sub_industry in SKIP_DCF_SUBINDUSTRIES:
            return ValuationResult(intrinsic_value=None, details={"skipped": "financial_sector"})

        # FCF: use max of latest year and average of positive years
        # This smooths CapEx spikes (e.g., AMZN spending $132B on AI infra in one year)
        fcf_latest = data.get("free_cash_flow", 0)
        positive_fcfs = [v for v in data.free_cash_flow if v is not None and v > 0]
        fcf_avg = sum(positive_fcfs) / len(positive_fcfs) if positive_fcfs else None

        if fcf_latest and fcf_latest > 0 and fcf_avg:
            fcf = max(fcf_latest, fcf_avg)
        elif fcf_latest and fcf_latest > 0:
            fcf = fcf_latest
        elif fcf_avg:
            fcf = fcf_avg
        else:
            return ValuationResult(intrinsic_value=None, details={"skipped": "negative_fcf"})

        if data.shares_outstanding <= 0:
            return ValuationResult(intrinsic_value=None, details={"skipped": "no_shares"})

        # Calculate WACC
        wacc = self._calculate_wacc(data)
        if wacc is None or wacc <= DCF_TERMINAL_GROWTH:
            return ValuationResult(intrinsic_value=None, details={"skipped": "invalid_wacc"})

        # Estimate growth rate
        growth = self._estimate_growth(data)

        # Calculate 3 scenarios
        bear = self._dcf_scenario(
            fcf, data,
            wacc=wacc + DCF_BEAR_WACC_PENALTY,
            growth=max(growth - DCF_BEAR_GROWTH_PENALTY, 0),
        )
        base = self._dcf_scenario(
            fcf, data,
            wacc=wacc + WACC_SAFETY_BUFFER,
            growth=growth,
        )
        bull = self._dcf_scenario(
            fcf, data,
            wacc=wacc,
            growth=min(growth + DCF_BULL_GROWTH_BONUS, DCF_MAX_GROWTH_RATE + DCF_BULL_GROWTH_BONUS),
        )

        return ValuationResult(
            intrinsic_value=base,
            details={"dcf_bear": bear, "dcf_base": base, "dcf_bull": bull, "wacc": wacc, "growth": growth},
        )

    def _calculate_wacc(self, data: FinancialData) -> float | None:
        """WACC via CAPM: (E/V)*Re + (D/V)*Rd*(1-Tc)."""
        beta = data.beta if data.beta and data.beta > 0 else 1.0
        cost_of_equity = RISK_FREE_RATE + beta * EQUITY_RISK_PREMIUM

        # Cost of debt
        interest = data.get("interest_expense", 0) or 0
        debt = data.get("total_debt", 0) or 0
        tax_rate = data.effective_tax_rate or DEFAULT_TAX_RATE
        cost_of_debt = (interest / debt * (1 - tax_rate)) if debt > 0 else 0

        # Weights
        equity = data.market_cap
        total_value = equity + debt
        if total_value <= 0:
            return cost_of_equity

        e_weight = equity / total_value
        d_weight = debt / total_value

        return e_weight * cost_of_equity + d_weight * cost_of_debt

    def _estimate_growth(self, data: FinancialData) -> float:
        """Estimate FCF growth rate from historical data."""
        fcf_list = data.free_cash_flow
        valid = [(i, v) for i, v in enumerate(fcf_list) if v is not None and v > 0]

        if len(valid) >= 2:
            latest_i, latest_v = valid[0]
            earliest_i, earliest_v = valid[-1]
            years = earliest_i - latest_i
            if years == 0:
                years = 1
            growth = _cagr(latest_v, earliest_v, abs(years))
            if growth is not None:
                return max(min(growth, DCF_MAX_GROWTH_RATE), DCF_MIN_GROWTH_RATE)

        # Fallback: use revenue growth
        rev_list = data.revenue
        valid_rev = [(i, v) for i, v in enumerate(rev_list) if v is not None and v > 0]
        if len(valid_rev) >= 2:
            growth = _cagr(valid_rev[0][1], valid_rev[-1][1], len(valid_rev) - 1)
            if growth is not None:
                return max(min(growth, DCF_MAX_GROWTH_RATE), DCF_MIN_GROWTH_RATE)

        return DCF_MIN_GROWTH_RATE

    def _dcf_scenario(
        self, fcf: float, data: FinancialData, wacc: float, growth: float
    ) -> float | None:
        """Calculate per-share intrinsic value for one scenario."""
        terminal_growth = min(DCF_TERMINAL_GROWTH, wacc - 0.01)
        if wacc <= terminal_growth:
            return None

        # Project FCF with decaying growth
        pv_fcfs = 0.0
        projected_fcf = fcf
        for year in range(1, DCF_PROJECTION_YEARS + 1):
            # Decay growth linearly toward terminal growth
            decay_factor = 1 - (year - 1) / DCF_PROJECTION_YEARS
            year_growth = growth * decay_factor + terminal_growth * (1 - decay_factor)
            projected_fcf *= (1 + year_growth)
            pv_fcfs += projected_fcf / (1 + wacc) ** year

        # Terminal value
        terminal_value = projected_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
        pv_terminal = terminal_value / (1 + wacc) ** DCF_PROJECTION_YEARS

        # Enterprise → Equity → Per share
        enterprise_value = pv_fcfs + pv_terminal
        cash = data.get("cash_and_equivalents", 0) or 0
        debt = data.get("total_debt", 0) or 0
        equity_value = enterprise_value + cash - debt

        if equity_value <= 0 or data.shares_outstanding <= 0:
            return None

        return round(equity_value / data.shares_outstanding, 2)
