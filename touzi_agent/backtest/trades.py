from dataclasses import dataclass

from touzi_agent.quant.trade import Side


@dataclass(frozen=True)
class SimTrade:
    symbol: str
    side: str
    entry: float
    stop: float
    exit: float
    qty: int
    entry_cost: float
    exit_cost: float
    entry_date: str
    exit_date: str
    reason: str

    @property
    def gross_pnl(self) -> float:
        if self.side == Side.LONG:
            return (self.exit - self.entry) * self.qty
        return (self.entry - self.exit) * self.qty

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.entry_cost - self.exit_cost

    @property
    def dollar_risk(self) -> float:
        return abs(self.entry - self.stop) * self.qty

    @property
    def net_r(self) -> float:
        return self.net_pnl / self.dollar_risk
