from touzi_agent.models import MarketConfig
from touzi_agent.quant.costs import compute_cost
import pytest


def _cfg(market, costs):
    return MarketConfig(market=market, currency="X", settlement="T+0",
                        short_selling="x", code_prefix="", daily_limit=None,
                        costs=costs)


def test_us_commission_floor_applies():
    cfg = _cfg("US", {"commission_rate": 0.0003, "min_commission": 0.99})
    # notional = 100*1 = 100; rate cost = 0.03 -> floored to 0.99
    assert compute_cost(cfg, "BUY", 100, 1) == pytest.approx(0.99)


def test_cn_stamp_on_sell_only():
    cfg = _cfg("CN", {"commission_rate": 0.0, "min_commission": 0.0,
                      "stamp_duty": 0.0005, "transfer_fee": 0.0})
    notional = 10 * 1000  # 10000
    assert compute_cost(cfg, "BUY", 10, 1000) == pytest.approx(0.0)
    assert compute_cost(cfg, "SELL", 10, 1000) == pytest.approx(notional * 0.0005)


def test_hk_stamp_on_both_sides():
    cfg = _cfg("HK", {"commission_rate": 0.0, "min_commission": 0.0,
                      "stamp_duty": 0.0013, "platform_fee": 0.0})
    notional = 100 * 100  # 10000
    assert compute_cost(cfg, "BUY", 100, 100) == pytest.approx(notional * 0.0013)
    assert compute_cost(cfg, "SELL", 100, 100) == pytest.approx(notional * 0.0013)


def test_platform_and_transfer_fees_added():
    cfg = _cfg("HK", {"commission_rate": 0.0, "min_commission": 0.0,
                      "stamp_duty": 0.0, "platform_fee": 15.0})
    assert compute_cost(cfg, "BUY", 100, 100) == pytest.approx(15.0)
