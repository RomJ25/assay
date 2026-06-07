# Reproducing the Evidence

Every headline number in this repo traces to a command you can run and a file you
can open. This document maps claims → command → output, and is honest about the
limits of that reproducibility.

## Pinned snapshot

The site and the case studies render from a **pinned snapshot dated 2026-04-26**,
committed so a fresh clone shows real data instead of an empty state:

| File | Size | Powers |
|---|---|---|
| `results/screen_2026-04-26.json` | ~1.2 MB | Home, Universe, stock sheets, search |
| `results/backtest_2026-04-26.csv` | <1 KB | Evidence page summary table |
| `results/backtest_detail_2026-04-26.csv` | ~5 KB | Evidence per-pick detail |

All other `results/*` output is git-ignored (it is regenerated locally). When you
re-run the screener, a newer-dated file is written and the API automatically
serves the latest one (`api/routes.py:_find_latest_screen` / `_find_latest_backtest`).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Requires **Python 3.11+**. No API keys. First run downloads and caches its data
sources (see *Data sources* below); later runs read the cache in `storage/`.

## Regenerate the live screen (Home / Universe)

```bash
python main.py                 # S&P 500, financials excluded (default)
# writes results/screen_<today>.csv and results/screen_<today>.json
```

Serve it locally:

```bash
python server.py               # FastAPI; the web app fetches /api/v1/screen and /api/v1/backtest
# in another shell:
cd web && pnpm install && pnpm run dev
```

## Regenerate the backtest evidence

```bash
python main.py --backtest                  # 4 years, survivorship-free, 10 bps costs (defaults)
# writes results/backtest_<today>.csv and results/backtest_detail_<today>.csv
```

The default is **survivorship-free** (point-in-time S&P 500 constituents). The
`--survivorship-naive` flag reproduces the old, inflated mode for comparison only
— see the SMCI note below.

## Claim → command → file

| Claim (where it appears) | Command | Verify in |
|---|---|---|
| Default screen contracts to ~6 names in expensive markets; held 17 through the 2022 −16% quarter (`README.md`) | `python main.py --backtest` | `results/backtest_*.csv` (`num_picks` column) |
| Strict bar reaches **zero** picks at the Dec 2025 rebalance (`README.md`) | `python main.py --backtest` with the stricter buy threshold (see `docs/DESIGN_DECISIONS.md` "buy80") | `results/e5_buy80_*.csv` |
| Selective sell: **+10.4% CAGR / +0.4%/yr** selection alpha, within noise (`docs/STRATEGY.md` §6) | `python scripts/run_policy_lab.py` | policy-lab output + `docs/CAPITAL_RESEARCH_PLAN.md` |
| Within-list conviction ranking does **not** predict returns (`README.md`, `docs/DESIGN_DECISIONS.md`) | `python backtest/case_study.py` | case-study bucket/Kendall-tau output |
| 62 years of value+quality factor evidence (+7.1%/yr) (`docs/CASE_STUDIES/long_term_evidence.md`) | `python -c "from data.fama_french import download_portfolios_32; print(download_portfolios_32().tail())"` | Kenneth French Data Library (cited) |

## Data sources (all free, auto-cached)

| Source | Module | Cache | Mutability |
|---|---|---|---|
| Fundamentals & prices | `data/` via `yfinance` / `yahooquery` | `storage/cache.db` | **Mutable** — Yahoo revises/restates history; numbers drift over time |
| Point-in-time S&P 500 membership | `data/sp500_historical.py` | `storage/sp500_historical.csv` | Pinned to a dated `fja05680/sp500` snapshot |
| Fama-French factors / 32 portfolios | `data/fama_french.py` | `storage/ff_*.csv` | Updated monthly by Dartmouth; revised occasionally |

## Honest limits of reproducibility

- **The numbers will not match to the last decimal.** `yfinance`/EDGAR data is
  mutable: vendors restate financials and adjust price history, so a run today can
  differ slightly from the 2026-04-26 snapshot. Treat agreement to within a small
  tolerance (and the same *direction*/*ranking*) as a successful reproduction, not
  bit-for-bit equality.
- **Survivorship bias (the SMCI retraction).** Earlier versions of this repo
  reported a much higher selective-sell alpha (+4.3%/yr). An April 2026 audit found
  it was almost entirely a single survivorship-biased name — SMCI, present in
  backtest quarters before its March 2024 S&P 500 addition. The survivorship-free
  default and the corrected figures above are the result. Full detail:
  `docs/STRATEGY.md` §6 and `docs/DESIGN_DECISIONS.md` (2026-04-15 audit).
- **Small sample.** 16 quarters is too short to establish a factor edge; the
  pre-declared capital gate in `research/policy_lab.py` requires 30+. See
  `docs/CAPITAL_RESEARCH_PLAN.md` for why the algorithm is **not** capital-ready.
- **Russell 1000 is approximate.** Its point-in-time membership uses cached
  financials + a market-cap floor, not true IWB constituent history.
