# Capital Research Plan

This document exists to keep Assay honest before real money is put behind it.
The current screener is a good idea-generation engine. It is not yet a
capital-ready trading system.

## Current Verdict

**Do not allocate serious capital to the current production algorithm yet.**

The latest policy-lab run on the point-in-time S&P 500 window produced this
summary:

| Policy | CAGR | EW Universe | CAGR Alpha | Avg Picks | Verdict |
|---|---:|---:|---:|---:|---|
| Current CB | 8.5% | 8.1% | +0.4% | 14.8 | Not ready |
| Raw V/Q no gates | 7.9% | 8.1% | -0.2% | 25.6 | Not ready |
| Diversified V/Q top 30 | 7.7% | 8.1% | -0.4% | 30.0 | Not ready |
| V/Q + momentum top 30 | 10.0% | 8.1% | +1.9% | 29.9 | Not ready |
| Sector-capped V/Q + momentum | 10.1% | 8.1% | +2.0% | 29.0 | Not ready |

After repairing Russell 1000 sector metadata, the cached point-in-time Russell
policy-lab run produced this summary:

| Policy | CAGR | EW Universe | CAGR Alpha | Hit Rate | Avg Picks | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Current CB | 10.4% | 9.3% | +1.1% | 62% | 24.3 | Not ready |
| Raw V/Q no gates | 11.7% | 9.3% | +2.4% | 50% | 40.4 | Not ready |
| Diversified V/Q top 30 | 10.5% | 9.3% | +1.2% | 56% | 30.0 | Not ready |
| V/Q + momentum top 30 | 13.3% | 9.3% | +4.0% | 44% | 30.0 | Not ready |
| Sector-capped V/Q + momentum | 11.6% | 9.3% | +2.3% | 56% | 30.0 | Not ready |

The Russell result is directionally more interesting than S&P 500, but still
does not justify serious capital. The best CAGR policy has a weak hit rate and
wide confidence interval; the steadier policies do not clear the +3.0% CAGR
alpha bar or statistical-significance bar.

None clears the capital gate in `research/policy_lab.py`:

- 30+ return quarters.
- Bonferroni-significant excess return.
- CAGR alpha of at least +3.0% versus the equal-weight screened universe.
- Hit rate of at least 55% versus the equal-weight screened universe.
- Average portfolio size of at least 25 positions.

This gate is deliberately strict. If the strategy cannot beat this bar in
research, it does not deserve serious money.

## Wrong Assumptions

### 1. A clean classification matrix is not the same as edge

The 3x3 matrix is understandable, but the repo's own investigation shows weak
return separation:

- RESEARCH CANDIDATE beat AVOID in only 4 of 12 replayed quarters.
- Full monotonic bucket ordering appeared in only 1 of 12 quarters.
- VALUE TRAP did not reliably underperform RESEARCH CANDIDATE.

The matrix is useful for explanation. It should not be treated as proof of
expected return.

### 2. Large-cap S&P 500 screening is probably too efficient

Piotroski's original evidence says the benefit of financial statement analysis
is concentrated in small and medium firms, low-turnover firms, and firms with
little analyst coverage. Assay's default S&P 500 universe is the opposite:
liquid, well-followed, and heavily arbitraged.

The current evidence says S&P 500 is useful as a test bed, not the main alpha
surface.

### 3. Conviction score is not a position-sizing signal

The investigation found essentially zero relation between conviction rank and
next-quarter return inside RESEARCH CANDIDATE. Therefore:

- Do not buy only the top 5.
- Do not size larger positions by conviction score.
- Do not market "highest conviction" as higher expected return.

Conviction can remain a display field, but portfolio construction needs its own
validated evidence.

### 4. Some gates are more narrative than proven

The F-score gate and VALUE TRAP label are intuitively appealing, but the current
sample does not show strong realized benefit. Momentum is more defensible, but
the negative-only gate is likely underusing the signal.

The next algorithm should treat gates as hypotheses, not laws.

### 5. Annual fundamentals plus quarterly rebalancing can create churn

Many quarterly changes are price/rank movement, not genuinely new fundamental
information. If fundamentals update annually or quarterly with lag, the
portfolio should avoid pretending every quarter contains a new full signal.

Future tests should compare quarterly, semiannual, annual, and earnings-season
refresh schedules.

### 6. Unknown sectors break portfolio construction

The Russell 1000 experiments are promising but polluted by missing sector data.
In the saved R1000 detail file, 189 of 392 historical picks have `Unknown`
sector. That makes sector caps, sector-neutral alpha, and diversification
claims unreliable.

Fixing sector/industry metadata is a prerequisite for serious broader-universe
testing.

## What The Better Algorithm Should Become

Assay should move from a hard-threshold screener to a continuous expected-return
ranking model with robust portfolio constraints.

Minimum factor families:

| Family | Examples | Why |
|---|---|---|
| Value | EBIT/EV, FCF yield, shareholder yield, book/market | Price paid still matters. |
| Profitability | gross profitability, operating profitability, ROE/ROA | Profitability improves value strategies. |
| Investment | asset growth, capex growth, equity issuance | Conservative investment is a major factor. |
| Momentum | 12-1, 6-1, recent recovery from lows | Momentum is one of the most robust anomalies. |
| Earnings quality | accruals, cash conversion, margin stability | Avoids accounting mirages. |
| Risk/liquidity | volatility, beta, leverage, turnover/liquidity | Controls drawdown and implementation cost. |

The initial model should be simple and regularized:

1. Winsorize raw signals.
2. Convert to cross-sectional percentiles.
3. Combine into pre-declared composites by family.
4. Use walk-forward validation only.
5. Add sector caps and minimum liquidity constraints.
6. Compare against equal-weight universe and simple factor ETF proxies.

Do not jump straight to a complex ML model until the data layer is point-in-time
and clean. Gu, Kelly, and Xiu show that nonlinear models can add value, but they
also require a much broader, cleaner predictor set and strict overfit control.

## Research Protocol

Every future change must pass this sequence:

1. **Write the hypothesis before running the test.**
   Example: "Positive momentum overlay improves hit rate and reduces drawdown
   without lowering CAGR alpha."

2. **Use one training window and one untouched test window.**
   If the sample is too short for this, label the result exploratory.

3. **Benchmark correctly.**
   Primary benchmark is the same-universe equal-weight return. SPY is context,
   not stock-selection alpha.

4. **Report uncertainty.**
   Every alpha needs standard error, confidence interval, t-stat, and
   multiple-testing correction.

5. **Track implementation friction.**
   Report turnover, average positions, liquidity, and sector concentration.

6. **Promote only after out-of-sample evidence.**
   No parameter should become default because it looked good on the same sample
   that produced the idea.

## Immediate Work Packages

### A. Policy Lab

Status: first pass built.

Run:

```bash
python scripts/run_policy_lab.py --years 4 --universe sp500
```

This compares pre-declared policies and prints a capital-readiness verdict.

### B. Sector Metadata Repair

Status: first pass built.

`data/universe.py` now enriches Russell 1000 sector/industry metadata from
Yahoo asset profiles, normalizes Yahoo sector names to the GICS-style labels
used by S&P data, and caches the profile results. `scripts/run_policy_lab.py`
also enriches point-in-time Russell snapshot metadata before screening.

The cached Russell proxy improved from 1,108 unknown-sector names out of 1,610
to 117 out of 1,610. The latest policy-lab run had 16-22 unknown-sector names
per quarter out of about 550-615 screened names. Selected-name unknown-sector
rates were low for most policies, but the sector-capped V/Q+momentum policy
still averaged 1.25 unknown-sector picks out of 30 (4.2%), so this is improved
but not fully finished.

Acceptance:

- Less than 5% `Unknown` sector among screened names.
- Less than 2% `Unknown` sector among selected names.
- Per-pick unknown-sector reporting in the policy-lab CSV.

### C. Longer Point-In-Time Dataset

Free data is fine for prototyping. Real-money research needs a licensed or
otherwise reliable point-in-time data source with delisted names and stable
filing availability.

Acceptance:

- At least 30 quarters.
- Preferably 60+ quarters.
- Includes delistings and acquisitions.
- No current-constituent replay.

### D. Continuous Multi-Factor Model

Build a new `research` model that computes family scores:

- Value.
- Profitability.
- Investment/conservatism.
- Momentum.
- Earnings quality.
- Risk/liquidity.

The model must be evaluated in policy lab before it can touch production.

### E. Portfolio Construction

Default research portfolio should be:

- 30 to 80 names.
- Sector cap.
- Minimum liquidity filter.
- Equal weight unless a sizing rule is validated out-of-sample.
- No top-5 concentration until ranking has proven predictive power.

## Research Sources

- Novy-Marx: gross profitability improves value strategies and predicts returns.
  https://www.nber.org/papers/w15940
- Piotroski: F-score effect is strongest inside high book-to-market names and is
  concentrated in small/mid, low-turnover, low-analyst-coverage firms.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=249455
- Fama-French five-factor model: profitability and investment are central return
  dimensions.
  https://www.sciencedirect.com/science/article/abs/pii/S0304405X14002323
- Asness, Moskowitz, Pedersen: value and momentum should be studied jointly.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2174501
- Gu, Kelly, Xiu: machine learning can improve asset pricing by modeling
  nonlinear interactions, but requires overfit control.
  https://academic.oup.com/rfs/article/33/5/2223/5758276
- Open Source Asset Pricing: public reference set for 209 predictive
  firm-level characteristics.
  https://www.openassetpricing.com/data/
