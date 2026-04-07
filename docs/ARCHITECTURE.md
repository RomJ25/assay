# Architecture

A technical guide to Assay's system design, data flow, caching strategy, and module responsibilities.

---

## Table of Contents

- [System Overview](#system-overview)
- [Pipeline Stages](#pipeline-stages)
- [Data Layer](#data-layer)
- [Scoring Layer](#scoring-layer)
- [Output Layer](#output-layer)
- [Configuration](#configuration)
- [Error Handling & Resilience](#error-handling--resilience)

---

## System Overview

Assay follows a **linear pipeline architecture** — data flows in one direction through seven stages, with no circular dependencies between layers.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ASSAY PIPELINE                                   │
│                                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │  Stage 1  │──►│  Stage 2  │──►│  Stage 3  │──►│  Stage 4  │──►│  Stage 5  │ │
│  │  Fetch    │   │  Filter   │   │  Score    │   │  Classify │   │  Output  │ │
│  │  S&P 500  │   │  Data     │   │  Value &  │   │  9-Cell   │   │  Report  │ │
│  │  + Data   │   │  Quality  │   │  Quality  │   │  Matrix   │   │  & CSV   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │                                                                     │
│       ▼                                                                     │
│  ┌────────────────────────┐                                                 │
│  │      SQLite Cache      │  ◄── Persistent across runs                     │
│  │  (TTL-based eviction)  │                                                 │
│  └────────────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Dependency Map

```
main.py
  ├── config.py                  (constants only — no side effects)
  ├── data/
  │     ├── sp500.py             → fetcher.py
  │     ├── fetcher.py           → cache.py, providers/*
  │     ├── cache.py             (standalone — SQLite)
  │     └── providers/
  │           ├── base.py        (FinancialData dataclass)
  │           ├── yahooquery_provider.py → base.py
  │           └── yfinance_provider.py  → base.py
  ├── scoring/
  │     ├── filters.py           → providers/base.py
  │     ├── value_scorer.py      → providers/base.py
  │     ├── quality_scorer.py    → providers/base.py, quality/piotroski.py
  │     └── conviction.py        → config.py
  ├── quality/
  │     ├── piotroski.py         → providers/base.py, quality/base.py
  │     ├── growth.py            → providers/base.py, quality/base.py
  │     └── base.py              (abstract)
  ├── models/
  │     ├── dcf.py               → providers/base.py, models/base.py, config.py
  │     ├── relative.py          → providers/base.py, models/base.py
  │     └── base.py              (dataclasses)
  └── output/
        ├── console_report.py    (standalone — Rich library)
        └── csv_report.py        (standalone — csv/json)
```

**Key constraint:** Arrows point downward only. The scoring layer never imports from output. The data layer never imports from scoring. This makes each layer independently testable.

---

## Pipeline Stages

### Stage 1 — Fetch S&P 500 List

```
Wikipedia HTML Table ──► pandas.read_html() ──► List[ticker, name, sector, sub_industry]
                                                          │
                                                          ▼
                                                   Cache (7-day TTL)
```

**Module:** `data/sp500.py`

Parses the Wikipedia "List of S&P 500 companies" table. The list is cached for 7 days since index composition changes are infrequent (~25 changes per year).

### Stage 2 — Fetch Financial Data

```
                    ┌──────────────────────────────┐
                    │        DataFetcher            │
                    │                               │
  Ticker List ────► │  1. Check cache (by ticker)   │
                    │  2. Identify stale entries     │
                    │  3. Batch-fetch via yahooquery │ ──► 85 tickers/batch
                    │  4. Fallback to yfinance       │     5s delay between
                    │  5. Merge fresh prices         │
                    │  6. Update cache               │
                    └──────────────────────────────┘
```

**Module:** `data/fetcher.py`

The fetcher checks the SQLite cache first. Only stale or missing tickers are fetched from the network. This means a typical run with warm cache fetches **only prices** (24h TTL) and skips fundamentals entirely (7d TTL).

**Batching strategy:**

| Provider | Batch Size | Workers | Timeout | Use Case |
|:---|:---:|:---:|:---:|:---|
| yahooquery | 85 tickers | 8 threads | 10s | Primary — fast batch API |
| yfinance | 1 ticker | 1 thread | — | Fallback — slower, more reliable |

### Stage 3 — Filter

```
has_minimum_data(stock) ──► True:  include in ranking universe
                          └► False: exclude silently
```

**Module:** `scoring/filters.py`

Filters out stocks with insufficient data before scoring. This ensures percentile ranks are computed only over stocks with valid fundamentals.

### Stage 4 — Score

Two independent scoring passes run over the filtered universe:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Value Scorer                Quality Scorer          │
│  ───────────                 ──────────────          │
│  For each stock:             For each stock:         │
│    compute EY                  compute Piotroski     │
│    compute FCF yield           compute GP/Assets     │
│  Percentile rank all         Percentile rank prof.   │
│  Composite: 70/30            Composite: 50/50        │
│                                                     │
│          ▼                           ▼               │
│    Value Score (0-100)      Quality Score (0-100)    │
│          │                           │               │
│          └───────────┬───────────────┘               │
│                      ▼                               │
│              Conviction Score                         │
│              = √(V × Q)                              │
│                      │                               │
│                      ▼                               │
│            classify(V, Q) → 9-cell                   │
│            confidence(V, Q) → H/M/L                  │
│            f_score_gate(class, F) → downgrade?       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Modules:** `scoring/value_scorer.py`, `scoring/quality_scorer.py`, `scoring/conviction.py`

### Stage 5 — Supplementary Models (Optional)

```
For each scored stock:
  ├── DCFModel.calculate()        → bear / base / bull intrinsic value
  ├── RelativeModel.calculate()   → P/E, EV/EBITDA, P/S vs sector
  └── GrowthModel.calculate()     → revenue momentum, margins, PEG
```

**Modules:** `models/dcf.py`, `models/relative.py`, `quality/growth.py`

These models provide context for the console and CSV output but **do not influence** the conviction score or classification.

### Stage 6 — Output

```
Scored & classified stocks
         │
         ├──► ConsoleReport  ──► Rich terminal tables
         │     - Grouped by classification
         │     - Color-coded by conviction level
         │     - Optional Piotroski breakdown grid
         │
         ├──► CSVReport  ──► results/screen_YYYY-MM-DD.csv
         │     - 37 columns: scores, metrics, 9 Piotroski booleans
         │
         └──► JSONReport ──► results/screen_YYYY-MM-DD.json
               - Full structure with breakdown objects
```

**Modules:** `output/console_report.py`, `output/csv_report.py`

---

## Data Layer

### FinancialData Dataclass

The core data structure (`data/providers/base.py`) stores 66 fields organized into 6 sections:

```
FinancialData
├── Identification
│     ticker, company_name, sector, sub_industry
│
├── Price Data
│     current_price, market_cap, enterprise_value, beta
│     fifty_two_week_high, fifty_two_week_low
│     shares_outstanding
│
├── Valuation Multiples
│     trailing_pe, forward_pe, price_to_book, price_to_sales
│     ev_to_ebitda, ev_to_revenue, peg_ratio
│
├── Income Statement (lists: [year₀, year₋₁, year₋₂, year₋₃])
│     revenue, gross_profit, operating_income, net_income
│     diluted_eps, interest_expense, ebitda
│
├── Balance Sheet (lists: [year₀, year₋₁])
│     total_assets, total_debt, current_assets, current_liabilities
│     cash_and_equivalents, ordinary_shares_number
│
├── Cash Flow (lists: [year₀, year₋₁, year₋₂, year₋₃])
│     operating_cash_flow, capital_expenditure, free_cash_flow
│
└── Analyst Context
      analyst_target_price, recommendation_mean
```

**Safe access pattern:**

```python
fd.get("revenue", 0)     # Latest year's revenue (None if missing)
fd.get("revenue", 1)     # Prior year's revenue
fd.get("total_debt", 0)  # Latest year's total debt
```

The `.get(field, year_index)` method handles missing data, out-of-range indices, and type mismatches without raising exceptions.

### SQLite Cache

```
┌──────────────────────────────────────────┐
│              cache.db                     │
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │ fundamentals                        │ │
│  │   key: ticker                       │ │
│  │   value: serialized FinancialData   │ │
│  │   timestamp: insertion time         │ │
│  │   TTL: 7 days                       │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │ prices                              │ │
│  │   key: ticker                       │ │
│  │   value: {price, market_cap, ...}   │ │
│  │   TTL: 24 hours                     │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │ sp500                               │ │
│  │   key: "list"                       │ │
│  │   value: [{ticker, name, ...}, ...] │ │
│  │   TTL: 7 days                       │ │
│  └─────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

**TTL logic:**

```python
is_fresh = (current_time - timestamp) < ttl_hours * 3600
```

Stale entries are evicted when they exceed **2× TTL** (cleanup runs on cache write). This prevents the database from growing unboundedly while keeping recently-stale data available as a fallback during network failures.

### Provider Architecture

```
        ┌──────────────┐
        │ DataProvider  │  (Abstract base)
        │              │
        │  fetch()     │  → Dict[str, FinancialData]
        │  fetch_one() │  → FinancialData
        └──────┬───────┘
               │
       ┌───────┴────────┐
       │                │
┌──────┴──────┐  ┌──────┴──────┐
│ yahooquery  │  │  yfinance   │
│  Provider   │  │  Provider   │
│             │  │             │
│ Batch: 85   │  │ Batch: 1    │
│ Workers: 8  │  │ Sequential  │
│ Timeout: 10s│  │ No timeout  │
└─────────────┘  └─────────────┘
     Primary          Fallback
```

The fetcher tries yahooquery first (fast, batch-capable). For any tickers that fail, it falls back to yfinance (slower but more reliable). Both providers return the same `FinancialData` dataclass.

---

## Scoring Layer

### Independence Guarantee

Value and quality scores are computed **completely independently**:

- Value scoring reads: `operating_income`, `enterprise_value`, `free_cash_flow`, `market_cap`, `total_debt`, `cash_and_equivalents`, `trailing_pe`
- Quality scoring reads: `net_income`, `operating_cash_flow`, `total_assets`, `total_debt`, `current_assets`, `current_liabilities`, `ordinary_shares_number`, `gross_profit`, `revenue`

There is **zero field overlap** between value and quality inputs (except `total_debt`, which is used for different purposes: EV calculation vs. leverage ratio). This means the two scores contain genuinely independent information.

### Ranking Methodology

All percentile rankings follow the same algorithm:

```python
sorted_tickers = sort(tickers, by=metric, descending=True)
for i, ticker in enumerate(sorted_tickers):
    percentile[ticker] = (N - i) / N * 100
```

This produces a **uniform distribution** from ≈0 to ≈100 regardless of the underlying metric's distribution. Benefits:

1. **Outlier-robust** — A stock with 50% earnings yield doesn't dominate one with 12%
2. **No distributional assumptions** — Works for skewed, fat-tailed financial data
3. **Comparable across dimensions** — Value 70 and Quality 70 both mean "top 30%"

---

## Output Layer

### Console Report Structure

```
┌─────────────────────────────────────────────────┐
│  ★ CONVICTION BUYS (sorted by conviction score) │
│  ┌───────────────────────────────────────────┐   │
│  │ Ticker  Conv.  Value  Quality  Class.     │   │
│  │ ...     ...    ...    ...      ...        │   │
│  └───────────────────────────────────────────┘   │
│                                                  │
│  ⚠ VALUE TRAPS                                   │
│  ┌───────────────────────────────────────────┐   │
│  │ ...                                       │   │
│  └───────────────────────────────────────────┘   │
│                                                  │
│  WATCH LIST / HOLD / AVOID / etc.                │
│                                                  │
│  [Optional: Piotroski Breakdown Grid]            │
│  ┌───────────────────────────────────────────┐   │
│  │ Ticker  F  NI  OCF  ROA  Acr  Dbt  CR    │   │
│  │ AAPL   8   ✓   ✓    ✓    ✓    ✗   ✓  ...│   │
│  └───────────────────────────────────────────┘   │
│                                                  │
│  Sector Breakdown of Conviction Buys             │
└─────────────────────────────────────────────────┘
```

### CSV Schema (37 columns)

| Group | Columns |
|:---|:---|
| Identity | ticker, company_name, sector, sub_industry |
| Scores | value_score, quality_score, conviction_score, classification, confidence |
| Value Metrics | earnings_yield, fcf_yield, trailing_pe |
| Quality Metrics | piotroski_f, profitability_ratio, gross_margin |
| Piotroski Detail | f1_ni, f2_ocf, f3_roa, f4_accruals, f5_debt, f6_cr, f7_dilution, f8_margin, f9_turnover |
| Price Data | current_price, 52w_high, market_cap |
| Valuation Context | dcf_bear, dcf_base, dcf_bull, pe_vs_sector, analyst_upside |
| Growth Context | revenue_cagr, growth_score |

---

## Configuration

All tunable parameters live in a single file (`config.py`), organized by section:

```python
# Conviction Matrix Thresholds
VALUE_HIGH_THRESHOLD = 70        # top 30% on value
QUALITY_HIGH_THRESHOLD = 70      # top 30% on quality
VALUE_LOW_THRESHOLD = 40         # boundary between mid and low
QUALITY_LOW_THRESHOLD = 40
MIN_PIOTROSKI_F = 5              # F-Score gate for conviction buys
QUALITY_SINGLE_SOURCE_PENALTY = 0.8  # 20% discount for single-signal quality

# Cache TTLs
SP500_CACHE_TTL_HOURS = 168      # 7 days
FUNDAMENTALS_CACHE_TTL_HOURS = 168  # 7 days (financials update quarterly)
PRICE_CACHE_TTL_HOURS = 24       # 1 day

# DCF Parameters (context only)
RISK_FREE_RATE = 0.0431          # 10Y Treasury yield
EQUITY_RISK_PREMIUM = 0.0423     # Damodaran implied ERP
DCF_TERMINAL_GROWTH = 0.025      # 2.5% perpetual growth
```

**No parameters are hardcoded in scoring modules.** Every threshold, weight, and rate traces back to `config.py`.

---

## Error Handling & Resilience

### Data Fetching

```
Request failed?
  ├── yahooquery timeout → retry with yfinance fallback
  ├── yfinance failed   → skip ticker, log warning
  └── Network error     → use cached data (even if stale)
```

### Scoring

```
Missing field?
  ├── Value:   no EBIT → use 1/PE fallback
  │            no PE   → exclude from value ranking
  ├── Quality: no GP   → use ROA fallback
  │            no data → exclude from quality ranking
  └── Both:    → classification = "INSUFFICIENT DATA"
```

### Output

```
Division by zero?  → None (not displayed)
Negative value?    → Floor at 0
No scored stocks?  → Empty table with explanatory message
```

The system is designed to **degrade gracefully** — a single missing field never crashes the pipeline. Stocks with incomplete data simply receive `None` scores and are classified as "INSUFFICIENT DATA."

---

<p align="center">
  <sub><a href="../README.md">← Back to README</a></sub>
</p>
