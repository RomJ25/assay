#!/usr/bin/env python3
"""Experiment E2: re-test the Safety dimension after historical-beta backfill.

E1 (2026-04-17) found that disabling Safety improved selection alpha by 44 bps,
but the test was contaminated: backtest set beta=None, so what got measured was
"the leverage component of Safety alone." With historical betas now computed
in backtest/historical_beta.py and injected at backtest/engine.py, Safety in
backtest matches the production formula (½ inverse-beta + ½ inverse-leverage).

This script re-runs the no_safety vs baseline A/B with real betas. Decision rule
unchanged from E1: a feature must beat baseline by ≥30 bps net of t-cost AND
directionally improve in ≥10 of 16 quarters to keep its default.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Reuse the E1 runner — same machinery, different label.
from scripts.run_e1 import (  # noqa: E402
    compute_metrics,
    print_comparison_table,
    run_variant,
)
from config import RESULTS_DIR  # noqa: E402
import csv
from datetime import date


VARIANTS = [
    ("baseline_e2", {}),
    ("no_safety_e2", {"ASSAY_SAFETY_ENABLED": "false"}),
]


def main():
    metrics = []
    baseline = None
    for name, env in VARIANTS:
        csv_path = run_variant(name, env)
        m = compute_metrics(name, csv_path)
        metrics.append(m)
        if name == "baseline_e2":
            baseline = m

    if baseline is None:
        print("Error: baseline run not found")
        sys.exit(1)

    print_comparison_table(metrics, baseline)

    summary_path = RESULTS_DIR / f"e2_summary_{date.today().isoformat()}.csv"
    with open(summary_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "variant", "n_quarters", "portfolio_cagr_pct", "universe_cagr_pct",
            "spy_cagr_pct", "selection_alpha_pct", "spy_alpha_pct",
            "hit_rate_vs_universe", "sharpe_quarterly",
            "avg_turnover_pct", "avg_picks",
        ])
        for m in metrics:
            w.writerow([
                m.name, m.n_quarters, f"{m.portfolio_cagr:.4f}",
                f"{m.universe_cagr:.4f}", f"{m.spy_cagr:.4f}",
                f"{m.selection_alpha:.4f}", f"{m.spy_alpha:.4f}",
                f"{m.hit_rate_vs_universe:.4f}", f"{m.sharpe_quarterly:.4f}",
                f"{m.avg_turnover:.4f}" if m.avg_turnover is not None else "",
                f"{m.avg_picks:.2f}",
            ])
    print(f"\nE2 summary CSV: {summary_path}")


if __name__ == "__main__":
    main()
