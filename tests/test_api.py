"""Integration tests for the web API endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import RESULTS_DIR


@pytest.fixture
def client():
    """Create a test client for the API."""
    from server import app
    return TestClient(app)


@pytest.fixture
def has_screen_data():
    """Check if screen data exists for testing."""
    files = sorted(RESULTS_DIR.glob("screen_*.json"), reverse=True)
    full_screens = [f for f in files if f.stat().st_size > 10000]
    return len(full_screens) > 0


@pytest.fixture
def has_backtest_data():
    """Check if backtest data exists for testing."""
    return any(RESULTS_DIR.glob("backtest_[0-9]*.csv"))


class TestScreenEndpoints:
    def test_get_screen(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/screen")
        assert r.status_code == 200
        data = r.json()
        assert "universe" in data
        assert "stocks" in data
        assert "date" in data
        assert "screened" in data
        assert data["screened"] > 100
        assert len(data["stocks"]) == data["screened"]

    def test_get_screen_stock_shape(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/screen")
        stock = r.json()["stocks"][0]
        required_fields = [
            "ticker", "company", "sector", "price",
            "value_score", "quality_score", "conviction_score",
            "classification", "piotroski_f",
        ]
        for field in required_fields:
            assert field in stock, f"Missing field: {field}"

    def test_get_screen_classifications(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/screen")
        stocks = r.json()["stocks"]
        classifications = {s["classification"] for s in stocks}
        # Should have at least some of the expected classifications
        assert len(classifications) >= 3

    def test_screen_diff(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/screen/diff")
        # May be 404 if only one screen exists
        if r.status_code == 200:
            data = r.json()
            assert "current_date" in data
            assert "new_picks" in data
            assert "dropped_picks" in data
            assert "changed_scores" in data


class TestStockEndpoints:
    def test_get_stock(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        # First find a valid ticker
        screen = client.get("/api/v1/screen").json()
        ticker = screen["stocks"][0]["ticker"]

        r = client.get(f"/api/v1/stock/{ticker}")
        assert r.status_code == 200
        data = r.json()
        assert data["ticker"] == ticker
        assert "value_score" in data
        assert "piotroski_breakdown" in data

    def test_get_stock_not_found(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/stock/ZZZZZ")
        assert r.status_code == 404

    def test_get_stock_peers(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        screen = client.get("/api/v1/screen").json()
        ticker = screen["stocks"][0]["ticker"]

        r = client.get(f"/api/v1/stock/{ticker}/peers")
        assert r.status_code == 200
        data = r.json()
        assert data["ticker"] == ticker
        assert "sector" in data
        assert "peers" in data
        assert len(data["peers"]) > 0

    def test_get_stock_history(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/stock/MO/history")
        if r.status_code == 200:
            data = r.json()
            assert data["ticker"] == "MO"
            assert "history" in data


class TestSearchEndpoint:
    def test_search_by_ticker(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/search?q=AAPL")
        assert r.status_code == 200
        data = r.json()
        assert len(data["results"]) > 0
        assert data["results"][0]["ticker"] == "AAPL"

    def test_search_by_company(self, client, has_screen_data):
        if not has_screen_data:
            pytest.skip("No screen data available")
        r = client.get("/api/v1/search?q=apple")
        assert r.status_code == 200
        assert len(r.json()["results"]) > 0

    def test_search_empty(self, client):
        r = client.get("/api/v1/search?q=")
        assert r.status_code == 200
        assert r.json()["results"] == []


class TestBacktestEndpoint:
    def test_get_backtest(self, client, has_backtest_data):
        if not has_backtest_data:
            pytest.skip("No backtest data available")
        r = client.get("/api/v1/backtest")
        assert r.status_code == 200
        data = r.json()
        assert "quarters" in data
        assert "picks" in data
        assert len(data["quarters"]) > 0

    def test_backtest_quarter_shape(self, client, has_backtest_data):
        if not has_backtest_data:
            pytest.skip("No backtest data available")
        r = client.get("/api/v1/backtest")
        quarter = r.json()["quarters"][0]
        required = ["date", "num_picks", "portfolio_return", "universe_return", "spy_return"]
        for field in required:
            assert field in quarter, f"Missing field: {field}"


class TestHealthAndStatus:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_screen_status(self, client):
        r = client.get("/api/v1/screen/status")
        assert r.status_code == 200
        assert "running" in r.json()
