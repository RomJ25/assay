# Assay

**A system that only acts when the evidence is aligned — and stays silent when it isn't.**

*An S&P 500 value + quality screener — a first filter for research, not a trading signal. Built for investors who would rather see zero picks than a forced shortlist of twenty.*

Most screeners give you a list every time you run them. Assay is different. For five consecutive quarterly rebalances from March 2022 through March 2023, it produced zero picks. In the worst of those quarters, the S&P 500 fell 16% — Assay had nothing to buy. It didn't predict the crash. It simply couldn't find a single stock where cheapness, quality, and financial health all aligned. That willingness to say "nothing qualifies" is the system's most distinctive behavior.

When Assay does surface a name, you know:
- It's **cheap** relative to every other S&P 500 stock (Value score >= 70, driven by Earnings Yield with a Free Cash Flow reality check)
- It's **financially healthy** (Piotroski F-Score >= 6/9 — positive cash flow, improving returns, no dilution)
- It's **profitable** (Quality score >= 70, anchored in Gross Profitability and the Piotroski criteria)
- It's **not in freefall** (passed the momentum gate)
- And both cheapness and quality are high **at the same time** (geometric mean prevents one good dimension from masking a terrible one)

The result is a short list of conviction buys — typically 15-25 in normal markets, occasionally zero when nothing qualifies — where every name has survived every filter. Your job is the last mile: pick 2-3 from that list using your own judgment about the business, the sector, and the timing.

Assay doesn't predict prices. It doesn't forecast earnings. It doesn't use machine learning. Every score traces to observable, auditable data — nine binary Piotroski criteria, two percentile ranks, one geometric mean. You can see exactly why every stock is where it is and decide whether you agree.

## How It Works

**Value Score (0-100):** Percentile rank by Earnings Yield (EBIT / Enterprise Value). Cheapest = 100. Composite of 70% earnings yield + 30% free cash flow yield. Negative EBIT/FCF rank at the bottom, not excluded.

**Quality Score (0-100):** 50% Piotroski F-Score (9 binary financial health criteria, normalized) + 50% Gross Profitability (GP / Assets) percentile rank. Negative profitability ranks at the bottom, not excluded.

**Conviction Score:** Geometric mean of value and quality — both must be high. A stock that's very cheap but low quality (value trap) gets punished. A stock that's high quality but expensive (overvalued quality) also gets punished.

**Gates:** Minimum F-Score of 6/9 and bottom-25% momentum both downgrade a CONVICTION BUY to WATCH LIST.

**Classification Matrix:**

|  | Quality High (>=70) | Quality Mid (40-70) | Quality Low (<40) |
|---|---|---|---|
| **Value High (>=70)** | CONVICTION BUY | WATCH LIST | VALUE TRAP |
| **Value Mid (40-70)** | QUALITY GROWTH PREMIUM | HOLD | AVOID |
| **Value Low (<40)** | OVERVALUED QUALITY | OVERVALUED | AVOID |

**Trajectory Score:** Measures fundamental improvement (ROA change, margin change, deleveraging, buybacks) combined with 12-month price momentum. Used as a visible tie-breaker within conviction buys — not hidden inside the score.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Screen all S&P 500 stocks (financials excluded by default)
python main.py

# Top 30 with extra columns and Piotroski breakdown
python main.py --top 30 --wide --breakdown

# Include banks/insurance/REITs
python main.py --include-financials

# Single stock deep dive
python main.py --ticker AAPL --breakdown --wide

# Run historical backtest (4 years, 10bps transaction costs)
python main.py --backtest --backtest-years 4 --tcost-bps 10

# Sector-relative scoring (70% absolute + 30% within-sector rank)
python main.py --sector-relative

# Fresh data (bypass cache)
python main.py --refresh
```

## CLI Reference

| Flag | Description |
|------|-------------|
| `--ticker, -t` | Screen a single ticker (e.g., AAPL) |
| `--top N` | Show top N results (default: 20) |
| `--wide` | Wide table: adds FCF yield, P/E, Piotroski breakdown columns |
| `--breakdown` | Show Piotroski 9-criterion pass/fail grid per stock |
| `--include-financials` | Include banks, insurance, and REITs (excluded by default) |
| `--sector-relative` | Blend 70% absolute + 30% within-sector percentile for value score |
| `--backtest` | Run historical backtest instead of live screen |
| `--backtest-years N` | Years to backtest (default: 4) |
| `--tcost-bps N` | Transaction cost per rebalance in basis points (default: 0) |
| `--refresh` | Bypass cache, fetch fresh data |
| `--verbose, -v` | Debug logging |

## Output

**Console:** Rich-formatted tables sorted by conviction score, with trajectory as visible tie-breaker. Conviction buys show confidence level (HIGH/MODERATE/LOW).

**CSV:** `results/screen_YYYY-MM-DD.csv` — all stocks with scores, metrics, trajectory, and Piotroski criterion breakdown. Sorted by classification bucket, then conviction.

**JSON:** `results/screen_YYYY-MM-DD.json` — same data, structured format.

**Backtest:** Shows full portfolio AND concentrated "Best Ideas" analysis (top 1/3/5 picks), grounded in Cohen, Polk & Silli research. Includes statistical caveat when sample size is below 30 quarters.

## Academic Foundation

- **Carlisle** — Acquirer's Multiple (EV/EBIT): 17.9% CAGR over 44 years
- **Piotroski** — F-Score: separates winners from losers within value stocks (7.5% annual improvement). Effect is strongest in small/mid caps; reduced but present in S&P 500 large caps.
- **Novy-Marx** — Gross Profitability: predictive power equal to book-to-market ratio
- **Cohen, Polk & Silli** — "Best Ideas": highest-conviction positions outperform by 2.8-4.5% per year; the rest of the portfolio shows no alpha

## What This Is Not

This is not a prediction engine. It does not forecast prices, estimate fair value for ranking, or use machine learning. The conviction score tells you where cheapness and quality overlap — it does not tell you which stock will outperform the most. In our 12-quarter component investigation (Q1 2023–Q1 2026), individual CB picks beat the universe mean 52% of the time with a win/loss magnitude ratio of 1.05×. The screener's value appears to come from systematic sector tilting toward cheap, quality sectors rather than individual stock selection within sectors. It is a disciplined filter — not an alpha engine.

Financials (banks, insurance, REITs) are excluded by default because the EBIT/EV model is structurally wrong for them. Use `--include-financials` to override, understanding that these stocks use a 1/PE fallback for value scoring.

**131 tests. No API keys required. All data sources free.**

## Case Studies

Individual market events are not evidence — the backtest is. These case studies exist only to illustrate, in concrete terms, the kind of behavior the engine is designed to exhibit when a specific day exposes the mechanism clearly.

- [`docs/CASE_STUDIES/2026-04-08_ceasefire.md`](docs/CASE_STUDIES/2026-04-08_ceasefire.md) — Iran ceasefire rally. The 2026-04-07 screen held zero Energy in CONVICTION BUY; when WTI crashed ~15% the next morning on the ceasefire announcement, AVOID was the worst-performing bucket in the universe, the confidence gradient (HIGH/MODERATE/LOW) was cleanly monotonic, and 19 of 20 CBs closed positive.

## Data Sources

- **S&P 500 list:** Wikipedia (cached 7 days)
- **Fundamentals:** yahooquery (primary), yfinance (fallback) — annual statements
- **Prices:** yfinance (cached 24 hours)

## References

- Piotroski, J. (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research.
- Novy-Marx, R. (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics.
- Carlisle, T. (2014). *Deep Value.* Wiley.
- Cohen, R., Polk, C., & Silli, B. (2010). *Best Ideas.* Working Paper, London School of Economics.

---

*Research tool for idea generation. Not financial advice. Past academic performance does not guarantee future results.*
