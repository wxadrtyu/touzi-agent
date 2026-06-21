# V4.0 Plan 2 — Quant Engine Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the decision core: R-multiples, expectancy statistics (with confidence interval), per-market net cost model, the strategy interface, fractional-Kelly position sizing, and the portfolio risk model with binding caps.

**Architecture:** A new `touzi_agent/quant/` package of small, pure, dependency-injected modules. Everything is deterministic and unit-testable with plain numbers — no market data or 富途 needed. These modules are the "numbers" layer the spec mandates Python owns; the LLM never produces these values.

**Tech Stack:** Python 3.12, pytest. (Stdlib only — `statistics` for stats; no new deps.)

## Global Constraints

- **Expectancy in R units is the optimization metric** — `R = |entry − stop|`; all P&L in R-multiples. (spec §3)
- **Costs always net** — every cost figure includes commission, stamp duty, platform/transfer fees per market. (spec §3, §4.4)
- **Risk caps are binding** (block, not warn): total heat ≤ ~6%, per-position ≤ ~15–20%, per-market cap, cluster cap, max-drawdown de-risk. (spec §4.3)
- **Sizing is risk-first, expectancy-weighted** via fractional Kelly (¼-Kelly default), capped. (spec §4.2)
- **TDD, DRY, YAGNI, frequent commits.**
- **Toolchain:** venv (conda unavailable on host). Run tests: `.venv/Scripts/python.exe -m pytest`.

---

## File Structure

```
touzi_agent/quant/
  __init__.py
  trade.py        # Side, r_multiple(), ClosedTrade
  expectancy.py   # ExpectancyStats, expectancy()
  costs.py        # compute_cost()
  strategy.py     # Signal, StrategyStatus, Strategy (ABC)
  sizing.py       # kelly_risk_fraction(), size_position()
  portfolio.py    # Position, Portfolio
  risk.py         # RiskLimits, RiskDecision, RiskModel
tests/
  test_trade.py
  test_expectancy.py
  test_costs.py
  test_strategy.py
  test_sizing.py
  test_portfolio.py
  test_risk.py
```

---

### Task 1: R-multiple + ClosedTrade

**Files:** Create `touzi_agent/quant/__init__.py`, `touzi_agent/quant/trade.py`; Test `tests/test_trade.py`.

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Side` — string constants `Side.LONG = "LONG"`, `Side.SHORT = "SHORT"`.
  - `r_multiple(entry: float, stop: float, exit: float, side: str) -> float` — raises `ValueError` if `entry == stop`.
  - `ClosedTrade(symbol, side, entry, stop, exit, qty)` frozen dataclass with property `r: float`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_trade.py
import pytest
from touzi_agent.quant.trade import Side, r_multiple, ClosedTrade


def test_long_win_is_positive_r():
    # risk = 2 (100->98), profit = 6 (100->106) => 3R
    assert r_multiple(100, 98, 106, Side.LONG) == 3.0


def test_long_loss_is_negative_r():
    assert r_multiple(100, 98, 98, Side.LONG) == -1.0


def test_short_win_is_positive_r():
    # risk = 2 (100->102), profit = 4 (100->96) => 2R
    assert r_multiple(100, 102, 96, Side.SHORT) == 2.0


def test_zero_risk_rejected():
    with pytest.raises(ValueError):
        r_multiple(100, 100, 110, Side.LONG)


def test_closed_trade_r_property():
    t = ClosedTrade(symbol="US.AAPL", side=Side.LONG, entry=100,
                    stop=98, exit=106, qty=10)
    assert t.r == 3.0
```

- [ ] **Step 2: Run test, expect FAIL** — `ModuleNotFoundError: touzi_agent.quant.trade`.
  Run: `.venv/Scripts/python.exe -m pytest tests/test_trade.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/__init__.py
```

```python
# touzi_agent/quant/trade.py
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
```

- [ ] **Step 4: Run test, expect PASS** (5 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/quant/__init__.py touzi_agent/quant/trade.py tests/test_trade.py
git commit -m "feat: R-multiple and ClosedTrade"
```

---

### Task 2: Expectancy statistics

**Files:** Create `touzi_agent/quant/expectancy.py`; Test `tests/test_expectancy.py`.

**Interfaces:**
- Consumes: nothing (operates on a list of R-multiples).
- Produces:
  - `ExpectancyStats(n: int, win_rate: float, avg_win_r: float, avg_loss_r: float, expectancy_r: float, ci_low: float, ci_high: float)` frozen dataclass.
  - `expectancy(r_multiples: list[float]) -> ExpectancyStats` — raises `ValueError` on empty input. `expectancy_r` is the mean of all R-multiples. `avg_loss_r` is negative (mean of losers; 0 if none). 95% CI via normal approx `mean ± 1.96·sd/√n` (sd is sample std, ddof=1; CI collapses to the mean when n==1).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_expectancy.py
import pytest
from touzi_agent.quant.expectancy import expectancy, ExpectancyStats


def test_basic_expectancy():
    # 2 wins (+3R each), 3 losses (-1R each): mean = (6-3)/5 = 0.6
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    assert stats.n == 5
    assert stats.win_rate == pytest.approx(0.4)
    assert stats.avg_win_r == pytest.approx(3.0)
    assert stats.avg_loss_r == pytest.approx(-1.0)
    assert stats.expectancy_r == pytest.approx(0.6)


def test_all_wins_no_losers():
    stats = expectancy([1.0, 2.0])
    assert stats.win_rate == 1.0
    assert stats.avg_loss_r == 0.0
    assert stats.expectancy_r == pytest.approx(1.5)


def test_confidence_interval_brackets_mean():
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    assert stats.ci_low < stats.expectancy_r < stats.ci_high


def test_single_trade_ci_collapses():
    stats = expectancy([2.0])
    assert stats.ci_low == stats.ci_high == 2.0


def test_empty_rejected():
    with pytest.raises(ValueError):
        expectancy([])
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_expectancy.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/expectancy.py
from dataclasses import dataclass
from statistics import mean, stdev
from math import sqrt

_Z = 1.96


@dataclass(frozen=True)
class ExpectancyStats:
    n: int
    win_rate: float
    avg_win_r: float
    avg_loss_r: float
    expectancy_r: float
    ci_low: float
    ci_high: float


def expectancy(r_multiples: list[float]) -> ExpectancyStats:
    if not r_multiples:
        raise ValueError("need at least one R-multiple")
    n = len(r_multiples)
    wins = [r for r in r_multiples if r > 0]
    losses = [r for r in r_multiples if r <= 0]
    exp_r = mean(r_multiples)
    if n > 1:
        margin = _Z * stdev(r_multiples) / sqrt(n)
    else:
        margin = 0.0
    return ExpectancyStats(
        n=n,
        win_rate=len(wins) / n,
        avg_win_r=mean(wins) if wins else 0.0,
        avg_loss_r=mean(losses) if losses else 0.0,
        expectancy_r=exp_r,
        ci_low=exp_r - margin,
        ci_high=exp_r + margin,
    )
```

- [ ] **Step 4: Run test, expect PASS** (5 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/quant/expectancy.py tests/test_expectancy.py
git commit -m "feat: expectancy stats with confidence interval"
```

---

### Task 3: Per-market net cost model

**Files:** Create `touzi_agent/quant/costs.py`; Test `tests/test_costs.py`.

**Interfaces:**
- Consumes: `MarketConfig` (Plan 1).
- Produces:
  - `compute_cost(config: MarketConfig, side: str, price: float, qty: int) -> float` — total round-side cost. Commission = `max(notional·commission_rate, min_commission)`. Stamp duty on SELL for all markets, plus on BUY for HK (both sides). Transfer fee (if present) on both sides. Platform fee flat per trade. Missing cost keys default to 0.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_costs.py
from touzi_agent.models import MarketConfig
from touzi_agent.quant.costs import compute_cost
import pytest


def _cfg(market, costs):
    return MarketConfig(market=market, currency="X", settlement="T+0",
                        short_selling="x", code_prefix="", daily_limit=None,
                        costs=costs)


def test_us_commission_floor_applies():
    cfg = _cfg("US", {"commission_rate": 0.0003, "min_commission": 0.99})
    # notional = 100*1 = 100; rate cost = 0.03 -> floored to 0.99
    assert compute_cost(cfg, "BUY", 100, 1) == pytest.approx(0.99)


def test_cn_stamp_on_sell_only():
    cfg = _cfg("CN", {"commission_rate": 0.0, "min_commission": 0.0,
                      "stamp_duty": 0.0005, "transfer_fee": 0.0})
    notional = 10 * 1000  # 10000
    assert compute_cost(cfg, "BUY", 10, 1000) == pytest.approx(0.0)
    assert compute_cost(cfg, "SELL", 10, 1000) == pytest.approx(notional * 0.0005)


def test_hk_stamp_on_both_sides():
    cfg = _cfg("HK", {"commission_rate": 0.0, "min_commission": 0.0,
                      "stamp_duty": 0.0013, "platform_fee": 0.0})
    notional = 100 * 100  # 10000
    assert compute_cost(cfg, "BUY", 100, 100) == pytest.approx(notional * 0.0013)
    assert compute_cost(cfg, "SELL", 100, 100) == pytest.approx(notional * 0.0013)


def test_platform_and_transfer_fees_added():
    cfg = _cfg("HK", {"commission_rate": 0.0, "min_commission": 0.0,
                      "stamp_duty": 0.0, "platform_fee": 15.0})
    assert compute_cost(cfg, "BUY", 100, 100) == pytest.approx(15.0)
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_costs.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/costs.py
from touzi_agent.models import MarketConfig


def compute_cost(config: MarketConfig, side: str,
                 price: float, qty: int) -> float:
    c = config.costs
    notional = price * qty
    commission = max(notional * c.get("commission_rate", 0.0),
                     c.get("min_commission", 0.0))
    stamp_rate = c.get("stamp_duty", 0.0)
    if side == "SELL" or config.market == "HK":
        stamp = notional * stamp_rate
    else:
        stamp = 0.0
    transfer = notional * c.get("transfer_fee", 0.0)
    platform = c.get("platform_fee", 0.0)
    return commission + stamp + transfer + platform
```

- [ ] **Step 4: Run test, expect PASS** (4 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/quant/costs.py tests/test_costs.py
git commit -m "feat: per-market net cost model"
```

---

### Task 4: Signal + Strategy interface

**Files:** Create `touzi_agent/quant/strategy.py`; Test `tests/test_strategy.py`.

**Interfaces:**
- Consumes: `Bar` (Plan 1).
- Produces:
  - `StrategyStatus` — Enum: `CANDIDATE, PROBATION, PROMOTED, RETIRED`.
  - `Signal(symbol: str, side: str, entry: float, stop: float, target: float | None = None, cluster: str = "", meta: dict | None = None)` frozen dataclass.
  - `Strategy` — ABC with attributes `name: str`, `status: StrategyStatus`, `universe: list[str]`, and abstract method `generate(bars_by_symbol: dict[str, list[Bar]]) -> list[Signal]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_strategy.py
import pytest
from touzi_agent.models import Bar
from touzi_agent.quant.strategy import Signal, Strategy, StrategyStatus


def test_signal_defaults():
    s = Signal(symbol="US.AAPL", side="LONG", entry=100, stop=98)
    assert s.target is None
    assert s.cluster == ""


def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        Strategy()  # cannot instantiate ABC with abstract generate


def test_concrete_strategy_generates_signals():
    class AlwaysBuy(Strategy):
        name = "always_buy"
        status = StrategyStatus.CANDIDATE
        universe = ["US.AAPL"]

        def generate(self, bars_by_symbol):
            out = []
            for sym, bars in bars_by_symbol.items():
                last = bars[-1]
                out.append(Signal(symbol=sym, side="LONG",
                                  entry=last.close, stop=last.low))
            return out

    strat = AlwaysBuy()
    bars = {"US.AAPL": [Bar("US.AAPL", "2026-06-19", 1, 2, 0.5, 1.5, 10, 15.0)]}
    signals = strat.generate(bars)
    assert signals[0].symbol == "US.AAPL"
    assert signals[0].entry == 1.5
    assert strat.status == StrategyStatus.CANDIDATE
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_strategy.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/strategy.py
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
```

- [ ] **Step 4: Run test, expect PASS** (3 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/quant/strategy.py tests/test_strategy.py
git commit -m "feat: Signal and Strategy interface with status lifecycle"
```

---

### Task 5: Fractional-Kelly sizing

**Files:** Create `touzi_agent/quant/sizing.py`; Test `tests/test_sizing.py`.

**Interfaces:**
- Consumes: `ExpectancyStats` (Task 2).
- Produces:
  - `kelly_risk_fraction(stats: ExpectancyStats, kelly_cap: float = 0.25, max_risk_pct: float = 0.01, floor: float = 0.0) -> float` — Kelly fraction `f = W − (1−W)/b` where `b = avg_win_r / |avg_loss_r|`; returns `clamp(kelly_cap · f, floor, max_risk_pct)`. If there are no losers (`avg_loss_r == 0`), returns `max_risk_pct`. Non-positive edge returns `floor`.
  - `size_position(equity: float, risk_fraction: float, entry: float, stop: float, lot_size: int = 1) -> int` — `qty = floor(equity·risk_fraction / |entry−stop| / lot_size) · lot_size`; raises `ValueError` if `entry == stop`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sizing.py
import pytest
from touzi_agent.quant.expectancy import expectancy
from touzi_agent.quant.sizing import kelly_risk_fraction, size_position


def test_positive_edge_fraction_capped():
    # W=0.4, avg_win=3, avg_loss=-1 -> b=3, f=0.4-0.6/3=0.2
    # kelly_cap*f = 0.25*0.2 = 0.05 -> capped at max_risk_pct=0.01
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    assert kelly_risk_fraction(stats) == pytest.approx(0.01)


def test_positive_edge_below_cap():
    stats = expectancy([3.0, 3.0, -1.0, -1.0, -1.0])
    # raise the ceiling so the clamp doesn't bite: 0.25*0.2 = 0.05
    frac = kelly_risk_fraction(stats, max_risk_pct=0.10)
    assert frac == pytest.approx(0.05)


def test_negative_edge_returns_floor():
    # all losers -> f negative -> floor
    stats = expectancy([-1.0, -1.0, -1.0])
    assert kelly_risk_fraction(stats, floor=0.0) == 0.0


def test_no_losers_returns_max():
    stats = expectancy([1.0, 2.0])
    assert kelly_risk_fraction(stats, max_risk_pct=0.02) == 0.02


def test_size_position_rounds_to_lot():
    # equity 100000, risk_fraction 0.01 -> risk $1000; per-share risk $2
    # raw = 500 shares; lot 100 -> 500
    assert size_position(100000, 0.01, entry=100, stop=98, lot_size=100) == 500


def test_size_position_rounds_down_partial_lot():
    # risk $1000, per-share risk $3 -> raw 333.3; lot 100 -> 300
    assert size_position(100000, 0.01, entry=100, stop=97, lot_size=100) == 300


def test_size_position_zero_risk_rejected():
    with pytest.raises(ValueError):
        size_position(100000, 0.01, entry=100, stop=100)
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_sizing.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/sizing.py
from math import floor

from touzi_agent.quant.expectancy import ExpectancyStats


def kelly_risk_fraction(stats: ExpectancyStats, kelly_cap: float = 0.25,
                        max_risk_pct: float = 0.01,
                        floor: float = 0.0) -> float:
    if stats.avg_loss_r == 0:
        return max_risk_pct
    b = stats.avg_win_r / abs(stats.avg_loss_r)
    if b <= 0:
        return floor
    f = stats.win_rate - (1 - stats.win_rate) / b
    frac = kelly_cap * f
    if frac < floor:
        return floor
    if frac > max_risk_pct:
        return max_risk_pct
    return frac


def size_position(equity: float, risk_fraction: float, entry: float,
                  stop: float, lot_size: int = 1) -> int:
    per_share_risk = abs(entry - stop)
    if per_share_risk == 0:
        raise ValueError("entry and stop must differ")
    risk_amount = equity * risk_fraction
    raw_qty = risk_amount / per_share_risk
    return int(floor(raw_qty / lot_size) * lot_size)
```

- [ ] **Step 4: Run test, expect PASS** (7 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/quant/sizing.py tests/test_sizing.py
git commit -m "feat: fractional-Kelly risk fraction and position sizing"
```

---

### Task 6: Portfolio state

**Files:** Create `touzi_agent/quant/portfolio.py`; Test `tests/test_portfolio.py`.

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Position(symbol: str, side: str, qty: int, entry: float, stop: float, market: str, cluster: str = "")` frozen dataclass with properties `notional: float` (= `entry·qty`) and `open_risk: float` (= `|entry−stop|·qty`).
  - `Portfolio(equity: float, positions: list[Position], peak_equity: float | None = None)` — `peak_equity` defaults to `equity` when None. Methods: `total_heat() -> float` (sum open_risk / equity); `market_exposure(market) -> float` (sum notional in market / equity); `cluster_exposure(cluster) -> float`; `drawdown() -> float` (`(peak−equity)/peak`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_portfolio.py
import pytest
from touzi_agent.quant.portfolio import Position, Portfolio


def _pos(sym, qty, entry, stop, market="US", cluster=""):
    return Position(symbol=sym, side="LONG", qty=qty, entry=entry,
                    stop=stop, market=market, cluster=cluster)


def test_position_derived_values():
    p = _pos("US.AAPL", 100, 100, 98)
    assert p.notional == 10000
    assert p.open_risk == 200


def test_total_heat():
    pf = Portfolio(equity=100000, positions=[
        _pos("US.AAPL", 100, 100, 98),   # risk 200
        _pos("US.MSFT", 50, 200, 196),   # risk 200
    ])
    assert pf.total_heat() == pytest.approx(0.004)


def test_market_and_cluster_exposure():
    pf = Portfolio(equity=100000, positions=[
        _pos("US.AAPL", 100, 100, 98, market="US", cluster="ai"),
        _pos("HK.00700", 100, 300, 290, market="HK", cluster="ai"),
    ])
    assert pf.market_exposure("US") == pytest.approx(0.10)
    assert pf.cluster_exposure("ai") == pytest.approx(0.40)


def test_drawdown():
    pf = Portfolio(equity=80000, positions=[], peak_equity=100000)
    assert pf.drawdown() == pytest.approx(0.20)


def test_peak_defaults_to_equity():
    pf = Portfolio(equity=100000, positions=[])
    assert pf.drawdown() == 0.0
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_portfolio.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/portfolio.py
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
```

- [ ] **Step 4: Run test, expect PASS** (5 passed).
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/quant/portfolio.py tests/test_portfolio.py
git commit -m "feat: Portfolio and Position state with heat/exposure/drawdown"
```

---

### Task 7: Portfolio risk model (binding caps)

**Files:** Create `touzi_agent/quant/risk.py`; Test `tests/test_risk.py`.

**Interfaces:**
- Consumes: `Position`, `Portfolio` (Task 6).
- Produces:
  - `RiskLimits(max_total_heat=0.06, max_position_pct=0.20, max_market_pct=0.40, max_cluster_pct=0.30, drawdown_derisk=0.20)` frozen dataclass.
  - `RiskDecision(allowed: bool, reasons: list[str])` frozen dataclass.
  - `RiskModel(limits: RiskLimits)` with `check(portfolio: Portfolio, candidate: Position) -> RiskDecision` — evaluates the portfolio *as if* `candidate` were added; appends a reason string per breached cap; `allowed = (reasons == [])`. If `portfolio.drawdown() >= drawdown_derisk`, blocks with a drawdown reason.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_risk.py
from touzi_agent.quant.portfolio import Position, Portfolio
from touzi_agent.quant.risk import RiskLimits, RiskModel


def _pos(sym, qty, entry, stop, market="US", cluster=""):
    return Position(symbol=sym, side="LONG", qty=qty, entry=entry,
                    stop=stop, market=market, cluster=cluster)


def test_allows_within_all_caps():
    rm = RiskModel(RiskLimits())
    pf = Portfolio(equity=100000, positions=[])
    cand = _pos("US.AAPL", 100, 100, 98)  # heat 0.002, pos 0.10
    assert rm.check(pf, cand).allowed is True


def test_blocks_when_heat_exceeded():
    rm = RiskModel(RiskLimits(max_total_heat=0.005))
    pf = Portfolio(equity=100000, positions=[_pos("US.MSFT", 100, 100, 96)])  # risk 400 -> 0.004
    cand = _pos("US.AAPL", 100, 100, 98)  # +200 -> total 0.006 > 0.005
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("heat" in r.lower() for r in decision.reasons)


def test_blocks_when_position_too_large():
    rm = RiskModel(RiskLimits(max_position_pct=0.05))
    pf = Portfolio(equity=100000, positions=[])
    cand = _pos("US.AAPL", 100, 100, 98)  # notional 10000 -> 0.10 > 0.05
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("position" in r.lower() for r in decision.reasons)


def test_blocks_when_market_cap_exceeded():
    rm = RiskModel(RiskLimits(max_market_pct=0.15))
    pf = Portfolio(equity=100000, positions=[_pos("US.MSFT", 100, 100, 98)])  # US 0.10
    cand = _pos("US.AAPL", 100, 100, 98)  # +0.10 -> 0.20 > 0.15
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("market" in r.lower() for r in decision.reasons)


def test_blocks_when_cluster_cap_exceeded():
    rm = RiskModel(RiskLimits(max_cluster_pct=0.15))
    pf = Portfolio(equity=100000, positions=[
        _pos("US.MSFT", 100, 100, 98, cluster="ai")])
    cand = _pos("US.AAPL", 100, 100, 98, cluster="ai")  # cluster 0.20 > 0.15
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("cluster" in r.lower() for r in decision.reasons)


def test_blocks_all_new_entries_in_drawdown():
    rm = RiskModel(RiskLimits(drawdown_derisk=0.20))
    pf = Portfolio(equity=80000, positions=[], peak_equity=100000)  # dd 0.20
    cand = _pos("US.AAPL", 1, 100, 98)
    decision = rm.check(pf, cand)
    assert decision.allowed is False
    assert any("drawdown" in r.lower() for r in decision.reasons)
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_risk.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/quant/risk.py
from dataclasses import dataclass

from touzi_agent.quant.portfolio import Position, Portfolio


@dataclass(frozen=True)
class RiskLimits:
    max_total_heat: float = 0.06
    max_position_pct: float = 0.20
    max_market_pct: float = 0.40
    max_cluster_pct: float = 0.30
    drawdown_derisk: float = 0.20


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reasons: list[str]


class RiskModel:
    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def check(self, portfolio: Portfolio, candidate: Position) -> RiskDecision:
        lim = self.limits
        eq = portfolio.equity
        reasons: list[str] = []

        if portfolio.drawdown() >= lim.drawdown_derisk:
            reasons.append(
                f"drawdown {portfolio.drawdown():.2%} >= de-risk "
                f"threshold {lim.drawdown_derisk:.2%}; new entries paused")

        prospective = Portfolio(
            equity=eq,
            positions=list(portfolio.positions) + [candidate],
            peak_equity=portfolio.peak_equity,
        )

        if prospective.total_heat() > lim.max_total_heat:
            reasons.append(
                f"total heat {prospective.total_heat():.2%} > cap "
                f"{lim.max_total_heat:.2%}")

        pos_pct = candidate.notional / eq
        if pos_pct > lim.max_position_pct:
            reasons.append(
                f"position size {pos_pct:.2%} > cap "
                f"{lim.max_position_pct:.2%}")

        mkt_pct = prospective.market_exposure(candidate.market)
        if mkt_pct > lim.max_market_pct:
            reasons.append(
                f"market {candidate.market} exposure {mkt_pct:.2%} > cap "
                f"{lim.max_market_pct:.2%}")

        if candidate.cluster:
            cl_pct = prospective.cluster_exposure(candidate.cluster)
            if cl_pct > lim.max_cluster_pct:
                reasons.append(
                    f"cluster {candidate.cluster} exposure {cl_pct:.2%} > "
                    f"cap {lim.max_cluster_pct:.2%}")

        return RiskDecision(allowed=(reasons == []), reasons=reasons)
```

- [ ] **Step 4: Run test, expect PASS** (6 passed).
- [ ] **Step 5: Run full suite** — `.venv/Scripts/python.exe -m pytest -q` (all Plan 1 + Plan 2 green).
- [ ] **Step 6: Commit**

```bash
git add touzi_agent/quant/risk.py tests/test_risk.py
git commit -m "feat: portfolio risk model with binding caps"
```

---

## Plan Self-Review

**Spec coverage (Plan 2 = quant engine core):**
- R/expectancy as core metric (spec §3) → Tasks 1, 2 ✅
- Net cost model (spec §4.4) → Task 3 ✅
- Strategy interface + status lifecycle (spec §4.1, §5.1) → Task 4 ✅
- Risk-first + fractional-Kelly sizing (spec §4.2) → Task 5 ✅
- Portfolio state + binding risk caps: heat, per-position, per-market, cluster, drawdown de-risk (spec §4.3) → Tasks 6, 7 ✅
- *Deferred (correct):* signal-generation strategies themselves (later), backtest/forward (Plan 3), discovery promotion (Plan 4).

**Placeholder scan:** None — every step has complete code and expected results. ✅

**Type consistency:** `ExpectancyStats` fields used identically in Tasks 2/5; `Position`/`Portfolio` signatures match between Tasks 6/7; `Signal`/`StrategyStatus` consistent. `Side` constants ("LONG"/"SHORT") align with `Position.side`/`Signal.side` usage. ✅
