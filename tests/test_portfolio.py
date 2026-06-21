import pytest
from touzi_agent.quant.portfolio import Position, Portfolio


def _pos(sym, qty, entry, stop, market="US", cluster=""):
    return Position(symbol=sym, side="LONG", qty=qty, entry=entry,
                    stop=stop, market=market, cluster=cluster)


def test_position_derived_values():
    p = _pos("US.AAPL", 100, 100, 98)
    assert p.notional == 10000
    assert p.open_risk == 200


def test_total_heat():
    pf = Portfolio(equity=100000, positions=[
        _pos("US.AAPL", 100, 100, 98),   # risk 200
        _pos("US.MSFT", 50, 200, 196),   # risk 200
    ])
    assert pf.total_heat() == pytest.approx(0.004)


def test_market_and_cluster_exposure():
    pf = Portfolio(equity=100000, positions=[
        _pos("US.AAPL", 100, 100, 98, market="US", cluster="ai"),
        _pos("HK.00700", 100, 300, 290, market="HK", cluster="ai"),
    ])
    assert pf.market_exposure("US") == pytest.approx(0.10)
    assert pf.cluster_exposure("ai") == pytest.approx(0.40)


def test_drawdown():
    pf = Portfolio(equity=80000, positions=[], peak_equity=100000)
    assert pf.drawdown() == pytest.approx(0.20)


def test_peak_defaults_to_equity():
    pf = Portfolio(equity=100000, positions=[])
    assert pf.drawdown() == 0.0
