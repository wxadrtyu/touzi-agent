# V4.1 Phase 1 — Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the V4.1 architecture connects end-to-end with the thinnest possible vertical slice: the four pipelines (1-1, 1-2, 2, 3) each emit a common output type, flow through the cross-cutting discipline layer + unified risk ledger + human gate, and land in the L7 journal. Not good yet — just *whole*. This phase freezes the shared contracts every later track builds on.

**Architecture:** New `core/` (contracts, journal, ledger, proposal, orchestrator), `strategies/` (one real MA-cross), `pipelines/` (the four pipelines, stubs where noted), `discipline/` (guardrail layer). Reuses Plan 1/2 modules (`models`, `quant.*`) and the existing `backtest.*` engine. LLM-dependent parts (1-1 overlay, Pipeline 2, Pipeline 3) are honest stubs — wired in shape, not intelligence.

**Tech Stack:** Python 3.12, pytest, stdlib + existing deps. No new third-party deps.

## Global Constraints

- **Scope:** US + HK only; daily bars; file/in-memory stubs for RAG. (spec §0.1, §13)
- **Single unified portfolio/risk ledger (N1):** every pipeline output AND manual trade is sized/checked against one `Ledger` before acceptance. (spec §4.5)
- **Common output contract:** all strategy-producing pipelines emit the same `ActionableStrategy` type. (ROADMAP Phase 1)
- **Numbers in code, not LLM:** sizing/risk via `quant.*`; stubs never invent numbers. (spec §1.1)
- **Binding guardrail present even in skeleton:** "stop required" blocks. (spec §8.2)
- **Pipeline 3 is independent on-demand Q&A** (not part of the discipline layer). (spec §7.2)
- **TDD, DRY, YAGNI, frequent commits.** Run tests: `.venv/Scripts/python.exe -m pytest`.

---

## File Structure

```
touzi_agent/
  core/
    __init__.py
    contracts.py      # ActionableStrategy (common pipeline output)
    journal.py        # L7 journal: JournalEntry, JournalStatus, Journal (SQLite)
    ledger.py         # Ledger: unified portfolio + risk check (wraps quant.portfolio/risk)
    proposal.py       # Proposal, assemble_proposal, human_gate
    orchestrator.py   # run_once: wire pipelines → discipline → ledger → gate → journal
  strategies/
    __init__.py
    ma_cross.py       # MACrossStrategy (concrete Strategy)
  pipelines/
    __init__.py
    quant.py          # run_quant_pipeline (modes "1-1","1-2") + llm_overlay_stub
    llm_pick.py       # run_llm_pick_stub  (Pipeline 2 stub)
    decision_support.py # answer_query (Pipeline 3 stub)
  discipline/
    __init__.py
    layer.py          # GuardrailResult, DisciplineLayer
tests/
  test_contracts.py  test_journal.py  test_ledger.py  test_ma_cross.py
  test_pipeline_quant.py  test_pipeline_llm_pick.py  test_pipeline_decision_support.py
  test_discipline.py  test_proposal.py  test_orchestrator_e2e.py
```

---

### Task 1: Common output contract — `ActionableStrategy`

**Files:** Create `touzi_agent/core/__init__.py`, `touzi_agent/core/contracts.py`; Test `tests/test_contracts.py`.

**Interfaces:**
- Produces: `ActionableStrategy(symbol: str, market: str, side: str, entry: float, stop: float, target: float | None, source: str, rationale: str, cluster: str = "")` frozen dataclass with property `risk_per_share: float` (= `|entry − stop|`). `source` ∈ {"1-1","1-2","2","manual"}.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_contracts.py
from touzi_agent.core.contracts import ActionableStrategy


def test_fields_and_risk_per_share():
    s = ActionableStrategy(symbol="US.AAPL", market="US", side="LONG",
                           entry=100, stop=98, target=110, source="1-2",
                           rationale="ma cross up")
    assert s.risk_per_share == 2
    assert s.cluster == ""
    assert s.source == "1-2"
```

- [ ] **Step 2: Run test, expect FAIL** — `ModuleNotFoundError`.
  Run: `.venv/Scripts/python.exe -m pytest tests/test_contracts.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/core/__init__.py
```

```python
# touzi_agent/core/contracts.py
from dataclasses import dataclass


@dataclass(frozen=True)
class ActionableStrategy:
    symbol: str
    market: str
    side: str
    entry: float
    stop: float
    target: float | None
    source: str
    rationale: str
    cluster: str = ""

    @property
    def risk_per_share(self) -> float:
        return abs(self.entry - self.stop)
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/core/__init__.py touzi_agent/core/contracts.py tests/test_contracts.py
git commit -m "feat: ActionableStrategy common pipeline output contract"
```

---

### Task 2: L7 journal (SQLite)

**Files:** Create `touzi_agent/core/journal.py`; Test `tests/test_journal.py`.

**Interfaces:**
- Consumes: nothing (stores primitives).
- Produces:
  - `JournalStatus` Enum: `PROPOSED, ACCEPTED, REJECTED`.
  - `JournalEntry(timestamp: str, symbol: str, market: str, side: str, qty: int, entry: float, stop: float, target: float | None, source: str, rationale: str, status: str, planned_r: float, reject_reason: str = "")` frozen dataclass.
  - `Journal(conn)` with `init()`, `append(entry) -> int` (returns row id), `all() -> list[JournalEntry]` (ascending by id).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_journal.py
import sqlite3
import pytest
from touzi_agent.core.journal import Journal, JournalEntry, JournalStatus


@pytest.fixture
def journal():
    j = Journal(sqlite3.connect(":memory:"))
    j.init()
    return j


def _entry(status):
    return JournalEntry(timestamp="2026-06-21T10:00:00", symbol="US.AAPL",
                        market="US", side="LONG", qty=100, entry=100, stop=98,
                        target=110, source="1-2", rationale="x",
                        status=status, planned_r=2.0)


def test_append_and_read_back(journal):
    rid = journal.append(_entry(JournalStatus.ACCEPTED.value))
    assert rid == 1
    rows = journal.all()
    assert len(rows) == 1
    assert rows[0].symbol == "US.AAPL"
    assert rows[0].status == "ACCEPTED"


def test_multiple_entries_ordered(journal):
    journal.append(_entry(JournalStatus.PROPOSED.value))
    journal.append(_entry(JournalStatus.REJECTED.value))
    rows = journal.all()
    assert [r.status for r in rows] == ["PROPOSED", "REJECTED"]
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_journal.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/core/journal.py
import sqlite3
from dataclasses import dataclass
from enum import Enum


class JournalStatus(Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class JournalEntry:
    timestamp: str
    symbol: str
    market: str
    side: str
    qty: int
    entry: float
    stop: float
    target: float | None
    source: str
    rationale: str
    status: str
    planned_r: float
    reject_reason: str = ""


_COLS = ("timestamp", "symbol", "market", "side", "qty", "entry", "stop",
         "target", "source", "rationale", "status", "planned_r",
         "reject_reason")


class Journal:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def init(self) -> None:
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS l7_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT, symbol TEXT, market TEXT, side TEXT,
                qty INTEGER, entry REAL, stop REAL, target REAL,
                source TEXT, rationale TEXT, status TEXT, planned_r REAL,
                reject_reason TEXT)""")
        self.conn.commit()

    def append(self, entry: JournalEntry) -> int:
        cur = self.conn.execute(
            f"INSERT INTO l7_journal ({','.join(_COLS)}) "
            f"VALUES ({','.join('?' * len(_COLS))})",
            tuple(getattr(entry, c) for c in _COLS))
        self.conn.commit()
        return cur.lastrowid

    def all(self) -> list[JournalEntry]:
        rows = self.conn.execute(
            f"SELECT {','.join(_COLS)} FROM l7_journal ORDER BY id ASC"
        ).fetchall()
        return [JournalEntry(*row) for row in rows]
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/core/journal.py tests/test_journal.py
git commit -m "feat: L7 journal (SQLite) with append/read"
```

---

### Task 3: Unified portfolio/risk ledger (N1)

**Files:** Create `touzi_agent/core/ledger.py`; Test `tests/test_ledger.py`.

**Interfaces:**
- Consumes: `Position`, `Portfolio` (quant.portfolio), `RiskLimits`, `RiskModel`, `RiskDecision` (quant.risk).
- Produces:
  - `Ledger(equity: float, limits: RiskLimits)` with: `check(pos: Position) -> RiskDecision` (delegates to `RiskModel.check` against current portfolio); `record(pos: Position) -> None` (adds to the single shared portfolio); `positions -> list[Position]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ledger.py
from touzi_agent.quant.portfolio import Position
from touzi_agent.quant.risk import RiskLimits
from touzi_agent.core.ledger import Ledger


def _pos(sym, qty, entry, stop, market="US", cluster=""):
    return Position(symbol=sym, side="LONG", qty=qty, entry=entry,
                    stop=stop, market=market, cluster=cluster)


def test_check_allows_then_record_accumulates():
    led = Ledger(equity=100000, limits=RiskLimits())
    cand = _pos("US.AAPL", 100, 100, 98)
    assert led.check(cand).allowed is True
    led.record(cand)
    assert len(led.positions) == 1


def test_shared_ledger_blocks_combined_breach():
    # per-position cap 0.05; two 0.10 names individually fine vs heat,
    # but the shared ledger sees the second as breaching position cap
    led = Ledger(equity=100000, limits=RiskLimits(max_position_pct=0.05))
    cand = _pos("US.AAPL", 100, 100, 98)  # notional 0.10 > 0.05
    assert led.check(cand).allowed is False
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_ledger.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/core/ledger.py
from touzi_agent.quant.portfolio import Position, Portfolio
from touzi_agent.quant.risk import RiskLimits, RiskModel, RiskDecision


class Ledger:
    """Single authoritative portfolio + risk gate (spec N1, §4.5)."""

    def __init__(self, equity: float, limits: RiskLimits):
        self._portfolio = Portfolio(equity=equity, positions=[])
        self._model = RiskModel(limits)

    def check(self, pos: Position) -> RiskDecision:
        return self._model.check(self._portfolio, pos)

    def record(self, pos: Position) -> None:
        self._portfolio.positions.append(pos)

    @property
    def positions(self) -> list[Position]:
        return list(self._portfolio.positions)
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/core/ledger.py tests/test_ledger.py
git commit -m "feat: unified portfolio/risk ledger (N1)"
```

---

### Task 4: Concrete MA-cross strategy

**Files:** Create `touzi_agent/strategies/__init__.py`, `touzi_agent/strategies/ma_cross.py`; Test `tests/test_ma_cross.py`.

**Interfaces:**
- Consumes: `Bar` (models), `Signal`, `Strategy`, `StrategyStatus` (quant.strategy), `Side` (quant.trade).
- Produces:
  - `MACrossStrategy(fast: int = 2, slow: int = 3)` — `Strategy` subclass; `name="ma_cross"`, `status=StrategyStatus.CANDIDATE`, `universe=[]`. `generate` emits a LONG `Signal` (entry = last close, stop = min low of last `slow` bars) on a fast-over-slow SMA cross-up on the final bar.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ma_cross.py
from touzi_agent.models import Bar
from touzi_agent.strategies.ma_cross import MACrossStrategy


def _bar(date, close, low=None):
    low = close if low is None else low
    return Bar("US.AAPL", date, close, close + 1, low, close, 100, 100.0)


def test_emits_long_on_cross_up():
    # rising series so fast SMA crosses above slow SMA on the last bar
    bars = [_bar("d1", 10, 9), _bar("d2", 10, 9), _bar("d3", 10, 9),
            _bar("d4", 14, 11)]
    strat = MACrossStrategy(fast=2, slow=3)
    sigs = strat.generate({"US.AAPL": bars})
    assert len(sigs) == 1
    assert sigs[0].side == "LONG"
    assert sigs[0].entry == 14
    assert sigs[0].stop == min(9, 9, 11)  # min low over last `slow` bars


def test_no_signal_when_not_enough_bars():
    strat = MACrossStrategy(fast=2, slow=3)
    assert strat.generate({"US.AAPL": [_bar("d1", 10)]}) == []


def test_no_signal_when_flat():
    bars = [_bar("d1", 10) for _ in range(5)]
    assert MACrossStrategy(2, 3).generate({"US.AAPL": bars}) == []
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_ma_cross.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/strategies/__init__.py
```

```python
# touzi_agent/strategies/ma_cross.py
from touzi_agent.models import Bar
from touzi_agent.quant.strategy import Signal, Strategy, StrategyStatus
from touzi_agent.quant.trade import Side


def _sma(values: list[float], n: int) -> float:
    return sum(values[-n:]) / n


class MACrossStrategy(Strategy):
    name = "ma_cross"
    status = StrategyStatus.CANDIDATE
    universe: list[str] = []

    def __init__(self, fast: int = 2, slow: int = 3):
        self.fast = fast
        self.slow = slow

    def generate(self, bars_by_symbol: dict[str, list[Bar]]) -> list[Signal]:
        out: list[Signal] = []
        for symbol, bars in bars_by_symbol.items():
            if len(bars) < self.slow + 1:
                continue
            closes = [b.close for b in bars]
            fast_now, slow_now = _sma(closes, self.fast), _sma(closes, self.slow)
            fast_prev = _sma(closes[:-1], self.fast)
            slow_prev = _sma(closes[:-1], self.slow)
            crossed_up = fast_prev <= slow_prev and fast_now > slow_now
            if not crossed_up:
                continue
            last = bars[-1]
            stop = min(b.low for b in bars[-self.slow:])
            out.append(Signal(symbol=symbol, side=Side.LONG,
                              entry=last.close, stop=stop))
        return out
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Sanity-check it runs through the existing backtester**

Run:
```bash
.venv/Scripts/python.exe -c "from touzi_agent.strategies.ma_cross import MACrossStrategy; from touzi_agent.backtest.engine import backtest; from touzi_agent.config.loader import load_market_config, DEFAULT_MARKETS_DIR; from touzi_agent.models import Bar; bars=[Bar('US.AAPL','d%02d'%i, 10+max(0,i-3)*2, 12,9,10+max(0,i-3)*2,100,100.0) for i in range(6)]; cfg=load_market_config(DEFAULT_MARKETS_DIR/'market-us.yaml'); print(backtest(MACrossStrategy(2,3), {'US.AAPL':bars}, cfg, 100000, 0.01))"
```
Expected: prints a `BacktestResult` without error (proves the strategy is engine-compatible).

- [ ] **Step 6: Commit**

```bash
git add touzi_agent/strategies tests/test_ma_cross.py
git commit -m "feat: concrete MA-cross strategy on the Strategy interface"
```

---

### Task 5: Pipeline 1 — quant (modes 1-1 and 1-2)

**Files:** Create `touzi_agent/pipelines/__init__.py`, `touzi_agent/pipelines/quant.py`; Test `tests/test_pipeline_quant.py`.

**Interfaces:**
- Consumes: `Bar`, `Strategy`, `Signal`, `ActionableStrategy`.
- Produces:
  - `to_actionable(sig: Signal, market: str, source: str) -> ActionableStrategy`.
  - `llm_overlay_stub(s: ActionableStrategy) -> ActionableStrategy | None` — skeleton pass-through (returns `s`); the veto/shrink hook (returns `None`/shrunk later). Documented as a stub.
  - `run_quant_pipeline(strategy: Strategy, bars_by_symbol: dict[str, list[Bar]], market: str, mode: str) -> list[ActionableStrategy]` — `mode` ∈ {"1-1","1-2"}; "1-2" returns raw; "1-1" applies `llm_overlay_stub`, dropping `None`s.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline_quant.py
from touzi_agent.models import Bar
from touzi_agent.strategies.ma_cross import MACrossStrategy
from touzi_agent.pipelines.quant import run_quant_pipeline


def _bar(date, close, low):
    return Bar("US.AAPL", date, close, close + 1, low, close, 100, 100.0)


def _rising():
    return [_bar("d1", 10, 9), _bar("d2", 10, 9), _bar("d3", 10, 9),
            _bar("d4", 14, 11)]


def test_mode_1_2_direct():
    out = run_quant_pipeline(MACrossStrategy(2, 3), {"US.AAPL": _rising()},
                             "US", "1-2")
    assert len(out) == 1
    assert out[0].source == "1-2"
    assert out[0].symbol == "US.AAPL"
    assert out[0].entry == 14


def test_mode_1_1_overlay_passthrough():
    out = run_quant_pipeline(MACrossStrategy(2, 3), {"US.AAPL": _rising()},
                             "US", "1-1")
    assert len(out) == 1
    assert out[0].source == "1-1"
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_quant.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/pipelines/__init__.py
```

```python
# touzi_agent/pipelines/quant.py
from touzi_agent.models import Bar
from touzi_agent.quant.strategy import Signal, Strategy
from touzi_agent.core.contracts import ActionableStrategy


def to_actionable(sig: Signal, market: str, source: str) -> ActionableStrategy:
    return ActionableStrategy(
        symbol=sig.symbol, market=market, side=sig.side, entry=sig.entry,
        stop=sig.stop, target=sig.target, source=source,
        rationale=f"{source} quant signal", cluster=sig.cluster)


def llm_overlay_stub(s: ActionableStrategy) -> ActionableStrategy | None:
    """Phase-1 stub for the 1-1 LLM validation overlay.

    Real version may veto (return None) or shrink. Skeleton: pass-through.
    """
    return s


def run_quant_pipeline(strategy: Strategy, bars_by_symbol: dict[str, list[Bar]],
                       market: str, mode: str) -> list[ActionableStrategy]:
    if mode not in ("1-1", "1-2"):
        raise ValueError(f"mode must be '1-1' or '1-2', got {mode!r}")
    signals = strategy.generate(bars_by_symbol)
    items = [to_actionable(s, market, mode) for s in signals]
    if mode == "1-1":
        items = [r for s in items if (r := llm_overlay_stub(s)) is not None]
    return items
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/pipelines/__init__.py touzi_agent/pipelines/quant.py tests/test_pipeline_quant.py
git commit -m "feat: Pipeline 1 quant (modes 1-1 overlay / 1-2 direct)"
```

---

### Task 6: Pipeline 2 — pure-LLM stub

**Files:** Create `touzi_agent/pipelines/llm_pick.py`; Test `tests/test_pipeline_llm_pick.py`.

**Interfaces:**
- Produces: `run_llm_pick_stub(market: str) -> list[ActionableStrategy]` — returns one canned, reasoned `ActionableStrategy` with `source="2"`. (Real version aggregates RAG+news daily; stub returns a fixed candidate.)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline_llm_pick.py
from touzi_agent.pipelines.llm_pick import run_llm_pick_stub


def test_returns_one_reasoned_candidate():
    out = run_llm_pick_stub("US")
    assert len(out) == 1
    assert out[0].source == "2"
    assert out[0].market == "US"
    assert out[0].rationale  # non-empty reasoning
    assert out[0].risk_per_share > 0
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_llm_pick.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/pipelines/llm_pick.py
from touzi_agent.core.contracts import ActionableStrategy


def run_llm_pick_stub(market: str) -> list[ActionableStrategy]:
    """Phase-1 stub for Pipeline 2 (pure RAG+LLM stock picking).

    Real version: daily aggregate RAG + market data + news -> reasoned
    shortlist. Skeleton: one fixed reasoned candidate.
    """
    return [ActionableStrategy(
        symbol="US.MSFT", market=market, side="LONG", entry=400.0,
        stop=380.0, target=460.0, source="2",
        rationale="[stub] illustrative pure-LLM pick; not yet wired to RAG")]
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/pipelines/llm_pick.py tests/test_pipeline_llm_pick.py
git commit -m "feat: Pipeline 2 pure-LLM pick stub"
```

---

### Task 7: Pipeline 3 — decision-support stub

**Files:** Create `touzi_agent/pipelines/decision_support.py`; Test `tests/test_pipeline_decision_support.py`.

**Interfaces:**
- Produces: `answer_query(query: str) -> str` — returns targeted advice text for a self-directed trade query. (Real version: RAG+LLM over holdings/history; stub echoes the query in a structured canned answer.) Raises `ValueError` on empty query.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline_decision_support.py
import pytest
from touzi_agent.pipelines.decision_support import answer_query


def test_returns_targeted_advice():
    ans = answer_query("Should I buy AAPL here?")
    assert isinstance(ans, str)
    assert "AAPL" in ans


def test_empty_query_rejected():
    with pytest.raises(ValueError):
        answer_query("   ")
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_decision_support.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/pipelines/decision_support.py
def answer_query(query: str) -> str:
    """Phase-1 stub for Pipeline 3 (independent on-demand Q&A).

    Real version: RAG+LLM over holdings/history/risk model. Skeleton:
    structured canned response echoing the query.
    """
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    return (f"[decision-support stub] Re: {query.strip()!r} — "
            "RAG+LLM not yet wired. Remember: define your stop before entry.")
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/pipelines/decision_support.py tests/test_pipeline_decision_support.py
git commit -m "feat: Pipeline 3 decision-support stub"
```

---

### Task 8: Cross-cutting discipline layer

**Files:** Create `touzi_agent/discipline/__init__.py`, `touzi_agent/discipline/layer.py`; Test `tests/test_discipline.py`.

**Interfaces:**
- Consumes: `ActionableStrategy`.
- Produces:
  - `GuardrailResult(allowed: bool, reasons: list[str])` frozen dataclass.
  - `DisciplineLayer()` with `check(s: ActionableStrategy) -> GuardrailResult` (blocks when `risk_per_share == 0` → "stop required") and `log(event: str) -> None` (appends to `events: list[str]`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_discipline.py
from touzi_agent.core.contracts import ActionableStrategy
from touzi_agent.discipline.layer import DisciplineLayer


def _s(entry, stop):
    return ActionableStrategy("US.AAPL", "US", "LONG", entry, stop, None,
                              "1-2", "x")


def test_allows_with_valid_stop():
    assert DisciplineLayer().check(_s(100, 98)).allowed is True


def test_blocks_when_no_effective_stop():
    res = DisciplineLayer().check(_s(100, 100))
    assert res.allowed is False
    assert any("stop" in r.lower() for r in res.reasons)


def test_logging():
    layer = DisciplineLayer()
    layer.log("checked AAPL")
    assert layer.events == ["checked AAPL"]
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_discipline.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/discipline/__init__.py
```

```python
# touzi_agent/discipline/layer.py
from dataclasses import dataclass, field

from touzi_agent.core.contracts import ActionableStrategy


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reasons: list[str]


@dataclass
class DisciplineLayer:
    """Cross-cutting binding guardrails over ALL trades (spec §8)."""
    events: list[str] = field(default_factory=list)

    def check(self, s: ActionableStrategy) -> GuardrailResult:
        reasons: list[str] = []
        if s.risk_per_share == 0:
            reasons.append("stop required (entry == stop, no risk defined)")
        return GuardrailResult(allowed=(reasons == []), reasons=reasons)

    def log(self, event: str) -> None:
        self.events.append(event)
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/discipline tests/test_discipline.py
git commit -m "feat: cross-cutting discipline layer with binding stop guardrail"
```

---

### Task 9: Proposal assembly + human gate

**Files:** Create `touzi_agent/core/proposal.py`; Test `tests/test_proposal.py`.

**Interfaces:**
- Consumes: `ActionableStrategy`, `Ledger`, `DisciplineLayer`, `Position` (quant.portfolio), `size_position` (quant.sizing), `RiskDecision`, `GuardrailResult`.
- Produces:
  - `Proposal(strategy: ActionableStrategy, qty: int, risk: RiskDecision, guard: GuardrailResult)` frozen dataclass with property `acceptable: bool` (= `qty > 0 and risk.allowed and guard.allowed`).
  - `assemble_proposal(s, ledger, discipline, equity, risk_fraction, lot_size=1) -> Proposal` — sizes via `size_position`, builds a candidate `Position`, runs ledger + discipline checks.
  - `human_gate(proposal, confirm_fn) -> bool` — returns False immediately if not `proposal.acceptable`; else returns `confirm_fn(proposal)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_proposal.py
from touzi_agent.core.contracts import ActionableStrategy
from touzi_agent.core.ledger import Ledger
from touzi_agent.quant.risk import RiskLimits
from touzi_agent.discipline.layer import DisciplineLayer
from touzi_agent.core.proposal import assemble_proposal, human_gate


def _s(entry=100, stop=98):
    return ActionableStrategy("US.AAPL", "US", "LONG", entry, stop, 110,
                              "1-2", "x")


def _ctx():
    return Ledger(100000, RiskLimits()), DisciplineLayer()


def test_acceptable_proposal_and_confirm():
    led, dis = _ctx()
    p = assemble_proposal(_s(), led, dis, 100000, 0.01, lot_size=1)
    assert p.qty > 0
    assert p.acceptable is True
    assert human_gate(p, lambda prop: True) is True
    assert human_gate(p, lambda prop: False) is False


def test_no_stop_blocks_regardless_of_confirm():
    led, dis = _ctx()
    p = assemble_proposal(_s(100, 100), led, dis, 100000, 0.01)
    assert p.acceptable is False
    assert human_gate(p, lambda prop: True) is False  # gate refuses


def test_risk_breach_blocks():
    led = Ledger(100000, RiskLimits(max_position_pct=0.005))
    dis = DisciplineLayer()
    p = assemble_proposal(_s(), led, dis, 100000, 0.01)
    assert p.risk.allowed is False
    assert p.acceptable is False
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_proposal.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/core/proposal.py
from dataclasses import dataclass

from touzi_agent.core.contracts import ActionableStrategy
from touzi_agent.core.ledger import Ledger
from touzi_agent.discipline.layer import DisciplineLayer, GuardrailResult
from touzi_agent.quant.portfolio import Position
from touzi_agent.quant.risk import RiskDecision
from touzi_agent.quant.sizing import size_position


@dataclass(frozen=True)
class Proposal:
    strategy: ActionableStrategy
    qty: int
    risk: RiskDecision
    guard: GuardrailResult

    @property
    def acceptable(self) -> bool:
        return self.qty > 0 and self.risk.allowed and self.guard.allowed


def assemble_proposal(s: ActionableStrategy, ledger: Ledger,
                      discipline: DisciplineLayer, equity: float,
                      risk_fraction: float, lot_size: int = 1) -> Proposal:
    guard = discipline.check(s)
    if s.risk_per_share == 0:
        qty = 0
        from touzi_agent.quant.risk import RiskDecision as _RD
        risk = _RD(allowed=False, reasons=["no stop; not sized"])
    else:
        qty = size_position(equity, risk_fraction, s.entry, s.stop, lot_size)
        cand = Position(symbol=s.symbol, side=s.side, qty=qty, entry=s.entry,
                        stop=s.stop, market=s.market, cluster=s.cluster)
        risk = ledger.check(cand)
    return Proposal(strategy=s, qty=qty, risk=risk, guard=guard)


def human_gate(proposal: Proposal, confirm_fn) -> bool:
    if not proposal.acceptable:
        return False
    return bool(confirm_fn(proposal))
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Commit**

```bash
git add touzi_agent/core/proposal.py tests/test_proposal.py
git commit -m "feat: proposal assembly + human gate (ledger+discipline checks)"
```

---

### Task 10: Orchestrator + end-to-end smoke test

**Files:** Create `touzi_agent/core/orchestrator.py`; Test `tests/test_orchestrator_e2e.py`.

**Interfaces:**
- Consumes: everything above (`run_quant_pipeline`, `run_llm_pick_stub`, `MACrossStrategy`, `Ledger`, `DisciplineLayer`, `Journal`, `assemble_proposal`, `human_gate`, `Position`).
- Produces:
  - `run_once(bars_by_symbol, market, strategy, ledger, discipline, journal, equity, risk_fraction, confirm_fn, lot_size=1) -> dict` — runs Pipelines 1-2, 1-1, and 2; for each output assembles a proposal, runs the gate; on accept records to ledger + writes an ACCEPTED `JournalEntry`, else writes a REJECTED one. Returns `{"outputs": [...], "accepted": [...]}`.
  - Helper `_now() -> str` (ISO timestamp).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orchestrator_e2e.py
import sqlite3
from touzi_agent.models import Bar
from touzi_agent.strategies.ma_cross import MACrossStrategy
from touzi_agent.core.ledger import Ledger
from touzi_agent.quant.risk import RiskLimits
from touzi_agent.discipline.layer import DisciplineLayer
from touzi_agent.core.journal import Journal
from touzi_agent.core.orchestrator import run_once
from touzi_agent.pipelines.decision_support import answer_query


def _bar(date, close, low):
    return Bar("US.AAPL", date, close, close + 1, low, close, 100, 100.0)


def _rising():
    return [_bar("d1", 10, 9), _bar("d2", 10, 9), _bar("d3", 10, 9),
            _bar("d4", 14, 11)]


def test_end_to_end_full_path():
    conn = sqlite3.connect(":memory:")
    journal = Journal(conn)
    journal.init()
    ledger = Ledger(100000, RiskLimits())
    out = run_once({"US.AAPL": _rising()}, "US", MACrossStrategy(2, 3),
                   ledger, DisciplineLayer(), journal,
                   equity=100000, risk_fraction=0.01,
                   confirm_fn=lambda prop: True)
    # Pipelines 1-2, 1-1 (quant) + 2 (stub) all produced outputs
    assert len(out["outputs"]) >= 3
    # at least one trade accepted, recorded, journaled
    assert len(out["accepted"]) >= 1
    rows = journal.all()
    assert any(r.status == "ACCEPTED" for r in rows)
    assert len(ledger.positions) >= 1


def test_pipeline_3_is_independent_qa():
    # Pipeline 3 runs on its own, not part of run_once
    assert "AAPL" in answer_query("thoughts on AAPL?")
```

- [ ] **Step 2: Run test, expect FAIL.**
  Run: `.venv/Scripts/python.exe -m pytest tests/test_orchestrator_e2e.py -v`

- [ ] **Step 3: Implement**

```python
# touzi_agent/core/orchestrator.py
from datetime import datetime, timezone

from touzi_agent.models import Bar
from touzi_agent.quant.strategy import Strategy
from touzi_agent.quant.portfolio import Position
from touzi_agent.core.ledger import Ledger
from touzi_agent.core.journal import Journal, JournalEntry, JournalStatus
from touzi_agent.core.proposal import assemble_proposal, human_gate, Proposal
from touzi_agent.discipline.layer import DisciplineLayer
from touzi_agent.pipelines.quant import run_quant_pipeline
from touzi_agent.pipelines.llm_pick import run_llm_pick_stub


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _journal_entry(p: Proposal, status: str, reject: str = "") -> JournalEntry:
    s = p.strategy
    return JournalEntry(
        timestamp=_now(), symbol=s.symbol, market=s.market, side=s.side,
        qty=p.qty, entry=s.entry, stop=s.stop, target=s.target,
        source=s.source, rationale=s.rationale, status=status,
        planned_r=s.risk_per_share, reject_reason=reject)


def run_once(bars_by_symbol: dict[str, list[Bar]], market: str,
             strategy: Strategy, ledger: Ledger, discipline: DisciplineLayer,
             journal: Journal, equity: float, risk_fraction: float,
             confirm_fn, lot_size: int = 1) -> dict:
    outputs = []
    outputs += run_quant_pipeline(strategy, bars_by_symbol, market, "1-2")
    outputs += run_quant_pipeline(strategy, bars_by_symbol, market, "1-1")
    outputs += run_llm_pick_stub(market)

    accepted = []
    for s in outputs:
        p = assemble_proposal(s, ledger, discipline, equity, risk_fraction,
                              lot_size)
        if human_gate(p, confirm_fn):
            ledger.record(Position(symbol=s.symbol, side=s.side, qty=p.qty,
                                   entry=s.entry, stop=s.stop,
                                   market=s.market, cluster=s.cluster))
            journal.append(_journal_entry(p, JournalStatus.ACCEPTED.value))
            accepted.append(p)
        else:
            reason = "; ".join(p.guard.reasons + p.risk.reasons) or "declined"
            journal.append(_journal_entry(p, JournalStatus.REJECTED.value,
                                          reason))
    return {"outputs": outputs, "accepted": accepted}
```

- [ ] **Step 4: Run test, expect PASS.**
- [ ] **Step 5: Run the full suite** — `.venv/Scripts/python.exe -m pytest -q` (all prior + Phase 1 green).
- [ ] **Step 6: Commit**

```bash
git add touzi_agent/core/orchestrator.py tests/test_orchestrator_e2e.py
git commit -m "feat: orchestrator wiring four pipelines -> discipline+ledger -> gate -> journal"
```

---

## Plan Self-Review

**Spec coverage (Phase 1 = walking skeleton, spec §13):**
- Freeze contracts (output type, journal, ledger) → Tasks 1, 2, 3 ✅
- Single unified portfolio/risk ledger N1 (§4.5) → Task 3 ✅
- One simple price/volume quant strategy + engine compatibility → Task 4 ✅
- Pipeline 1-2 (direct) & 1-1 (LLM-overlay stub) → Task 5 ✅
- Pipeline 2 pure-LLM stub → Task 6 ✅
- Pipeline 3 independent Q&A stub (§7.2) → Task 7 ✅
- Cross-cutting discipline layer + binding stop guardrail (§8.2) → Task 8 ✅
- Proposal → human gate → L7 journal → Tasks 9, 10 ✅
- End-to-end smoke across four pipelines → Task 10 ✅
- *Deferred (correct):* real LLM overlay/picks, RAG, forward-paper depth, §12 fidelity fixes, promotion loop — later phases/tracks.

**Placeholder scan:** Stubs are intentional and labeled (`run_llm_pick_stub`, `llm_overlay_stub`, `answer_query`, decision-support) — each has complete, runnable code, not a TODO. No "TBD"/"implement later". ✅

**Type consistency:** `ActionableStrategy` fields used identically across Tasks 1/5/6/8/9/10; `Proposal`/`Ledger`/`DisciplineLayer`/`Journal` signatures match between producer and consumer tasks; `source` codes ("1-1","1-2","2") consistent; `risk_per_share` used uniformly. `run_quant_pipeline(strategy, bars_by_symbol, market, mode)` arg order identical in Tasks 5 and 10. ✅

**Note for implementer:** Tasks are sequential (each consumes prior). After Task 10, update `ROADMAP.md` Phase 1 checkboxes to ✅ and the snapshot row.
