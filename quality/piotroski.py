"""Piotroski F-Score: 9 binary criteria for financial health.

Academic backing: 13.4% annual outperformance over 20 years when combined with value.
"""

from __future__ import annotations

from data.providers.base import FinancialData
from quality.base import QualityModel


class PiotroskiModel(QualityModel):
    """Piotroski F-Score (0-9) normalized to 0-100."""

    @property
    def name(self) -> str:
        return "piotroski"

    def calculate(self, data: FinancialData) -> float | None:
        """Return normalized 0-100 score."""
        return self.calculate_detailed(data)[0]

    def calculate_detailed(self, data: FinancialData) -> tuple[float | None, dict]:
        """Return (normalized_score, breakdown) with per-criterion detail.

        Breakdown has 'raw_score' (0-9) and 'criteria' dict with 9 entries,
        each containing 'pass' (bool) and the values used for evaluation.
        """
        criteria = {}

        # --- Profitability (4 criteria) ---

        # 1. Net Income > 0 (current year)
        ni = data.get("net_income", 0)
        passed = ni is not None and ni > 0
        criteria["net_income_positive"] = {"pass": passed, "value": ni}

        # 2. Operating Cash Flow > 0 (current year)
        ocf = data.get("operating_cash_flow", 0)
        passed = ocf is not None and ocf > 0
        criteria["ocf_positive"] = {"pass": passed, "value": ocf}

        # 3. ROA improving (this year > last year)
        assets_0 = data.get("total_assets", 0)
        assets_1 = data.get("total_assets", 1)
        ni_0 = data.get("net_income", 0)
        ni_1 = data.get("net_income", 1)
        roa_0 = roa_1 = None
        passed = False
        if all(v is not None and v > 0 for v in [assets_0, assets_1, ni_0]) and ni_1 is not None:
            roa_0 = ni_0 / assets_0
            roa_1 = ni_1 / assets_1
            passed = roa_0 > roa_1
        criteria["roa_improving"] = {"pass": passed, "current": roa_0, "prior": roa_1}

        # 4. Accruals: OCF > Net Income (earnings backed by cash)
        passed = ocf is not None and ni is not None and ocf > ni
        criteria["accruals_quality"] = {"pass": passed, "ocf": ocf, "ni": ni}

        # --- Leverage, Liquidity & Source of Funds (3 criteria) ---

        # 5. Debt ratio decreased
        debt_0 = data.get("total_debt", 0)
        debt_1 = data.get("total_debt", 1)
        dr_0 = dr_1 = None
        passed = False
        if debt_0 is not None and debt_1 is not None and assets_0 and assets_1:
            if assets_0 > 0 and assets_1 > 0:
                dr_0 = debt_0 / assets_0
                dr_1 = debt_1 / assets_1
                passed = dr_0 < dr_1
        criteria["debt_ratio_decreasing"] = {"pass": passed, "current": dr_0, "prior": dr_1}

        # 6. Current ratio increased
        ca_0 = data.get("current_assets", 0)
        cl_0 = data.get("current_liabilities", 0)
        ca_1 = data.get("current_assets", 1)
        cl_1 = data.get("current_liabilities", 1)
        cr_0 = cr_1 = None
        passed = False
        if all(v is not None and v > 0 for v in [ca_0, cl_0, ca_1, cl_1]):
            cr_0 = ca_0 / cl_0
            cr_1 = ca_1 / cl_1
            passed = cr_0 > cr_1
        criteria["current_ratio_up"] = {"pass": passed, "current": cr_0, "prior": cr_1}

        # 7. No share dilution (shares outstanding <= last year)
        shares_0 = data.get("ordinary_shares_number", 0)
        shares_1 = data.get("ordinary_shares_number", 1)
        passed = False
        if shares_0 is not None and shares_1 is not None and shares_0 > 0 and shares_1 > 0:
            passed = shares_0 <= shares_1
        criteria["no_dilution"] = {"pass": passed, "current": shares_0, "prior": shares_1}

        # --- Operating Efficiency (2 criteria) ---

        # 8. Gross margin increased
        gp_0 = data.get("gross_profit", 0)
        rev_0 = data.get("revenue", 0)
        gp_1 = data.get("gross_profit", 1)
        rev_1 = data.get("revenue", 1)
        gm_0 = gm_1 = None
        passed = False
        if all(v is not None and v > 0 for v in [gp_0, rev_0, gp_1, rev_1]):
            gm_0 = gp_0 / rev_0
            gm_1 = gp_1 / rev_1
            passed = gm_0 > gm_1
        criteria["gross_margin_up"] = {"pass": passed, "current": gm_0, "prior": gm_1}

        # 9. Asset turnover increased
        at_0 = at_1 = None
        passed = False
        if rev_0 and rev_1 and assets_0 and assets_1:
            if assets_0 > 0 and assets_1 > 0:
                at_0 = rev_0 / assets_0
                at_1 = rev_1 / assets_1
                passed = at_0 > at_1
        criteria["asset_turnover_up"] = {"pass": passed, "current": at_0, "prior": at_1}

        raw = sum(1 for c in criteria.values() if c["pass"])
        normalized = round((raw / 9) * 100, 1)
        breakdown = {"raw_score": raw, "criteria": criteria}
        return normalized, breakdown

    def raw_score(self, data: FinancialData) -> int:
        """Return the raw 0-9 F-Score."""
        normalized = self.calculate(data)
        if normalized is None:
            return 0
        return round(normalized * 9 / 100)
