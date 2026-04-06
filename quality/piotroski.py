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
        score = 0
        details = {}

        # --- Profitability (4 criteria) ---

        # 1. Net Income > 0 (current year)
        ni = data.get("net_income", 0)
        if ni is not None and ni > 0:
            score += 1
            details["f_ni"] = True

        # 2. Operating Cash Flow > 0 (current year)
        ocf = data.get("operating_cash_flow", 0)
        if ocf is not None and ocf > 0:
            score += 1
            details["f_ocf"] = True

        # 3. ROA improving (this year > last year)
        assets_0 = data.get("total_assets", 0)
        assets_1 = data.get("total_assets", 1)
        ni_0 = data.get("net_income", 0)
        ni_1 = data.get("net_income", 1)
        if all(v is not None and v > 0 for v in [assets_0, assets_1, ni_0]) and ni_1 is not None:
            roa_0 = ni_0 / assets_0
            roa_1 = ni_1 / assets_1
            if roa_0 > roa_1:
                score += 1
                details["f_roa_improving"] = True

        # 4. Accruals: OCF > Net Income (earnings backed by cash)
        if ocf is not None and ni is not None and ocf > ni:
            score += 1
            details["f_accrual"] = True

        # --- Leverage, Liquidity & Source of Funds (3 criteria) ---

        # 5. Debt ratio decreased
        debt_0 = data.get("total_debt", 0)
        debt_1 = data.get("total_debt", 1)
        if debt_0 is not None and debt_1 is not None and assets_0 and assets_1:
            if assets_0 > 0 and assets_1 > 0:
                ratio_0 = debt_0 / assets_0
                ratio_1 = debt_1 / assets_1
                if ratio_0 < ratio_1:
                    score += 1
                    details["f_leverage_down"] = True

        # 6. Current ratio increased
        ca_0 = data.get("current_assets", 0)
        cl_0 = data.get("current_liabilities", 0)
        ca_1 = data.get("current_assets", 1)
        cl_1 = data.get("current_liabilities", 1)
        if all(v is not None and v > 0 for v in [ca_0, cl_0, ca_1, cl_1]):
            cr_0 = ca_0 / cl_0
            cr_1 = ca_1 / cl_1
            if cr_0 > cr_1:
                score += 1
                details["f_liquidity_up"] = True

        # 7. No share dilution (shares outstanding <= last year)
        shares_0 = data.get("ordinary_shares_number", 0)
        shares_1 = data.get("ordinary_shares_number", 1)
        if shares_0 is not None and shares_1 is not None and shares_0 > 0 and shares_1 > 0:
            if shares_0 <= shares_1:
                score += 1
                details["f_no_dilution"] = True

        # --- Operating Efficiency (2 criteria) ---

        # 8. Gross margin increased
        gp_0 = data.get("gross_profit", 0)
        rev_0 = data.get("revenue", 0)
        gp_1 = data.get("gross_profit", 1)
        rev_1 = data.get("revenue", 1)
        if all(v is not None and v > 0 for v in [gp_0, rev_0, gp_1, rev_1]):
            gm_0 = gp_0 / rev_0
            gm_1 = gp_1 / rev_1
            if gm_0 > gm_1:
                score += 1
                details["f_margin_up"] = True

        # 9. Asset turnover increased
        if rev_0 and rev_1 and assets_0 and assets_1:
            if assets_0 > 0 and assets_1 > 0:
                at_0 = rev_0 / assets_0
                at_1 = rev_1 / assets_1
                if at_0 > at_1:
                    score += 1
                    details["f_turnover_up"] = True

        normalized = round((score / 9) * 100, 1)
        return normalized

    def raw_score(self, data: FinancialData) -> int:
        """Return the raw 0-9 F-Score."""
        normalized = self.calculate(data)
        if normalized is None:
            return 0
        return round(normalized * 9 / 100)
