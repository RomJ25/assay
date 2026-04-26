"""Unit tests for SEC EDGAR filed-date preservation (Slice B).

Verifies that:
1. _build_rows_from_concepts() preserves the earliest `filed` date per
   fiscal-year-end as `filed_date` on the output row.
2. _filter_statements() respects `prefer_filed_date` and uses the real
   filing date when present, falling back to the period-end + lag proxy
   when missing.
"""

from datetime import date

from backtest.edgar_fetcher import _build_statement_rows, _INCOME_CONCEPTS
from backtest.snapshot_builder import _filter_statements


def test_filed_date_preserved_from_edgar_entries():
    """When EDGAR entries include a `filed` field, the row should expose it as filed_date."""
    gaap = {
        "Revenues": {
            "units": {
                "USD": [
                    {
                        "form": "10-K",
                        "start": "2023-01-01",
                        "end": "2023-12-31",
                        "val": 1000,
                        "filed": "2024-02-28",
                    },
                ],
            },
        },
        "NetIncomeLoss": {
            "units": {
                "USD": [
                    {
                        "form": "10-K",
                        "start": "2023-01-01",
                        "end": "2023-12-31",
                        "val": 100,
                        "filed": "2024-02-28",
                    },
                ],
            },
        },
    }
    rows = _build_statement_rows(gaap, _INCOME_CONCEPTS, "income")
    assert len(rows) == 1
    assert rows[0]["filed_date"] == "2024-02-28"
    assert rows[0]["asOfDate"] == "2023-12-31T00:00:00"


def test_earliest_filed_wins_on_amended_filings():
    """If multiple entries share a fiscal-year-end (e.g., 10-K + 10-K/A amendment),
    the earliest filed date should be preserved — that's when the data first
    became publicly available."""
    gaap = {
        "Revenues": {
            "units": {
                "USD": [
                    {
                        "form": "10-K",
                        "start": "2023-01-01",
                        "end": "2023-12-31",
                        "val": 1000,
                        "filed": "2024-02-28",
                    },
                ],
            },
        },
        "NetIncomeLoss": {
            "units": {
                "USD": [
                    {
                        "form": "10-K",
                        "start": "2023-01-01",
                        "end": "2023-12-31",
                        "val": 100,
                        "filed": "2024-05-15",
                    },
                ],
            },
        },
    }
    rows = _build_statement_rows(gaap, _INCOME_CONCEPTS, "income")
    assert rows[0]["filed_date"] == "2024-02-28"


def test_filter_uses_proxy_lag_by_default():
    """Without prefer_filed_date, the period-end+lag proxy is the only test."""
    rows = [
        {"asOfDate": "2023-12-31T00:00:00", "filed_date": "2024-02-28", "TotalRevenue": 1000},
    ]
    # as_of_date = 2024-03-01 → cutoff = 2023-12-16 (75-day proxy).
    # 2023-12-31 > 2023-12-16, so the row should be EXCLUDED by proxy.
    cutoff = date(2024, 3, 1) - __import__("datetime").timedelta(days=75)
    out = _filter_statements(rows, cutoff, date(2024, 3, 1), prefer_filed_date=False)
    assert out == []


def test_filter_includes_when_real_filed_date_in_past():
    """With prefer_filed_date=True, the actual filed date governs availability.
    The 75-day proxy would EXCLUDE this row (period end 2023-12-31 with as_of
    2024-03-01 is 60 days, less than 75) — but the real filed_date 2024-02-28
    IS before as_of, so the row is INCLUDED."""
    rows = [
        {"asOfDate": "2023-12-31T00:00:00", "filed_date": "2024-02-28", "TotalRevenue": 1000},
    ]
    cutoff = date(2024, 3, 1) - __import__("datetime").timedelta(days=75)
    out = _filter_statements(rows, cutoff, date(2024, 3, 1), prefer_filed_date=True)
    assert len(out) == 1
    assert out[0]["TotalRevenue"] == 1000


def test_filter_excludes_when_real_filed_date_in_future():
    """A row with a filed_date AFTER as_of must be excluded under prefer_filed_date,
    even if the proxy would include it."""
    rows = [
        {"asOfDate": "2023-12-31T00:00:00", "filed_date": "2024-04-15", "TotalRevenue": 1000},
    ]
    # 2024-04-01 is AFTER period+75-day proxy (2024-03-15), so proxy would include.
    # But filed_date 2024-04-15 is AFTER 2024-04-01, so true point-in-time excludes.
    cutoff = date(2024, 4, 1) - __import__("datetime").timedelta(days=75)
    out = _filter_statements(rows, cutoff, date(2024, 4, 1), prefer_filed_date=True)
    assert out == []


def test_filter_falls_back_to_proxy_when_filed_date_missing():
    """Rows without filed_date must fall back to the proxy even with prefer_filed_date=True."""
    rows = [
        {"asOfDate": "2022-12-31T00:00:00", "TotalRevenue": 500},  # no filed_date
    ]
    cutoff = date(2024, 4, 1) - __import__("datetime").timedelta(days=75)
    # 2022-12-31 is well before 2024-01-16 cutoff → included via proxy.
    out = _filter_statements(rows, cutoff, date(2024, 4, 1), prefer_filed_date=True)
    assert len(out) == 1


def test_filter_handles_malformed_filed_date():
    """Bad filed_date strings must not crash; should fall back to proxy."""
    rows = [
        {"asOfDate": "2022-12-31T00:00:00", "filed_date": "not-a-date", "TotalRevenue": 500},
    ]
    cutoff = date(2024, 4, 1) - __import__("datetime").timedelta(days=75)
    out = _filter_statements(rows, cutoff, date(2024, 4, 1), prefer_filed_date=True)
    assert len(out) == 1  # proxy includes it
