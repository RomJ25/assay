#!/usr/bin/env python3
"""Experiment E4: universe-expansion comparison (S&P 500 vs Russell 1000).

Audit §6.4. Pre-conditions complete:
  - §6.3: real historical betas now computed (E2 baseline = −0.21%/yr)
  - §6.4 prep: IWB historical prices backfilled (cache now 1003 tickers vs 505)

This script runs identical screens on:
  (a) S&P 500 (current default, 504 historical-price tickers, ~500 per quarter)
  (b) Russell 1000 ($3B floor, ~780 historical-price tickers per quarter)

Pass condition (per audit §6.4 / Experiment E4): selection alpha on Russell 1000
must exceed S&P 500 by ≥80 bps net of t-cost AND directionally improve in
at least 10 of 16 quarters.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_e1 import compute_metrics, parse_csv  # noqa: E402
from config import RESULTS_DIR  # noqa: E402

VARIANTS = [
    ("e4_sp500", ["--universe", "sp500"]),
    ("e4_russell1000", ["--universe", "russell1000"]),
]
YEARS = 4


def run_universe_variant(name: str, extra_args: list[str]) -> Path:
    print(f"\n=== Running variant: {name} (args: {extra_args}) ===")
    today = date.today().isoformat()
    main_csv = RESULTS_DIR / f"backtest_{today}.csv"
    detail_csv = RESULTS_DIR / f"backtest_detail_{today}.csv"
    backup_main = main_csv.with_suffix(".csv.preE4") if main_csv.exists() else None
    backup_detail = detail_csv.with_suffix(".csv.preE4") if detail_csv.exists() else None
    if backup_main:
        main_csv.rename(backup_main)
    if backup_detail:
        detail_csv.rename(backup_detail)

    cmd = [sys.executable, "main.py", "--backtest", f"--backtest-years={YEARS}"] + extra_args
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
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
    for name, args in VARIANTS:
        csv_path = run_universe_variant(name, args)
        metrics.append(compute_metrics(name, csv_path))

    sp = next(m for m in metrics if m.name == "e4_sp500")
    r1k = next(m for m in metrics if m.name == "e4_russell1000")
    delta_bps = (r1k.selection_alpha - sp.selection_alpha) * 100

    print("\n" + "=" * 84)
    print("EXPERIMENT E4 — Universe expansion: S&P 500 vs Russell 1000")
    print("=" * 84)
    print(f"  Sample: {sp.n_quarters} quarters, survivorship-free, equal-weight, 10 bps t-cost")
    print(f"  Config: post-E1/E2 (real historical betas, R&D + Safety + Revenue gate ON)")
    print()
    print(f"{'Variant':<18} {'CAGR':>7} {'EW univ':>8} {'Alpha vs EW':>13} {'Alpha vs SPY':>13} {'Hit rate':>9} {'Sharpe':>8} {'Picks':>7} {'Turn':>7}")
    print("-" * 96)
    for m in metrics:
        turn = f"{m.avg_turnover:.1f}%" if m.avg_turnover is not None else "n/a"
        print(
            f"{m.name:<18} "
            f"{m.portfolio_cagr:>6.2f}% "
            f"{m.universe_cagr:>7.2f}% "
            f"{m.selection_alpha:>+12.2f}% "
            f"{m.spy_alpha:>+12.2f}% "
            f"{m.hit_rate_vs_universe*100:>7.1f}% "
            f"{m.sharpe_quarterly:>7.3f} "
            f"{m.avg_picks:>6.1f} "
            f"{turn:>7}"
        )
    print()
    print(f"Δ (R1000 − S&P 500) selection alpha: {delta_bps:+.0f} bps/yr")

    # Per-quarter spread analysis
    sp_rows = parse_csv(sp.csv_path)
    r_rows = parse_csv(r1k.csv_path)
    sp_excess = {r["date"]: float(r["excess_return"]) for r in sp_rows}
    r_excess = {r["date"]: float(r["excess_return"]) for r in r_rows}
    common_dates = sorted(set(sp_excess) & set(r_excess))

    wins = 0
    print(f"\nPer-quarter excess-return comparison (vs each universe's EW benchmark):")
    print(f"{'Quarter':<12} {'S&P 500':>10} {'R1000':>10} {'R1000 − SP':>12}")
    for d in common_dates:
        sp_ex = sp_excess[d]
        r_ex = r_excess[d]
        diff = r_ex - sp_ex
        if diff > 0:
            wins += 1
        print(f"{d:<12} {sp_ex:>+9.2f}% {r_ex:>+9.2f}% {diff:>+11.2f}%")
    print()
    print(f"R1000 excess return > S&P 500 excess return in {wins}/{len(common_dates)} quarters")
    print()
    print("Pass condition (audit §6.4): ≥80 bps alpha improvement AND ≥10 of 16 quarters.")
    if delta_bps >= 80 and wins >= 10:
        verdict = "PASS — switch default universe to Russell 1000"
    elif delta_bps >= 30:
        verdict = "DIRECTIONAL — Russell 1000 helps but below the 80 bps / 10-quarter bar"
    elif delta_bps > -30:
        verdict = "NEUTRAL — universe choice doesn't materially affect alpha at n=16"
    else:
        verdict = "FAIL — Russell 1000 underperforms; investigate cache state or universe approximation bias"
    print(f"Verdict: {verdict}")

    # Save summary CSV
    summary_path = RESULTS_DIR / f"e4_summary_{date.today().isoformat()}.csv"
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
    print(f"\nE4 summary CSV: {summary_path}")


if __name__ == "__main__":
    main()
