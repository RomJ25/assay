<div align="center">

# Architecture

**System design, data flow, caching strategy, and module responsibilities**

</div>

---

### Contents

[System Overview](#system-overview) · [Pipeline Stages](#pipeline-stages) · [Data Layer](#data-layer) · [Scoring Layer](#scoring-layer) · [Output Layer](#output-layer) · [Configuration](#configuration) · [Error Handling](#error-handling--resilience)

---

## System Overview

Assay follows a **linear pipeline architecture** — data flows in one direction through seven stages with no circular dependencies.

```
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                          A S S A Y   P I P E L I N E                     │
    │                                                                          │
    │   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────┐│
    │   │ Stage 1  │───►│ Stage 2  │───►│ Stage 3  │───►│ Stage 4  │───►│ Stage ││
    │   │  FETCH   │    │ FILTER   │    │  SCORE   │    │CLASSIFY  │    │   5   ││
    │   │ S&P 500  │    │  Data    │    │ Value &  │    │ 9-Cell   │    │OUTPUT ││
    │   │ + Data   │    │ Quality  │    │ Quality  │    │ Matrix   │    │Report ││
    │   └────┬─────┘    └─────────┘    └─────────┘    └─────────┘    └───────┘│
    │        │                                                                 │
    │        ▼                                                                 │
    │   ┌─────────────────────────────┐                                        │
    │   │       SQLite Cache          │  ◄── Persists across runs              │
    │   │    (TTL-based eviction)     │                                        │
    │   └─────────────────────────────┘                                        │
    └──────────────────────────────────────────────────────────────────────────┘
```

### Layer Dependency Map

```
    main.py
    ├── config.py                          constants only — no side effects
    │
    ├── data/                              DATA LAYER
    │   ├── sp500.py                       → fetcher.py
    │   ├── fetcher.py                     → cache.py, providers/*
    │   ├── cache.py                       standalone (SQLite)
    │   └── providers/
    │       ├── base.py                    FinancialData dataclass
    │       ├── yahooquery_provider.py     → base.py
    │       └── yfinance_provider.py       → base.py
    │
    ├── scoring/                           SCORING LAYER
    │   ├── filters.py                     → providers/base.py
    │   ├── value_scorer.py                → providers/base.py
    │   ├── quality_scorer.py              → providers/base.py, quality/piotroski.py
    │   ├── conviction.py                  → config.py
    │   └── momentum_scorer.py             → config.py
    │
    ├── quality/                           QUALITY MODELS
    │   ├── piotroski.py                   → providers/base.py, quality/base.py
    │   ├── growth.py                      → providers/base.py, quality/base.py
    │   └── base.py                        abstract
    │
    ├── models/                            SUPPLEMENTARY (context only)
    │   ├── dcf.py                         → providers/base.py, config.py
    │   ├── relative.py                    → providers/base.py
    │   └── base.py                        dataclasses
    │
    ├── backtest/                          HISTORICAL BACKTESTING
    │   ├── engine.py                      → scoring/*, data/*
    │   ├── portfolio.py                   standalone
    │   ├── cache.py                       → data/cache.py
    │   ├── historical_fetcher.py          → data/providers/*
    │   ├── snapshot_builder.py            → data/providers/base.py
    │   └── report.py                      standalone
    │
    └── output/                            OUTPUT LAYER
        ├── console_report.py              standalone (Rich)
        └── csv_report.py                  standalone (csv/json)
```

**Key constraint:** Arrows point downward only. Scoring never imports from output. Data never imports from scoring. Each layer is independently testable.

---

## Pipeline Stages

### Stage 1 — Fetch S&P 500 List & Financial Data

```
    Wikipedia HTML ──► pandas.read_html() ──► [ticker, name, sector, sub_industry]
                                                         │
                                                         ▼
                                                  Cache (7-day TTL)
```

**Module:** `data/sp500.py`

Parses Wikipedia's "List of S&P 500 companies" table. Cached for 7 days (index composition changes ~25 times/year).

**Data fetching** (`data/fetcher.py`):

```
    ┌──────────────────────────────────────────────────────┐
    │                    DataFetcher                        │
    │                                                      │
    │   Ticker List ──►  1. Check cache (by ticker)        │
    │                    2. Identify stale entries          │
    │                    3. Batch-fetch via yahooquery ───► │─── 85 tickers/batch
    │                    4. Fallback to yfinance            │    5s between batches
    │                    5. Merge fresh prices              │    8 parallel workers
    │                    6. Update cache                    │
    └──────────────────────────────────────────────────────┘
```

With a warm cache, only **prices** (24h TTL) are fetched — fundamentals (7d TTL) are skipped entirely.

```
    ┌──────────────────────────────────────────────────────────┐
    │  Provider       Batch    Workers    Timeout    Role      │
    │  ────────       ─────    ───────    ───────    ────      │
    │  yahooquery       85         8        10s      Primary   │
    │  yfinance          1         1          —      Fallback  │
    └──────────────────────────────────────────────────────────┘
```

### Stage 2 — Filter

```
    has_minimum_data(stock) ──► True:  include in ranking universe
                               False: exclude silently
```

**Module:** `scoring/filters.py`

Ensures percentile ranks are computed only over stocks with valid fundamentals.

### Stage 3 — Score

Two independent scoring passes run over the filtered universe:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │  VALUE SCORER                    QUALITY SCORER              │
    │  ────────────                    ──────────────              │
    │  For each stock:                 For each stock:             │
    │    • compute Earnings Yield        • compute Piotroski F     │
    │    • compute FCF Yield             • compute GP/Assets       │
    │  Percentile rank all             Percentile rank profitab.   │
    │  Composite: 70/30                Composite: 50/50            │
    │                                                             │
    │          ▼                                ▼                  │
    │    Value Score (0-100)          Quality Score (0-100)        │
    │          │                                │                  │
    │          └──────────────┬─────────────────┘                  │
    │                         ▼                                    │
    │                 Conviction Score                              │
    │                  = √(V × Q)                                  │
    │                         │                                    │
    │                         ▼                                    │
    │              ┌── classify(V, Q) ──────► 9-cell matrix        │
    │              ├── confidence(V, Q) ────► HIGH / MOD / LOW     │
    │              ├── f_score_gate(F) ─────► downgrade if F < 6   │
    │              └── momentum_gate(M) ───► downgrade if bot 25%  │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

**Modules:** `scoring/value_scorer.py`, `scoring/quality_scorer.py`, `scoring/conviction.py`, `scoring/momentum_scorer.py`

### Stage 4 — Supplementary Models (Optional)

```
    For each scored stock:
      ├── DCFModel.calculate()        → bear / base / bull intrinsic value
      ├── RelativeModel.calculate()   → P/E, EV/EBITDA, P/S vs sector
      └── GrowthModel.calculate()     → revenue momentum, margins, PEG
```

These provide context for console and CSV output but **do not influence** rankings.

### Stage 5 — Output

```
    Scored & classified stocks
             │
             ├──► Console   Rich terminal tables, color-coded, grouped by class
             ├──► CSV       results/screen_YYYY-MM-DD.csv  (37 columns)
             └──► JSON      results/screen_YYYY-MM-DD.json (full structure)
```

---

## Data Layer

### FinancialData Dataclass

The core data structure (`data/providers/base.py`) — 66 fields organized into 6 sections:

```
    FinancialData
    │
    ├── Identification
    │   ticker, company_name, sector, sub_industry
    │
    ├── Price Data
    │   current_price, market_cap, enterprise_value, beta
    │   fifty_two_week_high, fifty_two_week_low, shares_outstanding
    │
    ├── Valuation Multiples
    │   trailing_pe, forward_pe, price_to_book, price_to_sales
    │   ev_to_ebitda, ev_to_revenue, peg_ratio
    │
    ├── Income Statement                    (lists: [year₀, year₋₁, year₋₂, year₋₃])
    │   revenue, gross_profit, operating_income, net_income
    │   diluted_eps, interest_expense, ebitda
    │
    ├── Balance Sheet                       (lists: [year₀, year₋₁])
    │   total_assets, total_debt, current_assets, current_liabilities
    │   cash_and_equivalents, ordinary_shares_number
    │
    ├── Cash Flow                           (lists: [year₀, year₋₁, year₋₂, year₋₃])
    │   operating_cash_flow, capital_expenditure, free_cash_flow
    │
    └── Analyst Context
        analyst_target_price, recommendation_mean
```

**Safe access:**

```python
fd.get("revenue", 0)     # Latest year's revenue (None if missing)
fd.get("revenue", 1)     # Prior year's revenue
fd.get("total_debt", 0)  # Latest year's total debt
```

The `.get(field, year_index)` method handles missing data, out-of-range indices, and type mismatches without raising exceptions.

### SQLite Cache

```
    ┌──────────────────────────────────────────────────┐
    │                    cache.db                       │
    │                                                  │
    │   ┌──────────────────────────────────────────┐   │
    │   │  fundamentals                            │   │
    │   │  key: ticker    TTL: 7 days              │   │
    │   │  value: serialized FinancialData         │   │
    │   └──────────────────────────────────────────┘   │
    │                                                  │
    │   ┌──────────────────────────────────────────┐   │
    │   │  prices                                  │   │
    │   │  key: ticker    TTL: 24 hours            │   │
    │   │  value: {price, market_cap, ...}         │   │
    │   └──────────────────────────────────────────┘   │
    │                                                  │
    │   ┌──────────────────────────────────────────┐   │
    │   │  sp500                                   │   │
    │   │  key: "list"    TTL: 7 days              │   │
    │   │  value: [{ticker, name, ...}, ...]       │   │
    │   └──────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────┘
```

**TTL logic:**

```python
is_fresh = (current_time - timestamp) < ttl_hours * 3600
```

Stale entries are evicted at **2x TTL** (cleanup runs on write). This prevents unbounded growth while keeping recently-stale data available as a network-failure fallback.

### Provider Architecture

```
            ┌──────────────┐
            │ DataProvider  │  Abstract base
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

Tries yahooquery first (fast, batch-capable). For any tickers that fail, falls back to yfinance (slower, more reliable). Both return the same `FinancialData` dataclass.

---

## Scoring Layer

### Independence Guarantee

Value and quality scores are computed **completely independently**:

```
    VALUE reads:                           QUALITY reads:
    ────────────                           ─────────────
    operating_income                       net_income
    enterprise_value                       operating_cash_flow
    free_cash_flow                         total_assets
    market_cap                             total_debt (leverage ratio)
    total_debt (EV calc)                   current_assets
    cash_and_equivalents                   current_liabilities
    trailing_pe                            ordinary_shares_number
                                           gross_profit
                                           revenue
```

**Zero field overlap** in meaning (except `total_debt`, used for different purposes). The two scores contain genuinely independent information.

### Ranking Methodology

All percentile rankings follow the same algorithm:

```python
sorted_tickers = sort(tickers, by=metric, descending=True)
for i, ticker in enumerate(sorted_tickers):
    percentile[ticker] = (N - i) / N * 100
```

This produces a **uniform distribution** from ~0 to ~100 regardless of the underlying metric's shape:

```
    1. Outlier-robust        A 50% yield doesn't dominate a 12% yield
    2. No assumptions        Works for skewed, fat-tailed financial data
    3. Cross-comparable      Value 70 and Quality 70 both mean "top 30%"
```

---

## Output Layer

### Console Report

```
    ┌──────────────────────────────────────────────────────────┐
    │  ★ CONVICTION BUYS  (sorted by conviction score)        │
    │  ┌──────────────────────────────────────────────────┐    │
    │  │ Ticker   Conv.   Value   Quality   Confidence    │    │
    │  │ ...      ...     ...     ...       ...           │    │
    │  └──────────────────────────────────────────────────┘    │
    │                                                          │
    │  ⚠ VALUE TRAPS                                           │
    │  ┌──────────────────────────────────────────────────┐    │
    │  │ ...                                              │    │
    │  └──────────────────────────────────────────────────┘    │
    │                                                          │
    │  WATCH LIST  /  HOLD  /  AVOID  /  etc.                  │
    │                                                          │
    │  [Optional: Piotroski Breakdown Grid]                    │
    │  ┌──────────────────────────────────────────────────┐    │
    │  │ Ticker  F  NI  OCF  ROA  Acr  Dbt  CR  Dil  M  T│    │
    │  │ AAPL   8   ✓   ✓    ✓    ✓    ✗   ✓   ✓   ✓  ✗ │    │
    │  └──────────────────────────────────────────────────┘    │
    │                                                          │
    │  Sector Breakdown of Conviction Buys                     │
    └──────────────────────────────────────────────────────────┘
```

### CSV Schema (37 columns)

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  Group               Columns                                     │
    │  ─────               ───────                                     │
    │  Identity            ticker, company_name, sector, sub_industry  │
    │  Scores              value, quality, conviction, class, confid.  │
    │  Value Metrics       earnings_yield, fcf_yield, trailing_pe      │
    │  Quality Metrics     piotroski_f, profitability, gross_margin    │
    │  Piotroski Detail    f1..f9 (9 boolean columns)                  │
    │  Price Data          current_price, 52w_high, market_cap         │
    │  Valuation Context   dcf_bear, dcf_base, dcf_bull, pe_vs_sector │
    │  Growth Context      revenue_cagr, growth_score                  │
    └──────────────────────────────────────────────────────────────────┘
```

---

## Configuration

All tunable parameters live in **one file** — `config.py`:

```
    ┌──────────────────────────────────────────────────────────────────┐
    │  CONVICTION MATRIX                                               │
    │  VALUE_HIGH_THRESHOLD        = 70       top 30% on value         │
    │  QUALITY_HIGH_THRESHOLD      = 70       top 30% on quality       │
    │  VALUE_LOW_THRESHOLD         = 40       mid/low boundary         │
    │  QUALITY_LOW_THRESHOLD       = 40       mid/low boundary         │
    │  MIN_PIOTROSKI_F             = 6        F-Score gate             │
    │  QUALITY_SINGLE_SOURCE_PEN.  = 0.8      20% single-signal disc.  │
    │  MOMENTUM_GATE_PERCENTILE    = 25       bottom quartile gate     │
    │                                                                  │
    │  CACHE TTLs                                                      │
    │  SP500_CACHE_TTL_HOURS       = 168      7 days                   │
    │  FUNDAMENTALS_CACHE_TTL_HRS  = 168      7 days                   │
    │  PRICE_CACHE_TTL_HOURS       = 24       1 day                    │
    │                                                                  │
    │  DCF PARAMETERS (context only)                                   │
    │  RISK_FREE_RATE              = 0.0431   10Y Treasury yield       │
    │  EQUITY_RISK_PREMIUM         = 0.0423   Damodaran implied ERP    │
    │  DCF_TERMINAL_GROWTH         = 0.025    2.5% perpetual growth    │
    └──────────────────────────────────────────────────────────────────┘
```

**No parameters are hardcoded in scoring modules.** Every threshold, weight, and rate traces back to `config.py`.

---

## Error Handling & Resilience

### Data Fetching

```
    Request failed?
      ├── yahooquery timeout  →  retry with yfinance fallback
      ├── yfinance failed     →  skip ticker, log warning
      └── Network error       →  use cached data (even if stale)
```

### Scoring

```
    Missing field?
      ├── Value:    no EBIT  →  use 1/PE fallback
      │             no PE    →  exclude from value ranking
      ├── Quality:  no GP    →  use ROA fallback
      │             no data  →  exclude from quality ranking
      └── Both:     →  classification = "INSUFFICIENT DATA"
```

### Output

```
    Division by zero?   →  None (not displayed)
    Negative value?     →  Floor at 0
    No scored stocks?   →  Empty table with explanatory message
```

The system **degrades gracefully** — a single missing field never crashes the pipeline. Stocks with incomplete data receive `None` scores and are classified as "INSUFFICIENT DATA."

---

<div align="center">

<sub>[Back to README](../README.md)</sub>

</div>
