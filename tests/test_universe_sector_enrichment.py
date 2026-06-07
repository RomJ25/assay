import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from data import universe as universe_mod


def test_sector_fields_from_profile_normalizes_yahoo_labels():
    sector, industry = universe_mod._sector_fields_from_profile(
        {
            "sector": "Technology",
            "industry": "Semiconductors",
        }
    )

    assert sector == "Information Technology"
    assert industry == "Semiconductors"


def test_apply_sector_profile_values_fills_unknown_without_overriding_known_sector():
    info = {
        "AAPL": {
            "company_name": "Apple",
            "sector": "Information Technology",
            "sub_industry": "Unknown",
        },
        "HRB": {
            "company_name": "H&R Block",
            "sector": "Unknown",
            "sub_industry": "Unknown",
        },
    }

    updated = universe_mod._apply_sector_profile_values(
        info,
        {
            "AAPL": {"sector": "Technology", "sub_industry": "Consumer Electronics"},
            "HRB": {"sector": "Consumer Cyclical", "sub_industry": "Personal Services"},
        },
    )

    assert updated == 2
    assert info["AAPL"]["sector"] == "Information Technology"
    assert info["AAPL"]["sub_industry"] == "Consumer Electronics"
    assert info["HRB"]["sector"] == "Consumer Discretionary"
    assert info["HRB"]["sub_industry"] == "Personal Services"


def test_sector_profile_cache_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(universe_mod, "CACHE_DB_PATH", tmp_path / "cache.db")

    universe_mod._set_sector_profile_cache(
        {
            "CRUS": {"sector": "Information Technology", "sub_industry": "Semiconductors"},
        }
    )

    cached = universe_mod._get_sector_profile_cache(["CRUS", "MISSING"])
    assert cached == {
        "CRUS": {
            "sector": "Information Technology",
            "sub_industry": "Semiconductors",
        }
    }


def test_r1000_cache_can_be_read_for_exploratory_stale_research(monkeypatch, tmp_path):
    cache_path = tmp_path / "cache.db"
    monkeypatch.setattr(universe_mod, "CACHE_DB_PATH", cache_path)

    conn = sqlite3.connect(str(cache_path))
    conn.execute("""CREATE TABLE r1000_cache (
        data_json TEXT NOT NULL,
        fetched_at TEXT NOT NULL
    )""")
    old_ts = (datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)).isoformat()
    conn.execute(
        "INSERT INTO r1000_cache (data_json, fetched_at) VALUES (?, ?)",
        (json.dumps({"tickers": ["OLD"], "info": {"OLD": {"sector": "Unknown"}}}), old_ts),
    )
    conn.commit()
    conn.close()

    assert universe_mod._get_r1000_cache(max_age_hours=1) is None
    cached = universe_mod._get_r1000_cache(max_age_hours=None)
    assert cached is not None
    assert cached[0] == ["OLD"]


def test_russell1000_enriches_sector_metadata_before_cache(monkeypatch):
    class FakeTicker:
        def __init__(self, *_args, **_kwargs):
            pass

        @property
        def price(self):
            return {
                "MID": {"marketCap": 4_000_000_000},
                "SMALL": {"marketCap": 1_000_000_000},
            }

    all_info = {
        "SPY": {"company_name": "SPY", "sector": "Information Technology", "sub_industry": "ETF"},
        "MID": {"company_name": "Mid Cap", "sector": "Unknown", "sub_industry": "Unknown"},
        "SMALL": {"company_name": "Small Cap", "sector": "Unknown", "sub_industry": "Unknown"},
    }
    captured = {}

    monkeypatch.setitem(sys.modules, "yahooquery", SimpleNamespace(Ticker=FakeTicker))
    monkeypatch.setattr(universe_mod, "_get_r1000_cache", lambda: None)
    monkeypatch.setattr(universe_mod, "_fetch_us_all", lambda: (["SPY", "MID", "SMALL"], all_info))
    monkeypatch.setattr(
        universe_mod,
        "_fetch_sp500",
        lambda: (
            ["SPY"],
            {"SPY": {"company_name": "SPY", "sector": "Information Technology", "sub_industry": "ETF"}},
        ),
    )
    monkeypatch.setattr(
        universe_mod,
        "_enrich_info_with_sector_profiles",
        lambda info, tickers: info["MID"].update(
            {"sector": "Information Technology", "sub_industry": "Semiconductors"}
        ) or 1,
    )
    monkeypatch.setattr(
        universe_mod,
        "_set_r1000_cache",
        lambda tickers, info: captured.update(
            {
                "tickers": list(tickers),
                "info": {ticker: dict(row) for ticker, row in info.items()},
            }
        ),
    )

    tickers, info = universe_mod._fetch_russell1000()

    assert tickers == ["SPY", "MID"]
    assert info["MID"]["sector"] == "Information Technology"
    assert captured["info"]["MID"]["sub_industry"] == "Semiconductors"
