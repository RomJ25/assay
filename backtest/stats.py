"""Statistical-rigor helpers for backtest results (Slice G).

The repo reports many "+X bps from gate Y" findings (e1, e2, e5...) without
standard errors or multiple-testing correction. At the typical sample size
of 16 quarters, most of those reported deltas sit below the noise floor —
this module makes that visible.

The helpers are deliberately simple:

  alpha_stats(quarterly_returns_or_alphas) → AlphaStats with mean/SE/CI/t.

  bonferroni_threshold(num_tests, df, alpha=0.05) → critical |t|.

Use these alongside any reported alpha or alpha-delta so the reader can see
whether the result is distinguishable from zero, and from zero across the
multiple tests run in the same e1–e5 grid.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AlphaStats:
    """Summary statistics for a sequence of per-period alpha (or excess-return) values.

    `mean`, `std`, `se` and `ci_low`/`ci_high` are all in the same units as the
    input (typically per-period decimals — caller annualizes if desired).
    """

    n: int
    mean: float
    std: float
    se: float
    t_stat: float
    ci_low: float
    ci_high: float
    significant_at_05: bool
    bonferroni_significant: bool


def alpha_stats(
    series: list[float],
    *,
    num_tests: int = 1,
    alpha: float = 0.05,
) -> AlphaStats:
    """Compute mean / SE / 95% CI / t-stat for a per-period return or alpha series.

    Args:
        series: Per-period values (e.g., quarterly excess returns vs benchmark).
        num_tests: Number of hypotheses being tested in the same family
            (e.g., the 5 variants in e1–e5). Used for Bonferroni correction.
            Default 1 means no correction.
        alpha: Family-wise significance level. Default 0.05.

    Returns:
        AlphaStats with both raw and Bonferroni-corrected significance flags.
    """
    n = len(series)
    if n < 2:
        raise ValueError("Need at least 2 observations to compute stats")

    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / (n - 1)
    std = math.sqrt(var)
    se = std / math.sqrt(n)
    t_stat = mean / se if se > 0 else 0.0

    df = n - 1
    t_crit_raw = _t_critical(df, alpha)
    t_crit_bonf = _t_critical(df, alpha / max(num_tests, 1))
    half_width = t_crit_raw * se

    return AlphaStats(
        n=n,
        mean=mean,
        std=std,
        se=se,
        t_stat=t_stat,
        ci_low=mean - half_width,
        ci_high=mean + half_width,
        significant_at_05=abs(t_stat) >= t_crit_raw,
        bonferroni_significant=abs(t_stat) >= t_crit_bonf,
    )


def bonferroni_threshold(num_tests: int, df: int, alpha: float = 0.05) -> float:
    """Critical |t| at which a single test in a family of `num_tests` clears
    family-wise alpha after Bonferroni correction.
    """
    return _t_critical(df, alpha / max(num_tests, 1))


# ── t-critical lookup ─────────────────────────────────────────────────────
# Two-sided critical values at common alphas. Linear-interpolated by df.
# Avoids a SciPy dependency for a tiny use case. Accuracy is sufficient for
# guidance — a published paper would use scipy.stats.t.ppf.

_T_TABLE: dict[float, list[tuple[int, float]]] = {
    # Two-sided alpha → list of (df, t_crit) pairs sorted by df
    0.05:  [(5, 2.571), (10, 2.228), (15, 2.131), (20, 2.086), (30, 2.042),
            (60, 2.000), (120, 1.980), (10**6, 1.960)],
    0.025: [(5, 3.163), (10, 2.634), (15, 2.490), (20, 2.423), (30, 2.360),
            (60, 2.299), (120, 2.270), (10**6, 2.241)],
    0.01:  [(5, 4.032), (10, 3.169), (15, 2.947), (20, 2.845), (30, 2.750),
            (60, 2.660), (120, 2.617), (10**6, 2.576)],
    0.005: [(5, 4.773), (10, 3.581), (15, 3.286), (20, 3.153), (30, 3.030),
            (60, 2.915), (120, 2.860), (10**6, 2.807)],
    0.001: [(5, 6.869), (10, 4.587), (15, 4.073), (20, 3.850), (30, 3.646),
            (60, 3.460), (120, 3.373), (10**6, 3.291)],
}


def _t_critical(df: int, alpha: float) -> float:
    """Two-sided t-critical at level `alpha` and `df` degrees of freedom.

    Uses linear interpolation between tabulated rows. For alphas not in the
    table, falls back to the nearest tabulated alpha (conservative).
    """
    df = max(df, 1)
    # Pick the closest tabulated alpha (linear in alpha is too unstable; nearest
    # is the safe practical choice).
    closest_alpha = min(_T_TABLE.keys(), key=lambda a: abs(a - alpha))
    rows = _T_TABLE[closest_alpha]
    # Find bracketing rows
    if df <= rows[0][0]:
        return rows[0][1]
    if df >= rows[-1][0]:
        return rows[-1][1]
    for (df_lo, t_lo), (df_hi, t_hi) in zip(rows, rows[1:]):
        if df_lo <= df <= df_hi:
            frac = (df - df_lo) / (df_hi - df_lo)
            return t_lo + frac * (t_hi - t_lo)
    return rows[-1][1]
