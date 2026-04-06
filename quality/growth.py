"""Growth & Profitability scoring — revenue, margins, FCF, PEG.

14 metrics grouped into 4 sub-scores: revenue momentum (35%),
profitability & margin expansion (30%), earnings & FCF growth (20%),
PEG attractiveness (15%).
"""

from __future__ import annotations

from config import PEG_TIERS, REVENUE_CAGR_TIERS
from data.providers.base import FinancialData
from quality.base import QualityModel


def _tier_score(value: float, tiers: list[tuple[float, int]], default_low: int = 0) -> float:
    """Map a value to a score using tier thresholds."""
    for threshold, base_score in tiers:
        if value >= threshold:
            return base_score + 10  # midpoint of tier range
    return default_low + 15  # midpoint of lowest tier


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _growth_rate(latest: float | None, prev: float | None) -> float | None:
    if latest is None or prev is None or prev == 0:
        return None
    return (latest - prev) / abs(prev)


class GrowthModel(QualityModel):
    """Growth & Profitability score (0-100)."""

    @property
    def name(self) -> str:
        return "growth"

    def calculate(self, data: FinancialData) -> float | None:
        sub_scores = []
        sub_weights = []

        # A. Revenue Momentum (35%)
        rev_score = self._revenue_momentum(data)
        if rev_score is not None:
            sub_scores.append(rev_score)
            sub_weights.append(0.35)

        # B. Profitability & Margin Expansion (30%)
        prof_score = self._profitability(data)
        if prof_score is not None:
            sub_scores.append(prof_score)
            sub_weights.append(0.30)

        # C. Earnings & FCF Growth (20%)
        earn_score = self._earnings_fcf_growth(data)
        if earn_score is not None:
            sub_scores.append(earn_score)
            sub_weights.append(0.20)

        # D. PEG Attractiveness (15%)
        peg_score = self._peg_attractiveness(data)
        if peg_score is not None:
            sub_scores.append(peg_score)
            sub_weights.append(0.15)

        if not sub_scores:
            return None

        total_weight = sum(sub_weights)
        weighted = sum(s * w for s, w in zip(sub_scores, sub_weights))
        return round(weighted / total_weight, 1)

    def _revenue_momentum(self, data: FinancialData) -> float | None:
        """Revenue CAGR 3yr + YoY + acceleration."""
        rev = data.revenue
        valid = [v for v in rev if v is not None and v > 0]
        if len(valid) < 2:
            return None

        # 3yr CAGR (or available years)
        years = len(valid) - 1
        cagr = (valid[0] / valid[-1]) ** (1 / years) - 1

        score = _tier_score(cagr, REVENUE_CAGR_TIERS)

        # Acceleration bonus: is YoY growth speeding up?
        if len(valid) >= 3:
            yoy_latest = (valid[0] - valid[1]) / valid[1] if valid[1] > 0 else 0
            yoy_prev = (valid[1] - valid[2]) / valid[2] if valid[2] > 0 else 0
            if yoy_latest > yoy_prev:
                score = min(100, score + 10)

        return min(100, max(0, score))

    def _profitability(self, data: FinancialData) -> float | None:
        """Margin levels + expansion trends."""
        scores = []

        # Current margins
        gm = _safe_div(data.get("gross_profit", 0), data.get("revenue", 0))
        om = _safe_div(data.get("operating_income", 0), data.get("revenue", 0))
        nm = _safe_div(data.get("net_income", 0), data.get("revenue", 0))
        fcfm = _safe_div(data.get("free_cash_flow", 0), data.get("revenue", 0))

        # Margin level score (0-50)
        positive_margins = sum(1 for m in [gm, om, nm, fcfm] if m is not None and m > 0)
        margin_level_score = positive_margins * 12.5  # 0-50

        # Margin trend score (0-50) — compare current to 2 years ago
        expanding = 0
        total_checked = 0

        for metric_name, current_metric in [("gross_profit", gm), ("operating_income", om), ("net_income", nm)]:
            val_2yr = data.get(metric_name, 2)
            rev_2yr = data.get("revenue", 2)
            if val_2yr is not None and rev_2yr is not None and rev_2yr > 0 and current_metric is not None:
                old_margin = val_2yr / rev_2yr
                total_checked += 1
                if current_metric > old_margin:
                    expanding += 1

        if total_checked > 0:
            trend_score = (expanding / total_checked) * 50
        else:
            trend_score = 25  # neutral

        total = margin_level_score + trend_score
        return min(100, max(0, total))

    def _earnings_fcf_growth(self, data: FinancialData) -> float | None:
        """EPS and FCF YoY growth."""
        eps_growth = _growth_rate(data.get("diluted_eps", 0), data.get("diluted_eps", 1))
        fcf_growth = _growth_rate(data.get("free_cash_flow", 0), data.get("free_cash_flow", 1))

        if eps_growth is None and fcf_growth is None:
            return None

        scores = []
        if eps_growth is not None:
            if eps_growth > 0.10:
                scores.append(90)
            elif eps_growth > 0:
                scores.append(70)
            elif eps_growth > -0.10:
                scores.append(40)
            else:
                scores.append(15)

        if fcf_growth is not None:
            if fcf_growth > 0.10:
                scores.append(90)
            elif fcf_growth > 0:
                scores.append(70)
            elif fcf_growth > -0.10:
                scores.append(40)
            else:
                scores.append(15)

        return sum(scores) / len(scores) if scores else None

    def _peg_attractiveness(self, data: FinancialData) -> float | None:
        """PEG ratio scoring."""
        if not data.trailing_pe or data.trailing_pe <= 0:
            return None

        eps_list = [e for e in data.diluted_eps if e is not None and e > 0]
        if len(eps_list) < 2:
            return None

        years = len(eps_list) - 1
        growth = (eps_list[0] / eps_list[-1]) ** (1 / years) - 1
        if growth <= 0:
            return None

        peg = data.trailing_pe / (growth * 100)

        # Invert PEG tiers (lower PEG = higher score)
        for threshold, base_score in PEG_TIERS:
            if peg < threshold:
                return base_score + 10
        return 15  # PEG > 1.5
