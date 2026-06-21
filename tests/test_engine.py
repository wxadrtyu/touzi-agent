import pytest
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy, StrategyStatus, Signal
from touzi_agent.backtest.engine import simulate_symbol, backtest

ZERO_COST = MarketConfig(market="US", currency="USD", settlement="T+0",
                         short_selling="allowed", code_prefix="US",
                         daily_limit=None, costs={})


class OnceLong(Strategy):
    """Emits a single LONG signal on the first bar it sees."""
    name = "once_long"
    status = StrategyStatus.CANDIDATE
    universe = ["T"]

    def __init__(self, entry, stop, target):
        self._e, self._s, self._t = entry, stop, target

    def generate(self, bars_by_symbol):
        for sym, bars in bars_by_symbol.items():
            if len(bars) == 1:
                return [Signal(sym, "LONG", self._e, self._s, self._t)]
        return []


def _bar(date, o, h, low, c):
    return Bar("T", date, open=o, high=h, low=low, close=c,
               volume=1, turnover=1.0)


def test_target_hit_produces_3r_trade():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),   # entry @100
        _bar("2026-01-02", 101, 107, 101, 105),  # target 106 hit
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, ZERO_COST,
                             equity=100000, risk_fraction=0.01)
    assert len(trades) == 1
    assert trades[0].reason == "target"
    assert trades[0].qty == 500  # risk $1000 / $2 per share
    assert trades[0].net_r == pytest.approx(3.0)


def test_stop_hit_produces_minus_1r():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 100, 101, 97, 99),   # stop 98 hit
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, ZERO_COST,
                             equity=100000, risk_fraction=0.01)
    assert trades[0].reason == "stop"
    assert trades[0].net_r == pytest.approx(-1.0)


def test_open_position_closed_at_eod():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 100, 105, 99, 104),  # neither stop nor target
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, ZERO_COST,
                             equity=100000, risk_fraction=0.01)
    assert trades[0].reason == "eod"
    assert trades[0].exit == 104


def test_costs_reduce_net_pnl():
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None,
                       costs={"commission_rate": 0.0003, "min_commission": 0.0})
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 101, 107, 101, 105),  # target 106
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, cfg,
                             equity=100000, risk_fraction=0.01)
    # entry commission 100*500*0.0003=15; exit 106*500*0.0003=15.9
    assert trades[0].entry_cost == pytest.approx(15.0)
    assert trades[0].exit_cost == pytest.approx(15.9)
    assert trades[0].net_pnl == pytest.approx(3000 - 30.9)


def test_backtest_aggregates_result():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 101, 107, 101, 105),
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    res = backtest(strat, {"T": bars}, ZERO_COST,
                   start_equity=100000, risk_fraction=0.01)
    assert res.stats.n == 1
    assert res.total_return == pytest.approx(0.03)
