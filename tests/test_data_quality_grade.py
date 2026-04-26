"""Unit tests for the red/yellow/green data-quality grade (Slice D)."""

from data.providers.base import FinancialData
from data.quality import grade_data_quality, YELLOW_FISCAL_AGE_THRESHOLD_DAYS


def _make_fd(**overrides) -> FinancialData:
    defaults = dict(
        ticker="ACME",
        company_name="Acme",
        sector="Technology",
        sub_industry="Software",
        current_price=100.0,
        market_cap=1e10,
        revenue=[1000.0, 900.0, 800.0, 700.0],
        net_income=[100.0, 90.0, 80.0, 70.0],
        data_source="yahooquery",
        fallback_used=False,
        fiscal_age_days=30,
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


def test_green_when_primary_provider_and_fresh_filing():
    fd = _make_fd()
    report = grade_data_quality(fd)
    assert report.grade == "green"
    assert report.warnings == ()


def test_red_when_current_price_missing():
    fd = _make_fd(current_price=0)
    report = grade_data_quality(fd)
    assert report.grade == "red"
    assert any("current_price" in w for w in report.warnings)


def test_red_when_revenue_missing():
    fd = _make_fd(revenue=[None, None, None, None])
    report = grade_data_quality(fd)
    assert report.grade == "red"


def test_red_when_revenue_zero_or_negative():
    fd = _make_fd(revenue=[0, 100, 100, 100])
    report = grade_data_quality(fd)
    assert report.grade == "red"


def test_red_when_net_income_missing():
    fd = _make_fd(net_income=[None, 0, 0, 0])
    report = grade_data_quality(fd)
    assert report.grade == "red"


def test_yellow_when_fallback_used():
    fd = _make_fd(data_source="yfinance_fallback", fallback_used=True)
    report = grade_data_quality(fd)
    assert report.grade == "yellow"
    assert any("fallback" in w for w in report.warnings)


def test_yellow_when_fiscal_age_exceeds_threshold():
    fd = _make_fd(fiscal_age_days=YELLOW_FISCAL_AGE_THRESHOLD_DAYS + 1)
    report = grade_data_quality(fd)
    assert report.grade == "yellow"
    assert any("filing" in w for w in report.warnings)


def test_yellow_combines_fallback_and_stale():
    fd = _make_fd(
        data_source="yfinance_fallback",
        fallback_used=True,
        fiscal_age_days=YELLOW_FISCAL_AGE_THRESHOLD_DAYS + 100,
    )
    report = grade_data_quality(fd)
    assert report.grade == "yellow"
    assert len(report.warnings) >= 2


def test_red_dominates_over_yellow():
    """A red condition should win even if a yellow condition is also present."""
    fd = _make_fd(current_price=0, fallback_used=True)
    report = grade_data_quality(fd)
    assert report.grade == "red"
