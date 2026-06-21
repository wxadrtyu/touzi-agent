import pytest
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy, StrategyStatus, Signal
from touzi_agent.backtest.walkforward import walk_forward

ZERO_COST = MarketConfig(market="US", currency="USD", settlement="T+0",
                         short_selling="allowed", code_prefix="US",
                         daily_limit=None, costs={})


class OnceLong(Strategy):
    name = "once_long"
    status = StrategyStatus.CANDIDATE
    universe = ["T"]

    def generate(self, bars_by_symbol):
        for sym, bars in bars_by_symbol.items():
            if len(bars) == 1:
                return [Signal(sym, "LONG", 100, 98, 106)]
        return []


def _bar(date, h, low, c):
    return Bar("T", date, open=100, high=h, low=low, close=c,
               volume=1, turnover=1.0)


def test_walk_forward_aggregates_two_windows():
    bars = [
        _bar("2026-01-01", 101, 99, 100),
        _bar("2026-01-02", 107, 101, 105),   # window 1 target
        _bar("2026-02-01", 101, 99, 100),
        _bar("2026-02-02", 107, 101, 105),   # window 2 target
    ]
    windows = [("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28")]
    res = walk_forward(lambda: OnceLong(), {"T": bars}, windows,
                       ZERO_COST, start_equity=100000, risk_fraction=0.01)
    assert res.stats.n == 2
    assert all(t.reason == "target" for t in res.trades)
