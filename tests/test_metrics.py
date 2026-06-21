import pytest
from touzi_agent.quant.trade import Side
from touzi_agent.backtest.trades import SimTrade
from touzi_agent.backtest.metrics import max_drawdown, build_result


def test_max_drawdown_simple():
    assert max_drawdown([100, 120, 90, 110]) == pytest.approx((120 - 90) / 120)


def test_max_drawdown_monotonic_is_zero():
    assert max_drawdown([100, 110, 120]) == 0.0


def _trade(net_pnl, exit_date, entry=100, stop=98, qty=500):
    # craft exit so gross == net_pnl (no costs); long
    exit = entry + net_pnl / qty
    return SimTrade("T", Side.LONG, entry, stop, exit, qty, 0.0, 0.0,
                    "2026-01-01", exit_date, "target")


def test_build_result_orders_and_aggregates():
    trades = [
        _trade(+1000, "2026-01-03"),
        _trade(-500, "2026-01-02"),
    ]
    res = build_result(trades, start_equity=100000)
    # ordered by exit_date: -500 then +1000
    assert res.equity_curve == [100000, 99500, 100500]
    assert res.final_equity == 100500
    assert res.total_return == pytest.approx(0.005)
    assert res.stats.n == 2


def test_build_result_no_trades():
    res = build_result([], start_equity=100000)
    assert res.trades == []
    assert res.equity_curve == [100000]
    assert res.total_return == 0.0
    assert res.max_drawdown == 0.0
    assert res.stats is None
