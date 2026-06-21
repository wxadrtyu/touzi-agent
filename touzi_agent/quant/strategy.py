from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from touzi_agent.models import Bar


class StrategyStatus(Enum):
    CANDIDATE = "candidate"
    PROBATION = "probation"
    PROMOTED = "promoted"
    RETIRED = "retired"


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: str
    entry: float
    stop: float
    target: float | None = None
    cluster: str = ""
    meta: dict | None = None


class Strategy(ABC):
    name: str
    status: StrategyStatus
    universe: list[str]

    @abstractmethod
    def generate(self, bars_by_symbol: dict[str, list[Bar]]) -> list[Signal]:
        ...
