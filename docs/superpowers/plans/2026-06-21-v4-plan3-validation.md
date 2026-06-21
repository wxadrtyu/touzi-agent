# V4.0 Plan 3 — Validation (Backtest + Forward Paper-Trade) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the validation substrate: a deterministic bar-by-bar simulation engine that runs a `Strategy` through the Plan 2 quant core, a walk-forward harness for out-of-sample evaluation, and a stateful forward paper-trade broker — all producing net-of-cost, R-based metrics.

**Architecture:** A new `touzi_agent/backtest/` package. The same simulation primitives (`resolve_exit`, `SimTrade`, sizing, costs) power both the batch backtester and the incremental `PaperBroker`, so backtest and forward results are computed identically. Everything is deterministic and tested with synthetic bars — no market data or 富途 needed.

**Tech Stack:** Python 3.12, pytest, stdlib only. Reuses Plan 1 (`Bar`, `MarketConfig`) and Plan 2 (`Signal`, `Strategy`, `size_position`, `compute_cost`, `expectancy`).

## Global Constraints

- **Expectancy in R units, net of costs** — per-trade `net_r = net_pnl / dollar_risk`, where `dollar_risk = |entry−stop|·qty` (1R in dollars) and `net_pnl` already subtracts entry+exit costs. (spec §3, §4.4)
- **Two-track validation** — this engine serves rules-based backtests *and* forward paper-trading; the *certification gate* is forward paper-trading (this plan provides the substrate, not the promotion policy — that's Plan 4). (spec §5, §10)
- **Walk-forward / out-of-sample only** for backtest evaluation; never judge on a fitted window. (spec §5.4)
- **Stop priority:** if a bar's range hits both stop and target, assume the stop filled first (conservative). (risk-first)
- **Sizing uses starting equity** (fixed-fractional) within a run for deterministic, path-independent validation. Compounding is out of scope here.
- **TDD, DRY, YAGNI, frequent commits.** Toolchain: venv. Run tests: `.venv/Scripts/python.exe -m pytest`.

---

## File Structure

```
touzi_agent/backtest/
  __init__.py
  exits.py        # resolve_exit()
  trades.py       # SimTrade (net_pnl, dollar_risk, net_r)
  metrics.py      # max_drawdown(), BacktestResult, build_result()
  engine.py       # simulate_symbol(), backtest()
  walkforward.py  # walk_forward()
  paper.py        # PaperBroker
tests/
  test_exits.py
  test_simtrade.py
  test_metrics.py
  test_engine.py
  test_walkforward.py
  test_paper.py
```

---

### Task 1: Exit resolution

**Files:** Create `touzi_agent/backtest/__init__.py`, `touzi_agent/backtest/exits.py`; Test `tests/test_exits.py`.

**Interfaces:**
- Consumes: `Bar` (Plan 1), `Side` (Plan 2).
- Produces: `resolve_exit(side: str, stop: float, target: float | None, bar: Bar) -> tuple[float, str] | None` — returns `(exit_price, reason)` where reason ∈ `{"stop","target"}`, or `None` if neither triggered. Stop checked before target.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_exits.py
from touzi_agent.models import Bar
from touzi_agent.quant.trade import Side
from touzi_agent.backtest.exits import resolve_exit


def _bar(high, low):
    return Bar("T", "2026-01-02", open=100, high=high, low=low,
               close=100, volume=1, turnover=1.0)


def test_long_stop_hit():
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(105, 97)) == (98, "stop")


def test_long_target_hit():
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(107, 99)) == (106, "target")


def test_long_stop_priority_when_both():
    # range hits both -> stop wins
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(107, 97)) == (98, "stop")


def test_long_neither():
    assert resolve_exit(Side.LONG, stop=98, target=106, bar=_bar(105, 99)) is None


def test_short_stop_hit():
    assert resolve_exit(Side.SHORT, stop=102, target=96, bar=_bar(103, 100)) == (102, "stop")


def test_short_target_hit():
    assert resolve_exit(Side.SHORT, stop=102, target=96, bar=_bar(101, 95)) == (96, "target")


def test_no_target_only_stop():
    assert resolve_exit(Side.LONG, stop=98, target=None, bar=_bar(105, 99)) is None
    assert resolve_exit(Side.LONG, stop=98, target=None, bar=_bar(105, 97)) == (98, "stop")
```

- [ ] **Step 2: Run test, expect FAIL.** `.venv/Scripts/python.exe -m pytest tests/test_exits.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/backtest/__init__.py
```

```python
# touzi_agent/backtest/exits.py
from touzi_agent.models import Bar
from touzi_agent.quant.trade import Side


def resolve_exit(side: str, stop: float, target: float | None,
                 bar: Bar) -> tuple[float, str] | None:
    if side == Side.LONG:
        if bar.low <= stop:
            return (stop, "stop")
        if target is not None and bar.high >= target:
            return (target, "target")
    else:
        if bar.high >= stop:
            return (stop, "stop")
        if target is not None and bar.low <= target:
            return (target, "target")
    return None
```

- [ ] **Step 4: Run test, expect PASS** (7 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/backtest/__init__.py touzi_agent/backtest/exits.py tests/test_exits.py
git commit -m "feat: bar exit resolution (stop priority)"
```

---

### Task 2: SimTrade record

**Files:** Create `touzi_agent/backtest/trades.py`; Test `tests/test_simtrade.py`.

**Interfaces:**
- Consumes: `Side` (Plan 2).
- Produces: `SimTrade(symbol, side, entry, stop, exit, qty, entry_cost, exit_cost, entry_date, exit_date, reason)` frozen dataclass with properties `gross_pnl`, `net_pnl` (`= gross_pnl − entry_cost − exit_cost`), `dollar_risk` (`= |entry−stop|·qty`), `net_r` (`= net_pnl / dollar_risk`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_simtrade.py
from touzi_agent.quant.trade import Side
from touzi_agent.backtest.trades import SimTrade


def _t(side, entry, stop, exit, qty, ec=0.0, xc=0.0):
    return SimTrade(symbol="T", side=side, entry=entry, stop=stop, exit=exit,
                    qty=qty, entry_cost=ec, exit_cost=xc,
                    entry_date="2026-01-01", exit_date="2026-01-02",
                    reason="target")


def test_long_net_r_no_costs():
    t = _t(Side.LONG, 100, 98, 106, 500)
    assert t.gross_pnl == 3000
    assert t.dollar_risk == 1000
    assert t.net_r == 3.0


def test_long_net_r_with_costs():
    t = _t(Side.LONG, 100, 98, 106, 500, ec=15.0, xc=15.9)
    assert t.net_pnl == 3000 - 15.0 - 15.9
    assert t.net_r == (3000 - 30.9) / 1000


def test_short_pnl():
    t = _t(Side.SHORT, 100, 102, 96, 500)
    assert t.gross_pnl == 2000
    assert t.net_r == 2.0
```

- [ ] **Step 2: Run test, expect FAIL.** `.venv/Scripts/python.exe -m pytest tests/test_simtrade.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/backtest/trades.py
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
```

- [ ] **Step 4: Run test, expect PASS** (3 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/backtest/trades.py tests/test_simtrade.py
git commit -m "feat: SimTrade record with net-of-cost R"
```

---

### Task 3: Metrics + BacktestResult

**Files:** Create `touzi_agent/backtest/metrics.py`; Test `tests/test_metrics.py`.

**Interfaces:**
- Consumes: `SimTrade` (Task 2), `expectancy`/`ExpectancyStats` (Plan 2).
- Produces:
  - `max_drawdown(equity_curve: list[float]) -> float` — largest peak-to-trough drop as a positive fraction; `0.0` for non-decreasing curves.
  - `BacktestResult(trades, equity_curve, total_return, max_drawdown, final_equity, stats)` frozen dataclass (`stats: ExpectancyStats | None`).
  - `build_result(trades: list[SimTrade], start_equity: float) -> BacktestResult` — orders trades by `exit_date`, builds the equity curve by applying `net_pnl` sequentially, computes total return and max drawdown, and `stats = expectancy([t.net_r for t in trades])` (or `None` if no trades).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_metrics.py
import pytest
from touzi_agent.quant.trade import Side
from touzi_agent.backtest.trades import SimTrade
from touzi_agent.backtest.metrics import max_drawdown, build_result


def test_max_drawdown_simple():
    assert max_drawdown([100, 120, 90, 110]) == pytest.approx((120 - 90) / 120)


def test_max_drawdown_monotonic_is_zero():
    assert max_drawdown([100, 110, 120]) == 0.0


def _trade(net_pnl, exit_date, entry=100, stop=98, qty=500):
    # craft exit so gross == net_pnl (no costs); long
    exit = entry + net_pnl / qty
    return SimTrade("T", Side.LONG, entry, stop, exit, qty, 0.0, 0.0,
                    "2026-01-01", exit_date, "target")


def test_build_result_orders_and_aggregates():
    trades = [
        _trade(+1000, "2026-01-03"),
        _trade(-500, "2026-01-02"),
    ]
    res = build_result(trades, start_equity=100000)
    # ordered by exit_date: -500 then +1000
    assert res.equity_curve == [100000, 99500, 100500]
    assert res.final_equity == 100500
    assert res.total_return == pytest.approx(0.005)
    assert res.stats.n == 2


def test_build_result_no_trades():
    res = build_result([], start_equity=100000)
    assert res.trades == []
    assert res.equity_curve == [100000]
    assert res.total_return == 0.0
    assert res.max_drawdown == 0.0
    assert res.stats is None
```

- [ ] **Step 2: Run test, expect FAIL.** `.venv/Scripts/python.exe -m pytest tests/test_metrics.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/backtest/metrics.py
from dataclasses import dataclass

from touzi_agent.backtest.trades import SimTrade
from touzi_agent.quant.expectancy import expectancy, ExpectancyStats


def max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        if peak > 0:
            drop = (peak - value) / peak
            if drop > worst:
                worst = drop
    return worst


@dataclass(frozen=True)
class BacktestResult:
    trades: list[SimTrade]
    equity_curve: list[float]
    total_return: float
    max_drawdown: float
    final_equity: float
    stats: ExpectancyStats | None


def build_result(trades: list[SimTrade],
                 start_equity: float) -> BacktestResult:
    ordered = sorted(trades, key=lambda t: t.exit_date)
    equity_curve = [start_equity]
    running = start_equity
    for t in ordered:
        running += t.net_pnl
        equity_curve.append(running)
    total_return = (running - start_equity) / start_equity
    stats = expectancy([t.net_r for t in ordered]) if ordered else None
    return BacktestResult(
        trades=ordered,
        equity_curve=equity_curve,
        total_return=total_return,
        max_drawdown=max_drawdown(equity_curve),
        final_equity=running,
        stats=stats,
    )
```

- [ ] **Step 4: Run test, expect PASS** (4 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/backtest/metrics.py tests/test_metrics.py
git commit -m "feat: backtest metrics (max drawdown, result builder)"
```

---

### Task 4: Simulation engine

**Files:** Create `touzi_agent/backtest/engine.py`; Test `tests/test_engine.py`.

**Interfaces:**
- Consumes: `Bar`/`MarketConfig` (Plan 1), `Strategy`/`Signal`/`Side` + `size_position` + `compute_cost` (Plan 2), `resolve_exit` (Task 1), `SimTrade` (Task 2), `build_result` (Task 3).
- Produces:
  - `simulate_symbol(strategy, symbol, bars, market_config, equity, risk_fraction, t_plus=0, lot_size=1) -> list[SimTrade]` — one position at a time; enters at a signal bar's close; checks exits only on bars where `i - entry_index > t_plus`; closes any open position at the final bar's close (`reason="eod"`). Entry/exit costs via `compute_cost` (long entry=BUY/exit=SELL; short entry=SELL/exit=BUY). Skips entry if `size_position` returns `<= 0`.
  - `backtest(strategy, bars_by_symbol, market_config, start_equity, risk_fraction, t_plus=0, lot_size=1) -> BacktestResult`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py
import pytest
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy, StrategyStatus, Signal
from touzi_agent.backtest.engine import simulate_symbol, backtest

ZERO_COST = MarketConfig(market="US", currency="USD", settlement="T+0",
                         short_selling="allowed", code_prefix="US",
                         daily_limit=None, costs={})


class OnceLong(Strategy):
    """Emits a single LONG signal on the first bar it sees."""
    name = "once_long"
    status = StrategyStatus.CANDIDATE
    universe = ["T"]

    def __init__(self, entry, stop, target):
        self._e, self._s, self._t = entry, stop, target

    def generate(self, bars_by_symbol):
        for sym, bars in bars_by_symbol.items():
            if len(bars) == 1:
                return [Signal(sym, "LONG", self._e, self._s, self._t)]
        return []


def _bar(date, o, h, low, c):
    return Bar("T", date, open=o, high=h, low=low, close=c,
               volume=1, turnover=1.0)


def test_target_hit_produces_3r_trade():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),   # entry @100
        _bar("2026-01-02", 101, 107, 101, 105),  # target 106 hit
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, ZERO_COST,
                             equity=100000, risk_fraction=0.01)
    assert len(trades) == 1
    assert trades[0].reason == "target"
    assert trades[0].qty == 500  # risk $1000 / $2 per share
    assert trades[0].net_r == pytest.approx(3.0)


def test_stop_hit_produces_minus_1r():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 100, 101, 97, 99),   # stop 98 hit
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, ZERO_COST,
                             equity=100000, risk_fraction=0.01)
    assert trades[0].reason == "stop"
    assert trades[0].net_r == pytest.approx(-1.0)


def test_open_position_closed_at_eod():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 100, 105, 99, 104),  # neither stop nor target
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, ZERO_COST,
                             equity=100000, risk_fraction=0.01)
    assert trades[0].reason == "eod"
    assert trades[0].exit == 104


def test_costs_reduce_net_pnl():
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None,
                       costs={"commission_rate": 0.0003, "min_commission": 0.0})
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 101, 107, 101, 105),  # target 106
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    trades = simulate_symbol(strat, "T", bars, cfg,
                             equity=100000, risk_fraction=0.01)
    # entry commission 100*500*0.0003=15; exit 106*500*0.0003=15.9
    assert trades[0].entry_cost == pytest.approx(15.0)
    assert trades[0].exit_cost == pytest.approx(15.9)
    assert trades[0].net_pnl == pytest.approx(3000 - 30.9)


def test_backtest_aggregates_result():
    bars = [
        _bar("2026-01-01", 100, 101, 99, 100),
        _bar("2026-01-02", 101, 107, 101, 105),
    ]
    strat = OnceLong(entry=100, stop=98, target=106)
    res = backtest(strat, {"T": bars}, ZERO_COST,
                   start_equity=100000, risk_fraction=0.01)
    assert res.stats.n == 1
    assert res.total_return == pytest.approx(0.03)
```

- [ ] **Step 2: Run test, expect FAIL.** `.venv/Scripts/python.exe -m pytest tests/test_engine.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/backtest/engine.py
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
```

- [ ] **Step 4: Run test, expect PASS** (5 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/backtest/engine.py tests/test_engine.py
git commit -m "feat: bar-by-bar simulation engine and backtest runner"
```

---

### Task 5: Walk-forward harness

**Files:** Create `touzi_agent/backtest/walkforward.py`; Test `tests/test_walkforward.py`.

**Interfaces:**
- Consumes: `backtest` (Task 4), `build_result` (Task 3), `Bar`/`MarketConfig` (Plan 1), `Strategy` (Plan 2).
- Produces:
  - `walk_forward(make_strategy: Callable[[], Strategy], bars_by_symbol, windows: list[tuple[str, str]], market_config, start_equity, risk_fraction, t_plus=0, lot_size=1) -> BacktestResult` — for each `(start_date, end_date)` window: builds a fresh strategy via `make_strategy()`, slices each symbol's bars to the inclusive date window, runs `backtest`, and aggregates all trades across windows into a single combined `BacktestResult` (the out-of-sample record).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_walkforward.py
import pytest
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy, StrategyStatus, Signal
from touzi_agent.backtest.walkforward import walk_forward

ZERO_COST = MarketConfig(market="US", currency="USD", settlement="T+0",
                         short_selling="allowed", code_prefix="US",
                         daily_limit=None, costs={})


class OnceLong(Strategy):
    name = "once_long"
    status = StrategyStatus.CANDIDATE
    universe = ["T"]

    def generate(self, bars_by_symbol):
        for sym, bars in bars_by_symbol.items():
            if len(bars) == 1:
                return [Signal(sym, "LONG", 100, 98, 106)]
        return []


def _bar(date, h, low, c):
    return Bar("T", date, open=100, high=h, low=low, close=c,
               volume=1, turnover=1.0)


def test_walk_forward_aggregates_two_windows():
    bars = [
        _bar("2026-01-01", 101, 99, 100),
        _bar("2026-01-02", 107, 101, 105),   # window 1 target
        _bar("2026-02-01", 101, 99, 100),
        _bar("2026-02-02", 107, 101, 105),   # window 2 target
    ]
    windows = [("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28")]
    res = walk_forward(lambda: OnceLong(), {"T": bars}, windows,
                       ZERO_COST, start_equity=100000, risk_fraction=0.01)
    assert res.stats.n == 2
    assert all(t.reason == "target" for t in res.trades)
```

- [ ] **Step 2: Run test, expect FAIL.** `.venv/Scripts/python.exe -m pytest tests/test_walkforward.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/backtest/walkforward.py
from typing import Callable

from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Strategy
from touzi_agent.backtest.engine import backtest
from touzi_agent.backtest.metrics import build_result, BacktestResult


def walk_forward(make_strategy: Callable[[], Strategy],
                 bars_by_symbol: dict[str, list[Bar]],
                 windows: list[tuple[str, str]],
                 market_config: MarketConfig, start_equity: float,
                 risk_fraction: float, t_plus: int = 0,
                 lot_size: int = 1) -> BacktestResult:
    aggregated = []
    for start_date, end_date in windows:
        strategy = make_strategy()
        sliced = {
            sym: [b for b in bars if start_date <= b.date <= end_date]
            for sym, bars in bars_by_symbol.items()
        }
        res = backtest(strategy, sliced, market_config, start_equity,
                       risk_fraction, t_plus, lot_size)
        aggregated += res.trades
    return build_result(aggregated, start_equity)
```

- [ ] **Step 4: Run test, expect PASS** (1 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/backtest/walkforward.py tests/test_walkforward.py
git commit -m "feat: walk-forward harness aggregating out-of-sample trades"
```

---

### Task 6: Forward paper-trade broker

**Files:** Create `touzi_agent/backtest/paper.py`; Test `tests/test_paper.py`.

**Interfaces:**
- Consumes: `Bar`/`MarketConfig` (Plan 1), `Signal`/`Side` + `size_position` + `compute_cost` (Plan 2), `resolve_exit` (Task 1), `SimTrade` (Task 2).
- Produces:
  - `PaperBroker(market_config, equity, risk_fraction, lot_size=1)` — stateful incremental forward simulator. Methods:
    - `submit(signal: Signal, date: str) -> bool` — opens a position for `signal.symbol` if none is open and `size_position > 0`; records entry cost; returns whether opened.
    - `on_bar(bar: Bar) -> SimTrade | None` — for an open position matching `bar.code`, only considers an exit when `bar.date > entry_date` (next-day, models T+1); on a stop/target hit closes and appends to `closed_trades`, returning the `SimTrade`.
    - Attributes: `open_positions: dict[str, dict]`, `closed_trades: list[SimTrade]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_paper.py
import pytest
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.quant.strategy import Signal
from touzi_agent.backtest.paper import PaperBroker

ZERO_COST = MarketConfig(market="US", currency="USD", settlement="T+0",
                         short_selling="allowed", code_prefix="US",
                         daily_limit=None, costs={})


def _bar(date, h, low, c):
    return Bar("T", date, open=100, high=h, low=low, close=c,
               volume=1, turnover=1.0)


def test_submit_opens_position():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    opened = pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    assert opened is True
    assert "T" in pb.open_positions


def test_no_exit_same_day():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    # same-day bar that would hit target must NOT close (T+1)
    assert pb.on_bar(_bar("2026-01-01", 107, 99, 105)) is None
    assert "T" in pb.open_positions


def test_exit_next_day_target():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    trade = pb.on_bar(_bar("2026-01-02", 107, 101, 105))
    assert trade is not None
    assert trade.reason == "target"
    assert trade.net_r == pytest.approx(3.0)
    assert "T" not in pb.open_positions
    assert pb.closed_trades == [trade]


def test_duplicate_submit_ignored_while_open():
    pb = PaperBroker(ZERO_COST, equity=100000, risk_fraction=0.01)
    pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01")
    assert pb.submit(Signal("T", "LONG", 100, 98, 106), "2026-01-01") is False
```

- [ ] **Step 2: Run test, expect FAIL.** `.venv/Scripts/python.exe -m pytest tests/test_paper.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/backtest/paper.py
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
```

- [ ] **Step 4: Run test, expect PASS** (4 passed).
- [ ] **Step 5: Run full suite** — `.venv/Scripts/python.exe -m pytest -q` (all green).
- [ ] **Step 6: Commit**

```bash
git add touzi_agent/backtest/paper.py tests/test_paper.py
git commit -m "feat: forward paper-trade broker (T+1-aware)"
```

---

## Plan Self-Review

**Spec coverage (Plan 3 = validation substrate):**
- Walk-forward backtester (spec §5.4, §10) → Tasks 4, 5 ✅
- Forward paper-trade simulator (spec §5, §10) → Task 6 ✅
- Net-of-cost R-based metrics + expectancy (spec §3, §4.4) → Tasks 2, 3 ✅
- Stop-priority exit modeling (risk-first) → Task 1 ✅
- T+1 awareness (spec §8.3) → `t_plus` in engine + next-day rule in PaperBroker ✅
- *Deferred (correct):* promotion/demotion policy + min-sample/CI gates (Plan 4); A-share limit-down gap-risk sizing refinement (later, builds on `t_plus`).

**Placeholder scan:** None — every step has complete code and expected results. ✅

**Type consistency:** `SimTrade` fields/properties identical across Tasks 2/3/4/6; `BacktestResult` shape consistent in Tasks 3/4/5; `resolve_exit` return tuple consumed identically in engine and paper; `_entry_side`/`_exit_side` helpers consistent. `Signal`/`Side`/`size_position`/`compute_cost`/`expectancy` signatures match Plan 2 definitions. ✅
