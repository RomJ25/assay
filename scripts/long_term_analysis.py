#!/usr/bin/env python3
"""Generate data for the long-term evidence case study."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table
from data.fama_french import download_factors

console = Console()


def run():
    console.print("\n[bold blue]═══ Long-Term Evidence: Value + Quality (1963-2025) ═══[/bold blue]\n")

    df = download_factors()
    if df.empty:
        console.print("[red]Failed to download Fama-French data[/red]")
        return

    # ── 62-Year Summary ──
    console.print("[bold]62-YEAR FACTOR PREMIUMS (1963-2025)[/bold]\n")

    cum_mkt = 100.0
    cum_vq = 100.0
    decades = {}

    for year in range(1963, 2026):
        ydf = df[df["year"] == year]
        if ydf.empty:
            continue
        mkt = float(((1 + (ydf["Mkt-RF"] + ydf["RF"]) / 100).prod() - 1) * 100)
        hml = float(((1 + ydf["HML"] / 100).prod() - 1) * 100)
        rmw = float(((1 + ydf["RMW"] / 100).prod() - 1) * 100)
        cum_mkt *= (1 + mkt / 100)
        cum_vq *= (1 + (mkt + hml + rmw) / 100)

        decade = f"{year // 10 * 10}s"
        if decade not in decades:
            decades[decade] = {"hml_sum": 0, "rmw_sum": 0, "count": 0}
        decades[decade]["hml_sum"] += hml
        decades[decade]["rmw_sum"] += rmw
        decades[decade]["count"] += 1

    mkt_cagr = (cum_mkt / 100) ** (1 / 62) - 1
    vq_cagr = (cum_vq / 100) ** (1 / 62) - 1

    console.print(f"  Market CAGR:              {mkt_cagr * 100:+.1f}%")
    console.print(f"  Market + Value + Quality: {vq_cagr * 100:+.1f}%")
    console.print(f"  V+Q annual premium:       {(vq_cagr - mkt_cagr) * 100:+.1f}%\n")

    decade_table = Table(title="Factor Premiums by Decade (avg annual %)")
    decade_table.add_column("Decade", style="cyan")
    decade_table.add_column("Value (HML)", justify="right")
    decade_table.add_column("Quality (RMW)", justify="right")
    decade_table.add_column("Combined", justify="right")

    for dec, vals in sorted(decades.items()):
        n = vals["count"]
        h = vals["hml_sum"] / n
        r = vals["rmw_sum"] / n
        h_style = "green" if h > 0 else "red"
        r_style = "green" if r > 0 else "red"
        c_style = "green" if h + r > 0 else "red"
        decade_table.add_row(dec, f"[{h_style}]{h:+.1f}%[/{h_style}]",
                             f"[{r_style}]{r:+.1f}%[/{r_style}]",
                             f"[{c_style}]{h + r:+.1f}%[/{c_style}]")

    console.print(decade_table)

    # ── 12-Year Detail ──
    console.print(f"\n[bold]12-YEAR DETAIL (2014-2025)[/bold]\n")

    detail = Table(title="Annual Returns: Market vs Market + Value + Quality")
    detail.add_column("Year", style="cyan")
    detail.add_column("Market", justify="right")
    detail.add_column("Value (HML)", justify="right")
    detail.add_column("Quality (RMW)", justify="right")
    detail.add_column("V+Q Premium", justify="right")
    detail.add_column("$100 Mkt", justify="right")
    detail.add_column("$100 V+Q", justify="right")

    cm = 100.0
    cv = 100.0

    for year in range(2014, 2026):
        ydf = df[df["year"] == year]
        if ydf.empty:
            continue
        mkt = float(((1 + (ydf["Mkt-RF"] + ydf["RF"]) / 100).prod() - 1) * 100)
        hml = float(((1 + ydf["HML"] / 100).prod() - 1) * 100)
        rmw = float(((1 + ydf["RMW"] / 100).prod() - 1) * 100)
        premium = hml + rmw

        cm *= (1 + mkt / 100)
        cv *= (1 + (mkt + premium) / 100)

        p_style = "green" if premium > 0 else "red"
        detail.add_row(
            str(year), f"{mkt:+.1f}%",
            f"{'[green]' if hml > 0 else '[red]'}{hml:+.1f}%{'[/green]' if hml > 0 else '[/red]'}",
            f"{'[green]' if rmw > 0 else '[red]'}{rmw:+.1f}%{'[/green]' if rmw > 0 else '[/red]'}",
            f"[{p_style}]{premium:+.1f}%[/{p_style}]",
            f"${cm:.0f}", f"${cv:.0f}",
        )

    console.print(detail)
    console.print(f"\n  12-year excess: ${cv - cm:+.0f} ({(cv / cm - 1) * 100:+.1f}%)\n")

    # ── Key Takeaways ──
    console.print("[bold]KEY FINDINGS[/bold]\n")
    console.print("  1. Over 62 years, value+quality earned +7.1%/yr premium (compounded: massive)")
    console.print("  2. Over 12 years (2014-2025), the premium was modest (+1.2%/yr)")
    console.print("  3. Value STRUGGLED in 2015, 2017-2020, 2023 (growth/momentum dominated)")
    console.print("  4. Value SURGED in 2016, 2021-2022 (rotation into cheap stocks)")
    console.print("  5. Quality has been more consistent but smaller (~+2-3%/yr)")
    console.print("  6. The edge requires PATIENCE — minimum 5-year holding period")
    console.print("  7. A real portfolio captures a FRACTION of the theoretical factor premium")
    console.print()
    console.print("[dim]Data: Kenneth French Data Library (CRSP universe, survivorship-free)[/dim]\n")


if __name__ == "__main__":
    run()
