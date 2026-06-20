import pytest
from touzi_agent.models import MarketConfig


class FakeFutuClient:
    """In-memory stand-in for FutuClient; returns canned daily kline."""

    def __init__(self, rows=None):
        self._rows = rows if rows is not None else [
            {"time_key": "2026-06-18 00:00:00", "open": 1.5, "high": 2.5,
             "low": 1.0, "close": 2.0, "volume": 20, "turnover": 40.0},
            {"time_key": "2026-06-19 00:00:00", "open": 2.0, "high": 3.0,
             "low": 1.8, "close": 2.8, "volume": 30, "turnover": 84.0},
        ]
        self.calls = []

    def get_history_kline(self, code, start, end, ktype="K_DAY"):
        self.calls.append((code, start, end, ktype))
        return list(self._rows)


@pytest.fixture
def fake_client():
    return FakeFutuClient()


@pytest.fixture
def us_config():
    return MarketConfig(market="US", currency="USD", settlement="T+0",
                        short_selling="allowed", code_prefix="US",
                        daily_limit=None, costs={})
