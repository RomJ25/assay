<div align="center">

# Design Decisions

**A permanent log of algorithm choices we have considered, rejected, accepted, or deferred — so future audits don't re-litigate the same questions**

</div>

---

### Contents

[Purpose](#purpose) · [How to read this file](#how-to-read-this-file) · [Kept decisions](#kept-decisions-actively-defended) · [Rejected alternatives](#rejected-alternatives-considered-and-declined) · [Deferred changes](#deferred-changes-would-require-data-layer-work) · [Known deviations](#known-deviations-from-academic-reproduction) · [Empirical investigation](#empirical-investigation--component-effectiveness-april-2026) · [Review log](#review-log)

---

## Purpose

This document exists so that every future audit of Assay's core algorithm starts from a shared baseline instead of re-opening settled questions. Each entry below records:

- **What was considered** — the alternative, its academic source, and the specific claim in its favor
- **What was decided** — keep the current behavior, adopt the alternative, or defer
- **Why** — the reasoning that made the call, with citations where relevant
- **Last reviewed** — the date of the most recent deep look, so stale conclusions can be refreshed

The goal is not to be final. It is to be *legible*. If a future audit reaches a different conclusion, the entry should be updated — with the old reasoning preserved in the review log at the bottom — so the project's thinking is always recoverable.

A decision can move between categories over time. "Rejected" today can become "accepted" tomorrow if new evidence arrives. "Deferred" can become "accepted" once the blocking data or engineering work is done. What must not happen is that a question gets re-asked from scratch without reference to the previous round's reasoning.

---

## How to read this file

Entries are grouped by status, not by pipeline stage, because the question a future reader is almost always asking is "has this been considered before?" and not "what does the value scorer do?" (For the latter, see [`METHODOLOGY.md`](METHODOLOGY.md).)

Each entry uses the following shape:

> **Title** — short descriptor
>
> **Status:** KEPT / REJECTED / DEFERRED / PARTIAL
>
> **Last reviewed:** YYYY-MM-DD
>
> **Context.** The alternative being considered and its academic source.
>
> **Decision.** What we do today.
>
> **Why.** The reasoning behind the call — ideally with a citation.
>
> **Would move us:** What kind of new evidence or engineering would cause us to reopen the question.

---

## Kept decisions (actively defended)

These are the core choices that have survived at least one deep audit against primary academic sources. They are not arbitrary — each one has been compared against its closest alternative and kept for a specific reason.

### EBIT/EV as the primary value signal

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Book-to-market (B/M) is the classical Fama-French value factor. Earnings Yield (EBIT/EV), also known as the Acquirer's Multiple, is the modern alternative championed by Carlisle (2014) and validated in Schwartz & Hanauer (2024) "Formula Investing."

**Decision.** EBIT/EV is the primary signal, weighted 70% of the Value score.

**Why.** Schwartz & Hanauer (2024) report that over the 1963-2022 U.S. sample, the Acquirer's Multiple produced the highest top-decile raw return of any single-factor formula they tested. EBIT/EV is also capital-structure neutral (uses EV, not market cap), which book-to-market is not. Book value has become progressively less informative as intangibles have grown as a share of corporate assets.

**Would move us:** A post-2022 replication showing EBIT/EV has lost its edge on large-caps specifically, or a synthesized intangibles-adjusted book value that restores B/M's original signal strength.

---

### 70 / 30 Earnings-Yield / Free-Cash-Flow composite

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** A pure EBIT/EV score can be gamed by aggressive accruals. FCF is a cash-based reality check; combining them diversifies the signal.

**Decision.** Value = 0.70 × EarningsYield_percentile + 0.30 × FCFYield_percentile.

**Why.** There is no academic consensus on the optimal blend. The 70/30 tilt keeps EBIT/EV as the primary driver (the factor with the strongest long-run evidence) while letting FCF penalize names whose earnings and cash flows diverge. Equal-weighting would give FCF more power than its comparative evidence base justifies.

**Would move us:** A study showing a specific blend (e.g., 60/40, 80/20) systematically outperforms on large-caps. Absent that, the exact ratio is defensible but not uniquely correct.

---

### Percentile-rank scoring (not z-scores)

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** The two common ways to normalize a fundamental factor across a universe are (a) cross-sectional z-scores, and (b) percentile ranks. Z-scores preserve magnitude but are sensitive to outliers and distributional assumptions.

**Decision.** All factor scoring uses percentile rank `(n - i) / n × 100`.

**Why.** Fundamentals are heavy-tailed and prone to outliers (a single megacap with a distorted EV, a single firm reporting a one-time charge). Percentile rank is outlier-robust by construction and makes no distributional assumption. The trade-off — losing magnitude information — is acceptable because the downstream classification and conviction logic only cares about ordering, not distance.

**Would move us:** A specific use case where magnitude matters for the decision (e.g., sizing positions by factor distance from neutral). Assay is a screener, not a portfolio optimizer, so this does not currently apply.

---

### Include negative earners, rank them at the bottom

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Most academic value studies drop firms with negative EBIT or negative FCF from the universe. Schwartz & Hanauer (2024) note this explicitly for the Acquirer's Multiple.

**Decision.** Negative EBIT and negative FCF firms stay in the universe and rank at the bottom of their respective factors. They are never silently excluded.

**Why.** Excluding them creates a hidden filter that users cannot see. A negative earner should show up in the output classified as AVOID or VALUE TRAP so the user knows the engine saw it and rejected it, not that it was quietly omitted. The downstream Piotroski F-gate (F ≥ 6 for CONVICTION BUY) and classification thresholds handle these cases correctly.

**Would move us:** Evidence that the bottom-of-universe rank biases the percentile distribution in a way that distorts legitimate value scores. We have not seen this in practice.

---

### Piotroski F-Score (9 binary criteria) as the quality backbone

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Alternatives include the Greenblatt Magic Formula's ROC (Return on Capital), the Conservative Formula's low-volatility plus payout yield mix, and pure Gross Profitability alone.

**Decision.** Piotroski F-Score forms 50% of the Quality score. The remaining 50% is Gross Profitability.

**Why.** Piotroski (2000) originally demonstrated 13.4% long-only excess returns and a 23% long-short spread (1976-1996) on high-B/M stocks. Schwartz & Hanauer (2024) confirmed the 23% figure and documented that Piotroski's F-Score retains post-2000 predictive power, especially as a filter within value stocks. No other single-factor quality signal has the same length of independent validation. The geometric mean aggregation of Value and Quality means Quality needs a hard-edge filter, not just a soft percentile — the F-gate at F ≥ 6 provides that.

**Would move us:** A 20+ year post-2000 replication showing the F-Score's edge has fully decayed on large-caps. Current evidence (Schwartz & Hanauer 2024) says it has weakened but not disappeared.

---

### Gross Profitability (GP / Assets) as the second quality signal

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Novy-Marx (2013) introduced Gross Profitability as a quality signal with predictive power "roughly equal to book-to-market ratio." He argued that it is the cleanest profitability measure because gross profit is the furthest-upstream income statement line and is least distorted by accounting choices.

**Decision.** GP/Assets = (Revenue − COGS) / Total Assets, computed as a percentile rank, forms 50% of the Quality score.

**Why.** Direct match to Novy-Marx 2013. We considered but rejected Novy-Marx's 2025 update (which adds R&D back to gross profit) because it has not yet become the accepted convention in the literature and the improvement is modest on large-caps where R&D capitalization choices are more uniform.

**Would move us:** Broad adoption of the R&D-add-back convention in academic reproduction papers, or a specific showing that it materially improves large-cap signal strength.

---

### 50 / 50 Piotroski / GP quality composite

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** There is no academic consensus on how to weight Piotroski's F-Score against Gross Profitability when combining them.

**Decision.** Quality = 0.50 × F_normalized + 0.50 × GP_percentile (with a 0.80 single-source penalty if either input is missing).

**Why.** Equal weighting treats the two signals as independent complements: F-Score captures financial health and accounting discipline; Gross Profitability captures business quality. There is no empirical basis for tilting toward one over the other on a 500-name universe. The single-source penalty ensures a stock missing one of the two inputs cannot receive a perfect Quality score on the strength of the other alone.

**Would move us:** A study that specifically optimizes this blend on a large-cap universe. We searched; none exists.

---

### Geometric mean for conviction aggregation

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** The two common ways to combine two factor scores into a composite are (a) arithmetic mean, (b) geometric mean, (c) rank sum (the Magic Formula approach).

**Decision.** Conviction = √(Value × Quality), rounded to one decimal.

**Why.** The geometric mean is uniquely justified by the AM-GM inequality: it is the only aggregation that enforces "both dimensions must be high" as a hard mathematical constraint. A stock with Value 95 and Quality 30 gets a conviction of ~53 (arithmetic mean would give 62.5). A stock with Value 70 and Quality 70 gets a conviction of exactly 70. This matches the philosophical claim in the README that the engine only acts when cheapness *and* quality align. Arithmetic mean would let one dimension compensate for weakness in the other — which is exactly the value-trap / overvalued-quality failure mode the engine is built to avoid.

**Would move us:** Nothing short of a fundamental rethink of the project's thesis. This is the decision with the strongest internal logic.

---

### 40 / 70 classification thresholds

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** The 3×3 classification matrix splits each dimension into Low / Mid / High. The split points could be at any percentile.

**Decision.** High ≥ 70, Low < 40, Mid in between.

**Why.** 70 is the conventional "top-30% of the universe" cutoff used in most academic factor studies. 40 is a slightly wider "bottom cohort" that keeps the Mid bucket from being artificially narrow. The asymmetry (30pp Low, 30pp Mid, 30pp High, with 10pp of overlap absorbed into Mid) is a deliberate choice to make CONVICTION BUY rare (it requires the top-30% on *both* dimensions) while keeping HOLD and WATCH LIST populated enough to be informative. Alternatives (33/67, 30/70) are equally defensible; we picked 40/70 because it produced the cleanest separation on the 2026-04-08 ceasefire case study and the backtest bucket returns.

**Would move us:** A specific empirical showing that a different split produces materially better CB-vs-AVOID return separation.

---

### F-Score gate at F ≥ 6

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Piotroski's 2000 paper compared F ≥ 8 ("high") against F ≤ 1 ("low") stocks and reported the 13.4% long-only excess return and 23% long-short spread from that cohort comparison. A strict reading would suggest the gate should be at F ≥ 8, not F ≥ 6.

**Decision.** Stocks with F < 6 are downgraded from CONVICTION BUY to WATCH LIST regardless of their composite Quality score.

**Why.** Piotroski's 8-vs-1 result was a long-short finding on a universe that included micro-caps where the F-Score effect is strongest. Assay runs long-only on the S&P 500 (large-caps only, where the effect is weaker but still present per Schwartz & Hanauer 2024). Tightening the gate to F ≥ 8 on 500 large-cap names would likely collapse CONVICTION BUY to zero picks most quarters without a clear showing of improved risk-adjusted returns. F ≥ 6 is a pragmatic middle ground: stricter than the "any value stock" baseline Piotroski compared against, looser than his headline 8-vs-1 comparison. It preserves meaningful quality discrimination while allowing the engine to surface picks on a 500-name universe.

**Would move us:** A 20+ year backtest on S&P 500 specifically showing F ≥ 7 or F ≥ 8 produces better risk-adjusted returns than F ≥ 6.

---

### Bottom-25% momentum gate

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** The purpose of the momentum gate is not to add a momentum factor — it is to avoid catching a falling knife. A cheap, high-quality stock in steep decline is usually cheap for a reason the fundamentals have not yet caught up to.

**Decision.** Stocks in the bottom 25% of 12-1 month momentum percentile are downgraded from CONVICTION BUY to WATCH LIST.

**Why.** Research Affiliates (2024) showed that adding a simple "avoid bottom-quintile momentum" filter to value strategies reduces drawdowns without meaningfully reducing long-run returns. Bottom-25% is a slightly looser version of that filter, calibrated to leave room for contrarian picks that have started to recover.

**Would move us:** Evidence that a different cutoff (bottom 20%, bottom 33%) produces materially better drawdown protection.

---

### 12-minus-1 month momentum

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Jegadeesh & Titman (1993) established the 12-1 month window as the canonical academic momentum measure: 12-month return, skipping the most recent month to avoid short-term reversal.

**Decision.** Momentum = (price_{t−1mo} − price_{t−12mo}) / price_{t−12mo}.

**Why.** Direct match to academic convention. The skip-month is not optional — short-term reversal is a separate, documented effect, and including it would contaminate the momentum signal.

**Would move us:** Nothing. This is a canonical calculation with no meaningful alternatives.

---

### Filing lag: 75 days

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** Academic convention (Fama-French 1993, Jensen et al. 2023, Schwartz & Hanauer 2024) is 180 days from fiscal year-end before a company's annual financial data is considered "known" to investors. The SEC's 10-K deadline for large accelerated filers is 60 days.

**Decision.** `BACKTEST_FILING_LAG_DAYS = 75` in `config.py`.

**Why.** Assay's universe is S&P 500 only. Every S&P 500 firm is a large accelerated filer and subject to the 60-day SEC deadline. Adding 180 days on top of fiscal year-end would force the backtest to use 15+ month stale fundamentals at each rebalance, which is overly conservative for this specific universe and would materially distort historical quality signals. 75 days (60-day legal deadline + 15-day buffer for data-provider lag) is defensible for S&P 500 but means Assay's backtest numbers are **not directly comparable** to academic papers using 180 days. This trade-off is documented in [`METHODOLOGY.md`](METHODOLOGY.md) §12.1.

**Would move us:** Evidence that S&P 500 firms routinely restate within the 60-90 day window in ways that would have changed F-scores or value ranks. We have not seen this.

---

### Equal-weight portfolio construction

**Status:** KEPT · **Last reviewed:** 2026-04-09

**Context.** The academic standard is capped value-weighting at the 80th NYSE percentile (Schwartz & Hanauer 2024 page 7-8). This tilts academic backtests toward larger firms.

**Decision.** The backtest computes equal-weighted returns across CONVICTION BUY picks.

**Why.** Equal-weighting is the honest benchmark for an individual investor, who would plausibly buy each name in equal dollar amounts rather than marking to float-adjusted market cap. It also gives more representation to smaller S&P 500 names where the factor signals are sometimes stronger. The trade-off is that Assay's backtest numbers are not directly comparable to academic cap-weighted returns — documented in [`METHODOLOGY.md`](METHODOLOGY.md) §12.3.

**Would move us:** A showing that cap-weighting within the CB bucket materially changes the headline backtest numbers or the bucket-return ordering.

---

### Survivorship bias handling

**Status:** MITIGATED · **Last reviewed:** 2026-04-12

**Context.** A historically correct backtest would use the S&P 500 constituent list as it existed on each rebalance date (point-in-time data). By default, Assay uses the current list and acknowledges the survivorship overstatement.

**Decision.** Two modes are available:
- **Default:** Current list replayed backward. The overstatement is disclosed in `backtest/report.py:31-37` and `METHODOLOGY.md` §12.2.
- **`--survivorship-free`:** Uses point-in-time constituents from `data/sp500_historical.py` for each quarter. Requires historical membership data (currently supported for S&P 500 only).

Additionally, stocks with a start-of-quarter price but no end-of-quarter price (delisting, acquisition) are assigned a conservative 0% return rather than being silently dropped from the portfolio average.

**Why.** Point-in-time data from CRSP/Compustat is paid. The `--survivorship-free` flag provides a best-effort correction using available historical membership data. The 0% delisting assumption is conservative without being catastrophic — appropriate for large-cap universes where most delistings are acquisitions, not bankruptcies.

**Would move us:** Access to free or cheap point-in-time constituent data with delisting returns. This remains the biggest methodological improvement opportunity.

---

## Rejected alternatives (considered and declined)

These are changes that have been specifically considered and rejected after deliberation. The reasoning is preserved so the same alternative is not re-proposed without reference to the prior round.

### Tighten F-gate to F ≥ 7 or F ≥ 8

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** Piotroski's 2000 paper's headline 13.4% long-only excess return came from the F ≥ 8 "high" cohort. A naive reading suggests the gate should be at F ≥ 8.

**Decision.** Keep the gate at F ≥ 6.

**Why rejected.** (1) Piotroski's universe was high-B/M value stocks that included micro-caps where the F-Score effect is strongest. Assay runs on the S&P 500 (large-caps only), where the effect is empirically weaker per Schwartz & Hanauer (2024). (2) Tightening to F ≥ 8 on a 500-name large-cap universe would collapse CB to near-zero picks most quarters. (3) F ≥ 6 already filters out 60-80% of the universe in a typical quarter — the stricter gate would not change the *direction* of the answer, only whether there is an answer at all. (4) We have no 20+ year S&P 500-specific backtest showing F ≥ 7 or F ≥ 8 produces better risk-adjusted returns on this universe.

**Would move us:** Any of the three gaps above being filled.

---

### Adopt the Magic Formula's ROC as an alternate quality signal

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** Schwartz & Hanauer (2024) reported that the Greenblatt Magic Formula (which combines EBIT/EV with Return on Capital) produced the highest post-2000 raw CAGR (15.8%) of any formula they tested, beating both the Acquirer's Multiple and the Conservative Formula.

**Decision.** Do not add ROC to the Quality score.

**Why rejected.** (1) This is a feature addition, not a bug fix. No user has asked for it. (2) Adding ROC to the Quality score would dilute the "Piotroski + Gross Profitability" thesis the project is built on. (3) Schwartz & Hanauer's result is the *raw* CAGR — the Conservative Formula actually produced the highest Sharpe ratio (0.78), and the Acquirer's Multiple produced the highest top-decile return over the full 1963-2022 sample. No single formula dominated on all metrics. (4) Adding ROC would create two independent profitability signals (GP and ROC) that measure similar things, which is less diversifying than keeping GP and swapping in a financial-health signal (Piotroski).

**Would move us:** A user request for a Magic-Formula mode with explicit awareness of the trade-off, or a replication showing ROC strictly dominates GP on large-caps.

---

### Rank-sum aggregation instead of geometric mean

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** The Greenblatt Magic Formula uses rank-sum aggregation: rank stocks on Value, rank them on Quality, add the two ranks, and sort by the sum.

**Decision.** Keep geometric mean.

**Why rejected.** Rank-sum is arithmetic by construction — a rank of 1 on Value and 500 on Quality gives the same combined rank (501) as 250 on both. That is exactly the substitution effect the geometric mean is designed to prevent. The philosophical claim of Assay is that value-without-quality is a trap and quality-without-value is overpriced, and the geometric mean is the only aggregation that enforces "both must be high" mathematically via AM-GM. Rank-sum is a valid aggregation for a different thesis (the Magic Formula's), not Assay's.

**Would move us:** Nothing short of abandoning the core "both must align" thesis.

---

### Value-weight the backtest portfolio (academic standard)

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** Academic factor studies use capped value-weighting at the 80th NYSE percentile. Equal-weighting is considered naive.

**Decision.** Keep equal-weighting.

**Why rejected.** Equal-weighting is the honest construction for the project's actual audience — individual investors who will buy each CB name in equal dollar amounts. Value-weighting would tilt the reported returns toward the largest megacaps in the CB bucket, which distorts the selection-alpha question: "did Assay's factor signals work?" becomes confounded with "did the largest names happen to win this quarter?" The academic convention exists to make results comparable across papers, not because it is better.

**Would move us:** A specific showing that equal-weighting distorts the headline backtest numbers in a misleading direction. Both constructions produce the same *ordering* of CB vs WATCH LIST vs AVOID buckets; the magnitudes differ but the ranking does not.

---

### Extend filing lag from 75 to 180 days

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** Academic convention is 180 days from fiscal year-end for "as-known" fundamentals (Fama-French 1993 and every replication since).

**Decision.** Keep 75 days.

**Why rejected.** The 180-day convention is built for universes that include smaller firms and non-accelerated filers, which have a 90-day SEC deadline (not 60). Assay's universe is S&P 500 only, where every firm is a large accelerated filer on a 60-day deadline. Adding 120 additional days on top of the legal filing deadline would force the backtest to use 15+ month stale fundamentals at every rebalance. The practical effect is that Assay's Q1 2023 rebalance would use December 2021 fundamentals instead of December 2022 — a full year of lost signal for no genuine prudence gain. The trade-off is documented transparently in `METHODOLOGY.md` §12.1: Assay's backtest is not directly comparable to academic papers using 180 days.

**Would move us:** Documented S&P 500 restatement rates in the 60-120 day window material enough to change F-scores. We have not seen this.

---

### Novy-Marx (2025) R&D add-back convention for Gross Profit

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** Novy-Marx's 2025 update argues that R&D should be added back to gross profit because it is an intangibles-like investment miscategorized as an expense. This would raise the reported GP of R&D-heavy firms.

**Decision.** Keep the original Novy-Marx 2013 definition: GP = Revenue − COGS, without R&D add-back.

**Why rejected.** (1) The 2025 update has not yet become the accepted convention in academic reproduction papers (Schwartz & Hanauer 2024 and Jensen et al. 2023 still use the 2013 definition). (2) On S&P 500 large-caps, the R&D-intensity dispersion is lower than in Novy-Marx's broader universe, so the practical impact is smaller. (3) Adopting a non-canonical convention unilaterally would make Assay less reproducible, not more.

**Would move us:** Broad adoption of the 2025 add-back in the reproduction literature.

---

### Different weights for Value composite (60/40, 80/20)

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** The 70/30 EarningsYield/FCF blend is one of many defensible combinations. Alternatives include 50/50 (equal), 80/20 (stronger EY tilt), and 60/40 (softer tilt).

**Decision.** Keep 70/30.

**Why rejected.** No academic consensus exists on the optimal blend, and we found no study that specifically optimizes this ratio on a large-cap universe. 70/30 keeps EBIT/EV as the primary driver (the factor with the strongest long-run evidence) while letting FCF serve as a reality check. Tuning this ratio in the absence of evidence would be overfitting to whatever period we tested against.

**Would move us:** A study that specifically optimizes the EY/FCF blend on S&P 500 or comparable large-cap universes.

---

### Different weights for Quality composite (60/40, 40/60)

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** The 50/50 Piotroski/GP split treats the two signals as independent complements. Alternatives tilt toward one or the other.

**Decision.** Keep 50/50.

**Why rejected.** Same reasoning as the Value composite: no academic consensus, no evidence basis for tilting on large-caps, tuning without evidence is overfitting.

**Would move us:** A study that specifically optimizes the Piotroski/GP blend.

---

### Alternate classification thresholds (30/70, 33/67)

**Status:** REJECTED · **Last reviewed:** 2026-04-09

**Context.** The 40/70 split point is one of several defensible choices.

**Decision.** Keep 40/70.

**Why rejected.** 30/70 and 33/67 are equally defensible. 40/70 was chosen because it produced the cleanest separation between CB and AVOID buckets on the 2026-04-08 ceasefire case study and the backtest. Changing it now in the absence of new evidence would be re-tuning on the same data.

**Would move us:** Out-of-sample evidence that a different split produces materially better bucket separation.

---

## Deferred changes (would require data-layer work)

These are changes we would make if the engineering and data cost were lower, but where the current implementation is good enough that the work is not justified by the expected improvement.

### F3 and F9 beginning-of-year asset denominator

**Status:** DEFERRED · **Last reviewed:** 2026-04-09

**Context.** The Jensen et al. (2023a) modern reproduction of Piotroski's F-Score uses beginning-of-year total assets as the denominator for ROA (F3) and Asset Turnover (F9). Assay uses end-of-year assets. For F3, this means Assay computes `NI_0 / Assets_0 > NI_1 / Assets_1` where the academic version is `NI_0 / Assets_{-1} > NI_{-1} / Assets_{-2}`.

**Decision.** Keep end-of-year denominator. Acknowledge the deviation in `METHODOLOGY.md` §12.6.

**Why deferred.** Fixing this requires extending `FinancialData` to store 3 years of balance-sheet history (currently 2) and forcing a full cache rebuild. For stable companies (most of the S&P 500), the direction-test result is identical — both conventions detect whether ROA and asset turnover improved year-over-year. The practical impact on F-scores is small. Producing *more academically reproducible* F-scores is a different goal from producing *better* F-scores, and we are not confident the change would improve the strategy.

**Would move us:** A separate reason to extend `FinancialData` to 3 years of balance-sheet depth (e.g., adding another signal that needs it). The marginal cost of fixing F3/F9 at that point would be trivial.

---

### F5 long-term debt field and ≤ comparison

**Status:** DEFERRED · **Last reviewed:** 2026-04-09

**Context.** The Jensen et al. (2023a) modern reproduction uses long-term debt (not total debt) for F5 (Leverage Decreasing), with a `≤` comparison ("did not increase"). Assay uses total debt with a strict `<` comparison ("fell"). Schwartz & Hanauer (2024) page 4 confirms the Jensen convention.

**Decision.** Keep total debt and strict `<`.

**Why deferred.** Fixing the debt definition requires adding a `long_term_debt` field to `FinancialData` and updating the yahooquery provider. For S&P 500 large-caps, long-term debt is typically 85-95% of total debt, so the practical overlap is very high — F5 would flip on perhaps 2-5% of firms in a typical quarter. The strict `<` vs `≤` question is separate: Assay's strict `<` matches Piotroski's 2000 original wording ("leverage fell") and is more conservative. Switching to `≤` would soften the criterion and produce slightly higher F-scores overall, which is not obviously better.

**Would move us:** A data provider that exposes long-term debt natively at the same cost as total debt, plus a showing that the ≤ convention materially improves signal strength.

---

### F7 EQIS field replacement for shares-outstanding proxy

**Status:** DEFERRED · **Last reviewed:** 2026-04-09

**Context.** The academic implementation of F7 (No Share Dilution) uses the Compustat EQIS field (equity issuance), which explicitly tracks secondary offerings. Assay uses `shares_outstanding_0 ≤ shares_outstanding_1` as a proxy because Yahoo does not expose EQIS.

**Decision.** Keep the shares-outstanding proxy.

**Why deferred.** Yahoo does not provide EQIS at any price. The proxy can disagree with EQIS when buybacks offset dilution within the same year (Assay's proxy would say "no dilution" because net shares didn't grow; EQIS would flag the equity issuance). But the proxy answers a slightly different and also-defensible question: did the firm net-dilute its shareholders? We consider this a reasonable proxy, not a bug.

**Would move us:** Access to a free data source with explicit equity-issuance tracking. We do not know of one.

---

### Point-in-time S&P 500 constituent data

**Status:** DEFERRED · **Last reviewed:** 2026-04-09

**Context.** The backtest uses the current S&P 500 list for all historical quarters, which creates survivorship bias. A correct backtest would use point-in-time constituents.

**Decision.** Keep current list. Disclose the 2-5% CAGR overstatement.

**Why deferred.** Point-in-time S&P 500 data is in CRSP/Compustat, which is paid. We surveyed free sources and found nothing reliable. The disclosure is prominent in `backtest/report.py:31-37` so users know the backtest numbers are inflated.

**Would move us:** A free or cheap point-in-time source (e.g., Wikipedia history pages scraped reliably, or a public dataset we have not found). This is the single biggest "if we could fix one thing" item in the backtest layer.

---

## Known deviations from academic reproduction

This section summarizes the places where Assay's implementation does not exactly match the canonical academic version of its reference papers. These are not bugs — they are documented choices, each with a specific justification above. The purpose of this section is to make the full list inspectable in one place.

| # | Signal | Assay | Academic (Jensen 2023a / Schwartz-Hanauer 2024) | Why |
|---|---|---|---|---|
| 1 | Piotroski F1 (NI > 0) | `net_income > 0` | `ROA > 0` | Mathematically identical for positive-asset firms |
| 2 | Piotroski F2 (OCF > 0) | `OCF > 0` | `CFO / Assets > 0` | Mathematically identical for positive-asset firms |
| 3 | Piotroski F3 (ROA improving) | End-of-year assets | Beginning-of-year assets | See [F3/F9 deferred entry](#f3-and-f9-beginning-of-year-asset-denominator) |
| 4 | Piotroski F5 (Leverage) | Total debt, strict `<` | Long-term debt, `≤` | See [F5 deferred entry](#f5-long-term-debt-field-and--comparison) |
| 5 | Piotroski F7 (Dilution) | `shares_out` proxy | Compustat EQIS | See [F7 deferred entry](#f7-eqis-field-replacement-for-shares-outstanding-proxy) |
| 6 | Piotroski F9 (Asset Turnover) | End-of-year assets | Beginning-of-year assets | See [F3/F9 deferred entry](#f3-and-f9-beginning-of-year-asset-denominator) |
| 7 | Filing lag | 75 days | 180 days | See [filing lag entry](#extend-filing-lag-from-75-to-180-days) |
| 8 | Portfolio weighting | Equal | Capped value-weight (80th NYSE pctile) | See [weighting entry](#value-weight-the-backtest-portfolio-academic-standard) |
| 9 | Survivorship | Current S&P 500 list | Point-in-time constituents | See [constituent data entry](#point-in-time-sp-500-constituent-data) |
| 10 | Gross Profit definition | Revenue − COGS (Novy-Marx 2013) | Revenue − COGS + R&D (Novy-Marx 2025) | See [R&D entry](#novy-marx-2025-rd-add-back-convention-for-gross-profit) |

Five of nine Piotroski criteria (F1, F2, F4, F6, F8) are mathematically identical to the academic version. Four (F3, F5, F7, F9) have minor convention differences, all documented above.

---

## Empirical investigation — component effectiveness (April 2026)

This section records the results of a systematic 10-test investigation that replayed the full screener across 12 quarters (Q1 2023 through Q1 2026, the range with reliable cached financial data) and tested each component independently. All findings are directional hypotheses at n=12 quarters — minimum 30 quarters needed for statistical significance.

Infrastructure: `backtest/case_study.py` (analysis engine), `scripts/run_investigation.py` (runner). The investigation replays the FULL classification pipeline for ALL stocks (not just CB picks), tracks which gate downgraded each stock, and computes per-bucket quarterly returns.

### Classification gradient is not consistently monotonic

**Status:** INVESTIGATED — WEAKER THAN EXPECTED

**Tested:** 2026-04-10 | **Sample:** 11 active quarters

**Finding.** CB beat AVOID in only 6 of 11 quarters. Average CB−AVOID spread: **−0.8%**. The full monotonic ordering (CB > WL > HOLD > AVOID) held in **0 of 11 quarters**. The middle buckets (WL, HOLD, OV) are jumbled and don't follow a consistent ordering.

**Decision.** Keep current 40/70 thresholds. The classification is directionally useful (VALUE TRAPs and AVOID are worst 7/11 quarters) but the clean gradient the README describes is not present per-quarter.

**Would move us:** If CB consistently underperforms AVOID over 30+ quarters, reconsider the threshold structure.

### F-gate is neutral

**Status:** INVESTIGATED — NEUTRAL

**Tested:** 2026-04-10 | **Sample:** 17 F-gate victims across 12 quarters

**Finding.** F-gate victims (V≥70, Q≥70, F<6) averaged **+2.7%** return vs CB survivors **+4.5%**. The gate helped in 4 quarters and hurt in 3. Repeat victims BLDR (4 appearances, highly volatile: −33.6%, +40.1%, −26.3%, −12.6%) dominate the sample. The gate fires 0–4 times per quarter.

**Decision.** KEEP. The gate is cheap insurance with near-zero cost (low firing rate) and an academic prior (Piotroski 2000). Removing it based on n=17 would be overfitting to noise.

**Would move us:** If 50+ victims over 30 quarters show significant outperformance of CB.

### Momentum gate helps

**Status:** INVESTIGATED — CONFIRMED

**Tested:** 2026-04-10 | **Sample:** 98 momentum-gate victims across 12 quarters

**Finding.** Momentum victims (bottom-25% momentum, downgraded from CB to WL) averaged **+2.6%** vs CB survivors **+4.5%** (delta −1.9%). Victims underperformed CB in **7 of 10** quarters with data. Notable exceptions exist (ULTA +27.6%, DVA +35.3%) but the central tendency is clear.

**Decision.** KEEP at bottom-25% percentile. This is the screener's most empirically validated gate.

**Would move us:** If victims begin systematically outperforming over an extended period.

### Confidence gradient works in aggregate, not per-quarter

**Status:** INVESTIGATED — PARTIALLY CONFIRMED

**Tested:** 2026-04-10 | **Sample:** 170 CB stock-quarter observations

**Finding.** Aggregate returns: HIGH **+6.7%** (n=17), MODERATE **+5.4%** (n=69), LOW **+3.3%** (n=84) — a perfect gradient. But per-quarter monotonicity held in only **1 of 11** quarters. The ceasefire case study (2026-04-08) caught one of the rare monotonic days.

**Decision.** KEEP confidence labels. They are meaningful in expectation but should not be relied on for any individual quarter. Frame as long-run probability, not per-quarter guarantee.

**Would move us:** If the aggregate gradient breaks down over 30+ quarters.

### VALUE TRAP classification works

**Status:** INVESTIGATED — CONFIRMED

**Tested:** 2026-04-10 | **Sample:** 276 VALUE TRAP stock-quarters

**Finding.** VALUE TRAPs underperformed CB in **7 of 11** quarters. The 4 failures include the Q4 2025 Iran oil shock (VT +26.6% vs CB +3.6%, driven by cheap energy names getting a macro tailwind) and quarters where both VT and CB were negative. On average, VT significantly trails CB.

**Decision.** KEEP. The classification correctly identifies cheap stocks with weak fundamentals. Failures during commodity booms are expected — the screener is correctly refusing a sector-directional bet.

**Would move us:** If VT consistently outperforms CB outside commodity events.

### Win/loss asymmetry — strategy-dependent

**Status:** INVESTIGATED — REVISED (April 2026)

**Tested:** 2026-04-10 (quarterly rebalance), 2026-04-12 (selective sell)

**Original finding (quarterly rebalance).** Win/loss ratio of **1.05×** at 52% hit rate. No meaningful asymmetry. This led to removing the asymmetry claim from the README.

**Revised finding (selective sell strategy).** Under the selective sell strategy (hold WL/QGP/OQ, sell only VT/AVOID/OV), the quarterly win/loss ratio improved to **1.28×** at 50% hit rate. The improvement comes from holding winners longer — positive excess quarters averaged +4.4% vs negative quarters at -3.4%.

**Decision.** The asymmetry IS present under the correct strategy. The original finding was an artifact of quarterly rebalancing (which sells winners). Under selective sell, the system exhibits the asymmetry the design intended. The magnitude (1.28x) is directional at n=12 quarters.

**Would move us:** Continued monitoring over 30+ quarters to confirm the 1.28x ratio persists.

### Sector exposure — improved under selective sell

**Status:** INVESTIGATED — REVISED (April 2026)

**Tested:** 2026-04-10 (quarterly rebalance), 2026-04-12 (selective sell)

**Original finding (quarterly rebalance).** Sector-neutralized alpha was **+0.1%** — essentially zero. The screener appeared to be a sector rotator, not a stock picker.

**Revised finding (selective sell).** Under the selective sell strategy, sector-neutralized alpha improved to **+0.5%** per quarter, positive in **6 of 12** quarters. The improvement comes from holding appreciated stocks that outperform their sector peers.

**Portfolio composition evolved:** The selective sell portfolio diversified naturally to 49 positions across 5 major sectors (Consumer Disc 27%, Health Care 20%, Industrials 16%, Consumer Staples 14%, IT 14%), with 24% of holdings in QUALITY GROWTH PREMIUM (appreciated winners).

**Decision.** The sector rotation finding was partially an artifact of quarterly rebalancing. Under selective sell, stock selection contributes more meaningfully. Still monitor over 30+ quarters.

**Would move us:** If sector-neutralized alpha exceeds +1.0% consistently over 30+ quarters, the stock selection thesis is confirmed.

### New entries outperform repeat picks

**Status:** INVESTIGATED — DIRECTIONAL

**Tested:** 2026-04-10 | **Sample:** 103 returning picks, 67 new entries

**Finding.** New entries to CB averaged **+5.5%** per quarter vs returning picks (in CB the previous quarter) at **+3.8%**, a delta of **−1.7%** against returning picks. "Permanent residents" (MO 9/12 quarters, HCA 9/12, NTAP 8/12) may be a drag.

**Decision.** LOG and MONITOR. Do not add a freshness signal or holding-period cap based on n=170. The finding is directionally interesting but could reverse with more data.

**Would move us:** If the delta persists and grows over 30+ quarters, add a freshness signal (e.g., flag first-quarter-in-CB picks as higher priority).

### Conviction ordering (sqrt(V×Q)) is not predictive within CB

**Status:** INVESTIGATED — NOT CONFIRMED

**Tested:** 2026-04-10 | **Sample:** 10 quarters with ≥3 CB picks

**Finding.** Kendall's τ between conviction score and quarterly return within CB averaged **−0.038**. Positive correlation appeared in only **2 of 10** quarters. Higher conviction scores do not predict higher returns within the CB bucket. The geometric mean is effective as a *threshold mechanism* (both V and Q must be ≥70) but not as a *ranking mechanism* for position sizing.

**Decision.** KEEP geometric mean for threshold qualification. Do not use conviction ordering for position sizing recommendations until an alternative ranking shows consistent positive τ. The "Best Ideas" (top 1/3/5) analysis in the backtest report should be interpreted with this caveat.

**Would move us:** If an alternative ranking signal (e.g., momentum, min(V,Q), or freshness) shows consistently positive τ over 30+ quarters.

---

## Review log

This log records each formal audit of the algorithm. The point is to make it visible how much has changed between audits, so the project's thinking is traceable over time.

### 2026-04-10 — Empirical component investigation (10 tests, 12 quarters)

**Scope.** Full classification replay of all ~420 stocks across 12 quarters (Q1 2023 to Q1 2026). Tested: classification gradient, F-gate, momentum gate, confidence gradient, VALUE TRAP validation, selectivity signal, win/loss asymmetry, sector-neutralized returns, repeat-pick persistence, conviction score ordering. Infrastructure built: `backtest/case_study.py`, `scripts/run_investigation.py`.

**Outcome.** Zero code changes to the algorithm. One README fix (asymmetry claim removed — unsupported by data). Nine findings logged in new [Empirical investigation](#empirical-investigation--component-effectiveness-april-2026) section. Stale docstring in `scoring/conviction.py:49` corrected.

**Key findings.** Momentum gate is the one clearly validated component (−1.9% delta, n=98). F-gate is neutral (n=17). Confidence gradient works in aggregate (HIGH +6.7% > MOD +5.4% > LOW +3.3%) but not per-quarter. Sector-neutralized alpha is near zero (+0.1%) — the screener tilts sectors, not picks stocks. Conviction ordering has slightly negative τ within CB. Win/loss asymmetry is 1.05× (essentially random). All findings are directional hypotheses at n=12 quarters.

**Audit triggered by.** User request to systematically investigate screener effectiveness and build evidence for case studies.

---

### 2026-04-12 — Selective sell strategy re-investigation

**Scope.** Re-ran the full 12-quarter investigation under the selective sell strategy (hold CB/WL/QGP/OQ, sell only VT/AVOID/OV, monitor HOLD for 1 quarter). Compared to original quarterly rebalance findings.

**Outcome.** Selective sell strategy significantly outperformed quarterly rebalance: CAGR +18.7% vs +11.2% (+7.5% improvement). Selection alpha flipped from -1.3% to +1.0%. Two investigation findings revised:
1. Win/loss asymmetry: 1.28x under selective sell (was 1.05x under quarterly rebalance)
2. Sector-neutral alpha: +0.5% under selective sell (was +0.1%)

Strategy document created at `docs/STRATEGY.md`. Selective sell simulation added to `backtest/portfolio.py`. 62-year Fama-French factor evidence case study added.

Also identified 6 scoring mechanism design issues (arbitrary weights, momentum redundancy, leverage tension, GP/Assets sector bias) — documented for future investigation, no code changes.

**Audit triggered by.** User investigation of optimal sell strategy and scoring validation.

---

### 2026-04-09 — Deep algorithm audit (third pass)

**Scope.** Every entry in [Kept decisions](#kept-decisions-actively-defended), [Rejected alternatives](#rejected-alternatives-considered-and-declined), and [Deferred changes](#deferred-changes-would-require-data-layer-work) was reviewed against primary academic sources (Piotroski 2000, Novy-Marx 2013, Carlisle 2014, Jegadeesh-Titman 1993, Jensen et al. 2023a, Schwartz & Hanauer 2024). Piotroski's 13.4% long-only and 23% long-short numbers were web-verified from independent secondary sources.

**Outcome.** Zero code changes. Three documentation fixes in `METHODOLOGY.md`:
1. §6.2 Piotroski F-gate attribution corrected (commit `a7d41f0`)
2. New §12 Backtest Conventions added with 7 sub-sections
3. Schwartz & Hanauer (2024) citation added to §11

**Why zero code changes.** The full reasoning is in the entries above, but the short version: every alternative considered either produced a more *academically reproducible* result (F3, F5, F7, F9, filing lag, weighting) without a confident improvement to strategy quality, or was a feature addition outside the project's scope (Magic Formula ROC), or required data that is not available (point-in-time constituents, EQIS), or re-tuned a parameter on the same data that justified the original choice (thresholds, weights). None of these cleared the bar of "confident this produces a better strategy."

**Audit triggered by.** User request to "make sure that you're confident about every single decision that we have made in the core algorithm engine."

---

<div align="center">

*This is a living document. When a future audit reaches a different conclusion on any entry, update the entry in place and add a new row to the review log above. Do not delete prior reasoning — preserve it so the project's thinking remains legible over time.*

</div>
