> **Naming note (2026-04-26):** This case study refers to the classification `CONVICTION BUY`. Effective 2026-04-26 that label was renamed to `RESEARCH CANDIDATE` everywhere in the live codebase, with no semantic change. This document is preserved as historical narrative and uses the original term.

<!--
  Convention: ASCII code-block tables for aggregated summaries (<= 10 rows).
  Real markdown tables are used only for detail listings like the 26-pick grid
  in section 6, where fixed-width formatting would be unreadable.
-->

<div align="center">

# Case Study — April 2025 "Liberation Day" Tariff Shock

**A multi-day stress test of Assay's Q1 2025 classifications against VIX 60 — the highest volatility regime since the 2008 financial crisis.**

</div>

---

### Contents

[1. Prologue](#1-prologue--liberation-day-timeline) · [2. The Portfolio at Rebalance](#2-the-screeners-portfolio-at-rebalance-mar-31) · [3. The Crash](#3-the-crash-apr-2-7-per-bucket-drawdown) · [4. The Recovery](#4-the-recovery-apr-7-9-who-bounced) · [5. Net Result](#5-net-result-mar-31--apr-14) · [6. Every Pick](#6-every-pick--daily-returns-through-the-event) · [7. VALUE TRAP Destruction](#7-value-trap-destruction) · [8. Investigation Context](#8-investigation-context) · [9. Takeaway](#9-takeaway--stress-tested-not-stress-proof) · [10. Caveats](#10-caveats)

---

## 1. Prologue — Liberation Day Timeline

On March 31, 2025, Assay produced its Q1 rebalance screen. VIX was 22.3 — elevated but not alarming. The output: 426 scorable names, 26 classified as CONVICTION BUY. Two days later, the tape broke.

```
    +--------+------+-----------------------------------------------+
    |  Date  |  VIX |  Event                                        |
    +--------+------+-----------------------------------------------+
    | Mar 28 | 21.6 |  Pre-event baseline                           |
    | Mar 31 | 22.3 |  Q1 2025 rebalance. 26 CB picks produced.     |
    | Apr  1 | 21.8 |  Calm before the storm                        |
    | Apr  2 | 21.5 |  Trump announces "Liberation Day" tariffs:    |
    |        |      |    10% on all imports + higher country rates   |
    | Apr  3 | 30.0 |  Markets begin selling                        |
    | Apr  4 | 45.3 |  China retaliates w/ 34% tariffs on US goods. |
    |        |      |    SPY -9.7% from Mar 31                      |
    | Apr  7 | 47.0 |  Crash continues. SPY -9.8% from Mar 31       |
    | Apr  8 | 52.3 |  VIX peaks. Intraday panic.                   |
    | Apr  9 | 33.6 |  Trump announces 90-day pause (except China).  |
    |        |      |    SPY rallies +8.8% in one day                |
    | Apr 10 | 40.7 |  Aftershock volatility                        |
    | Apr 14 | 30.9 |  Markets stabilize. SPY -3.6% from Mar 31     |
    +--------+------+-----------------------------------------------+
```

VIX 52.3 on April 8 was the highest reading since the 2008 financial crisis. The screener had never been tested in this regime. This document traces what the classifications did across five phases of the event: announcement, crash, peak fear, policy reversal, and stabilization. It uses daily close-to-close prices throughout.

Individual market events are not evidence — the backtest is. This case study exists to make the mechanism visible in concrete terms, not to argue the screener "worked" or "failed."

---

## 2. The Screener's Portfolio at Rebalance (Mar 31)

The Q1 2025 screen produced the following classification distribution:

```
    +---------------------------+------+---------+
    |  Bucket                   |   n  |  Share  |
    +---------------------------+------+---------+
    |  CONVICTION BUY           |   26 |   6.1%  |
    |  QUALITY GROWTH PREMIUM   |   40 |   9.4%  |
    |  WATCH LIST               |   72 |  16.9%  |
    |  HOLD                     |   83 |  19.5%  |
    |  OVERVALUED QUALITY       |   57 |  13.4%  |
    |  OVERVALUED               |   67 |  15.7%  |
    |  VALUE TRAP               |   17 |   4.0%  |
    |  AVOID                    |   64 |  15.0%  |
    |                           +------+         |
    |  Total (scorable)         |  426 |         |
    +---------------------------+------+---------+
```

The load-bearing fact of this section: **Consumer Discretionary was 35% of CONVICTION BUY.** Nine of the 26 CB picks were in the sector most directly exposed to tariff impacts on consumer goods. This was the screener's most dangerous configuration heading into a trade war.

```
    +---------------------------+-----+---------+
    |  CB Sector Composition    |  n  |  Share  |
    +---------------------------+-----+---------+
    |  Consumer Discretionary   |   9 |   35%   |
    |  Industrials              |   6 |   23%   |
    |  Health Care              |   5 |   19%   |
    |  Consumer Staples         |   3 |   12%   |
    |  Information Technology   |   2 |    8%   |
    |  Financials               |   1 |    4%   |
    +---------------------------+-----+---------+
```

The April 2026 empirical investigation (see `docs/DESIGN_DECISIONS.md`, "Sector rotation, not stock selection") found that 80% of CB pick-quarters across 12 quarters came from just four sectors: Consumer Discretionary (25.5%), Health Care (19.7%), Industrials (18.6%), and Consumer Staples (16.0%). The Q1 2025 screen is a textbook instance of that concentration pattern. Consumer Discretionary at 35% exceeds even the historical average — the screener was leaning into tariff exposure, not hedging it.

The engine does not know what tariffs are. It saw cheap valuations and strong quality scores in Consumer Discretionary and Industrials and classified accordingly. There was no macro view to override the signal.

---

## 3. The Crash (Apr 2-7): Per-Bucket Drawdown

Every classification bucket, matched to its drawdown from Mar 31 close to Apr 7 close. SPY benchmark: **-9.8%**.

```
    +---------------------------+-----+---------+---------+
    |  Bucket                   |  n  |  Mean   | vs SPY  |
    +---------------------------+-----+---------+---------+
    |  CONVICTION BUY           |  26 |  -8.8%  | +100 bp |
    |  QGP                      |  40 |  -8.6%  | +120 bp |
    |  WATCH LIST               |  72 | -11.1%  | -130 bp |
    |  HOLD                     |  83 |  -9.3%  |  +50 bp |
    |  OVERVALUED QUALITY       |  56 |  -8.8%  | +100 bp |
    |  OVERVALUED               |  67 | -10.5%  |  -70 bp |
    |  VALUE TRAP               |  17 | -14.4%  | -460 bp |
    |  AVOID                    |  64 | -10.2%  |  -40 bp |
    +---------------------------+-----+---------+---------+
```

CB fell **less** than SPY during the crash: -8.8% vs -9.8%, a gap of +100 basis points. For a 26-name portfolio that was 35% Consumer Discretionary heading into a tariff shock, this is a non-obvious result.

Where did the protection come from? Not from the tariff-exposed names — those were hit hard (BBY -16.8%, EXPE -16.8%, QCOM -15.6%). The protection came from the **other 65% of the portfolio**: Health Care (HCA -4.6%, DVA -4.2%, HSY -4.9%), Consumer Staples (MO -7.3%, SYY -6.8%), and selected Industrials (EME -5.2%, FIX -3.2%). The screener's diversification across multiple sectors — a natural consequence of the quality filter selecting across industries rather than chasing a single cheap sector — provided natural hedging that partially offset the tariff-exposed names.

The two worst buckets during the crash were **VALUE TRAP (-14.4%)** and **WATCH LIST (-11.1%)**. Value traps — cheap stocks with weak fundamentals — were devastated, falling 460 basis points worse than SPY and 560 basis points worse than CB. This is what the classification is designed to flag: names where the cheapness is a symptom, not an opportunity.

---

## 4. The Recovery (Apr 7-9): Who Bounced?

On April 9, Trump announced a 90-day pause on tariffs for all countries except China. SPY rallied **+8.8%** in a single session from the Apr 7 close. Returns by bucket:

```
    +---------------------------+-----+---------+---------+
    |  Bucket                   |  n  |  Mean   | vs SPY  |
    +---------------------------+-----+---------+---------+
    |  OVERVALUED               |  67 |  +7.6%  | -120 bp |
    |  OVERVALUED QUALITY       |  56 |  +7.5%  | -130 bp |
    |  WATCH LIST               |  72 |  +7.0%  | -180 bp |
    |  VALUE TRAP               |  17 |  +6.3%  | -250 bp |
    |  AVOID                    |  64 |  +6.0%  | -280 bp |
    |  CONVICTION BUY           |  26 |  +5.6%  | -320 bp |
    |  HOLD                     |  83 |  +5.6%  | -320 bp |
    |  QGP                      |  40 |  +5.3%  | -350 bp |
    +---------------------------+-----+---------+---------+
```

CB **lagged** the recovery: +5.6% vs SPY's +8.8%, a gap of -320 basis points.

This is the expected behavior for a value/quality-tilted portfolio. The stocks that bounced hardest were the most beaten-down, highest-beta names — exactly the kind the screener sorts into OVERVALUED (+7.6%), OVERVALUED QUALITY (+7.5%), and WATCH LIST (+7.0%). CB's holdings, selected for quality and defensive characteristics, are lower-beta by construction. They fell less in the crash and bounced less in the recovery. The pattern is textbook mean reversion: the names that lost the most recover the most, regardless of fundamental quality.

A user who followed CB through the crash would have been protected on the way down (-8.8% vs -9.8%) but left behind on the way up (+5.6% vs +8.8%). The asymmetry favors the benchmark on a V-shaped reversal. This is not a failure of the screener — it is the structural cost of owning lower-beta, higher-quality names during a snap-back rally.

---

## 5. Net Result (Mar 31 -> Apr 14)

Two weeks after rebalance, with the worst of the volatility past. SPY benchmark: **-3.6%**.

```
    +---------------------------+-----+---------+---------+
    |  Bucket                   |  n  |  Mean   | vs SPY  |
    +---------------------------+-----+---------+---------+
    |  OVERVALUED QUALITY       |  56 |  -2.1%  | +150 bp |
    |  QGP                      |  40 |  -3.5%  |  +10 bp |
    |  AVOID                    |  64 |  -4.7%  | -110 bp |
    |  CONVICTION BUY           |  26 |  -4.8%  | -120 bp |
    |  HOLD                     |  83 |  -4.9%  | -130 bp |
    |  OVERVALUED               |  67 |  -4.9%  | -130 bp |
    |  WATCH LIST               |  72 |  -7.0%  | -340 bp |
    |  VALUE TRAP               |  17 | -11.8%  | -820 bp |
    +---------------------------+-----+---------+---------+
```

**CB: -4.8% vs SPY: -3.6%.** The screener's picks trailed SPY by 120 basis points over the two-week window. This is within noise for a 26-name portfolio over two weeks of VIX 50+ volatility, but the direction is real: CB did not protect on a net basis.

The story underneath the headline:

1. **VALUE TRAP (-11.8%) was the worst bucket by a wide margin.** The classification's single clearest signal — cheap stocks with bad fundamentals lose the most — held under extreme stress. VALUE TRAPs trailed SPY by 820 basis points and CB by 700 basis points.

2. **WATCH LIST (-7.0%) was the second worst.** Names the engine flagged as "needs skepticism" underperformed the universe.

3. **OVERVALUED QUALITY (-2.1%) was the best bucket.** These are good businesses at high prices — exactly the names you would expect to be most resilient during a fear-driven selloff. Their quality floors limited drawdowns while their high starting valuations meant less distance to fall.

4. **CB (-4.8%) landed in the middle of the distribution.** Not the best, not the worst. The screener neither helped nor hurt during this event — it produced an approximately SPY-neutral outcome against the most extreme volatility in 17 years.

---

## 6. Every Pick — Daily Returns Through the Event

Every CONVICTION BUY from the Q1 2025 screen, with returns across the event windows. Sorted by net return (Pre -> Apr 14), best to worst:

| Ticker | Sector | V | Q | Conf | Pre->Apr4 | Pre->Apr7 | Apr7->Apr9 | Pre->Apr14 |
|---|---|---:|---:|---|---:|---:|---:|---:|
| **FIX** | Industrials | 81.2 | 72.6 | LOW | -8.0% | -3.2% | +14.3% | **+9.1%** |
| **EME** | Industrials | 91.6 | 82.1 | MOD | -7.5% | -5.2% | +11.6% | **+4.4%** |
| NVR | Consumer Disc | 92.7 | 75.1 | MOD | +2.3% | -2.7% | +1.1% | -0.0% |
| SNA | Industrials | 86.5 | 74.8 | LOW | -6.5% | -7.8% | +6.1% | -0.0% |
| HSY | Consumer Staples | 82.1 | 80.1 | MOD | -5.1% | -4.9% | +1.0% | -0.4% |
| DVA | Health Care | 88.6 | 71.8 | LOW | -2.3% | -4.2% | +4.3% | -1.4% |
| HCA | Health Care | 82.4 | 83.3 | MOD | -4.0% | -4.6% | +2.7% | -1.4% |
| EBAY | Consumer Disc | 74.6 | 73.2 | LOW | -7.9% | -9.7% | +1.3% | -2.5% |
| TROW | Financials | 96.1 | 74.7 | LOW | -10.1% | -11.1% | +10.4% | -2.8% |
| ALLE | Industrials | 71.7 | 82.8 | LOW | -5.2% | -7.4% | +3.2% | -3.2% |
| SYY | Consumer Staples | 74.5 | 80.6 | LOW | -4.1% | -6.8% | +2.3% | -3.6% |
| LOW | Consumer Disc | 71.1 | 87.4 | LOW | -4.3% | -7.0% | +2.9% | -3.9% |
| HSIC | Health Care | 78.3 | 73.8 | LOW | -4.4% | -6.1% | +2.9% | -4.2% |
| NTAP | Info Tech | 83.7 | 76.1 | MOD | -12.8% | -11.7% | +11.7% | -4.6% |
| MO | Consumer Staples | 92.4 | 80.0 | MOD | -6.6% | -7.3% | +1.3% | -4.8% |
| UHS | Health Care | 92.8 | 94.3 | HIGH | -7.1% | -8.6% | +6.6% | -4.8% |
| GILD | Health Care | 82.1 | 73.1 | LOW | -4.3% | -5.8% | -0.3% | -5.0% |
| WSM | Consumer Disc | 77.3 | 86.4 | MOD | -10.4% | -8.2% | +9.1% | -8.1% |
| LULU | Consumer Disc | 73.8 | 88.4 | LOW | -6.8% | -6.4% | +3.3% | -8.2% |
| RL | Consumer Disc | 70.2 | 98.2 | LOW | -10.5% | -12.5% | +7.9% | -8.6% |
| QCOM | Info Tech | 73.3 | 90.5 | LOW | -17.0% | -15.6% | +10.7% | -9.4% |
| GNRC | Industrials | 77.3 | 79.3 | MOD | -11.7% | -12.6% | +3.6% | -10.4% |
| MAS | Industrials | 84.1 | 85.8 | MOD | -9.5% | -12.3% | +4.6% | -10.3% |
| EXPE | Consumer Disc | 86.2 | 91.1 | HIGH | -15.6% | -16.8% | +15.6% | -11.2% |
| HAS | Consumer Disc | 77.5 | 74.9 | LOW | -12.2% | -13.5% | +3.8% | -13.2% |
| **BBY** | Consumer Disc | 81.6 | 81.2 | MOD | -17.9% | -16.8% | +4.0% | **-16.1%** |

> **2 of 26 were positive at Apr 14.** Both were Industrials (FIX +9.1%, EME +4.4%). Three more were flat (NVR -0.0%, SNA -0.0%, HSY -0.4%). The worst single pick was BBY (-16.1%), a Consumer Discretionary name directly in the path of tariffs on imported electronics.

The distribution of outcomes tells the story of sector exposure:

- **Defensive names held:** HSY -0.4%, DVA -1.4%, HCA -1.4%, GILD -5.0% — Health Care and Consumer Staples absorbed the shock.
- **Tariff-exposed names were hit hard:** BBY -16.1%, HAS -13.2%, EXPE -11.2%, QCOM -9.4% — Consumer Discretionary and Tech names with import-dependent supply chains took the worst damage.
- **Industrials split:** FIX and EME, both specialty construction/engineering firms with domestic revenue, recovered fully. MAS and GNRC — more exposed to materials costs — did not.

---

## 7. VALUE TRAP Destruction

The 17 names classified as VALUE TRAP on Mar 31 — cheap stocks with weak quality scores — were the worst-performing bucket across every window of this event:

```
    +-------------------+-----------+----------+
    |  Window           | VALUE TRAP|  CB      |
    +-------------------+-----------+----------+
    |  Crash (Pre->Apr7)|  -14.4%   |  -8.8%   |
    |  Recovery (Apr7-9)|   +6.3%   |  +5.6%   |
    |  Net (Pre->Apr14) |  -11.8%   |  -4.8%   |
    +-------------------+-----------+----------+
    |  VT - CB spread   |   -5.6pp  |          |
    |                   |   +0.7pp  |          |
    |                   |   -7.0pp  |          |
    +-------------------+-----------+----------+
```

VALUE TRAPs fell 560 basis points more than CB during the crash, recovered only marginally more during the bounce (+6.3% vs +5.6%), and ended the two-week window 700 basis points worse. The classification's core promise — that cheap stocks with weak fundamentals are traps, not bargains — held under VIX 50+ conditions.

The April 2026 empirical investigation confirmed this pattern at the quarterly level: VALUE TRAPs underperformed CB in 7 of 11 quarters tested. The 4 quarters where VALUE TRAPs outperformed included the Q4 2025 Iran oil shock, where cheap energy names got a macro tailwind (+26.6% VT vs +3.6% CB). Liberation Day was the inverse — a macro event that punished exactly the kind of fragile, cheap names that VALUE TRAP is designed to flag. Both directions confirm the classification is responding to the right signal.

---

## 8. Investigation Context

The April 2026 empirical investigation (`docs/DESIGN_DECISIONS.md`) tested 10 components of the screener across 12 quarters. Several of its findings are directly visible in the Liberation Day data:

**Sector exposure.** Under quarterly rebalancing, sector-neutralized alpha was +0.1%. Under the selective sell strategy (see `docs/STRATEGY.md`), this improved to +0.5% — holding appreciated stocks contributes genuine stock selection. However, Liberation Day demonstrates the risk of sector concentration: the tilt toward Consumer Discretionary (35% of CB) put the portfolio directly in the path of tariff impacts. The offsetting tilt toward Health Care (19%) and Consumer Staples (12%) provided partial hedging. Under selective sell, the portfolio at this point would have been ~40+ positions (more diversified than the 26 CB-only picks shown here), potentially moderating the sector concentration risk.

**Win/loss asymmetry improves with strategy.** Under quarterly rebalancing, the win/loss ratio was 1.05x (no meaningful asymmetry). Under selective sell, it improved to 1.28x — holding winners creates genuine asymmetry over time. Liberation Day itself is a single event and does not demonstrate asymmetry; the screener is not a tail-risk hedge.

**Confidence gradient works in aggregate, not per-event.** The investigation found the HIGH > MODERATE > LOW gradient held in aggregate (+6.7%, +5.4%, +3.3%) but in only 1 of 11 quarters. Liberation Day does not show a clean confidence gradient in the net returns: the single HIGH-confidence pick (UHS, -4.8%) landed near the portfolio mean, while LOW-confidence picks span the full range from FIX (+9.1%) to HAS (-13.2%). This is consistent with the investigation's finding that confidence labels are meaningful in expectation but unreliable for any single period.

---

## 9. Takeaway — Stress-Tested, Not Stress-Proof

Liberation Day was the screener's hardest test: VIX 52.3, the highest since 2008, with the portfolio 35% concentrated in the sector most exposed to the triggering event. The results:

1. **CB protected during the crash.** -8.8% vs SPY -9.8% — one percentage point of downside protection during a five-day, -9.8% drawdown. The protection came from defensive positions in Health Care and Consumer Staples offsetting the tariff-exposed Consumer Discretionary names.

2. **CB lagged the recovery.** +5.6% vs SPY +8.8% — the value/quality tilt produces lower-beta portfolios that do not participate fully in snap-back rallies. This is expected and structural.

3. **The net result was approximately SPY-neutral.** CB -4.8% vs SPY -3.6% — a 120 basis point gap that is within noise for a 26-name portfolio over two weeks of extreme volatility. The screener neither helped nor hurt on a net basis.

4. **VALUE TRAP destruction confirmed the classification.** -14.4% crash, -11.8% net — the worst bucket in every window, by a wide margin. Cheap stocks with weak fundamentals were devastated, exactly as the label predicts.

5. **The screener's diversification provided natural hedging.** Despite the dangerous Consumer Discretionary concentration, the quality filter's tendency to select across multiple sectors meant the portfolio included defensive positions that partially offset the tariff-exposed names. This is the sector rotation mechanism the April 2026 investigation identified — it works in both directions.

The temptation is to frame this as a success story (CB beat SPY during the crash) or a failure story (CB trailed SPY on a net basis). It is neither. It is a stress test that produced a result within the range the screener's mechanics predict: modest protection on the downside, lagging on the upside, VALUE TRAPs destroyed, approximately index-like net performance. The screener is a long-term disciplined filter measured in quarters. A two-week VIX-60 event tests the mechanism, it does not validate or invalidate the strategy.

The backtest is the evidence. This case study is an illustration.

---

## 10. Caveats

```
    +-------------------------------+-------------------------------------------+
    |  Limitation                   |  Effect on this case study                |
    +-------------------------------+-------------------------------------------+
    |  n = 1 event                  |  Nothing here is statistically            |
    |                               |  significant. One tariff shock is not a   |
    |                               |  sample. The backtest is the evidence.    |
    |                               |                                           |
    |  Close-to-close daily prices  |  All returns are computed from daily      |
    |                               |  close prices via yfinance. Intraday     |
    |                               |  moves — especially on Apr 9 — were      |
    |                               |  larger than close-to-close suggests.     |
    |                               |                                           |
    |  No transaction costs         |  A real portfolio rebalanced on Mar 31    |
    |                               |  would face execution costs. The          |
    |                               |  backtest includes tcosts; this does not. |
    |                               |                                           |
    |  No slippage, no borrow       |  Close-to-close assumes frictionless      |
    |                               |  execution. VIX 50+ spreads were          |
    |                               |  materially wider than normal.            |
    |                               |                                           |
    |  Static portfolio             |  Returns assume the Mar 31 portfolio was  |
    |                               |  held through Apr 14 with no rebalancing. |
    |                               |  The screener runs quarterly; no          |
    |                               |  mid-quarter adjustment was triggered.    |
    |                               |                                           |
    |  No bootstrap or t-test       |  All spreads in this document are         |
    |                               |  descriptive, not inferential. The        |
    |                               |  26-name CB vs SPY gap of -120 bps is    |
    |                               |  well inside the standard error of a     |
    |                               |  26-name equal-weighted portfolio.        |
    |                               |                                           |
    |  Survivorship bias            |  Universe is the S&P 500 membership as   |
    |                               |  of the Mar 31 screen date. No           |
    |                               |  adjustment for subsequent index          |
    |                               |  changes.                                 |
    +-------------------------------+-------------------------------------------+
```

> This is a stress test, not a performance claim. Do not tune parameters based on one event's results. The backtest is the only source of evidence this project treats as such; see [`docs/METHODOLOGY.md`](../METHODOLOGY.md) and the quarterly backtest output in `results/backtest_*.csv` for the only performance numbers that deserve statistical weight.

---

<div align="center">
<sub>[Back to README](../../README.md) · [Methodology](../METHODOLOGY.md) · [Ceasefire Case Study](2026-04-08_ceasefire.md)</sub>
</div>
