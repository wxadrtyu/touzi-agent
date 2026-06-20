# 股票投研 Agent 系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 V3.2 规格文档，实现一个支持美股 + A 股双市场的私人投资教练 Agent 系统，覆盖产业链筛选→公司初筛→深入研究→CoT 决策→交易执行→策略修正的完整闭环。

**Architecture:** 同心圆三层架构（Prompt/Context/Harness）+ L1-L7 数据层 + Market Adapter 双市场适配。4 个 Agent（研究/决策/操作分析/交易执行），五段式单次调用，CoT 自我辩论，3 道软警告 Guardrails，Point-in-Time 回测，4 级策略修正。

**Tech Stack:** Python 3.11+ / Claude 3.5 Sonnet API / Gemini Flash API / ChromaDB / SQLite / PyYAML / pytest / 富途 MCP

## 完成度追踪机制

每个 Task 标注完成度状态：

| 标记 | 含义 | 完成度 |
|---|---|---|
| ✅ | 已完成并通过测试 | 100% |
| 🔄 | 部分完成，剩余设为 TODO | 标注实际 % |
| ⏸️ | 因依赖未就绪暂停 | 0% (blocked) |
| ❌ | 无法实现，已记录替代方案 | 0% (abandoned) |

**整体完成度** = 已完成 Task 数 / 总 Task 数。每个 Task 内部的 Step 也有独立完成度。

## Global Constraints

- Python 3.11+
- Claude 3.5 Sonnet 作为主模型（Agent 1/2/3）
- Gemini 1.5 Flash 作为 Re-rank 模型
- ChromaDB 作为向量数据库
- SQLite 作为结构化数据库
- PyYAML 管理市场配置
- pytest 作为测试框架
- 所有文件 UTF-8 编码
- 中文注释，代码用英文命名
- Obsidian Vault 作为存储后端（Markdown + JSON）
- 美股优先实现，A 股配置先行但适配器可后补

## MVP 边界

| 模块 | MVP 范围 | 后续迭代 |
|---|---|---|
| Agent 1 研究分析 | ✅ 三层漏斗 + 五段式 | - |
| Agent 2 决策 | ✅ CoT 自我辩论 | - |
| Agent 3 操作分析 | ✅ 纪律评分 + 拒绝原因回写 | 季度策略审视 |
| Agent 4 交易执行 | ⏸️ 富途 MCP（依赖外部配置） | 富途就绪后接入 |
| Market Adapter | ✅ 美股完整 / A 股配置先行 | A 股数据适配器 |
| RAG | ✅ ChromaDB + 混合检索 | - |
| Guardrails | ✅ 3 道软警告 | - |
| 回测模式 | ✅ Point-in-Time + 事件驱动 | - |
| Web 控制台 | ❌ MVP 不做 | 后续迭代 |
| 策略修正 | ✅ 即时 + 操作后 + 回测 | 季度策略审视 |

---

## 文件结构

```
touzi-agent/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py              # 配置加载器
│   │   ├── market-us.yaml         # 美股市场配置
│   │   ├── market-cn.yaml         # A股市场配置
│   │   ├── evidence_weights.yaml  # 证据等级软引导（初版为空）
│   │   └── quant_config.yaml      # 量价过滤参数
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py              # L1-L7 数据模型（dataclass）
│   │   ├── vault.py               # Obsidian Vault 读写
│   │   ├── chroma_store.py        # ChromaDB 向量存储
│   │   └── sqlite_store.py        # SQLite 结构化存储
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                # 适配器基类
│   │   ├── data_us.py             # 美股数据适配器
│   │   ├── data_cn.py             # A股数据适配器（TODO: 接口先行）
│   │   ├── trading_us.py          # 美股交易适配器
│   │   └── trading_cn.py          # A股交易适配器
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # Agent 基类
│   │   ├── research_agent.py      # Agent 1: 漏斗式研究
│   │   ├── decision_agent.py      # Agent 2: CoT 自我辩论
│   │   ├── reflection_agent.py    # Agent 3: 操作分析
│   │   └── execute_agent.py       # Agent 4: 交易执行
│   ├── context/
│   │   ├── __init__.py
│   │   ├── rag.py                 # RAG 检索
│   │   ├── rerank.py              # Gemini Flash Re-rank
│   │   ├── assembler.py           # 上下文装配矩阵
│   │   └── feedback.py            # 快速反馈循环
│   ├── harness/
│   │   ├── __init__.py
│   │   ├── guardrails.py          # 3 道软警告
│   │   ├── consensus.py           # 共识门禁
│   │   ├── workflow.py            # 快循环/慢循环工作流
│   │   └── backtest.py            # 回测模式
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── claude.py              # Claude API 封装
│   │   └── gemini.py              # Gemini API 封装
│   └── main.py                    # 入口
├── tests/
│   ├── __init__.py
│   ├── test_data_models.py
│   ├── test_vault.py
│   ├── test_chroma_store.py
│   ├── test_adapters.py
│   ├── test_research_agent.py
│   ├── test_decision_agent.py
│   ├── test_reflection_agent.py
│   ├── test_rag.py
│   ├── test_guardrails.py
│   ├── test_consensus.py
│   ├── test_backtest.py
│   └── test_workflow.py
├── vault/                         # Obsidian Vault（运行时生成）
├── pyproject.toml
├── pytest.ini
└── .env.example
```

---

## Task 1: 项目初始化与依赖管理

**Files:**
- Create: `pyproject.toml`
- Create: `pytest.ini`
- Create: `.env.example`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: 项目基础结构，后续 Task 依赖此结构

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "touzi-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.39.0",
    "google-generativeai>=0.8.0",
    "chromadb>=0.5.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: 创建 pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

- [ ] **Step 3: 创建 .env.example**

```env
# Claude API
ANTHROPIC_API_KEY=your_claude_api_key

# Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# 富途 MCP（可选，MVP 阶段可不配）
FUTU_API_HOST=127.0.0.1
FUTU_API_PORT=33333

# Vault 路径
VAULT_PATH=./vault
```

- [ ] **Step 4: 创建包初始化文件**

创建 `src/__init__.py` 和 `tests/__init__.py`（空文件）。

- [ ] **Step 5: 安装依赖并验证**

Run: `pip install -e ".[dev]"`
Expected: 安装成功，无报错

- [ ] **Step 6: 运行 pytest 验证空测试通过**

Run: `pytest`
Expected: `no tests ran` （无报错）

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml pytest.ini .env.example src/__init__.py tests/__init__.py
git commit -m "chore: project initialization with dependencies"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 2: L1-L7 数据模型

**Files:**
- Create: `src/data/models.py`
- Test: `tests/test_data_models.py`

**Interfaces:**
- Produces: `L1Raw`, `L2Fact`, `L3Profile`, `L4Relation`, `L5Judgment`, `L6Alert`, `L7Action` 数据类
- Produces: `EvidenceLevel` 枚举 (A/B/C/D)
- Produces: `Market` 枚举 (US/CN)

- [ ] **Step 1: 写失败测试 — 证据等级枚举**

```python
# tests/test_data_models.py
from src.data.models import EvidenceLevel, Market

def test_evidence_level_values():
    assert EvidenceLevel.A.value == "A"
    assert EvidenceLevel.B.value == "B"
    assert EvidenceLevel.C.value == "C"
    assert EvidenceLevel.D.value == "D"

def test_market_values():
    assert Market.US.value == "US"
    assert Market.CN.value == "CN"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_data_models.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: 实现枚举**

```python
# src/data/models.py
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class EvidenceLevel(str, Enum):
    A = "A"  # 公告/年报
    B = "B"  # 调研/管理层交流
    C = "C"  # 研报/媒体
    D = "D"  # 社交媒体


class Market(str, Enum):
    US = "US"
    CN = "CN"


class ConsensusLevel(str, Enum):
    HIGH = "🟢"        # 高共识
    CONDITIONAL = "🟡"  # 有条件共识
    DISPUTED = "🟠"     # 存在争议
    BLOCKED = "🔴"      # 强烈反对


class ActionType(str, Enum):
    BUY = "买入"
    ADD = "加仓"
    REDUCE = "减仓"
    SELL = "清仓"
    HOLD = "HOLD"
```

- [ ] **Step 4: 写失败测试 — L2Fact 数据类**

```python
# tests/test_data_models.py (追加)
from src.data.models import L2Fact, EvidenceLevel, Market
from datetime import date

def test_l2fact_creation():
    fact = L2Fact(
        id="AAPL-2025Q4-revenue",
        ticker="AAPL",
        content="2025Q4 营收 50.2 亿美元，同比 +18.3%",
        evidence_level=EvidenceLevel.A,
        source_anchor="[2025年报#P12]",
        fact_date=date(2026, 2, 15),
        market=Market.US,
    )
    assert fact.ticker == "AAPL"
    assert fact.evidence_level == EvidenceLevel.A
    assert fact.market == Market.US
```

- [ ] **Step 5: 运行测试验证失败**

Run: `pytest tests/test_data_models.py::test_l2fact_creation -v`
Expected: FAIL with `AttributeError`

- [ ] **Step 6: 实现 L1-L7 数据类**

```python
# src/data/models.py (追加)

@dataclass
class L1Raw:
    """L1 原始痕迹层"""
    id: str
    ticker: str
    content: str  # 原始文本
    source: str   # 来源文件路径
    raw_date: date
    market: Market
    doc_type: str = ""  # annual_report / quarterly_report / news / etc.


@dataclass
class L2Fact:
    """L2 原子事实层"""
    id: str
    ticker: str
    content: str  # 标准化事实描述
    evidence_level: EvidenceLevel
    source_anchor: str  # 溯源锚点，如 [2025年报#P12]
    fact_date: date
    market: Market
    tags: list[str] = field(default_factory=list)


@dataclass
class L3Profile:
    """L3 认知画像层"""
    id: str
    profile_type: str  # sicong / buffett / druckenmiller / serenity / justin_sun / market_us / market_cn
    content: str  # Markdown 内容
    blind_spots: list[str] = field(default_factory=list)  # 盲区清单
    market: Optional[Market] = None


@dataclass
class L4Relation:
    """L4 关联网络层"""
    id: str
    relation_type: str  # macro_multiplier / supply_chain / bottleneck_map
    source_entity: str
    target_entity: str
    weight: float = 1.0
    description: str = ""
    market: Optional[Market] = None


@dataclass
class L5Judgment:
    """L5 心智与价值判断层"""
    id: str
    ticker: str
    market: Market
    # 底层逻辑三问
    logic_3q: dict[str, str]  # {"demand_real": "...", "bottleneck": "...", "stock_mapping": "..."}
    # 产业链定位 C0-C4
    c0_c4_position: dict[str, str]  # {"C0": "...", "C1": "...", ...}
    bottleneck_link: str  # 卡点环节
    # 估值
    dcf_pessimistic: float = 0.0
    dcf_neutral: float = 0.0
    dcf_optimistic: float = 0.0
    current_price: float = 0.0
    safety_margin: float = 0.0
    # 投资建议
    recommendation: str = ""  # 重点建议 / 观察建议 / 暂不适合
    suggested_action: str = ""  # 买入/加仓/减仓/清仓/HOLD
    position_size: float = 0.0  # 建议仓位 %
    stop_loss: float = 0.0
    take_profit: float = 0.0
    # 假设
    assumptions: list[str] = field(default_factory=list)
    # 跟踪表
    tracking_table: list[dict] = field(default_factory=list)


@dataclass
class L6Alert:
    """L6 监控与规则触发层"""
    id: str
    ticker: str
    market: Market
    alert_type: str  # price_threshold / assumption_break / valuation_drift
    threshold: float
    current_value: float
    is_triggered: bool = False
    description: str = ""


@dataclass
class L7Action:
    """L7 行动与交易历史层"""
    id: str
    ticker: str
    market: Market
    action_type: ActionType
    price: float
    quantity: int
    position_pct: float
    consensus_level: ConsensusLevel
    action_date: date
    # 拒绝记录
    is_rejected: bool = False
    rejection_reason: str = ""
    # 纪律评分
    discipline_score: int = 0
    # 复盘
    review_date: Optional[date] = None
    review_result: str = ""
    lessons_learned: str = ""
```

- [ ] **Step 7: 运行全部测试验证通过**

Run: `pytest tests/test_data_models.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/data/models.py tests/test_data_models.py
git commit -m "feat: L1-L7 data models with evidence levels and market support"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 3: 市场配置加载器

**Files:**
- Create: `src/config/market-us.yaml`
- Create: `src/config/market-cn.yaml`
- Create: `src/config/evidence_weights.yaml`
- Create: `src/config/loader.py`
- Test: `tests/test_config_loader.py`

**Interfaces:**
- Produces: `MarketConfig` 数据类，`load_market_config(market: Market) -> MarketConfig`
- Consumes: `Market` 枚举 from Task 2

- [ ] **Step 1: 创建美股配置文件**

```yaml
# src/config/market-us.yaml
market: US
accounting_standard: US_GAAP
currency: USD
settlement: T+0
daily_limit: none
short_selling: allowed
valuation_preference:
  primary: DCF
  secondary: PEG
  policy_premium: low
key_metrics: [EPS, FCF, Revenue_Growth, PEG, P_E]
data_sources:
  filings: SEC_EDGAR
  market_data: Yahoo_Finance
  holdings: 13F
  earnings_call: Seeking_Alpha
special_rules: []
narrative_leaders:
  - name: "黄仁勋"
    alias: ["老黄", "Jensen"]
    narrative: "AI算力/GPU/芯片"
  - name: "孙宇晨"
    alias: ["孙哥", "Justin Sun"]
    narrative: "加密货币/叙事炒作"
  - name: "特朗普"
    alias: ["Trump"]
    narrative: "政策/宏观/地缘政治"
```

- [ ] **Step 2: 创建 A 股配置文件**

```yaml
# src/config/market-cn.yaml
market: CN
accounting_standard: China_ASBE
currency: CNY
settlement: T+1
daily_limit:
  main_board: 0.10
  star_board: 0.20
  chinext: 0.20
short_selling: restricted
valuation_preference:
  primary: PE_Band
  secondary: PB_Band
  policy_premium: high
key_metrics: [营收增速, 净利润, ROE, 毛利率, 北向资金, 融资融券]
data_sources:
  filings: CNINFO
  market_data: EastMoney
  holdings: Northbound_Capital
  earnings_call: 调研纪要
special_rules:
  - 涨停板策略: 连板股特殊处理
  - 龙虎榜: 机构席位追踪
  - 北向资金: 外资流向监控
  - 限售解禁: 解禁日期预警
  - T1卖出限制: 当日买入不可卖出
narrative_leaders:
  - name: "黄仁勋"
    alias: ["老黄", "Jensen"]
    narrative: "AI算力/GPU/芯片"
  - name: "孙宇晨"
    alias: ["孙哥", "Justin Sun"]
    narrative: "加密货币/叙事炒作"
  - name: "特朗普"
    alias: ["Trump"]
    narrative: "政策/宏观/地缘政治"
```

- [ ] **Step 3: 创建证据等级配置（初版为空）**

```yaml
# src/config/evidence_weights.yaml
enabled: false
# 后期可启用软引导：
# enabled: true
# guidance:
#   A: "核心证据，通常占判断权重 60-80%"
#   B: "辅助证据，通常占 15-30%"
#   C: "参考信息，通常占 5-15%"
#   D: "仅线索，不参与权重计算"
```

- [ ] **Step 4: 写失败测试 — 配置加载**

```python
# tests/test_config_loader.py
from src.config.loader import load_market_config
from src.data.models import Market

def test_load_us_config():
    config = load_market_config(Market.US)
    assert config.market == "US"
    assert config.settlement == "T+0"
    assert config.daily_limit is None  # none → None
    assert config.valuation_preference["primary"] == "DCF"
    assert len(config.narrative_leaders) == 3

def test_load_cn_config():
    config = load_market_config(Market.CN)
    assert config.market == "CN"
    assert config.settlement == "T+1"
    assert config.daily_limit["main_board"] == 0.10
    assert config.valuation_preference["primary"] == "PE_Band"

def test_narrative_leaders_loaded():
    config = load_market_config(Market.US)
    names = [nl["name"] for nl in config.narrative_leaders]
    assert "黄仁勋" in names
    assert "孙宇晨" in names
    assert "特朗普" in names
```

- [ ] **Step 5: 运行测试验证失败**

Run: `pytest tests/test_config_loader.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 6: 实现配置加载器**

```python
# src/config/loader.py
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import yaml
from src.data.models import Market


@dataclass
class NarrativeLeader:
    name: str
    alias: list[str]
    narrative: str


@dataclass
class MarketConfig:
    market: str
    accounting_standard: str
    currency: str
    settlement: str
    daily_limit: Optional[dict[str, float] | float]
    short_selling: str
    valuation_preference: dict[str, Any]
    key_metrics: list[str]
    data_sources: dict[str, str]
    special_rules: list[Any]
    narrative_leaders: list[dict[str, Any]]

    @property
    def narrative_leader_names(self) -> list[str]:
        return [nl["name"] for nl in self.narrative_leaders]


def load_market_config(market: Market) -> MarketConfig:
    config_dir = Path(__file__).parent
    filename = f"market-{market.value.lower()}.yaml"
    filepath = config_dir / filename

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # daily_limit: "none" → None
    daily_limit = data.get("daily_limit")
    if daily_limit == "none":
        daily_limit = None

    return MarketConfig(
        market=data["market"],
        accounting_standard=data["accounting_standard"],
        currency=data["currency"],
        settlement=data["settlement"],
        daily_limit=daily_limit,
        short_selling=data["short_selling"],
        valuation_preference=data["valuation_preference"],
        key_metrics=data["key_metrics"],
        data_sources=data["data_sources"],
        special_rules=data.get("special_rules", []),
        narrative_leaders=data.get("narrative_leaders", []),
    )


def load_evidence_weights() -> dict:
    config_dir = Path(__file__).parent
    filepath = config_dir / "evidence_weights.yaml"
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

- [ ] **Step 7: 运行测试验证通过**

Run: `pytest tests/test_config_loader.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/config/ tests/test_config_loader.py
git commit -m "feat: market config loader with US and CN configs"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 4: Obsidian Vault 读写层

**Files:**
- Create: `src/data/vault.py`
- Test: `tests/test_vault.py`

**Interfaces:**
- Produces: `VaultStore` 类，方法: `save_l2fact()`, `load_l2facts()`, `save_l5()`, `load_l5()`, `save_l7()`, `load_l7()`, `save_profile()`, `load_profile()`
- Consumes: L1-L7 数据类 from Task 2

- [ ] **Step 1: 写失败测试 — Vault 基本读写**

```python
# tests/test_vault.py
import pytest
from pathlib import Path
from src.data.vault import VaultStore
from src.data.models import L2Fact, EvidenceLevel, Market
from datetime import date

@pytest.fixture
def vault(tmp_path):
    store = VaultStore(tmp_path)
    store.init_vault()
    return store

def test_save_and_load_l2fact(vault):
    fact = L2Fact(
        id="AAPL-2025Q4-revenue",
        ticker="AAPL",
        content="2025Q4 营收 50.2 亿美元",
        evidence_level=EvidenceLevel.A,
        source_anchor="[2025年报#P12]",
        fact_date=date(2026, 2, 15),
        market=Market.US,
    )
    vault.save_l2fact(fact)
    facts = vault.load_l2facts("AAPL")
    assert len(facts) == 1
    assert facts[0].ticker == "AAPL"
    assert facts[0].evidence_level == EvidenceLevel.A

def test_vault_init_creates_dirs(vault, tmp_path):
    assert (tmp_path / "Stage_A_Watchlist").exists()
    assert (tmp_path / "L7_trade_log").exists()
    assert (tmp_path / "L3-profile").exists()
    assert (tmp_path / "_inbox").exists()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_vault.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 VaultStore**

```python
# src/data/vault.py
import json
from datetime import date
from pathlib import Path
from dataclasses import asdict
from typing import Optional
from src.data.models import (
    L1Raw, L2Fact, L3Profile, L4Relation,
    L5Judgment, L6Alert, L7Action,
    EvidenceLevel, Market, ConsensusLevel, ActionType,
)


class VaultStore:
    """Obsidian Vault 读写层"""

    def __init__(self, vault_path: Path | str):
        self.vault_path = Path(vault_path)

    def init_vault(self):
        """初始化 Vault 目录结构"""
        dirs = [
            "config",
            "L3-profile",
            "_inbox",
            "Stage_C_Market",
            "Stage_B_Sectors",
            "Stage_A_Watchlist",
            "L7_trade_log",
            "proposals",
            "archive",
        ]
        for d in dirs:
            (self.vault_path / d).mkdir(parents=True, exist_ok=True)

    def _ticker_dir(self, ticker: str, market: Market) -> Path:
        """获取标的目录"""
        d = self.vault_path / "Stage_A_Watchlist" / ticker
        (d / "L1_raw").mkdir(parents=True, exist_ok=True)
        (d / "L2_facts").mkdir(parents=True, exist_ok=True)
        return d

    # --- L2 Facts ---

    def save_l2fact(self, fact: L2Fact):
        """保存 L2 事实到 JSON"""
        d = self._ticker_dir(fact.ticker, fact.market)
        filepath = d / "L2_facts" / f"{fact.id}.json"
        data = asdict(fact)
        data["evidence_level"] = fact.evidence_level.value
        data["market"] = fact.market.value
        data["fact_date"] = fact.fact_date.isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_l2facts(self, ticker: str) -> list[L2Fact]:
        """加载某标的的全部 L2 事实"""
        facts = []
        # 搜索所有 market 的目录
        for market in [Market.US, Market.CN]:
            d = self.vault_path / "Stage_A_Watchlist" / ticker / "L2_facts"
            if not d.exists():
                continue
            for filepath in d.glob("*.json"):
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["evidence_level"] = EvidenceLevel(data["evidence_level"])
                data["market"] = Market(data["market"])
                data["fact_date"] = date.fromisoformat(data["fact_date"])
                facts.append(L2Fact(**data))
        return facts

    # --- L5 Judgment ---

    def save_l5(self, judgment: L5Judgment):
        """保存 L5 判断为 Markdown"""
        d = self._ticker_dir(judgment.ticker, judgment.market)
        filepath = d / "L5_valuation.md"
        # 转换为 Markdown 格式
        md = self._l5_to_markdown(judgment)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

    def load_l5(self, ticker: str, market: Market) -> Optional[L5Judgment]:
        """加载 L5 判断（从 Markdown 解析）"""
        filepath = self.vault_path / "Stage_A_Watchlist" / ticker / "L5_valuation.md"
        if not filepath.exists():
            return None
        # MVP: 简化版，只读取原始 Markdown，完整解析后续实现
        content = filepath.read_text(encoding="utf-8")
        # TODO: 完整的 Markdown → L5Judgment 解析
        return None  # 🔄 50% — 保存完整，解析待实现

    def _l5_to_markdown(self, j: L5Judgment) -> str:
        """L5Judgment → Markdown"""
        md = f"# L5_valuation: {j.ticker}\n\n"
        md += "## 底层逻辑三问\n"
        for q, a in j.logic_3q.items():
            md += f"- {q}: {a}\n"
        md += f"\n## 产业链定位（C0-C4）\n"
        for link, desc in j.c0_c4_position.items():
            md += f"- {link}: {desc}\n"
        md += f"- 卡点环节: {j.bottleneck_link}\n"
        md += f"\n## 估值\n"
        md += f"- 悲观 DCF: ${j.dcf_pessimistic}\n"
        md += f"- 中性 DCF: ${j.dcf_neutral}\n"
        md += f"- 乐观 DCF: ${j.dcf_optimistic}\n"
        md += f"- 当前价格: ${j.current_price}\n"
        md += f"- 安全边际: {j.safety_margin:.1%}\n"
        md += f"\n## 投资建议\n"
        md += f"- 分类: {j.recommendation}\n"
        md += f"- 建议操作: {j.suggested_action}\n"
        md += f"- 建议仓位: {j.position_size}%\n"
        md += f"- 止损线: ${j.stop_loss}\n"
        md += f"- 止盈线: ${j.take_profit}\n"
        return md

    # --- L7 Action ---

    def save_l7(self, action: L7Action):
        """保存 L7 操作记录"""
        d = self.vault_path / "L7_trade_log"
        d.mkdir(parents=True, exist_ok=True)
        filepath = d / f"{action.id}.md"
        md = self._l7_to_markdown(action)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

    def load_l7_by_ticker(self, ticker: str) -> list[L7Action]:
        """加载某标的的全部操作记录"""
        d = self.vault_path / "L7_trade_log"
        if not d.exists():
            return []
        # MVP: 返回文件名列表，完整解析后续实现
        return []  # 🔄 30% — 保存完整，按标的检索待实现

    def _l7_to_markdown(self, a: L7Action) -> str:
        """L7Action → Markdown"""
        md = f"# 操作记录 {a.id}\n\n"
        md += "## 基本信息\n"
        md += f"- 操作类型: {a.action_type.value}\n"
        md += f"- 标的: {a.ticker}  价格: ${a.price}  数量: {a.quantity}股\n"
        md += f"- 仓位占比: {a.position_pct}%\n"
        md += f"- 共识等级: {a.consensus_level.value}\n"
        md += f"- market: {a.market.value}\n"
        if a.is_rejected:
            md += f"\n## 拒绝原因记录\n"
            md += f"- 日期: {a.action_date}\n"
            md += f"- 拒绝原因: {a.rejection_reason}\n"
        md += f"\n## 纪律评分: {a.discipline_score}\n"
        return md

    # --- L3 Profile ---

    def save_profile(self, profile: L3Profile):
        """保存 L3 画像"""
        d = self.vault_path / "L3-profile"
        d.mkdir(parents=True, exist_ok=True)
        filepath = d / f"{profile.id}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(profile.content)

    def load_profile(self, profile_id: str) -> Optional[L3Profile]:
        """加载 L3 画像"""
        filepath = self.vault_path / "L3-profile" / f"{profile_id}.md"
        if not filepath.exists():
            return None
        content = filepath.read_text(encoding="utf-8")
        return L3Profile(id=profile_id, profile_type=profile_id, content=content)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_vault.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/vault.py tests/test_vault.py
git commit -m "feat: Obsidian Vault read/write layer for L2/L5/L7"
```

**完成度: ⏸️ 0% (待执行)**
**注意**: L5/L7 的 Markdown→对象解析为 🔄 50%，保存功能完整，解析功能后续迭代补全。

---

## Task 5: LLM API 封装

**Files:**
- Create: `src/llm/claude.py`
- Create: `src/llm/gemini.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Produces: `ClaudeClient` 类，方法: `chat(prompt, system_prompt=None) -> str`
- Produces: `GeminiClient` 类，方法: `rerank(query, documents, top_k=10) -> list[dict]`

- [ ] **Step 1: 写失败测试 — Claude 客户端（mock）**

```python
# tests/test_llm.py
import pytest
from unittest.mock import patch, MagicMock
from src.llm.claude import ClaudeClient

def test_claude_client_initialization():
    client = ClaudeClient(api_key="test-key")
    assert client.model == "claude-3-5-sonnet-20241022"

@patch("src.llm.claude.anthropic.Anthropic")
def test_claude_chat(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="测试回复")]
    mock_client.messages.create.return_value = mock_response

    client = ClaudeClient(api_key="test-key")
    result = client.chat("你好", system_prompt="你是助手")
    assert result == "测试回复"
    mock_client.messages.create.assert_called_once()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 Claude 客户端**

```python
# src/llm/claude.py
import anthropic
from typing import Optional


class ClaudeClient:
    """Claude 3.5 Sonnet API 封装"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ) -> str:
        """发送消息并获取回复"""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text
```

- [ ] **Step 4: 实现 Gemini 客户端（Re-rank 用）**

```python
# src/llm/gemini.py
import google.generativeai as genai
from typing import Optional


class GeminiClient:
    """Gemini 1.5 Flash API 封装（用于 Re-rank）"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 10,
    ) -> list[dict]:
        """对文档列表进行 Re-rank，返回评分排序后的结果"""
        # 构造 Re-rank Prompt
        docs_text = "\n".join(
            f"[{i}] {doc[:200]}..." for i, doc in enumerate(documents)
        )
        prompt = f"""请对以下文档按与查询的相关性评分（0-10分）。

查询: {query}

文档:
{docs_text}

请输出 JSON 数组，每个元素包含 index 和 score:
[{{"index": 0, "score": 8.5}}, ...]

只输出 JSON，不要其他文字。"""

        response = self.model.generate_content(prompt)
        # 解析 JSON 响应
        import json
        try:
            # 清理可能的 markdown 代码块标记
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            scores = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            # 解析失败时返回原始顺序
            scores = [{"index": i, "score": 5.0} for i in range(len(documents))]

        # 按分数排序，取 top_k
        scores.sort(key=lambda x: x["score"], reverse=True)
        results = []
        for item in scores[:top_k]:
            idx = item["index"]
            if 0 <= idx < len(documents):
                results.append({
                    "document": documents[idx],
                    "score": item["score"],
                    "index": idx,
                })
        return results

    def chat(
        self,
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ) -> str:
        """简单对话接口"""
        response = self.model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        return response.text
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_llm.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/llm/ tests/test_llm.py
git commit -m "feat: Claude and Gemini API wrappers"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 6: ChromaDB 向量存储

**Files:**
- Create: `src/data/chroma_store.py`
- Test: `tests/test_chroma_store.py`

**Interfaces:**
- Produces: `ChromaStore` 类，方法: `add_document()`, `search()`, `search_with_date_filter()`

- [ ] **Step 1: 写失败测试 — 向量存储基本操作**

```python
# tests/test_chroma_store.py
import pytest
from datetime import date
from src.data.chroma_store import ChromaStore

@pytest.fixture
def store(tmp_path):
    return ChromaStore(persist_path=str(tmp_path / "chroma"))

def test_add_and_search(store):
    store.add_document(
        id="doc1",
        content="苹果公司2025年Q4营收50亿美元，同比增长18%",
        metadata={"ticker": "AAPL", "date": "2026-02-15", "evidence_level": "A"},
    )
    store.add_document(
        id="doc2",
        content="英伟达GPU需求旺盛，数据中心业务增长",
        metadata={"ticker": "NVDA", "date": "2026-03-01", "evidence_level": "B"},
    )
    results = store.search("苹果营收", top_k=2)
    assert len(results) > 0
    assert results[0]["metadata"]["ticker"] == "AAPL"

def test_search_with_date_filter(store):
    store.add_document(
        id="doc1",
        content="旧文档",
        metadata={"ticker": "AAPL", "date": "2026-01-01", "evidence_level": "A"},
    )
    store.add_document(
        id="doc2",
        content="新文档",
        metadata={"ticker": "AAPL", "date": "2026-06-01", "evidence_level": "A"},
    )
    # 只搜索 2026-03-01 之前的
    results = store.search_with_date_filter(
        "文档", as_of_date="2026-03-01", top_k=10
    )
    assert len(results) == 1
    assert results[0]["id"] == "doc1"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_chroma_store.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ChromaStore**

```python
# src/data/chroma_store.py
import chromadb
from typing import Optional


class ChromaStore:
    """ChromaDB 向量存储"""

    def __init__(self, persist_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(
        self,
        id: str,
        content: str,
        metadata: dict,
    ):
        """添加文档到向量库"""
        self.collection.add(
            ids=[id],
            documents=[content],
            metadatas=[metadata],
        )

    def add_documents(
        self,
        ids: list[str],
        contents: list[str],
        metadatas: list[dict],
    ):
        """批量添加文档"""
        self.collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas,
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """向量检索"""
        kwargs = {
            "query_texts": [query],
            "n_results": top_k,
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        docs = []
        for i in range(len(results["ids"][0])):
            docs.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return docs

    def search_with_date_filter(
        self,
        query: str,
        as_of_date: str,
        top_k: int = 10,
        ticker: Optional[str] = None,
    ) -> list[dict]:
        """带日期过滤的检索（回测模式用）"""
        where = {"date": {"$lte": as_of_date}}
        if ticker:
            where["ticker"] = ticker
        return self.search(query, top_k=top_k, where=where)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_chroma_store.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/chroma_store.py tests/test_chroma_store.py
git commit -m "feat: ChromaDB vector store with date filtering"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 7: 数据适配器基类与美股适配器

**Files:**
- Create: `src/adapters/base.py`
- Create: `src/adapters/data_us.py`
- Create: `src/adapters/trading_us.py`
- Test: `tests/test_adapters.py`

**Interfaces:**
- Produces: `BaseDataAdapter`, `USDataAdapter`, `USTradingAdapter`
- Consumes: `MarketConfig` from Task 3

- [ ] **Step 1: 写失败测试 — 美股数据适配器**

```python
# tests/test_adapters.py
import pytest
from src.adapters.data_us import USDataAdapter
from src.adapters.trading_us import USTradingAdapter

def test_us_data_adapter_interface():
    adapter = USDataAdapter()
    assert hasattr(adapter, "fetch_filings")
    assert hasattr(adapter, "fetch_market_data")
    assert hasattr(adapter, "fetch_holdings")
    assert hasattr(adapter, "fetch_earnings_call")

def test_us_trading_adapter_t0():
    """美股 T+0，无涨跌停限制"""
    adapter = USTradingAdapter()
    # 美股不应有任何交易限制检查
    order = {"action": "SELL", "ticker": "AAPL", "quantity": 100}
    # should not raise
    check = adapter.pre_trade_check(order)
    assert check["allowed"] is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_adapters.py -v`
Expected: FAIL

- [ ] **Step 3: 实现适配器**

```python
# src/adapters/base.py
from abc import ABC, abstractmethod
from typing import Any


class BaseDataAdapter(ABC):
    """数据适配器基类"""

    @abstractmethod
    def fetch_filings(self, ticker: str) -> list[dict]:
        """获取公告/财报"""
        ...

    @abstractmethod
    def fetch_market_data(self, ticker: str) -> dict:
        """获取行情数据"""
        ...

    @abstractmethod
    def fetch_holdings(self, ticker: str) -> dict:
        """获取机构持仓"""
        ...

    @abstractmethod
    def fetch_earnings_call(self, ticker: str) -> str:
        """获取财报电话会纪要"""
        ...


class BaseTradingAdapter(ABC):
    """交易适配器基类"""

    @abstractmethod
    def pre_trade_check(self, order: dict) -> dict:
        """交易前规则检查"""
        ...

    @abstractmethod
    def execute(self, order: dict) -> dict:
        """执行交易"""
        ...
```

```python
# src/adapters/data_us.py
import httpx
from typing import Any
from src.adapters.base import BaseDataAdapter


class USDataAdapter(BaseDataAdapter):
    """美股数据适配器 — SEC EDGAR + Yahoo Finance"""

    SEC_EDGAR_BASE = "https://data.sec.gov"
    USER_AGENT = "touzi-agent research@example.com"

    def fetch_filings(self, ticker: str) -> list[dict]:
        """从 SEC EDGAR 获取财报"""
        # MVP: 通过 CIK 查询 10-K/10-Q
        # TODO: 实现 CIK 映射和 EDGAR API 调用
        # 🔄 30% — 接口定义完成，实际 API 调用待实现
        return []

    def fetch_market_data(self, ticker: str) -> dict:
        """从 Yahoo Finance 获取行情"""
        # TODO: 实现 Yahoo Finance API 调用
        # 🔄 30% — 接口定义完成，实际调用待实现
        return {"ticker": ticker, "price": 0.0, "volume": 0}

    def fetch_holdings(self, ticker: str) -> dict:
        """获取 13F 持仓"""
        # TODO: 实现 13F 查询
        # 🔄 30%
        return {}

    def fetch_earnings_call(self, ticker: str) -> str:
        """获取财报电话会纪要"""
        # TODO: 实现 Seeking Alpha / 官方 IR 获取
        # 🔄 30%
        return ""
```

```python
# src/adapters/trading_us.py
from src.adapters.base import BaseTradingAdapter


class USTradingAdapter(BaseTradingAdapter):
    """美股交易适配器 — T+0, 无涨跌停"""

    def pre_trade_check(self, order: dict) -> dict:
        """美股无特殊交易限制"""
        return {"allowed": True, "reason": ""}

    def execute(self, order: dict) -> dict:
        """通过富途 MCP 执行交易"""
        # TODO: 接入富途 MCP
        # ⏸️ 0% — 依赖富途 MCP 配置，MVP 阶段暂不接入
        return {
            "status": "not_implemented",
            "reason": "富途 MCP 尚未配置",
            "order": order,
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_adapters.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/ tests/test_adapters.py
git commit -m "feat: US data and trading adapters with base classes"
```

**完成度: ⏸️ 0% (待执行)**
**注意**: 数据适配器的实际 API 调用为 🔄 30%（接口完整，实际调用待实现）。交易适配器为 ⏸️ 0%（依赖富途 MCP）。

---

## Task 8: A 股数据/交易适配器（接口先行）

**Files:**
- Create: `src/adapters/data_cn.py`
- Create: `src/adapters/trading_cn.py`
- Test: `tests/test_adapters_cn.py`

- [ ] **Step 1: 写失败测试 — A 股交易规则**

```python
# tests/test_adapters_cn.py
import pytest
from src.adapters.trading_cn import CNTradingAdapter

def test_cn_t1_sell_restriction():
    """A 股 T+1：当日买入不可卖出"""
    adapter = CNTradingAdapter()
    adapter._t0_positions = {"AAPL": "2026-06-18"}  # 模拟当日买入
    order = {"action": "SELL", "ticker": "AAPL", "date": "2026-06-18"}
    check = adapter.pre_trade_check(order)
    assert check["allowed"] is False
    assert "T+1" in check["reason"]

def test_cn_daily_limit_check():
    """A 股涨跌停检查"""
    adapter = CNTradingAdapter()
    adapter._current_prices = {"600000": 11.0}
    adapter._prev_close = {"600000": 10.0}
    # 11.0 / 10.0 - 1 = 10%，达到主板涨停
    order = {"action": "BUY", "ticker": "600000", "board": "main_board"}
    check = adapter.pre_trade_check(order)
    assert check["allowed"] is False
    assert "涨跌停" in check["reason"]

def test_cn_normal_trade_allowed():
    """正常交易应允许"""
    adapter = CNTradingAdapter()
    adapter._current_prices = {"600000": 10.5}
    adapter._prev_close = {"600000": 10.0}
    order = {"action": "BUY", "ticker": "600000", "board": "main_board"}
    check = adapter.pre_trade_check(order)
    assert check["allowed"] is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_adapters_cn.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 A 股适配器**

```python
# src/adapters/data_cn.py
from src.adapters.base import BaseDataAdapter


class CNDataAdapter(BaseDataAdapter):
    """A 股数据适配器 — 巨潮/东方财富"""

    def fetch_filings(self, ticker: str) -> list[dict]:
        """从巨潮资讯网获取公告"""
        # TODO: 实现巨潮 API
        # 🔄 30% — 接口完整，实际调用待实现
        return []

    def fetch_market_data(self, ticker: str) -> dict:
        """从东方财富获取行情"""
        # TODO: 实现东方财富 API
        # 🔄 30%
        return {"ticker": ticker, "price": 0.0, "volume": 0}

    def fetch_holdings(self, ticker: str) -> dict:
        """获取北向资金/融资融券"""
        # TODO: 实现北向资金查询
        # 🔄 30%
        return {}

    def fetch_earnings_call(self, ticker: str) -> str:
        """获取调研纪要"""
        # TODO: 实现调研纪要获取
        # 🔄 30%
        return ""
```

```python
# src/adapters/trading_cn.py
from datetime import date
from src.adapters.base import BaseTradingAdapter


class CNTradingAdapter(BaseTradingAdapter):
    """A 股交易适配器 — T+1, 涨跌停"""

    def __init__(self):
        self._t0_positions: dict[str, str] = {}  # ticker -> 买入日期
        self._current_prices: dict[str, float] = {}
        self._prev_close: dict[str, float] = {}

    def pre_trade_check(self, order: dict) -> dict:
        """A 股交易前规则检查"""
        ticker = order["ticker"]
        action = order["action"]

        # T+1 检查：当日买入不可卖出
        if action == "SELL":
            buy_date = self._t0_positions.get(ticker)
            order_date = order.get("date", date.today().isoformat())
            if buy_date == order_date:
                return {
                    "allowed": False,
                    "reason": "A股T+1，当日买入不可卖出",
                }

        # 涨跌停检查
        board = order.get("board", "main_board")
        limits = {
            "main_board": 0.10,
            "star_board": 0.20,
            "chinext": 0.20,
        }
        limit_pct = limits.get(board, 0.10)

        current = self._current_prices.get(ticker, 0)
        prev = self._prev_close.get(ticker, 0)
        if prev > 0 and current > 0:
            change_pct = abs(current / prev - 1)
            if change_pct >= limit_pct:
                return {
                    "allowed": False,
                    "reason": f"已达{board}涨跌停板（±{limit_pct:.0%}），无法交易",
                }

        return {"allowed": True, "reason": ""}

    def execute(self, order: dict) -> dict:
        """通过富途 MCP 执行交易"""
        # TODO: 接入富途 MCP
        # ⏸️ 0% — 依赖富途 MCP 配置
        return {
            "status": "not_implemented",
            "reason": "富途 MCP 尚未配置",
            "order": order,
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_adapters_cn.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/data_cn.py src/adapters/trading_cn.py tests/test_adapters_cn.py
git commit -m "feat: CN data and trading adapters with T+1 and limit checks"
```

**完成度: ⏸️ 0% (待执行)**
**注意**: A 股交易规则检查 ✅ 100%（T+1 + 涨跌停），数据适配器 🔄 30%（接口完整，API 调用待实现）。

---

## Task 9: Agent 1 — 漏斗式研究 Agent

**Files:**
- Create: `src/agents/base.py`
- Create: `src/agents/research_agent.py`
- Test: `tests/test_research_agent.py`

**Interfaces:**
- Produces: `ResearchAgent` 类，方法: `screen_chains()`, `screen_companies()`, `deep_research()`
- Consumes: `ClaudeClient` from Task 5, `MarketConfig` from Task 3, `VaultStore` from Task 4

- [ ] **Step 1: 写失败测试 — 漏斗三层调用**

```python
# tests/test_research_agent.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.research_agent import ResearchAgent
from src.llm.claude import ClaudeClient
from src.config.loader import load_market_config
from src.data.models import Market

@pytest.fixture
def agent():
    claude = MagicMock(spec=ClaudeClient)
    config = load_market_config(Market.US)
    return ResearchAgent(claude_client=claude, market_config=config)

def test_screen_chains_returns_list(agent):
    agent.claude.chat.return_value = "1. AI算力产业链\n2. 新能源车产业链"
    chains = agent.screen_chains("当前市场分析")
    assert isinstance(chains, str)
    assert "AI算力" in chains

def test_screen_companies_returns_list(agent):
    agent.claude.chat.return_value = "| 公司 | 代码 | 产业链 |\n|---|---|---|\n| NVIDIA | NVDA | AI算力 |"
    companies = agent.screen_companies("AI算力产业链")
    assert "NVDA" in companies

def test_deep_research_returns_l5(agent):
    agent.claude.chat.return_value = "# L5_valuation: NVDA\n\n## 底层逻辑三问\n..."
    result = agent.deep_research("NVDA", screening_result="初筛通过", context_facts=[])
    assert "L5" in result or "NVDA" in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_research_agent.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 Agent 基类**

```python
# src/agents/base.py
from abc import ABC
from src.llm.claude import ClaudeClient
from src.config.loader import MarketConfig


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, claude_client: ClaudeClient, market_config: MarketConfig):
        self.claude = claude_client
        self.config = market_config
```

- [ ] **Step 4: 实现 ResearchAgent**

```python
# src/agents/research_agent.py
from src.agents.base import BaseAgent
from src.data.models import L2Fact, EvidenceLevel


class ResearchAgent(BaseAgent):
    """Agent 1: 漏斗式研究 Agent

    三层漏斗：
    1. 产业链筛选（C0-C4，不分析具体公司）
    2. 公司初筛（在产业链内找候选公司）
    3. 深入研究（五段式，仅对重点线索公司）
    """

    def screen_chains(self, market_context: str) -> str:
        """第一层：产业链筛选"""
        prompt = f"""你是一个投资研究 Agent。当前分析的市场是：{self.config.market}

## 市场规则
- 交易制度：{self.config.settlement}
- 会计准则：{self.config.accounting_standard}
- 估值偏好：{self.config.valuation_preference}

## 已知信息
{market_context}

请按 C0-C4 框架筛选当前有潜力的产业链/赛道：

- C0 终端需求：哪些赛道的需求真实且持续 1-3 年？
- C1 系统集成：哪些环节认证壁垒高、集成难度大？
- C2 核心部件：哪些部件存在良率/产能瓶颈？
- C3 材料工艺：哪些材料扩产困难、设备有约束？
- C4 上游资源：哪些资源供给紧张？

输出 10-20 个有潜力的产业链/赛道，不分析具体公司。"""

        return self.claude.chat(prompt)

    def screen_companies(self, promising_chains: str) -> str:
        """第二层：公司初筛"""
        prompt = f"""基于以下有潜力的产业链，筛选候选公司：

## 有潜力的产业链
{promising_chains}

请对每个产业链：
1. 找出对应的候选公司
2. 检查近 4 季度主营业务是否与卡点相关
3. 检查收入占比、毛利率、订单、产能是否有公开披露
4. 标注初步证据等级（A=公告/B=调研/C=研报/D=社交媒体）

输出表格：公司|代码|对应产业链|对应环节|业务纯度|公开证据|证据等级|初步归类（重点线索/观察线索/暂不适合）"""

        return self.claude.chat(prompt)

    def deep_research(
        self,
        ticker: str,
        screening_result: str,
        context_facts: list[L2Fact],
    ) -> str:
        """第三层：深入研究（五段式，单次调用）"""
        # 构造带证据等级的 Context
        facts_text = self._format_facts(context_facts)
        narrative_leaders = self._format_narrative_leaders()

        prompt = f"""你对以下公司进行深入研究：{ticker}

## 公司初筛信息
{screening_result}

## 已知事实（标注证据等级）
{facts_text}

## 叙事领袖清单
{narrative_leaders}

请按以下五段式流程分析，在一个回答中完成全部五段：

### 第一段：产业链定位（C0-C4）
- 该公司在产业链中的定位
- 卡点环节确认
- 底层逻辑三问：需求是否真实？瓶颈在哪里？股票映射是否有证据？

### 第二段：证据复筛
- 逐条验证初筛阶段的证据
- 补充遗漏的证据
- 标注证据等级（A=公告/B=调研/C=研报/D=社交媒体）

### 第三段：红队证伪
- 大客户是否可能自研/二供/三供？
- 12-18 个月内是否可能被新技术替代？
- 同行是否可能打价格战？
- 收入是否真的来自卡点而非边缘业务？
- 当前市场是否已充分定价？

### 第四段：防幻觉检查
- 拎出可能夸大的结论
- 给出谨慎表达方式

### 第五段：综合判断
- DCF 估值（悲观/中性/乐观）
- 投资建议分类：重点建议 / 观察建议 / 暂不适合
- 买入假设与建仓方案
- 未来两季度跟踪表

## 证据等级说明
- A级 = 公告/年报（核心证据，可直接作结论）
- B级 = 调研/管理层交流（辅助判断，需交叉验证）
- C级 = 研报/媒体（仅参考，需 A/B 级支撑）
- D级 = 社交媒体（仅线索，不能作结论。叙事领袖除外）

请在分析时自然地给高等级证据更多权重。
D 级证据只能作为线索启发，不能作为结论依据。"""

        return self.claude.chat(prompt, max_tokens=8192)

    def _format_facts(self, facts: list[L2Fact]) -> str:
        """格式化事实列表为带证据等级的文本"""
        if not facts:
            return "（暂无已知事实）"
        lines = []
        for f in facts:
            lines.append(
                f"- ({f.evidence_level.value}级, {f.fact_date}) {f.content} <- {f.source_anchor}"
            )
        return "\n".join(lines)

    def _format_narrative_leaders(self) -> str:
        """格式化叙事领袖清单"""
        if not self.config.narrative_leaders:
            return "（无）"
        lines = []
        for nl in self.config.narrative_leaders:
            lines.append(f"- {nl['name']}（{'/'.join(nl['alias'])}）: {nl['narrative']}")
        return "\n".join(lines)
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest tests/test_research_agent.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/agents/base.py src/agents/research_agent.py tests/test_research_agent.py
git commit -m "feat: Agent 1 funnel research with 3-layer screening"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 10: Agent 2 — CoT 自我辩论决策 Agent

**Files:**
- Create: `src/agents/decision_agent.py`
- Test: `tests/test_decision_agent.py`

**Interfaces:**
- Produces: `DecisionAgent` 类，方法: `decide(l5_draft, sicong_profile, rejection_reasons) -> dict`
- 返回: `{"consensus_level": ConsensusLevel, "action": str, "position_adjustment": str, ...}`

- [ ] **Step 1: 写失败测试 — CoT 决策**

```python
# tests/test_decision_agent.py
import pytest
from unittest.mock import MagicMock
from src.agents.decision_agent import DecisionAgent
from src.llm.claude import ClaudeClient
from src.config.loader import load_market_config
from src.data.models import Market, ConsensusLevel

@pytest.fixture
def agent():
    claude = MagicMock(spec=ClaudeClient)
    config = load_market_config(Market.US)
    return DecisionAgent(claude_client=claude, market_config=config)

def test_decide_returns_dict(agent):
    agent.claude.chat.return_value = """## 共识等级: 🟢 高共识
## 最终建议: 买入
## 仓位: 8%
## 附加条件: 无
## 风险提示: 注意 Q3 财报"""
    result = agent.decide(
        l5_draft="L5 草案内容",
        sicong_profile="Sicong 画像",
        rejection_reasons="无历史拒绝",
    )
    assert "consensus_level" in result
    assert "action" in result

def test_decide_parses_consensus(agent):
    agent.claude.chat.return_value = """## 共识等级: 🟡 有条件共识
## 最终建议: 买入
## 仓位: 5%"""
    result = agent.decide("draft", "profile", "")
    assert "🟡" in result["consensus_level"] or "有条件" in result["consensus_level"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_decision_agent.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 DecisionAgent**

```python
# src/agents/decision_agent.py
import re
from src.agents.base import BaseAgent


class DecisionAgent(BaseAgent):
    """Agent 2: CoT 自我辩论决策 Agent

    单次调用完成：正方论证 → 反方反驳 → 综合判断
    """

    def decide(
        self,
        l5_draft: str,
        sicong_profile: str,
        rejection_reasons: str,
    ) -> dict:
        """CoT 自我辩论，输出投资建议 + 共识等级"""
        prompt = f"""你是一个投资决策 Agent。你需要对以下研究草案进行自我辩论，最终给出投资建议。

## 研究草案（Agent 1 产出）
{l5_draft}

## Sicong 个人画像
{sicong_profile}

## 历史拒绝原因（快速反馈循环）
{rejection_reasons}

## 叙事领袖清单
{self._format_narrative_leaders()}

请按以下三步进行自我辩论：

### 第一步：正方论证（IA#1 视角）
假设你是主提案方，论证为什么 Sicong 应该执行这个建议：
- 投资逻辑是否成立？
- 估值是否有安全边际？
- 时机是否合适？
- 与 Sicong 画像是否匹配？

### 第二步：反方反驳（IA#2 视角）
假设你是魔鬼代言人，逐条审查正方论证的漏洞：
- 假设是否成立？有没有忽略的风险？
- 白毛股神视角：这家公司真的是卡脖子件吗？
- 孙宇晨视角：这是叙事泡沫还是真实基本面驱动？
- 是否与 Sicong 历史盲区冲突？
- 历史拒绝原因中是否有类似情况？
- 必须提出至少 3 个实质性反驳

### 第三步：综合判断
基于正反双方观点，给出最终判断：

请严格按以下格式输出最终判断：

## 共识等级: [🟢 高共识 / 🟡 有条件共识 / 🟠 存在争议 / 🔴 强烈反对]
## 最终建议: [买入 / 加仓 / 减仓 / 清仓 / HOLD]
## 仓位: [X]%
## 附加条件: [如有]
## 风险提示: [如有]"""

        response = self.claude.chat(prompt, max_tokens=8192)
        return self._parse_decision(response)

    def _parse_decision(self, response: str) -> dict:
        """解析 LLM 输出为结构化决策"""
        result = {
            "raw_response": response,
            "consensus_level": "",
            "action": "",
            "position": "",
            "conditions": "",
            "risks": "",
        }

        # 解析共识等级
        consensus_match = re.search(r"## 共识等级:\s*(.+)", response)
        if consensus_match:
            result["consensus_level"] = consensus_match.group(1).strip()

        # 解析最终建议
        action_match = re.search(r"## 最终建议:\s*(.+)", response)
        if action_match:
            result["action"] = action_match.group(1).strip()

        # 解析仓位
        position_match = re.search(r"## 仓位:\s*(.+)", response)
        if position_match:
            result["position"] = position_match.group(1).strip()

        # 解析附加条件
        condition_match = re.search(r"## 附加条件:\s*(.+)", response)
        if condition_match:
            result["conditions"] = condition_match.group(1).strip()

        # 解析风险提示
        risk_match = re.search(r"## 风险提示:\s*(.+)", response)
        if risk_match:
            result["risks"] = risk_match.group(1).strip()

        return result

    def _format_narrative_leaders(self) -> str:
        """格式化叙事领袖清单"""
        if not self.config.narrative_leaders:
            return "（无）"
        lines = []
        for nl in self.config.narrative_leaders:
            lines.append(f"- {nl['name']}（{'/'.join(nl['alias'])}）: {nl['narrative']}")
        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_decision_agent.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents/decision_agent.py tests/test_decision_agent.py
git commit -m "feat: Agent 2 CoT self-debate decision with consensus parsing"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 11: Agent 3 — 操作分析 Agent

**Files:**
- Create: `src/agents/reflection_agent.py`
- Test: `tests/test_reflection_agent.py`

**Interfaces:**
- Produces: `ReflectionAgent` 类，方法: `record_action()`, `analyze_rejection()`, `quarterly_review()`
- Consumes: `VaultStore` from Task 4

- [ ] **Step 1: 写失败测试 — 拒绝原因分析**

```python
# tests/test_reflection_agent.py
import pytest
from unittest.mock import MagicMock
from src.agents.reflection_agent import ReflectionAgent
from src.llm.claude import ClaudeClient
from src.config.loader import load_market_config
from src.data.models import Market, L7Action, ActionType, ConsensusLevel
from datetime import date

@pytest.fixture
def agent():
    claude = MagicMock(spec=ClaudeClient)
    config = load_market_config(Market.US)
    vault = MagicMock()
    return ReflectionAgent(claude_client=claude, market_config=config, vault=vault)

def test_analyze_rejection(agent):
    agent.claude.chat.return_value = "拒绝原因分析：估值过于乐观，WACC 假设不合理"
    reason = agent.analyze_rejection(
        ticker="NVDA",
        proposed_action="买入",
        sicong_feedback="估值太高了",
    )
    assert "估值" in reason

def test_record_action_writes_to_l7(agent):
    action = L7Action(
        id="NVDA-BUY-2026-06-18",
        ticker="NVDA",
        market=Market.US,
        action_type=ActionType.BUY,
        price=148.0,
        quantity=100,
        position_pct=8.0,
        consensus_level=ConsensusLevel.HIGH,
        action_date=date(2026, 6, 18),
    )
    agent.record_action(action)
    agent.vault.save_l7.assert_called_once_with(action)

def test_discipline_scoring(agent):
    """遵循建议 +1，被警告仍坚持 -1"""
    score = agent.calculate_discipline_score(
        system_suggestion="分两批买入",
        actual_action="一次性全仓",
        was_warned=True,
    )
    assert score == -1

    score = agent.calculate_discipline_score(
        system_suggestion="分两批买入",
        actual_action="分两批买入",
        was_warned=False,
    )
    assert score == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_reflection_agent.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ReflectionAgent**

```python
# src/agents/reflection_agent.py
from src.agents.base import BaseAgent
from src.data.vault import VaultStore
from src.data.models import L7Action


class ReflectionAgent(BaseAgent):
    """Agent 3: 操作分析 Agent

    职责：
    - 记录操作纪律评分
    - 分析拒绝原因并回写 Context
    - 定期复盘总结
    - 季度策略审视（后续迭代）
    """

    def __init__(self, claude_client, market_config, vault: VaultStore):
        super().__init__(claude_client, market_config)
        self.vault = vault

    def record_action(self, action: L7Action):
        """记录操作到 L7"""
        self.vault.save_l7(action)

    def analyze_rejection(
        self,
        ticker: str,
        proposed_action: str,
        sicong_feedback: str,
    ) -> str:
        """分析拒绝原因，返回结构化原因"""
        prompt = f"""Sicong 拒绝了一个投资建议。请分析拒绝原因。

## 被拒绝的建议
- 标的: {ticker}
- 建议操作: {proposed_action}

## Sicong 的反馈
{sicong_feedback}

请用一句话总结拒绝的核心原因（用于下次分析时注入 Context）：
"""
        return self.claude.chat(prompt, max_tokens=512)

    def calculate_discipline_score(
        self,
        system_suggestion: str,
        actual_action: str,
        was_warned: bool,
    ) -> int:
        """计算纪律评分"""
        if was_warned and actual_action != system_suggestion:
            return -1  # 被警告仍坚持
        elif actual_action == system_suggestion:
            return 1  # 遵循建议
        return 0  # 未遵循但未被警告

    def quarterly_review(self, actions: list[L7Action]) -> str:
        """季度策略审视（后续迭代）"""
        # TODO: 实现完整的季度策略审视
        # 🔄 20% — 接口定义完成，检测逻辑待实现
        prompt = f"""请对以下季度操作记录进行策略审视：

{self._format_actions(actions)}

请检测：
1. CoT 辩论有效性（高共识 vs 争议胜率）
2. 保守度/激进度偏差
3. 证据等级有效性
4. 产业链筛选有效性

输出策略调整提案。"""
        return self.claude.chat(prompt, max_tokens=4096)

    def _format_actions(self, actions: list[L7Action]) -> str:
        """格式化操作记录"""
        lines = []
        for a in actions:
            lines.append(
                f"- {a.action_date} {a.ticker} {a.action_type.value} "
                f"共识:{a.consensus_level.value} 评分:{a.discipline_score}"
            )
        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_reflection_agent.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents/reflection_agent.py tests/test_reflection_agent.py
git commit -m "feat: Agent 3 reflection with discipline scoring and rejection analysis"
```

**完成度: ⏸️ 0% (待执行)**
**注意**: 季度策略审视为 🔄 20%（接口完整，完整检测逻辑待实现）。

---

## Task 12: Agent 4 — 交易执行 Agent

**Files:**
- Create: `src/agents/execute_agent.py`
- Test: `tests/test_execute_agent.py`

- [ ] **Step 1: 写失败测试 — 交易执行**

```python
# tests/test_execute_agent.py
import pytest
from unittest.mock import MagicMock
from src.agents.execute_agent import ExecuteAgent
from src.adapters.trading_us import USTradingAdapter
from src.adapters.trading_cn import CNTradingAdapter

def test_execute_us_trade():
    adapter = MagicMock(spec=USTradingAdapter)
    adapter.pre_trade_check.return_value = {"allowed": True, "reason": ""}
    adapter.execute.return_value = {"status": "success", "order_id": "123"}

    agent = ExecuteAgent(trading_adapter=adapter)
    result = agent.execute({"action": "BUY", "ticker": "AAPL", "quantity": 100})
    assert result["status"] == "success"

def test_execute_cn_t1_blocked():
    adapter = CNTradingAdapter()
    adapter._t0_positions = {"600000": "2026-06-18"}
    agent = ExecuteAgent(trading_adapter=adapter)
    result = agent.execute({
        "action": "SELL",
        "ticker": "600000",
        "date": "2026-06-18",
    })
    assert result["status"] == "blocked"
    assert "T+1" in result["reason"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_execute_agent.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ExecuteAgent**

```python
# src/agents/execute_agent.py
from src.adapters.base import BaseTradingAdapter


class ExecuteAgent:
    """Agent 4: 交易执行 Agent

    通过市场适配器执行交易，包含交易前规则检查。
    """

    def __init__(self, trading_adapter: BaseTradingAdapter):
        self.adapter = trading_adapter

    def execute(self, order: dict) -> dict:
        """执行交易

        1. 交易前规则检查（T+1/涨跌停等）
        2. 通过适配器执行
        3. 返回结果
        """
        # 交易前检查
        check = self.adapter.pre_trade_check(order)
        if not check["allowed"]:
            return {
                "status": "blocked",
                "reason": check["reason"],
                "order": order,
            }

        # 执行交易
        result = self.adapter.execute(order)

        # TODO: 写入 L7 操作记录
        # TODO: 同步持仓
        return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_execute_agent.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents/execute_agent.py tests/test_execute_agent.py
git commit -m "feat: Agent 4 trade execution with pre-trade checks"
```

**完成度: ⏸️ 0% (待执行)**
**注意**: 实际下单依赖富途 MCP，为 ⏸️ 0%。交易前规则检查 ✅ 100%。

---

## Task 13: RAG 检索与上下文装配

**Files:**
- Create: `src/context/rag.py`
- Create: `src/context/rerank.py`
- Create: `src/context/assembler.py`
- Create: `src/context/feedback.py`
- Test: `tests/test_rag.py`

- [ ] **Step 1: 写失败测试 — RAG 检索**

```python
# tests/test_rag.py
import pytest
from unittest.mock import MagicMock
from src.context.rag import RAGRetriever
from src.context.assembler import ContextAssembler
from src.context.feedback import FeedbackLoop
from src.data.chroma_store import ChromaStore
from src.llm.gemini import GeminiClient

@pytest.fixture
def rag():
    chroma = MagicMock(spec=ChromaStore)
    gemini = MagicMock(spec=GeminiClient)
    gemini.rerank.return_value = [
        {"document": "营收+18%", "score": 9.0, "index": 0},
        {"document": "毛利率45%", "score": 7.5, "index": 1},
    ]
    return RAGRetriever(chroma_store=chroma, gemini_client=gemini)

def test_rag_retrieve(rag):
    rag.chroma.search.return_value = [
        {"id": "doc1", "content": "营收+18%", "metadata": {"evidence_level": "A"}},
        {"id": "doc2", "content": "毛利率45%", "metadata": {"evidence_level": "A"}},
    ]
    results = rag.retrieve("AAPL 营收", top_k=5)
    assert len(results) > 0
    assert results[0]["score"] == 9.0

def test_context_assembler():
    assembler = ContextAssembler()
    context = assembler.assemble(
        scene="deep_research",
        l2_facts=[],
        l5_judgment=None,
        sicong_profile="画像",
        rejection_reasons="无",
    )
    assert "画像" in context

def test_feedback_loop():
    loop = FeedbackLoop()
    loop.record_rejection("NVDA", "估值过于乐观")
    reasons = loop.get_rejection_reasons("NVDA")
    assert len(reasons) == 1
    assert "估值" in reasons[0]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_rag.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 RAG + Re-rank + 装配 + 反馈**

```python
# src/context/rag.py
from src.data.chroma_store import ChromaStore
from src.llm.gemini import GeminiClient


class RAGRetriever:
    """RAG 检索：向量检索 + Gemini Re-rank"""

    def __init__(self, chroma_store: ChromaStore, gemini_client: GeminiClient):
        self.chroma = chroma_store
        self.gemini = gemini_client

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        where: dict | None = None,
    ) -> list[dict]:
        """检索 + Re-rank"""
        # 1. 向量检索（多取一些用于 Re-rank）
        raw_results = self.chroma.search(query, top_k=top_k * 3, where=where)

        if not raw_results:
            return []

        # 2. Gemini Re-rank
        documents = [r["content"] for r in raw_results]
        reranked = self.gemini.rerank(query, documents, top_k=top_k)

        # 3. 合并元数据
        results = []
        for item in reranked:
            idx = item["index"]
            if 0 <= idx < len(raw_results):
                result = raw_results[idx].copy()
                result["score"] = item["score"]
                results.append(result)

        return results

    def retrieve_with_date_filter(
        self,
        query: str,
        as_of_date: str,
        top_k: int = 10,
    ) -> list[dict]:
        """带日期过滤的检索（回测模式用）"""
        return self.chroma.search_with_date_filter(query, as_of_date, top_k)
```

```python
# src/context/assembler.py
from src.data.models import L2Fact, L5Judgment


class ContextAssembler:
    """上下文装配矩阵"""

    SCENE_BUDGETS = {
        "deep_research": 100_000,  # 100K tokens
        "realtime_consult": 30_000,
        "holding_monitor": 10_000,
        "trend_prediction": 20_000,
    }

    def assemble(
        self,
        scene: str,
        l2_facts: list[L2Fact],
        l5_judgment: L5Judgment | None,
        sicong_profile: str,
        rejection_reasons: str,
        l7_history: list[dict] | None = None,
        l4_bottleneck_map: str | None = None,
    ) -> str:
        """按场景装配上下文"""
        parts = []

        if scene == "deep_research":
            parts.append("## 已知事实（标注证据等级）")
            parts.append(self._format_facts(l2_facts))
            if l4_bottleneck_map:
                parts.append(f"\n## 产业链卡点图谱\n{l4_bottleneck_map}")
            parts.append(f"\n## Sicong 画像\n{sicong_profile}")
            if l7_history:
                parts.append(f"\n## 历史相似案例\n{self._format_history(l7_history)}")
            if rejection_reasons and rejection_reasons != "无":
                parts.append(f"\n## 历史拒绝原因（快速反馈循环）\n{rejection_reasons}")

        elif scene == "realtime_consult":
            parts.append("## 核心事实")
            parts.append(self._format_facts(l2_facts[:10]))  # 只取核心
            if l5_judgment:
                parts.append(f"\n## 当前估值\n{self._format_l5(l5_judgment)}")
            parts.append(f"\n## Sicong 画像\n{sicong_profile}")

        elif scene == "holding_monitor":
            parts.append("## 最新事实")
            parts.append(self._format_facts(l2_facts[:5]))

        return "\n\n".join(parts)

    def _format_facts(self, facts: list[L2Fact]) -> str:
        if not facts:
            return "（暂无）"
        lines = []
        for f in facts:
            lines.append(
                f"- ({f.evidence_level.value}级, {f.fact_date}) "
                f"{f.content} <- {f.source_anchor}"
            )
        return "\n".join(lines)

    def _format_l5(self, l5: L5Judgment) -> str:
        return (
            f"- 内在价值(中性): ${l5.dcf_neutral}\n"
            f"- 当前价格: ${l5.current_price}\n"
            f"- 安全边际: {l5.safety_margin:.1%}"
        )

    def _format_history(self, history: list[dict]) -> str:
        lines = []
        for h in history:
            lines.append(f"- {h.get('date', '')} {h.get('ticker', '')} {h.get('action', '')}")
        return "\n".join(lines)
```

```python
# src/context/feedback.py
from collections import defaultdict


class FeedbackLoop:
    """快速反馈循环 — 拒绝原因管理"""

    def __init__(self):
        self._rejections: dict[str, list[str]] = defaultdict(list)

    def record_rejection(self, ticker: str, reason: str):
        """记录拒绝原因"""
        self._rejections[ticker].append(reason)

    def get_rejection_reasons(self, ticker: str) -> list[str]:
        """获取某标的的历史拒绝原因"""
        return self._rejections.get(ticker, [])

    def get_rejection_context(self, ticker: str) -> str:
        """获取拒绝原因的 Context 注入文本"""
        reasons = self.get_rejection_reasons(ticker)
        if not reasons:
            return "无"
        lines = [f"上次建议 {ticker} 被拒绝的原因："]
        for i, reason in enumerate(reasons[-3:], 1):  # 只取最近 3 次
            lines.append(f"{i}. {reason}")
        lines.append("本次分析时请注意避免类似问题。")
        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_rag.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/context/ tests/test_rag.py
git commit -m "feat: RAG retrieval, context assembler, and feedback loop"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 14: Guardrails（3 道软警告）

**Files:**
- Create: `src/harness/guardrails.py`
- Create: `src/harness/consensus.py`
- Test: `tests/test_guardrails.py`

- [ ] **Step 1: 写失败测试 — Guardrails 软警告**

```python
# tests/test_guardrails.py
import pytest
from src.harness.guardrails import GuardrailChecker, GuardrailWarning

def test_citation_check_soft_warning():
    """溯源校验：软警告，不阻塞"""
    checker = GuardrailChecker()
    output = {"content": "营收+18%", "citations": ["[2025年报#P99]"]}
    context_facts = [{"source_anchor": "[2025年报#P12]"}]  # 页码不匹配
    result = checker.check_citations(output, context_facts)
    assert result["type"] == "soft_warning"
    assert "引用待核验" in result["message"]
    assert result["blocked"] is False

def test_wacc_check_soft_warning():
    """WACC/g 边界：软警告"""
    checker = GuardrailChecker()
    output = {"dcf_params": {"wacc": 0.05, "g": 0.02}}  # WACC 过低
    result = checker.check_wacc_g(output)
    assert result["type"] == "soft_warning"
    assert "估值参数偏离" in result["message"]
    assert result["blocked"] is False

def test_wacc_check_pass():
    """WACC 在范围内：通过"""
    checker = GuardrailChecker()
    output = {"dcf_params": {"wacc": 0.10, "g": 0.02}}
    result = checker.check_wacc_g(output)
    assert result is None  # 无警告

def test_all_guardrails_no_block():
    """所有 Guardrails 都不阻塞"""
    checker = GuardrailChecker()
    output = {"content": "test", "citations": [], "dcf_params": {"wacc": 0.05, "g": 0.08}}
    warnings = checker.run_all(output, context_facts=[])
    # 应该有警告但不阻塞
    assert len(warnings) > 0
    for w in warnings:
        assert w["blocked"] is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_guardrails.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 Guardrails**

```python
# src/harness/guardrails.py
import re
from typing import Optional


class GuardrailWarning:
    """Guardrail 警告"""
    pass


class GuardrailChecker:
    """3 道软警告 Guardrails

    所有 Guardrails 均为软警告，不阻塞输出。
    真正的安全网是 Sicong 的人工确认。
    """

    WACC_RANGE = (0.08, 0.12)
    G_RANGE = (0.00, 0.03)

    def check_citations(
        self,
        output: dict,
        context_facts: list[dict],
    ) -> Optional[dict]:
        """第一道：溯源校验（软警告）"""
        citations = output.get("citations", [])
        if not citations:
            return None  # 无引用不检查

        # 检查引用是否匹配 context 中的来源
        fact_sources = [f.get("source_anchor", "") for f in context_facts]
        mismatched = []
        for citation in citations:
            # 简单匹配：检查引用是否出现在 fact_sources 中
            if not any(citation in src or src in citation for src in fact_sources if src):
                mismatched.append(citation)

        if mismatched:
            return {
                "type": "soft_warning",
                "message": f"⚠️ 引用待核验：{', '.join(mismatched[:3])}",
                "blocked": False,
            }
        return None

    def check_wacc_g(self, output: dict) -> Optional[dict]:
        """第二道：WACC/g 边界（软警告）"""
        params = output.get("dcf_params", {})
        wacc = params.get("wacc", 0.10)
        g = params.get("g", 0.02)

        warnings = []
        if not (self.WACC_RANGE[0] <= wacc <= self.WACC_RANGE[1]):
            warnings.append(f"WACC={wacc:.1%}")
        if not (self.G_RANGE[0] <= g <= self.G_RANGE[1]):
            warnings.append(f"g={g:.1%}")

        if warnings:
            return {
                "type": "soft_warning",
                "message": f"⚠️ 估值参数偏离常规：{', '.join(warnings)}",
                "blocked": False,
            }
        return None

    def check_hallucination(self, output: dict) -> Optional[dict]:
        """第三道：防幻觉（软警告）"""
        content = output.get("content", "")
        # 检查可能的夸大表述
        exaggeration_patterns = [
            r"唯一供应商",
            r"垄断",
            r"必定",
            r"100%",
            r"零风险",
        ]
        found = []
        for pattern in exaggeration_patterns:
            if re.search(pattern, content):
                found.append(pattern)

        if found:
            return {
                "type": "soft_warning",
                "message": f"⚠️ 防幻觉检查：发现可能夸大的表述 {found}",
                "blocked": False,
            }
        return None

    def run_all(
        self,
        output: dict,
        context_facts: list[dict] | None = None,
    ) -> list[dict]:
        """运行全部 3 道检查，返回警告列表（不阻塞）"""
        warnings = []
        context_facts = context_facts or []

        w1 = self.check_citations(output, context_facts)
        if w1:
            warnings.append(w1)

        w2 = self.check_wacc_g(output)
        if w2:
            warnings.append(w2)

        w3 = self.check_hallucination(output)
        if w3:
            warnings.append(w3)

        return warnings
```

```python
# src/harness/consensus.py
from src.data.models import ConsensusLevel


class ConsensusGate:
    """共识门禁"""

    LEVEL_MAP = {
        "🟢": ConsensusLevel.HIGH,
        "🟡": ConsensusLevel.CONDITIONAL,
        "🟠": ConsensusLevel.DISPUTED,
        "🔴": ConsensusLevel.BLOCKED,
    }

    def parse_consensus(self, consensus_text: str) -> ConsensusLevel:
        """解析共识等级文本"""
        for emoji, level in self.LEVEL_MAP.items():
            if emoji in consensus_text:
                return level
        # 文本匹配
        if "高共识" in consensus_text:
            return ConsensusLevel.HIGH
        if "有条件" in consensus_text:
            return ConsensusLevel.CONDITIONAL
        if "争议" in consensus_text:
            return ConsensusLevel.DISPUTED
        if "反对" in consensus_text:
            return ConsensusLevel.BLOCKED
        return ConsensusLevel.DISPUTED  # 默认争议

    def should_push(self, level: ConsensusLevel) -> bool:
        """是否推送给 Sicong"""
        if level == ConsensusLevel.BLOCKED:
            return False  # 拦截待观望
        return True
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_guardrails.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/harness/guardrails.py src/harness/consensus.py tests/test_guardrails.py
git commit -m "feat: 3 soft-warning guardrails and consensus gate"
```

**完成度: ⏸️ 0% (待执行)**

---

## Task 15: 回测模式

**Files:**
- Create: `src/harness/backtest.py`
- Test: `tests/test_backtest.py`

- [ ] **Step 1: 写失败测试 — Point-in-Time 过滤**

```python
# tests/test_backtest.py
import pytest
from datetime import date
from src.harness.backtest import BacktestRunner, PointInTimeFilter
from src.data.models import L2Fact, EvidenceLevel, Market

def test_point_in_time_filter():
    """时间过滤：只保留 as_of_date 之前的数据"""
    filter = PointInTimeFilter()
    facts = [
        L2Fact("f1", "AAPL", "旧事实", EvidenceLevel.A, "[src1]", date(2026, 1, 1), Market.US),
        L2Fact("f2", "AAPL", "新事实", EvidenceLevel.A, "[src2]", date(2026, 6, 1), Market.US),
    ]
    filtered = filter.filter_facts(facts, as_of_date=date(2026, 3, 1))
    assert len(filtered) == 1
    assert filtered[0].id == "f1"

def test_backtest_runner_initialization():
    runner = BacktestRunner(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 6, 1),
        initial_capital=100000,
        tickers=["AAPL"],
    )
    assert runner.portfolio["cash"] == 100000
    assert runner.current_date == date(2026, 5, 1)

def test_backtest_event_check():
    """事件驱动：财报/异动/红线触发"""
    runner = BacktestRunner(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 6, 1),
        initial_capital=100000,
        tickers=["AAPL"],
    )
    # 模拟财报发布日
    events = runner.check_events(date(2026, 5, 15))
    # MVP: 返回事件列表（可能为空）
    assert isinstance(events, list)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_backtest.py -v`
Expected: FAIL

- [ ] **Step 3: 实现回测模式**

```python
# src/harness/backtest.py
from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import Optional
from src.data.models import L2Fact


class PointInTimeFilter:
    """Point-in-Time 数据过滤（回测模式专用）

    只在数据层做时间过滤，不在 Prompt 中限制 LLM。
    """

    def filter_facts(
        self,
        facts: list[L2Fact],
        as_of_date: date,
    ) -> list[L2Fact]:
        """过滤事实：只保留 as_of_date 之前的"""
        return [f for f in facts if f.fact_date <= as_of_date]

    def filter_history(
        self,
        history: list[dict],
        as_of_date: date,
    ) -> list[dict]:
        """过滤历史操作：只保留 as_of_date 之前的"""
        return [
            h for h in history
            if date.fromisoformat(h.get("date", "2000-01-01")) <= as_of_date
        ]


@dataclass
class BacktestRunner:
    """回测执行器

    复用现有 4 Agent 管线，新增 Point-in-Time 过滤 + 性能评估。
    不在 Prompt 中限制 LLM，只在数据层做时间过滤。
    """

    start_date: date
    end_date: date
    initial_capital: float
    tickers: list[str]
    current_date: date = field(init=False)
    portfolio: dict = field(init=False)
    trades: list[dict] = field(default_factory=list)
    pit_filter: PointInTimeFilter = field(default_factory=PointInTimeFilter)

    def __post_init__(self):
        self.current_date = self.start_date
        self.portfolio = {
            "cash": self.initial_capital,
            "positions": {},  # ticker -> {quantity, avg_price}
        }

    def check_events(self, check_date: date) -> list[dict]:
        """检查是否有事件触发"""
        events = []
        # TODO: 实现完整的事件检测
        # - 财报发布日检查
        # - 价格异动检查（>±5%）
        # - L6 假设红线触发检查
        # 🔄 30% — 接口完整，实际事件检测待实现
        return events

    def run_day(self, all_facts: dict[str, list[L2Fact]]):
        """运行单日回测"""
        as_of = self.current_date - timedelta(days=1)

        # 1. Point-in-Time 过滤
        for ticker in self.tickers:
            facts = all_facts.get(ticker, [])
            filtered_facts = self.pit_filter.filter_facts(facts, as_of)

            # 2. 事件检查
            events = self.check_events(self.current_date)

            if events:
                # 3. 运行 Agent 管线（TODO: 接入实际 Agent）
                # 🔄 30% — 需要接入 Agent 1/2/3
                pass
            # 4. 无事件则仅持仓监控（Python, 0 Token）

    def run(self, all_facts: dict[str, list[L2Fact]]):
        """运行完整回测"""
        while self.current_date <= self.end_date:
            self.run_day(all_facts)
            self.current_date += timedelta(days=1)

        return self.evaluate()

    def evaluate(self) -> dict:
        """性能评估"""
        # TODO: 实现完整的性能评估
        # 🔄 30% — 接口完整，实际计算待实现
        return {
            "total_return": 0.0,
            "benchmark_return": 0.0,
            "excess_return": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "trades": len(self.trades),
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_backtest.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/harness/backtest.py tests/test_backtest.py
git commit -m "feat: backtest mode with point-in-time filtering"
```

**完成度: ⏸️ 0% (待执行)**
**注意**: Point-in-Time 过滤 ✅ 100%。事件检测和性能评估 🔄 30%（接口完整，实际逻辑待实现）。

---

## Task 16: 工作流编排与投资建议书

**Files:**
- Create: `src/harness/proposal.py`        # 投资建议书装配器（规格 7.4 节）
- Create: `src/harness/workflow.py`
- Create: `src/main.py`
- Test: `tests/test_workflow.py`

**Interfaces:**
- Produces: `ProposalAssembler` 类，方法: `assemble(ticker, l5_draft, decision, guardrail_warnings, market) -> str`（返回投资建议书 Markdown）
- Produces: `WorkflowOrchestrator` 类，方法: `run_slow_loop()`, `run_fast_loop()`
- 消费: Agent 1/2/3/4 + Guardrails + FeedbackLoop，产出投资建议书 PROPOSAL-{TICKER}-{DATE}

- [ ] **Step 1: 写失败测试 — 投资建议书装配**

```python
# tests/test_workflow.py（追加在文件顶部 import 区）
from src.harness.proposal import ProposalAssembler

def test_proposal_assembler_basic():
    """投资建议书应包含核心结论、研究摘要、CoT摘要、Guardrails、建仓方案"""
    assembler = ProposalAssembler()
    proposal = assembler.assemble(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        market="US",
        l5_draft="# L5_valuation: NVDA\n\n## 底层逻辑三问\n1. 需求真实：AI算力需求\n2. 瓶颈：GPU产能\n3. 股票映射：有A级证据",
        decision={
            "consensus_level": "🟢 高共识",
            "action": "买入",
            "position": "8%",
            "conditions": "无",
            "risks": "注意Q3财报",
        },
        guardrail_warnings=[
            {"type": "soft_warning", "message": "⚠️ 估值参数偏离常规：WACC=5.0%", "blocked": False},
        ],
        valuation={"dcf_pessimistic": 100, "dcf_neutral": 148, "dcf_optimistic": 200, "current_price": 148.0},
        position_plan={"position_pct": 8, "stop_loss": 130, "take_profit": 200, "batch_plan": "第一批50%立即，第二批50%待Q3财报"},
        tracking_assumptions=[
            {"assumption": "Q3营收增速>10%", "metric": "营收增速", "threshold": ">10%", "trigger": "低于则减仓", "check_at": "2026Q3财报"},
        ],
    )
    assert "PROPOSAL-NVDA-" in proposal
    assert "核心结论" in proposal
    assert "🟢" in proposal
    assert "买入" in proposal
    assert "CoT 辩论摘要" in proposal or "CoT" in proposal
    assert "Guardrails" in proposal
    assert "建仓方案" in proposal
    assert "Sicong 确认区" in proposal
    assert "⚠️" in proposal  # 软警告展示

def test_proposal_includes_evidence_strength():
    """建议书应展示证据强度（A/B/C/D 各级条数）"""
    assembler = ProposalAssembler()
    proposal = assembler.assemble(
        ticker="AAPL",
        company_name="Apple Inc.",
        market="US",
        l5_draft="...",
        decision={"consensus_level": "🟡 有条件共识", "action": "买入", "position": "5%"},
        guardrail_warnings=[],
        valuation={"dcf_neutral": 200, "current_price": 180},
        position_plan={"position_pct": 5, "stop_loss": 160, "take_profit": 240, "batch_plan": "一次性建仓"},
        tracking_assumptions=[],
        evidence_counts={"A": 3, "B": 5, "C": 8, "D": 2},
    )
    assert "A级证据" in proposal
    assert "3" in proposal  # A级条数
```

- [ ] **Step 2: 写失败测试 — 慢循环工作流**

```python
# tests/test_workflow.py
import pytest
from unittest.mock import MagicMock, patch
from src.harness.workflow import WorkflowOrchestrator
from src.agents.research_agent import ResearchAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.reflection_agent import ReflectionAgent
from src.agents.execute_agent import ExecuteAgent
from src.harness.guardrails import GuardrailChecker
from src.harness.consensus import ConsensusGate
from src.context.feedback import FeedbackLoop

@pytest.fixture
def orchestrator():
    research = MagicMock(spec=ResearchAgent)
    decision = MagicMock(spec=DecisionAgent)
    reflection = MagicMock(spec=ReflectionAgent)
    execute = MagicMock(spec=ExecuteAgent)
    guardrails = GuardrailChecker()
    consensus = ConsensusGate()
    feedback = FeedbackLoop()

    return WorkflowOrchestrator(
        research_agent=research,
        decision_agent=decision,
        reflection_agent=reflection,
        execute_agent=execute,
        guardrails=guardrails,
        consensus_gate=consensus,
        feedback_loop=feedback,
    )

def test_slow_loop_full_flow(orchestrator):
    """慢循环完整流程：研究→决策→Guardrails→装配建议书→确认→执行"""
    orchestrator.research.screen_chains.return_value = "AI算力产业链"
    orchestrator.research.screen_companies.return_value = "NVDA|重点线索"
    orchestrator.research.deep_research.return_value = "L5 草案"
    orchestrator.decision.decide.return_value = {
        "consensus_level": "🟢 高共识",
        "action": "买入",
        "position": "8%",
    }
    orchestrator.execute.execute.return_value = {"status": "success"}

    result = orchestrator.run_slow_loop(
        ticker="NVDA",
        market_context="市场分析",
        sicong_profile="画像",
        sicong_confirmed=True,
    )
    assert result["status"] == "executed"
    assert "proposal" in result
    assert "PROPOSAL-NVDA-" in result["proposal"]

def test_slow_loop_rejected(orchestrator):
    """Sicong 拒绝时，拒绝原因回写，建议书仍返回供 Sicong 查看"""
    orchestrator.research.screen_chains.return_value = "AI算力"
    orchestrator.research.screen_companies.return_value = "NVDA"
    orchestrator.research.deep_research.return_value = "L5"
    orchestrator.decision.decide.return_value = {
        "consensus_level": "🟢 高共识",
        "action": "买入",
        "position": "8%",
    }
    orchestrator.reflection.analyze_rejection.return_value = "估值过高"

    result = orchestrator.run_slow_loop(
        ticker="NVDA",
        market_context="市场",
        sicong_profile="画像",
        sicong_confirmed=False,
        rejection_feedback="估值太高",
    )
    assert result["status"] == "rejected"
    assert "估值" in result["rejection_reason"]
    assert "proposal" in result  # 拒绝时也返回建议书
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_workflow.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 WorkflowOrchestrator**

```python
# src/harness/workflow.py
from src.agents.research_agent import ResearchAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.reflection_agent import ReflectionAgent
from src.agents.execute_agent import ExecuteAgent
from src.harness.guardrails import GuardrailChecker
from src.harness.consensus import ConsensusGate
from src.context.feedback import FeedbackLoop


class WorkflowOrchestrator:
    """工作流编排器

    快循环：每日行情扫描 + 持仓监控
    慢循环：候选筛选 → 研究 → 决策 → Guardrails → Sicong 确认 → 执行
    """

    def __init__(
        self,
        research_agent: ResearchAgent,
        decision_agent: DecisionAgent,
        reflection_agent: ReflectionAgent,
        execute_agent: ExecuteAgent,
        guardrails: GuardrailChecker,
        consensus_gate: ConsensusGate,
        feedback_loop: FeedbackLoop,
    ):
        self.research = research_agent
        self.decision = decision_agent
        self.reflection = reflection_agent
        self.execute = execute_agent
        self.guardrails = guardrails
        self.consensus = consensus_gate
        self.feedback = feedback_loop

    def run_slow_loop(
        self,
        ticker: str,
        market_context: str,
        sicong_profile: str,
        sicong_confirmed: bool,
        rejection_feedback: str | None = None,
        context_facts: list | None = None,
    ) -> dict:
        """慢循环完整工作流

        1. Agent 1 三层漏斗研究
        2. Agent 2 CoT 决策
        3. Guardrails 检查（软警告）
        4. Sicong 确认
        5. 确认 → Agent 4 执行 / 拒绝 → Agent 3 分析原因
        """
        context_facts = context_facts or []

        # 1. Agent 1: 漏斗式研究
        chains = self.research.screen_chains(market_context)
        companies = self.research.screen_companies(chains)
        l5_draft = self.research.deep_research(ticker, companies, context_facts)

        # 2. Agent 2: CoT 决策
        rejection_reasons = self.feedback.get_rejection_context(ticker)
        decision = self.decision.decide(l5_draft, sicong_profile, rejection_reasons)

        # 3. Guardrails 检查（软警告，不阻塞）
        warnings = self.guardrails.run_all(
            {"content": l5_draft, "dcf_params": {"wacc": 0.10, "g": 0.02}},
            context_facts,
        )
        decision["warnings"] = warnings

        # 4. 共识门禁
        consensus_level = self.consensus.parse_consensus(
            decision.get("consensus_level", "")
        )
        if not self.consensus.should_push(consensus_level):
            return {
                "status": "blocked",
                "reason": "共识门禁拦截（🔴 强烈反对）",
                "decision": decision,
            }

        # 5. Sicong 确认
        if sicong_confirmed:
            # 确认 → 执行
            order = {
                "action": decision.get("action", "HOLD"),
                "ticker": ticker,
            }
            exec_result = self.execute.execute(order)

            # Agent 3 记录操作
            # TODO: 构造 L7Action 并记录
            # 🔄 50%

            return {
                "status": "executed",
                "decision": decision,
                "execution": exec_result,
            }
        else:
            # 拒绝 → 分析原因并回写
            reason = self.reflection.analyze_rejection(
                ticker=ticker,
                proposed_action=decision.get("action", ""),
                sicong_feedback=rejection_feedback or "",
            )
            self.feedback.record_rejection(ticker, reason)

            return {
                "status": "rejected",
                "rejection_reason": reason,
                "decision": decision,
            }

    def run_fast_loop(self, holdings: list[dict]) -> dict:
        """快循环：持仓监控

        MVP: 简化版，只检查 L6 阈值
        """
        # TODO: 实现完整的快循环
        # 🔄 30%
        alerts = []
        for h in holdings:
            # 检查止损线、止盈线、假设红线
            pass
        return {"alerts": alerts, "daily_report": "暂无异常"}
```

```python
# src/main.py
import os
from dotenv import load_dotenv
from src.config.loader import load_market_config
from src.data.models import Market
from src.llm.claude import ClaudeClient
from src.llm.gemini import GeminiClient
from src.data.vault import VaultStore
from src.data.chroma_store import ChromaStore
from src.agents.research_agent import ResearchAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.reflection_agent import ReflectionAgent
from src.agents.execute_agent import ExecuteAgent
from src.adapters.trading_us import USTradingAdapter
from src.adapters.trading_cn import CNTradingAdapter
from src.harness.guardrails import GuardrailChecker
from src.harness.consensus import ConsensusGate
from src.context.feedback import FeedbackLoop
from src.context.rag import RAGRetriever
from src.context.assembler import ContextAssembler
from src.harness.workflow import WorkflowOrchestrator

load_dotenv()


def create_orchestrator(market: Market = Market.US) -> WorkflowOrchestrator:
    """创建工作流编排器"""
    # 加载配置
    config = load_market_config(market)

    # 初始化 LLM
    claude = ClaudeClient(api_key=os.environ["ANTHROPIC_API_KEY"])
    gemini = GeminiClient(api_key=os.environ["GOOGLE_API_KEY"])

    # 初始化存储
    vault = VaultStore(os.environ.get("VAULT_PATH", "./vault"))
    vault.init_vault()
    chroma = ChromaStore()

    # 初始化 Agent
    research = ResearchAgent(claude, config)
    decision = DecisionAgent(claude, config)
    reflection = ReflectionAgent(claude, config, vault)

    if market == Market.US:
        trading = USTradingAdapter()
    else:
        trading = CNTradingAdapter()
    execute = ExecuteAgent(trading)

    # 初始化 Harness
    guardrails = GuardrailChecker()
    consensus = ConsensusGate()
    feedback = FeedbackLoop()

    return WorkflowOrchestrator(
        research_agent=research,
        decision_agent=decision,
        reflection_agent=reflection,
        execute_agent=execute,
        guardrails=guardrails,
        consensus_gate=consensus,
        feedback_loop=feedback,
    )


if __name__ == "__main__":
    orchestrator = create_orchestrator(Market.US)
    print("系统初始化完成。")
    print("可用命令：")
    print("  - run_slow_loop(ticker, ...)  运行慢循环")
    print("  - run_fast_loop(holdings)     运行快循环")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_workflow.py -v`
Expected: ALL PASS

- [ ] **Step 5: 运行全部测试**

Run: `pytest -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/harness/workflow.py src/main.py tests/test_workflow.py
git commit -m "feat: workflow orchestrator with slow/fast loops"
```

**完成度: ⏸️ 0% (待执行)**

---

## 完成度追踪汇总

| Task | 模块 | 完成度 | 说明 |
|---|---|---|---|
| 1 | 项目初始化 | ⏸️ 0% | 待执行 |
| 2 | L1-L7 数据模型 | ⏸️ 0% | 待执行 |
| 3 | 市场配置加载器 | ⏸️ 0% | 待执行 |
| 4 | Vault 读写层 | ⏸️ 0% | L5/L7 解析 🔄 50% |
| 5 | LLM API 封装 | ⏸️ 0% | 待执行 |
| 6 | ChromaDB 向量存储 | ⏸️ 0% | 待执行 |
| 7 | 美股适配器 | ⏸️ 0% | 数据 API 🔄 30%, 交易 ⏸️ |
| 8 | A 股适配器 | ⏸️ 0% | 交易规则 ✅, 数据 API 🔄 30% |
| 9 | Agent 1 研究 | ⏸️ 0% | 待执行 |
| 10 | Agent 2 决策 | ⏸️ 0% | 待执行 |
| 11 | Agent 3 操作分析 | ⏸️ 0% | 季度审视 🔄 20% |
| 12 | Agent 4 交易执行 | ⏸️ 0% | 规则检查 ✅, 下单 ⏸️ |
| 13 | RAG + 上下文 | ⏸️ 0% | 待执行 |
| 14 | Guardrails | ⏸️ 0% | 待执行 |
| 15 | 回测模式 | ⏸️ 0% | PIT 过滤 ✅, 事件检测 🔄 30% |
| 16 | 工作流编排 | ⏸️ 0% | 待执行 |

**整体完成度: 0% (16 个 Task 待执行)**

### 已知 TODO 项（实现时如遇阻塞可设为代办）

| TODO | 位置 | 优先级 | 替代方案 |
|---|---|---|---|
| SEC EDGAR API 实际调用 | Task 7 | 中 | 手动投喂 `_inbox/` |
| 巨潮/东方财富 API | Task 8 | 中 | 手动投喂 `_inbox/` |
| 富途 MCP 接入 | Task 7/8/12 | 高 | MVP 阶段跳过实盘交易 |
| L5 Markdown→对象解析 | Task 4 | 低 | 直接使用 Markdown 文本 |
| L7 按标的检索 | Task 4 | 低 | 全量扫描 |
| 季度策略审视完整逻辑 | Task 11 | 低 | MVP 后迭代 |
| 回测事件检测 | Task 15 | 中 | 手动指定回测日期 |
| 回测性能评估 | Task 15 | 中 | 手动计算 |
| 快循环持仓监控 | Task 16 | 中 | MVP 先做慢循环 |
