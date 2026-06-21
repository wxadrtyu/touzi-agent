from dataclasses import dataclass

from touzi_agent.backtest.trades import SimTrade
from touzi_agent.quant.expectancy import expectancy, ExpectancyStats


def max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        if peak > 0:
            drop = (peak - value) / peak
            if drop > worst:
                worst = drop
    return worst


@dataclass(frozen=True)
class BacktestResult:
    trades: list[SimTrade]
    equity_curve: list[float]
    total_return: float
    max_drawdown: float
    final_equity: float
    stats: ExpectancyStats | None


def build_result(trades: list[SimTrade],
                 start_equity: float) -> BacktestResult:
    ordered = sorted(trades, key=lambda t: t.exit_date)
    equity_curve = [start_equity]
    running = start_equity
    for t in ordered:
        running += t.net_pnl
        equity_curve.append(running)
    total_return = (running - start_equity) / start_equity
    stats = expectancy([t.net_r for t in ordered]) if ordered else None
    return BacktestResult(
        trades=ordered,
        equity_curve=equity_curve,
        total_return=total_return,
        max_drawdown=max_drawdown(equity_curve),
        final_equity=running,
        stats=stats,
    )
