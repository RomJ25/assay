#!/usr/bin/env python3
"""Experiment E5: buy/hold spread (Novy-Marx & Velikov 2023).

Audit §6.5. Hypothesis: enter at a stricter bar (e.g., V≥80, Q≥80), hold while
in the existing CB-eligible region (V≥70, Q≥70 — now QGP under the modified
classifier). Cuts turnover with minimal alpha loss; should reduce tax drag.

Three variants on the post-§6.3+§6.4 baseline:
  baseline_e5: BUY=70 (current default; identical to e4_russell1000)
  buy75:        BUY=75 (mild lift)
  buy80:        BUY=80 (the canonical Novy-Marx-Velikov spread)

Pass condition (audit §6.5): turnover reduction ≥30% AND alpha loss ≤10 bps.
Bonus if alpha actually improves.

Run on Russell 1000 universe so this experiment uses the post-§6.4 best baseline.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_e1 import compute_metrics, parse_csv  # noqa: E402
from config import RESULTS_DIR  # noqa: E402

VARIANTS = [
    ("e5_buy70", {}),
    ("e5_buy75", {"ASSAY_BUY_VALUE_THRESHOLD": "75", "ASSAY_BUY_QUALITY_THRESHOLD": "75"}),
    ("e5_buy80", {"ASSAY_BUY_VALUE_THRESHOLD": "80", "ASSAY_BUY_QUALITY_THRESHOLD": "80"}),
]
YEARS = 4
UNIVERSE = "russell1000"


def run_variant_with_universe(name: str, env_overrides: dict[str, str]) -> Path:
    print(f"\n=== Running variant: {name} ===")
    print(f"    Env overrides: {env_overrides or '(none — defaults)'}")

    today = date.today().isoformat()
    main_csv = RESULTS_DIR / f"backtest_{today}.csv"
    detail_csv = RESULTS_DIR / f"backtest_detail_{today}.csv"
    backup_main = main_csv.with_suffix(".csv.preE5") if main_csv.exists() else None
    backup_detail = detail_csv.with_suffix(".csv.preE5") if detail_csv.exists() else None
    if backup_main:
        main_csv.rename(backup_main)
    if backup_detail:
        detail_csv.rename(backup_detail)

    env = os.environ.copy()
    env.update(env_overrides)
    cmd = [
        sys.executable, "main.py", "--backtest",
        f"--backtest-years={YEARS}",
        f"--universe={UNIVERSE}",
    ]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        print("STDOUT:", proc.stdout[-2000:])
        print("STDERR:", proc.stderr[-2000:])
        raise RuntimeError(f"Backtest variant {name} failed (rc={proc.returncode})")
    if not main_csv.exists():
        raise RuntimeError(f"Expected output CSV not found: {main_csv}")

    new_main = RESULTS_DIR / f"{name}_{today}.csv"
    new_detail = RESULTS_DIR / f"{name}_detail_{today}.csv"
    main_csv.rename(new_main)
    if detail_csv.exists():
        detail_csv.rename(new_detail)
    if backup_main:
        backup_main.rename(main_csv)
    if backup_detail:
        backup_detail.rename(detail_csv)

    print(f"    -> {new_main.name}")
    return new_main


def main():
    metrics = []
    for name, env in VARIANTS:
        csv_path = run_variant_with_universe(name, env)
        metrics.append(compute_metrics(name, csv_path))

    baseline = metrics[0]

    print("\n" + "=" * 92)
    print(f"EXPERIMENT E5 — Buy/hold spread on {UNIVERSE.upper()} (post-E1/E2/E4 config)")
    print("=" * 92)
    print(f"  Sample: {baseline.n_quarters} quarters, survivorship-free, equal-weight, 10 bps t-cost")
    print()
    print(f"{'Variant':<14} {'CAGR':>7} {'EW univ':>8} {'Alpha vs EW':>13} {'Δalpha':>9} {'Sharpe':>8} {'Picks':>7} {'Turn':>7} {'Δturn':>9}")
    print("-" * 92)
    for m in metrics:
        delta_alpha = (m.selection_alpha - baseline.selection_alpha) * 100
        delta_alpha_str = "—" if m is baseline else f"{delta_alpha:+.0f} bps"
        delta_turn = (m.avg_turnover - baseline.avg_turnover) if (
            m.avg_turnover is not None and baseline.avg_turnover is not None) else None
        delta_turn_str = "—" if m is baseline else (f"{delta_turn:+.1f}pp" if delta_turn is not None else "n/a")
        turn = f"{m.avg_turnover:.1f}%" if m.avg_turnover is not None else "n/a"
        print(
            f"{m.name:<14} "
            f"{m.portfolio_cagr:>6.2f}% "
            f"{m.universe_cagr:>7.2f}% "
            f"{m.selection_alpha:>+12.2f}% "
            f"{delta_alpha_str:>9} "
            f"{m.sharpe_quarterly:>7.3f} "
            f"{m.avg_picks:>6.1f} "
            f"{turn:>7} "
            f"{delta_turn_str:>9}"
        )
    print()
    for m in metrics:
        if m is baseline:
            continue
        delta_alpha = (m.selection_alpha - baseline.selection_alpha) * 100
        delta_turn = (m.avg_turnover - baseline.avg_turnover) if (
            m.avg_turnover is not None and baseline.avg_turnover is not None) else None
        delta_turn_pct = (delta_turn / baseline.avg_turnover * 100) if (
            delta_turn is not None and baseline.avg_turnover) else None
        print(f"  {m.name}: Δalpha {delta_alpha:+.0f} bps, "
              f"turnover change {delta_turn:+.1f}pp ({delta_turn_pct:+.0f}%)" if delta_turn_pct is not None
              else f"  {m.name}: Δalpha {delta_alpha:+.0f} bps, turnover unchanged")
    print()
    print("Pass condition (audit §6.5): turnover reduction ≥30% AND alpha loss ≤10 bps.")
    for m in metrics:
        if m is baseline:
            continue
        delta_alpha = (m.selection_alpha - baseline.selection_alpha) * 100
        delta_turn_pct = (m.avg_turnover - baseline.avg_turnover) / baseline.avg_turnover * 100 if (
            m.avg_turnover is not None and baseline.avg_turnover) else 0
        passes_turn = delta_turn_pct <= -30
        passes_alpha = delta_alpha >= -10
        if passes_turn and passes_alpha:
            verdict = "PASS — efficiency win, ship default"
        elif delta_alpha > 0 and delta_turn_pct < 0:
            verdict = "BONUS — alpha and turnover both improved"
        elif passes_turn and not passes_alpha:
            verdict = "PARTIAL — turnover cut but alpha cost too large"
        else:
            verdict = "FAIL — turnover reduction below the 30% bar"
        print(f"  {m.name}: {verdict}")

    summary_path = RESULTS_DIR / f"e5_summary_{date.today().isoformat()}.csv"
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
    print(f"\nE5 summary CSV: {summary_path}")


if __name__ == "__main__":
    main()
