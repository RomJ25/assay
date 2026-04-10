"""Backtest report — Rich console output and CSV export."""

from __future__ import annotations

import csv
from datetime import date

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import RESULTS_DIR

console = Console()


def print_backtest_report(result) -> None:
    """Print the full backtest report to console."""
    m = result.metrics

    # Header
    console.print(Panel(
        f"[bold]ASSAY BACKTEST — S&P 500 VALUE + QUALITY[/bold]\n"
        f"Period: {result.effective_start} to {result.effective_end} "
        f"({m.total_quarters} quarters)\n"
        f"Rebalancing: Quarterly, equal-weight CONVICTION BUY picks",
        style="bold blue",
    ))

    # Limitations
    console.print(Panel(
        "[yellow]KNOWN LIMITATIONS[/yellow]\n"
        "  Survivorship bias: uses current S&P 500 list (est. 2-5% CAGR overstatement)\n"
        "  Sample size: below 30-period minimum for statistical significance\n"
        "  Data: Yahoo Finance (may include retroactive restatements)\n"
        "  This is preliminary evidence, not proof. Do NOT tune parameters based on results.",
        style="yellow",
    ))

    # Performance summary
    perf = Table(show_header=True, header_style="bold cyan", show_lines=False)
    perf.add_column("", width=20)
    perf.add_column("Portfolio", justify="right", width=14)
    perf.add_column("Universe (EW)", justify="right", width=14)
    perf.add_column("S&P 500 (SPY)", justify="right", width=14)

    perf.add_row("Total Return",
                 _pct(m.total_return), _pct(m.universe_total_return), _pct(m.spy_total_return))
    perf.add_row("CAGR",
                 _pct(m.cagr), _pct(m.universe_cagr), _pct(m.spy_cagr))
    perf.add_row("Max Drawdown", _pct(m.max_drawdown), "", "")
    perf.add_row("Sharpe Ratio", f"{m.sharpe_ratio:.2f}", "", "")

    console.print("\n[bold]PERFORMANCE SUMMARY[/bold]")
    console.print(perf)

    # Selection alpha
    alpha_style = "green" if m.selection_alpha > 0 else "red"
    console.print(f"\n[bold]SELECTION ALPHA (Portfolio vs Universe)[/bold]")
    console.print(f"  CAGR Difference: [{alpha_style}]{_pct(m.selection_alpha)}[/{alpha_style}]")
    console.print(f"  [dim]Measures whether the conviction matrix adds value beyond\n"
                  f"  equal-weight S&P 500 stock picking, controlling for biases.[/dim]")

    # Pick analysis
    console.print(f"\n[bold]PICK ANALYSIS[/bold]")
    console.print(f"  Avg picks/quarter     {m.avg_picks_per_quarter:.1f}")
    console.print(f"  Hit rate (vs univ.)   {m.hit_rate:.1f}%")
    console.print(f"  Avg excess return     {_pct(m.avg_excess_return / 100)}/qtr")
    console.print(f"  Avg turnover          {m.avg_turnover:.1f}%")

    # F-Score tier breakdown
    f_low = sum(1 for qr in result.quarters for p in qr.pick_details if p["piotroski_f"] <= 6)
    f_mid = sum(1 for qr in result.quarters for p in qr.pick_details if p["piotroski_f"] == 7)
    f_high = sum(1 for qr in result.quarters for p in qr.pick_details if p["piotroski_f"] >= 8)
    f_total = f_low + f_mid + f_high
    if f_total > 0:
        console.print(f"\n[bold]F-SCORE TIERS[/bold] (strongest quality signal)")
        console.print(f"  F=6       {f_low:3d}  ({f_low/f_total*100:.0f}%)")
        console.print(f"  F=7       {f_mid:3d}  ({f_mid/f_total*100:.0f}%)")
        console.print(f"  F=8-9     {f_high:3d}  ({f_high/f_total*100:.0f}%)")

    # Top-N concentrated portfolio analysis
    if result.top_n_metrics:
        console.print(f"\n[bold]CONCENTRATED PORTFOLIO — \"Best Ideas\" Analysis[/bold]")
        console.print("  [dim]Research (Cohen, Polk & Silli) shows highest-conviction positions"
                      "\n  outperform by 2.8-4.5% per year. Top-N picks are sorted by conviction"
                      "\n  score (√(V×Q)). Note: empirical testing shows conviction ordering has"
                      "\n  near-zero correlation with subsequent returns within CB (Kendall τ ≈ −0.04"
                      "\n  over 12 quarters). Treat Top-N as concentration analysis, not as evidence"
                      "\n  that higher-conviction picks are better.[/dim]")

        n_table = Table(show_header=True, header_style="bold cyan", show_lines=False)
        n_table.add_column("Portfolio", width=14)
        n_table.add_column("CAGR", justify="right", width=8)
        n_table.add_column("Total", justify="right", width=8)
        n_table.add_column("vs SPY", justify="right", width=8)
        n_table.add_column("Sharpe", justify="right", width=7)
        n_table.add_column("MaxDD", justify="right", width=8)
        n_table.add_column("Avg Picks", justify="right", width=9)

        for n in (1, 3, 5):
            if n in result.top_n_metrics:
                tm = result.top_n_metrics[n]
                vs_spy = tm.cagr - m.spy_cagr
                vs_style = "green" if vs_spy > 0 else "red"
                n_table.add_row(
                    f"Top {n}",
                    _pct(tm.cagr),
                    _pct(tm.total_return),
                    f"[{vs_style}]{_pct(vs_spy)}[/{vs_style}]",
                    f"{tm.sharpe_ratio:.2f}",
                    f"{tm.max_drawdown*100:+.1f}%",
                    f"{tm.avg_picks_per_quarter:.1f}",
                )

        # Add full portfolio and SPY for comparison
        vs_spy_full = m.cagr - m.spy_cagr
        vs_style = "green" if vs_spy_full > 0 else "red"
        n_table.add_row(
            f"All {m.avg_picks_per_quarter:.0f}",
            _pct(m.cagr),
            _pct(m.total_return),
            f"[{vs_style}]{_pct(vs_spy_full)}[/{vs_style}]",
            f"{m.sharpe_ratio:.2f}",
            f"{m.max_drawdown*100:+.1f}%",
            f"{m.avg_picks_per_quarter:.1f}",
        )
        n_table.add_row("SPY", _pct(m.spy_cagr), _pct(m.spy_total_return), "-", "-", "-", "-")
        console.print(n_table)

        n_quarters = m.total_quarters
        if n_quarters < 30:
            console.print(f"  [yellow]⚠ {n_quarters} quarters — minimum 30 required for statistical inference[/yellow]")

        console.print(f"\n  [dim]Confidence tiers within CB (aggregate across 12-quarter investigation):[/dim]")
        console.print(f"  [dim]  HIGH (V,Q ≥ 85): +6.7%/qtr avg  |  MOD (V,Q ≥ 75): +5.4%  |  LOW (near 70): +3.3%[/dim]")
        console.print(f"  [dim]  Gradient is directional in aggregate but not reliable per-quarter.[/dim]")

    # Quarterly breakdown
    if result.portfolio_returns:
        console.print(f"\n[bold]QUARTERLY BREAKDOWN[/bold]")
        qtable = Table(show_header=True, header_style="bold", show_lines=False)
        qtable.add_column("#", style="dim", width=3)
        qtable.add_column("Period", width=12)
        qtable.add_column("Picks", justify="right", width=5)
        qtable.add_column("Portfolio", justify="right", width=11)
        qtable.add_column("Universe", justify="right", width=11)
        qtable.add_column("SPY", justify="right", width=11)
        qtable.add_column("Excess", justify="right", width=11)
        qtable.add_column("Turnover", justify="right", width=11)

        for i, rec in enumerate(result.portfolio_returns, 1):
            excess = rec["excess_return"]
            ex_style = "green" if excess > 0 else "red" if excess < 0 else ""
            turnover_str = f"{rec['turnover']:.0f}%" if rec.get("turnover") is not None else "--"
            qtable.add_row(
                str(i),
                rec["date"],
                str(rec["num_picks"]),
                f"{rec['portfolio_return']:+.1f}%",
                f"{rec['universe_return']:+.1f}%",
                f"{rec['spy_return']:+.1f}%",
                f"[{ex_style}]{excess:+.1f}%[/{ex_style}]",
                turnover_str,
            )

        console.print(qtable)


def save_backtest_csv(result) -> str:
    """Save backtest results to CSV. Returns file path."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"backtest_{date.today().isoformat()}.csv"

    fieldnames = [
        "date", "next_date", "num_picks", "portfolio_return",
        "universe_return", "spy_return", "excess_return", "turnover",
    ]

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in result.portfolio_returns:
            writer.writerow(rec)

    console.print(f"\n[green]Backtest CSV saved to {path}[/green]")

    # Detail CSV: per-stock picks with scores
    detail_path = RESULTS_DIR / f"backtest_detail_{date.today().isoformat()}.csv"
    detail_fields = [
        "quarter", "ticker", "sector", "value_score", "quality_score", "piotroski_f",
        "momentum_pct",
    ]
    with open(detail_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=detail_fields)
        writer.writeheader()
        for qr in result.quarters:
            for pick in qr.pick_details:
                row = {"quarter": qr.date.isoformat()}
                row.update(pick)
                writer.writerow(row)

    console.print(f"[green]Detail CSV saved to {detail_path}[/green]")
    return str(path)


def _pct(value: float) -> str:
    """Format a decimal as a percentage string."""
    return f"{value * 100:+.1f}%"
