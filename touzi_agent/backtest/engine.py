from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy
from touzi_agent.quant.trade import Side
from touzi_agent.quant.sizing import size_position
from touzi_agent.quant.costs import compute_cost
from touzi_agent.backtest.exits import resolve_exit
from touzi_agent.backtest.trades import SimTrade
from touzi_agent.backtest.metrics import build_result, BacktestResult


def _entry_side(side: str) -> str:
    return "BUY" if side == Side.LONG else "SELL"


def _exit_side(side: str) -> str:
    return "SELL" if side == Side.LONG else "BUY"


def simulate_symbol(strategy: Strategy, symbol: str, bars: list[Bar],
                    market_config: MarketConfig, equity: float,
                    risk_fraction: float, t_plus: int = 0,
                    lot_size: int = 1) -> list[SimTrade]:
    trades: list[SimTrade] = []
    pos = None

    for i, bar in enumerate(bars):
        if pos is None:
            signals = strategy.generate({symbol: bars[:i + 1]})
            sig = next((s for s in signals if s.symbol == symbol), None)
            if sig is None:
                continue
            qty = size_position(equity, risk_fraction, sig.entry,
                                sig.stop, lot_size)
            if qty <= 0:
                continue
            entry_cost = compute_cost(market_config, _entry_side(sig.side),
                                      sig.entry, qty)
            pos = {"side": sig.side, "entry": sig.entry, "stop": sig.stop,
                   "target": sig.target, "qty": qty,
                   "entry_cost": entry_cost, "entry_date": bar.date,
                   "entry_index": i}
            continue

        if i - pos["entry_index"] > t_plus:
            hit = resolve_exit(pos["side"], pos["stop"], pos["target"], bar)
            if hit is not None:
                exit_price, reason = hit
                exit_cost = compute_cost(market_config,
                                         _exit_side(pos["side"]),
                                         exit_price, pos["qty"])
                trades.append(_close(pos, exit_price, bar.date, reason,
                                     exit_cost, symbol))
                pos = None

    if pos is not None:
        last = bars[-1]
        exit_cost = compute_cost(market_config, _exit_side(pos["side"]),
                                 last.close, pos["qty"])
        trades.append(_close(pos, last.close, last.date, "eod",
                             exit_cost, symbol))

    return trades


def _close(pos: dict, exit_price: float, exit_date: str, reason: str,
           exit_cost: float, symbol: str) -> SimTrade:
    return SimTrade(
        symbol=symbol, side=pos["side"], entry=pos["entry"],
        stop=pos["stop"], exit=exit_price, qty=pos["qty"],
        entry_cost=pos["entry_cost"], exit_cost=exit_cost,
        entry_date=pos["entry_date"], exit_date=exit_date, reason=reason,
    )


def backtest(strategy: Strategy, bars_by_symbol: dict[str, list[Bar]],
             market_config: MarketConfig, start_equity: float,
             risk_fraction: float, t_plus: int = 0,
             lot_size: int = 1) -> BacktestResult:
    all_trades: list[SimTrade] = []
    for symbol, bars in bars_by_symbol.items():
        all_trades += simulate_symbol(strategy, symbol, bars, market_config,
                                      start_equity, risk_fraction, t_plus,
                                      lot_size)
    return build_result(all_trades, start_equity)
