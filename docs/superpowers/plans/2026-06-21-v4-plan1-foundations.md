# V4.0 Plan 1 — Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the greenfield project and a 富途-backed data foundation: project scaffold, domain models, per-market config (US/HK/CN), a structured SQLite store, rule-aware market adapters, and an ingestion path that fetches OHLCV via 富途 OpenD and persists it.

**Architecture:** Layered and dependency-injected. 富途 coupling lives behind a single `FutuClient` protocol so adapters depend on an interface (real client wraps the 富途 SDK; a fake client drives all tests — the live OpenD gateway is never touched in tests). All numeric market data lands in a structured SQLite store (never a vector store). Each market's differences (settlement, limits, costs, code prefix) live in YAML config, consumed by a shared adapter base.

**Tech Stack:** Python 3.12, conda, pytest, pandas, PyYAML, futu-api (富途 OpenD SDK).

## Global Constraints

- **Markets:** US (primary), HK, A-share (CN). Source: 富途 OpenAPI (OpenD) for all three. — copied from spec §1.3, §8.
- **Numbers → structured store only.** Prices/financials/returns live in SQLite/Parquet, never the vector store. — spec §6.1 ("数字永不来自向量库").
- **A-share rules are first-class:** T+1 settlement, ±10%/±20% daily limits, sell-side stamp duty. Config must carry these so later plans can model gap risk. — spec §8.2, §8.3.
- **Base currency: HKD.** Each market config carries its own trade currency (USD/HKD/CNY). — spec §8.5.
- **Costs are always available net** (commission, stamp duty, platform fee) per market for later expectancy math. — spec §3, §4.4.
- **TDD, DRY, YAGNI, frequent commits.** Every code step is preceded by a failing test.

---

## File Structure

```
environment.yml                         # conda env (python 3.12, pytest, pandas, pyyaml, futu-api)
pyproject.toml                          # package metadata, pytest config
touzi_agent/
  __init__.py
  models.py                             # MarketConfig, Instrument, Bar dataclasses
  config/
    __init__.py
    loader.py                           # load_market_config, load_all_markets
    markets/
      market-us.yaml
      market-hk.yaml
      market-cn.yaml
  data/
    __init__.py
    db.py                               # init_db, upsert/query instruments & bars
  adapters/
    __init__.py
    client.py                           # FutuClient protocol + RealFutuClient
    base.py                             # BaseDataAdapter
    markets.py                          # USDataAdapter, HKDataAdapter, CNDataAdapter
  ingestion/
    __init__.py
    ingest.py                           # ingest_bars(adapter, conn, symbol, start, end)
tests/
  conftest.py                           # FakeFutuClient, temp db, sample configs
  test_models.py
  test_config_loader.py
  test_db.py
  test_base_adapter.py
  test_market_adapters.py
  test_ingest.py
```

---

### Task 1: Project scaffold + conda env + pytest

**Files:**
- Create: `environment.yml`
- Create: `pyproject.toml`
- Create: `touzi_agent/__init__.py`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing.
- Produces: importable package `touzi_agent` with `__version__: str`; a working `pytest` run.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
import touzi_agent


def test_package_has_version():
    assert isinstance(touzi_agent.__version__, str)
    assert touzi_agent.__version__ != ""
```

- [ ] **Step 2: Create the conda env file and package metadata**

```yaml
# environment.yml
name: touzi-agent
channels:
  - conda-forge
dependencies:
  - python=3.12
  - pytest
  - pandas
  - pyyaml
  - pip
  - pip:
      - futu-api
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "touzi-agent"
version = "0.1.0"
requires-python = ">=3.12"

[tool.setuptools.packages.find]
include = ["touzi_agent*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"
```

```python
# touzi_agent/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 3: Create the environment and install the package**

Run:
```bash
conda env create -f environment.yml
conda run -n touzi-agent pip install -e .
```
Expected: env `touzi-agent` created; editable install succeeds ("Successfully installed touzi-agent").

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_smoke.py -v`
Expected: PASS (`test_package_has_version PASSED`).

- [ ] **Step 5: Commit**

```bash
git add environment.yml pyproject.toml touzi_agent/__init__.py tests/test_smoke.py
git commit -m "feat: project scaffold (conda env, package, pytest smoke test)"
```

---

### Task 2: Domain models

**Files:**
- Create: `touzi_agent/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Bar(code: str, date: str, open: float, high: float, low: float, close: float, volume: int, turnover: float)` — frozen dataclass.
  - `Instrument(code: str, market: str, name: str, lot_size: int, board: str)` — frozen dataclass.
  - `MarketConfig(market: str, currency: str, settlement: str, short_selling: str, code_prefix: str, daily_limit: dict | None, costs: dict)` — frozen dataclass with method `limit_for(board: str) -> float | None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from touzi_agent.models import Bar, Instrument, MarketConfig


def test_bar_fields():
    bar = Bar(code="US.AAPL", date="2026-06-19", open=1.0, high=2.0,
              low=0.5, close=1.5, volume=100, turnover=150.0)
    assert bar.code == "US.AAPL"
    assert bar.close == 1.5


def test_instrument_fields():
    inst = Instrument(code="HK.00700", market="HK", name="TENCENT",
                      lot_size=100, board="main_board")
    assert inst.lot_size == 100


def test_market_config_limit_lookup():
    cfg = MarketConfig(market="CN", currency="CNY", settlement="T+1",
                       short_selling="restricted", code_prefix="",
                       daily_limit={"main_board": 0.10, "chinext": 0.20},
                       costs={"commission_rate": 0.0003})
    assert cfg.limit_for("main_board") == 0.10
    assert cfg.limit_for("chinext") == 0.20
    assert cfg.limit_for("unknown") is None


def test_market_config_no_limit_market():
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None, costs={})
    assert cfg.limit_for("main_board") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n touzi-agent pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touzi_agent.models'`.

- [ ] **Step 3: Write minimal implementation**

```python
# touzi_agent/models.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_models.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add touzi_agent/models.py tests/test_models.py
git commit -m "feat: domain models (Bar, Instrument, MarketConfig)"
```

---

### Task 3: Per-market config + loader

**Files:**
- Create: `touzi_agent/config/__init__.py`
- Create: `touzi_agent/config/markets/market-us.yaml`
- Create: `touzi_agent/config/markets/market-hk.yaml`
- Create: `touzi_agent/config/markets/market-cn.yaml`
- Create: `touzi_agent/config/loader.py`
- Test: `tests/test_config_loader.py`

**Interfaces:**
- Consumes: `MarketConfig` from Task 2.
- Produces:
  - `load_market_config(path: str | Path) -> MarketConfig` — raises `ValueError` if a required field is missing or `settlement` not in `{"T+0","T+1","T+2"}`.
  - `load_all_markets(dir: str | Path) -> dict[str, MarketConfig]` — keyed by `MarketConfig.market` (e.g. `"US"`).
  - `DEFAULT_MARKETS_DIR: Path` — points at `touzi_agent/config/markets`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config_loader.py
import pytest
from touzi_agent.config.loader import (
    load_market_config, load_all_markets, DEFAULT_MARKETS_DIR,
)


def test_loads_us_config():
    cfg = load_market_config(DEFAULT_MARKETS_DIR / "market-us.yaml")
    assert cfg.market == "US"
    assert cfg.settlement == "T+0"
    assert cfg.daily_limit is None
    assert cfg.currency == "USD"


def test_loads_cn_config_with_limits():
    cfg = load_market_config(DEFAULT_MARKETS_DIR / "market-cn.yaml")
    assert cfg.market == "CN"
    assert cfg.settlement == "T+1"
    assert cfg.limit_for("main_board") == 0.10
    assert cfg.limit_for("chinext") == 0.20


def test_load_all_markets_keyed_by_market():
    markets = load_all_markets(DEFAULT_MARKETS_DIR)
    assert set(markets) == {"US", "HK", "CN"}
    assert markets["HK"].settlement == "T+2"


def test_invalid_settlement_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "market: XX\ncurrency: USD\nsettlement: T+9\n"
        "short_selling: allowed\ncode_prefix: XX\n"
        "daily_limit: null\ncosts: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_market_config(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n touzi-agent pytest tests/test_config_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touzi_agent.config.loader'`.

- [ ] **Step 3: Create the config package, YAML files, and loader**

```python
# touzi_agent/config/__init__.py
```

```yaml
# touzi_agent/config/markets/market-us.yaml
market: US
currency: USD
settlement: T+0
short_selling: allowed
code_prefix: US
daily_limit: null
costs:
  commission_rate: 0.0003
  min_commission: 0.99
  stamp_duty: 0.0
  platform_fee: 0.0
```

```yaml
# touzi_agent/config/markets/market-hk.yaml
market: HK
currency: HKD
settlement: T+2
short_selling: limited
code_prefix: HK
daily_limit: null
costs:
  commission_rate: 0.0003
  min_commission: 3.0
  stamp_duty: 0.0013
  platform_fee: 15.0
```

```yaml
# touzi_agent/config/markets/market-cn.yaml
market: CN
currency: CNY
settlement: T+1
short_selling: restricted
code_prefix: ""
daily_limit:
  main_board: 0.10
  star_board: 0.20
  chinext: 0.20
costs:
  commission_rate: 0.0003
  min_commission: 5.0
  stamp_duty: 0.0005
  transfer_fee: 0.00001
```

```python
# touzi_agent/config/loader.py
from pathlib import Path
import yaml

from touzi_agent.models import MarketConfig

DEFAULT_MARKETS_DIR = Path(__file__).parent / "markets"
_REQUIRED = ("market", "currency", "settlement", "short_selling",
             "code_prefix", "daily_limit", "costs")
_VALID_SETTLEMENT = {"T+0", "T+1", "T+2"}


def load_market_config(path: str | Path) -> MarketConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise ValueError(f"{path}: missing required fields {missing}")
    if data["settlement"] not in _VALID_SETTLEMENT:
        raise ValueError(
            f"{path}: invalid settlement {data['settlement']!r}")
    return MarketConfig(
        market=data["market"],
        currency=data["currency"],
        settlement=data["settlement"],
        short_selling=data["short_selling"],
        code_prefix=data["code_prefix"],
        daily_limit=data["daily_limit"],
        costs=data["costs"],
    )


def load_all_markets(dir: str | Path) -> dict[str, MarketConfig]:
    result: dict[str, MarketConfig] = {}
    for path in sorted(Path(dir).glob("market-*.yaml")):
        cfg = load_market_config(path)
        result[cfg.market] = cfg
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_config_loader.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add touzi_agent/config tests/test_config_loader.py
git commit -m "feat: per-market config (US/HK/CN) + validating loader"
```

---

### Task 4: Structured SQLite store

**Files:**
- Create: `touzi_agent/data/__init__.py`
- Create: `touzi_agent/data/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `Bar`, `Instrument` from Task 2.
- Produces:
  - `init_db(conn: sqlite3.Connection) -> None` — creates `instruments` and `ohlcv` tables (idempotent).
  - `upsert_instrument(conn, inst: Instrument) -> None`
  - `get_instrument(conn, code: str) -> Instrument | None`
  - `upsert_bars(conn, bars: list[Bar]) -> int` — returns rows written; primary key `(code, date)`, re-ingest overwrites.
  - `get_bars(conn, code: str, start: str, end: str) -> list[Bar]` — inclusive date range, ordered ascending by date.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db.py
import sqlite3
import pytest
from touzi_agent.models import Bar, Instrument
from touzi_agent.data.db import (
    init_db, upsert_instrument, get_instrument, upsert_bars, get_bars,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


def test_instrument_roundtrip(conn):
    inst = Instrument(code="US.AAPL", market="US", name="Apple",
                      lot_size=1, board="main_board")
    upsert_instrument(conn, inst)
    assert get_instrument(conn, "US.AAPL") == inst
    assert get_instrument(conn, "US.MISSING") is None


def test_bars_insert_and_range_query(conn):
    bars = [
        Bar("US.AAPL", "2026-06-17", 1, 2, 0.5, 1.5, 10, 15.0),
        Bar("US.AAPL", "2026-06-18", 1.5, 2.5, 1, 2.0, 20, 40.0),
        Bar("US.AAPL", "2026-06-19", 2.0, 3, 1.8, 2.8, 30, 84.0),
    ]
    assert upsert_bars(conn, bars) == 3
    got = get_bars(conn, "US.AAPL", "2026-06-18", "2026-06-19")
    assert [b.date for b in got] == ["2026-06-18", "2026-06-19"]
    assert got[0].close == 2.0


def test_bars_upsert_overwrites(conn):
    upsert_bars(conn, [Bar("US.AAPL", "2026-06-19", 1, 1, 1, 1, 1, 1.0)])
    upsert_bars(conn, [Bar("US.AAPL", "2026-06-19", 2, 2, 2, 2, 2, 2.0)])
    got = get_bars(conn, "US.AAPL", "2026-06-19", "2026-06-19")
    assert len(got) == 1
    assert got[0].close == 2.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n touzi-agent pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touzi_agent.data.db'`.

- [ ] **Step 3: Write minimal implementation**

```python
# touzi_agent/data/__init__.py
```

```python
# touzi_agent/data/db.py
import sqlite3

from touzi_agent.models import Bar, Instrument


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS instruments (
            code TEXT PRIMARY KEY, market TEXT NOT NULL, name TEXT,
            lot_size INTEGER NOT NULL, board TEXT NOT NULL)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ohlcv (
            code TEXT NOT NULL, date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL,
            volume INTEGER, turnover REAL,
            PRIMARY KEY (code, date))"""
    )
    conn.commit()


def upsert_instrument(conn: sqlite3.Connection, inst: Instrument) -> None:
    conn.execute(
        """INSERT INTO instruments (code, market, name, lot_size, board)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(code) DO UPDATE SET
             market=excluded.market, name=excluded.name,
             lot_size=excluded.lot_size, board=excluded.board""",
        (inst.code, inst.market, inst.name, inst.lot_size, inst.board),
    )
    conn.commit()


def get_instrument(conn: sqlite3.Connection, code: str) -> Instrument | None:
    row = conn.execute(
        "SELECT code, market, name, lot_size, board FROM instruments "
        "WHERE code = ?", (code,)).fetchone()
    if row is None:
        return None
    return Instrument(*row)


def upsert_bars(conn: sqlite3.Connection, bars: list[Bar]) -> int:
    conn.executemany(
        """INSERT INTO ohlcv
             (code, date, open, high, low, close, volume, turnover)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(code, date) DO UPDATE SET
             open=excluded.open, high=excluded.high, low=excluded.low,
             close=excluded.close, volume=excluded.volume,
             turnover=excluded.turnover""",
        [(b.code, b.date, b.open, b.high, b.low, b.close,
          b.volume, b.turnover) for b in bars],
    )
    conn.commit()
    return len(bars)


def get_bars(conn: sqlite3.Connection, code: str,
             start: str, end: str) -> list[Bar]:
    rows = conn.execute(
        """SELECT code, date, open, high, low, close, volume, turnover
           FROM ohlcv WHERE code = ? AND date >= ? AND date <= ?
           ORDER BY date ASC""", (code, start, end)).fetchall()
    return [Bar(*row) for row in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_db.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add touzi_agent/data tests/test_db.py
git commit -m "feat: structured SQLite store for instruments and OHLCV"
```

---

### Task 5: FutuClient protocol + base adapter + shared test fixtures

**Files:**
- Create: `touzi_agent/adapters/__init__.py`
- Create: `touzi_agent/adapters/client.py`
- Create: `touzi_agent/adapters/base.py`
- Create: `tests/conftest.py`
- Test: `tests/test_base_adapter.py`

**Interfaces:**
- Consumes: `Bar`, `MarketConfig` from Tasks 2/3.
- Produces:
  - `FutuClient` (typing.Protocol): `get_history_kline(code: str, start: str, end: str, ktype: str = "K_DAY") -> list[dict]` where each dict has keys `time_key, open, high, low, close, volume, turnover`.
  - `RealFutuClient` — wraps the 富途 `OpenQuoteContext`; constructed with `host`/`port`. (Not unit-tested; integration only.)
  - `BaseDataAdapter(config: MarketConfig, client: FutuClient)` with:
    - `full_code(symbol: str) -> str` — joins `code_prefix` + symbol (e.g. `"AAPL" -> "US.AAPL"`).
    - `fetch_bars(symbol: str, start: str, end: str) -> list[Bar]` — calls client, normalizes rows to `Bar` (date = first 10 chars of `time_key`).
  - Pytest fixtures in `conftest.py`: `fake_client` (a `FakeFutuClient` with canned kline) and `us_config` (a `MarketConfig` for US).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_base_adapter.py
from touzi_agent.adapters.base import BaseDataAdapter


def test_full_code_prefixes(us_config, fake_client):
    adapter = BaseDataAdapter(us_config, fake_client)
    assert adapter.full_code("AAPL") == "US.AAPL"


def test_fetch_bars_normalizes_kline(us_config, fake_client):
    adapter = BaseDataAdapter(us_config, fake_client)
    bars = adapter.fetch_bars("AAPL", "2026-06-18", "2026-06-19")
    assert [b.date for b in bars] == ["2026-06-18", "2026-06-19"]
    assert bars[0].code == "US.AAPL"
    assert bars[0].close == 2.0
    assert bars[1].volume == 30
```

- [ ] **Step 2: Write the shared fixtures**

```python
# tests/conftest.py
import pytest
from touzi_agent.models import MarketConfig


class FakeFutuClient:
    """In-memory stand-in for FutuClient; returns canned daily kline."""

    def __init__(self, rows=None):
        self._rows = rows if rows is not None else [
            {"time_key": "2026-06-18 00:00:00", "open": 1.5, "high": 2.5,
             "low": 1.0, "close": 2.0, "volume": 20, "turnover": 40.0},
            {"time_key": "2026-06-19 00:00:00", "open": 2.0, "high": 3.0,
             "low": 1.8, "close": 2.8, "volume": 30, "turnover": 84.0},
        ]
        self.calls = []

    def get_history_kline(self, code, start, end, ktype="K_DAY"):
        self.calls.append((code, start, end, ktype))
        return list(self._rows)


@pytest.fixture
def fake_client():
    return FakeFutuClient()


@pytest.fixture
def us_config():
    return MarketConfig(market="US", currency="USD", settlement="T+0",
                        short_selling="allowed", code_prefix="US",
                        daily_limit=None, costs={})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `conda run -n touzi-agent pytest tests/test_base_adapter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touzi_agent.adapters.base'`.

- [ ] **Step 4: Write minimal implementation**

```python
# touzi_agent/adapters/__init__.py
```

```python
# touzi_agent/adapters/client.py
from typing import Protocol


class FutuClient(Protocol):
    def get_history_kline(self, code: str, start: str, end: str,
                          ktype: str = "K_DAY") -> list[dict]:
        ...


class RealFutuClient:
    """Wraps 富途 OpenQuoteContext. Requires a running OpenD gateway.

    Not exercised by unit tests; used in production/integration only.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        from futu import OpenQuoteContext
        self._ctx = OpenQuoteContext(host=host, port=port)

    def get_history_kline(self, code: str, start: str, end: str,
                          ktype: str = "K_DAY") -> list[dict]:
        from futu import RET_OK, KLType
        ret, data = self._ctx.request_history_kline(
            code, start=start, end=end,
            ktype=getattr(KLType, ktype))
        if ret != RET_OK:
            raise RuntimeError(f"富途 history kline failed: {data}")
        return data.to_dict("records")

    def close(self) -> None:
        self._ctx.close()
```

```python
# touzi_agent/adapters/base.py
from touzi_agent.models import Bar, MarketConfig
from touzi_agent.adapters.client import FutuClient


class BaseDataAdapter:
    def __init__(self, config: MarketConfig, client: FutuClient):
        self.config = config
        self.client = client

    def full_code(self, symbol: str) -> str:
        prefix = self.config.code_prefix
        return f"{prefix}.{symbol}" if prefix else symbol

    def fetch_bars(self, symbol: str, start: str, end: str) -> list[Bar]:
        code = self.full_code(symbol)
        rows = self.client.get_history_kline(code, start, end)
        return [
            Bar(code=code, date=row["time_key"][:10],
                open=row["open"], high=row["high"], low=row["low"],
                close=row["close"], volume=int(row["volume"]),
                turnover=row["turnover"])
            for row in rows
        ]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_base_adapter.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add touzi_agent/adapters/__init__.py touzi_agent/adapters/client.py \
        touzi_agent/adapters/base.py tests/conftest.py tests/test_base_adapter.py
git commit -m "feat: FutuClient protocol + base data adapter + test fixtures"
```

---

### Task 6: Per-market adapters (US / HK / CN code handling)

**Files:**
- Create: `touzi_agent/adapters/markets.py`
- Test: `tests/test_market_adapters.py`

**Interfaces:**
- Consumes: `BaseDataAdapter` (Task 5), `MarketConfig` (Task 2).
- Produces:
  - `USDataAdapter(config, client)` and `HKDataAdapter(config, client)` — inherit `BaseDataAdapter` unchanged (prefix join: `US.AAPL`, `HK.00700`).
  - `CNDataAdapter(config, client)` — overrides `full_code`: accepts `"600519.SH"`/`"000001.SZ"` and converts to 富途 form `"SH.600519"`/`"SZ.000001"`; raises `ValueError` on a symbol without a recognized `.SH`/`.SZ` suffix.
  - `build_adapter(config: MarketConfig, client) -> BaseDataAdapter` — factory returning the right subclass by `config.market`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_market_adapters.py
import pytest
from touzi_agent.models import MarketConfig
from touzi_agent.adapters.markets import (
    USDataAdapter, HKDataAdapter, CNDataAdapter, build_adapter,
)


def _cfg(market, prefix):
    return MarketConfig(market=market, currency="X", settlement="T+1",
                        short_selling="x", code_prefix=prefix,
                        daily_limit=None, costs={})


def test_us_full_code(fake_client):
    a = USDataAdapter(_cfg("US", "US"), fake_client)
    assert a.full_code("AAPL") == "US.AAPL"


def test_hk_full_code(fake_client):
    a = HKDataAdapter(_cfg("HK", "HK"), fake_client)
    assert a.full_code("00700") == "HK.00700"


def test_cn_full_code_converts_suffix(fake_client):
    a = CNDataAdapter(_cfg("CN", ""), fake_client)
    assert a.full_code("600519.SH") == "SH.600519"
    assert a.full_code("000001.SZ") == "SZ.000001"


def test_cn_full_code_rejects_bad_symbol(fake_client):
    a = CNDataAdapter(_cfg("CN", ""), fake_client)
    with pytest.raises(ValueError):
        a.full_code("600519")


def test_build_adapter_dispatches_by_market(fake_client):
    assert isinstance(build_adapter(_cfg("US", "US"), fake_client),
                      USDataAdapter)
    assert isinstance(build_adapter(_cfg("CN", ""), fake_client),
                      CNDataAdapter)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n touzi-agent pytest tests/test_market_adapters.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touzi_agent.adapters.markets'`.

- [ ] **Step 3: Write minimal implementation**

```python
# touzi_agent/adapters/markets.py
from touzi_agent.models import MarketConfig
from touzi_agent.adapters.base import BaseDataAdapter
from touzi_agent.adapters.client import FutuClient


class USDataAdapter(BaseDataAdapter):
    pass


class HKDataAdapter(BaseDataAdapter):
    pass


class CNDataAdapter(BaseDataAdapter):
    def full_code(self, symbol: str) -> str:
        if symbol.endswith(".SH"):
            return f"SH.{symbol[:-3]}"
        if symbol.endswith(".SZ"):
            return f"SZ.{symbol[:-3]}"
        raise ValueError(
            f"CN symbol must end with .SH or .SZ, got {symbol!r}")


_BY_MARKET = {"US": USDataAdapter, "HK": HKDataAdapter, "CN": CNDataAdapter}


def build_adapter(config: MarketConfig, client: FutuClient) -> BaseDataAdapter:
    cls = _BY_MARKET.get(config.market)
    if cls is None:
        raise ValueError(f"no adapter for market {config.market!r}")
    return cls(config, client)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_market_adapters.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add touzi_agent/adapters/markets.py tests/test_market_adapters.py
git commit -m "feat: US/HK/CN data adapters with market code handling"
```

---

### Task 7: Ingestion path (adapter → DB)

**Files:**
- Create: `touzi_agent/ingestion/__init__.py`
- Create: `touzi_agent/ingestion/ingest.py`
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: `BaseDataAdapter` (Task 5/6), `upsert_bars`/`get_bars`/`init_db` (Task 4).
- Produces:
  - `ingest_bars(adapter: BaseDataAdapter, conn, symbol: str, start: str, end: str) -> int` — fetches via the adapter, persists via `upsert_bars`, returns the number of bars written.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ingest.py
import sqlite3
import pytest
from touzi_agent.models import MarketConfig
from touzi_agent.data.db import init_db, get_bars
from touzi_agent.adapters.markets import USDataAdapter
from touzi_agent.ingestion.ingest import ingest_bars


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    yield c
    c.close()


def test_ingest_fetches_and_persists(conn, fake_client):
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None, costs={})
    adapter = USDataAdapter(cfg, fake_client)
    written = ingest_bars(adapter, conn, "AAPL", "2026-06-18", "2026-06-19")
    assert written == 2
    stored = get_bars(conn, "US.AAPL", "2026-06-18", "2026-06-19")
    assert [b.date for b in stored] == ["2026-06-18", "2026-06-19"]
    assert fake_client.calls == [("US.AAPL", "2026-06-18", "2026-06-19", "K_DAY")]


def test_ingest_is_idempotent(conn, fake_client):
    cfg = MarketConfig(market="US", currency="USD", settlement="T+0",
                       short_selling="allowed", code_prefix="US",
                       daily_limit=None, costs={})
    adapter = USDataAdapter(cfg, fake_client)
    ingest_bars(adapter, conn, "AAPL", "2026-06-18", "2026-06-19")
    ingest_bars(adapter, conn, "AAPL", "2026-06-18", "2026-06-19")
    stored = get_bars(conn, "US.AAPL", "2026-06-18", "2026-06-19")
    assert len(stored) == 2  # no duplicate rows
```

- [ ] **Step 2: Run test to verify it fails**

Run: `conda run -n touzi-agent pytest tests/test_ingest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touzi_agent.ingestion.ingest'`.

- [ ] **Step 3: Write minimal implementation**

```python
# touzi_agent/ingestion/__init__.py
```

```python
# touzi_agent/ingestion/ingest.py
import sqlite3

from touzi_agent.adapters.base import BaseDataAdapter
from touzi_agent.data.db import upsert_bars


def ingest_bars(adapter: BaseDataAdapter, conn: sqlite3.Connection,
                symbol: str, start: str, end: str) -> int:
    bars = adapter.fetch_bars(symbol, start, end)
    return upsert_bars(conn, bars)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `conda run -n touzi-agent pytest tests/test_ingest.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the full suite**

Run: `conda run -n touzi-agent pytest -v`
Expected: PASS (all tests across Tasks 1–7 green).

- [ ] **Step 6: Commit**

```bash
git add touzi_agent/ingestion tests/test_ingest.py
git commit -m "feat: ingestion path wiring adapter fetch to SQLite store"
```

---

## Plan Self-Review

**Spec coverage (Plan 1 scope = Foundations):**
- Project scaffold + toolchain (conda/pytest) → Task 1 ✅
- Domain models incl. market rule fields → Task 2 ✅
- Per-market config US/HK/CN with T+1, limits, costs, currency (spec §8.2/§8.3/§8.5) → Task 3 ✅
- Structured store for numbers only (spec §6.1) → Task 4 ✅
- 富途-backed data layer isolated behind a client protocol (Global Constraints) → Task 5 ✅
- US/HK/CN adapters incl. A-share code handling → Task 6 ✅
- Ingestion path → Task 7 ✅
- *Deferred to later plans (correctly out of scope):* quant engine/expectancy (Plan 2), validation/backtest (Plan 3), discovery loop (Plan 4), RAG/memory (Plan 5), behavioral guardrails (Plan 6), orchestration/execution/富途 trading (Plan 7).

**Placeholder scan:** No TBD/TODO; every code step shows complete code; every command shows expected output. ✅

**Type consistency:** `Bar`/`Instrument`/`MarketConfig` field names are identical across Tasks 2/4/5/6/7; `full_code`, `fetch_bars`, `get_history_kline`, `upsert_bars`, `ingest_bars` signatures match between producer and consumer tasks. ✅

**Note for the implementer:** Tasks 1–7 are sequential (each consumes the previous). `RealFutuClient` (Task 5) is the only component that touches live OpenD and is intentionally not unit-tested; verify it manually once OpenD is running before Plan 7.
