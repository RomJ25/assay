# Assay Portfolio Doctor — Sample Report

_Generated 2026-04-26 from S&P 500 snapshot dated 2026-04-26 (prior baseline: 2026-04-05)_

> **Public-data review tool. Not personalized financial advice.** Review flags, not buy/sell recommendations. Minimum 3–5 year horizon. Selection alpha unproven; this report organizes evidence — it does not forecast returns.

## 1. Executive summary

- **Reviewed:** 10 tickers
- **Sell-review flags:** 3
- **Monitor flags:** 6
- **Data-quality warnings:** 8
- **No-action holdings:** 1

> _Important: these are research-review flags, not buy/sell recommendations._

## 2. What this report won't tell you

- **It will not predict returns.** Empirical testing on this system shows selection alpha is unproven and too fragile to sell as a forecast — see the Bonferroni framework in `docs/DESIGN_DECISIONS.md`.
- **It will not tell you to buy or sell.** Every flag in this report is a *review* trigger, not an action.
- **It will not factor in your personal situation.** Tax basis, holding period, concentration, time horizon, liquidity needs — all yours to weigh.
- **It will not tell you the bull case.** The system is structurally biased toward skepticism; the bull case is yours to build.
- **It will not replace reading the 10-K.** The screen organizes public evidence; it does not understand the business.

## 3. Holdings requiring review

| Ticker | Review state | Severity | Primary reason | Data quality | Next research action |
|---|---|---|---|---|---|
| **AAPL** | Monitor | 🟡 medium | OVERVALUED QUALITY — mixed evidence, no all-clear | 🟡 yellow | Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters. |
| **MSFT** | Monitor | 🟡 medium | OVERVALUED — V low while Q mid | 🟡 yellow | Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters. |
| **GOOGL** | Monitor | 🟡 medium | OVERVALUED QUALITY — mixed evidence, no all-clear | 🟡 yellow | Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters. |
| **JNJ** | Sell Review | 🟡 medium | low absolute Piotroski F-score (F=3/9) | 🟡 yellow | Pull the Piotroski breakdown: which 3+ criteria are failing? Focus on profitability and accrual quality. |
| **INTC** | Monitor | 🟡 medium | OVERVALUED — V low while Q mid; thesis review date (2026-04-01) is past | 🟡 yellow | Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters. |
| **DIS** | Monitor | 🟡 medium | WATCH LIST — mixed evidence, no all-clear | 🟡 yellow | Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters. |
| **PYPL** | Sell Review | 🟡 medium | new gate fired this quarter (momentum_gate_fired) | 🟡 yellow | Re-examine the original thesis. What changed materially since purchase? |
| **TGT** | Monitor | ⚪ low | WATCH LIST — mixed evidence, no all-clear | 🟢 green | Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters. |
| **NVDA** | Sell Review | 🟡 medium | low absolute Piotroski F-score (F=4/9) | 🟢 green | Pull the Piotroski breakdown: which 3+ criteria are failing? Focus on profitability and accrual quality. |

## 4. What changed since prior screen

_Compared 2026-04-26 (current) vs. 2026-04-05 (prior). At a 21-day window, deltas are small by design — the format is what's being demonstrated. Real value compounds over true quarterly cadence (next 10-K cycle)._

### AAPL
- value_score: 27.1 → 29.6
- quality_score: 91.2 → 83.1
- conviction_score: 49.7 → 49.6

### MSFT
- Classification: **QUALITY GROWTH PREMIUM** → **OVERVALUED**
- value_score: 44.7 → 39.3
- quality_score: 68.5 → 64.1
- conviction_score: 55.3 → 50.2
- piotroski_f: 6 → 5

### GOOGL
- value_score: 27.3 → 24.8
- quality_score: 74.2 → 74.1
- conviction_score: 45.0 → 42.9

### JNJ
- value_score: 42.1 → 51.5
- quality_score: 57.8 → 59.4
- conviction_score: 49.3 → 55.3
- piotroski_f: 4 → 3

### INTC
- Classification: **INSUFFICIENT DATA** → **OVERVALUED**
- value_score: None → 4.0
- quality_score: 33.7 → 45.6
- conviction_score: None → 13.5
- piotroski_f: 5 → 6

### DIS
- Classification: **RESEARCH CANDIDATE** → **WATCH LIST**
- value_score: 73.9 → 74.6
- quality_score: 63.7 → 57.4
- conviction_score: 68.6 → 65.4

### PYPL
- Classification: **RESEARCH CANDIDATE** → **WATCH LIST**
- Gate newly fired: `momentum_gate_fired`
- value_score: 98.6 → 99.0
- quality_score: 71.6 → 70.5
- conviction_score: 84.0 → 83.5

### TGT
- Classification: **RESEARCH CANDIDATE** → **WATCH LIST**
- value_score: 75.5 → 77.4
- quality_score: 78.5 → 69.6
- conviction_score: 77.0 → 73.4

### NVDA
- Classification: **OVERVALUED QUALITY** → **OVERVALUED**
- value_score: 18.3 → 20.5
- quality_score: 71.1 → 66.8
- conviction_score: 36.1 → 37.0

### CMCSA
- value_score: 95.7 → 97.5
- quality_score: 80.8 → 71.8
- conviction_score: 87.9 → 83.7


## 5. Per-ticker evidence scorecard

### AAPL — Apple Inc.

- **Sector:** Information Technology  |  **Position:** holding  |  **Classification:** **OVERVALUED QUALITY**
- **Thesis as written:** _High-quality ecosystem compounder; services margin expansion_
- **Value score:** 29.6  |  **Quality score:** 83.1  |  **Conviction:** 49.6
- **Piotroski F:** 8/9  |  **Gross profitability:** 0.64
- **Earnings yield:** 3.3%  |  **FCF yield:** 2.5%  |  **P/E:** 34.4  |  **12m momentum:** 20.0%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 208 days old (>95d threshold)

**Bear case:**
- Quality is excellent (Q=83.1, F=8/9, GP=0.64) — the ecosystem-compounder thesis is intact on the screen's terms. **The risk is the price, not the business.** P/E 34.4 with FCF yield 2.5% prices in continued services growth and hardware refresh durability. Any meaningful slip in either compresses the multiple before it compresses earnings.
- Quality score dropped 91.2 → 83.1 over the prior 21 days (see §4). That is a non-trivial slip in a name positioned as 'high quality.' Identify which Q component fell — leverage, accrual quality, or operating efficiency.
- 208-day fiscal age is the highest in the portfolio. Apple's fiscal year ends late September, so the screen is using FY2024 data for FY2026-Q2 decision-making. The next 10-K materially repaints the picture.
- Services margin expansion is the thesis's load-bearing assumption. The DOJ App Store rulings, EU DMA enforcement, and Google search-default revenue (a meaningful slice of Services) are all overhangs the financial statements have not yet quantified.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### MSFT — Microsoft

- **Sector:** Information Technology  |  **Position:** holding  |  **Classification:** **OVERVALUED**
- **Thesis as written:** _Cloud + AI operating leverage; durable enterprise franchise_
- **Value score:** 39.3  |  **Quality score:** 64.1  |  **Conviction:** 50.2
- **Piotroski F:** 5/9  |  **Gross profitability:** 0.37
- **Earnings yield:** 4.0%  |  **FCF yield:** 2.2%  |  **P/E:** 26.6  |  **12m momentum:** -5.6%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 300 days old (>95d threshold)

**Bear case:**
- Classification flipped from QUALITY GROWTH PREMIUM → OVERVALUED in the prior 21-day window (see §4). F-score also dropped 6 → 5. Two simultaneous quality signals weakened. The thesis describes 'operating leverage'; recent fundamentals describe operating *deleverage* from AI capex.
- AI capex compression: the operating-leverage thesis assumes Azure AI revenue growth outpaces capex amortization. That trade-off has not yet shown in the financials and may not for several quarters. F=5 with deteriorating Q is exactly the pattern you'd see if capex is rising faster than revenue is converting.
- 12m momentum −5.6% says the market is pricing this skepticism even as the headline narrative remains positive. When momentum and quality both turn against a name, it is rarely a buying opportunity until at least one stabilizes.
- 300-day fiscal age is the longest in the portfolio. Microsoft's FY ends in June; the screen is using FY2025 fundamentals well into FY2026. The most recent 10-Q (not yet incorporated) is the one that matters for the AI-capex question.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### GOOGL — Alphabet Inc. (Class A)

- **Sector:** Communication Services  |  **Position:** holding  |  **Classification:** **OVERVALUED QUALITY**
- **Thesis as written:** _Search moat + cloud upside despite ad-cyclicality risk_
- **Value score:** 24.8  |  **Quality score:** 74.1  |  **Conviction:** 42.9
- **Piotroski F:** 6/9  |  **Gross profitability:** 0.51
- **Earnings yield:** 3.1%  |  **FCF yield:** 1.8%  |  **P/E:** 31.9  |  **12m momentum:** 81.7%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 116 days old (>95d threshold)

**Bear case:**
- Quality is solid (Q=74.1, F=6/9, GP=0.51) but value is bottom-quartile (V=24.8). The thesis acknowledges 'ad-cyclicality risk'; the screen is also pricing in moat *durability* risk via the lowest FCF yield (1.8%) of any name in the portfolio's holding sleeve.
- 12m momentum +81.7% has done the work the financials are catching up to. The cloud-upside leg of the thesis is partly priced; what isn't yet priced is the ad-revenue impact of generative-search alternatives (ChatGPT, Perplexity, Claude) eroding query share at the margin.
- DOJ search-monopoly remedies remain in motion and are not reflected in any of the screen's quality components. A forced separation of Chrome / Android default-search payments to Apple would compress the highest-margin query-distribution moat.
- F-score didn't drop in the prior window (see §4), but the value score slipped 27.3 → 24.8. The pattern is 'quality stable, market more expensive' — i.e., multiple expansion did the work, not fundamental improvement.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### JNJ — Johnson & Johnson

- **Sector:** Health Care  |  **Position:** holding  |  **Classification:** **HOLD**
- **Thesis as written:** _Defensive healthcare cash machine; consumer-spinoff completed_
- **Value score:** 51.5  |  **Quality score:** 59.4  |  **Conviction:** 55.3
- **Piotroski F:** 3/9  |  **Gross profitability:** 0.39
- **Earnings yield:** 4.4%  |  **FCF yield:** 3.3%  |  **P/E:** 26.4  |  **12m momentum:** 60.7%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 116 days old (>95d threshold)

**Bear case:**
- Piotroski F=3/9 is the headline finding for a name positioned in the thesis as a 'defensive cash machine.' Six of nine accounting criteria are failing — meaning the post-Kenvue financial profile no longer looks like the cash machine it did pre-spinoff. The bull narrative depends on margin and ROA stability; the F-score says both are weakening on a year-over-year comparison.
- F-score dropped 4 → 3 between the prior screen and this one (see §4). One additional criterion failed in the latest filing. Identify which: F=3 with positive 12m momentum (+60.7%) implies the market is pricing in optimism the financial trend doesn't yet support.
- The HOLD classification (V=51.5, Q=59.4) means this is no longer a 'buy at a discount' story — it's a 'do I keep holding through deterioration?' story. The defensive thesis only works if quality stabilizes before earnings catch the deterioration.
- Talc/Tylenol litigation reserves and pharma pipeline gaps are exogenous tail risks not captured in F-score. Re-read the latest 10-Q litigation disclosures before sizing decisions.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### INTC — Intel

- **Sector:** Information Technology  |  **Position:** holding  |  **Classification:** **OVERVALUED**
- **Thesis as written:** _Foundry turnaround optionality; bought as deep value_
- **Value score:** 4.0  |  **Quality score:** 45.6  |  **Conviction:** 13.5
- **Piotroski F:** 6/9  |  **Gross profitability:** 0.15
- **Earnings yield:** -0.0%  |  **FCF yield:** -1.1%  |  **P/E:** —  |  **12m momentum:** 119.6%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 116 days old (>95d threshold)

**Bear case:**
- The thesis says 'deep value.' The screen says V=4.0 — the **2nd percentile** of the 425-stock universe on value. That is not deep value; that is no value. The earnings yield is negative (−0.0%, rounding hides the sign), FCF yield is −1.1%, P/E is undefined because earnings flipped negative. There is no fundamental anchor under the share price right now.
- 12-month momentum +120% has done all the heavy lifting. The market priced in foundry-turnaround optionality faster than the financials can validate it. If Intel 18A yields, customer wins, or the IFS spin-off drag for one quarter, the +120% becomes the downside.
- Gross profitability of 0.15 is bottom-quartile for a semiconductor name — even before turnaround capex. The foundry build is structurally negative for near-term GP (high depreciation, low utilization), and Q (return on assets, leverage, accruals) reflects this.
- The thesis review date (2026-04-01) is past per the portfolio CSV — and the classification has weakened from INSUFFICIENT DATA to OVERVALUED in the most recent 21 days (see §4). Re-write the thesis: what concrete milestone (process node yield, foundry customer, FCF positive) would change your view?
- Foundry capex is not yet self-funding. The thesis only resolves favorably if either (a) external customers fund the investment cycle or (b) the rest of the business stabilizes enough to absorb it. Neither has occurred in the most recent filings.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### DIS — Walt Disney Company (The)

- **Sector:** Communication Services  |  **Position:** watchlist  |  **Classification:** **WATCH LIST**
- **Thesis as written:** _Streaming margin recovery candidate post-restructuring_
- **Value score:** 74.6  |  **Quality score:** 57.4  |  **Conviction:** 65.4
- **Piotroski F:** 8/9  |  **Gross profitability:** 0.18
- **Earnings yield:** 6.1%  |  **FCF yield:** 4.4%  |  **P/E:** 15.1  |  **12m momentum:** 7.1%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 208 days old (>95d threshold)

**Bear case:**
- Lost RESEARCH CANDIDATE status this quarter (CB → WATCH LIST). Quality dropped 63.7 → 57.4 across 21 days — that's a meaningful deterioration on a name where the entire thesis is 'quality recovers.' If the recovery is happening, this snapshot does not show it.
- Gross profitability 0.18 is bottom-decile; F=8/9 says the *direction* of accounting metrics is improving (most year-over-year comparisons cleared) but the *level* remains weak. Direction-without-level is fragile: one bad linear-TV quarter or one expensive content slate can flip several Piotroski criteria back to fail.
- Streaming 'margin recovery' depends on three things simultaneously: (1) DTC revenue growth holding, (2) content amortization stabilizing, (3) linear TV declining no faster than DTC grows. The screen captures (3) imperfectly; (1) and (2) won't be visible until the next 10-Q.
- 208-day fiscal age — Disney's FY ends late September, so the screen is reading FY2024 fundamentals. Any post-Iger-return strategic shifts in studios, parks pricing, or sports rights are not in the data yet.
- Parks/Experiences cyclicality is the largest unscored risk. Secular consumer-spending pullback would compress the segment carrying the bulk of operating profit.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### PYPL — PayPal

- **Sector:** Financials  |  **Position:** watchlist  |  **Classification:** **WATCH LIST**
- **Thesis as written:** _Cheap if branded-checkout durability holds_
- **Value score:** 99.0  |  **Quality score:** 70.5  |  **Conviction:** 83.5
- **Piotroski F:** 9/9  |  **Gross profitability:** 0.23
- **Earnings yield:** 13.2%  |  **FCF yield:** 11.5%  |  **P/E:** 9.3  |  **12m momentum:** -30.9%
- **Gates fired:** momentum gate
- **Data quality:** 🟡 yellow — latest annual filing is 116 days old (>95d threshold)

**Bear case:**
- This is the cleanest 'cheap-and-good but unloved' reading the system can produce: V=99, Q=70.5, F=9/9, P/E 9.3, FCF yield 11.5%. **And the system flagged it WATCH LIST anyway** because the momentum gate fired. That gate exists precisely for cases like this — when the market is selling a fundamentally clean name, it usually knows something the financial statements haven't yet caught.
- 12-month total return of −30.9% with F=9/9 is rare, and historically those divergences split: roughly half resolve in favor of the fundamentals, half resolve in favor of the price action. The empirical edge in either direction is small. Don't treat the V=99/F=9 combination as a 'discount waiting to be revealed.'
- The branded-checkout thesis (per the portfolio note) is the single load-bearing assumption. Apple Pay, Stripe-embedded checkout, Shopify Pay, and Klarna's checkout all encroach on the take-rate. If branded-checkout TPV growth slows below 3–5%/yr, the FCF yield evaporates as the multiple compresses on a now-no-growth name.
- The momentum-gate firing in this 21-day window (see §4) is a *new* signal; the prior screen had this name as a RESEARCH CANDIDATE. The gate caught the deterioration in real time — a working example of why the system flags rather than recommends.
- Yellow data quality (116-day fiscal age) means scoring uses last fiscal year-end fundamentals; the next 10-Q will likely move all four quality components. Re-screen after the next filing before any sizing decision.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Verify primary-source filing date and refresh fundamentals if stale
- [ ] Compare current evidence against the thesis as written at purchase

### TGT — Target Corporation

- **Sector:** Consumer Staples  |  **Position:** watchlist  |  **Classification:** **WATCH LIST**
- **Thesis as written:** _Mean-reversion candidate post-margin compression_
- **Value score:** 77.4  |  **Quality score:** 69.6  |  **Conviction:** 73.4
- **Piotroski F:** 6/9  |  **Gross profitability:** 0.49
- **Earnings yield:** 7.0%  |  **FCF yield:** 3.9%  |  **P/E:** 15.9  |  **12m momentum:** 31.1%
- **Gates fired:** none
- **Data quality:** 🟢 green

**Bear case:**
- Lost RESEARCH CANDIDATE status this quarter (CB → WATCH LIST). Quality dropped 78.5 → 69.6 — nearly 9 points in 21 days. **Green data quality means we trust this read.** Whatever margin pressure is in the most recent filing is real, not a snapshot artifact.
- The thesis is 'mean reversion post-margin compression.' The screen is now saying margins are still compressing, not reverting. F-score didn't change but Quality slipped — typically that means working-capital or operating-efficiency components are weakening even when the binary criteria (positive earnings, positive cash flow) still pass.
- Consumer-staples sector context: the price-conscious consumer migration to Walmart in 2023–2025 was the original cause of TGT's margin compression. The screen has no signal that that migration has reversed. Re-confirm the thesis premise before sizing.
- V=77.4 (top-quartile value) means the stock is already cheap on conventional metrics. Cheap-and-getting-cheaper resolves only when the margin trend turns. Watch for two consecutive quarters of GP/EBIT margin expansion before treating the mean-reversion thesis as live.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Compare current evidence against the thesis as written at purchase

### NVDA — Nvidia

- **Sector:** Information Technology  |  **Position:** holding  |  **Classification:** **OVERVALUED**
- **Thesis as written:** _AI compute leader at premium valuation_
- **Value score:** 20.5  |  **Quality score:** 66.8  |  **Conviction:** 37.0
- **Piotroski F:** 4/9  |  **Gross profitability:** 0.83
- **Earnings yield:** 2.6%  |  **FCF yield:** 1.9%  |  **P/E:** 42.6  |  **12m momentum:** 60.2%
- **Gates fired:** none
- **Data quality:** 🟢 green

**Bear case:**
- The headline divergence: gross profitability is exceptional (0.83 — a top-decile signal of moat), yet Piotroski F=4/9. Five accounting criteria are failing despite the moat. That gap usually means working-capital growth, accruals, or dilution is eating into the cash-flow quality the gross margin would otherwise imply.
- Valuation has no margin for error: P/E 42.6, FCF yield 1.9%, earnings yield 2.6%. The thesis explicitly accepts 'premium valuation' — but that thesis only survives if growth keeps compounding at hyperscaler-capex rates. Any 1–2 quarters of decel and the multiple compresses sharply.
- 12m momentum +60% reflects the recent run; the OVERVALUED classification (V=20.5) reflects the bill that has come due. Both can be true. The question is which signal you weight when sizing.
- Customer concentration: roughly half of data-center revenue ties to a handful of hyperscalers. Their capex cycles are not yet known to be steady-state. A capex air-pocket would compress revenue growth and EPS simultaneously.
- The classification flipped from OVERVALUED QUALITY → OVERVALUED in the prior 21-day window (see §4). Quality slipped a tier while value stayed compressed — a directional signal worth watching for two more quarters.

**Before any action, verify:**
- [ ] Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)
- [ ] Check share-count trend (dilution offset to fundamental gains)
- [ ] Confirm whether free cash flow weakness is temporary or structural
- [ ] Compare current evidence against the thesis as written at purchase

### CMCSA — Comcast

- **Sector:** Communication Services  |  **Position:** holding  |  **Classification:** **RESEARCH CANDIDATE**
- **Thesis as written:** _Broadband moat + media optionality at low-double-digit P/E_
- **Value score:** 97.5  |  **Quality score:** 71.8  |  **Conviction:** 83.7
- **Piotroski F:** 8/9  |  **Gross profitability:** 0.33
- **Earnings yield:** 11.2%  |  **FCF yield:** 10.5%  |  **P/E:** 5.4  |  **12m momentum:** -7.6%
- **Gates fired:** none
- **Data quality:** 🟡 yellow — latest annual filing is 116 days old (>95d threshold)

**Bear case:**
- This is the cleanest name in the portfolio on the screen's terms (V=97.5, Q=71.8, F=8/9, P/E 5.4) — but 'cleanest on screen' and 'best forward return' are not the same statement. The empirical work in `docs/DESIGN_DECISIONS.md` shows ranking within RESEARCH CANDIDATE has Kendall τ ≈ −0.04 with subsequent returns. Treat the high score as evidence that nothing is currently broken, not as a forecast.
- Negative 12m momentum (−7.6%) is the market's tell. The fundamentals look pristine; the price is drifting lower. That divergence resolves either through fundamental catch-up (good for holders) or through fundamental break-down (bad). The system can't tell you which.
- Cable broadband subscribers: net adds turned negative in 2024 industry-wide as fiber overbuild and fixed-wireless access penetrated suburban markets. Comcast's broadband moat depends on either (a) faster DOCSIS deployment to defend share or (b) revenue-per-user growth offsetting unit decline. The current GP of 0.33 cannot widen if competitive pricing intensifies.
- Media (NBCUniversal, Peacock) is the optionality leg of the thesis. Streaming margins remain thin sector-wide; cord-cutting compresses the linear advertising base every quarter. The thesis assumes media is 'optionality' — re-confirm that the market is not pricing in negative optionality.
- Yellow data quality from 116-day fiscal age means the broadband-trend update from the most recent 10-Q is not yet captured. Re-screen after the next filing before sizing.

## 6. Data-quality warnings

- **AAPL** (🟡 yellow): latest annual filing is 208 days old (>95d threshold)
- **MSFT** (🟡 yellow): latest annual filing is 300 days old (>95d threshold)
- **GOOGL** (🟡 yellow): latest annual filing is 116 days old (>95d threshold)
- **JNJ** (🟡 yellow): latest annual filing is 116 days old (>95d threshold)
- **INTC** (🟡 yellow): latest annual filing is 116 days old (>95d threshold)
- **DIS** (🟡 yellow): latest annual filing is 208 days old (>95d threshold)
- **PYPL** (🟡 yellow): latest annual filing is 116 days old (>95d threshold)
- **CMCSA** (🟡 yellow): latest annual filing is 116 days old (>95d threshold)

## 7. Decision journal prompt

For each flagged holding, write one paragraph answering:

- Why do I own (or watch) this company?
- What evidence would make me change my mind?
- What changed since my original thesis?
- Am I reacting to price movement or business evidence?
- What is the next filing or event that matters?
- Have I read the bear case fairly, or am I dismissing it?

---

_Sample artifact for the Assay Portfolio Doctor. Reviews public evidence; does not predict returns. Reviewed in conjunction with primary filings and the investor's own thesis. Not personalized financial advice._
