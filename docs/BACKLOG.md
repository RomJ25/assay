# Backlog

**Research and development items for future investigation. Each item needs empirical validation before implementation.**

---

## 1. Sell Strategy — When to Exit Positions

**Priority:** HIGH — The screener tells you what to buy but nothing about when to sell. This is half the strategy missing.

**Preliminary findings (n=50 dropped stocks, 10 quarters):**
- Stocks that DROP from CB return +5.2% on average the next quarter — dropping from CB is NOT a sell signal
- Stocks that move to QUALITY GROWTH PREMIUM (price appreciated): +9.8% — NEVER sell these
- Stocks that move to WATCH LIST (still close): +5.7% — hold
- Stocks that move to HOLD or AVOID (genuine deterioration): -25.0% — SELL
- Value drop (price went up): +9.8% avg — selling winners destroys value
- Quality drop (fundamentals weakened): -3.0% avg — THIS is the real sell signal

**Hypothesis to validate:**
- SELL on VALUE TRAP, AVOID, OVERVALUED, or INSUFFICIENT DATA
- MONITOR HOLD for one quarter; sell if HOLD persists 2+ consecutive quarters
- HOLD everything else (CB, WATCH LIST, QUALITY GROWTH PREMIUM, OVERVALUED QUALITY)
- The sell signal is quality deterioration, not classification change
- Need 30+ quarters to validate
- See `docs/STRATEGY.md` for the validated strategy

**What to build:**
- Portfolio tracking: user marks which stocks they own
- Classification monitoring: alert when owned stock hits VT/AVOID/OVERVALUED
- "What Changed for my portfolio" view distinct from the general screen diff

---

## 2. Sector-Neutral Stock Selection

**Priority:** HIGH — Investigation found sector-neutralized alpha is +0.1% (near zero). The screener is a sector rotator, not a stock picker.

**Research findings:**
- Harvey (Financial Analysts Journal, 2023): sector-neutral factor strategies improve robustness
- Northern Trust: sector-neutral weighting outperforms equal-weight for factor strategies
- Sector-relative scoring already built (`--sector-relative` flag, 70% absolute + 30% within-sector)

**To investigate:**
- Should sector-relative be the default? Backtest both modes over 12 quarters
- Should portfolio construction be sector-neutral (equal sector exposure vs current unconstrained)?
- Does sector-neutral construction preserve the "sector rotation" edge or destroy it?
- What's the optimal absolute/sector blend? Test 50/50, 60/40, 70/30, 80/20

---

## 3. Quality Signal Improvements

**Priority:** HIGH — Quality score uses single-year GP snapshot and equally-weighted Piotroski.

**Research findings:**
- Novy-Marx 2025 ("Profitability Retrospective"): GP/Assets unpunished for R&D has highest predictive power and "subsumes all of quality investing"
- AQR Quality Minus Junk: broader quality definition (profitability + growth + safety)
- Piotroski criteria have unequal predictive power — F1, F2, F4 are stronger

**To investigate:**
- Use 2-3 year average GP instead of single-year snapshot (reduces noise)
- Add Interest Coverage Ratio (EBIT / Interest Expense) — data already available, never used
- Add Operating Margin trend (flag if declining 2+ years)
- Weight Piotroski criteria by strength (F1, F2, F4 at 1.5x; others at 1.0x)
- Test AQR-style multi-dimensional quality (profitability + safety + growth) vs current Piotroski+GP

---

## 4. Conviction Ordering Within CB

**Priority:** MEDIUM — Investigation found Kendall τ = -0.038. Current ranking (sqrt(V×Q)) doesn't predict returns within CB.

**Preliminary findings:**
- Confidence gradient works in aggregate: HIGH +6.7%, MOD +5.4%, LOW +3.3%
- But conviction score (geometric mean) has no correlation with subsequent returns
- New entries outperform repeat picks by 1.7%

**To investigate:**
- Replace sqrt(V×Q) ranking with min(V-70, Q-70) (confidence margin) — aggregate data supports this
- Test momentum-weighted ranking within CB
- Test freshness bonus (new CB entries ranked higher than repeats)
- Test trajectory score as primary ranking (already computed as tie-breaker)

---

## 5. Momentum Integration

**Priority:** MEDIUM — Momentum gate is the most validated component (-1.9% delta). Could it be used more effectively?

**Research findings:**
- Alpha Architect: keeping momentum SEPARATE is superior to integrating into combined score
- Current gate catches underperformers in 7/10 quarters
- Gate victims averaged +2.6% vs CB's +4.5%

**To investigate:**
- Keep as binary gate (current) vs use as scoring overlay (weight CB picks by momentum)
- Optimal gate threshold: test bottom 20%, 25% (current), 30%, 33%
- Should the gate apply to HOLD decisions too? (sell if owned stock enters bottom 25% momentum)
- Positive momentum bonus: should top-quartile momentum boost conviction?

---

## 6. Position Sizing and Portfolio Construction

**Priority:** MEDIUM — Currently equal-weight. No position limits. No sector caps.

**Research findings:**
- Northern Trust: equal-weight has higher uncompensated risk and turnover than alternatives
- Cohen, Polk & Silli: highest-conviction positions outperform (but our conviction ordering is not predictive)

**To investigate:**
- Equal-weight (current) vs confidence-weighted (HIGH=40%, MOD=35%, LOW=25%)
- Sector caps (max 30% from any sector) — would this have helped or hurt historically?
- Max position count (10 vs 15 vs 20 vs all CB picks)
- Concentrated "Best Ideas" portfolio (top 5 only) — does it work despite ordering weakness?

---

## 7. Rebalancing Frequency

**Priority:** LOW — Quarterly is academically supported but worth validating.

**Research findings:**
- QuantPedia: optimal rebalance for value is 3-4 months, quality is 4-5 months
- Quarterly (current) aligns with both factor decay cycles
- Monthly adds cost without benefit for these factors

**To investigate:**
- Monthly vs quarterly vs semi-annual rebalance (backtest all three)
- "Stale data" problem: 75-day filing lag means using 3-6 month old financials
- Event-driven rebalancing: re-screen after earnings season (Feb/May/Aug/Nov) instead of calendar quarters?

---

## 8. Data Layer Improvements

**Priority:** LOW — Expand what data is available for scoring.

**To investigate:**
- Extend balance sheet from 2 years to 3 years (enables better trend detection)
- Add R&D expense data (for Novy-Marx 2025 GP adjustment)
- Add insider trading data (management confidence signal)
- Add earnings surprise data (if available from free sources)
- Add short interest data (sentiment signal)

---

## 9. Universe Expansion

**Priority:** PARTIALLY DONE — S&P 500 (default), Russell 1000, TASE, US All, and custom tickers are implemented.

**Done:**
- Russell 1000 proxy (top ~1000 US by market cap, `--universe russell1000`) with 7-day cache
- TASE TA-125 (`--universe tase`) and all TASE stocks (`--universe tase_all`)
- All US stocks (`--universe us_all`, ~6,200 NYSE + NASDAQ)
- Custom ticker lists (`--tickers AAPL,MSFT,TEVA.TA`)
- Combined universes (`--universe sp500+tase`)
- Russell 1000 historical approximation for survivorship-free backtest

**To investigate:**
- Russell 3000 ex-micro (market cap > $500M) — requires broader survivorship data
- International developed markets (London, Frankfurt, Tokyo)
- Sector-specific screens (e.g., only screen Healthcare)

---

## 10. Portfolio Monitoring and Alerts

**Priority:** DEPENDS ON #1 — Build after sell strategy is validated.

**To build:**
- User marks owned stocks in the UI
- Dashboard section: "My Portfolio" with current classification of owned stocks
- Alert when owned stock moves to HOLD/VT/AVOID (sell signal)
- Weekly email digest (if deployed as a service)
- Position-level P&L tracking (entry price vs current)

---

## Investigation Priority Order

| # | Item | Why First |
|---|------|-----------|
| 1 | Sell Strategy | Half the strategy is missing. Preliminary data exists. |
| 2 | Sector-Neutral | Addresses the #1 weakness (+0.1% sector-neutral alpha). |
| 3 | Quality Improvements | Strengthens the core signal with available data. |
| 4 | Conviction Ordering | Fixes the broken ranking within CB. |
| 5 | Momentum Integration | Optimizes the best-performing component. |
| 6-10 | Later | Lower priority, longer-term improvements. |

Each item needs empirical validation via `scripts/run_investigation.py` before implementation. No parameter tuning on the same data that generated the hypothesis — wait for out-of-sample quarters.

---

*Last updated: 2026-04-11*
