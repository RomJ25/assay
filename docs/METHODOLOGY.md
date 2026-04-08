<div align="center">

# Methodology

**Complete mathematical specification of Assay's scoring, ranking, and classification system**

</div>

---

### Contents

[1. Philosophy](#1-philosophy) · [2. Value Dimension](#2-value-dimension) · [3. Quality Dimension](#3-quality-dimension) · [4. Conviction Scoring](#4-conviction-scoring) · [5. Classification Matrix](#5-classification-matrix) · [6. Safety Gates](#6-safety-gates) · [7. Momentum Gate](#7-momentum-gate) · [8. Trajectory Score](#8-trajectory-score) · [9. Supplementary Models](#9-supplementary-models) · [10. Fallback Hierarchy](#10-fallback-hierarchy) · [11. Academic Foundation](#11-academic-foundation)

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

Both yields are converted to **percentile ranks** across the S&P 500:

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

### 3.2 Signal 2 — Gross Profitability

Novy-Marx (2013) showed that **Gross Profit / Total Assets** has predictive power for future returns equal to the book-to-market ratio — but on the *opposite* side of the value spectrum.

```
                        Gross Profit
    Profitability  =  ──────────────
                       Total Assets
```

This captures a company's fundamental economic engine before SG&A, depreciation, and other discretionary expenses. It is then converted to a **percentile rank** across the universe, identical to the earnings yield ranking. **Negative gross profit is included** — it ranks at the bottom, not excluded.

**Bank fallback:** When Gross Profit is truly unavailable (`None`):

```
                      Net Income
    ROA Fallback  =  ────────────
                      Total Assets
```

### 3.3 Composite Quality Score

```
    Quality Score  =  0.50 × F_normalized  +  0.50 × Profitability_percentile
```

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

### 6.2 Minimum F-Score Gate

```
    if classification = "CONVICTION BUY"  and  raw_F < 6:
        classification ← "WATCH LIST"
```

Piotroski found the strongest return differential at **F ≥ 5-6**. Stocks below this may have high composite quality (through profitability) but show multiple signs of financial deterioration.

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

**Jegadeesh, N. & Titman, S.** (1993). *Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.* Journal of Finance, 48(1), 65-91.

> The foundational cross-sectional momentum paper. Stocks that performed well over the past 3-12 months continue to outperform, and vice versa. The 12-1 month variant (skip most recent month) is the most widely used in academic factor research.

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
    │                          Fundamental economic engine                  │
    │                                                                      │
    │   Momentum Gate  ────►  "Is the market catching on?"                 │
    │                          Excludes stocks the market is still dumping  │
    │                                                                      │
    │   Together:  Cheap  +  improving  +  good business  +  not falling   │
    │              = highest probability of outperformance                  │
    │                                                                      │
    └──────────────────────────────────────────────────────────────────────┘
```

---

<div align="center">

<sub>[Back to README](../README.md)</sub>

</div>
