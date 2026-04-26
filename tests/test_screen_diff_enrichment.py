"""Unit tests for the /screen/diff gate-flip enrichment (Slice E)."""

from api.routes import _explain_change


def _row(**overrides):
    base = {
        "ticker": "ACME",
        "classification": "RESEARCH CANDIDATE",
        "raw_classification": "RESEARCH CANDIDATE",
        "value_score": 80.0,
        "quality_score": 78.0,
        "conviction_score": 79.0,
        "piotroski_f": 7,
        "f_gate_fired": False,
        "momentum_gate_fired": False,
        "revenue_gate_fired": False,
    }
    base.update(overrides)
    return base


def test_no_change_yields_empty_deltas_and_no_gate_transitions():
    row = _row()
    out = _explain_change(row, row)
    assert out["metric_deltas"] == {}
    assert out["newly_fired"] == []
    assert out["newly_cleared"] == []


def test_metric_delta_is_reported():
    prior = _row(value_score=80, quality_score=78)
    current = _row(value_score=72, quality_score=78)
    out = _explain_change(prior, current)
    assert out["metric_deltas"]["value_score"] == {"previous": 80, "current": 72}
    assert "quality_score" not in out["metric_deltas"]


def test_newly_fired_gate_is_surfaced():
    prior = _row()
    current = _row(
        f_gate_fired=True,
        classification="WATCH LIST",
        raw_classification="RESEARCH CANDIDATE",
    )
    out = _explain_change(prior, current)
    assert "f_gate_fired" in out["newly_fired"]
    assert out["newly_cleared"] == []
    assert out["final_classification"] == {"previous": "RESEARCH CANDIDATE", "current": "WATCH LIST"}


def test_newly_cleared_gate_is_surfaced():
    prior = _row(momentum_gate_fired=True, classification="WATCH LIST")
    current = _row(momentum_gate_fired=False, classification="RESEARCH CANDIDATE")
    out = _explain_change(prior, current)
    assert "momentum_gate_fired" in out["newly_cleared"]
    assert out["newly_fired"] == []


def test_multiple_gates_independent():
    prior = _row(f_gate_fired=False, momentum_gate_fired=True)
    current = _row(f_gate_fired=True, momentum_gate_fired=False)
    out = _explain_change(prior, current)
    assert "f_gate_fired" in out["newly_fired"]
    assert "momentum_gate_fired" in out["newly_cleared"]


def test_tolerates_legacy_rows_without_gate_fields():
    """Older screen JSON only had revenue_gate_fired; treat missing fields as False."""
    prior = {"ticker": "ACME", "classification": "RESEARCH CANDIDATE"}
    current = {
        "ticker": "ACME",
        "classification": "WATCH LIST",
        "f_gate_fired": True,
        "momentum_gate_fired": False,
        "revenue_gate_fired": False,
    }
    out = _explain_change(prior, current)
    assert out["newly_fired"] == ["f_gate_fired"]
    # final_classification falls back to top-level classification when raw_classification absent.
    assert out["final_classification"]["previous"] == "RESEARCH CANDIDATE"


def test_raw_classification_falls_back_to_final_when_absent():
    prior = {"ticker": "ACME", "classification": "WATCH LIST"}
    current = {"ticker": "ACME", "classification": "AVOID"}
    out = _explain_change(prior, current)
    assert out["raw_classification"]["previous"] == "WATCH LIST"
    assert out["raw_classification"]["current"] == "AVOID"
