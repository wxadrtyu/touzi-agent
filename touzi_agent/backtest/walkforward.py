from typing import Callable

from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy
from touzi_agent.backtest.engine import backtest
from touzi_agent.backtest.metrics import build_result, BacktestResult


def walk_forward(make_strategy: Callable[[], Strategy],
                 bars_by_symbol: dict[str, list[Bar]],
                 windows: list[tuple[str, str]],
                 market_config: MarketConfig, start_equity: float,
                 risk_fraction: float, t_plus: int = 0,
                 lot_size: int = 1) -> BacktestResult:
    aggregated = []
    for start_date, end_date in windows:
        strategy = make_strategy()
        sliced = {
            sym: [b for b in bars if start_date <= b.date <= end_date]
            for sym, bars in bars_by_symbol.items()
        }
        res = backtest(strategy, sliced, market_config, start_equity,
                       risk_fraction, t_plus, lot_size)
        aggregated += res.trades
    return build_result(aggregated, start_equity)
