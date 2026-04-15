<div align="center">

# Methodology

**Complete mathematical specification of Assay's scoring, ranking, and classification system**

</div>

---

### Contents

[1. Philosophy](#1-philosophy) · [2. Value Dimension](#2-value-dimension) · [3. Quality Dimension](#3-quality-dimension) (Piotroski + Profitability + Safety) · [4. Conviction Scoring](#4-conviction-scoring) · [5. Classification Matrix](#5-classification-matrix) · [6. Safety Gates](#6-safety-gates) · [7. Momentum Gate](#7-momentum-gate) · [8. Trajectory Score](#8-trajectory-score) · [9. Supplementary Models](#9-supplementary-models) · [10. Fallback Hierarchy](#10-fallback-hierarchy) · [11. Academic Foundation](#11-academic-foundation) · [12. Backtest Conventions](#12-backtest-conventions) · [13. Design Decision Log](#13-design-decision-log)

---

## 1. Philosophy

Assay is built on a core principle: **the intersection of value and quality produces superior risk-adjusted returns.**

- Buying cheap stocks alone exposes you to **value traps** — companies that are cheap because they *deserve* to be.
- Buying high-quality stocks alone means **overpaying** for excellence.
- The combination dramatically outperforms either factor in isolation.

The system makes **zero forward-looking assumptions**. No growth estimates, no WACC calculations, no terminal values in the ranking process. Every score derives from **reported financial data** and **market prices** — observable, auditable, reproducible.

### Design Principles

```
    1. Transparency over complexity     Every formula is inspectable. No ML, no black boxes.
    2. Rank, don't predict              Percentile rankings need no distributional assumptions.
    3. Two dimensions, not one          Separate axes reveal the TYPE of opportunity.
    4. Geometric mean, not arithmetic   Both dimensions must be strong. No substitutes.
```

---

## 2. Value Dimension

### 2.1 Earnings Yield

The primary value signal is **Earnings Yield** — the inverse of the Acquirer's Multiple:

```
                      EBIT
    Earnings Yield = ──────
                       EV
```

Where:
- **EBIT** = Operating Income (most recent fiscal year)
- **EV** = Enterprise Value = Market Cap + Total Debt - Cash & Equivalents

This measures how much operating profit you're buying per dollar of total enterprise cost. Higher yield = cheaper stock. **Negative EBIT is included** — a company losing money gets a negative yield and ranks at the bottom, rather than being excluded. Only truly missing EBIT (`None`) triggers the bank fallback.

**Why EBIT/EV instead of P/E:**

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  Metric       Numerator          Denominator     Cap-Structure  │
    │  ──────       ─────────          ───────────     Neutral?       │
    │  P/E          Price              Net Income      No             │
    │  EBIT/EV      Enterprise Value   Operating Inc   Yes ✓          │
    └──────────────────────────────────────────────────────────────────┘
```

P/E is distorted by leverage, tax strategies, and one-time charges. EBIT/EV compares operating profitability against the true total cost of acquiring the business, making it comparable across capital structures.

### 2.2 Free Cash Flow Yield

The secondary signal confirms that reported earnings are backed by actual cash:

```
                        FCF
    FCF Yield  =  ────────
                        EV
```

Where **FCF** = Operating Cash Flow - Capital Expenditures.

A stock can have high EBIT but low FCF if it spends heavily on CapEx or if working capital is consuming cash. The FCF yield is a reality check. **Negative FCF is ranked at the bottom**, not treated as missing. Only truly absent FCF data (`None`) defaults to the 50th percentile.

### 2.3 Percentile Ranking

Both yields are converted to **percentile ranks** across the universe (S&P 500 or Russell 1000):

```
                        N - rank_position
    Percentile_i  =  ──────────────────── × 100
                              N
```

Where `N` is the total number of stocks with valid data, and `rank_position` is the stock's position when sorted highest-to-lowest (0-indexed).

Properties of percentile ranking:
- **Outlier-robust** — a 50% yield doesn't dominate a 12% yield disproportionately
- **No distributional assumptions** — works for skewed, fat-tailed financial data
- **Cross-comparable** — Value 70 and Quality 70 both mean "top 30%"

### 2.4 Composite Value Score

```
    Value Score  =  0.70 × EY_percentile  +  0.30 × FCF_percentile
```

The 70/30 weighting reflects:
- Earnings yield is the primary, academically-validated signal (Carlisle)
- FCF yield is confirmatory — catches cases where EBIT overstates economic reality
- If FCF data is truly unavailable (`None`), the stock defaults to the **50th percentile** for that component. Negative FCF is ranked normally (at the bottom), not defaulted.

### 2.5 Bank Fallback

Banks and insurance companies often don't report Operating Income comparably. When EBIT is truly missing (`None`), not merely negative:

```
                         1
    Earnings Yield  ≈  ──────
                        P/E
```

This is reasonable because financials typically have low CapEx and minimal difference between operating and net income. A stock with negative EBIT uses the EBIT/EV path (negative yield, ranked at bottom) — it does NOT fall through to this fallback. Financials are excluded by default (`--include-financials` to override).

---

## 3. Quality Dimension

### 3.1 Signal 1 — Piotroski F-Score

Nine binary criteria measuring profitability, leverage, liquidity, and efficiency. Each is passed (1) or failed (0).

#### Profitability (4 criteria)

```
    F₁   Net Income > 0              NI₀ > 0                    Basic profitability
    F₂   Positive Cash Flow          OCF₀ > 0                   Cash-generating ability
    F₃   Improving ROA              NI₀/A₀ > NI₁/A₁            Earnings momentum (negative NI allowed)
    F₄   Accruals Quality           OCF₀ > NI₀                  Cash backs earnings
```

#### Leverage & Liquidity (3 criteria)

```
    F₅   Decreasing Leverage        D₀/A₀ < D₁/A₁              Reducing financial risk
    F₆   Improving Liquidity       CA₀/CL₀ > CA₁/CL₁           Better short-term solvency
    F₇   No Share Dilution         Shares₀ ≤ Shares₁            Not financing via equity
```

#### Operating Efficiency (2 criteria)

```
    F₈   Expanding Margins         GP₀/Rev₀ > GP₁/Rev₁         Pricing power (negative GP allowed)
    F₉   Improving Turnover        Rev₀/A₀ > Rev₁/A₁           More efficient asset use
```

> *Subscript ₀ = current year, ₁ = prior year*

#### Normalization

```
                         raw_score
    F_normalized  =  ─────────────  ×  100
                           9
```

```
    ┌──────────────────────────────────────────┐
    │  Raw Score    Normalized    Interpretation│
    │  ─────────    ──────────    ──────────────│
    │     9           100.0      Perfect health │
    │     7            77.8      Strong         │
    │     5            55.6      Borderline     │
    │     3            33.3      Weak           │
    │     0             0.0      Severe distress│
    └──────────────────────────────────────────┘
```

### 3.2 Signal 2 — Profitability

Novy-Marx (2013) showed that **Gross Profit / Total Assets** has predictive power for future returns equal to the book-to-market ratio — but on the *opposite* side of the value spectrum. Novy-Marx & Medhat (2025) further demonstrated that **(GP + R&D) / Assets** dominates plain GP/Assets over 50 years of data.

```
                        Gross Profit + R&D
    Profitability  =  ────────────────────
                           Total Assets
```

When R&D data is unavailable, falls back to `GP / Assets`. This captures a company's fundamental economic engine before SG&A, depreciation, and other discretionary expenses. The R&D add-back accounts for the fact that R&D is an investment in future profitability, not a pure expense — penalizing R&D-heavy firms (Tech, Healthcare) understates their true economic profitability.

Profitability is converted to a **percentile rank** across the universe, identical to the earnings yield ranking. **Negative gross profit is included** — it ranks at the bottom, not excluded.

**Bank fallback:** When Gross Profit is truly unavailable (`None`):

```
                      Net Income
    ROA Fallback  =  ────────────
                      Total Assets
```

### 3.3 Signal 3 — Safety

Asness, Frazzini & Pedersen (2019) showed that the safety dimension of Quality Minus Junk (QMJ) has positive crisis convexity and 55-66 bps/month alpha. Low-beta + low-leverage stocks within value have better risk-adjusted returns.

```
    Safety  =  0.50 × InverseBeta_percentile  +  0.50 × InverseLeverage_percentile
```

Where:
- **InverseBeta_percentile**: Stocks ranked by beta (ascending). Lower beta = higher safety score.
- **InverseLeverage_percentile**: Stocks ranked by Debt/Assets (ascending). Lower leverage = higher safety score.
- Missing beta (common in backtest) defaults to neutral 50th percentile.

### 3.4 Composite Quality Score

```
    Quality Score  =  0.40 × F_normalized  +  0.40 × Profitability_percentile  +  0.20 × Safety_percentile
```

The 40/40/20 weighting reflects:
- Piotroski and Profitability are the primary, most-validated quality signals (equal weight)
- Safety provides crisis convexity and drawdown reduction (lower weight — supplementary but impactful)

When safety is disabled (`SAFETY_ENABLED = False` in config), falls back to 50/50 Piotroski + Profitability.

#### Single-Source Penalty

When only one signal is available:

```
    Quality Score  =  available_signal  ×  0.80
```

The 20% penalty prevents a single noisy signal from inflating the composite. Without this, a stock with a perfect F-Score but no profitability data would receive Quality = 100, the same as a stock excelling on *both* measures.

---

## 4. Conviction Scoring

### 4.1 The Geometric Mean

```
    Conviction  =  √( Value × Quality )
```

Equivalently:

```
    Conviction  =  exp( ½ × [ ln(Value) + ln(Quality) ] )
```

#### Why geometric mean?

The arithmetic mean `(V + Q) / 2` treats the two dimensions as **substitutes** — a high value score can compensate for low quality. The geometric mean treats them as **complements** — both must be present.

**Formal property:** For any fixed sum `V + Q = S`, the geometric mean is maximized when `V = Q` and decreases as the scores diverge. This follows directly from the AM-GM inequality:

```
    √(V × Q)  ≤  (V + Q) / 2        equality iff V = Q
```

**Practical consequence:**

```
    V = 90,  Q = 10   →   √(  900)  =  30.0      severely penalized
    V = 50,  Q = 50   →   √( 2500)  =  50.0      balanced average
    V = 80,  Q = 80   →   √( 6400)  =  80.0      balanced excellence
    V = 95,  Q = 95   →   √( 9025)  =  95.0      top conviction
```

The geometric mean naturally rewards balanced excellence and penalizes extreme imbalance.

### 4.2 Edge Cases

```
    Either score is None   →   Conviction = None    (insufficient data)
    Either score is ≤ 0    →   Conviction = 0       (floor at zero)
    Result rounded to 1 decimal place
```

---

## 5. Classification Matrix

### 5.1 Thresholds

```
    VALUE_HIGH   = 70        top 30% on value
    VALUE_LOW    = 40        boundary between mid and low
    QUALITY_HIGH = 70        top 30% on quality
    QUALITY_LOW  = 40        boundary between mid and low
```

These create three tiers on each axis, producing a **3 x 3 matrix** of 9 classifications.

### 5.2 Classification Logic

```
    classify(V, Q) =
    ┌
    │  CONVICTION BUY           if V ≥ 70  and  Q ≥ 70
    │  VALUE TRAP               if V ≥ 70  and  Q < 40
    │  WATCH LIST               if V ≥ 70  and  40 ≤ Q < 70
    │  QUALITY GROWTH PREMIUM   if 40 ≤ V < 70  and  Q ≥ 70
    │  HOLD                     if 40 ≤ V < 70  and  40 ≤ Q < 70
    │  OVERVALUED QUALITY       if V < 40  and  Q ≥ 70
    │  OVERVALUED               if V < 40  and  40 ≤ Q < 70
    │  AVOID                    if Q < 40  and  V < 70
    │  INSUFFICIENT DATA        if V or Q is None
    └
```

### 5.3 Interpretation

```
    ┌────────────────────────────────────────────────────────────────────────────┐
    │  Classification             Meaning                           Action      │
    │  ──────────────             ───────                           ──────      │
    │  CONVICTION BUY             Cheap AND healthy                 Research    │
    │  WATCH LIST                 Cheap, middling quality           Monitor     │
    │  VALUE TRAP                 Cheap but deteriorating           Avoid       │
    │  QUALITY GROWTH PREMIUM     Great business, fair price        Hold / dip  │
    │  HOLD                       Middle of the road                No signal   │
    │  OVERVALUED QUALITY         Great business, priced for it     Wait        │
    │  OVERVALUED                 Neither cheap nor quality         Avoid       │
    │  AVOID                      Low quality, not compensated      Stay away   │
    └────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Safety Gates

### 6.1 Confidence Levels

For stocks classified as CONVICTION BUY:

```
    confidence(V, Q) =
    ┌
    │  HIGH        if  min(V - 70, Q - 70) ≥ 15      both ≥ 85
    │  MODERATE    if  min(V - 70, Q - 70) ≥ 5       both ≥ 75
    │  LOW         otherwise                          at least one barely > 70
    └
```

The `min()` function ensures the **weakest dimension** determines confidence. A stock scoring (95, 71) gets LOW despite its stellar value score.

> See [`docs/CASE_STUDIES/2026-04-08_ceasefire.md`](CASE_STUDIES/2026-04-08_ceasefire.md) §4 for an empirical observation of this formula producing a monotonic HIGH/MODERATE/LOW return gradient on a one-day, high-variance event.

### 6.2 Minimum F-Score Gate

```
    if classification = "CONVICTION BUY"  and  raw_F < 6:
        classification ← "WATCH LIST"
```

Piotroski's 2000 paper compared stocks with F-scores of **8-9** ("high" financial health) against F-scores of **0-1** ("low") within high book-to-market value stocks, reporting the 13.4% long-only excess return cited in §11 and a 23% long-short return differential over 1976-1996. That paper does not single out F ≥ 5-6 as a threshold; the 6-of-9 gate is a pragmatic long-only choice Assay makes to preserve meaningful quality discrimination while allowing broader investment coverage on a 500-name universe. A stock with F < 6 may still have high composite Quality via strong Gross Profitability, but the raw F-Score is showing multiple signs of financial deterioration simultaneously — the gate prevents these from being promoted to CONVICTION BUY regardless of how high the composite score looks.

### 6.3 Data Quality Filter

```
    has_minimum_data(stock) =
        current_price > 0
        AND revenue[0] is not None  and  revenue[0] > 0
        AND net_income[0] is not None
```

Stocks failing this filter are excluded entirely, ensuring percentile ranks are computed only over stocks with meaningful data.

---

## 7. Momentum Gate

### 7.1 Momentum Calculation

Based on Jegadeesh & Titman (1993): 12-month lookback, skip most recent month to avoid short-term reversal:

```
                    Price₁₁ₘ_ago  -  Price₁₂ₘ_ago
    Momentum₁₂₋₁ = ────────────────────────────────
                         Price₁₂ₘ_ago
```

### 7.2 Momentum as Negative Filter

Momentum is **not** a scoring dimension. It serves only as a negative gate:

```
    if classification = "CONVICTION BUY"  and  momentum_percentile ≤ 25:
        classification ← "WATCH LIST"
```

Research Affiliates (2024) demonstrated that excluding bottom-quartile momentum from value picks improved returns by **+2.8%/yr** over 32 years in a long-only, US large-cap universe.

---

## 8. Trajectory Score

A tie-breaker that measures fundamental improvement direction combined with price momentum. **Not used for ranking or classification** — visible as a separate column within conviction buys.

### 8.1 Fundamental Trajectory

```
    ΔROA  = NI₀/A₀ - NI₁/A₁           (requires A > 0)
    ΔGM   = GP₀/Rev₀ - GP₁/Rev₁       (requires Rev > 0)
    ΔLEV  = D₁/A₁ - D₀/A₀             (positive = deleveraging)
    ΔSHR  = -(Shares₀/Shares₁ - 1)     (positive = buybacks)

    FT  = 0.35 × p(ΔROA) + 0.25 × p(ΔGM) + 0.25 × p(ΔLEV) + 0.15 × p(ΔSHR)
```

Where `p()` denotes cross-sectional percentile rank (0-100). Missing components default to 50 (neutral).

### 8.2 Combined Trajectory

```
    Trajectory  =  0.70 × FT  +  0.30 × Momentum_percentile
```

A stock with improving ROA, expanding margins, declining debt, buybacks, AND strong price momentum scores highest. A stock deteriorating on all dimensions scores lowest.

### 8.3 Sector-Relative Scoring (Optional)

When `--sector-relative` is active, the value score blends absolute and within-sector percentile ranks:

```
    Value_blended = 0.70 × Value_absolute + 0.30 × Value_within_sector
```

Sectors with fewer than 3 stocks fall back to 100% absolute. This prevents a portfolio concentrated in one cheap sector (e.g., all energy during a commodity crash) while still rewarding the cheapest stock within any sector.

---

## 9. Supplementary Models

These models provide **context only** — they do not affect rankings or classifications.

### 9.1 Discounted Cash Flow (DCF)

Three-scenario DCF for additional perspective:

```
                       T                FCF_T × (1 + g_terminal)         1
    IV_per_share = [  Σ  PV(FCF_t)  +  ────────────────────────  ×  ──────────  +  Cash - Debt  ]  /  Shares
                      t=1                  WACC - g_terminal         (1+WACC)^T
```

Parameters:
- **T = 5** projection years
- Growth decays linearly from estimated rate toward terminal growth
- WACC via CAPM: `(E/V) × Rₑ + (D/V) × R_d × (1 - Tax)`
- Three scenarios: **Bear** (+1.5% WACC, -3% growth), **Base** (+0.5% buffer), **Bull** (no buffer, +2% growth)

> *Skipped for banks, insurance, and REITs where FCF-based valuation is inappropriate.*

### 9.2 Relative Valuation

Compares a stock's multiples against its sector median:

```
    P/E Discount  =  (Sector Median P/E - Stock P/E) / Sector Median P/E  ×  100%
```

Also computes EV/EBITDA and P/S relative discounts, plus PEG ratio. Outliers filtered: P/E > 100 and EV/EBITDA > 50 are excluded from sector medians. Sectors with < 3 comparables are skipped.

### 9.3 Growth Score

A 0-100 display-only composite:

```
    ┌────────────────────────────────────────────────────┐
    │  Component             Weight    Inputs             │
    │  ─────────             ──────    ──────             │
    │  Revenue Momentum       35%     3yr CAGR + YoY      │
    │  Profitability          30%     Margin + expansion   │
    │  Earnings & FCF         20%     EPS + FCF YoY        │
    │  PEG Attractiveness     15%     P/E ÷ growth rate    │
    └────────────────────────────────────────────────────┘
```

---

## 10. Fallback Hierarchy

The system is designed to produce scores for as many stocks as possible with graceful degradation:

```
    ┌──────────────────────────────────────────────────────────────────────┐
    │  Scenario                    Behavior                              │
    │  ────────                    ────────                              │
    │  Negative EBIT               EBIT/EV computed (negative yield,     │
    │                              ranks at bottom). NOT a fallback case.│
    │  Missing EBIT (None)         1 / P·E fallback (banks only)        │
    │  Negative Gross Profit       GP/Assets computed (negative ratio,   │
    │                              ranks at bottom). NOT excluded.       │
    │  Missing GP (None)           NI / Assets (ROA) fallback           │
    │  Negative FCF                FCF/EV computed (ranks at bottom)     │
    │  Missing FCF (None)          50th percentile default               │
    │  No Enterprise Value         MCap + Debt - Cash                    │
    │  Only one quality signal     Signal × 0.80                         │
    │  Negative FCF (all years)    Skip DCF entirely (context model)     │
    └──────────────────────────────────────────────────────────────────────┘
```

---

## 11. Academic Foundation

### Primary Sources

**Carlisle, T.** (2014). *Deep Value: Why Activist Investors and Other Contrarians Battle for Control of Losing Corporations.* Wiley Finance.

> The Acquirer's Multiple (EV/EBIT) achieved a **17.9% compound annual growth rate** from 1973 to 2017, outperforming all other value metrics including P/E, P/B, and EV/EBITDA. The key insight: buying statistically cheap stocks — even those in temporary distress — works because mean reversion is one of the most powerful forces in finance.

**Piotroski, J.D.** (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research, 38, 1-41.

> Among high book-to-market (value) stocks, a simple 9-point checklist of financial health separated winners from losers by **13.4% annually** over 20 years. The F-Score works because it identifies cheap stocks where the *cheapness is temporary* (improving fundamentals) versus permanent (deteriorating business).

**Novy-Marx, R.** (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics, 108(1), 1-28.

> Gross Profitability (GP/Assets) predicts the cross-section of expected returns with the same power as book-to-market — but on the *opposite* side. Profitable firms outperform unprofitable firms. Combined with value, the two factors are "complementary": controlling for one dramatically increases the performance of the other.

**Novy-Marx, R. & Medhat, M.** (2025). *Betting Against Quant: Examining the Factor Efficiency of Profitability Measures.* NBER Working Paper 33601.

> (GP + R&D) / Assets dominates plain GP/Assets for return prediction over 50 years. R&D expenditure is better understood as an investment in future profitability than as a current expense, and penalizing R&D-heavy firms systematically understates their economic profitability. This is the basis for Assay's R&D add-back in the profitability signal.

**Asness, C., Frazzini, A. & Pedersen, L.** (2019). *Quality Minus Junk.* Review of Accounting Studies, 24(1), 34-112.

> The safety dimension of Quality Minus Junk (low beta + low leverage) has positive crisis convexity and generates 55-66 bps/month alpha. Within value stocks, safety further improves risk-adjusted returns by reducing maximum drawdown. This is the basis for Assay's 20% safety weight in the quality composite.

**Jegadeesh, N. & Titman, S.** (1993). *Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65-91.

> The foundational cross-sectional momentum paper. Stocks that performed well over the past 3-12 months continue to outperform, and vice versa. The 12-1 month variant (skip most recent month) is the most widely used in academic factor research.

**Schwartz, M. & Hanauer, M. X.** (2024). *Formula Investing.* SSRN Working Paper 5043197.

> The first unified empirical comparison of the Piotroski F-Score, Greenblatt Magic Formula, Carlisle Acquirer's Multiple, and van Vliet-Koning Conservative Formula over the 1963-2022 U.S. sample (CRSP/Compustat, microcaps excluded, 6-month filing lag, 921 average stocks). For concentrated post-2000 portfolios of 40 stocks, the Magic Formula produced the highest raw CAGR (**15.8%**), the Conservative Formula the highest Sharpe ratio (**0.78**), and the Acquirer's Multiple the highest top-decile return in the full 60-year sample — no single formula dominated across all metrics. The paper directly validates several of Assay's architectural choices: (a) EBIT/EV as a cap-structure-neutral replacement for book-to-market, (b) the value-plus-quality combination over either factor alone, (c) quarterly rebalance with a filing-lag convention, (d) annual accounting data only, (e) exclusion of financials. It is also the canonical modern reference for Piotroski's 23% long-short spread.

### Why These Together

The factors are not redundant. They capture different dimensions of a stock's attractiveness:

```
    ┌──────────────────────────────────────────────────────────────────────┐
    │                                                                      │
    │   Earnings Yield  ───►  "Is it cheap?"                               │
    │                          Price relative to operating fundamentals     │
    │                                                                      │
    │   F-Score  ──────────►  "Is it getting better?"                      │
    │                          Trajectory of financial health               │
    │                                                                      │
    │   Profitability  ────►  "Is it a good business?"                     │
    │                          (GP + R&D) / Assets — economic engine       │
    │                                                                      │
    │   Safety  ───────────►  "Is it resilient?"                           │
    │                          Low beta + low leverage = crisis convexity   │
    │                                                                      │
    │   Momentum Gate  ────►  "Is the market catching on?"                 │
    │                          Excludes stocks the market is still dumping  │
    │                                                                      │
    │   Together:  Cheap + improving + good business + safe + not falling   │
    │              = highest probability of outperformance                  │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
```

---

## 12. Backtest Conventions

Assay's backtest applies specific implementation conventions that affect how its return numbers should be interpreted, especially in comparison to published academic backtests. This section documents each one explicitly so a user running `python main.py --backtest` can tell why the numbers might differ from a Schwartz-Hanauer (2024) style replication, and which of Assay's choices are deliberate vs. simply the best available from free data.

### 12.1 Filing Lag — 75 Days

```
    BACKTEST_FILING_LAG_DAYS = 75    # config.py
```

At each rebalance date, Assay's backtest only uses financial statements with `asOfDate ≤ rebal_date − 75 days`. The 75-day choice reflects the **SEC Form 10-K deadline for large accelerated filers** (60 days after fiscal year-end) plus a 15-day buffer for late filings.

Academic factor research (Fama & French 1993, Jensen et al. 2023, Schwartz & Hanauer 2024) uses a **180-day (6-month)** lag as a universally conservative convention. That choice is appropriate when the universe includes smaller firms with longer filing deadlines (90+ days for non-accelerated filers), or when paid databases like Compustat report accounting data with a multi-month lag relative to the SEC filing date.

For an **S&P 500-only universe** — every member is a large accelerated filer subject to the 60-day rule — a 180-day lag would force the backtest to use financial data that is **15+ months old** at each rebalance. Assay's 75-day lag gives the screener access to the most recent annual report as soon as the filing window has passed plus a small buffer.

**Trade-off**: Assay's backtest returns are **not directly comparable** to academic papers that use a 180-day lag. A 180-day lag is stricter (more conservative) and will generally produce slightly worse backtest returns because the screener is trading on older data. Users who want strict academic comparability can modify `BACKTEST_FILING_LAG_DAYS` in `config.py`.

### 12.2 Survivorship Bias

Assay's backtest defaults to **survivorship-free mode** (`--survivorship-free`, now the default), which uses point-in-time constituent lists from `sp500_historical.py` — the actual S&P 500 membership at each rebalance date, reconstructed from historical addition/removal records.

```
    survivorship_free=True  (default)  →  point-in-time constituents per quarter
    --survivorship-naive               →  current membership replayed backward (biased)
```

**Why this matters:** An adversarial audit (April 2026) found that the entire reported selection alpha (+2.2%/yr) under the naive (current-list) mode was attributable to survivorship bias — primarily SMCI, which was included in the Q4 2023 backtest despite not being added to the S&P 500 until March 2024. Correcting for SMCI alone flipped selection alpha from +2.2%/yr to −1.5%/yr.

The `--survivorship-naive` flag is retained for comparison but is no longer the default. For universes without historical membership data (e.g., Russell 1000), survivorship bias remains a known limitation.

### 12.3 Equal-Weight Portfolio Construction

```
    def _compute_equal_weight_return(tickers, ...):
        returns = [return_for(t) for t in tickers]
        return sum(returns) / len(returns)
```

Assay computes equal-weighted returns from the CONVICTION BUY tickers each quarter. Academic factor research (Schwartz-Hanauer 2024, Jensen et al. 2023b) typically reports **capped value-weighted** returns — weighted by market capitalization, then capped at the 80th percentile of NYSE market cap to prevent a single mega-cap from dominating the portfolio.

Equal-weighting is **appropriate for individual investors** holding a small number of positions — nobody buys $10M of AAPL just because it's bigger than WMT. It also avoids the complexity of point-in-time market-cap reweighting.

**Trade-off**: Equal-weighted backtest returns have slightly more exposure to smaller names in the universe. This is a deliberate design choice for the individual-investor use case, not an oversight.

### 12.4 Quarterly Rebalance on Calendar Quarter-Ends

```
    BACKTEST_QUARTERS = [(3, 31), (6, 30), (9, 30), (12, 31)]    # config.py
```

Rebalance dates are the **last trading day of March, June, September, and December**, matching Schwartz-Hanauer 2024 and standard academic convention. The screen is run at market close on the rebalance date and the portfolio is assumed to re-weight instantaneously at that price — no slippage, no overnight gap, no intra-quarter adjustments.

**Transaction costs**: The default is `TCOST_BPS_ROUNDTRIP = 10` (10 basis points per rebalance round-trip), consistent with Frazzini, Israel & Moskowitz (JFE) estimates for S&P 500 names. At ~50-60% quarterly turnover, this deducts approximately 0.5-0.7%/yr from CAGR. Users can override with `--tcost-bps`.

### 12.5 Benchmark Universe — Two Benchmarks, Two Questions

The backtest reports two benchmarks side by side:

- **SPY** — the S&P 500 ETF, used as the standard market benchmark. Familiar to users.
- **Equal-weighted universe** — every stock that successfully scored on that rebalance date (i.e., had enough data to receive both a value and quality score). Excludes INSUFFICIENT DATA.

These answer **different questions**. Assay-vs-SPY measures whether the strategy beats the most familiar index-fund alternative. Assay-vs-universe-EW measures **selection alpha** — whether Assay's pick logic outperforms random equal-weighted selection from the same data-available pool, controlling for survivorship and data availability. The latter is the more meaningful test of the classifier itself; the former is the more meaningful comparison for a retail investor deciding whether to follow Assay's picks instead of holding SPY.

### 12.6 Piotroski Implementation Deviations from the Modern Academic Reproduction

Assay's Piotroski F-Score matches the 2000 paper exactly on **5 of 9 criteria** (F1 Net Income > 0, F2 Operating Cash Flow > 0, F4 Accruals, F6 Current Ratio, F8 Gross Margin). Four criteria have minor convention differences from the Jensen et al. (2023a) / Schwartz-Hanauer (2024) modern reproduction:

```
    ┌───────────────────────────────────────────────────────────────────┐
    │  Criterion  Assay                   Academic standard             │
    │  ────────   ─────                   ─────────────────             │
    │  F3 ΔROA    end-of-year assets      beginning-of-year assets      │
    │  F5 ΔLEV    total_debt, strict <    LT_debt, ≤ ("did not rise")   │
    │  F7 EQIS    shares_out ≤ prior yr   Compustat EQIS field          │
    │  F9 ΔTURN   end-of-year assets      beginning-of-year assets      │
    └───────────────────────────────────────────────────────────────────┘
```

- **F3 and F9 (denominator convention)**: Assay uses end-of-year total assets; Jensen et al. 2023a uses beginning-of-year (= prior-year ending) assets. Both conventions detect the same trend direction for stable companies. Fixing to the academic convention would require extending `FinancialData` balance-sheet depth from 2 to 3 years.
- **F5 (leverage)**: Assay uses `TotalDebt` (Yahoo's combined long-term + short-term debt field) and a strict `<` comparison. The academic reproduction uses long-term debt specifically and `≤` ("did not increase"). For S&P 500 large-caps, long-term debt is typically 85-95% of total debt, so the practical impact is small. Assay's strict `<` matches Piotroski 2000's original "fell" language.
- **F7 (no share dilution)**: Assay uses `shares_outstanding ≤ prior year` as a proxy. The academic reproduction uses Compustat's explicit EQIS (equity issuance) field. Yahoo does not expose EQIS; the shares proxy is the best available from free data. Buybacks can occasionally offset dilution in the proxy.

**These deviations are documented for transparency, not flagged as errors.** They are alternative conventions present in the broader Piotroski literature, not implementation bugs. Fixing them to match the modern academic reproduction would require data-layer refactors (a 3rd year of balance sheet, a long-term debt field) and would change historical F-scores for some stocks — with no clear evidence of producing a better strategy on S&P 500 large-caps.

### 12.7 Sample-Size Disclaimer

The default backtest covers 4 years (16 quarters). Academic factor research uses 20-60 year samples (80+ quarters minimum). Assay's backtest report explicitly warns when the sample is below 30 quarters (`backtest/report.py:129`).

**All CAGR, Sharpe, and excess-return numbers from a short backtest should be treated as illustrative, not inferential.** The four-year sample spans at most one bear market and one recovery cycle and is too small for any statistical claim about factor performance. The backtest's main value at this sample size is validating that the pipeline runs without look-ahead bias, not estimating expected returns.

---

## 13. Design Decision Log

Every deviation, alternative convention, and rejected change documented in this methodology is logged in a permanent decision register at [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md). That file records *what was considered, what was decided, and why*, so future audits of the algorithm do not re-litigate settled questions from scratch. The register is organized by status (**kept**, **rejected**, **deferred**, **known deviations**) rather than by pipeline stage, because the question a future reader is almost always asking is "has this been considered before?" rather than "what does this scorer do?"

If you are reading this document to evaluate whether a specific change to the algorithm would be an improvement, start there first — the answer may already be on the books.

---

<div align="center">

<sub>[Back to README](../README.md) · [Design Decisions](DESIGN_DECISIONS.md)</sub>

</div>
