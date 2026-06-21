from dataclasses import dataclass, field


@dataclass(frozen=True)
class Position:
    symbol: str
    side: str
    qty: int
    entry: float
    stop: float
    market: str
    cluster: str = ""

    @property
    def notional(self) -> float:
        return self.entry * self.qty

    @property
    def open_risk(self) -> float:
        return abs(self.entry - self.stop) * self.qty


@dataclass
class Portfolio:
    equity: float
    positions: list[Position] = field(default_factory=list)
    peak_equity: float | None = None

    def __post_init__(self):
        if self.peak_equity is None:
            self.peak_equity = self.equity

    def total_heat(self) -> float:
        return sum(p.open_risk for p in self.positions) / self.equity

    def market_exposure(self, market: str) -> float:
        return sum(p.notional for p in self.positions
                   if p.market == market) / self.equity

    def cluster_exposure(self, cluster: str) -> float:
        return sum(p.notional for p in self.positions
                   if p.cluster == cluster) / self.equity

    def drawdown(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return (self.peak_equity - self.equity) / self.peak_equity
