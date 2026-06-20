import pytest
from touzi_agent.models import MarketConfig
from touzi_agent.adapters.markets import (
    USDataAdapter, HKDataAdapter, CNDataAdapter, build_adapter,
)


def _cfg(market, prefix):
    return MarketConfig(market=market, currency="X", settlement="T+1",
                        short_selling="x", code_prefix=prefix,
                        daily_limit=None, costs={})


def test_us_full_code(fake_client):
    a = USDataAdapter(_cfg("US", "US"), fake_client)
    assert a.full_code("AAPL") == "US.AAPL"


def test_hk_full_code(fake_client):
    a = HKDataAdapter(_cfg("HK", "HK"), fake_client)
    assert a.full_code("00700") == "HK.00700"


def test_cn_full_code_converts_suffix(fake_client):
    a = CNDataAdapter(_cfg("CN", ""), fake_client)
    assert a.full_code("600519.SH") == "SH.600519"
    assert a.full_code("000001.SZ") == "SZ.000001"


def test_cn_full_code_rejects_bad_symbol(fake_client):
    a = CNDataAdapter(_cfg("CN", ""), fake_client)
    with pytest.raises(ValueError):
        a.full_code("600519")


def test_build_adapter_dispatches_by_market(fake_client):
    assert isinstance(build_adapter(_cfg("US", "US"), fake_client),
                      USDataAdapter)
    assert isinstance(build_adapter(_cfg("CN", ""), fake_client),
                      CNDataAdapter)
