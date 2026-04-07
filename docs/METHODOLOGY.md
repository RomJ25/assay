# Methodology

A complete mathematical specification of Assay's scoring, ranking, and classification system.

---

## Table of Contents

- [1. Philosophy](#1-philosophy)
- [2. Value Dimension](#2-value-dimension)
- [3. Quality Dimension](#3-quality-dimension)
- [4. Conviction Scoring](#4-conviction-scoring)
- [5. Classification Matrix](#5-classification-matrix)
- [6. Safety Gates](#6-safety-gates)
- [7. Supplementary Models](#7-supplementary-models)
- [8. Fallback Hierarchy](#8-fallback-hierarchy)
- [9. Academic Foundation](#9-academic-foundation)

---

## 1. Philosophy

Assay is built on a core principle: **the intersection of value and quality produces superior risk-adjusted returns.**

Buying cheap stocks alone exposes you to value traps — companies that are cheap because they *deserve* to be. Buying high-quality stocks alone means overpaying for excellence. The academic literature consistently shows that the combination dramatically outperforms either factor in isolation.

The system makes **zero forward-looking assumptions**. There are no growth estimates, no WACC calculations, no terminal values in the ranking process. Every score is derived from **reported financial data** and **market prices** — observable, auditable, reproducible.

### Design Principles

1. **Transparency over complexity** — Every formula is inspectable. No ML, no ensemble models, no opaque signals.
2. **Rank, don't predict** — Percentile rankings are robust to outliers and require no distributional assumptions.
3. **Two dimensions, not one** — A single score conflates value and quality. Keeping them separate reveals the *type* of opportunity.
4. **Geometric mean, not arithmetic** — The conviction score mathematically enforces that both dimensions must be strong.

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
- **EV** = Enterprise Value = Market Cap + Total Debt − Cash & Equivalents

This measures how much operating profit you're buying per dollar of total enterprise cost. Higher yield = cheaper stock.

**Why EBIT/EV instead of P/E?**

| Metric | Numerator | Denominator | Capital-Structure Neutral? |
|:---|:---|:---|:---:|
| P/E | Price | Net Income | No |
| EBIT/EV | Enterprise Value | Operating Income | **Yes** |

P/E is distorted by leverage, tax strategies, and one-time charges. EBIT/EV compares operating profitability against the true total cost of acquiring the business (equity + debt − cash), making it comparable across capital structures.

### 2.2 Free Cash Flow Yield

The secondary value signal confirms that reported earnings are backed by actual cash:

```
                      FCF
FCF Yield = ──────
                      EV
```

Where **FCF** = Operating Cash Flow − Capital Expenditures.

A stock can have high EBIT but low FCF if it's spending heavily on CapEx, or if working capital is consuming cash. The FCF yield serves as a reality check.

### 2.3 Percentile Ranking

Both yields are converted to **percentile ranks** across the entire S&P 500 universe:

```
                        N − rank_position
Percentile_i = ──────────────────── × 100
                            N
```

Where `N` is the total number of stocks with valid data, and `rank_position` is the stock's position when sorted from highest yield to lowest (0-indexed).

The stock with the highest yield receives percentile ≈ 100. The lowest receives percentile ≈ 0.

### 2.4 Composite Value Score

```
Value Score = 0.70 × EY_percentile + 0.30 × FCF_percentile
```

The 70/30 weighting reflects:
- Earnings yield is the primary, academically-validated signal (Carlisle)
- FCF yield is confirmatory — it catches cases where EBIT overstates economic reality
- If FCF data is unavailable, the stock defaults to the 50th percentile for that component

### 2.5 Bank Fallback

Banks and insurance companies often don't report Operating Income in a way that's comparable to industrial companies. When EBIT is missing:

```
                     1
Earnings Yield ≈ ──────   (net earnings yield from trailing P/E)
                    P/E
```

This is a reasonable approximation because financials typically have low CapEx and minimal difference between operating and net income.

---

## 3. Quality Dimension

### 3.1 Signal 1 — Piotroski F-Score

The F-Score is a checklist of **nine binary criteria** measuring profitability, leverage, liquidity, and operating efficiency. Each criterion is either passed (1) or failed (0).

#### Profitability (4 criteria)

| # | Criterion | Formula | Rationale |
|:-:|:---|:---|:---|
| F₁ | Positive Net Income | `NI₀ > 0` | Basic profitability |
| F₂ | Positive Cash Flow | `OCF₀ > 0` | Cash-generating ability |
| F₃ | Improving ROA | `NI₀/A₀ > NI₁/A₁` | Earnings momentum |
| F₄ | Accruals Quality | `OCF₀ > NI₀` | Earnings backed by cash, not accounting |

> *Subscript 0 = current year, 1 = prior year*

#### Leverage & Liquidity (3 criteria)

| # | Criterion | Formula | Rationale |
|:-:|:---|:---|:---|
| F₅ | Decreasing Leverage | `D₀/A₀ < D₁/A₁` | Reducing financial risk |
| F₆ | Improving Liquidity | `CA₀/CL₀ > CA₁/CL₁` | Better short-term solvency |
| F₇ | No Share Dilution | `Shares₀ ≤ Shares₁` | Not financing via equity issuance |

#### Operating Efficiency (2 criteria)

| # | Criterion | Formula | Rationale |
|:-:|:---|:---|:---|
| F₈ | Expanding Margins | `GP₀/Rev₀ > GP₁/Rev₁` | Pricing power or cost control |
| F₉ | Improving Turnover | `Rev₀/A₀ > Rev₁/A₁` | More efficient asset utilization |

#### Normalization

The raw F-Score (0–9) is normalized to a 0–100 scale:

```
                     raw_score
F_normalized = ─────────── × 100
                        9
```

| Raw Score | Normalized | Interpretation |
|:---------:|:----------:|:---|
| 9 | 100.0 | Perfect financial health |
| 7 | 77.8 | Strong |
| 5 | 55.6 | Borderline |
| 3 | 33.3 | Weak |
| 0 | 0.0 | Severe distress |

### 3.2 Signal 2 — Gross Profitability

Novy-Marx (2013) demonstrated that **Gross Profit / Total Assets** has predictive power for future returns equal to the book-to-market ratio — but on the *opposite* side of the value spectrum.

```
                      GP
Profitability = ──────
                       A
```

This metric captures a company's fundamental economic engine before SG&A, depreciation, and other discretionary expenses. It is then converted to a **percentile rank** across the universe, identical to the earnings yield ranking.

#### Bank Fallback

When Gross Profit is unavailable (banks, insurance):

```
                    NI
ROA Fallback = ──────
                     A
```

### 3.3 Composite Quality Score

```
Quality Score = 0.50 × F_normalized + 0.50 × Profitability_percentile
```

#### Single-Source Penalty

When only one signal is available (e.g., Piotroski score exists but profitability data is missing):

```
Quality Score = available_signal × 0.80
```

The 20% penalty prevents a single noisy signal from inflating the composite score. Without this, a stock with a perfect F-Score but no profitability data would receive Quality = 100 — the same as a stock that excels on *both* measures.

---

## 4. Conviction Scoring

### 4.1 Geometric Mean

The conviction score uses the **geometric mean** of value and quality:

```
Conviction = √(Value × Quality)
```

This is mathematically equivalent to:

```
Conviction = exp( ½ × [ln(Value) + ln(Quality)] )
```

#### Why Geometric Mean?

The arithmetic mean `(V + Q) / 2` treats the two dimensions as substitutes — a high value score can compensate for a low quality score. The geometric mean treats them as **complements** — both must be present for a high score.

**Formal property:** For any fixed sum `V + Q = S`, the geometric mean is maximized when `V = Q` and decreases as the scores diverge. This is a direct consequence of the AM-GM inequality:

```
√(V × Q) ≤ (V + Q) / 2
```

with equality only when `V = Q`.

**Practical consequence:**

```
V = 90,  Q = 10  →  Conviction = √(900)  = 30.0
V = 50,  Q = 50  →  Conviction = √(2500) = 50.0
V = 80,  Q = 80  →  Conviction = √(6400) = 80.0
V = 95,  Q = 95  →  Conviction = √(9025) = 95.0
```

The geometric mean naturally produces the behavior we want: it rewards balanced excellence and penalizes extreme imbalance.

### 4.2 Edge Cases

- If either score is `None` → Conviction = `None` (insufficient data)
- If either score is ≤ 0 → Conviction = 0 (floor at zero)
- The score is rounded to one decimal place

---

## 5. Classification Matrix

### 5.1 Threshold Definitions

```
VALUE_HIGH  = 70    (top 30% on value)
VALUE_LOW   = 40    (bottom 40% on value)
QUALITY_HIGH = 70   (top 30% on quality)
QUALITY_LOW  = 40   (bottom 40% on quality)
```

These thresholds create three tiers on each axis, producing a 3×3 matrix of 9 classifications.

### 5.2 Classification Logic

```
classify(V, Q) =
    ┌ CONVICTION BUY          if V ≥ 70 and Q ≥ 70
    │ VALUE TRAP               if V ≥ 70 and Q < 40
    │ WATCH LIST               if V ≥ 70 and 40 ≤ Q < 70
    │ QUALITY GROWTH PREMIUM   if 40 ≤ V < 70 and Q ≥ 70
    │ HOLD                     if 40 ≤ V < 70 and 40 ≤ Q < 70
    │ OVERVALUED QUALITY       if V < 40 and Q ≥ 70
    │ OVERVALUED               if V < 40 and 40 ≤ Q < 70
    │ AVOID                    if Q < 40 and V < 70
    └ INSUFFICIENT DATA        if V or Q is None
```

### 5.3 Interpretation Guide

| Classification | What It Means | Action |
|:---|:---|:---|
| **CONVICTION BUY** | Cheap *and* healthy — the intersection of value and quality | Research for purchase |
| **WATCH LIST** | Cheap but middling quality — one catalyst away from conviction | Monitor closely |
| **VALUE TRAP** | Cheap but deteriorating — the market may be right to price it low | Avoid unless you know why |
| **QUALITY GROWTH PREMIUM** | Excellent business at a fair (not bargain) price | Hold if owned; consider on dips |
| **HOLD** | Middle of the road on both dimensions | No strong signal either way |
| **OVERVALUED QUALITY** | Great business, but priced for perfection | Wait for a better entry |
| **OVERVALUED** | Neither cheap nor high quality at premium prices | Avoid |
| **AVOID** | Low quality, not compensated by cheapness | Clear stay-away |

---

## 6. Safety Gates

### 6.1 Confidence Levels

For stocks classified as CONVICTION BUY, a confidence tag indicates how far above the threshold both scores sit:

```
confidence(V, Q) =
    ┌ HIGH       if min(V − 70, Q − 70) ≥ 15   (both ≥ 85)
    │ MODERATE   if min(V − 70, Q − 70) ≥ 5    (both ≥ 75)
    └ LOW        otherwise                       (at least one barely > 70)
```

The `min()` function ensures the weakest dimension determines the confidence level. A stock scoring (95, 71) gets LOW confidence despite its stellar value score.

### 6.2 Minimum F-Score Gate

```
if classification = "CONVICTION BUY" and raw_F < 5:
    classification ← "WATCH LIST"
```

Piotroski's research found that the strongest return differential occurs at **F ≥ 5**. Stocks below this threshold may have a high composite quality score (e.g., through strong profitability) but show multiple signs of financial deterioration. The gate prevents these from receiving the highest classification.

### 6.3 Data Quality Filter

Before scoring, stocks must pass minimum data requirements:

```
has_minimum_data(stock) =
    current_price > 0
    AND revenue[0] is not None
    AND revenue[0] > 0
    AND net_income[0] is not None
```

Stocks failing this filter are excluded from ranking entirely, ensuring that percentile ranks are computed only over stocks with meaningful data.

---

## 7. Supplementary Models

These models provide **context only** — they do not affect rankings or classifications.

### 7.1 Discounted Cash Flow (DCF)

Three-scenario DCF for additional perspective:

```
                   T            FCF_T × (1 + g_terminal)       1
IV_per_share = [ Σ  PV(FCF_t) + ──────────────────────── × ────────── + Cash − Debt ] / Shares
                  t=1              WACC − g_terminal       (1+WACC)^T
```

Where:
- `T = 5` projection years
- Growth decays linearly from estimated rate toward terminal growth
- WACC via CAPM: `(E/V) × Rₑ + (D/V) × R_d × (1 − Tₐₓ)`
- Three scenarios: **Bear** (+1.5% WACC, −3% growth), **Base** (+0.5% buffer), **Bull** (no buffer, +2% growth)

> *Skipped for banks, insurance, and REITs where FCF-based valuation is inappropriate.*

### 7.2 Relative Valuation

Compares a stock's multiples against its sector median:

```
P/E Discount = (Sector Median P/E − Stock P/E) / Sector Median P/E × 100%
```

Also computes:
- EV/EBITDA relative discount
- P/S relative discount
- PEG ratio (P/E ÷ EPS growth rate)

Outliers are filtered: P/E > 100 and EV/EBITDA > 50 are excluded from sector median calculations. Sectors with fewer than 3 comparable stocks are skipped.

### 7.3 Growth Score

A 0–100 composite from four sub-scores (display only):

| Sub-Score | Weight | Components |
|:---|:---:|:---|
| Revenue Momentum | 35% | 3-year CAGR + YoY growth + acceleration |
| Profitability | 30% | Margin levels + expansion trends |
| Earnings & FCF | 20% | EPS and FCF year-over-year growth |
| PEG Attractiveness | 15% | P/E divided by growth rate |

---

## 8. Fallback Hierarchy

The system is designed to produce scores for as many stocks as possible, with graceful degradation:

| Scenario | Primary | Fallback |
|:---|:---|:---|
| No Operating Income (banks) | EBIT / EV | 1 / P·E |
| No Gross Profit (banks) | GP / Assets | NI / Assets (ROA) |
| No Enterprise Value | Yahoo's EV | Market Cap + Debt − Cash |
| No FCF data | FCF yield rank | 50th percentile default |
| Only one quality signal | 50/50 composite | Single signal × 0.80 |
| No Diluted EPS | Reported EPS | NI / Shares Outstanding |
| Negative FCF (all years) | Latest FCF | Skip DCF entirely |

---

## 9. Academic Foundation

### Primary Sources

**Carlisle, T.** (2014). *Deep Value: Why Activist Investors and Other Contrarians Battle for Control of Losing Corporations.* Wiley Finance.

> The Acquirer's Multiple (EV/EBIT) achieved a **17.9% compound annual growth rate** from 1973 to 2017, outperforming all other value metrics including P/E, P/B, and EV/EBITDA. The key insight: buying statistically cheap stocks — even those in temporary distress — works because mean reversion is one of the most powerful forces in finance.

**Piotroski, J.D.** (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research, 38, 1–41.

> Among high book-to-market (value) stocks, a simple 9-point checklist of financial health separated winners from losers by **13.4% annually** over 20 years. The F-Score works because it identifies cheap stocks where the *cheapness is temporary* (improving fundamentals) versus permanent (deteriorating business).

**Novy-Marx, R.** (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics, 108(1), 1–28.

> Gross Profitability (GP/Assets) predicts the cross-section of expected returns with the same power as book-to-market — but on the *opposite* side. Profitable firms outperform unprofitable firms. Combined with value, the two factors are "complementary": controlling for one dramatically increases the performance of the other.

### Why These Three Together

The three factors are not redundant — they capture different dimensions of a stock's attractiveness:

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   Earnings Yield ──► "Is it cheap?"                      │
│                       (price relative to fundamentals)   │
│                                                          │
│   F-Score ─────────► "Is it getting better?"             │
│                       (trajectory of financial health)   │
│                                                          │
│   Profitability ───► "Is it a good business?"            │
│                       (fundamental economic engine)      │
│                                                          │
│   Together: "Cheap + improving + good business"          │
│             = highest probability of outperformance      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

<p align="center">
  <sub><a href="../README.md">← Back to README</a></sub>
</p>
