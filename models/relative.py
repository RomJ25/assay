"""Relative valuation vs GICS sector medians + PEG ratio."""

from __future__ import annotations

import logging
from statistics import median

from config import EVEBITDA_OUTLIER_MAX, PE_OUTLIER_MAX
from data.providers.base import FinancialData
from models.base import ValuationModel, ValuationResult

logger = logging.getLogger(__name__)


class RelativeModel(ValuationModel):
    """Compare P/E, EV/EBITDA, P/S, and PEG against sector medians."""

    @property
    def name(self) -> str:
        return "relative"

    def __init__(self):
        self._sector_medians: dict[str, dict[str, float]] = {}

    def compute_sector_medians(self, all_data: dict[str, FinancialData]):
        """Pre-compute sector medians from all screened stocks."""
        sectors: dict[str, dict[str, list[float]]] = {}

        for fd in all_data.values():
            sector = fd.sector
            if sector not in sectors:
                sectors[sector] = {"pe": [], "ev_ebitda": [], "ps": []}

            if fd.trailing_pe and 0 < fd.trailing_pe < PE_OUTLIER_MAX:
                sectors[sector]["pe"].append(fd.trailing_pe)
            if fd.enterprise_to_ebitda and 0 < fd.enterprise_to_ebitda < EVEBITDA_OUTLIER_MAX:
                sectors[sector]["ev_ebitda"].append(fd.enterprise_to_ebitda)
            if fd.price_to_sales and fd.price_to_sales > 0:
                sectors[sector]["ps"].append(fd.price_to_sales)

        self._sector_medians = {}
        min_for_median = 3  # need at least 3 stocks for meaningful sector median
        for sector, metrics in sectors.items():
            self._sector_medians[sector] = {
                "pe": median(metrics["pe"]) if len(metrics["pe"]) >= min_for_median else None,
                "ev_ebitda": median(metrics["ev_ebitda"]) if len(metrics["ev_ebitda"]) >= min_for_median else None,
                "ps": median(metrics["ps"]) if len(metrics["ps"]) >= min_for_median else None,
            }
            logger.debug(f"Sector {sector}: medians = {self._sector_medians[sector]}")

    def calculate(self, data: FinancialData) -> ValuationResult:
        medians = self._sector_medians.get(data.sector, {})
        if not medians:
            return ValuationResult(intrinsic_value=None, details={"skipped": "no_sector_medians"})

        discounts = []
        details = {}

        # P/E comparison
        if data.trailing_pe and 0 < data.trailing_pe < PE_OUTLIER_MAX:
            med_pe = medians.get("pe")
            if med_pe:
                disc = (med_pe - data.trailing_pe) / med_pe
                discounts.append(disc)
                details["pe_discount"] = round(disc, 4)

        # EV/EBITDA comparison
        if data.enterprise_to_ebitda and 0 < data.enterprise_to_ebitda < EVEBITDA_OUTLIER_MAX:
            med_ev = medians.get("ev_ebitda")
            if med_ev:
                disc = (med_ev - data.enterprise_to_ebitda) / med_ev
                discounts.append(disc)
                details["ev_ebitda_discount"] = round(disc, 4)

        # P/S comparison
        if data.price_to_sales and data.price_to_sales > 0:
            med_ps = medians.get("ps")
            if med_ps:
                disc = (med_ps - data.price_to_sales) / med_ps
                discounts.append(disc)
                details["ps_discount"] = round(disc, 4)

        # PEG ratio
        peg = self._calculate_peg(data)
        if peg is not None:
            details["peg_ratio"] = round(peg, 2)
            # PEG < 1 means undervalued relative to growth
            if peg > 0:
                peg_discount = max(-1.0, min(1.0, (1.0 - peg)))  # clamp to [-1, 1]
                discounts.append(peg_discount * 0.5)  # weight PEG less than other metrics

        if not discounts:
            return ValuationResult(intrinsic_value=None, details={"skipped": "no_applicable_metrics"})

        avg_discount = sum(discounts) / len(discounts)
        implied_fair_value = data.current_price * (1 + avg_discount)

        details["avg_relative_discount"] = round(avg_discount, 4)
        details["sector_medians"] = medians

        return ValuationResult(
            intrinsic_value=round(max(implied_fair_value, 0), 2),
            details=details,
        )

    @staticmethod
    def _calculate_peg(data: FinancialData) -> float | None:
        """PEG = P/E / EPS growth rate (%)."""
        if not data.trailing_pe or data.trailing_pe <= 0:
            return None

        eps_list = [e for e in data.diluted_eps if e is not None and e > 0]
        if len(eps_list) < 2:
            return None

        # EPS CAGR
        years = len(eps_list) - 1
        growth = (eps_list[0] / eps_list[-1]) ** (1 / years) - 1 if eps_list[-1] > 0 else None
        if growth is None or growth <= 0:
            return None

        return data.trailing_pe / (growth * 100)
