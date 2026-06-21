import pytest
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Signal
from touzi_agent.backtest.paper import PaperBroker

ZERO_COST = MarketConfig(market="US", currency="USD", settlement="T+0",
                         short_selling="allowed", code_prefix="US",
                         daily_limit=None, costs={})


def _bar(date, h, low, c):
    return Bar("T", date, open=100, high=h, low=low, close=c,
               volume=1, turnover=1.0)


def test_submit_opens_position():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    opened = pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    assert opened is True
    assert "T" in pb.open_positions


def test_no_exit_same_day():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    # same-day bar that would hit target must NOT close (T+1)
    assert pb.on_bar(_bar("2026-01-01", 107, 99, 105)) is None
    assert "T" in pb.open_positions


def test_exit_next_day_target():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    trade = pb.on_bar(_bar("2026-01-02", 107, 101, 105))
    assert trade is not None
    assert trade.reason == "target"
    assert trade.net_r == pytest.approx(3.0)
    assert "T" not in pb.open_positions
    assert pb.closed_trades == [trade]


def test_duplicate_submit_ignored_while_open():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    assert pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01") is False
