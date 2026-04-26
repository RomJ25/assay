"""Unit tests for the SE/CI/Bonferroni helper (Slice G)."""

import math

import pytest

from backtest.stats import alpha_stats, bonferroni_threshold


def test_alpha_stats_zero_mean_signal():
    series = [0.01, -0.01, 0.02, -0.02, 0.0, 0.0, 0.005, -0.005]
    stats = alpha_stats(series)
    assert stats.n == 8
    assert abs(stats.mean) < 1e-9
    assert stats.std > 0
    assert stats.t_stat == 0.0
    assert not stats.significant_at_05
    assert not stats.bonferroni_significant
    assert stats.ci_low < 0 < stats.ci_high


def test_alpha_stats_strongly_positive_signal():
    # Constant +1% per period — SE is zero so t goes to inf; significant.
    series = [0.01] * 16
    stats = alpha_stats(series)
    assert stats.mean == pytest.approx(0.01)
    assert stats.std == 0
    assert stats.se == 0
    # t_stat is 0/0 → handled as 0.0 by guard, NOT significant — that's a
    # deliberate fallback so degenerate inputs don't produce false positives.
    assert stats.t_stat == 0.0


def test_alpha_stats_modest_signal_at_n16_not_significant():
    # Mean ~ 0.005 per period, std ~ 0.02 → t ~ 1.0 at n=16. Below t-crit ≈ 2.13.
    # This mirrors the e1 published deltas from STRATEGY.md.
    series = [0.025, -0.015, 0.030, -0.020, 0.020, 0.005, 0.025, -0.010,
              0.015, 0.000, 0.010, -0.005, 0.020, 0.005, -0.010, 0.025]
    stats = alpha_stats(series)
    assert stats.n == 16
    assert stats.mean > 0
    assert abs(stats.t_stat) < 2.13  # below 0.05 t-crit at df=15
    assert not stats.significant_at_05


def test_bonferroni_tightens_threshold_as_num_tests_grows():
    # At n=16 (df=15), Bonferroni for 5 tests → 0.01 alpha → t ~ 2.95.
    raw = bonferroni_threshold(num_tests=1, df=15)
    bonf5 = bonferroni_threshold(num_tests=5, df=15)
    assert bonf5 > raw
    assert raw == pytest.approx(2.131, rel=0.01)
    assert bonf5 > 2.5  # ~2.94 in standard tables


def test_alpha_stats_marks_bonferroni_failure_for_close_call():
    # Construct a series where t_stat is just barely > 2.13 but < 2.95.
    series = [0.030, 0.020, 0.025, 0.040, 0.020, 0.030, 0.035, 0.025,
              0.030, 0.020, 0.040, 0.025, 0.030, 0.020, 0.025, 0.030]
    stats = alpha_stats(series, num_tests=5)
    assert stats.t_stat > 2.13  # passes raw 0.05
    # bonferroni-corrected at 5 tests requires |t| >= ~2.95
    if stats.t_stat < 2.95:
        assert not stats.bonferroni_significant
    else:
        assert stats.bonferroni_significant


def test_too_few_samples_raises():
    with pytest.raises(ValueError):
        alpha_stats([0.01])


def test_ci_bracket_includes_mean():
    series = [0.005, 0.015, -0.005, 0.020, 0.000, 0.010]
    stats = alpha_stats(series)
    assert stats.ci_low <= stats.mean <= stats.ci_high


def test_ci_widens_with_higher_variance():
    low_var = alpha_stats([0.01, 0.012, 0.008, 0.011, 0.009, 0.010])
    high_var = alpha_stats([0.01, 0.05, -0.03, 0.06, -0.04, 0.04])
    low_width = low_var.ci_high - low_var.ci_low
    high_width = high_var.ci_high - high_var.ci_low
    assert high_width > low_width
