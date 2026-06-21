from touzi_agent.models import Bar
from touzi_agent.quant.trade import Side
from touzi_agent.backtest.exits import resolve_exit


def _bar(high, low):
    return Bar("T", "2026-01-02", open=100, high=high, low=low,
               close=100, volume=1, turnover=1.0)


def test_long_stop_hit():
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(105, 97)) == (98, "stop")


def test_long_target_hit():
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(107, 99)) == (106, "target")


def test_long_stop_priority_when_both():
    # range hits both -> stop wins
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(107, 97)) == (98, "stop")


def test_long_neither():
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(105, 99)) is None


def test_short_stop_hit():
    assert resolve_exit(Side.SHORT, stop=102, target=96, bar=_bar(103, 100)) == (102, "stop")


def test_short_target_hit():
    assert resolve_exit(Side.SHORT, stop=102, target=96, bar=_bar(101, 95)) == (96, "target")


def test_no_target_only_stop():
    assert resolve_exit(Side.LONG, stop=98, target=None, bar=_bar(105, 99)) is None
    assert resolve_exit(Side.LONG, stop=98, target=None, bar=_bar(105, 97)) == (98, "stop")
