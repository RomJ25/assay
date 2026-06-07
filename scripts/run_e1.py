#!/usr/bin/env python3
"""Experiment E1: A/B-test the three April-15 additions.

Runs four backtest configurations on the same 16-quarter S&P 500 window:
  - baseline: all features ON (current production config)
  - no_rd: ASSAY_RD_ADDBACK_ENABLED=False
  - no_safety: ASSAY_SAFETY_ENABLED=False
  - no_revenue: ASSAY_REVENUE_GATE_ENABLED=False

For each variant, computes selection alpha vs EW universe, hit rate (quarters
beating EW), Sharpe-like metric, average turnover. Decision rule per
docs/your-mission audit §6.2: a feature must beat baseline by ≥30 bps net of
t-cost AND directionally improve at least 10 of 16 quarters to keep its default.
"""

from __future__ import annotations

import csv
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import RESULTS_DIR  # noqa: E402

VARIANTS = [
    ("baseline", {}),
    ("no_rd", {"ASSAY_RD_ADDBACK_ENABLED": "false"}),
    ("no_safety", {"ASSAY_SAFETY_ENABLED": "false"}),
    ("no_revenue", {"ASSAY_REVENUE_GATE_ENABLED": "false"}),
]

YEARS = 4


@dataclass
class VariantMetrics:
    name: str
    n_quarters: int
    portfolio_cagr: float
    universe_cagr: float
    spy_cagr: float
    selection_alpha: float
    spy_alpha: float
    hit_rate_vs_universe: float  # fraction of quarters portfolio_return > universe_return
    sharpe_quarterly: float       # mean / std of quarterly portfolio returns
    avg_turnover: float | None
    avg_picks: float
    csv_path: Path


def cagr(quarterly_returns_pct: list[float]) -> float:
    """Compound CAGR from list of quarterly returns expressed in percent."""
    growth = 1.0
    for r in quarterly_returns_pct:
        growth *= (1.0 + r / 100.0)
    n_years = len(quarterly_returns_pct) / 4.0
    if n_years <= 0:
        return float("nan")
    return (growth ** (1.0 / n_years) - 1.0) * 100.0


def stddev(xs: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)


def parse_csv(path: Path) -> dict:
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def compute_metrics(name: str, csv_path: Path) -> VariantMetrics:
    rows = parse_csv(csv_path)
    portfolio = [float(r["portfolio_return"]) for r in rows]
    universe = [float(r["universe_return"]) for r in rows]
    spy = [float(r["spy_return"]) for r in rows]
    excess = [float(r["excess_return"]) for r in rows]
    turnovers = [float(r["turnover"]) for r in rows if r["turnover"]]
    picks = [int(r["num_picks"]) for r in rows]

    p_cagr = cagr(portfolio)
    u_cagr = cagr(universe)
    s_cagr = cagr(spy)

    hit_rate = sum(1 for e in excess if e > 0) / len(excess) if excess else 0.0
    p_mean = sum(portfolio) / len(portfolio)
    p_std = stddev(portfolio)
    sharpe = p_mean / p_std if p_std and not math.isnan(p_std) else float("nan")

    return VariantMetrics(
        name=name,
        n_quarters=len(rows),
        portfolio_cagr=p_cagr,
        universe_cagr=u_cagr,
        spy_cagr=s_cagr,
        selection_alpha=p_cagr - u_cagr,
        spy_alpha=p_cagr - s_cagr,
        hit_rate_vs_universe=hit_rate,
        sharpe_quarterly=sharpe,
        avg_turnover=(sum(turnovers) / len(turnovers)) if turnovers else None,
        avg_picks=sum(picks) / len(picks) if picks else 0.0,
        csv_path=csv_path,
    )


def run_variant(name: str, env_overrides: dict[str, str]) -> Path:
    """Run a single backtest variant in a subprocess and rename the CSV.

    Returns the path of the renamed CSV.
    """
    print(f"\n=== Running variant: {name} ===")
    print(f"    Env overrides: {env_overrides or '(none — defaults)'}")

    env = os.environ.copy()
    env.update(env_overrides)
    # Ensure deterministic output naming
    today = date.today().isoformat()
    main_csv = RESULTS_DIR / f"backtest_{today}.csv"
    detail_csv = RESULTS_DIR / f"backtest_detail_{today}.csv"

    # Move any pre-existing same-day CSV out of the way so we know the new run produced it
    backup_main = main_csv.with_suffix(".csv.preE1") if main_csv.exists() else None
    backup_detail = detail_csv.with_suffix(".csv.preE1") if detail_csv.exists() else None
    if backup_main:
        main_csv.rename(backup_main)
    if backup_detail:
        detail_csv.rename(backup_detail)

    cmd = [
        sys.executable, "main.py", "--backtest",
        f"--backtest-years={YEARS}",
    ]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        print("STDOUT:", proc.stdout[-2000:])
        print("STDERR:", proc.stderr[-2000:])
        raise RuntimeError(f"Backtest variant {name} failed (rc={proc.returncode})")

    if not main_csv.exists():
        raise RuntimeError(f"Expected output CSV not found: {main_csv}")

    # Rename to variant-specific paths
    new_main = RESULTS_DIR / f"e1_{name}_{today}.csv"
    new_detail = RESULTS_DIR / f"e1_{name}_detail_{today}.csv"
    main_csv.rename(new_main)
    if detail_csv.exists():
        detail_csv.rename(new_detail)

    # Restore any pre-existing same-day CSVs
    if backup_main:
        backup_main.rename(main_csv)
    if backup_detail:
        backup_detail.rename(detail_csv)

    print(f"    -> {new_main.name}")
    return new_main


def print_comparison_table(metrics: list[VariantMetrics], baseline: VariantMetrics) -> None:
    print("\n" + "=" * 78)
    print("EXPERIMENT E1 — A/B-test the April-15 additions")
    print("=" * 78)
    print(f"  Sample: {baseline.n_quarters} quarters, S&P 500, survivorship-free, equal-weight, 10 bps t-cost")
    print()
    print(f"{'Variant':<14} {'CAGR':>7} {'EW univ':>8} {'Alpha vs EW':>13} {'Δ vs base':>11} {'Hit rate':>9} {'Sharpe':>8} {'Picks':>7} {'Turn':>7}")
    print("-" * 90)
    for m in metrics:
        delta = (m.selection_alpha - baseline.selection_alpha) * 100  # bps
        delta_str = "—" if m.name == baseline.name else f"{delta:+.0f} bps"
        turn = f"{m.avg_turnover:.1f}%" if m.avg_turnover is not None else "n/a"
        print(
            f"{m.name:<14} "
            f"{m.portfolio_cagr:>6.2f}% "
            f"{m.universe_cagr:>7.2f}% "
            f"{m.selection_alpha:>+12.2f}% "
            f"{delta_str:>11} "
            f"{m.hit_rate_vs_universe*100:>7.1f}% "
            f"{m.sharpe_quarterly:>7.3f} "
            f"{m.avg_picks:>6.1f} "
            f"{turn:>7}"
        )
    print()
    print("Decision rule (per audit §6.2): a feature must beat baseline by ≥30 bps")
    print("net AND directionally improve in ≥10 of 16 quarters to keep its default.")
    print("Removing a feature = positive Δ for the 'no_X' run.")
    print()
    for m in metrics:
        if m.name == baseline.name:
            continue
        delta_bps = (m.selection_alpha - baseline.selection_alpha) * 100
        feature = m.name.replace("no_", "").upper()
        verdict_keep = "KEEP feature ON (removing it hurt by ≥30 bps)"
        verdict_drop = "DISABLE feature (removing it helped by ≥30 bps)"
        verdict_neutral = "NEUTRAL (delta < 30 bps in absolute terms)"
        if delta_bps >= 30:
            verdict = verdict_drop
        elif delta_bps <= -30:
            verdict = verdict_keep
        else:
            verdict = verdict_neutral
        print(f"  {feature:<8}: Δalpha = {delta_bps:+.0f} bps  →  {verdict}")
    print()
    print("Per-quarter spread vs baseline (positive = no_X variant beat baseline that quarter):")
    print()
    base_rows = parse_csv(baseline.csv_path)
    base_dates = [r["date"] for r in base_rows]
    base_returns = [float(r["portfolio_return"]) for r in base_rows]
    print(f"{'Quarter':<12} " + " ".join(f"{m.name[:10]:>11}" for m in metrics if m.name != baseline.name))
    variant_returns = {}
    for m in metrics:
        if m.name == baseline.name:
            continue
        rows = parse_csv(m.csv_path)
        variant_returns[m.name] = {r["date"]: float(r["portfolio_return"]) for r in rows}

    wins = {m.name: 0 for m in metrics if m.name != baseline.name}
    for d, br in zip(base_dates, base_returns):
        line = f"{d:<12}"
        for m in metrics:
            if m.name == baseline.name:
                continue
            vr = variant_returns[m.name].get(d)
            if vr is None:
                line += f"{'n/a':>12}"
                continue
            spread = vr - br
            if spread > 0:
                wins[m.name] += 1
            line += f"{spread:>+10.2f}%"
        print(line)
    print()
    for m in metrics:
        if m.name == baseline.name:
            continue
        feature = m.name.replace("no_", "").upper()
        print(f"  {feature:<8}: {m.name} variant beat baseline in {wins[m.name]}/{len(base_dates)} quarters")


def main():
    metrics = []
    baseline = None
    for name, env in VARIANTS:
        csv_path = run_variant(name, env)
        m = compute_metrics(name, csv_path)
        metrics.append(m)
        if name == "baseline":
            baseline = m

    if baseline is None:
        print("Error: baseline run not found")
        sys.exit(1)

    print_comparison_table(metrics, baseline)

    # Also save the comparison table as a structured CSV
    summary_path = RESULTS_DIR / f"e1_summary_{date.today().isoformat()}.csv"
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
    print(f"\nSummary CSV: {summary_path}")


if __name__ == "__main__":
    main()
