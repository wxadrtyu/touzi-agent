from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Signal
from touzi_agent.quant.trade import Side
from touzi_agent.quant.sizing import size_position
from touzi_agent.quant.costs import compute_cost
from touzi_agent.backtest.exits import resolve_exit
from touzi_agent.backtest.trades import SimTrade


def _entry_side(side: str) -> str:
    return "BUY" if side == Side.LONG else "SELL"


def _exit_side(side: str) -> str:
    return "SELL" if side == Side.LONG else "BUY"


class PaperBroker:
    def __init__(self, market_config: MarketConfig, equity: float,
                 risk_fraction: float, lot_size: int = 1):
        self.market_config = market_config
        self.equity = equity
        self.risk_fraction = risk_fraction
        self.lot_size = lot_size
        self.open_positions: dict[str, dict] = {}
        self.closed_trades: list[SimTrade] = []

    def submit(self, signal: Signal, date: str) -> bool:
        if signal.symbol in self.open_positions:
            return False
        qty = size_position(self.equity, self.risk_fraction, signal.entry,
                            signal.stop, self.lot_size)
        if qty <= 0:
            return False
        entry_cost = compute_cost(self.market_config,
                                  _entry_side(signal.side), signal.entry, qty)
        self.open_positions[signal.symbol] = {
            "side": signal.side, "entry": signal.entry, "stop": signal.stop,
            "target": signal.target, "qty": qty, "entry_cost": entry_cost,
            "entry_date": date,
        }
        return True

    def on_bar(self, bar: Bar) -> SimTrade | None:
        pos = self.open_positions.get(bar.code)
        if pos is None or bar.date <= pos["entry_date"]:
            return None
        hit = resolve_exit(pos["side"], pos["stop"], pos["target"], bar)
        if hit is None:
            return None
        exit_price, reason = hit
        exit_cost = compute_cost(self.market_config, _exit_side(pos["side"]),
                                 exit_price, pos["qty"])
        trade = SimTrade(
            symbol=bar.code, side=pos["side"], entry=pos["entry"],
            stop=pos["stop"], exit=exit_price, qty=pos["qty"],
            entry_cost=pos["entry_cost"], exit_cost=exit_cost,
            entry_date=pos["entry_date"], exit_date=bar.date, reason=reason,
        )
        del self.open_positions[bar.code]
        self.closed_trades.append(trade)
        return trade
