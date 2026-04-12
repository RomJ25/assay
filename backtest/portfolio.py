"""Portfolio simulation — equal-weight with three return series."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date

from config import RISK_FREE_RATE
from backtest.cache import HistoricalCache

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    total_return: float
    universe_total_return: float
    spy_total_return: float
    cagr: float
    universe_cagr: float
    spy_cagr: float
    selection_alpha: float  # portfolio CAGR - universe CAGR
    max_drawdown: float
    sharpe_ratio: float
    hit_rate: float  # % of stock-quarters beating universe mean
    avg_excess_return: float  # per pick per quarter vs universe
    avg_turnover: float
    total_quarters: int
    avg_picks_per_quarter: float


def simulate_portfolio(
    quarterly_picks: list[tuple[date, list[str]]],
    quarterly_universe: list[tuple[date, list[str]]],
    cache: HistoricalCache,
    rebalance_dates: list[date],
    tcost_bps: int = 0,
) -> tuple[list[dict], BacktestMetrics]:
    """Simulate equal-weight portfolio and compute three return series.

    Returns:
        (per_quarter_records, metrics)
    """
    records = []
    portfolio_values = [1.0]  # cumulative value series for drawdown
    universe_values = [1.0]
    spy_values = [1.0]

    hits = 0
    total_stock_quarters = 0
    excess_returns_sum = 0.0
    turnovers = []
    prev_picks = set()
    picks_counts = []

    for i, (rebal_date, picks) in enumerate(quarterly_picks):
        # Find the next rebalance date (or use last available)
        next_date = _find_next_date(rebal_date, rebalance_dates)
        if next_date is None:
            continue

        # Find matching universe for this date
        universe_tickers = []
        for ud, ut in quarterly_universe:
            if ud == rebal_date:
                universe_tickers = ut
                break

        # Compute returns for the quarter
        portfolio_ret = _compute_equal_weight_return(picks, rebal_date, next_date, cache)
        universe_ret = _compute_equal_weight_return(universe_tickers, rebal_date, next_date, cache)
        spy_ret = _compute_ticker_return("SPY", rebal_date, next_date, cache)

        if portfolio_ret is None or universe_ret is None or spy_ret is None:
            logger.warning(f"{rebal_date}: could not compute returns, skipping")
            continue

        # Turnover (computed before cumulative update so costs can be deducted)
        current_picks_set = set(picks)
        quarter_turnover = None
        if prev_picks:
            sym_diff = len(prev_picks.symmetric_difference(current_picks_set))
            total = len(prev_picks.union(current_picks_set))
            quarter_turnover = sym_diff / total * 100 if total > 0 else 0
            turnovers.append(quarter_turnover)
        prev_picks = current_picks_set
        picks_counts.append(len(picks))

        # Deduct transaction costs from portfolio return
        if tcost_bps > 0 and quarter_turnover is not None:
            portfolio_ret -= (quarter_turnover / 100) * (tcost_bps / 10000)

        # Update cumulative values
        portfolio_values.append(portfolio_values[-1] * (1 + portfolio_ret))
        universe_values.append(universe_values[-1] * (1 + universe_ret))
        spy_values.append(spy_values[-1] * (1 + spy_ret))

        # Hit rate: how many individual picks beat the universe mean?
        individual_rets = _compute_individual_returns(picks, rebal_date, next_date, cache)
        for _, ret in individual_rets:
            total_stock_quarters += 1
            if ret > universe_ret:
                hits += 1
            excess_returns_sum += ret - universe_ret

        records.append({
            "date": rebal_date.isoformat(),
            "next_date": next_date.isoformat(),
            "num_picks": len(picks),
            "portfolio_return": round(portfolio_ret * 100, 2),
            "universe_return": round(universe_ret * 100, 2),
            "spy_return": round(spy_ret * 100, 2),
            "excess_return": round((portfolio_ret - universe_ret) * 100, 2),
            "turnover": round(quarter_turnover, 1) if quarter_turnover is not None else None,
        })

    # Compute aggregate metrics
    n_quarters = len(records)
    if n_quarters == 0:
        return records, _empty_metrics()

    total_return = portfolio_values[-1] - 1
    universe_total = universe_values[-1] - 1
    spy_total = spy_values[-1] - 1

    years = n_quarters / 4.0
    cagr = _cagr(portfolio_values[-1], years)
    universe_cagr = _cagr(universe_values[-1], years)
    spy_cagr = _cagr(spy_values[-1], years)

    # Quarterly returns for Sharpe
    quarterly_rets = []
    for i in range(1, len(portfolio_values)):
        quarterly_rets.append(portfolio_values[i] / portfolio_values[i - 1] - 1)

    metrics = BacktestMetrics(
        total_return=total_return,
        universe_total_return=universe_total,
        spy_total_return=spy_total,
        cagr=cagr,
        universe_cagr=universe_cagr,
        spy_cagr=spy_cagr,
        selection_alpha=cagr - universe_cagr,
        max_drawdown=_max_drawdown(portfolio_values),
        sharpe_ratio=_sharpe(quarterly_rets),
        hit_rate=hits / total_stock_quarters * 100 if total_stock_quarters > 0 else 0,
        avg_excess_return=excess_returns_sum / total_stock_quarters * 100 if total_stock_quarters > 0 else 0,
        avg_turnover=sum(turnovers) / len(turnovers) if turnovers else 0,
        total_quarters=n_quarters,
        avg_picks_per_quarter=sum(picks_counts) / len(picks_counts) if picks_counts else 0,
    )

    return records, metrics


def simulate_selective_sell(
    quarterly_snapshots: list[tuple[date, dict[str, str]]],
    quarterly_universe: list[tuple[date, list[str]]],
    cache: HistoricalCache,
    rebalance_dates: list[date],
    tcost_bps: int = 0,
) -> tuple[list[dict], BacktestMetrics]:
    """Simulate selective-sell portfolio aligned with STRATEGY.md.

    Instead of selling everything that leaves CB each quarter, this strategy:
    - BUYS when a stock enters CONVICTION BUY
    - HOLDS if it moves to WATCH LIST or QUALITY GROWTH PREMIUM
    - SELLS on VALUE TRAP, AVOID, OVERVALUED, or INSUFFICIENT DATA
    - MONITORS HOLD for one quarter; sells if HOLD persists 2+ consecutive quarters

    Args:
        quarterly_snapshots: list of (date, {ticker: classification}) for all stocks
        quarterly_universe: list of (date, [tickers]) for benchmark
        cache: price data
        rebalance_dates: all quarter-end dates
        tcost_bps: transaction cost per rebalance
    """
    SELL_CLASSIFICATIONS = {"VALUE TRAP", "AVOID", "OVERVALUED", "INSUFFICIENT DATA"}

    records = []
    portfolio = set()  # accumulates over time
    portfolio_values = [1.0]
    universe_values = [1.0]
    spy_values = [1.0]
    hits = 0
    total_stock_quarters = 0
    excess_returns_sum = 0.0
    turnovers = []
    picks_counts = []
    prev_portfolio = set()
    hold_quarters: dict[str, int] = {}  # ticker -> consecutive quarters in HOLD

    for rebal_date, classifications in quarterly_snapshots:
        next_date = _find_next_date(rebal_date, rebalance_dates)
        if next_date is None:
            continue

        # Find matching universe
        universe_tickers = []
        for ud, ut in quarterly_universe:
            if ud == rebal_date:
                universe_tickers = ut
                break

        # Add new CB entries
        new_cb = {t for t, cl in classifications.items() if cl == "CONVICTION BUY"}
        added_count = len(new_cb - prev_portfolio)  # compute BEFORE updating prev_portfolio
        portfolio.update(new_cb)

        # Track consecutive HOLD quarters — sell after 2+ consecutive
        current_hold = {t for t in portfolio if classifications.get(t) == "HOLD"}
        new_hold_quarters: dict[str, int] = {}
        for t in current_hold:
            new_hold_quarters[t] = hold_quarters.get(t, 0) + 1
        hold_quarters = new_hold_quarters

        # Remove stocks that hit sell classifications or stayed in HOLD too long
        to_remove = {t for t in portfolio if classifications.get(t) in SELL_CLASSIFICATIONS}
        to_remove |= {t for t in portfolio if hold_quarters.get(t, 0) >= 2}
        portfolio -= to_remove

        # Also remove stocks no longer in the screened universe (delisted, etc.)
        portfolio = {t for t in portfolio if t in classifications}

        active = list(portfolio)

        # Compute returns
        portfolio_ret = _compute_equal_weight_return(active, rebal_date, next_date, cache)
        universe_ret = _compute_equal_weight_return(universe_tickers, rebal_date, next_date, cache)
        spy_ret = _compute_ticker_return("SPY", rebal_date, next_date, cache)

        if portfolio_ret is None or universe_ret is None or spy_ret is None:
            continue

        # Turnover
        current_set = set(active)
        quarter_turnover = None
        if prev_portfolio:
            sym_diff = len(prev_portfolio.symmetric_difference(current_set))
            total = len(prev_portfolio.union(current_set))
            quarter_turnover = sym_diff / total * 100 if total > 0 else 0
            turnovers.append(quarter_turnover)
        prev_portfolio = current_set
        picks_counts.append(len(active))

        # Transaction costs
        if tcost_bps > 0 and quarter_turnover is not None:
            portfolio_ret -= (quarter_turnover / 100) * (tcost_bps / 10000)

        # Cumulative
        portfolio_values.append(portfolio_values[-1] * (1 + portfolio_ret))
        universe_values.append(universe_values[-1] * (1 + universe_ret))
        spy_values.append(spy_values[-1] * (1 + spy_ret))

        # Hit rate
        individual_rets = _compute_individual_returns(active, rebal_date, next_date, cache)
        for _, ret in individual_rets:
            total_stock_quarters += 1
            if ret > universe_ret:
                hits += 1
            excess_returns_sum += ret - universe_ret

        records.append({
            "date": rebal_date.isoformat(),
            "next_date": next_date.isoformat(),
            "num_picks": len(active),
            "portfolio_return": round(portfolio_ret * 100, 2),
            "universe_return": round(universe_ret * 100, 2),
            "spy_return": round(spy_ret * 100, 2),
            "excess_return": round((portfolio_ret - universe_ret) * 100, 2),
            "turnover": round(quarter_turnover, 1) if quarter_turnover is not None else None,
            "added": added_count,
            "removed": len(to_remove),
        })

    # Aggregate metrics
    n_quarters = len(records)
    if n_quarters == 0:
        return records, _empty_metrics()

    total_return = portfolio_values[-1] - 1
    universe_total = universe_values[-1] - 1
    spy_total = spy_values[-1] - 1
    years = n_quarters / 4.0
    cagr_val = _cagr(portfolio_values[-1], years)
    universe_cagr = _cagr(universe_values[-1], years)
    spy_cagr_val = _cagr(spy_values[-1], years)

    quarterly_rets = [portfolio_values[i] / portfolio_values[i - 1] - 1 for i in range(1, len(portfolio_values))]

    metrics = BacktestMetrics(
        total_return=total_return,
        universe_total_return=universe_total,
        spy_total_return=spy_total,
        cagr=cagr_val,
        universe_cagr=universe_cagr,
        spy_cagr=spy_cagr_val,
        selection_alpha=cagr_val - universe_cagr,
        max_drawdown=_max_drawdown(portfolio_values),
        sharpe_ratio=_sharpe(quarterly_rets),
        hit_rate=hits / total_stock_quarters * 100 if total_stock_quarters > 0 else 0,
        avg_excess_return=excess_returns_sum / total_stock_quarters * 100 if total_stock_quarters > 0 else 0,
        avg_turnover=sum(turnovers) / len(turnovers) if turnovers else 0,
        total_quarters=n_quarters,
        avg_picks_per_quarter=sum(picks_counts) / len(picks_counts) if picks_counts else 0,
    )

    return records, metrics


def _find_next_date(current: date, all_dates: list[date]) -> date | None:
    """Find the next rebalance date after current."""
    for d in all_dates:
        if d > current:
            return d
    return None


def _compute_equal_weight_return(
    tickers: list[str],
    start_date: date,
    end_date: date,
    cache: HistoricalCache,
) -> float | None:
    """Compute equal-weight portfolio return using Adj Close."""
    if not tickers:
        return 0.0  # cash position — don't skip the quarter

    returns = []
    for ticker in tickers:
        ret = _compute_ticker_return(ticker, start_date, end_date, cache)
        if ret is not None:
            returns.append(ret)

    if not returns:
        return None

    return sum(returns) / len(returns)


def _compute_ticker_return(
    ticker: str,
    start_date: date,
    end_date: date,
    cache: HistoricalCache,
) -> float | None:
    """Compute total return for a single ticker using Adj Close.

    If start price exists but end price is missing (delisting, acquisition),
    assumes 0% return rather than silently dropping the ticker.
    """
    start_data = cache.get_price(ticker, start_date.isoformat())
    if start_data is None:
        return None  # never had this stock

    _, adj_start = start_data
    if adj_start <= 0:
        return None

    end_data = cache.get_price(ticker, end_date.isoformat())
    if end_data is None:
        # Stock existed at start but has no end price — likely delisted/acquired.
        # Conservative assumption: 0% return (better than silently dropping).
        return 0.0

    _, adj_end = end_data
    return (adj_end - adj_start) / adj_start


def _compute_individual_returns(
    tickers: list[str],
    start_date: date,
    end_date: date,
    cache: HistoricalCache,
) -> list[tuple[str, float]]:
    """Compute individual returns for each ticker."""
    results = []
    for ticker in tickers:
        ret = _compute_ticker_return(ticker, start_date, end_date, cache)
        if ret is not None:
            results.append((ticker, ret))
    return results


def _cagr(final_value: float, years: float) -> float:
    """Compound Annual Growth Rate."""
    if years <= 0:
        return 0.0
    if final_value <= 0:
        return -1.0  # Total loss
    return final_value ** (1 / years) - 1


def _max_drawdown(values: list[float]) -> float:
    """Maximum peak-to-trough drawdown."""
    if len(values) < 2:
        return 0.0
    peak = values[0]
    max_dd = 0.0
    for v in values[1:]:
        if v > peak:
            peak = v
        dd = (peak - v) / peak
        if dd > max_dd:
            max_dd = dd
    return -max_dd  # negative convention


def _sharpe(quarterly_returns: list[float]) -> float:
    """Annualized Sharpe ratio from quarterly returns."""
    if len(quarterly_returns) < 2:
        return 0.0
    mean_q = sum(quarterly_returns) / len(quarterly_returns)
    var_q = sum((r - mean_q) ** 2 for r in quarterly_returns) / (len(quarterly_returns) - 1)
    std_q = math.sqrt(var_q) if var_q > 0 else 0.0
    if std_q == 0:
        return 0.0
    # Annualize: mean * 4, std * sqrt(4)
    rf_quarterly = (1 + RISK_FREE_RATE) ** 0.25 - 1
    excess_mean = mean_q - rf_quarterly
    return (excess_mean * 4) / (std_q * 2)


def _empty_metrics() -> BacktestMetrics:
    return BacktestMetrics(
        total_return=0, universe_total_return=0, spy_total_return=0,
        cagr=0, universe_cagr=0, spy_cagr=0, selection_alpha=0,
        max_drawdown=0, sharpe_ratio=0, hit_rate=0, avg_excess_return=0,
        avg_turnover=0, total_quarters=0, avg_picks_per_quarter=0,
    )
