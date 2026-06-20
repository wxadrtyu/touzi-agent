from touzi_agent.models import Bar, Instrument, MarketConfig


def test_bar_fields():
    bar = Bar(code="US.AAPL", date="2026-06-19", open=1.0, high=2.0,
              low=0.5, close=1.5, volume=100, turnover=150.0)
    assert bar.code == "US.AAPL"
    assert bar.close == 1.5


def test_instrument_fields():
    inst = Instrument(code="HK.00700", market="HK", name="TENCENT",
                      lot_size=100, board="main_board")
    assert inst.lot_size == 100


def test_market_config_limit_lookup():
    cfg = MarketConfig(market="CN", currency="CNY", settlement="T+1",
                       short_selling="restricted", code_prefix="",
                       daily_limit={"main_board": 0.10, "chinext": 0.20},
                       costs={"commission_rate": 0.0003})
    assert cfg.limit_for("main_board") == 0.10
    assert cfg.limit_for("chinext") == 0.20
    assert cfg.limit_for("unknown") is None


def test_market_config_no_limit_market():
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None, costs={})
    assert cfg.limit_for("main_board") is None
