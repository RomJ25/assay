<div align="center">

# Contributing

**Development setup, testing, code standards, and how to submit changes**

</div>

---

## Development Setup

```bash
git clone https://github.com/romj25/assay.git
cd assay

python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
pip install -e ".[dev]"
```

**Requirements:** Python 3.11+ &nbsp;|&nbsp; No API keys needed

---

## Running Tests

```bash
python -m pytest tests/ -v                                  # All 54+ tests
python -m pytest tests/test_quality_models.py -v            # Specific file
python -m pytest tests/ --cov=. --cov-report=term-missing   # With coverage
```

### Test Coverage

| File | What it covers |
|:---|:---|
| `test_cache.py` | SQLite TTL, eviction, data type independence |
| `test_filters.py` | Data quality validation edge cases |
| `test_quality_models.py` | Piotroski criteria, profitability ranking, bank fallbacks |
| `test_value_models.py` | Earnings yield ranking, FCF yield, composite scoring |
| `test_relative_model.py` | Sector median computation, PEG ratios |
| `test_momentum.py` | Momentum percentile ranking, gate logic |
| `test_backtest_engine.py` | Historical screening replay |
| `test_portfolio.py` | Portfolio simulation & metrics |
| `test_snapshot_builder.py` | Point-in-time dataset construction |

---

## Project Structure

```
    assay/
    ├── main.py              Pipeline orchestrator (entry point)
    ├── config.py            All constants — thresholds, rates, paths
    ├── data/                Data fetching, caching, providers
    ├── scoring/             Value scoring, quality scoring, classification
    ├── quality/             Piotroski F-Score, growth model
    ├── models/              DCF, relative valuation (context only)
    ├── backtest/            Historical backtesting engine
    ├── output/              Console and file reporting
    └── tests/               Unit tests
```

**Layer rule:** Dependencies flow downward only. `scoring/` imports from `data/` but never from `output/`.

---

## Code Standards

### Style

- Follow existing code style — no linter is enforced, but consistency matters
- Use type hints for function signatures
- Prefer explicit over clever

### Architecture Principles

```
    1. All thresholds in config.py       No magic numbers in scoring modules
    2. Rank, don't predict               Percentile rankings, not absolute scores
    3. Graceful degradation              Missing data → None, never crashes
    4. Independence                      Value and quality must remain independent
```

### What Not to Do

- Don't add ML/AI models to the scoring pipeline — the value is in simplicity and transparency
- Don't hardcode thresholds in scoring modules — use `config.py`
- Don't add data providers without implementing the `DataProvider` interface
- Don't make supplementary models (DCF, relative) affect rankings

---

## Adding a New Quality Criterion

1. Implement in the appropriate module under `quality/`
2. Ensure it returns a normalized 0-100 score
3. Add tests in `tests/`
4. Update composite weighting in `scoring/quality_scorer.py` if it should affect rankings
5. Document the academic basis in `docs/METHODOLOGY.md`

---

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run the full test suite: `python -m pytest tests/ -v`
5. Commit with a clear message
6. Open a pull request with:
   - What you changed and why
   - Any new dependencies
   - Test results

---

## Reporting Issues

When filing an issue, please include:

- Python version (`python --version`)
- Steps to reproduce
- Expected vs. actual behavior
- Any error traceback

---

<div align="center">

<sub>[Back to README](README.md)</sub>

</div>
