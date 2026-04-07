# Contributing to Assay

Thank you for your interest in improving Assay. This guide covers development setup, testing, code standards, and how to submit changes.

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/romj25/assay.git
cd assay

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies (runtime + dev)
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Requirements

- **Python 3.11+** (uses modern type hints, walrus operator, etc.)
- No API keys needed — all data sources are free

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_quality_models.py -v

# Run with coverage (if installed)
python -m pytest tests/ --cov=. --cov-report=term-missing
```

The test suite includes **54+ tests** covering:

| Test File | Coverage |
|:---|:---|
| `test_cache.py` | SQLite cache TTL, eviction, data type independence |
| `test_filters.py` | Data quality validation edge cases |
| `test_quality_models.py` | Piotroski criteria, profitability ranking, bank fallbacks |
| `test_value_models.py` | Earnings yield ranking, FCF yield, composite scoring |
| `test_relative_model.py` | Sector median computation, PEG ratios |

---

## Project Structure

```
assay/
├── main.py              # Pipeline orchestrator (entry point)
├── config.py            # All constants — thresholds, rates, paths
├── data/                # Data fetching, caching, providers
├── scoring/             # Value scoring, quality scoring, classification
├── quality/             # Piotroski F-Score, growth model
├── models/              # DCF, relative valuation (context only)
├── output/              # Console and file reporting
└── tests/               # Unit tests
```

**Layer rule:** Dependencies flow downward only. `scoring/` imports from `data/` but never from `output/`. `output/` imports from neither `scoring/` nor `data/`.

---

## Code Standards

### Style

- Follow existing code style — no linter is enforced, but consistency matters
- Use type hints for function signatures
- Prefer explicit over clever

### Architecture Principles

1. **All thresholds in `config.py`** — No magic numbers in scoring modules
2. **Rank, don't predict** — Percentile rankings, not absolute scores
3. **Graceful degradation** — Missing data → `None` scores, never crashes
4. **Independence** — Value and quality scores must remain independently computed

### What Not to Do

- Don't add ML/AI models to the scoring pipeline — the value is in simplicity and transparency
- Don't hardcode thresholds in scoring modules — use `config.py`
- Don't add new data providers without implementing the `DataProvider` interface
- Don't make supplementary models (DCF, relative) affect rankings

---

## Adding a New Quality Criterion

If you want to add a criterion (e.g., to the growth model or as a new quality signal):

1. Implement in the appropriate module under `quality/`
2. Ensure it returns a normalized 0–100 score
3. Add tests in `tests/`
4. Update the composite weighting in `scoring/quality_scorer.py` if it should affect rankings
5. Document the academic basis in `docs/METHODOLOGY.md`

---

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the full test suite (`python -m pytest tests/ -v`)
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

<p align="center">
  <sub><a href="README.md">← Back to README</a></sub>
</p>
