> **Naming note (2026-04-26):** This case study refers to the classification `CONVICTION BUY`. Effective 2026-04-26 that label was renamed to `RESEARCH CANDIDATE` everywhere in the live codebase, with no semantic change. This document is preserved as historical narrative and uses the original term.

<!--
  Convention: ASCII code-block tables for aggregated summaries (<= 10 rows).
  Real markdown tables are used only for detail listings like the 5-pick grid
  in section 4, where fixed-width formatting would be unreadable.
-->

<div align="center">

# Case Study — Q4 2023: When Everything Aligned

**The screener's best quarter in the 12-quarter sample: concentration + sector tailwind + genuine stock selection.**

</div>

---

> Individual market events are not evidence — the backtest is. These case studies exist only to illustrate, in concrete terms, the kind of behavior the engine is designed to exhibit.

---

### Contents

[1. Prologue](#1-prologue--the-q4-2023-setup) · [2. Classifications](#2-the-screeners-classifications) · [3. Result by Bucket](#3-result-by-bucket) · [4. The Five Picks](#4-the-five-picks) · [5. Sector-Neutralized](#5-sector-neutralized-genuine-stock-selection) · [6. What the Screener Missed](#6-what-the-screener-missed) · [7. Investigation Context](#7-investigation-context) · [8. Takeaway](#8-takeaway) · [9. Caveats](#9-caveats)

---

## 1. Prologue — The Q4 2023 Setup

The Fed completed its hiking cycle in August 2023, parking the federal funds rate at 5.25-5.50%. Through September, markets ground sideways as participants debated whether the rate peak was truly in. Then, between October and December, sentiment shifted. Investors began pricing rate cuts for 2024. The result was a broad, powerful rally: SPY returned **+11.6%** for the quarter. Technology led.

On 2023-09-30, Assay produced its quarterly screen against this backdrop. The output classified 417 scorable names using value and quality ranks against reported fundamentals — no macro view, no rate-cycle model, no sector rotation signal.

The screen was bearish. More than a third of the universe landed in AVOID.

---

## 2. The Screener's Classifications

```
    +-------------------------------------------------------------+
    |  Bucket                            n      Share              |
    |  ------                          ---    --------             |
    |  CONVICTION BUY                    5        1.2%             |
    |  QUALITY GROWTH PREMIUM            6        1.4%             |
    |  WATCH LIST                       69       16.5%             |
    |  HOLD                             71       17.0%             |
    |  OVERVALUED QUALITY                2        0.5%             |
    |  OVERVALUED                       74       17.7%             |
    |  VALUE TRAP                       39        9.4%             |
    |  AVOID                           151       36.2%             |
    |                                  ---                         |
    |  Total (scorable)               417                          |
    +-------------------------------------------------------------+
```

Five CONVICTION BUYs out of 417 names — 1.2% of the universe. This was among the most selective screens in the 12-quarter sample. The engine found almost nothing it wanted to own. By contrast, the 2026-04-07 ceasefire screen produced 20 CBs (4.7%). The selectivity here was extreme.

151 names — over a third — sat in AVOID. The engine was looking at a market where most stocks were either too expensive, too low quality, or both. When it did find something, it concentrated heavily.

---

## 3. Result by Bucket

Every classification, matched to its Q4 2023 forward return (2023-09-30 through 2023-12-31):

```
    +--------------------------------------------------------------------+
    |  Bucket                   n     Mean     %pos   vs AVOID            |
    |  ------                 ---   -------   -----   --------            |
    |  CONVICTION BUY           5   +23.0%    100%     +11.8%            |
    |  OVERVALUED QUALITY       2   +19.8%      --       +8.6%           |
    |  OVERVALUED               74   +15.0%     84%      +3.8%           |
    |  QUALITY GROWTH PREMIUM    6   +14.4%    100%      +3.2%           |
    |  HOLD                     71   +12.3%     93%      +1.1%           |
    |  AVOID                   151   +11.2%     81%        --            |
    |  VALUE TRAP               39   +10.6%     82%      -0.6%           |
    |  WATCH LIST               69    +7.1%     68%      -4.1%           |
    |                                                                     |
    |  SPY (benchmark)               +11.6%                              |
    +--------------------------------------------------------------------+
```

**CB beat AVOID by +11.8 percentage points** — the widest spread of any quarter in the 12-quarter sample. All five CB picks were positive. The hit rate was 100%.

This is a strong rising-tide quarter: even AVOID returned +11.2%. The market lifted almost everything. But the five names the screener chose returned twice the market.

Two observations about the bucket ordering:

1. **WATCH LIST was the worst-performing bucket**, not AVOID. The 69 WL names returned only +7.1% — lagging even VALUE TRAP — with the lowest hit rate (68%). In a quarter where almost everything worked, the "needs more evidence" bucket was the weakest.
2. **OVERVALUED (+15.0%) beat HOLD (+12.3%).** In a broad tech rally, the names the screener considered expensive (high quality, high price) were rewarded. This is what a value-tilted screener looks like when growth rips: the buckets it rejects on valuation grounds outperform the neutral tier.

---

## 4. The Five Picks

Every CONVICTION BUY on 2023-09-30, with its Q4 forward return:

| Ticker | Sector | V | Q | Conv | F | Mom | Conf | Return |
|---|---|---:|---:|---:|---:|---:|---|---:|
| **TPR** | Consumer Discretionary | 92.0 | 92.7 | 92.3 | 8 | 42.4 | HIGH | **+29.4%** |
| MCHP | Information Technology | 75.0 | 79.8 | 77.4 | 8 | 68.2 | MODERATE | +16.1% |
| NTAP | Information Technology | 78.1 | 74.1 | 76.1 | 6 | 52.3 | LOW | +17.0% |
| KLAC | Information Technology | 71.3 | 75.9 | 73.6 | 6 | 88.9 | LOW | +27.1% |
| LRCX | Information Technology | 73.7 | 73.4 | 73.5 | 6 | 95.2 | LOW | +25.3% |

**Sector composition:** 4 IT (80%), 1 Consumer Discretionary (20%). The portfolio was heavily concentrated in technology — the sector that happened to lead the rally. Four of the five names were semiconductors or semiconductor-adjacent (MCHP, NTAP, KLAC, LRCX).

**What the scores show:** All five names were cheap (V 71-92), high quality (Q 73-93), and financially healthy (F 6-8, all passing the F>=6 gate). Three of the five had strong momentum (KLAC 88.9, LRCX 95.2, MCHP 68.2). This was the engine finding a cluster of value + quality + health in a sector that happened to be catching a macro tailwind.

**Gate activity:**

```
    +------------------------------------------------------------+
    |  Gate              Victims   Detail                         |
    |  ----              -------   ------                         |
    |  F-gate (F < 6)        0     No stocks rejected             |
    |  Momentum gate         1     SYY (V=75.9, Q=97.2, F=9,     |
    |                               Mom=17.1) -> returned +11.6%  |
    +------------------------------------------------------------+
```

SYY (Sysco) would have qualified for CB on value and quality alone. The momentum gate caught it in the bottom 25% on momentum (17.1) and downgraded it to WATCH LIST. It returned +11.6% — a fine return on its own but well below the CB average of +23.0%. The gate did its job: filtering a low-momentum name that would have diluted the portfolio.

**Confidence gradient:**

```
    +---------------------------------------------------+
    |  Confidence    n    Mean      Best         Worst   |
    |  ----------  ---  --------  ----------   -------   |
    |  HIGH          1   +29.4%   TPR +29.4%   (n=1)    |
    |  MODERATE      1   +16.1%   MCHP +16.1%  (n=1)    |
    |  LOW           3   +23.1%   KLAC +27.1%  +17.0%   |
    +---------------------------------------------------+
```

The gradient was **not monotonic**. The three LOW-confidence picks (NTAP, KLAC, LRCX) outperformed the single MODERATE pick (MCHP) by +7 percentage points. With n=1 in each of the top two tiers, the gradient is meaningless for this quarter — consistent with the investigation's finding that per-quarter monotonicity held in only 1 of 11 quarters.

**Conviction ordering:** Kendall tau = 0.000 — the ordering of picks by conviction score was uncorrelated with returns. TPR (highest conviction, 92.3) was indeed the best performer (+29.4%), but the pattern didn't hold below that: MCHP (second-highest, 77.4) was the worst performer (+16.1%), while LRCX (lowest conviction, 73.5) returned +25.3%. This matches the investigation finding that conviction ordering averages tau = -0.038 across the sample.

---

## 5. Sector-Neutralized: Genuine Stock Selection

This is the load-bearing section of this case study.

The April 2026 empirical investigation (see [`docs/DESIGN_DECISIONS.md`](../DESIGN_DECISIONS.md#sector-rotation-not-stock-selection)) found that the screener's average sector-neutralized excess return was **+0.1%** across 12 quarters — essentially zero. The finding was blunt: the screener tilts sectors, it does not pick stocks. On average, a CB pick performs about as well as a randomly chosen stock from the same sector.

Q4 2023 was the exception.

```
    +--------------------------------------------------------------------+
    |  Ticker  Return   Sector Mean   Excess vs Sector                    |
    |  ------  ------   -----------   ----------------                    |
    |  TPR     +29.4%      +16.1%         +13.4%                          |
    |  KLAC    +27.1%      +17.3%          +9.8%                          |
    |  LRCX    +25.3%      +17.3%          +8.0%                          |
    |  NTAP    +17.0%      +17.3%          -0.3%                          |
    |  MCHP    +16.1%      +17.3%          -1.1%                          |
    |                                                                      |
    |  Mean sector-neutralized excess:   +6.0%                            |
    |  (Best of any quarter in the 12-quarter sample)                     |
    +--------------------------------------------------------------------+
```

Three of the five picks beat their own sector meaningfully. TPR was the standout: +29.4% in Consumer Discretionary when the sector averaged +16.1%, a +13.4% excess. KLAC and LRCX both beat the IT sector mean by +8-10%. The two underperformers (NTAP and MCHP) were essentially sector-inline, not losers.

**Why this matters:** A portfolio that picks 4 IT stocks during a tech rally will look brilliant even if those 4 stocks are chosen at random. The sector-neutralized view strips that away. +6.0% excess vs own sector is not a sector bet — it is the engine finding specific cheap, high-quality names within a sector and those names outperforming their peers. This is what genuine stock selection looks like.

But it was the outlier. The investigation average was +0.1%. The other 11 quarters showed essentially no within-sector alpha. This quarter's +6.0% is what pulled the average up from what would otherwise be slightly negative. One swallow does not make a summer.

---

## 6. What the Screener Missed

**Biggest winners in the universe (Q4 2023):**

| Ticker | Sector | Classification | Return |
|---|---|---|---:|
| CRWD | Information Technology | OVERVALUED | +52.5% |
| EXPE | Consumer Discretionary | WATCH LIST | +47.3% |
| AMD | Information Technology | AVOID | +43.4% |
| GDDY | Information Technology | HOLD | +42.5% |
| INTC | Information Technology | AVOID | +41.8% |
| DHI | Consumer Discretionary | WATCH LIST | +41.7% |
| RCL | Consumer Discretionary | AVOID | +40.5% |
| PHM | Consumer Discretionary | WATCH LIST | +39.7% |

The CB portfolio captured **zero** of the eight best performers. The biggest winners were growth and momentum tech names — CRWD, AMD, INTC — that the screener classified as OVERVALUED or AVOID because they failed the value test. These are exactly the names a value+quality screen is designed to skip: expensive on fundamentals, priced for future growth, rewarded when the market rallies hard on multiple expansion.

The screener's 5 picks returned +23.0%. The top 8 returned +40-52%. The gap is real and reflects the engine's structural bias: it will never catch the momentum leaders in a growth rally. What it caught instead was a concentrated set of value+quality tech names that doubled the market return. The question is always whether "+23% while the top did +50%" is an acceptable trade-off for the quarters when the expensive names crash and the screener is sitting in cheap, healthy businesses. The backtest is the only place that trade-off can be evaluated.

**Worst 10 performers (none were CB):**

```
    +------------------------------------------------------------+
    |  Rank  Ticker  Sector               Class        Return    |
    |  ----  ------  ------               -----        ------    |
    |    1   HAS     Consumer Disc         OVERVALUED   -21.6%   |
    |    2   HRL     Consumer Staples      AVOID        -14.8%   |
    |    3   ALB     Materials             VALUE TRAP   -14.8%   |
    |    4   XOM     Energy                WATCH LIST   -14.2%   |
    |    5   TPL     Energy                HOLD         -13.6%   |
    |    6   APA     Energy                WATCH LIST   -12.2%   |
    |    7   PFE     Health Care           WATCH LIST   -12.0%   |
    |    8   CHTR    Comm Services         VALUE TRAP   -11.6%   |
    |    9   BMY     Health Care           WATCH LIST   -10.7%   |
    |   10   CVX     Energy                WATCH LIST   -10.6%   |
    +------------------------------------------------------------+
```

Zero CONVICTION BUYs in the bottom 10. Energy names dominated the losers (XOM, TPL, APA, CVX) — the same sector the screener refused to own. WATCH LIST appeared five times in the bottom 10, consistent with that bucket's poor overall performance this quarter (+7.1%, worst bucket).

---

## 7. Investigation Context

The April 2026 empirical investigation ([`docs/DESIGN_DECISIONS.md`](../DESIGN_DECISIONS.md#empirical-investigation--component-effectiveness-april-2026)) tested every component of the screener across 12 quarters. Q4 2023 stands out in the investigation data on several dimensions:

```
    +-------------------------------------------------------------------+
    |  Metric                    Q4 2023     12-Quarter Avg              |
    |  ------                    -------     --------------              |
    |  CB - AVOID spread          +11.8%          -0.8%                  |
    |  Sector-neutral excess       +6.0%          +0.1%                  |
    |  CB hit rate                  100%             52%                  |
    |  Confidence monotonic?          No       1 of 11 qtrs              |
    |  Conviction tau               0.00           -0.04                  |
    +-------------------------------------------------------------------+
```

Every metric that looks impressive in isolation is an outlier relative to the full sample:

- **CB-AVOID spread:** The +11.8% is the widest in the sample. The average is -0.8% — CB actually underperforms AVOID on average.
- **Sector-neutral excess:** The +6.0% is the best quarter. Strip this quarter out and the remaining 11 average below zero.
- **Hit rate:** 100% at n=5 is statistically meaningless. The aggregate hit rate across 170 stock-quarter observations is 52%.
- **Confidence gradient and conviction ordering:** Neither worked this quarter, consistent with the investigation's finding that neither works per-quarter in general.

The investigation's central conclusion was that the screener is a sector-rotation engine, not a stock picker. Q4 2023 is the one quarter where it demonstrably picked stocks — and it happened to coincide with the right sector tailwind. These two forces compounded: sector tilt provided the base return; within-sector selection added +6.0% on top. The result was the best quarter in the sample.

---

## 8. Takeaway

Three things had to align for this result:

1. **The screener found cheap, high-quality stocks.** KLAC, LRCX, NTAP, and MCHP were all value+quality semiconductors — cheap on EV/EBIT, strong on Piotroski and gross profitability, healthy enough to pass the F-gate. TPR was the same profile in consumer discretionary.

2. **Those stocks happened to be concentrated in the quarter's leading sector.** Four of five picks were IT. When the Fed-pivot rally lifted tech, the concentration amplified returns. This is the sector-rotation mechanism the investigation identified as the screener's primary source of returns.

3. **The specific stocks outperformed their own sector.** This is the rare part. TPR beat Consumer Discretionary by +13.4%. KLAC and LRCX beat IT by +8-10%. The screener didn't just pick the right sector — it picked the right names within the sector. This happened in Q4 2023 and essentially nowhere else in the 12-quarter sample.

When all three align, the screener produces +23% against a +12% market. When only the first two align (which is the normal case), returns track the sector and the sector-neutralized alpha is zero. When none align — when the screener concentrates in the wrong sector — the result is a losing quarter.

The lesson is not "the screener picks stocks." The investigation showed it doesn't, on average. The lesson is that the screener's structural concentration — 5 picks out of 417, 80% in one sector — creates high variance. When that variance lands favorably, as in Q4 2023, the result is dramatic. When it lands unfavorably, the result is equally dramatic in the other direction. The backtest averages across both.

---

## 9. Caveats

```
    +-------------------------------------------------------------------+
    |  Limitation                  Effect on this case study             |
    |  ----------                  -------------------------             |
    |  n = 5 picks                 Any performance analysis on 5 names   |
    |                              is inside noise. Hit rate of 100%     |
    |                              at n=5 carries no statistical weight. |
    |                                                                     |
    |  No transaction costs        The +23.0% return assumes zero        |
    |                              friction. The backtest includes       |
    |                              transaction cost modeling.            |
    |                                                                     |
    |  Survivorship bias           Universe is S&P 500 membership as     |
    |                              of the screen date. Stocks that       |
    |                              were later removed are not tracked.   |
    |                                                                     |
    |  Cherry-picked quarter       This is the BEST quarter in the       |
    |                              12-quarter sample. Presenting it      |
    |                              without the investigation context     |
    |                              (section 7) would be misleading.      |
    |                              The average CB-AVOID spread is        |
    |                              -0.8%, not +11.8%.                    |
    |                                                                     |
    |  Sector-neutral finding      The +6.0% sector-neutralized excess   |
    |                              is one observation. It could be       |
    |                              luck. The 12-quarter average is       |
    |                              +0.1%. Do not extrapolate.            |
    |                                                                     |
    |  No bootstrap or t-test      All spreads in this document are      |
    |                              descriptive, not inferential.         |
    +-------------------------------------------------------------------+
```

> This case study presents the screener's best quarter because the best quarter is the most interesting one to understand mechanically. It is not representative. The backtest is the only source of evidence this project treats as such; see [`docs/METHODOLOGY.md`](../METHODOLOGY.md) and the quarterly backtest output in `results/backtest_*.csv` for the only performance numbers that deserve statistical weight.

---

<div align="center">
<sub>[Back to README](../../README.md) · [Methodology](../METHODOLOGY.md) · [Design Decisions](../DESIGN_DECISIONS.md) · [Ceasefire Case Study](2026-04-08_ceasefire.md)</sub>
</div>
