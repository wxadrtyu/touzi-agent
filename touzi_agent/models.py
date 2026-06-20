from dataclasses import dataclass


@dataclass(frozen=True)
class Bar:
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: float


@dataclass(frozen=True)
class Instrument:
    code: str
    market: str
    name: str
    lot_size: int
    board: str


@dataclass(frozen=True)
class MarketConfig:
    market: str
    currency: str
    settlement: str
    short_selling: str
    code_prefix: str
    daily_limit: dict | None
    costs: dict

    def limit_for(self, board: str) -> float | None:
        if not self.daily_limit:
            return None
        return self.daily_limit.get(board)
