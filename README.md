<div align="center">

# A S S A Y

**Quantitative Value + Quality Stock Screener for the S&P 500**

*Three decades of academic research. Zero black boxes. One screener.*

---

[![Python](https://img.shields.io/badge/python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Data](https://img.shields.io/badge/data-Yahoo%20Finance-7B1FA2?style=for-the-badge)](https://finance.yahoo.com)
[![API Keys](https://img.shields.io/badge/API%20keys-none%20required-2ea44f?style=for-the-badge)](.)
[![Tests](https://img.shields.io/badge/tests-54+-2196f3?style=for-the-badge)](tests/)

[**Mathematics**](#-the-mathematics) ·
[**Conviction Matrix**](#-the-conviction-matrix) ·
[**Quick Start**](#-quick-start) ·
[**CLI**](#-cli-reference) ·
[**Methodology**](docs/METHODOLOGY.md) ·
[**Architecture**](docs/ARCHITECTURE.md)

</div>

---

Assay screens every stock in the S&P 500 across two independent dimensions — **how cheap it is** and **how financially healthy it is** — then classifies each into a conviction matrix that separates real opportunities from traps.

Every score traces back to published, peer-reviewed research:

| Strategy | Paper | Evidence |
|:---|:---|:---|
| **Acquirer's Multiple** (EBIT/EV) | Carlisle, 2014 | **17.9% CAGR** over 44 years (1973-2017) |
| **Piotroski F-Score** | Piotroski, 2000 | **13.4%/yr** outperformance over 20 years |
| **Gross Profitability** (GP/A) | Novy-Marx, 2013 | Predictive power equal to book-to-market |
| **Momentum Gate** | Jegadeesh & Titman, 1993 | **+2.8%/yr** from excluding bottom quartile |

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/math-symbols.svg"> The Mathematics

Every stock receives a **Value Score** and a **Quality Score** on a 0-100 scale. These combine into a single **Conviction Score** via geometric mean, which mathematically enforces that *both* must be high.

### Value Dimension — *How cheap is it?*

The primary signal is **Earnings Yield**, the inverse of the Acquirer's Multiple:

```
              EBIT                              FCF
    EY  =  ────────              FCF Yield  =  ────────
               EV                                EV
```

> **EBIT** = Operating Income &nbsp;&nbsp;|&nbsp;&nbsp; **EV** = Market Cap + Debt - Cash &nbsp;&nbsp;|&nbsp;&nbsp; **FCF** = Operating Cash Flow - CapEx

Both metrics are converted to **percentile ranks** across the full S&P 500 universe, then blended:

```
    Value Score  =  0.70 × EY_percentile  +  0.30 × FCF_percentile
```

The 70/30 weighting reflects earnings yield as the primary academically-validated signal (Carlisle), with FCF yield as a cash-reality check. EBIT/EV is preferred over P/E because it is **capital-structure neutral** — it compares operating profit against the true total cost of acquiring the business.

> *For banks without operating income, `1/P·E` serves as a proxy for earnings yield.*

### Quality Dimension — *Is it financially healthy?*

Quality blends two independent academic signals at equal weight:

**Signal 1 — Piotroski F-Score** &nbsp; Nine binary tests of financial strength:

```
    PROFITABILITY               LEVERAGE & LIQUIDITY          EFFICIENCY
    ─────────────               ────────────────────          ──────────
    F₁  Net Income > 0          F₅  Debt ratio ↓             F₈  Gross margin ↑
    F₂  Cash Flow > 0           F₆  Current ratio ↑          F₉  Asset turnover ↑
    F₃  ROA improving           F₇  No share dilution
    F₄  Cash Flow > Net Income
```

```
    F-Score (normalized)  =  (criteria passed / 9)  ×  100
```

**Signal 2 — Gross Profitability** &nbsp; Novy-Marx's factor, percentile-ranked:

```
                    Gross Profit
    Profitability = ─────────────        (fallback: NI / Assets for banks)
                    Total Assets
```

**Composite:**

```
    Quality Score  =  0.50 × F-Score  +  0.50 × Profitability_percentile
```

When only one signal is available, a **20% penalty** applies: `score × 0.80`

### Conviction Score — *Should I act on this?*

The **geometric mean** of both dimensions:

```
    Conviction  =  √( Value × Quality )
```

This is the core mathematical insight. The geometric mean **punishes imbalance** — a direct consequence of the AM-GM inequality (`√(VQ) ≤ (V+Q)/2`, equality iff `V = Q`):

```
    ┌────────────────────────────────────────────────────────────────┐
    │   Value    Quality    Arithmetic Mean    Geometric Mean        │
    │   ─────    ───────    ───────────────    ──────────────        │
    │    95         5             50              21.8  ← penalized  │
    │    50        50             50              50.0                │
    │    80        80             80              80.0  ← rewarded   │
    │    90        70             80              79.4                │
    │    95        95             95              95.0                │
    └────────────────────────────────────────────────────────────────┘
```

A stock that's extremely cheap but financially distressed **(95, 5)** scores only **21.8**, not 50. Both dimensions must be strong.

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/grid-3x3.svg"> The Conviction Matrix

Stocks are classified into a **3 x 3 grid** based on where their Value and Quality scores fall:

```
                          Q U A L I T Y
                   High (≥70)      Mid (40-70)      Low (<40)
              ┌────────────────┬────────────────┬────────────────┐
   V   High   │                │                │                │
   A  (≥70)   │  ★ CONVICTION  │   WATCH LIST   │  ⚠ VALUE TRAP  │
   L          │     BUY        │                │                │
   U          ├────────────────┼────────────────┼────────────────┤
   E   Mid    │   QUALITY      │                │                │
      (40-70) │   GROWTH       │     HOLD       │    AVOID       │
              │   PREMIUM      │                │                │
              ├────────────────┼────────────────┼────────────────┤
       Low    │  OVERVALUED    │                │                │
      (<40)   │  QUALITY       │  OVERVALUED    │    AVOID       │
              │                │                │                │
              └────────────────┴────────────────┴────────────────┘
```

### Confidence Levels

Every **Conviction Buy** receives a confidence tag based on margin above the 70-point threshold:

| Level | Requirement | Meaning |
|:---:|:---|:---|
| **HIGH** | Both ≥ 85 | Strong margin of safety on both axes |
| **MODERATE** | Both ≥ 75 | Solid positioning, minor risk |
| **LOW** | At least one barely > 70 | Borderline — needs further diligence |

### Safety Gates

Three independent gates prevent false positives:

```
    Gate 1 ─ F-Score Minimum     If raw F < 6 out of 9  →  downgrade to WATCH LIST
    Gate 2 ─ Momentum Filter     If bottom 25% momentum →  downgrade to WATCH LIST
    Gate 3 ─ Data Quality        Must have price, revenue, and net income to rank
```

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/rocket.svg"> Quick Start

```bash
pip install -r requirements.txt

python main.py                            # Screen all S&P 500, top 20
python main.py --top 30 --wide            # Top 30 with extended metrics
python main.py --ticker AAPL --breakdown  # Deep-dive single stock
python main.py --exclude-financials       # Remove banks, insurance, REITs
python main.py --refresh                  # Bypass cache, fresh data
python main.py --backtest                 # 4-year historical backtest
python main.py --backtest --backtest-years 10  # 10-year backtest
```

### Docker

```bash
docker compose up                         # Build and run
```

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/terminal-2.svg"> CLI Reference

| Flag | Description |
|:---|:---|
| `--ticker, -t SYMBOL` | Analyze a single stock instead of the full S&P 500 |
| `--top N` | Number of results to display (default: 20) |
| `--wide` | Extended table: F-Score, GP/A, P/E, 52-week high, sector |
| `--breakdown` | Show all 9 Piotroski criteria as pass/fail per stock |
| `--exclude-financials` | Remove banks, insurance, and REITs from the screen |
| `--refresh` | Bypass cache — fetch fresh data from Yahoo Finance |
| `--backtest` | Run historical backtest instead of live screen |
| `--backtest-years N` | Number of years to backtest (default: 4) |
| `--verbose, -v` | Enable debug logging |

### Output Formats

| Format | Location | Content |
|:---|:---|:---|
| **Console** | Terminal | Rich-formatted tables grouped by classification |
| **CSV** | `results/screen_YYYY-MM-DD.csv` | All stocks with 37 columns of scores & metrics |
| **JSON** | `results/screen_YYYY-MM-DD.json` | Full structured data with breakdown objects |

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/building-bank.svg"> Financial Sector Handling

Banks, insurance companies, and REITs have fundamentally different financial structures. The `--exclude-financials` flag removes sectors where standard metrics are structurally distorted:

- **Real Estate** — REITs use FFO, not earnings
- **Banks & Insurance** — lack comparable operating income; use `1/P·E` as fallback when included

Companies with normal financial statements (Visa, Mastercard, PayPal) are retained.

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/sitemap.svg"> Architecture

```
assay/
│
├── main.py                          ─ 7-stage pipeline orchestrator
├── config.py                        ─ All thresholds, rates, and paths
│
├── data/                            ── Data Layer ──────────────────
│   ├── fetcher.py                      Batched fetching + caching + fallback
│   ├── sp500.py                        S&P 500 list from Wikipedia
│   ├── cache.py                        SQLite with per-type TTL
│   └── providers/
│       ├── base.py                     FinancialData dataclass (66 fields)
│       ├── yahooquery_provider.py      Primary: batch API, 8 workers
│       └── yfinance_provider.py        Fallback: single-threaded
│
├── scoring/                         ── Scoring Layer ───────────────
│   ├── value_scorer.py                 Earnings Yield percentile ranking
│   ├── quality_scorer.py              Piotroski + Profitability composite
│   ├── conviction.py                   Geometric mean + 9-cell classify
│   ├── momentum_scorer.py             12-1 month momentum gate
│   └── filters.py                      Data quality pre-checks
│
├── quality/                         ── Quality Models ──────────────
│   ├── piotroski.py                    9 binary criteria + breakdown
│   ├── growth.py                       Revenue, margins, PEG (display)
│   └── base.py                         Abstract QualityModel
│
├── models/                          ── Valuation Context ───────────
│   ├── dcf.py                          DCF bear/base/bull scenarios
│   ├── relative.py                     Sector-relative multiples + PEG
│   └── base.py                         ValuationModel + ValuationResult
│
├── backtest/                        ── Historical Backtesting ──────
│   ├── engine.py                       Quarterly screening replay
│   ├── portfolio.py                    Portfolio simulation & metrics
│   ├── cache.py                        Historical data cache
│   ├── historical_fetcher.py           Historical snapshot fetcher
│   ├── snapshot_builder.py             Point-in-time dataset builder
│   └── report.py                       Backtest reporting
│
├── output/                          ── Reporting ───────────────────
│   ├── console_report.py              Rich terminal tables
│   └── csv_report.py                   CSV + JSON export
│
├── tests/                           54+ unit tests
├── scripts/run-daily.sh             Cron runner (weekdays 6:30 PM ET)
└── Dockerfile                       Python 3.13-slim container
```

### Data Pipeline

```
  Wikipedia            Yahoo Finance              yfinance
     │                      │                        │
     ▼                      ▼                        ▼
 ┌────────┐         ┌──────────────┐         ┌────────────┐
 │ S&P500 │         │  yahooquery   │         │  Fallback   │
 │  List  │         │  (85/batch)   │◄───────►│  Provider   │
 └───┬────┘         └──────┬───────┘         └─────┬──────┘
     │                     │                       │
     └──────────┬──────────┴───────────────────────┘
                ▼
 ┌──────────────────────────────────────────────────────────┐
 │                    SQLite Cache                          │
 │  S&P 500: 7d TTL  │  Fundamentals: 7d  │  Prices: 24h   │
 └──────────────────────────┬───────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────┐
 │                   Scoring Engine                         │
 │                                                          │
 │  Value Score ────────────┐                               │
 │  (EY + FCF percentile)   │                               │
 │                          ├──► √(V × Q) ──► Classify      │
 │  Quality Score ──────────┘                               │
 │  (Piotroski + GP/A)         Conviction    9-Cell Matrix  │
 │                                                          │
 │          ┌── F-Score Gate ──┐  ┌── Momentum Gate ──┐     │
 │          │  raw F < 6?      │  │  bottom 25%?      │     │
 │          │  → WATCH LIST    │  │  → WATCH LIST     │     │
 │          └──────────────────┘  └───────────────────┘     │
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

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/book.svg"> Academic References

1. **Carlisle, T.** (2014). *Deep Value: Why Activist Investors and Other Contrarians Battle for Control of Losing Corporations.* Wiley.
   — Acquirer's Multiple: **17.9% CAGR**, 1973-2017.

2. **Piotroski, J.D.** (2000). *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers.* Journal of Accounting Research, 38, 1-41.
   — F-Score: **13.4% annual outperformance** among high book-to-market firms.

3. **Novy-Marx, R.** (2013). *The Other Side of Value: The Gross Profitability Premium.* Journal of Financial Economics, 108(1), 1-28.
   — Gross Profitability predicts returns as well as book-to-market.

4. **Jegadeesh, N. & Titman, S.** (1993). *Returns to Buying Winners and Selling Losers.* Journal of Finance, 48(1), 65-91.
   — 12-1 month momentum: the original cross-sectional momentum paper.

5. **Research Affiliates** (2024). *Momentum as a Negative Screen.*
   — Excluding bottom-quartile momentum improved value returns by **+2.8%/yr** over 32 years.

---

## <img width="20" src="https://cdn.jsdelivr.net/npm/@tabler/icons@2.47.0/icons/files.svg"> Further Reading

| Document | Description |
|:---|:---|
| [**Methodology**](docs/METHODOLOGY.md) | Complete mathematical specification — every formula, every weight, every edge case |
| [**Architecture**](docs/ARCHITECTURE.md) | System design, data flow, caching strategy, module responsibilities |
| [**Contributing**](CONTRIBUTING.md) | Development setup, testing, code standards, and contribution guidelines |

---

<div align="center">

<sub>

*This is a research tool, not financial advice. Past academic performance does not guarantee future results.*
*Always do your own due diligence before making investment decisions.*

</sub>

</div>
