"""Rich terminal output — conviction buys with earnings yield, quality, and context."""

from __future__ import annotations

from datetime import date

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

_CRITERION_LABELS = [
    ("net_income_positive", "NI"),
    ("ocf_positive", "OCF"),
    ("roa_improving", "ROA"),
    ("accruals_quality", "Accrual"),
    ("debt_ratio_decreasing", "Debt"),
    ("current_ratio_up", "CurRatio"),
    ("no_dilution", "NoDilute"),
    ("gross_margin_up", "Margin"),
    ("asset_turnover_up", "Turnover"),
]

_CONF_STYLE = {"HIGH": "bold green", "MODERATE": "yellow", "LOW": "red"}


def print_report(today: date, results: list[dict], top_n: int = 20,
                 wide: bool = False, breakdown: bool = False,
                 include_financials: bool = False):
    """Print the screening report."""
    total = len(results)
    sorted_results = sorted(results, key=lambda r: r.get("conviction_score") or 0, reverse=True)

    exclusion_note = "" if include_financials else " | [yellow]Financials/RE excluded[/yellow]"
    console.print()
    console.print(Panel(
        f"[bold]ASSAY — S&P 500 VALUE + QUALITY SCREENER[/bold]\n"
        f"Date: {today.isoformat()} | Screened: {total} stocks{exclusion_note}\n"
        f"Value: Earnings Yield rank (Carlisle) | Quality: Piotroski + Gross Profitability (Novy-Marx)\n"
        f"[dim]Research tool for idea generation. Not a trading signal. Minimum 3-5 year horizon.[/dim]",
        style="bold blue",
    ))

    # Conviction Buys — sorted by opportunity score (definitive ranking)
    buys = [r for r in sorted_results if r.get("classification") == "CONVICTION BUY"]
    if buys:
        buys.sort(key=lambda r: r.get("opportunity_score") or 0, reverse=True)
        _print_main_table("CONVICTION BUYS — Ranked by Opportunity Score", buys[:top_n], "green", wide, breakdown)

    # Value Traps
    traps = [r for r in sorted_results if r.get("classification") == "VALUE TRAP"]
    if traps:
        _print_main_table("VALUE TRAPS — Cheap but Low Quality (AVOID)", traps[:10], "red", wide, breakdown)
        financial_traps = [r for r in traps if r.get("sector") == "Financials"]
        if financial_traps:
            console.print(
                "[dim]Note: Financial sector stocks (e.g. banks) may appear here due to "
                "bank-specific balance sheet structure, not actual distress.[/dim]"
            )

    # Watch List
    watch = [r for r in sorted_results if r.get("classification") == "WATCH LIST"]
    if watch:
        _print_main_table("WATCH LIST — Cheap, Moderate Quality (Investigate)", watch[:10], "yellow", wide, breakdown)

    # Summary
    from collections import Counter
    counts = Counter(r.get("classification") for r in sorted_results)
    console.print("\n[bold]Classification Summary:[/bold]")
    for cl, n in counts.most_common():
        console.print(f"  {cl}: {n}")

    # Sector breakdown of conviction buys
    if buys:
        sectors: dict[str, list[str]] = {}
        for r in buys:
            sectors.setdefault(r.get("sector", "?"), []).append(r["ticker"])
        console.print("\n[bold]Conviction Buys by Sector:[/bold]")
        for s, ticks in sorted(sectors.items(), key=lambda x: -len(x[1])):
            console.print(f"  {s}: {len(ticks)} — {', '.join(ticks)}")
    console.print()


def _format_breakdown(r: dict) -> str:
    """Format Piotroski criterion breakdown as a compact string."""
    bd = r.get("piotroski_breakdown", {})
    criteria = bd.get("criteria", {})
    if not criteria:
        return ""
    parts = []
    for key, label in _CRITERION_LABELS:
        c = criteria.get(key, {})
        mark = "\u2713" if c.get("pass") else "\u2717"
        parts.append(f"{mark}{label}")
    raw = bd.get("raw_score", "?")
    return f"F={raw}/9: {' '.join(parts)}"


def _print_main_table(title: str, results: list[dict], color: str,
                      wide: bool = False, breakdown: bool = False):
    """Print a table with earnings yield, quality metrics, and context.

    Normal mode (11 cols, ~105 chars): scores + key context
    Wide mode (16 cols, ~155 chars): adds F-Score, GP/A, P/E, 52wH, Sector
    """
    console.print(f"\n[bold {color}]{title}[/bold {color}]")

    company_w = 25 if wide else 20

    has_opp = any(r.get("opportunity_score") is not None for r in results)

    table = Table(show_header=True, header_style=f"bold {color}", show_lines=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Ticker", style="bold", width=6)
    table.add_column("Company", width=company_w, overflow="ellipsis")
    table.add_column("Price", justify="right", width=7)
    if has_opp:
        table.add_column("Opp", justify="right", width=4, style="bold")
    table.add_column("EY%", justify="right", width=5)
    table.add_column("V", justify="right", width=3)
    table.add_column("Q", justify="right", width=3)
    table.add_column("Conv", justify="right", width=4)
    if r_has_confidence(results):
        table.add_column("Conf", justify="center", width=4)
    if has_opp:
        table.add_column("Trj", justify="right", width=3)
    table.add_column("F", justify="right", width=4)
    if wide:
        table.add_column("GP/A", justify="right", width=5)
        table.add_column("P/E", justify="right", width=5)
    table.add_column("Analyst", justify="right", width=12)
    if wide:
        table.add_column("52wH", justify="right", width=6)
    table.add_column("DCF", justify="right", width=8)

    show_conf = r_has_confidence(results)

    for i, r in enumerate(results, 1):
        ey = f"{r['earnings_yield']:.1f}" if r.get("earnings_yield") else "-"
        v = f"{r['value_score']:.0f}" if r.get("value_score") is not None else "-"
        q = f"{r['quality_score']:.0f}" if r.get("quality_score") is not None else "-"
        cv = f"{r['conviction_score']:.0f}" if r.get("conviction_score") is not None else "-"
        opp = f"{r['opportunity_score']:.0f}" if r.get("opportunity_score") is not None else "-"
        trj = f"{r['trajectory_score']:.0f}" if r.get("trajectory_score") is not None else "-"
        f_sc = f"{r.get('piotroski_f', 0)}/9"
        gpa = f"{r['gross_profitability']:.0%}" if r.get("gross_profitability") else "-"

        if r.get("analyst_target") and r.get("analyst_upside") is not None:
            up = r["analyst_upside"]
            analyst = f"${r['analyst_target']:.0f}({up:+.0f}%)"
        else:
            analyst = "-"

        fh = f"{r['pct_from_52w_high']:+.0f}%" if r.get("pct_from_52w_high") is not None else "-"
        dcf = f"${r['dcf_base']:.0f}" if r.get("dcf_base") else "-"

        row = [str(i), r.get("ticker", ""), (r.get("company", "") or "")[:company_w],
               f"${r.get('price', 0):.0f}"]
        if has_opp:
            row.append(opp)
        row.extend([ey, v, q, cv])
        if show_conf:
            conf = r.get("confidence") or ""
            style = _CONF_STYLE.get(conf, "")
            row.append(f"[{style}]{conf[:3]}[/{style}]" if conf else "-")
        if has_opp:
            row.append(trj)
        row.append(f_sc)
        if wide:
            row.extend([gpa])
            row.append(f"{r['pe_ratio']:.1f}" if r.get("pe_ratio") else "-")
        row.append(analyst)
        if wide:
            row.append(fh)
        row.append(dcf)

        table.add_row(*row)

    console.print(table)

    # Breakdown: print criterion grid below the table
    if breakdown:
        console.print(f"  [dim]Piotroski Criterion Breakdown:[/dim]")
        for r in results:
            bd_str = _format_breakdown(r)
            if bd_str:
                console.print(f"    [bold]{r.get('ticker', ''):6s}[/bold] {bd_str}")


def r_has_confidence(results: list[dict]) -> bool:
    """Check if any result has a confidence level (i.e., is a conviction buy)."""
    return any(r.get("confidence") for r in results)
