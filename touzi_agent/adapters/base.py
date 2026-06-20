from touzi_agent.models import Bar, MarketConfig
from touzi_agent.adapters.client import FutuClient


class BaseDataAdapter:
    def __init__(self, config: MarketConfig, client: FutuClient):
        self.config = config
        self.client = client

    def full_code(self, symbol: str) -> str:
        prefix = self.config.code_prefix
        return f"{prefix}.{symbol}" if prefix else symbol

    def fetch_bars(self, symbol: str, start: str, end: str) -> list[Bar]:
        code = self.full_code(symbol)
        rows = self.client.get_history_kline(code, start, end)
        return [
            Bar(code=code, date=row["time_key"][:10],
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=int(row["volume"]),
                turnover=row["turnover"])
            for row in rows
        ]
