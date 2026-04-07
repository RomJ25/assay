<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/ASSAY-S%26P%20500%20Screener-white?style=for-the-badge&labelColor=0d1117&color=58a6ff">
    <img alt="Assay" src="https://img.shields.io/badge/ASSAY-S%26P%20500%20Screener-black?style=for-the-badge&labelColor=f6f8fa&color=24292f">
  </picture>
</p>

<h3 align="center">
  A quantitative value + quality stock screener<br>
  built on three decades of academic research
</h3>

<p align="center">
  <a href="#the-mathematics">Mathematics</a> · 
  <a href="#quick-start">Quick Start</a> · 
  <a href="#the-conviction-matrix">Matrix</a> · 
  <a href="#cli-reference">CLI</a> · 
  <a href="docs/METHODOLOGY.md">Methodology</a> · 
  <a href="docs/ARCHITECTURE.md">Architecture</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/data-Yahoo%20Finance-7B1FA2?style=flat-square" alt="Yahoo Finance">
  <img src="https://img.shields.io/badge/API%20keys-none%20required-4caf50?style=flat-square" alt="No API keys">
  <img src="https://img.shields.io/badge/tests-54+-2196f3?style=flat-square" alt="Tests">
</p>

---

Assay screens every stock in the S&P 500 across two independent dimensions — **how cheap it is** and **how financially healthy it is** — then classifies each into a 9-cell conviction matrix. No black boxes, no proprietary signals. Every score traces back to published, peer-reviewed research.

> **Three strategies. Three decades of evidence. One screener.**

| Strategy | Academic Source | Track Record |
|:---|:---|:---|
| Acquirer's Multiple (EBIT/EV) | Carlisle, 2014 | **17.9% CAGR** over 44 years |
| Piotroski F-Score | Piotroski, 2000 | **13.4%** annual outperformance |
| Gross Profitability | Novy-Marx, 2013 | Predictive power = book-to-market |

---

## The Mathematics

Assay reduces the universe of 500 stocks to a small set of high-conviction ideas through a precise, two-dimensional ranking system. Every stock receives a **Value Score** and a **Quality Score**, each on a 0–100 scale, then a **Conviction Score** that requires *both* to be high.

### Value Dimension — *"How cheap is it?"*

Each stock is ranked by **Earnings Yield**, the inverse of the Acquirer's Multiple:

```
                    EBIT
Earnings Yield = ─────────
                    EV
```

where **EBIT** is operating income and **EV** is enterprise value (market cap + debt − cash). The cheapest stock gets rank 100, the most expensive gets rank 0.

A secondary signal — **Free Cash Flow Yield** (FCF / EV) — confirms that cheap earnings are backed by real cash generation:

```
Value Score = 0.70 × EY_percentile + 0.30 × FCF_percentile
```

> *For banks and financials without operating income, `1/P·E` is used as a proxy for earnings yield.*

### Quality Dimension — *"Is it financially healthy?"*

Quality combines two academically independent signals at equal weight:

**Signal 1 — Piotroski F-Score** (normalized 0–100)

Nine binary tests of financial strength, each worth one point:

| # | Criterion | Test |
|:-:|:---|:---|
| 1 | Profitability | Net Income > 0 |
| 2 | Cash Generation | Operating Cash Flow > 0 |
| 3 | Earnings Trend | ROA improving year-over-year |
| 4 | Accruals Quality | OCF > Net Income |
| 5 | Leverage | Debt-to-Assets ratio decreasing |
| 6 | Liquidity | Current Ratio increasing |
| 7 | Dilution | No new share issuance |
| 8 | Margins | Gross Margin expanding |
| 9 | Efficiency | Asset Turnover increasing |

```
F-Score (normalized) = (criteria passed / 9) × 100
```

**Signal 2 — Gross Profitability** (percentile rank)

Novy-Marx's factor, ranked across the full universe:

```
                     Gross Profit
Gross Profitability = ─────────────
                      Total Assets
```

> *For banks without gross profit, ROA (Net Income / Total Assets) is used as fallback.*

**Composite:**

```
Quality Score = 0.50 × F-Score + 0.50 × Profitability_percentile
```

If only one signal is available, a **20% penalty** is applied to prevent score inflation from incomplete data.

### Conviction Score — *"Should I act on this?"*

The geometric mean of both dimensions ensures a stock must rank well on **both** axes:

```
Conviction = √(Value × Quality)
```

This is the key mathematical insight. The geometric mean punishes imbalance:

| Value | Quality | Arithmetic Mean | **Geometric Mean** |
|:-----:|:-------:|:---------------:|:------------------:|
| 95 | 5 | 50 | **21.8** |
| 80 | 80 | 80 | **80.0** |
| 90 | 70 | 80 | **79.4** |
| 50 | 50 | 50 | **50.0** |

A stock that's extremely cheap but financially distressed (95, 5) scores only **21.8** — not 50. Both dimensions must be strong.

---

## The Conviction Matrix

Stocks are classified into a 3×3 grid based on their Value and Quality scores:

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │            Q U A L I T Y   D I M E N S I O N               │
                    │                                                             │
                    │    High (≥ 70)          Mid (40–70)        Low (< 40)       │
         ┌──────────┼───────────────────┬──────────────────┬──────────────────────┤
         │ High     │                   │                  │                      │
  V      │ (≥ 70)  │  ★ CONVICTION BUY │   WATCH LIST     │   ⚠ VALUE TRAP      │
  A      │         │                   │                  │                      │
  L      ├─────────┼───────────────────┼──────────────────┼──────────────────────┤
  U      │ Mid     │  QUALITY GROWTH   │                  │                      │
  E      │ (40–70) │  PREMIUM          │   HOLD           │   AVOID              │
         │         │                   │                  │                      │
         ├─────────┼───────────────────┼──────────────────┼──────────────────────┤
         │ Low     │  OVERVALUED       │                  │                      │
         │ (< 40)  │  QUALITY          │   OVERVALUED     │   AVOID              │
         └─────────┴───────────────────┴──────────────────┴──────────────────────┘
```

### Confidence Levels

Every Conviction Buy is tagged with a confidence level based on how far *both* scores exceed the 70-point threshold:

| Confidence | Requirement | Interpretation |
|:---|:---|:---|
| **HIGH** | Both scores ≥ 85 | Strong margin of safety on both axes |
| **MODERATE** | Both scores ≥ 75 | Solid positioning, minor risk |
| **LOW** | At least one barely > 70 | Borderline — needs further due diligence |

### F-Score Gate

An additional safety check: if a stock's raw Piotroski F-Score is below **5 out of 9**, it is downgraded from CONVICTION BUY to WATCH LIST — regardless of its composite quality score. This reflects Piotroski's finding that the strongest outperformance occurs at F ≥ 5.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Screen all S&P 500 stocks (default: top 20)
python main.py

# Top 30 results with extended metrics
python main.py --top 30 --wide

# Deep-dive into a single stock
python main.py --ticker AAPL --breakdown --wide

# Exclude banks, insurance, REITs (recommended for cleaner comparisons)
python main.py --exclude-financials

# Force fresh data (bypass 7-day cache)
python main.py --refresh
```

---

## CLI Reference

| Flag | Description |
|:---|:---|
| `--ticker, -t SYMBOL` | Analyze a single stock instead of the full S&P 500 |
| `--top N` | Show top N results (default: 20) |
| `--wide` | Extended table: F-Score, GP/A, P/E, 52-week high, sector |
| `--breakdown` | Show all 9 Piotroski criteria as pass/fail per stock |
| `--exclude-financials` | Remove banks, insurance, and REITs from the screen |
| `--refresh` | Bypass cache — fetch fresh data from Yahoo Finance |
| `--verbose, -v` | Enable debug logging |

---

## Output Formats

| Format | Location | Content |
|:---|:---|:---|
| **Console** | Terminal | Rich-formatted tables grouped by classification |
| **CSV** | `results/screen_YYYY-MM-DD.csv` | All stocks with scores, metrics, 9 Piotroski criteria |
| **JSON** | `results/screen_YYYY-MM-DD.json` | Structured data with full breakdown objects |

---

## Financial Sector Handling

Banks, insurance companies, and REITs have fundamentally different financial structures. The `--exclude-financials` flag removes:

- **Real Estate** — REITs use FFO, not earnings; standard metrics are structurally distorted
- **Banks & Insurance** — lack comparable operating income; use 1/P·E as fallback when included

Companies with normal financial statements (Visa, Mastercard, PayPal, CBOE) are retained.

---

## Architecture

```
assay/
│
├── main.py                          # 7-step pipeline orchestrator
├── config.py                        # All thresholds, rates, and paths
│
├── data/                            # ── Data Layer ──────────────────
│   ├── fetcher.py                   #    Batched fetching, caching, fallback
│   ├── sp500.py                     #    S&P 500 list (Wikipedia, cached 7d)
│   ├── cache.py                     #    SQLite with per-type TTL
│   └── providers/
│       ├── base.py                  #    FinancialData dataclass (66 fields)
│       ├── yahooquery_provider.py   #    Primary: batch API, 8 workers
│       └── yfinance_provider.py     #    Fallback: single-threaded
│
├── scoring/                         # ── Scoring Layer ───────────────
│   ├── value_scorer.py              #    Earnings Yield percentile ranking
│   ├── quality_scorer.py            #    Piotroski + Profitability composite
│   ├── conviction.py                #    Geometric mean, 9-cell classification
│   └── filters.py                   #    Data quality pre-checks
│
├── quality/                         # ── Quality Models ──────────────
│   ├── piotroski.py                 #    9 binary criteria + breakdown
│   ├── growth.py                    #    Revenue, margins, PEG (display only)
│   └── base.py                      #    Abstract QualityModel
│
├── models/                          # ── Valuation Context ───────────
│   ├── dcf.py                       #    DCF with bear/base/bull scenarios
│   ├── relative.py                  #    Sector-relative multiples + PEG
│   └── base.py                      #    ValuationModel + ValuationResult
│
├── output/                          # ── Reporting ───────────────────
│   ├── console_report.py            #    Rich terminal tables
│   └── csv_report.py                #    CSV + JSON export
│
├── tests/                           # 54+ unit tests
├── scripts/run-daily.sh             # Cron runner (weekdays 6:30 PM ET)
└── Dockerfile                       # Python 3.13-slim container
```

---

## Docker

```bash
# Build and run with Docker Compose
docker compose up

# Automated daily screening (weekdays, 30 min after market close)
# Add to crontab:
# 30 18 * * 1-5 /path/to/assay/scripts/run-daily.sh >> /tmp/assay.log 2>&1
```

---

## Data Pipeline

```
  Wikipedia            Yahoo Finance API           yfinance
     │                       │                        │
     ▼                       ▼                        ▼
 ┌────────┐          ┌──────────────┐          ┌────────────┐
 │ S&P500 │          │  yahooquery   │          │  Fallback   │
 │  List  │          │  (85/batch)   │◄────────►│  Provider   │
 └───┬────┘          └──────┬───────┘          └─────┬──────┘
     │                      │                        │
     ▼                      ▼                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │                    SQLite Cache                          │
 │  S&P 500: 7d TTL  │  Fundamentals: 7d  │  Prices: 24h   │
 └──────────────────────────┬───────────────────────────────┘
                            │
                            ▼
 ┌──────────────────────────────────────────────────────────┐
 │                   Scoring Engine                         │
 │                                                          │
 │  Value Score ────────────┐                               │
 │  (EY + FCF percentile)   ├──► √(V × Q) ──► Classify     │
 │  Quality Score ──────────┘                               │
 │  (Piotroski + GP/A)         Conviction    9-Cell Matrix  │
 └──────────────────────────────┬───────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
               ┌────────┐ ┌────────┐ ┌──────────┐
               │Console │ │  CSV   │ │   JSON   │
               │ (Rich) │ │ Export │ │  Export  │
               └────────┘ └────────┘ └──────────┘
```

**No API keys required.** All data sources are free and keyless.

---

## Academic References

1. **Carlisle, T.** (2014). *Deep Value: Why Activist Investors and Other Contrarians Battle for Control of Losing Corporations.* Wiley.
   — Acquirer's Multiple: 17.9% CAGR, 1973–2017.

2. **Piotroski, J.D.** (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research, 38, 1–41.
   — F-Score: 13.4% annual outperformance among high book-to-market firms.

3. **Novy-Marx, R.** (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics, 108(1), 1–28.
   — Gross Profitability (GP/Assets) predicts cross-section of returns as well as book-to-market.

---

## Further Reading

| Document | Description |
|:---|:---|
| [**Methodology**](docs/METHODOLOGY.md) | Deep dive into the mathematical framework, scoring formulas, and design decisions |
| [**Architecture**](docs/ARCHITECTURE.md) | System design, data flow, caching strategy, and module responsibilities |
| [**Contributing**](CONTRIBUTING.md) | Development setup, testing, and contribution guidelines |

---

<p align="center">
  <sub>
    <em>This is a research tool, not financial advice. Past academic performance does not guarantee future results.<br>Always do your own due diligence before making investment decisions.</em>
  </sub>
</p>
