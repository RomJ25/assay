"""Unit tests for backtest detail CSV gate audit trail (Slice C)."""

import csv
from datetime import date
from pathlib import Path

import pytest

from backtest.report import _gate_message, save_backtest_csv


def test_gate_message_no_gates():
    assert _gate_message({}) == ""
    assert _gate_message({"f_gate_fired": False, "momentum_gate_fired": False, "revenue_gate_fired": False}) == ""


def test_gate_message_single_gate():
    assert _gate_message({"f_gate_fired": True}) == "f<6"
    assert _gate_message({"momentum_gate_fired": True}) == "momentum<25th%"
    assert _gate_message({"revenue_gate_fired": True}) == "revenue declining 2+yr"


def test_gate_message_multiple_gates():
    msg = _gate_message({
        "f_gate_fired": True,
        "momentum_gate_fired": True,
        "revenue_gate_fired": False,
    })
    assert "f<6" in msg and "momentum<25th%" in msg
    assert "; " in msg


def test_gate_message_all_three():
    msg = _gate_message({
        "f_gate_fired": True,
        "momentum_gate_fired": True,
        "revenue_gate_fired": True,
    })
    assert msg == "f<6; momentum<25th%; revenue declining 2+yr"


class _FakeQuarter:
    def __init__(self, d: date, picks: list[dict]):
        self.date = d
        self.pick_details = picks


class _FakeMetrics:
    selection_alpha = 0.0
    total_return = 0.0
    universe_total_return = 0.0
    spy_total_return = 0.0
    cagr = 0.0
    universe_cagr = 0.0
    spy_cagr = 0.0
    max_drawdown = 0.0
    sharpe_ratio = 0.0
    avg_picks_per_quarter = 1.0
    hit_rate = 0.0
    avg_excess_return = 0.0
    avg_turnover = 0.0
    total_quarters = 1


class _FakeResult:
    def __init__(self, quarters):
        self.quarters = quarters
        self.portfolio_returns = []
        self.metrics = _FakeMetrics()
        self.effective_start = date(2024, 1, 1)
        self.effective_end = date(2024, 4, 1)
        self.survivorship_free = True
        self.selective_sell_metrics = None
        self.top_n_metrics = {}


def test_detail_csv_includes_gate_columns(tmp_path, monkeypatch):
    pick = {
        "ticker": "ACME",
        "sector": "Technology",
        "value_score": 80.0,
        "quality_score": 75.0,
        "piotroski_f": 5,
        "momentum_pct": 0.10,
        "f_gate_fired": True,
        "momentum_gate_fired": False,
        "revenue_gate_fired": False,
        "raw_classification": "RESEARCH CANDIDATE",
        "final_classification": "WATCH LIST",
    }
    result = _FakeResult([_FakeQuarter(date(2024, 1, 1), [pick])])

    import backtest.report as report
    monkeypatch.setattr(report, "RESULTS_DIR", tmp_path)
    save_backtest_csv(result)

    detail_path = tmp_path / f"backtest_detail_{date.today().isoformat()}.csv"
    assert detail_path.exists()

    with open(detail_path) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    row = rows[0]
    for col in ("f_gate_fired", "momentum_gate_fired", "revenue_gate_fired",
                "raw_classification", "final_classification", "gate_message"):
        assert col in row, f"missing column {col}"
    assert row["gate_message"] == "f<6"
    assert row["raw_classification"] == "RESEARCH CANDIDATE"
    assert row["final_classification"] == "WATCH LIST"
