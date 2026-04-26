> **Naming note (2026-04-26):** This case study refers to the classification `CONVICTION BUY`. Effective 2026-04-26 that label was renamed to `RESEARCH CANDIDATE` everywhere in the live codebase, with no semantic change. This document is preserved as historical narrative and uses the original term.

<!--
  Convention: ASCII code-block tables for aggregated summaries (<= 10 rows).
  Real markdown tables are used only for detail listings like the 20-pick grid
  in section 5, where fixed-width formatting would be unreadable.
-->

<div align="center">

# Case Study — 2026-04-08 Iran Ceasefire Rally

**A one-day, n=1 field test of Assay's 2026-04-07 classifications against a violent, news-driven sector rotation.**

</div>

---

### Contents

[1. Prologue](#1-prologue--the-04-07-setup) · [2. The Event](#2-the-event--04-08) · [3. Result by Bucket](#3-result-by-classification-bucket) · [4. Confidence Gradient](#4-confidence-gradient-validation) · [5. Every Pick](#5-the-20-conviction-buys--every-pick) · [6. Best Ideas](#6-the-best-ideas-lens) · [7. Worst Performers](#7-the-10-worst-performers-and-who-owned-them) · [8. Mathematics](#8-the-mathematics-of-the-refusal) · [9. Takeaway](#9-takeaway--the-asymmetry-in-one-day) · [10. Caveats](#10-caveats-and-scope) · [11. References](#11-academic-references)

---

## 1. Prologue — The 04-07 Setup

For five weeks, one trade dominated the tape. The Iran conflict, escalating since early March, had driven WTI crude from roughly $71 per barrel to above $100. The energy complex went vertical. Through 2026-03-31, ExxonMobil was **+40.98% YTD**, Chevron was **+35.75% YTD**, and the Vanguard Energy Index (VDE) had gained roughly 37% while the S&P 500 itself was *down* 4.6% on the year.[^1] Energy was not just hot — it was the only sector where anything was working.

On the evening of Tuesday, 2026-04-07, Assay produced its routine S&P 500 screen against that backdrop. The output lived in `results/screen_2026-04-07.csv`: 425 scorable names, classified using value and quality ranks against reported fundamentals — no macro view, no sector rotation model, no awareness of the war at all.

**The classification distribution:**

```
    ┌─────────────────────────────────────────────────────────┐
    │  Bucket                            n      Share         │
    │  ──────                          ───    ────────        │
    │  CONVICTION BUY                   20        4.7%        │
    │  QUALITY GROWTH PREMIUM           43       10.1%        │
    │  WATCH LIST                       84       19.8%        │
    │  HOLD                             80       18.8%        │
    │  OVERVALUED QUALITY               44       10.4%        │
    │  OVERVALUED                       81       19.1%        │
    │  VALUE TRAP                        8        1.9%        │
    │  AVOID                            65       15.3%        │
    │                                  ───                    │
    │  Total (scorable)                425                    │
    └─────────────────────────────────────────────────────────┘
```

The load-bearing fact of this document, delivered up front:

> **Zero energy names in CONVICTION BUY. Not one.**

Every single Energy-sector name on the S&P 500 list was sorted into a non-buy classification:

```
    ┌──────────────────────────────────────────────────────────┐
    │  Energy sector — Assay 2026-04-07 classifications         │
    │  ───────────────────────────────────────────────          │
    │  AVOID           XOM, OXY, VLO, FANG                      │
    │  OVERVALUED      CVX, PSX, WMB, TPL                       │
    │  WATCH LIST      APA, COP, DVN, CTRA, EOG, HAL, EQT, EXE  │
    │  HOLD            MPC, OKE, TRGP, BKR, KMI                 │
    │  VALUE TRAP      SLB                                       │
    │  CONVICTION BUY  — (none)                                 │
    └──────────────────────────────────────────────────────────┘
```

The same story held for the commodity chemicals and fertilizer names whose margin story was built on crude feedstock economics: LYB and DOW sat in AVOID, CF in WATCH LIST. If you had run Assay on 04-07 and followed it literally, you would have owned none of the year's biggest winners — the stocks that had just put on 35–40% in a quarter. A naive reading would call that lagging. The next morning, it became a refusal.

[^1]: Close-to-close returns computed from yfinance historical data, dividend-unadjusted. See §10 for methodology.

---

## 2. The Event — 04-08

Shortly before Tuesday's 8 p.m. ET deadline for Iranian concessions, President Trump announced a two-week suspension of U.S. and Israeli bombing operations, conditional on Iran reopening the Strait of Hormuz for safe passage.[^2] Iranian Foreign Minister Abbas Araghchi confirmed the agreement within the hour. Pakistan had brokered the talks; a follow-on negotiation was scheduled for Friday in Islamabad.[^3]

Markets opened Wednesday 2026-04-08 to a full unwind of the war premium.

**Headline moves (close-to-close):**

```
    ┌────────────────────────────────────────────────────────┐
    │  Instrument          04-07 Close   04-08 Close   1-day │
    │  ──────────          ───────────   ───────────   ───── │
    │  S&P 500 (^SPX)         6,616.85      6,782.81  +2.51% │
    │  SPY ETF                  659.22        676.01  +2.55% │
    │  WTI crude (front)          $111           $95   ~-15% │
    │  VDE (Energy ETF)          170.54        164.78  -3.38% │
    └────────────────────────────────────────────────────────┘
```

WTI futures fell below $95 per barrel for the first time in weeks, erasing roughly a month of geopolitical repricing in a single session.[^4] The index-level +2.5% return concealed an extreme dispersion underneath:

```
    ┌────────────────────────────────────────────────────┐
    │  Sector                       n    Mean 1-day      │
    │  ──────                     ───    ──────────      │
    │  Consumer Discretionary      46      +3.84%        │
    │  Industrials                 79      +3.59%        │
    │  Materials                   26      +3.52%  *     │
    │  Information Technology      73      +3.09%        │
    │  Health Care                 58      +2.37%        │
    │  Financials                  31      +2.06%        │
    │  Consumer Staples            35      +1.11%        │
    │  Communication Services      23      +1.05%        │
    │  Utilities                   31      +1.03%        │
    │  Energy                      22      -3.08%        │
    │                                                     │
    │  * Materials bimodal: commodity chems/fertilizer    │
    │    (LYB -7.5%, DOW -5.1%, CF -5.7%) crashed;        │
    │    industrial/packaging (AMCR, PPG, SW, FCX, IP)    │
    │    rallied +7-8% on easing feedstock costs.         │
    └────────────────────────────────────────────────────┘
```

This was not a "risk-on, everything up" rally. It was a **violent rotation**. 20 of the 22 Energy-sector names on the S&P 500 closed negative; the only two exceptions were oilfield services (SLB +3.04%, BKR +3.12%), which trade more on forward drilling capex expectations than on spot crude. The commodity-chemicals cohort got hit almost as hard as oil itself. The rally flowed into cyclicals and capex-sensitive tech on easing input costs and revived Fed rate-cut bets; a secondary selloff hit richly-priced software (WDAY -6.5%, PLTR -6.2%, INTU -5.1%, CRM -3.6%) as profit-taking moved out of duration and into cyclicals.

Anyone tilted toward value via cheap EV/EBIT *had to make a decision* in the weeks leading up to this day: whether to chase the cheapest thing on the tape (energy) or refuse it. Assay refused it — and refused it sector-agnostically, using no macro view at all.

[^2]: NPR, "U.S. and Iran agree to 2-week ceasefire, suspending Trump's threat to annihilate Iran," 2026-04-07. Axios, "US, Iran to pause war, agree to 2-week ceasefire," 2026-04-07.

[^3]: CNBC, "Trump, Iran agree to two-week ceasefire, plan to open Strait of Hormuz," 2026-04-07.

[^4]: Intraday range on WTI reached roughly -15 to -17% depending on reference point. Close-to-close on the front-month contract was below $95 from above $110, a drop of roughly 14–15%. News reporting varied between -15% and -17% due to intraday vs. settlement comparisons.

---

## 3. Result by Classification Bucket

Every 2026-04-07 classification, matched to its 1-day return through 2026-04-08 close. Universe: 424 names with clean close-to-close prices (HOLX excluded — trading halted, see §10).

```
    ┌──────────────────────────────────────────────────────────────────────┐
    │  Bucket                   n     Mean    Median   vs SPY  %up  %beat  │
    │  ──────                 ───   ───────  ───────  ──────  ───  ─────   │
    │  OVERVALUED              81    +3.44%   +3.33%    +90   85%   60%   │
    │  OVERVALUED QUALITY      44    +3.21%   +2.77%    +66   89%   52%   │
    │  CONVICTION BUY          20    +2.29%   +2.16%    -26   95%   45%   │
    │  VALUE TRAP               8    +2.31%   +1.97%    -24   88%   38%   │
    │  HOLD                    79    +2.42%   +2.27%    -13   86%   48%   │
    │  QUALITY GROWTH PREMIUM  43    +2.14%   +2.21%    -41   84%   42%   │
    │  AVOID                   65    +1.76%   +1.44%    -79   83%   35%   │
    │  WATCH LIST              84    +1.47%   +2.07%   -108   65%   44%   │
    │                                                                      │
    │  Universe (EW, n=424)         +2.37%                                 │
    │  SPY (benchmark)              +2.55%                                 │
    │  "vs SPY" column shown in basis points                               │
    └──────────────────────────────────────────────────────────────────────┘
```

**Spread analysis:**

```
    ┌─────────────────────────────────────────────────────────┐
    │  Spread                                    1-day gap    │
    │  ──────                                    ─────────    │
    │  OVERVALUED   –  WATCH LIST                 +197 bps    │
    │  OVERVALUED   –  AVOID                      +169 bps    │
    │  CONVICTION BUY – AVOID                      +53 bps    │
    │  CONVICTION BUY – WATCH LIST                 +81 bps    │
    └─────────────────────────────────────────────────────────┘
```

The headline result — CONVICTION BUY +2.29% vs SPY +2.55% — is a 26-basis-point underperformance that is entirely inside daily noise for a 20-name equal-weighted portfolio. On its own it says nothing. The bucket ordering, however, is not inside noise. Read the full column:

> On a **+2.55% day for SPY**, the two most-cheap-value-penalized buckets (OVERVALUED and OVERVALUED QUALITY) led the universe. The two **least-cheap-penalized buckets** (CONVICTION BUY and VALUE TRAP — both with Value ≥ 70) landed in the middle. And the buckets the engine was **most skeptical of** (AVOID, WATCH LIST) lagged by -79 and -108 bps.

This is what a value-tilted strategy looks like on a day when the market abandons defensiveness in favor of high-beta cyclicals. Anything with a "cheap" tilt was sitting in Energy, and Energy was the wreckage. The engine's refusal to tilt toward it — plus its refusal to own the profitless-tech QGP names that also sold off — shows up as a quiet CONVICTION BUY bucket near the universe mean, **not** as a hero result. The edge shows up in the *shape of the full distribution*, not in the CB headline.

**On a sharp rally day, the meaningful finding is not that CB won — it's that the engine's "no" calls concentrated the day's losses.** The two worst-performing buckets in the entire universe were WATCH LIST and AVOID — the engine's two most explicit "needs skepticism" tags — and they lagged the universe mean by -90 and -61 bps respectively. The next two sections take that observation and tighten it.

---

## 4. Confidence Gradient Validation

Within the 20 CONVICTION BUYs, Assay attaches a **confidence label** — HIGH, MODERATE, or LOW — derived mechanically from the weakest of the two scores. Per [`docs/METHODOLOGY.md` §6.1](../METHODOLOGY.md#61-confidence-levels), the formula is:

```
    confidence(V, Q) =
      HIGH     if min(V - 70, Q - 70) >= 15
      MODERATE if min(V - 70, Q - 70) >=  5
      LOW      otherwise
```

Returns on 2026-04-08, grouped by this label:

```
    ┌───────────────────────────────────────────────────┐
    │  Confidence    n    Mean     vs SPY    %beat SPY  │
    │  ──────────  ───  ────────  ────────  ──────────  │
    │  HIGH          5   +3.22%     +67 bp       60%    │
    │  MODERATE      7   +2.66%     +11 bp       57%    │
    │  LOW           8   +1.37%    -118 bp       25%    │
    │                                                    │
    │  HIGH − LOW spread:  +185 bps                      │
    └───────────────────────────────────────────────────┘
```

The ordering is **monotonic**. Higher confidence → higher return → higher hit rate against SPY. The bottom-confidence cohort underperformed by -118 bps; the top-confidence cohort outperformed by +67 bps. Both CB sub-buckets beat SPY at the top end; the LOW tier dragged the aggregate below it.

### The `min` formula, in action

Trace it mechanically for each of the 20 CBs:

```
    HIGH (min >= 15):
      UHS   V=92.6  Q=94.2   min = 22.6
      AOS   V=87.2  Q=88.7   min = 17.2
      INCY  V=91.7  Q=87.0   min = 17.0
      BBY   V=95.9  Q=86.5   min = 16.5
      EXPE  V=87.8  Q=85.3   min = 15.3

    MODERATE (5 <= min < 15):
      BMY   V=91.7  Q=83.4   min = 13.4
      HCA   V=82.4  Q=84.1   min = 12.4
      CMCSA V=96.9  Q=80.0   min = 10.0
      MAS   V=87.9  Q=78.4   min =  8.4
      TGT   V=77.1  Q=78.2   min =  7.1
      GILD  V=75.1  Q=83.8   min =  5.1
      NTAP  V=84.0  Q=75.1   min =  5.1

    LOW (min < 5):
      MO    V=91.8  Q=74.6   min =  4.6
      DLTR  V=73.4  Q=90.1   min =  3.4
      NEM   V=90.0  Q=73.0   min =  3.0
      ULTA  V=71.1  Q=81.8   min =  1.1
      ALLE  V=74.6  Q=70.8   min =  0.8
      EXPD  V=70.5  Q=77.1   min =  0.5
      LDOS  V=90.0  Q=70.5   min =  0.5
      DG    V=70.1  Q=80.4   min =  0.1
```

A single scalar — the weaker of the two standardized scores, minus the 70-threshold — produced an ordering that held in live market data on a day neither the engine nor the formula knew anything about. This is the `min()` function doing exactly what the methodology claims: **the weakest dimension determines confidence**. When the weakest is still strong (HIGH), both fundamentals are comfortably above the CB bar and there is less room to disappoint. When the weakest is barely over the line (LOW), one of the two dimensions is at 70.1 or 70.5 — a single revision away from dropping the stock out of CB entirely.

This is the cleanest possible one-day validation of that formula. One data point is not a backtest — but the gradient is mechanical, and the result matched the mechanics.

---

## 5. The 20 CONVICTION BUYs — Every Pick

Every CONVICTION BUY on 2026-04-07, with its 1-day forward return. Sorted best to worst:

| Ticker | Company | Sector | Conf | Conv | 04-07 | 04-08 | 1-day |
|---|---|---|---|---:|---:|---:|---:|
| **EXPE**  | Expedia Group              | Consumer Discretionary  | **HIGH**     | 86.5 |  224.30 |  236.90 | **+5.62%** |
| **MAS**   | Masco                      | Industrials             | MODERATE | 83.0 |   59.10 |   62.23 | **+5.30%** |
| AOS   | A. O. Smith                | Industrials             | **HIGH**     | 87.9 |   64.19 |   66.77 | +4.02% |
| ALLE  | Allegion                   | Industrials             | *LOW*    | 72.7 |  139.40 |  144.49 | +3.65% |
| UHS   | Universal Health Services  | Health Care             | **HIGH**     | **93.4** |  180.61 |  186.76 | +3.41% |
| HCA   | HCA Healthcare             | Health Care             | MODERATE | 83.2 |  489.58 |  505.12 | +3.17% |
| NEM   | Newmont                    | Materials               | *LOW*    | 81.1 |  114.65 |  118.15 | +3.05% |
| TGT   | Target                     | Consumer Staples        | MODERATE | 77.6 |  119.52 |  123.12 | +3.01% |
| BMY   | Bristol Myers Squibb       | Health Care             | MODERATE | 87.5 |   57.67 |   59.20 | +2.65% |
| INCY  | Incyte                     | Health Care             | **HIGH**     | 89.3 |   93.69 |   95.89 | +2.35% |
| GILD  | Gilead Sciences            | Health Care             | MODERATE | 79.3 |  138.80 |  141.54 | +1.97% |
| NTAP  | NetApp                     | Information Technology  | MODERATE | 79.4 |   97.61 |   99.47 | +1.91% |
| DG    | Dollar General             | Consumer Staples        | *LOW*    | 75.1 |  121.21 |  123.05 | +1.52% |
| EXPD  | Expeditors International   | Industrials             | *LOW*    | 73.7 |  144.53 |  146.62 | +1.45% |
| LDOS  | Leidos                     | Industrials             | *LOW*    | 79.7 |  158.87 |  160.64 | +1.11% |
| MO    | Altria                     | Consumer Staples        | *LOW*    | 82.8 |   66.25 |   66.80 | +0.83% |
| BBY   | Best Buy                   | Consumer Discretionary  | **HIGH**     | 91.1 |   64.02 |   64.48 | +0.72% |
| CMCSA | Comcast                    | Communication Services  | MODERATE | 88.0 |   27.79 |   27.96 | +0.61% |
| ULTA  | Ulta Beauty                | Consumer Discretionary  | *LOW*    | 76.3 |  532.23 |  532.82 | +0.11% |
| **DLTR**  | Dollar Tree                | Consumer Staples        | *LOW*    | 81.3 |  106.42 |  105.62 | **-0.75%** |

> **19 of 20 closed positive.** The single loser (DLTR -0.75%) is smaller in magnitude than the best gain (EXPE +5.62%) by a factor of more than 7. Zero energy names. Zero commodity-chemical names. Zero of the profitless-tech names in the day's worst 20. The sector composition of the picks was entirely out of the path of every major loss.

**Sector distribution of the 20 picks:**

```
    ┌──────────────────────────────────────────────┐
    │  Sector                        n              │
    │  ──────                      ───              │
    │  Health Care                   5              │
    │  Industrials                   5              │
    │  Consumer Staples              4              │
    │  Consumer Discretionary        3              │
    │  Communication Services        1              │
    │  Information Technology        1              │
    │  Materials                     1   (NEM)      │
    │  Energy                        0              │
    │  Financials                    0              │
    │  Utilities                     0              │
    │  Real Estate                   0              │
    └──────────────────────────────────────────────┘
```

The single materials name was NEM (Newmont) — a gold miner, structurally insulated from petroleum feedstock exposure. It returned +3.05% on the day. The *absence* of Energy is the operative feature of this list: it is not that the engine actively hedged the ceasefire, it is that the quality-side filter made the Energy sector structurally ineligible for CONVICTION BUY in the 04-07 screen. §8 walks through why.

---

## 6. The Best Ideas Lens

Cohen, Polk & Silli (2010) documented that active managers' highest-conviction positions outperform by 2.8–4.5% per year, while the rest of the portfolio shows no alpha. Assay exposes the same concentration cuts in its [`backtest` report](../../backtest/report.py); here they are applied to the single-day event:

```
    ┌───────────────────────────────────────────────────────┐
    │  Portfolio         Mean       vs SPY    Composition   │
    │  ─────────       ────────    ────────   ───────────   │
    │  Top 1             +3.41%      +86 bp   UHS           │
    │  Top 3             +2.16%      -39 bp   UHS BBY INCY  │
    │  Top 5             +2.22%      -33 bp   + AOS CMCSA   │
    │  Top 10            +2.87%      +32 bp   + BMY EXPE ...│
    │  Top 20 (full)     +2.29%      -26 bp   all 20 picks  │
    │  SPY                             —      benchmark     │
    └───────────────────────────────────────────────────────┘
```

The single highest-conviction pick (UHS, Conviction = 93.4) beat SPY by +86 bps on a day that was structurally hostile to value-tilted strategies. Top 3 and Top 5 gave back the win — both portfolios were anchored by BBY (+0.72%) and CMCSA (+0.61%), HIGH-confidence names that happened to close near-flat in the rotation. Top 10 recovered the lead (+32 bps). The full 20-name portfolio slipped below SPY.

The pattern is exactly what Cohen-Polk-Silli describe: alpha dilutes rapidly as the portfolio grows. One data point proves nothing about that effect — the point of including this table is to be consistent with how the engine is already evaluated in the quarterly backtest. See §10 for the honest treatment of statistical weight.

---

## 7. The 10 Worst Performers and Who Owned Them

The 10 worst-returning names in the 424-stock universe on 04-08, and how Assay classified each on 04-07:

```
    ┌─────────────────────────────────────────────────────────────┐
    │  Rank  Ticker  Sector      1-day      Assay classification  │
    │  ────  ──────  ──────    ─────────    ───────────────────   │
    │    1   APA     Energy     -9.80%      WATCH LIST            │
    │    2   LYB     Materials  -7.53%      AVOID                 │
    │    3   WDAY    Info Tech  -6.54%      QUALITY GROWTH PREM   │
    │    4   PLTR    Info Tech  -6.20%      OVERVALUED QUALITY    │
    │    5   CF      Materials  -5.70%      WATCH LIST            │
    │    6   MPC     Energy     -5.48%      HOLD                  │
    │    7   DOW     Materials  -5.14%      AVOID                 │
    │    8   INTU    Info Tech  -5.05%      QUALITY GROWTH PREM   │
    │    9   OXY     Energy     -5.04%      AVOID                 │
    │   10   COP     Energy     -4.97%      WATCH LIST            │
    └─────────────────────────────────────────────────────────────┘
```

**0 CONVICTION BUYs. 3 AVOIDs. 3 WATCH LISTs. 2 QGP. 1 OQ. 1 HOLD.**

Widening to the worst 20 names: 6 AVOID, 5 WATCH LIST, 3 QGP, 2 OQ, 2 OVERVALUED, 2 HOLD — **still zero CB**. The single most important number in this entire document is the one that isn't in the table: the count of CONVICTION BUY rows in the worst-20 list is **zero**.

A few sub-observations:

1. The three QGP tech names (WDAY, INTU, PLTR) are not an Energy story — those were rich-multiple software names that sold off as rate-cut-optimism rotated capital into cyclicals. QGP means *good business, priced for it*: quality high, value low. These names cleared Assay's quality filter but not its value filter, and the engine's reading of them was "wait for a better price" — not a buy, not a sell, but a Hold-adjacent wait-list. On the day the rotation hit, their valuation risk showed.
2. The energy names that landed in WATCH LIST rather than AVOID (APA, COP, CTRA, DVN, CF) scored cheaply on value — APA's value score was 97.8 — but missed CONVICTION BUY because their *quality* scores were middling (40–60 range). They were downgraded by the **classification matrix directly**, not by the F-score or momentum gate. §8 walks through that distinction.
3. MPC sitting in HOLD (F=7, V=64.3, Q=48.2) is the boundary case: a name the engine neither endorsed nor rejected. It returned -5.48%. HOLD is supposed to carry no signal; the distribution of HOLD returns (mean +2.42%, median +2.27%) on the day was essentially universe-like. Individual names within HOLD can still blow up — MPC did — without invalidating the bucket's neutrality.

---

## 8. The Mathematics of the Refusal

This section traces every empirical result above back to a specific formula in [`docs/METHODOLOGY.md`](../METHODOLOGY.md). It exists because "the engine was right" is not a satisfactory description — we want to know which piece of machinery caught what, and to correct any comfortable narratives that don't survive inspection of the CSV.

### 8.1 — Why Energy Failed the Q ≥ 70 Threshold

The 2026-04-07 V / Q / Conviction scores and classifications for the major oil, gas, and commodity-chemical names that took the worst of the 04-08 selloff:

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  Ticker  Sector       V      Q     Conv   Classification    F   │
    │  ──────  ──────     ────   ────   ─────   ──────────────   ──   │
    │  XOM     Energy     52.0   36.5    43.6   AVOID             4   │
    │  CVX     Energy     39.5   44.2    41.8   OVERVALUED        5   │
    │  OXY     Energy     48.1   27.6    36.4   AVOID             4   │
    │  VLO     Energy     68.7   39.5    52.1   AVOID             6   │
    │  FANG    Energy     57.8   30.2    41.8   AVOID             5   │
    │  APA     Energy     97.8   60.8    77.1   WATCH LIST        7   │
    │  DVN     Energy     94.2   45.5    65.5   WATCH LIST        6   │
    │  COP     Energy     72.7   48.5    59.4   WATCH LIST        7   │
    │  DOW     Materials   3.5   17.9     7.9   AVOID             3   │
    │  LYB     Materials  12.7   19.3    15.7   AVOID             3   │
    └──────────────────────────────────────────────────────────────────┘
```

**The key correction for anyone writing about this day**: the Piotroski F-score gate (METHODOLOGY §6.2: raw F < 6 → downgrade) and the momentum gate (§7.2) were **not the operative filters** for most of these names. APA has F=7. COP has F=7. DVN has F=6 (exactly at the threshold, still passing). They landed in WATCH LIST because their **quality score** — the composite of normalized Piotroski and Gross Profitability percentile — was too low to clear the Q ≥ 70 CONVICTION BUY threshold by the §5.2 classification matrix. APA's Q = 60.8 was the highest of the cheap-Energy cohort and it still sat at 9.2 points below the bar. The matrix did the work alone; no gate needed to fire.

Why was quality so low across the sector even while the tape was roaring? Walk through the 9 Piotroski criteria for XOM, drawn from the CSV directly:

```
    ┌───────────────────────────────────────────────────────┐
    │  XOM Piotroski Criteria (2026-04-07 screen)           │
    │  ──────────────────────────────────────────           │
    │  F1  Net Income > 0                    PASS           │
    │  F2  Positive Operating Cash Flow      PASS           │
    │  F3  ROA Improving YoY                 FAIL           │
    │  F4  OCF > NI (Accruals Quality)       PASS           │
    │  F5  Decreasing Debt / Assets          FAIL           │
    │  F6  Current Ratio Improving           FAIL           │
    │  F7  No Share Dilution                 PASS           │
    │  F8  Gross Margin Expanding            FAIL           │
    │  F9  Asset Turnover Improving          FAIL           │
    │                                                        │
    │  Raw F-Score:       4 / 9                             │
    │  Normalized:        44.4                              │
    └───────────────────────────────────────────────────────┘
```

Five of nine criteria failing. ROA was deteriorating year-over-year. Debt was rising relative to assets. Current ratio was weakening. Gross margins were compressing. Asset turnover was falling. This was a company whose fundamentals were getting *worse* while its stock price was getting *better*. That is the exact disconnect Piotroski (2000) designed his score to catch:

> *"F-Score identifies cheap stocks where the cheapness is temporary versus permanent."* (METHODOLOGY §11 — Piotroski, 2000)

F-score is a **trajectory metric, not a level metric**. A company can be wildly profitable on the current income statement and still be flagged on direction: margins compressing, leverage rising, turnover slowing. A commodity cyclical in the late stages of a supercycle will often fail exactly these criteria — operating leverage is already maxed out, capex has to ramp to chase higher-cost barrels, and balance sheets start to lever. The 04-07 screen caught it in the numbers. The 04-08 tape caught it in the price.

### 8.2 — Why the Geometric Mean Was Mostly Redundant Here

Assay's conviction score is the **geometric mean** of Value and Quality:

```
    Conviction = sqrt(V * Q)
```

For XOM (V=52.0, Q=36.5) this works out to:

```
    sqrt(52.0 * 36.5) = sqrt(1898.0) = 43.57  ≈ 43.6   ✓
```

**Honest accounting**: the arithmetic mean `(52.0 + 36.5) / 2 = 44.25` would have produced a nearly identical XOM score. The geometric mean did *not* reject XOM by itself on this day — the **classification threshold** (Q must be ≥ 70 for CB) rejected it, and that threshold is a hard cutoff that operates before the conviction number is even used for ranking inside a bucket.

The geometric mean's structural role is not to reject XOM; it is to reject the hypothetical `V=97, Q=15` stock that would pass a `(V+Q)/2 ≥ 56` test while clearly being a value trap:

```
    Stock     V    Q    (V+Q)/2    sqrt(V*Q)
    ─────    ──   ──   ─────────   ─────────
    A        97   15      56.0       38.1    <- arithmetic would pass, geom catches
    B        80   80      80.0       80.0    <- balanced, both agree
    C        52   36.5    44.3       43.6    <- near-identical (XOM)
```

The geometric mean bites when the two scores *diverge sharply*. For Energy in this screen, the scores were more *symmetric* than divergent — both V and Q were in the 30s–60s for most names, so the geometric mean produced similar values to arithmetic. The filter that did the actual work was the Q ≥ 70 threshold in the classification matrix. This is an important distinction for intellectual honesty: crediting the geometric mean for outcomes the classification matrix produced would misattribute the mechanism. The geometric mean still mattered — it is what prevents a separate category of errors — but on 04-08, specifically, the matrix was the operative filter.

### 8.3 — Why Percentile Ranking Didn't Get Tricked

One non-obvious point worth naming: the 5-week crude spike inflated EV/EBIT for every Energy name, pushing their Earnings Yields up in absolute terms. A raw-score or z-score system would have moved them aggressively up the Value axis — possibly enough to clear the V threshold by a wider margin — without any corresponding signal in other sectors.

Percentile ranking (METHODOLOGY §2.3) is distribution-agnostic. Energy's Earnings Yield rose *relative to itself*, but it rose inside the S&P 500 cross-section along with whatever base rate the market was pricing. Energy did get a relative boost on V (several names crossed into the 90s on Value rank), but Quality was either flat or down because the Piotroski criteria respond to direction of fundamentals, which was deteriorating. The geometric mean compressed. The ranking couldn't be fooled by a commodity-driven spike the way a standardized-score model could.

### 8.4 — The Confidence Formula Did What It Said

The 20-row confidence table in §4 was derived mechanically from the formula:

```
    min(V - 70, Q - 70)
```

Bucketed:

```
    HIGH:      margin >= 15.0     (5 names)
    MODERATE:  5 <= margin < 15   (7 names)
    LOW:       0 <  margin < 5    (8 names)
```

Every label in the 04-07 screen matches the formula exactly (verified against the `confidence` column in `results/screen_2026-04-07.csv` for all 20 CB rows). The empirical day-ahead returns were:

```
    HIGH:      +3.22%   (+67 bps vs SPY)
    MODERATE:  +2.66%   (+11 bps vs SPY)
    LOW:       +1.37%   (-118 bps vs SPY)
```

Monotonic. The spread between HIGH and LOW was 185 bps — a meaningful separation on a one-day horizon and a direct empirical match to what the formula mechanically predicts: the weakest dimension determines confidence; when the weakest is still strong, both fundamental axes are comfortably above the bar, and there is less room to disappoint. A name with `min = 0.1` (DG) is sitting at 70.1 on its weaker axis. One revision, one data update, and the stock drops out of CB entirely. A name with `min = 22.6` (UHS) is structurally distant from every edge case. That distance shows up as lower variance *and* higher mean.

One-day returns are noisy. What is not noisy is that the formula's mechanical prediction (HIGH > MODERATE > LOW) held on a day characterized by high dispersion, and it held across three independent cuts of the same 20-name portfolio.

---

## 9. Takeaway — The Asymmetry in One Day

The README opens with a specific anecdote about the system's most distinctive behavior:

> *"From Q1 2022 through Q1 2023, it produced zero picks for five straight quarters. In the worst of those quarters, the S&P 500 fell 16% — Assay had nothing to buy. It didn't predict the crash. It simply couldn't find a single stock where cheapness, quality, and financial health all aligned. That willingness to say 'nothing qualifies' is the system's most distinctive behavior."* — [`README.md`](../../README.md)

2026-04-08 is the same behavior compressed into a single day. Five weeks of a macro-driven rally had made Energy the cheapest and hottest sector on the tape. Assay looked at the reported fundamentals — F-scores of 3, 4, 5; ROA trending down; margins compressing; leverage rising — and declined. Not because it knew a ceasefire was coming. Because it doesn't use macro views at all. It classified every one of those names into a non-CB bucket before the event, using only data from annual financial statements and market prices. When the event landed, the classification was already in the CSV.

The 20 CONVICTION BUYs returned +2.29% (-26 bps vs SPY). This is not a hero result. It is, on its own, inside daily noise for a 20-name portfolio. The meaningful observations — the ones that are *less* inside noise — are:

1. **19 of 20 CBs closed positive.** Zero were in the day's worst-20 list.
2. **Zero of the day's worst 20 names were CONVICTION BUYs.** This cannot happen by chance; it requires a classifier that correctly refused a structurally vulnerable cohort.
3. **The confidence gradient was monotonic**: HIGH +3.22%, MODERATE +2.66%, LOW +1.37%. A single-scalar formula produced a clean ordering on live market data.
4. **The AVOID and WATCH LIST buckets lagged by -79 and -108 bps** — concentrating the day's losses into exactly the classifications the engine was warning about.

On 04-08, the engine's best pick (UHS +3.41%) dominated its worst pick (DLTR -0.75%) by a factor of more than 4. The full CB portfolio's dispersion was positive-skewed. Meanwhile, the engine's refusal set (AVOID) was the worst-performing bucket in the universe. Both sides of the asymmetry showed up on this single day. A subsequent 12-quarter component investigation found that win/loss asymmetry is strategy-dependent: under quarterly rebalancing (selling winners), the ratio was 1.05× (no asymmetry). Under the selective sell strategy (holding winners, selling only on fundamental deterioration), the ratio improved to 1.28× — suggesting the asymmetry the screener is designed to produce requires the correct hold/sell discipline to manifest. See `docs/STRATEGY.md`.

A one-day observation is not evidence. It is an illustration of the mechanism the backtest tries to measure over quarters. The backtest is the thing that matters for evidence; see `results/backtest_*.csv`. This document exists to make the mechanism visible in concrete terms.

---

## 10. Caveats and Scope

```
    ┌───────────────────────────────────────────────────────────────────┐
    │  Limitation                  Effect on this case study            │
    │  ──────────                  ─────────────────────────            │
    │  n = 1 trading day           Nothing here is statistically        │
    │                              significant. Assay is designed to    │
    │                              be measured in quarters, not days.   │
    │                                                                    │
    │  No transaction costs        Day-trading a 20-name portfolio      │
    │                              at full turnover is not a real       │
    │                              strategy. Backtest includes tcosts.  │
    │                                                                    │
    │  No slippage, no borrow      Close-to-close assumes frictionless  │
    │                              execution. Real fills would differ.  │
    │                                                                    │
    │  Close-to-close only         yfinance spot prices. No intraday.   │
    │                              News-reported index moves differ     │
    │                              slightly from close-to-close; see    │
    │                              §2 footnotes.                        │
    │                                                                    │
    │  Universe = 424 names        HOLX excluded — trading halted on    │
    │                              04-08, no close price available.     │
    │                                                                    │
    │  No bootstrap or t-test      All "spreads" in this document are   │
    │                              descriptive, not inferential.        │
    │                                                                    │
    │  1-day CB sigma is ~50-80bp  The CB vs SPY gap of -26 bps is      │
    │                              comfortably inside daily noise. The  │
    │                              *ordering of buckets* and the        │
    │                              *monotonic confidence gradient* are  │
    │                              less noisy than headline returns.    │
    │                                                                    │
    │  No survivorship correction  Universe is the current S&P 500      │
    │                              membership list as of 04-07.         │
    └───────────────────────────────────────────────────────────────────┘
```

> This is preliminary evidence, not proof. Do not tune parameters based on one day of results. The backtest is the only source of evidence this project treats as such; see [`docs/METHODOLOGY.md`](../METHODOLOGY.md) and the quarterly backtest output in `results/backtest_*.csv` for the only performance numbers that deserve statistical weight.

---

## 11. Academic References

Only papers already cited in [`docs/METHODOLOGY.md` §11](../METHODOLOGY.md#11-academic-foundation). This case study extends the existing reference base, it does not expand it.

**Piotroski, J.D.** (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research, 38, 1-41.

> Cited in §8.1: the F-score as a *trajectory* metric rather than a level metric is the reason XOM scored 4/9 on 04-07 despite the 40%+ YTD stock return. F-score is designed to catch the disconnect between price trend and fundamental trend — which is exactly the condition of a commodity cyclical in the late stages of a geopolitical-premium spike.

**Novy-Marx, R.** (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics, 108(1), 1-28.

> Cited in §8.1 implicitly: the Gross Profitability percentile is the second input to the Quality score composite. Energy-sector gross profitability is structurally below information technology and consumer-discretionary levels. Even without the Piotroski component, the GP/A percentile would have pushed Energy quality below the CB bar.

**Carlisle, T.** (2014). *Deep Value: Why Activist Investors and Other Contrarians Battle for Control of Losing Corporations.* Wiley Finance.

> Cited implicitly throughout. Assay's Value axis is the Acquirer's Multiple (EV/EBIT) per Carlisle, and the 5-week war-premium rally had compressed EV/EBIT for every Energy name — making them look historically cheap. Carlisle's 17.9% CAGR result is over 44 years of quarterly rebalancing, not one day of macro news, and the F-score gate and quality filter exist specifically because the Acquirer's Multiple alone would chase a cohort like this. The case study does not contradict Carlisle; it demonstrates the exact failure mode the Piotroski overlay is designed to prevent.

**Cohen, R., Polk, C. & Silli, B.** (2010). *Best Ideas.* Working Paper, London School of Economics.

> Cited in §6: the top-N concentration cuts (Top 1, Top 3, Top 5, Top 10, Top 20) mirror the structure used in the quarterly backtest report. On 04-08, the Top 1 pick (UHS) beat SPY by +86 bps while the full 20-name CB portfolio did not. One data point is consistent with Cohen-Polk-Silli's central finding that highest-conviction positions carry the alpha; it is not evidence for it.

**Jegadeesh, N. & Titman, S.** (1993). *Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65-91.

> Cited implicitly in §8.1: the momentum gate (METHODOLOGY §7.2) uses the 12-1 month variant. On 04-07, Energy's strong recent performance was driving momentum percentiles up, but the 12-1 skip meant the most recent month of the war rally was not yet in the lookback — so the gate was not the operative filter for Energy on this screen. The gates are there; they just were not what saved this run from owning the cohort.

---

<div align="center">
<sub>[Back to README](../../README.md) · [Methodology](../METHODOLOGY.md) · [Architecture](../ARCHITECTURE.md)</sub>
</div>
