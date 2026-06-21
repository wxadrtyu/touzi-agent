import pytest
from touzi_agent.quant.trade import Side, r_multiple, ClosedTrade


def test_long_win_is_positive_r():
    # risk = 2 (100->98), profit = 6 (100->106) => 3R
    assert r_multiple(100, 98, 106, Side.LONG) == 3.0


def test_long_loss_is_negative_r():
    assert r_multiple(100, 98, 98, Side.LONG) == -1.0


def test_short_win_is_positive_r():
    # risk = 2 (100->102), profit = 4 (100->96) => 2R
    assert r_multiple(100, 102, 96, Side.SHORT) == 2.0


def test_zero_risk_rejected():
    with pytest.raises(ValueError):
        r_multiple(100, 100, 110, Side.LONG)


def test_closed_trade_r_property():
    t = ClosedTrade(symbol="US.AAPL", side=Side.LONG, entry=100,
                    stop=98, exit=106, qty=10)
    assert t.r == 3.0
