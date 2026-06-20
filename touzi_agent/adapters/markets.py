from touzi_agent.models import MarketConfig
from touzi_agent.adapters.base import BaseDataAdapter
from touzi_agent.adapters.client import FutuClient


class USDataAdapter(BaseDataAdapter):
    pass


class HKDataAdapter(BaseDataAdapter):
    pass


class CNDataAdapter(BaseDataAdapter):
    def full_code(self, symbol: str) -> str:
        if symbol.endswith(".SH"):
            return f"SH.{symbol[:-3]}"
        if symbol.endswith(".SZ"):
            return f"SZ.{symbol[:-3]}"
        raise ValueError(
            f"CN symbol must end with .SH or .SZ, got {symbol!r}")


_BY_MARKET = {"US": USDataAdapter, "HK": HKDataAdapter, "CN": CNDataAdapter}


def build_adapter(config: MarketConfig, client: FutuClient) -> BaseDataAdapter:
    cls = _BY_MARKET.get(config.market)
    if cls is None:
        raise ValueError(f"no adapter for market {config.market!r}")
    return cls(config, client)
