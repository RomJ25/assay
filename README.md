# Assay

S&P 500 value + quality stock screener. Tests every stock for cheapness (Earnings Yield) and financial health (Piotroski F-Score + Gross Profitability), then classifies into a 9-cell conviction matrix.

Based on three academically proven strategies:

- **Carlisle's Acquirer's Multiple** (EV/EBIT) — 17.9% CAGR over 44 years
- **Piotroski F-Score** — 13.4% annual outperformance over 20 years
- **Novy-Marx Gross Profitability** — predictive power equal to book-to-market ratio

## How It Works

**Value Score (0-100):** Ranks all stocks by Earnings Yield (EBIT / Enterprise Value). Cheapest stock = 100, most expensive = 0. Composite of 70% earnings yield rank + 30% free cash flow yield rank.

**Quality Score (0-100):** 50% Piotroski F-Score (9 binary financial health criteria, normalized) + 50% Gross Profitability (Gross Profit / Total Assets) percentile rank.

**Conviction Score:** Geometric mean of value and quality. Both must be high for a high score.

**9-Cell Matrix:**

|  | Quality High (>=70) | Quality Mid (40-70) | Quality Low (<40) |
|---|---|---|---|
| **Value High (>=70)** | CONVICTION BUY | WATCH LIST | VALUE TRAP |
| **Value Mid (40-70)** | QUALITY GROWTH PREMIUM | HOLD | AVOID |
| **Value Low (<40)** | OVERVALUED QUALITY | OVERVALUED | AVOID |

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Screen all S&P 500 stocks
python main.py

# Top 30 with extra columns
python main.py --top 30 --wide

# Show Piotroski criterion breakdown
python main.py --breakdown

# Exclude banks/insurance/REITs (recommended)
python main.py --exclude-financials

# Single stock analysis
python main.py --ticker AAPL --breakdown --wide

# Fresh data (bypass cache)
python main.py --refresh
```

## CLI Reference

| Flag | Description |
|------|-------------|
| `--ticker, -t` | Screen a single ticker (e.g., AAPL) |
| `--top N` | Show top N results (default: 20) |
| `--wide` | Wide table: adds F-Score, GP/A, P/E, 52-week high, sector |
| `--breakdown` | Show Piotroski 9-criterion pass/fail grid per stock |
| `--exclude-financials` | Remove banks, insurance, and REITs from the screen |
| `--refresh` | Bypass cache, fetch fresh data from Yahoo Finance |
| `--verbose, -v` | Debug logging |

## Output

**Console:** Rich-formatted tables grouped by classification (conviction buys, value traps, watch list).

**CSV:** `results/screen_YYYY-MM-DD.csv` — all stocks with scores, metrics, and Piotroski criterion breakdown.

**JSON:** `results/screen_YYYY-MM-DD.json` — same data as CSV, structured format.

## Confidence Levels

Each conviction buy is tagged HIGH, MODERATE, or LOW based on how far above the 70/70 threshold both scores are:

- **HIGH** — Both value and quality >= 85
- **MODERATE** — Both >= 75
- **LOW** — At least one score barely above 70

## Financial Sector Handling

Banks and insurance companies don't report operating income in a way that's comparable to other sectors. The `--exclude-financials` flag removes:

- **Real Estate** — all REITs (structurally distorted metrics, use FFO not earnings)
- **Financials without EBIT** — banks, insurance companies that lack operating income data

It keeps fintech and payment companies (PayPal, Mastercard, Visa, CBOE) that have normal financial statements.

## Project Structure

```
assay/
  main.py              # Pipeline orchestrator
  config.py            # All thresholds, paths, and settings
  data/
    fetcher.py         # DataFetcher: batched Yahoo Finance + yfinance fallback
    sp500.py           # S&P 500 list from Wikipedia
    cache.py           # SQLite cache with TTL
    providers/
      base.py          # FinancialData dataclass
      yahooquery_provider.py  # Primary data source
      yfinance_provider.py    # Fallback
  scoring/
    value_scorer.py    # Earnings Yield percentile ranking
    quality_scorer.py  # Piotroski + Gross Profitability composite
    conviction.py      # Geometric mean, 9-cell matrix, confidence
    filters.py         # Data quality checks
  quality/
    piotroski.py       # 9 binary criteria with detailed breakdown
    growth.py          # Revenue, margins, PEG (context only)
  models/
    dcf.py             # Discounted cash flow (context only)
    relative.py        # Sector-relative valuation (context only)
  output/
    console_report.py  # Rich terminal tables
    csv_report.py      # CSV + JSON export
  tests/               # 54+ tests
  results/             # Screen output (gitignored)
```

## Docker

```bash
# Build and run
docker compose up

# Or use the cron script (weekdays 6:30 PM ET)
# crontab -e
# 30 18 * * 1-5 /path/to/assay/scripts/run-daily.sh >> /tmp/assay.log 2>&1
```

## Data Sources

- **S&P 500 list:** Wikipedia (cached 7 days)
- **Fundamentals:** yahooquery (primary, annual statements), yfinance (fallback)
- **Prices:** yahooquery (cached 24 hours)

No API keys required. All data sources are free.

## Academic References

- Carlisle, T. (2014). *Deep Value: Why Activist Investors and Other Contrarians Battle for Control of Losing Corporations.* Wiley.
- Piotroski, J. (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research.
- Novy-Marx, R. (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics.

---

*This is a research tool, not financial advice. Past academic performance does not guarantee future results. Always do your own due diligence before making investment decisions.*
