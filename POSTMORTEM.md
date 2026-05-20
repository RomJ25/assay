# Post-Mortem — I Built a Transparent Quant Screener, Then Proved I Should Just Buy the Index Fund

*A student's honest account of building Assay, stress-testing it, and reaching a conclusion I did not want.*

---

## The conclusion, up front

Assay is a transparent, long-only value-and-quality stock screener. I built it to find undervalued, financially healthy companies in the US large-cap universe, with every score traceable to observable data — no machine learning, no black box, no "trust me."

It works as designed. It is also not something I should run with my own money, and this document explains — with evidence — why.

The short version: I subjected Assay to the most adversarial testing I could design, and it did not clear the bar. Its central output, the conviction classification, did not reliably predict returns. When I went looking in the academic and practitioner literature for whether *any* retail-implementable screen of this kind beats a low-cost factor ETF after real-world frictions, the answer came back a clean and well-documented *no*.

So this repository is being open-sourced not as a product, but as a finished research project and an honest record of what I learned. If you are looking for a screener to run your savings through, the most useful thing this project can tell you is: **buy a broad index fund or a factor ETF, and spend your energy on something with a real edge.** That is not a cynical conclusion. It is the conclusion the evidence supports, and arriving at it was the point.

---

## What I set out to build

The idea behind Assay was simple and, I still think, reasonable. Decades of academic research document that cheap stocks (value) and profitable, financially healthy stocks (quality) have historically earned premiums. Joseph Piotroski's F-Score separates financially strong firms from weak ones. Robert Novy-Marx showed gross profitability predicts returns about as well as book-to-market. Tobias Carlisle's work on the Acquirer's Multiple, and the broader Fama-French factor literature, all point in the same direction.

Most retail stock screeners take this research and produce a list of names every time you run them. I wanted to build something more disciplined. Assay only classifies a stock as a "research candidate" when value and quality are *both* high at the same time — enforced with a geometric mean, so a great score on one dimension cannot paper over a terrible score on the other. It applies gates for financial health (Piotroski F-Score ≥ 6/9) and momentum (not in freefall). And — the feature I was proudest of — it is allowed to return *nothing*. For five consecutive quarterly rebalances, from March 2022 through March 2023, Assay produced zero picks: it could not find a single stock where cheapness, quality, and financial health all aligned. It did not predict the drawdown that followed. It simply refused to pretend.

That refusal-to-pretend was the whole philosophy. I did not want a prediction engine. I wanted a disciplined filter whose every decision I could audit and disagree with. The goal was to put my own (modest) savings behind it and let it compound.

## What I got right: building falsifiability in from the start

If there is one thing in this project I would defend without reservation, it is that I built it to be *falsifiable* — and then actually ran the tests that could falsify it.

Three decisions stand out:

**A permanent decision log.** Every algorithm choice — every value weight, every gate threshold, every alternative considered and rejected — is recorded in `docs/DESIGN_DECISIONS.md` with its academic source and the reasoning. The point was to make it impossible to quietly re-litigate a settled question or to forget why something was chosen. A future version of me auditing this project starts from a shared baseline, not a blank page.

**A survivorship-bias correction I did not want to find.** An early version of the backtest used the *current* S&P 500 constituent list and replayed it backward through history. This is a classic, seductive error: it silently assumes you would have known, in 2022, which companies would still be in the index in 2026. When I corrected it to use point-in-time constituents, the result was brutal. In one backtest window, a single stock — Super Micro Computer (SMCI), added to the S&P 500 only in March 2024 — accounted for 197% of the strategy's claimed alpha. The "edge" was substantially an artifact of look-ahead bias. I could have buried that. Instead it is documented, and the survivorship-free backtest is now the default.

**A statistical-rigor framework that judged my own findings.** Late in the project I added a Bonferroni-correction framework (`docs/DESIGN_DECISIONS.md`, "Statistical-rigor framework"). At my actual sample size — roughly 16 quarters of backtest data — the standard error of an annualized alpha estimate is about ±1.8% per year. Any finding smaller than that is not statistically distinguishable from zero. And because I had run a family of about five component tests, honest significance requires a t-statistic around 2.94, not the naive 2.0. I built the tool that would tell me most of my results were noise. Then I let it.

I am genuinely glad I did all three. They are the reason this post-mortem can be honest instead of wishful.

## The reckoning: what the evidence actually said

Here is what the testing showed, stated plainly.

**The conviction classification does not predict returns within itself.** The "conviction score" ranks research candidates. Across the backtest, the Kendall rank correlation between a stock's conviction score and its next-quarter return, *within* the research-candidate bucket, was about −0.04 — essentially zero, and slightly negative. Higher conviction did not mean higher expected return. I had been careful never to market "highest conviction" as "best pick," and the data vindicated that caution: conviction is a threshold mechanism, not a ranking signal.

**The classification gradient inverts about half the time.** This is the finding that mattered most. Assay sorts the universe into buckets from "research candidate" (best) down to "avoid" (worst). For the system to be useful, research candidates should, on average, beat the names it flags as avoid. Across eleven measured quarters, research candidates beat avoid in only **six** of them — barely better than a coin flip — and the *average* spread was **−0.8%**. In the worst quarter, Q1 2024, during the Magnificent Seven growth rally, the gradient fully inverted: the "avoid" bucket was the best performer (+2.3%) and the research-candidate bucket was the worst (−5.4%). The system did not break; it did exactly what it was designed to do. The market simply did not reward what it selects for, and it does not reliably reward it in any given quarter.

**Four of five component findings fail significance.** When I ran every component improvement — the revenue gate, the safety score, the selective-sell rule, sector-neutral construction, the buy-threshold tuning — through the Bonferroni framework, four of the five produced t-statistics below 1.0. They are statistically indistinguishable from zero. The fifth, a buy-threshold tweak, cleared the bar only barely, and only on a portfolio so small (about four stocks per quarter) that overfitting is the more likely explanation than skill. By my own honest standard, the system has not demonstrated an exploitable edge.

**The out-of-sample test failed.** I built a walk-forward validation harness to check whether the selective-sell strategy — hold winners, cut losers — beats simple quarterly rebalancing out-of-sample. It does not consistently do so. The logic is academically sound; the specific rules, on my data, did not survive honest validation.

None of this means the underlying academic factors are fake. It means *this implementation, on this universe, at this sample size, did not capture them in a way I could verify.* That distinction matters, and I will come back to it.

## The deeper question: even a working screener would not have mattered

For a while I told myself the fix was more work — a different universe, a continuous multi-factor model, more data. Maybe. But I eventually asked a harder question: *suppose the screener did capture a real edge. Would it then make me money?*

The honest answer, from the published literature, is still no — and this is the part I most wish I had understood at the start.

**Frictions eat the premium.** A factor screen requires turnover: stocks migrate in and out of the buckets, so you trade. Novy-Marx and Velikov's 2016 study in the *Review of Financial Studies* found that anomaly strategies with more than 50% monthly turnover generally fail to produce statistically significant net returns once realistic trading costs are included. Small-cap value stocks — exactly where the factor premium is supposed to be strongest — carry bid-ask spreads that can run 80–100 basis points versus 5–10 for large caps. Every rebalance pays that spread.

**Taxes eat more.** For a taxable investor, turnover triggers capital gains. Research by Arnott and colleagues found that an active strategy needs to clear a pre-tax alpha hurdle of *more than 2% per year* simply to break even, after taxes, against a low-turnover passive index. Most factor premiums, out-of-sample and net of costs, do not consistently clear that.

**Publication decays the edge.** McLean and Pontiff (2016, *Journal of Finance*) showed that documented anomalies decay about 58% after publication, as the market arbitrages them away. A screener built entirely on *published* academic factors — which Assay is, by design and on principle — is fishing in the most crowded water there is.

**The ETF wrapper wins structurally, not by being smarter.** A low-cost factor ETF such as Avantis' AVUV captures the same value-and-profitability premiums Assay targets. It charges 0.25% per year. And critically, through the in-kind creation/redemption mechanism (IRC §852(b)(6)), it rebalances *without* triggering the capital gains taxes that a retail investor doing the same trades cannot avoid. In 2023, about a third of active mutual funds distributed taxable capital gains; only about 4% of active ETFs did. A retail investor running their own screen simply cannot replicate that structural tax advantage. The ETF does not need a better algorithm. It has a better *container*.

Put the friction stack together — spreads, tax drag, the behavior gap that Morningstar documents for investors in volatile factor funds — and a retail do-it-yourself screen faces a 3–6% annual headwind that a tax-advantaged ETF does not. That is far larger than any edge a transparent, published-factor screen could plausibly deliver.

And then there is scale. I am a student. The capital I could realistically deploy is small. Even if Assay somehow delivered a heroic 5% of annual alpha, on a few thousand dollars that is a few hundred dollars a year. At my stage of life, my financial future is not determined by portfolio returns on a small balance — it is determined by what I learn and earn. Optimizing the screener was, in the most literal sense, optimizing the wrong variable.

## The honest conclusion

So here is what I actually concluded, and what I would tell anyone in my position:

**Put your savings in a broad, low-cost index fund or a factor ETF, and leave them there.** Not because indexing is glamorous, but because the structural math — frictions, taxes, the ETF wrapper, the behavior gap — is overwhelmingly in its favor and against a hand-run screen. This is not defeatism. It is the same evidence-respecting attitude that made me build the Bonferroni framework in the first place, applied to the question one level up.

**Assay was not a failure. The expectation attached to it was.** I built it expecting it to make money. Judged as a money-making engine, it does not work, and the evidence says no screener of its kind would. But judged as what it actually was — a student's research project — it succeeded completely. It taught me how to build a backtest that does not lie to itself, how survivorship bias hides in plain sight, what statistical significance actually requires, how to read primary academic sources, how to construct a full-stack data application, and — hardest of all — how to run the experiment that could prove my own idea wrong, and then believe the result.

That last skill is rarer than a working trading strategy, and it is worth more.

## What I would tell someone starting a similar project

A few things I wish I had known:

1. **Decide what would falsify your idea before you build it, and write the test down first.** I did this eventually. Doing it on day one would have saved months.

2. **Survivorship bias is not a footnote. It is probably the difference between your backtest and reality.** Use point-in-time data or assume your results are inflated.

3. **A small sample is not a small problem.** Sixteen quarters feels like a lot of data when you are staring at it. Statistically, it is almost nothing. Compute the noise floor early.

4. **Distinguish "the academic factor is real" from "my implementation captured it."** Both can be true; usually only the first is.

5. **Ask the question one level up.** Not "is my screener good?" but "would a good screener even win, after costs, taxes, and the alternatives?" If the answer to the second question is no, the first question does not matter.

6. **The most valuable output of a research project can be a clear negative result.** It just has to be an *honest* one.

## How to read this repository

- **`docs/METHODOLOGY.md`** — exactly how every score is computed.
- **`docs/DESIGN_DECISIONS.md`** — every algorithm choice, alternative considered, and the statistical-rigor framework. This is the heart of the project's reasoning.
- **`docs/CAPITAL_RESEARCH_PLAN.md`** — my own pre-committed honesty: the written verdict, before this post-mortem, that the algorithm was not capital-ready.
- **`docs/CASE_STUDIES/`** — concrete quarters, including `2024-Q1_when_the_market_left_us_behind.md`, the honest analysis of the worst quarter.
- **`docs/STRATEGY.md`** — the intended buy/hold/sell logic, with its in-sample caveats stated plainly.

The code runs. The screener is real, the backtest is survivorship-free by default, and the tests pass. You are welcome to use any of it. Just do so understanding what the evidence in these documents says — including the evidence that you would, in all likelihood, be better served by an index fund.

That is the most honest sentence I can end on, and honesty was always the point.

---

*This project is released under the MIT License. It is a research and learning artifact, not financial advice. Past academic performance does not guarantee future results.*
