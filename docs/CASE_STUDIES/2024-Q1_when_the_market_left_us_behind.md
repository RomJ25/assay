<!--
  Convention: ASCII code-block tables for aggregated summaries (<= 10 rows).
  Real markdown tables are used only for detail listings like the 19-pick grid
  in section 4, where fixed-width formatting would be unreadable.
-->

<div align="center">

# Case Study — Q1 2024: When the Market Left Us Behind

**The screener's worst quarter. A value+quality filter against a growth/momentum rally it was structurally blind to.**

</div>

---

> Individual market events are not evidence -- the backtest is. This case study
> exists to make the screener's structural limitation visible.

---

### Contents

[1. Prologue](#1-prologue--the-q1-2024-setup) · [2. The Classifications](#2-the-screeners-classifications) · [3. Result by Bucket](#3-result-by-bucket--the-inverted-gradient) · [4. The 19 Picks](#4-the-19-picks--what-went-wrong) · [5. What the Screener Missed](#5-what-the-screener-missed) · [6. Sector-Neutralized](#6-sector-neutralized-wrong-stocks-not-just-wrong-sectors) · [7. Gate Analysis](#7-gate-analysis-the-small-saves) · [8. Investigation Context](#8-investigation-context) · [9. Takeaway](#9-takeaway--when-not-to-trust-the-screener) · [10. Caveats](#10-caveats)

---

## 1. Prologue -- The Q1 2024 Setup

The first half of 2024 belonged to a single narrative: artificial intelligence. NVIDIA reported Q4 FY2024 earnings in late February, beating estimates by 29%. The stock was up 80% year-to-date by the end of March. The "Magnificent Seven" -- NVDA, META, MSFT, AAPL, AMZN, GOOGL, TSLA -- were pulling the cap-weighted S&P 500 upward while the equal-weighted index lagged by hundreds of basis points.

This was a growth/momentum tape. What mattered was revenue acceleration, TAM narrative, and price trend. What did not matter was cheapness, balance-sheet discipline, or earnings quality -- the three things Assay's classification matrix is built on.

SPY returned **+4.4%** over the quarter (2024-03-31 to 2024-06-30). The return was concentrated in expensive, high-momentum names. The screener did not break. It did exactly what it is designed to do. The market simply did not reward what the screener selects for.

---

## 2. The Screener's Classifications

**Universe:** 422 scorable names on 2024-03-31.

```
    +-------------------------------------------------------------+
    |  Bucket                            n      Share              |
    |  ------                          ---    --------             |
    |  CONVICTION BUY                   19        4.5%             |
    |  QUALITY GROWTH PREMIUM           40        9.5%             |
    |  WATCH LIST                       88       20.9%             |
    |  HOLD                             72       17.1%             |
    |  OVERVALUED QUALITY               48       11.4%             |
    |  OVERVALUED                        74       17.5%             |
    |  VALUE TRAP                         9        2.1%            |
    |  AVOID                            72       17.1%             |
    |                                  ---                         |
    |  Total (scorable)                422                         |
    +-------------------------------------------------------------+
```

The distribution looks normal. The engine found 19 names it liked -- a typical quarter. The problem was not in the classification machinery. It was in what the market chose to reward.

---

## 3. Result by Bucket -- The Inverted Gradient

Every 2024-03-31 classification, matched to its quarterly return through 2024-06-30:

```
    +----------------------------------------------------------------------+
    |  Bucket                   n     Mean     %pos   vs CB    Direction    |
    |  ------                 ---   -------  ------  ------   ----------   |
    |  AVOID                   72    +2.3%     64%   +7.7%    BEST         |
    |  OVERVALUED QUALITY      48    +0.5%     56%   +5.9%                 |
    |  QUALITY GROWTH PREMIUM  40    +1.1%     45%   +6.5%                 |
    |  OVERVALUED               74    -1.5%     43%   +3.9%                 |
    |  VALUE TRAP                9    -1.3%     33%   +4.1%                 |
    |  HOLD                    72    -2.0%     42%   +3.4%                 |
    |  WATCH LIST              88    -4.9%     35%   +0.5%                 |
    |  CONVICTION BUY          19    -5.4%     26%     --     WORST        |
    |                                                                      |
    |  SPY (benchmark)               +4.4%                                 |
    +----------------------------------------------------------------------+
```

**AVOID (+2.3%) was the best-performing bucket. CONVICTION BUY (-5.4%) was the worst.** The gradient did not just fail to be monotonic -- it *inverted*. Only 26% of CB picks were positive. AVOID had a 64% hit rate. The spread: **-7.7 percentage points**.

The April 2026 investigation found CB beat AVOID in only 6 of 11 quarters, with an average spread of -0.8%. This quarter was the worst example of a pattern that occurs roughly half the time.

---

## 4. The 19 Picks -- What Went Wrong

Every CONVICTION BUY on 2024-03-31, with its quarterly forward return. Sorted by conviction score, highest to lowest:

| Ticker | Sector | V | Q | Conv | F | Mom | Conf | Return |
|---|---|---|---|---:|---:|---:|---|---:|
| TPR | Consumer Discretionary | 90.3 | 92.7 | 91.5 | 8 | 46.7 | HIGH | **-9.1%** |
| EXPE | Consumer Discretionary | 88.6 | 90.6 | 89.6 | 8 | 76.6 | HIGH | **-8.5%** |
| MAS | Industrials | 84.1 | 90.7 | 87.3 | 8 | 87.8 | MOD | **-15.1%** |
| MO | Consumer Staples | 96.5 | 77.3 | 86.4 | 7 | 25.6 | MOD | +6.7% |
| SYY | Consumer Staples | 75.2 | 97.5 | 85.6 | 9 | 40.2 | MOD | -11.5% |
| SNA | Industrials | 89.9 | 80.6 | 85.1 | 8 | 48.3 | MOD | -11.2% |
| UHS | Health Care | 71.8 | 99.9 | 84.7 | 9 | 69.1 | LOW | +1.5% |
| EOG | Energy | 95.2 | 72.7 | 83.2 | 6 | 35.4 | LOW | -0.9% |
| AOS | Industrials | 76.2 | 88.6 | 82.2 | 8 | 55.7 | MOD | -8.2% |
| HCA | Health Care | 78.9 | 82.8 | 80.8 | 7 | 53.3 | MOD | -3.5% |
| CMCSA | Communication Services | 89.9 | 72.4 | 80.7 | 7 | 50.0 | LOW | **-9.0%** |
| CTSH | Information Technology | 88.8 | 71.2 | 79.5 | 6 | 68.7 | LOW | -6.8% |
| MCHP | Information Technology | 77.3 | 80.7 | 79.0 | 8 | 32.3 | MOD | +2.5% |
| FFIV | Information Technology | 71.2 | 86.7 | 78.6 | 8 | 66.5 | LOW | **-9.2%** |
| UNH | Health Care | 82.0 | 73.6 | 77.7 | 7 | 37.3 | LOW | +3.4% |
| EME | Industrials | 75.1 | 77.8 | 76.4 | 8 | 95.2 | MOD | +4.3% |
| ALLE | Industrials | 70.0 | 82.7 | 76.1 | 8 | 55.3 | LOW | -11.9% |
| CAT | Industrials | 78.0 | 73.5 | 75.7 | 8 | 83.0 | LOW | -8.8% |
| JNJ | Health Care | 74.9 | 75.7 | 75.3 | 7 | 39.5 | LOW | -6.9% |

**14 of 19 picks were negative.** Only 5 finished in the green: MO (+6.7%), EME (+4.3%), UNH (+3.4%), MCHP (+2.5%), UHS (+1.5%). The best gain was +6.7%; the worst loss was -15.1% (MAS). Losses were bigger than wins.

**Sector composition:**

```
    +----------------------------------------------+
    |  Sector                        n              |
    |  ------                      ---              |
    |  Industrials                   6   (32%)      |
    |  Health Care                   4   (21%)      |
    |  Information Technology        3   (16%)      |
    |  Consumer Staples              2   (11%)      |
    |  Consumer Discretionary        2   (11%)      |
    |  Communication Services        1    (5%)      |
    |  Energy                        1    (5%)      |
    |  Financials                    0              |
    |  Utilities                     0              |
    |  Real Estate                   0              |
    +----------------------------------------------+
```

Industrials and Health Care made up 53% of the picks. The April 2026 investigation found 80% of all CB picks across 12 quarters came from just 4 sectors. In a quarter where growth/momentum dominated and value/quality sectors lagged, the concentration was lethal.

**Confidence gradient:**

```
    +---------------------------------------------------+
    |  Confidence    n    Mean     vs SPY                |
    |  ----------  ---  --------  --------              |
    |  HIGH          2   -8.8%    -13.2 pp              |
    |  MODERATE      8   -4.5%     -8.9 pp              |
    |  LOW           9   -5.4%     -9.8 pp              |
    |                                                    |
    |  HIGH - LOW spread:  -3.4 pp  (INVERTED)          |
    +---------------------------------------------------+
```

The confidence gradient was also broken. The two highest-confidence picks -- TPR (-9.1%) and EXPE (-8.5%) -- were among the worst performers. HIGH underperformed LOW by 3.4 pp. Per-quarter confidence monotonicity held in only 1 of 11 quarters studied; this was one of the ugliest failures.

**Conviction ordering:** Kendall tau = **-0.146**. The correlation between conviction score and return was *negative*. Higher-conviction picks did worse. This is consistent with the investigation's finding that within-CB conviction ordering shows slightly negative tau in aggregate -- the conviction score tells you a stock clears the bar, not how much it will outperform.

---

## 5. What the Screener Missed

The quarter's biggest winners were overwhelmingly in OVERVALUED, AVOID, or OVERVALUED QUALITY -- the buckets the screener explicitly warns against:

| Ticker | Sector | Assay Classification | Q Return |
|---|---|---|---:|
| CVNA | Consumer Discretionary | OVERVALUED | **+46.4%** |
| NVDA | Information Technology | OVERVALUED | **+36.7%** |
| FSLR | Information Technology | AVOID | +33.6% |
| TER | Information Technology | OVERVALUED QUALITY | +31.5% |
| TPL | Energy | QUALITY GROWTH PREMIUM | +27.2% |
| GEV | Industrials | OVERVALUED | +25.4% |
| SATS | Communication Services | AVOID | +25.0% |
| TKO | Communication Services | AVOID | +25.0% |

NVDA was classified as OVERVALUED because it was expensive -- its Value score was low. The screener saw a company trading at a price that embedded years of growth expectations, and it said "overvalued." On its own terms, the classification was correct: NVDA *was* expensive relative to reported fundamentals. It just did not matter. The market was pricing AI growth that backward-looking fundamental data could not capture.

FSLR was in AVOID. SATS and TKO were in AVOID. The quarter's best-performing stocks were the ones the screener said to stay away from.

This is the structural limitation in its purest form. A value+quality filter scores on what a company *has earned and owns*. It cannot score on what a company *will earn* if a new technology reshapes its TAM. The screener is blind to narrative-driven rerating by design.

**For comparison, the quarter's worst performers:**

```
    +-------------------------------------------------------------+
    |  Rank  Ticker  Sector              Return   Classification   |
    |  ----  ------  ------            --------  ---------------   |
    |    1   BLDR    Industrials        -33.6%   WATCH LIST  *     |
    |    2   EPAM    Info Technology    -31.9%   HOLD              |
    |    3   EL      Consumer Staples   -30.6%   OVERVALUED        |
    |    4   INTC    Info Technology    -29.6%   AVOID             |
    |                                                              |
    |  * BLDR was an F-gate victim: would have been CB without     |
    |    the gate. See section 7.                                  |
    +-------------------------------------------------------------+
```

The screener avoided INTC (AVOID) and BLDR (caught by the F-gate). Small consolations in a -5.4% quarter.

---

## 6. Sector-Neutralized: Wrong Stocks, Not Just Wrong Sectors

The easy explanation is "wrong sectors." Partly true -- value/quality sectors lagged growth/momentum -- but not the whole story. When each CB pick's return is compared to its own sector mean, the average excess was **-3.6%**. The screener picked the wrong stocks *even within its own sectors*.

**Worst stock-selection within sectors:**

```
    +---------------------------------------------------------------+
    |  Ticker  Return   Sector Mean   Excess     Sector              |
    |  ------  ------   -----------   ------     ------              |
    |  FFIV    -9.2%      +5.2%       -14.4%    Info Technology      |
    |  CMCSA   -9.0%      +4.8%       -13.8%    Comm Services        |
    |  MAS    -15.1%      -3.0%       -12.2%    Industrials          |
    |  CTSH    -6.8%      +5.2%       -12.1%    Info Technology      |
    +---------------------------------------------------------------+
```

FFIV returned -9.2% while the average IT stock returned +5.2%. The screener's IT picks were the *wrong* IT stocks -- cheap, mature names (FFIV, CTSH, MCHP) rather than the expensive, fast-growing ones (NVDA, META, MSFT). Within IT, cheapness was a contrarian signal this quarter, and it lost.

**Best stock-selection within sectors:**

```
    +---------------------------------------------------------------+
    |  Ticker  Return   Sector Mean   Excess     Sector              |
    |  ------  ------   -----------   ------     ------              |
    |  MO      +6.7%      -5.1%       +11.8%    Consumer Staples     |
    |  UNH     +3.4%      -4.5%        +7.9%    Health Care          |
    +---------------------------------------------------------------+
```

MO and UNH were genuine stock-selection wins. But two winners in a portfolio of 19 picks do not offset the damage.

**The critical finding:** The April 2026 investigation found sector-neutralized CB excess averaged **+0.1%** across 170 stock-quarter observations -- essentially zero. The screener tilts sectors, not picks stocks. At -3.6% sector-neutral, Q1 2024 was the worst example of that structural feature becoming a liability.

---

## 7. Gate Analysis: The Small Saves

The F-gate and momentum gate -- designed to prevent the worst picks from reaching CONVICTION BUY -- had mixed results this quarter.

### F-gate victims (2 stocks)

```
    +---------------------------------------------------------------+
    |  Ticker  V      Q      F   Return   Gate outcome               |
    |  ------  ----   ----   --  ------   ------------               |
    |  BLDR    87.0   74.7    5  -33.6%   SAVED -- worst in universe |
    |  INCY    81.6   73.4    5   +6.4%   COST -- missed a winner    |
    +---------------------------------------------------------------+
```

BLDR would have been the screener's worst pick by a wide margin. The F-gate caught it. This single save -- preventing a -33.6% position -- would have dragged the CB mean from -5.4% to roughly -6.7%. INCY was a missed +6.4% gain. Net: the F-gate clearly helped this quarter.

### Momentum gate victims (7 stocks)

| Ticker | V | Q | F | Mom | Return | Gate outcome |
|---|---:|---:|---:|---:|---:|---|
| BMY | 82.5 | 70.9 | 6 | 4.5 | -22.5% | SAVED |
| GPC | 77.9 | 82.8 | 7 | 14.8 | -10.1% | SAVED |
| GILD | 88.9 | 73.5 | 7 | 12.2 | -5.2% | Saved |
| HSY | 70.0 | 86.4 | 8 | 4.3 | -4.9% | Saved |
| CSCO | 90.1 | 76.0 | 7 | 19.6 | -4.0% | Saved |
| CPB | 81.8 | 76.7 | 9 | 6.7 | +2.5% | Missed |
| KMB | 72.3 | 76.6 | 7 | 15.6 | +7.8% | Missed |

Five of seven momentum victims would have lost money. BMY (-22.5%) and GPC (-10.1%) were particularly bad saves. Two victims (CPB +2.5%, KMB +7.8%) were missed gains. Both gates helped this quarter, but these are small saves relative to the portfolio's -5.4% headline -- the gates prevented the result from being worse, but they could not fix the structural problem.

---

## 8. Investigation Context

The April 2026 empirical investigation ([`docs/DESIGN_DECISIONS.md`](../DESIGN_DECISIONS.md), "Empirical investigation -- component effectiveness") tested every component across 12 quarters. Q1 2024 was the worst quarter for nearly every metric:

1. **Classification gradient:** CB beat AVOID in only 6 of 11 quarters. Average CB-AVOID spread was -0.8%. Q1 2024 was the worst single quarter at -7.7%.

2. **Sector exposure:** Under quarterly rebalancing, sector-neutralized alpha was +0.1% (near zero). Under the selective sell strategy, this improved to +0.5% — holding appreciated stocks that outperform their sectors contributes genuine stock selection. Q1 2024 was still the worst quarter regardless of strategy.

3. **Confidence gradient:** Aggregate returns across 12 quarters were monotonic (HIGH +6.7% > MOD +5.4% > LOW +3.3%), but per-quarter monotonicity held in only 1 of 11 quarters. Q1 2024's inverted gradient (HIGH worst, MOD best) is ugly but not unusual.

4. **Win/loss asymmetry:** Under quarterly rebalancing, the win/loss ratio was 1.05x (essentially random). Under the selective sell strategy, it improved to 1.28x — holding winners longer creates meaningful asymmetry. Q1 2024 remains a losing quarter under both strategies.

5. **Momentum gate:** The investigation's most validated component (victims averaged +2.6% vs CB +4.5%, underperforming in 7 of 10 quarters). Q1 2024 was one of the quarters where the gate worked well.

The investigation led to the selective sell strategy (see `docs/STRATEGY.md`) — the single largest improvement to the system's performance.

---

## 9. Takeaway -- When NOT to Trust the Screener

This quarter makes the screener's structural limitation concrete:

**When growth/momentum dominates, expect the screener to underperform.** It is not broken -- it is filtering for value+quality, and value+quality does not work every quarter. When the market rewards the opposite characteristics, the screener will be on the wrong side.

The specific failure modes:

1. **The gradient inverted.** AVOID beat CB by 7.7 percentage points. The classification was exactly backwards.
2. **-3.6% sector-neutral.** Wrong stocks even within the screener's own sectors.
3. **AI/growth rally invisible to the filter.** NVDA was "OVERVALUED" because it was expensive. Backward-looking fundamentals cannot capture narrative-driven rerating.
4. **Confidence gradient inverted.** The two highest-confidence picks (TPR, EXPE) were among the worst performers.
5. **Gates helped but could not fix the problem.** The F-gate caught BLDR (-33.6%), the momentum gate caught BMY (-22.5%) and GPC (-10.1%). Band-aids on a structural wound.

**The practical implication for users:** If the Magnificent Seven are rallying 30-40% in a quarter, the screener's CB list is likely to lag. This is not a signal to override the screener and chase growth -- the backtest shows the screener wins more quarters than it loses. But it *is* a signal to calibrate expectations: value+quality is a long-run strategy, and long-run strategies have bad quarters. This was the worst one.

---

## 10. Caveats

```
    +-------------------------------------------------------------------+
    |  Limitation                  Effect on this case study             |
    |  ----------                  -------------------------             |
    |  n = 1 quarter               This is a single observation. The    |
    |                              backtest (12+ quarters) is the only  |
    |                              source of evidence this project      |
    |                              treats as such.                      |
    |                                                                    |
    |  No transaction costs        Quarterly rebalance with full        |
    |                              turnover understates friction.        |
    |                              Backtest includes tcosts.            |
    |                                                                    |
    |  Close-to-close only         yfinance adjusted close prices.      |
    |                              No intraday data.                    |
    |                                                                    |
    |  Survivorship bias           Universe is the S&P 500 list as of   |
    |                              2024-03-31. Stocks subsequently      |
    |                              removed from the index may bias      |
    |                              the sample.                          |
    |                                                                    |
    |  No bootstrap or t-test      All comparisons are descriptive,      |
    |                              not inferential.                     |
    |                                                                    |
    |  Sector means are simple     Equal-weighted sector means, not     |
    |  averages                    cap-weighted.                        |
    |                                                                    |
    |  Cherry-picked quarter       Selected because it is the worst,   |
    |                              not because it is representative.    |
    |                              Backtest mean CB return is positive. |
    +-------------------------------------------------------------------+
```

> This is a failure case study. The screener failed this quarter by every
> metric it claims to optimize. The honest response is not to explain it
> away but to document it clearly, understand why it happened, and
> acknowledge that it will happen again. Value+quality strategies have
> bad quarters. This was the worst one. The backtest is the only thing
> that matters for the long-run question; see `results/backtest_*.csv`.

---

<div align="center">
<sub>[Back to README](../../README.md) · [Methodology](../METHODOLOGY.md) · [Design Decisions](../DESIGN_DECISIONS.md) · [Ceasefire Case Study](2026-04-08_ceasefire.md)</sub>
</div>
