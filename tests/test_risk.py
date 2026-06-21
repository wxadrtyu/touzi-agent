from touzi_agent.quant.portfolio import Position, Portfolio
from touzi_agent.quant.risk import RiskLimits, RiskModel


def _pos(sym, qty, entry, stop, market="US", cluster=""):
    return Position(symbol=sym, side="LONG", qty=qty, entry=entry,
                    stop=stop, market=market, cluster=cluster)


def test_allows_within_all_caps():
    rm = RiskModel(RiskLimits())
    pf = Portfolio(equity=100000, positions=[])
    cand = _pos("US.AAPL", 100, 100, 98)  # heat 0.002, pos 0.10
    assert rm.check(pf, cand).allowed is True


def test_blocks_when_heat_exceeded():
    rm = RiskModel(RiskLimits(max_total_heat=0.005))
    pf = Portfolio(equity=100000, positions=[_pos("US.MSFT", 100, 100, 96)])  # risk 400 -> 0.004
    cand = _pos("US.AAPL", 100, 100, 98)  # +200 -> total 0.006 > 0.005
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("heat" in r.lower() for r in decision.reasons)


def test_blocks_when_position_too_large():
    rm = RiskModel(RiskLimits(max_position_pct=0.05))
    pf = Portfolio(equity=100000, positions=[])
    cand = _pos("US.AAPL", 100, 100, 98)  # notional 10000 -> 0.10 > 0.05
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("position" in r.lower() for r in decision.reasons)


def test_blocks_when_market_cap_exceeded():
    rm = RiskModel(RiskLimits(max_market_pct=0.15))
    pf = Portfolio(equity=100000, positions=[_pos("US.MSFT", 100, 100, 98)])  # US 0.10
    cand = _pos("US.AAPL", 100, 100, 98)  # +0.10 -> 0.20 > 0.15
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("market" in r.lower() for r in decision.reasons)


def test_blocks_when_cluster_cap_exceeded():
    rm = RiskModel(RiskLimits(max_cluster_pct=0.15))
    pf = Portfolio(equity=100000, positions=[
        _pos("US.MSFT", 100, 100, 98, cluster="ai")])
    cand = _pos("US.AAPL", 100, 100, 98, cluster="ai")  # cluster 0.20 > 0.15
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("cluster" in r.lower() for r in decision.reasons)


def test_blocks_all_new_entries_in_drawdown():
    rm = RiskModel(RiskLimits(drawdown_derisk=0.20))
    pf = Portfolio(equity=80000, positions=[], peak_equity=100000)  # dd 0.20
    cand = _pos("US.AAPL", 1, 100, 98)
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("drawdown" in r.lower() for r in decision.reasons)
