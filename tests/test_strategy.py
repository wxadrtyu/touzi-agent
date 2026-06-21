import pytest
from touzi_agent.models import Bar
from touzi_agent.quant.strategy import Signal, Strategy, StrategyStatus


def test_signal_defaults():
    s = Signal(symbol="US.AAPL", side="LONG", entry=100, stop=98)
    assert s.target is None
    assert s.cluster == ""


def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        Strategy()  # cannot instantiate ABC with abstract generate


def test_concrete_strategy_generates_signals():
    class AlwaysBuy(Strategy):
        name = "always_buy"
        status = StrategyStatus.CANDIDATE
        universe = ["US.AAPL"]

        def generate(self, bars_by_symbol):
            out = []
            for sym, bars in bars_by_symbol.items():
                last = bars[-1]
                out.append(Signal(symbol=sym, side="LONG",
                                  entry=last.close, stop=last.low))
            return out

    strat = AlwaysBuy()
    bars = {"US.AAPL": [Bar("US.AAPL", "2026-06-19", 1, 2, 0.5, 1.5, 10, 15.0)]}
    signals = strat.generate(bars)
    assert signals[0].symbol == "US.AAPL"
    assert signals[0].entry == 1.5
    assert strat.status == StrategyStatus.CANDIDATE
