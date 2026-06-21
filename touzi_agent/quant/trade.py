from dataclasses import dataclass


class Side:
    LONG = "LONG"
    SHORT = "SHORT"


def r_multiple(entry: float, stop: float, exit: float, side: str) -> float:
    risk = abs(entry - stop)
    if risk == 0:
        raise ValueError("entry and stop must differ (risk cannot be 0)")
    profit = (exit - entry) if side == Side.LONG else (entry - exit)
    return profit / risk


@dataclass(frozen=True)
class ClosedTrade:
    symbol: str
    side: str
    entry: float
    stop: float
    exit: float
    qty: int

    @property
    def r(self) -> float:
        return r_multiple(self.entry, self.stop, self.exit, self.side)
