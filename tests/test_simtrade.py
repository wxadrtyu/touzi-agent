from touzi_agent.quant.trade import Side
from touzi_agent.backtest.trades import SimTrade


def _t(side, entry, stop, exit, qty, ec=0.0, xc=0.0):
    return SimTrade(symbol="T", side=side, entry=entry, stop=stop, exit=exit,
                    qty=qty, entry_cost=ec, exit_cost=xc,
                    entry_date="2026-01-01", exit_date="2026-01-02",
                    reason="target")


def test_long_net_r_no_costs():
    t = _t(Side.LONG, 100, 98, 106, 500)
    assert t.gross_pnl == 3000
    assert t.dollar_risk == 1000
    assert t.net_r == 3.0


def test_long_net_r_with_costs():
    t = _t(Side.LONG, 100, 98, 106, 500, ec=15.0, xc=15.9)
    assert t.net_pnl == 3000 - 15.0 - 15.9
    assert t.net_r == (3000 - 30.9) / 1000


def test_short_pnl():
    t = _t(Side.SHORT, 100, 102, 96, 500)
    assert t.gross_pnl == 2000
    assert t.net_r == 2.0
