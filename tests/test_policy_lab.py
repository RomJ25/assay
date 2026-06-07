from datetime import date

import pytest

from backtest.engine import FullQuarterSnapshot, StockDetail
from research.policy_lab import (
    Policy,
    capital_ready,
    default_policies,
    evaluate_policy,
)


def _detail(
    ticker,
    *,
    sector="Tech",
    value=80,
    quality=80,
    conviction=80,
    momentum=60,
    raw="RESEARCH CANDIDATE",
    final="RESEARCH CANDIDATE",
):
    return StockDetail(
        ticker=ticker,
        sector=sector,
        value_score=value,
        quality_score=quality,
        conviction_score=conviction,
        piotroski_f=7,
        momentum_pct=momentum,
        raw_classification=raw,
        final_classification=final,
        f_gate_fired=False,
        momentum_gate_fired=False,
        revenue_gate_fired=False,
        confidence="MODERATE" if final == "RESEARCH CANDIDATE" else None,
    )


def _snapshot(day, details):
    return FullQuarterSnapshot(
        date=day,
        stock_details=details,
        classifications={"RESEARCH CANDIDATE": sum(1 for d in details if d.final_classification == "RESEARCH CANDIDATE")},
        num_screened=len(details),
    )


def test_current_cb_policy_selects_final_research_candidates():
    snap = _snapshot(
        date(2025, 3, 31),
        [
            _detail("A", conviction=85, final="RESEARCH CANDIDATE"),
            _detail("B", conviction=90, final="WATCH LIST", raw="RESEARCH CANDIDATE"),
            _detail("C", conviction=70, final="RESEARCH CANDIDATE"),
        ],
    )
    current = next(p for p in default_policies() if p.name == "current_cb")
    assert current.selector(snap) == ["A", "C"]


def test_raw_vq_policy_ignores_gate_downgrades():
    snap = _snapshot(
        date(2025, 3, 31),
        [
            _detail("A", conviction=85, final="RESEARCH CANDIDATE"),
            _detail("B", conviction=90, final="WATCH LIST", raw="RESEARCH CANDIDATE"),
            _detail("C", conviction=70, raw="HOLD", final="HOLD"),
        ],
    )
    raw = next(p for p in default_policies() if p.name == "raw_vq_no_gates")
    assert raw.selector(snap) == ["B", "A"]


def test_sector_capped_policy_limits_each_sector():
    snap = _snapshot(
        date(2025, 3, 31),
        [_detail(f"T{i}", sector="Tech", value=90 - i, quality=90, momentum=80) for i in range(9)]
        + [_detail(f"H{i}", sector="Health", value=85 - i, quality=88, momentum=75) for i in range(4)],
    )
    policy = next(p for p in default_policies() if p.name == "sector_capped_vq_mom")
    picks = policy.selector(snap)
    assert len([p for p in picks if p.startswith("T")]) == 5
    assert len([p for p in picks if p.startswith("H")]) == 4


def test_evaluate_policy_computes_excess_and_capital_gate():
    q1 = date(2025, 3, 31)
    q2 = date(2025, 6, 30)
    q3 = date(2025, 9, 30)
    snapshots = [
        (_snapshot(q1, [_detail("A"), _detail("B", final="HOLD", raw="HOLD")]), q2),
        (_snapshot(q2, [_detail("A"), _detail("B", final="HOLD", raw="HOLD")]), q3),
    ]
    returns = {
        (q1, q2): {"A": 0.10, "B": 0.00},
        (q2, q3): {"A": 0.05, "B": 0.00},
    }
    policy = Policy("a_only", "pick A", lambda snap: ["A"])
    result = evaluate_policy(policy, snapshots, returns)

    assert result.avg_picks == 1
    assert result.avg_unknown_sector_picks == 0
    assert result.avg_unknown_sector_pick_rate == 0
    assert result.hit_rate == 1.0
    assert result.cagr > result.universe_cagr
    ready, reasons = capital_ready(result)
    assert not ready
    assert any("quarters" in r for r in reasons)


def test_evaluate_policy_requires_two_quarters():
    q1 = date(2025, 3, 31)
    q2 = date(2025, 6, 30)
    snapshots = [(_snapshot(q1, [_detail("A")]), q2)]
    returns = {(q1, q2): {"A": 0.01}}
    policy = Policy("a_only", "pick A", lambda snap: ["A"])

    with pytest.raises(ValueError):
        evaluate_policy(policy, snapshots, returns)
