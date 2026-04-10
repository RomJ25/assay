#!/usr/bin/env python3
"""Run the full 10-test screener component investigation across 12 quarters."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from backtest.cache import HistoricalCache
from backtest.case_study import (
    BUCKET_ORDER,
    replay_screen_at_date,
    compute_stock_returns,
    compute_bucket_returns,
    test_gradient_monotonicity,
    test_gate_effectiveness,
    test_confidence_gradient,
    test_value_traps,
    test_asymmetry,
    test_sector_neutralized,
    test_repeat_picks,
    test_conviction_ordering,
)

console = Console()

# 12 usable quarters (Q1 2023 through Q1 2026)
REBALANCE_DATES = [
    date(2023, 3, 31), date(2023, 6, 30), date(2023, 9, 30), date(2023, 12, 31),
    date(2024, 3, 31), date(2024, 6, 30), date(2024, 9, 30), date(2024, 12, 31),
    date(2025, 3, 31), date(2025, 6, 30), date(2025, 9, 30), date(2025, 12, 31),
]

# Next quarter for each rebalance (for return computation)
NEXT_DATES = [
    date(2023, 6, 30), date(2023, 9, 30), date(2023, 12, 31), date(2024, 3, 31),
    date(2024, 6, 30), date(2024, 9, 30), date(2024, 12, 31), date(2025, 3, 31),
    date(2025, 6, 30), date(2025, 9, 30), date(2025, 12, 31), date(2026, 3, 31),
]


def fmt_pct(val, decimals=1):
    if val is None:
        return "n/a"
    return f"{val * 100:+.{decimals}f}%"


def run():
    console.print("\n[bold blue]═══ Assay Screener Component Investigation ═══[/bold blue]\n")
    console.print(f"Quarters: {len(REBALANCE_DATES)} ({REBALANCE_DATES[0]} to {REBALANCE_DATES[-1]})")
    console.print("Statistical note: n=12 quarters. All findings are directional hypotheses, not significant.\n")

    cache = HistoricalCache()
    try:
        # Phase 1: Replay all quarters
        console.print("[dim]Replaying all quarters...[/dim]")
        snapshots = []
        for rd in REBALANCE_DATES:
            snap = replay_screen_at_date(rd, cache)
            snapshots.append(snap)
            if snap:
                cb = snap.classifications.get("CONVICTION BUY", 0)
                console.print(f"  {rd}: {snap.num_screened} screened, {cb} CB picks")
            else:
                console.print(f"  {rd}: [red]replay failed[/red]")

        # Phase 2: Compute returns for each quarter
        console.print("\n[dim]Computing per-stock returns...[/dim]")
        quarter_data = []  # (snapshot, returns, spy_return, next_date)
        for i, (snap, rd, nd) in enumerate(zip(snapshots, REBALANCE_DATES, NEXT_DATES)):
            if snap is None:
                continue
            all_tickers = [sd.ticker for sd in snap.stock_details]
            returns = compute_stock_returns(all_tickers + ["SPY"], rd, nd, cache)
            spy_ret = returns.pop("SPY", None)
            quarter_data.append((snap, returns, spy_ret, nd))

        # ═══════════════════════════════════════════════════════════════
        # TEST 1: Classification Gradient
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 1: Classification Gradient Monotonicity ═══[/bold]\n")

        gradient_table = Table(title="Per-Bucket Mean Return by Quarter")
        gradient_table.add_column("Quarter", style="cyan")
        gradient_table.add_column("CB", justify="right")
        gradient_table.add_column("QGP", justify="right")
        gradient_table.add_column("WL", justify="right")
        gradient_table.add_column("HOLD", justify="right")
        gradient_table.add_column("OQ", justify="right")
        gradient_table.add_column("OV", justify="right")
        gradient_table.add_column("VT", justify="right")
        gradient_table.add_column("AVOID", justify="right")
        gradient_table.add_column("CB>AV?", justify="center")

        mono_count = 0
        cb_beat_avoid_count = 0
        total_counted = 0
        avg_spread = []

        for snap, returns, spy_ret, nd in quarter_data:
            bs = compute_bucket_returns(snap, returns)
            gm = test_gradient_monotonicity(bs)

            row = [str(snap.date)]
            for b in BUCKET_ORDER:
                s = bs.get(b)
                if s and s.n > 0:
                    row.append(f"{s.mean_return*100:+.1f}% ({s.n})")
                else:
                    row.append("—")

            if gm["cb_return"] is not None:
                total_counted += 1
                if gm["monotonic"]:
                    mono_count += 1
                if gm["cb_beat_avoid"]:
                    cb_beat_avoid_count += 1
                    row.append("[green]✓[/green]")
                else:
                    row.append("[red]✗[/red]")
                if gm["cb_vs_avoid_spread"] is not None:
                    avg_spread.append(gm["cb_vs_avoid_spread"])
            else:
                row.append("—")

            gradient_table.add_row(*row)

        console.print(gradient_table)
        console.print(f"\nFull monotonic (CB>WL>HOLD>AVOID): {mono_count}/{total_counted} quarters")
        console.print(f"CB beat AVOID: {cb_beat_avoid_count}/{total_counted} quarters")
        if avg_spread:
            console.print(f"Average CB-AVOID spread: {sum(avg_spread)/len(avg_spread)*100:+.1f}%")

        # ═══════════════════════════════════════════════════════════════
        # TEST 2 & 3: Gate Effectiveness
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 2: F-Gate Effectiveness ═══[/bold]\n")

        all_f_survivors = []
        all_f_victims = []
        f_table = Table(title="F-Gate (F<6): Survivors vs Victims")
        f_table.add_column("Quarter", style="cyan")
        f_table.add_column("Survivors", justify="right")
        f_table.add_column("Surv Mean", justify="right")
        f_table.add_column("Victims", justify="right")
        f_table.add_column("Vict Mean", justify="right")
        f_table.add_column("Delta", justify="right")

        for snap, returns, spy_ret, nd in quarter_data:
            fg = test_gate_effectiveness(snap, returns, "f_gate")
            all_f_survivors.extend([(snap.date, r) for _, r in
                                    [(sd.ticker, returns.get(sd.ticker)) for sd in snap.stock_details
                                     if sd.final_classification == "CONVICTION BUY" and returns.get(sd.ticker) is not None]])
            for t, r in fg["victim_details"]:
                all_f_victims.append((snap.date, t, r))

            f_table.add_row(
                str(snap.date),
                str(fg["n_survivors"]),
                fmt_pct(fg["survivor_mean"]),
                str(fg["n_victims"]),
                fmt_pct(fg["victim_mean"]),
                fmt_pct(fg["delta"]) if fg["delta"] is not None else "—",
            )

        console.print(f_table)
        if all_f_victims:
            vict_rets = [r for _, _, r in all_f_victims]
            console.print(f"\nAggregate F-gate victims: n={len(vict_rets)}, mean={sum(vict_rets)/len(vict_rets)*100:+.1f}%")
            console.print(f"  Victim details:")
            for dt, t, r in all_f_victims:
                console.print(f"    {dt} {t:6s} {r*100:+.1f}%")

        console.print("\n[bold]═══ Test 3: Momentum Gate Effectiveness ═══[/bold]\n")

        all_mom_victims = []
        mom_table = Table(title="Momentum Gate (≤25th pct): Survivors vs Victims")
        mom_table.add_column("Quarter", style="cyan")
        mom_table.add_column("Survivors", justify="right")
        mom_table.add_column("Surv Mean", justify="right")
        mom_table.add_column("Victims", justify="right")
        mom_table.add_column("Vict Mean", justify="right")
        mom_table.add_column("Delta", justify="right")

        for snap, returns, spy_ret, nd in quarter_data:
            mg = test_gate_effectiveness(snap, returns, "momentum_gate")
            for t, r in mg["victim_details"]:
                all_mom_victims.append((snap.date, t, r))

            mom_table.add_row(
                str(snap.date),
                str(mg["n_survivors"]),
                fmt_pct(mg["survivor_mean"]),
                str(mg["n_victims"]),
                fmt_pct(mg["victim_mean"]),
                fmt_pct(mg["delta"]) if mg["delta"] is not None else "—",
            )

        console.print(mom_table)
        if all_mom_victims:
            vict_rets = [r for _, _, r in all_mom_victims]
            console.print(f"\nAggregate momentum victims: n={len(vict_rets)}, mean={sum(vict_rets)/len(vict_rets)*100:+.1f}%")

        # ═══════════════════════════════════════════════════════════════
        # TEST 4: Confidence Gradient
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 4: Confidence Gradient (HIGH/MOD/LOW) ═══[/bold]\n")

        conf_table = Table(title="Confidence Tier Returns by Quarter")
        conf_table.add_column("Quarter", style="cyan")
        conf_table.add_column("HIGH n", justify="right")
        conf_table.add_column("HIGH mean", justify="right")
        conf_table.add_column("MOD n", justify="right")
        conf_table.add_column("MOD mean", justify="right")
        conf_table.add_column("LOW n", justify="right")
        conf_table.add_column("LOW mean", justify="right")
        conf_table.add_column("Mono?", justify="center")

        all_h, all_m, all_l = [], [], []
        mono_conf_count = 0
        conf_total = 0

        for snap, returns, spy_ret, nd in quarter_data:
            cg = test_confidence_gradient(snap, returns)
            t = cg["tiers"]

            if t["HIGH"]["n"] > 0:
                all_h.extend([returns[sd.ticker] for sd in snap.stock_details
                              if sd.final_classification == "CONVICTION BUY" and sd.confidence == "HIGH" and sd.ticker in returns])
            if t["MODERATE"]["n"] > 0:
                all_m.extend([returns[sd.ticker] for sd in snap.stock_details
                              if sd.final_classification == "CONVICTION BUY" and sd.confidence == "MODERATE" and sd.ticker in returns])
            if t["LOW"]["n"] > 0:
                all_l.extend([returns[sd.ticker] for sd in snap.stock_details
                              if sd.final_classification == "CONVICTION BUY" and sd.confidence == "LOW" and sd.ticker in returns])

            has_data = t["HIGH"]["n"] > 0 or t["MODERATE"]["n"] > 0 or t["LOW"]["n"] > 0
            if has_data:
                conf_total += 1
                if cg["monotonic"]:
                    mono_conf_count += 1

            conf_table.add_row(
                str(snap.date),
                str(t["HIGH"]["n"]), fmt_pct(t["HIGH"]["mean"]),
                str(t["MODERATE"]["n"]), fmt_pct(t["MODERATE"]["mean"]),
                str(t["LOW"]["n"]), fmt_pct(t["LOW"]["mean"]),
                "[green]✓[/green]" if cg["monotonic"] else "[red]✗[/red]" if has_data else "—",
            )

        console.print(conf_table)
        console.print(f"\nMonotonic (HIGH>MOD>LOW): {mono_conf_count}/{conf_total} quarters")
        if all_h:
            console.print(f"  Aggregate HIGH: n={len(all_h)}, mean={sum(all_h)/len(all_h)*100:+.1f}%")
        if all_m:
            console.print(f"  Aggregate MOD:  n={len(all_m)}, mean={sum(all_m)/len(all_m)*100:+.1f}%")
        if all_l:
            console.print(f"  Aggregate LOW:  n={len(all_l)}, mean={sum(all_l)/len(all_l)*100:+.1f}%")

        # ═══════════════════════════════════════════════════════════════
        # TEST 5: VALUE TRAP Validation
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 5: VALUE TRAP Validation ═══[/bold]\n")

        vt_table = Table(title="VALUE TRAP vs CB vs Universe")
        vt_table.add_column("Quarter", style="cyan")
        vt_table.add_column("VT n", justify="right")
        vt_table.add_column("VT mean", justify="right")
        vt_table.add_column("CB mean", justify="right")
        vt_table.add_column("Univ mean", justify="right")
        vt_table.add_column("Trap works?", justify="center")

        vt_works_count = 0
        vt_total = 0

        for snap, returns, spy_ret, nd in quarter_data:
            vt = test_value_traps(snap, returns)
            if vt["n_traps"] > 0 and vt["cb_mean"] is not None:
                vt_total += 1
                if vt["traps_underperform"]:
                    vt_works_count += 1

            vt_table.add_row(
                str(snap.date),
                str(vt["n_traps"]),
                fmt_pct(vt["vt_mean"]),
                fmt_pct(vt["cb_mean"]),
                fmt_pct(vt["universe_mean"]),
                "[green]✓[/green]" if vt["traps_underperform"] else "[red]✗[/red]" if vt["n_traps"] > 0 and vt["cb_mean"] is not None else "—",
            )

        console.print(vt_table)
        console.print(f"\nVALUE TRAPs underperform CB: {vt_works_count}/{vt_total} quarters")

        # ═══════════════════════════════════════════════════════════════
        # TEST 6: Selectivity (zero-pick quarters)
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 6: Selectivity Signal ═══[/bold]\n")

        for snap, returns, spy_ret, nd in quarter_data:
            cb_count = snap.classifications.get("CONVICTION BUY", 0)
            if cb_count == 0:
                console.print(f"[yellow]Zero-pick quarter: {snap.date}[/yellow]")
                console.print(f"  Screened: {snap.num_screened}")
                console.print(f"  Distribution:")
                for b in BUCKET_ORDER:
                    c = snap.classifications.get(b, 0)
                    if c > 0:
                        console.print(f"    {b:25s} {c:3d}")
                all_rets = [r for r in returns.values()]
                if all_rets:
                    console.print(f"  Universe mean return: {sum(all_rets)/len(all_rets)*100:+.1f}%")
                console.print(f"  SPY return: {fmt_pct(spy_ret)}")

        # Also show cumulative from existing CSV data
        console.print("\n  [dim]Zero-pick quarters from existing backtest CSV (2022, not replayable):[/dim]")
        console.print("    2022-Q1→Q2: Universe -16.86%, SPY -16.11% (avoided crash)")
        console.print("    2022-Q2→Q3: Universe  -1.97%, SPY  -4.93%")
        console.print("    2022-Q3→Q4: Universe +11.42%, SPY  +7.56% (missed rally)")
        console.print("    2022-Q4→Q1: Universe  +7.83%, SPY  +7.46% (missed rally)")
        console.print("    2023-Q1→Q2: Universe  +7.26%, SPY  +8.68% (missed rally — see above)")
        console.print("    Cumulative cash: 0% | Cumulative universe: ~+7.2% | 5 quarters in cash")

        # ═══════════════════════════════════════════════════════════════
        # TEST 7: Asymmetry Distribution
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 7: Asymmetry Distribution ═══[/bold]\n")

        all_excess = []
        for snap, returns, spy_ret, nd in quarter_data:
            all_rets = [r for r in returns.values()]
            if not all_rets:
                continue
            univ_mean = sum(all_rets) / len(all_rets)
            excess = test_asymmetry(snap, returns, univ_mean)
            all_excess.extend(excess)

        if all_excess:
            positive = [e["excess"] for e in all_excess if e["excess"] > 0]
            negative = [e["excess"] for e in all_excess if e["excess"] <= 0]

            console.print(f"Total CB stock-quarter observations: {len(all_excess)}")
            console.print(f"  Positive excess (winners): n={len(positive)}, mean={sum(positive)/len(positive)*100:+.1f}%" if positive else "  No winners")
            console.print(f"  Negative excess (losers):  n={len(negative)}, mean={sum(negative)/len(negative)*100:+.1f}%" if negative else "  No losers")
            if positive and negative:
                win_avg = sum(positive) / len(positive)
                loss_avg = abs(sum(negative) / len(negative))
                ratio = win_avg / loss_avg if loss_avg > 0 else float("inf")
                console.print(f"  Win/Loss ratio: {ratio:.2f}x (>1 = wins bigger than losses)")
                console.print(f"  Hit rate: {len(positive)/len(all_excess)*100:.0f}%")

        # ═══════════════════════════════════════════════════════════════
        # TEST 8: Sector-Neutralized Returns
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 8: Sector-Neutralized Returns (Stock Selection vs Sector Rotation) ═══[/bold]\n")

        sn_table = Table(title="CB Excess vs Own Sector Mean")
        sn_table.add_column("Quarter", style="cyan")
        sn_table.add_column("CB n", justify="right")
        sn_table.add_column("Mean excess vs sector", justify="right")
        sn_table.add_column("Selection?", justify="center")

        all_sn_excess = []
        sn_positive = 0
        sn_total = 0

        for snap, returns, spy_ret, nd in quarter_data:
            sn = test_sector_neutralized(snap, returns)
            if sn["n"] > 0:
                sn_total += 1
                if sn["stock_selection_positive"]:
                    sn_positive += 1
                all_sn_excess.append(sn["mean_excess_vs_sector"])

            sn_table.add_row(
                str(snap.date),
                str(sn["n"]),
                fmt_pct(sn["mean_excess_vs_sector"]),
                "[green]✓[/green]" if sn.get("stock_selection_positive") else "[red]✗[/red]" if sn["n"] > 0 else "—",
            )

        console.print(sn_table)
        console.print(f"\nPositive stock selection: {sn_positive}/{sn_total} quarters")
        if all_sn_excess:
            console.print(f"Average sector-neutralized excess: {sum(all_sn_excess)/len(all_sn_excess)*100:+.1f}%")

        # ═══════════════════════════════════════════════════════════════
        # TEST 9: Repeat-Pick Persistence
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 9: Repeat-Pick Persistence ═══[/bold]\n")

        snapshots_returns = [(snap, returns) for snap, returns, _, _ in quarter_data]
        rp = test_repeat_picks(snapshots_returns)

        console.print(f"Returning picks (in CB prev quarter): n={rp['n_returning']}, mean={fmt_pct(rp['returning_mean'])}")
        console.print(f"New entries (fresh to CB):             n={rp['n_new']}, mean={fmt_pct(rp['new_mean'])}")
        if rp["delta"] is not None:
            label = "Returning OUTPERFORM" if rp["delta"] > 0 else "New entries OUTPERFORM"
            console.print(f"Delta: {rp['delta']*100:+.1f}% ({label})")

        # ═══════════════════════════════════════════════════════════════
        # TEST 10: Conviction Ordering
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold]═══ Test 10: Conviction Score Ordering Within CB ═══[/bold]\n")

        co_table = Table(title="Kendall's τ: Conviction Score vs Return Rank")
        co_table.add_column("Quarter", style="cyan")
        co_table.add_column("CB n", justify="right")
        co_table.add_column("Kendall τ", justify="right")
        co_table.add_column("Positive?", justify="center")

        all_tau = []

        for snap, returns, spy_ret, nd in quarter_data:
            co = test_conviction_ordering(snap, returns)
            if co["insufficient_data"]:
                co_table.add_row(str(snap.date), str(co["n"]), "—", "—")
                continue

            all_tau.append(co["kendall_tau"])
            co_table.add_row(
                str(snap.date),
                str(co["n"]),
                f"{co['kendall_tau']:+.3f}",
                "[green]✓[/green]" if co["positive_correlation"] else "[red]✗[/red]",
            )

        console.print(co_table)
        if all_tau:
            console.print(f"\nAverage Kendall τ: {sum(all_tau)/len(all_tau):+.3f}")
            pos_count = sum(1 for t in all_tau if t > 0)
            console.print(f"Positive correlation: {pos_count}/{len(all_tau)} quarters")

        # ═══════════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════════
        console.print("\n[bold blue]═══ Investigation Summary ═══[/bold blue]\n")

        summary = Table(title="Component Effectiveness Summary")
        summary.add_column("Test", style="cyan")
        summary.add_column("Result", justify="left")
        summary.add_column("Signal", justify="center")

        summary.add_row("1. Gradient (CB>AVOID)", f"CB beat AVOID in {cb_beat_avoid_count}/{total_counted} quarters",
                         "[green]DIRECTIONAL[/green]" if cb_beat_avoid_count > total_counted / 2 else "[red]WEAK[/red]")

        if all_f_victims:
            f_v = [r for _, _, r in all_f_victims]
            summary.add_row("2. F-Gate", f"n={len(f_v)}, victim mean={sum(f_v)/len(f_v)*100:+.1f}%", "[yellow]NEUTRAL[/yellow]")
        else:
            summary.add_row("2. F-Gate", "No victims found", "[dim]NO DATA[/dim]")

        if all_mom_victims:
            m_v = [r for _, _, r in all_mom_victims]
            m_v_mean = sum(m_v) / len(m_v)
            # Compare momentum victims to CB survivors
            cb_all = [returns.get(sd.ticker) for snap, returns, _, _ in quarter_data
                      for sd in snap.stock_details if sd.final_classification == "CONVICTION BUY" and returns.get(sd.ticker) is not None]
            cb_mean = sum(cb_all) / len(cb_all) if cb_all else 0
            mom_helps = m_v_mean < cb_mean
            summary.add_row("3. Momentum Gate", f"n={len(m_v)}, victim mean={m_v_mean*100:+.1f}% vs CB {cb_mean*100:+.1f}%",
                            "[green]HELPS[/green]" if mom_helps else "[red]HURTS[/red]")

        summary.add_row("4. Confidence", f"Monotonic {mono_conf_count}/{conf_total} quarters",
                         "[green]DIRECTIONAL[/green]" if mono_conf_count > conf_total / 2 else "[yellow]WEAK[/yellow]")

        summary.add_row("5. VALUE TRAP", f"Underperform CB {vt_works_count}/{vt_total} quarters",
                         "[green]WORKS[/green]" if vt_works_count > vt_total / 2 else "[red]FAILS[/red]")

        summary.add_row("8. Sector-Neutral", f"Positive {sn_positive}/{sn_total} quarters",
                         "[green]STOCK SELECTION[/green]" if sn_positive > sn_total / 2 else "[red]SECTOR ROTATION[/red]")

        if rp["delta"] is not None:
            summary.add_row("9. Repeat Picks", f"Delta={rp['delta']*100:+.1f}%",
                            "[green]RETURNING[/green]" if rp["delta"] > 0 else "[yellow]NEW ENTRIES[/yellow]")

        if all_tau:
            avg_tau = sum(all_tau) / len(all_tau)
            summary.add_row("10. Conviction Order", f"Avg τ={avg_tau:+.3f}",
                            "[green]PREDICTIVE[/green]" if avg_tau > 0.05 else "[yellow]WEAK[/yellow]" if avg_tau > -0.05 else "[red]WRONG[/red]")

        console.print(summary)

        console.print("\n[dim]All findings are directional hypotheses (n=12 quarters). Minimum 30 quarters needed for significance.[/dim]\n")

    finally:
        cache.close()


if __name__ == "__main__":
    run()
