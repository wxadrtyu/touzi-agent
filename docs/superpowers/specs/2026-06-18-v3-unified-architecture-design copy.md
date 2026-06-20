# 投资研究 AI 系统规格说明书 (V3 - 同心圆三层 + 双循环 + L1-L7 统一架构)

- **日期**: 2026-06-18
- **状态**: Proposed (V3 — 统一 V1.5 业务逻辑与 V2 三层工程架构，新增操作分析 Agent 与富途 MCP 集成)
- **核心定位**: 针对 **Sicong** 的私人投资教练 Agent。主动给出"买什么、为什么、怎么买、买了后做什么、变化后做什么、何时卖"的全生命周期决策，并通过**双 Investment Advisor 内部辩论**过滤低质建议，再推送给 Sicong 确认。
- **技术栈**: Obsidian Vault（唯一真相存储）+ Python（Agent / RAG / Guardrail 后端）+ Web 前端
- **架构模型**: 同心圆三层（Prompt / Context / Harness）+ 双循环执行（System 1 快循环 / System 2 慢循环）+ L1-L7 数据地基

---

## 架构概览：同心圆三层 + 双循环 + L1-L7

```
┌─────────────────────────────────────────────────────────────┐
│  【Harness 外层】运行保障与优化闭环                              │
│  ├─ 工作流编排 (workflows/)                                    │
│  ├─ Guardrails 三道防线 (溯源/边界/一致性)                      │
│  ├─ 写入门禁 (permissions.md) — 分阶段权限                      │
│  ├─ 富途 MCP 桥接 (查询/交易)                                  │
│  └─ 监控与可观测性                                              │
│                          ↕ 调度·约束·保障                       │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  【Context 中层】信息供给与知识基础                        │   │
│  │  ├─ RAG 混合检索 (Dense + Sparse + RRF + Rerank)       │   │
│  │  ├─ 情绪数据管道 (Sentiment)                            │   │
│  │  ├─ Context 装配矩阵 (按场景动态组装)                    │   │
│  │  └─ 上下文压缩与长度控制                                 │   │
│  │                          ↕ 检索·装配·注入                 │   │
│  │  ┌───────────────────────────────────────────────┐    │   │
│  │  │  【Prompt 内层】7 个 Agent 的 6P 大脑             │    │   │
│  │  │  ├─ Agent 1: 研究咨询 Agent (Deep RAG 增强)     │    │   │
│  │  │  ├─ Agent 2: 情报分析 Agent (Sentiment)         │    │   │
│  │  │  ├─ Agent 3: 审计委员会 (白毛股神+孙宇晨+盲区)    │    │   │
│  │  │  ├─ Agent 4: IA#1 主提案方                      │    │   │
│  │  │  ├─ Agent 5: IA#2 魔鬼代言人                     │    │   │
│  │  │  ├─ Agent 6: 操作分析 Agent (新增)               │    │   │
│  │  │  └─ Agent 7: 交易执行 Agent (富途 MCP 桥接)      │    │   │
│  │  └───────────────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────────┘   │
│                          ↕ 读取·写入·提案                       │
│  ══════════════ 【L1-L7 唯一真相 Vault】 ══════════════       │
│  L1 原始痕迹 │ L2 原子事实 │ L3 身份画像 │ L4 关联网络         │
│  L5 心智判断 │ L6 监控规则 │ L7 行动记录                       │
└─────────────────────────────────────────────────────────────┘

                    ║ 双循环执行模式 ║
    ┌─────────────────┴─────────────────┐
    ▼                                     ▼
【快循环 System 1】               【慢循环 System 2】
实时咨询/查询                     定时深度分析/提案
用户提问 → RAG → 研究咨询Agent     定时触发 → 全Agent链
→ 直接回答 (轻量)                 → 共识门禁 → 提案推送
                                 → 操作复盘 (季度/平仓)
```

**三层与 L1-L7 的关系：**
- **Context 层**：从 L1-L7 **读取/检索**，动态装配上下文注入 Agent
- **Harness 层**：控制对 L1-L7 的**写入权限**（分阶段门禁）
- **Prompt 层**：Agent 消费上下文后，**产出提案**回流到 L1-L7（经 Harness 门禁校验）

**三层协同逻辑：**
- **Prompt 决定模型"做什么"**（任务定义与输出表达）
- **Context 决定模型"知道什么"**（信息供给与知识基础）
- **Harness 决定模型"如何可靠地做，并持续变好"**（运行保障与优化闭环）

---

## 一、 唯一真相：L1-L7 数据层定义与物理结构

知识库 Vault 物理上由纯 Markdown 文件和 Frontmatter 构成。Harness 不持有状态，所有的状态均存储于以下 L1-L7 的结构化 Markdown 中。

### 1. L1 原始痕迹层 (Raw Inbox)
- **物理路径**：`_inbox/*.md`
- **来源**：网页剪报、微信聊天导出、PDF 财报、富途持仓快照、Sicong 随手记
- **Frontmatter 格式**：
    ```yaml
    type: L1-raw
    source: chrome-extension | manual | wechat | futu-snapshot
    captured_at: 2026-06-18T18:00:00+08:00
    status: unprocessed | processed
    ```
- **职责**：未经加工的原始素材暂存区

### 2. L2 原子事实层 (Atomic Facts)
- **物理路径**：`L2-facts/[Ticker]-facts.md`（例如：`L2-facts/AAPL-facts.md`）
- **职责**：将 L1 零散表达与财报，抽成可检索、可合并的事实片段
- **Markdown 正文格式**（每条事实单行、自包含、带溯源锚点）：
    ```markdown
    - [FACT_01cf3] 苹果 2025 年第四季度服务业营收为 250 亿美元，同比增长 12%。<- [2025-Q4-Earnings.pdf#Page_12]
    - [FACT_9a2ef] 库克在 Q4 电话会中指出，AI 智能体的变现周期可能比预期更长。<- [2025-Q4-Call-Transcript.md#Page_3]
    ```

### 3. L3 身份画像层 (Profiles)
包含 Sicong 自己的画像与大师决策因子包。
- **物理路径**：
    - Sicong 个人画像：`L3-profile/investor-profile.md`（资金/风险边界/盲区清单/操作纪律评分）
    - 巴菲特画像：`L3-profile/persona-buffett.md`（护城河/安全边际/DCF 现金流审计）
    - 德鲁肯米勒画像：`L3-profile/persona-druckenmiller.md`（动量趋势/流动性驱动/快速纠错）
    - 白毛股神画像：`L3-profile/persona-serenity.md`（产业链卡脖子瓶颈选股审计）
    - 孙宇晨画像：`L3-profile/persona-sun.md`（叙事泡沫反向探测/FOMO 预警）
- **大师画像结构 (以巴菲特为例)**：
    ```yaml
    name: Warren Buffett
    load_trigger: on_value_stock
    core_metrics:
      min_roe: 0.15
      debt_to_equity_max: 0.5
      preferred_industries: ["Consumer", "Financial", "Energy"]
    forbidden_rules:
      - "严禁在高市盈率（PE > 35）且无强现金流支撑时买入"
    ```

### 4. L4 关联网络层 (Relations)
- **物理路径**：`L4-relations/`
    - 宏观传导乘数矩阵：`L4-relations/macro-multipliers.md`
    - 产业链上下游依赖图谱：`L4-relations/supply-chain-[Sector].md`
- **职责**：跨标的、跨板块的关联关系

### 5. L5 心智判断层 (Judgments)
- **物理路径**：`L5-judgments/[Ticker]-judgment.md`
- **Frontmatter 格式**：
    ```yaml
    ticker: AAPL
    last_updated: 2026-06-18
    status: proposed | approved  # proposed = Agent 提案，approved = Sicong 拍板后落盘
    ```
- **正文结构**：
    ```markdown
    # 核心论点 (Thesis)
    依靠高粘性服务业，具备极宽护城河。

    # 估值区间 (Valuation)
    - 悲观 DCF: 190.5 美元
    - 中性 DCF (Base): 225.0 美元
    - 乐观 DCF: 250.0 美元

    # 买入假设与建仓方案
    - Q3 营收增速必须 > 10%
    - 毛利率不低于 43%
    - 止损线：$190
    - 建仓步长：首批 5%，第二批 3%
    ```

### 6. L6 监控规则层 (Alerts)
- **物理路径**：`L6-alerts/[Ticker]-alerts.md`
- **内容**：估值偏离阈值、买入时锁定的财务假设红线、止盈止损线
- **职责**：持仓监控与规则触发

### 7. L7 行动记录层 (Action Logs)
- **物理路径**：`L7-actions/trades.md`
- **职责**：机械层自动记录，Sicong 交易指令落盘
- **格式**：
    ```markdown
    - [TRADE_88aef] 2026-06-18 10:00:00 | BUY | AAPL | 100 股 | 价格: 201.2 美元 | 关联 L5 提案: [AAPL-judgment#L5] | 共识等级: 🟢 高共识

    # 操作记录 AAPL-BUY-2026-06-18
    ## 基本信息
    - 操作类型：买入 / 加仓 / 减仓 / 清仓
    - 标的：AAPL  价格：$201.2  数量：100股  仓位占比：8%
    - 共识等级：🟢 高共识（IA#1 与 IA#2 完全同意）

    ## 决策背景
    - 系统建议：分两批买入（首批 5%，第二批 3%）
    - Sicong 实际决定：一次性买入 8%（未遵循分批建议）
    - 违规标记：❗ 未按建议执行（记入操作纪律评分）

    ## 买入时锁定的假设红线 (L6)
    - Q3 营收增速必须 > 10%
    - 毛利率不低于 43%
    - 止损线：$190

    ## 复盘评价（定期自动触发）
    - 3个月后价格：$225（+11.8%）
    - 假设是否被证伪：否
    - 操作评价：盈利，但未遵循分批建仓纪律
    - 经验/教训：本次操作验证了"低估值+财报超预期"策略有效，但一次性全仓存在择时风险
    - 新增画像条目：Sicong 在有信心时倾向于一次性重仓，不遵循分批纪律
    ```

---

## 二、 第一层：Prompt Engineering (7 个 Agent 的 6P 设计)

在此层中，核心 Agent 的 Prompt 必须直接感知数据层（L1-L7）的文件规范，并使用强类型指令来限制幻觉。每个 Agent 遵循 6P 设计框架：**Persona（角色）/ Purpose（目标）/ Process（流程）/ Policy（约束）/ Presentation（输出格式）/ Proof（自检）**。

### Agent 1：研究咨询 Agent (Deep RAG Analyst 增强)

| 6P | 定义 |
|---|---|
| **Persona** | CFA 股票估值专家 + 投研顾问。具备财报分析、DCF 估值、行业趋势预判能力 |
| **Purpose** | ① 从 L1 及外部资料提炼 L2 原子事实 ② 计算 DCF/PE-Band 估值 ③ 输出 L5 判断提案 ④ 回答 Sicong 实时咨询 ⑤ 基于历史数据与行业逻辑预测未来趋势 |
| **Process** | 1. 解析 Context 灌入的 `_inbox/` 文件与财报 PDF<br>2. 提取 L2 事实（带溯源锚点 `<- [文件#页码]`）<br>3. 在 `<analysis_draft>` 中跑 DCF 数学计算：$FCF = \text{Operating Cash Flow} - \text{CapEx}$，根据美债 10 年期收益率设定 WACC<br>4. 输出 L5 提案 + JSON 报告<br>5. **快循环模式**：直接回答用户咨询，引用 L2/L5 事实<br>6. **趋势预测**：基于 L2 历史数据 + L4 关联网络，推演 3-6 个月趋势 |
| **Policy** | • 溯源铁律：未在 Context 原文找到的数字必须标 `null`<br>• 只提案不落盘：严禁直接改写 L5 `status: approved`<br>• 趋势预测必须标注置信度（高/中/低）和关键假设 |
| **Presentation** | ① `<l2_facts_proposal>` 新原子事实 Markdown<br>② `<l5_judgment_proposal>` L5 草稿（`status: proposed`）<br>③ **快循环**：直接 Markdown 回答 + 引用溯源<br>④ `<trend_forecast>` 趋势预测（含置信度） |
| **Proof** | 输出前自检：所有数字是否有溯源锚点？WACC 在 5%-15%？永续增长率 g 在 0%-3%？ |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：快循环（实时咨询）+ 慢循环（深度分析）

---

### Agent 2：情报分析 Agent (Sentiment Analyst)

| 6P | 定义 |
|---|---|
| **Persona** | 市场情绪分析师 |
| **Purpose** | 批量抓取并分类舆情，计算板块/个股的情绪共识强度，作为 Context 注入其他 Agent |
| **Process** | 1. 从 Twitter/RSS/财经新闻抓取原始舆情<br>2. Gemini Flash 批量情感分类（看多/看空/中性）<br>3. 聚合计算板块情绪共识强度<br>4. 输出结构化情绪数据 |
| **Policy** | • 仅处理公开数据，不存储个人隐私<br>• 情绪数据有时效性，必须标注采集时间<br>• 情绪是参考因子，不是决策依据 |
| **Presentation** | JSON 格式：`{ticker, sentiment_score, volume, sources, collected_at}` |
| **Proof** | 检查样本量是否足够（< 10 条标记低置信度） |

- **模型**：Gemini 1.5 Flash
- **活跃循环**：慢循环（定时批量处理）

---

### Agent 3：审计委员会 (Audit Council)

| 6P | 定义 |
|---|---|
| **Persona** | 三脑合一的审计委员会：① 白毛股神（产业链卡脖子审计）② 孙宇晨（叙事泡沫反向探测）③ Sicong 盲区检测器 |
| **Purpose** | 对 Agent 1 的 L5 提案进行多视角审计，找出逻辑软肋、叙事泡沫风险、与 Sicong 历史盲区的冲突 |
| **Process** | 1. 载入 Agent 1 的 L5 提案 + L3 画像（白毛股神/孙宇晨/Sicong）<br>2. **白毛股神视角**：这家公司真的是产业链卡脖子环节吗？上下游依赖度如何？<br>3. **孙宇晨视角**：这是叙事泡沫还是真实基本面驱动？FOMO 信号强度？<br>4. **盲区检测**：与 `L3-profile/investor-profile.md` 中的历史盲区清单比对<br>5. 输出三份审计意见 + 综合风险评级 |
| **Policy** | • persona 防火墙：装载大师大脑时必须标注「以下为 \<name\> 视角的模拟」，用完交还决策权<br>• 严禁静默把 persona 结论写进 L5 当成 Sicong 的判断<br>• 三脑必须独立输出，不得互相污染 |
| **Presentation** | ① `<serenity_audit>` 白毛股神审计意见<br>② `<sun_audit>` 孙宇晨审计意见<br>③ `<blindspot_check>` 盲区检测结果<br>④ `<risk_rating>` 综合风险评级（低/中/高/极高） |
| **Proof** | 自检：三脑是否各自独立输出？是否引用了 L3 画像？盲区比对是否覆盖全部清单？ |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（L5 提案生成后触发）

---

### Agent 4：IA#1 主提案方 (Investment Advisor #1)

| 6P | 定义 |
|---|---|
| **Persona** | 首席投资官 |
| **Purpose** | 整合 Agent 1-3 所有情报（L5 提案 + 情绪 + 审计意见），结合 L3 画像和大师加权因子，生成完整操作建议草案 |
| **Process** | 1. 载入 Agent 1 的 L5 提案 + Agent 2 情绪数据 + Agent 3 审计意见<br>2. 读取 `L3-profile/investor-profile.md`（Sicong 画像）和激活的大师画像<br>3. 执行因子衰减计算：$\text{Final Weight} = \text{Raw Weight} \times \text{Attenuator}$<br>4. 计算安全边际、建仓步长、仓位上限<br>5. 输出买卖/建仓/减仓提案 |
| **Policy** | • 安全边际门禁：现价不低于中性估值 15% 一律 `HOLD`<br>• 个性化强校验：Sicong 画像含"对回撤敏感"→ 单股上限从 15% 衰减至 8%<br>• 高风险操作标记：追高/超仓/亏损加仓/VIX>30 需二次确认 |
| **Presentation** | JSON：`{action, ticker, target_price, position_size, rationale, risk_flags, consensus_level}` |
| **Proof** | 自检：安全边际是否满足？仓位是否超限？是否与盲区冲突？ |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（审计完成后触发）

---

### Agent 5：IA#2 魔鬼代言人 (Investment Advisor #2)

| 6P | 定义 |
|---|---|
| **Persona** | 风控官 / 魔鬼代言人 |
| **Purpose** | 强行攻击 Agent 4 的提案，找出逻辑和估值假设的软肋，达成共识才推送 Sicong |
| **Process** | 1. 载入 Agent 4 的提案 + Agent 1 的 DCF 假设<br>2. 锁定乐观因子（永续增长率 $g > 2.5\%$，折现率 $WACC < 7.5\%$）<br>3. 强行运行悲观参数 DCF，输出对比差值<br>4. 逐条审查：假设是否成立？忽略的风险？叙事泡沫？盲区冲突？<br>5. 输出共识等级 |
| **Policy** | • 必须反驳：禁止附和 IA#1，必须指出至少 2 点核心反驳<br>• 反驳必须含差值影响百分比 `rebuttal_impact_pct`<br>• 🔴 强烈反对时暂不推送，等待新数据窗口重新评估 |
| **Presentation** | JSON：`{verdict, rebuttals[], rebuttal_impact_pct, consensus_level, conditions[]}` |
| **Proof** | 自检：是否至少 2 点反驳？差值百分比是否计算？共识等级是否合理？ |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（IA#1 提案后触发）

#### 四级共识等级与推送策略

| 共识等级 | 条件 | 推送行为 | 标签 |
|---|---|---|---|
| 🟢 **高共识** | IA#1 与 IA#2 完全同意 | 立即推送，强烈建议执行 | `强推` |
| 🟡 **有条件共识** | 同意但 IA#2 附加补充条件 | 推送，同时展示 IA#2 的附加条件与风险提示 | `有条件同意` |
| 🟠 **存在争议** | IA#2 有重大异议 | 两方观点同时呈现给 Sicong，标注分歧焦点，Sicong 做最终裁决 | `存在争议` |
| 🔴 **IA#2 强烈反对** | IA#2 发现致命逻辑缺陷 | 暂不推送，等待新数据窗口（如下季财报）重新评估 | `拦截待观望` |

---

### Agent 6：操作分析 Agent (新增)

| 6P | 定义 |
|---|---|
| **Persona** | 投资行为分析师 + 画像优化顾问 |
| **Purpose** | ① 分析 Sicong 的历史操作（L7）② 总结操作模式与纪律遵从率 ③ 发现认知盲区 ④ 生成 L3 画像优化提案 ⑤ 提供行为修正建议 |
| **Process** | 1. 读取 `L7-actions/trades.md` 近 30/90/180 天操作记录<br>2. 对比"系统建议 vs 实际操作"，计算纪律遵从率<br>3. 识别操作模式：追高/恐慌卖/一次性重仓/不按分批等<br>4. 与 `L3-profile/investor-profile.md` 盲区清单比对，发现新盲区<br>5. 生成画像更新提案（L3 提案制，必须 Sicong 确认）<br>6. 输出行为修正建议 + 季度复盘报告 |
| **Policy** | • L3 提案制铁律：只能生成画像更新提案，严禁直接改写 L3<br>• 客观不评判：分析行为模式时不带道德判断，只陈述事实与统计<br>• 盲区发现必须有 L7 数据支撑，不得臆测<br>• 复盘报告必须含"遵循系统 vs 自行决策"胜率对比 |
| **Presentation** | ① `<behavior_analysis>` 操作模式分析（含统计图表数据）<br>② `<blindspot_proposal>` 新盲区发现提案<br>③ `<profile_update_proposal>` L3 画像更新提案（Diff 格式）<br>④ `<quarterly_review>` 季度复盘报告 |
| **Proof** | 自检：分析是否基于 L7 实际数据？盲区发现是否有 ≥3 次案例支撑？画像提案是否为 Diff 格式？ |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（每季度/每次平仓触发）+ 快循环（Sicong 主动要求复盘时）

---

### Agent 7：交易执行 Agent (富途 MCP 桥接)

| 6P | 定义 |
|---|---|
| **Persona** | 交易执行员（机械执行，不决策） |
| **Purpose** | ① 通过富途 MCP 查询账户/持仓/订单 ② 执行经共识门禁通过的买卖指令 ③ 自动记录到 L7 ④ 监控订单状态 |
| **Process** | 1. **查询模式**：接收 Sicong 查询指令 → 调用富途 MCP → 返回账户/持仓/订单信息<br>2. **交易模式**：接收经共识门禁通过的指令 → 调用富途 MCP 下单 → 确认成交 → 自动写入 L7<br>3. **监控模式**：定时查询订单状态 → 成交/撤单/部分成交 → 更新 L7 |
| **Policy** | • **绝不决策**：只执行经 IA#1+IA#2 共识通过且 Sicong 确认的指令<br>• **二次确认门禁**：高风险操作（追高/超仓/亏损加仓/VIX>30）默认选项为"取消"<br>• **紧急熔断例外**：价格跌破止损线超 5%，无需共识投票，直接推送红色硬止损警报<br>• **L7 即时写入**：交易成交后必须立即追加 L7 记录，零延迟<br>• **失败处理**：MCP 调用失败时重试 3 次，仍失败则告警 Sicong |
| **Presentation** | ① 查询结果：JSON 格式账户/持仓/订单数据<br>② 交易确认：`{order_id, ticker, action, qty, price, status, l7_record_id}`<br>③ 告警：`{alert_type, message, retry_count}` |
| **Proof** | 自检：指令是否经共识门禁通过？Sicong 是否已确认？L7 是否已写入？ |

- **模型**：Python 脚本 + 富途 MCP（0 Token，机械执行）
- **活跃循环**：快循环（查询）+ 慢循环（交易执行）+ 持续（订单监控）

#### 富途 MCP 能力清单
- **查询类**：账户余额、持仓明细、挂单状态、历史成交
- **交易类**：市价单、限价单、撤单
- **监控类**：订单状态轮询、成交回调

---

## 三、 第二层：Context Engineering (RAG 混合检索与上下文装配)

Context 层的核心任务是实现 **Context Loader** 的检索装配算法与本地轻量级 **RAG (Retrieval-Augmented Generation) 检索管道**。

### 1. RAG 物理切片与结构化清洗

| 数据类型 | 清洗规则 | 切片策略 |
|---|---|---|
| **财报 PDF** | `pdfplumber` 识别表格区域，转 Markdown Table / CSV。严禁纯 text 转换 | 1500 tokens/块，overlap 200。表格必须完整保留在一个 Chunk |
| **电话会纪要** | 按"发言人-答复"问答对切片 | 每个 QA 块绑定 metadata：`{ticker, date, speaker, type:qa_call}` |
| **新闻/舆情** | 去重 + 去噪 | 500 tokens/块，按时间窗口聚合 |
| **L1-L7 Markdown** | 直接按 Frontmatter 分块 | 按层级行为最小单元（L2 单条事实/L5 单个 Ticker 文件） |

### 2. 混合检索管道 (Hybrid Search Pipeline)

```
用户 Query / Agent 请求
        │
    ┌───┴───┐
    ▼       ▼
[Dense 语义]  [Sparse 关键词+数字]
 BAAI/bge-    SQLite FTS5
 small-zh-    全文索引
 v1.5 (384维)  关键词+数字
    │              │
 Top K1=15     Top K2=15
    └───┬───┘
        ▼
  [RRF 互惠等级融合]
   RRF_Score = 1/(60+r_dense) + 1/(60+r_sparse)
        │
   融合 Top 15
        ▼
  [Re-rank 重排]
   Gemini Flash 评分 0-10
   阈值拦截 < 5分
        │
   精炼 Top N (N≤8, ≤6k tokens)
        ▼
  注入 Agent Context
```

**双路召回设计理由**：
- **Dense 语义召回**：使用本地轻量级 `BAAI/bge-small-zh-v1.5`（384 维，仅 100MB 显存），防语义稀释
- **Sparse 关键词+数字召回**：SQLite FTS5 全文索引，针对关键数字（如"Q4"、"毛利率"、"8%"、"2025"）精确召回，防数字丢失
- **RRF 融合**：避免两路打分范围不同无法加权
- **轻量 Re-rank**：Gemini Flash 快速评分 0-10，拦截噪声 Chunk

### 3. 动态 Context 装配矩阵

| 触发场景 | 触发源 | 动态加载的 Vault 上下文组合 |
|---|---|---|
| **快循环：实时咨询** | Sicong 提问 | RAG 检索 Top 8 Chunks + 匹配的 `L5-judgments/[Ticker]` + `L3-profile/investor-profile.md` |
| **慢循环：inbox 提取 L2** | 定时任务 | `_inbox/` 未处理文件 + `L2-facts/[Ticker]` 增量比对 |
| **慢循环：更新 L5 提案** | 新增 L2 事实 | `L2-facts/[Ticker]` 全集 + 宏观无风险利率 + 旧 `L5-judgments/[Ticker]` |
| **慢循环：共识门禁** | L5 提案生成 | L5 提案 + Agent 3 审计意见 + `L3-profile/` 活跃大师画像 + Agent 2 情绪数据 |
| **慢循环：操作复盘** | 季度/平仓触发 | `L7-actions/` 30/90/180 天记录 + `L3-profile/investor-profile.md` 盲区清单 |
| **快循环：交易查询** | Sicong 查询 | 富途 MCP 实时数据 + `L7-actions/` 近期记录 |
| **慢循环：交易执行** | 共识通过+确认 | 交易指令 + `L5-judgments/[Ticker]` + `L6-alerts/[Ticker]` 假设红线 |

### 4. Context 长度控制与自适应压缩

```python
def assemble_context(ticker, query, scenario):
    # Tier 1: 核心指标与画像 (强制不压缩，100% 导入)
    tier1 = load_core_metrics(ticker) + load_profile()

    # Tier 2: RAG 混合检索 (动态压缩到 6k tokens)
    tier2 = run_hybrid_retrieval(ticker, query)

    # Tier 3: 历史行动记录 (聚合摘要，非全量)
    tier3 = get_aggregated_historical_logs(ticker, days=30)

    # 总长度检查：超过阈值时优先压缩 Tier 3
    return compress_and_assemble(tier1, tier2, tier3, max_tokens=12000)
```

---

## 四、 第三层：Harness Engineering (工作流·门禁·Guardrails·富途 MCP)

Harness 是保障整个 Vault 唯一真相不受污染的安全锁，物理落实在 `workflows/`、`permissions.md` 和 `guardrail_runner.py`。

### 1. 物理写入门禁权限表 (`harness/permissions.md`)

本表为绝对不变量。任何 Agent 写入操作在落盘前，Harness 必须读取此配置实施拦截。权限按**成熟度分阶段**设计：

| 目标数据层 | 数据特性 | Agent 权限 | 早期阶段（当前） | 成熟阶段（后续） |
|---|---|---|---|---|
| **L1 `_inbox/`** | 原始素材 | 读/写 | **Sicong 确认入库**（防止垃圾/错误素材污染源头） | 零确认（直接追加） |
| **L2 `L2-facts/`** | 机械数据事实 | 读/写 | **溯源校验 + Sicong 确认**（逐条审阅事实准确性） | 溯源校验 + 抽样审阅 |
| **L3 `L3-profile/`** | 核心人设/偏好 | **提案制** | **强确认**（Sicong 拍板合并） | 强确认（画像是核心，始终需要确认） |
| **L4 `L4-relations/`** | 关联网络 | **提案制** | **强确认**（Sicong 拍板合并） | 抽样确认 |
| **L5 `L5-judgments/`** | 交易方向/估值 | **提案制** | **强确认**（Sicong 改 `approved` 才合并） | 强确认（判断层始终需要确认） |
| **L6 `L6-alerts/`** | 监控规则 | **提案制** | **强确认**（Sicong 拍板合并） | 抽样确认 |
| **L7 `L7-actions/`** | 交易物理记录 | 读/写 | 零确认（机械记录，交易发生即写） | 零确认 |

**设计要点**：
- **早期阶段**：L1-L6 全部需要 Sicong 确认，确保数据质量从源头抓起
- **成熟阶段**：L1/L2/L4/L6 逐步放松为自动 + 抽样审阅，L3/L5 始终强确认
- **L7 始终零确认**：客观交易记录，不涉及判断
- **提案制**：Agent 主动维护，生成 Diff 格式提案 → Sicong 审阅拍板 → 合并落库

### 2. 三道 Guardrails 金融专防

Harness 运行在 Python 沙箱中，每次 API 响应都必须经过本地 `harness/scripts/guardrail_runner.py` 的管道过滤：

| 防线 | 名称 | 校验内容 | 失败处理 |
|---|---|---|---|
| **第一道** | 正则溯源校验器 | 匹配 `<- [文件名#页码]`，验证源文件和页码在 Context 中存在 | 自检重试 1 次，仍失败则拦截 |
| **第二道** | 交易一致性校验 | `BUY` 时 `target_price ≤ DCF中性 × 0.85`（15% 安全边际） | 驳回为 `HOLD` |
| **第三道** | WACC/g 边界断言 | WACC ∈ [5.0%, 15.0%]，永续增长率 g ∈ [0.0%, 3.0%] | 超范围拦截，要求重算 |

```python
import re

# 第一道防线：正则溯源校验器
def validate_data_anchoring(output_text, source_context):
    # 匹配 "<- [文件名#页码]"
    anchors = re.findall(r"<- \[(.*?)#(Page_.*?)\]", output_text)
    if not anchors:
        return False  # 必须包含数据源锚定

    for doc_name, page_no in anchors:
        # 在注入的上下文 source_context 里，查找是否存在对应的文档和页码标识
        if f"{doc_name}" not in source_context or f"{page_no}" not in source_context:
            return False  # 发现虚假溯源，拦截
    return True

# 第二道防线：交易一致性校验
def validate_trade_consistency(ia1_verdict, l5_proposal):
    if ia1_verdict["action"] == "BUY":
        max_price = l5_proposal["valuation"]["dcf_bear_mid_bull"][1] * 0.85
        if ia1_verdict["execution"]["target_price"] > max_price:
            ia1_verdict["action"] = "HOLD"  # 溢价过高，不符合 15% 安全边际
    return ia1_verdict

# 第三道防线：WACC/g 边界断言
def validate_dcf_bounds(l5_proposal):
    wacc = l5_proposal["valuation"]["wacc"]
    g = l5_proposal["valuation"]["perpetual_growth"]
    assert 0.05 <= wacc <= 0.15, f"WACC {wacc} 超出 [5%, 15%] 边界"
    assert 0.0 <= g <= 0.03, f"永续增长率 {g} 超出 [0%, 3%] 边界"
    return True
```

### 3. 富途 MCP 集成设计

```
【Sicong 确认交易】
       │
       ▼
【Harness 门禁校验】
  ├─ 共识等级检查（🟢🟡 可执行，🟠🔴 拦截）
  ├─ 高风险二次确认（追高/超仓/亏损加仓/VIX>30）
  └─ 紧急熔断检查（止损线超 5% → 直接硬止损警报）
       │
       ▼
【富途 MCP 调用】
  ├─ 查询：account_info / positions / orders
  └─ 交易：place_order(ticker, action, qty, price)
       │
       ▼
【L7 自动写入】
  └─ [TRADE_xxxx] 时间 | 操作 | Ticker | 数量 | 价格 | 关联L5 | 共识等级
       │
       ▼
【订单状态监控】
  └─ 定时查询 → 成交/撤单/部分成交 → 更新 L7
```

**富途 MCP 能力清单**：
- **查询类**：账户余额、持仓明细、挂单状态、历史成交
- **交易类**：市价单、限价单、撤单
- **监控类**：订单状态轮询、成交回调
- **失败处理**：MCP 调用失败时重试 3 次，仍失败则告警 Sicong

### 4. 双循环工作流

#### 快循环 (System 1)：实时咨询/查询

```python
def workflow_system1_realtime(user_query):
    # 1. Context 层：RAG 检索 + 装配
    context = ContextLoader.load(
        scenario="realtime_consult",
        query=user_query,
        rag_top_k=8
    )

    # 2. Prompt 层：研究咨询 Agent 直接回答
    if is_trading_query(user_query):
        # 交易查询走 Agent 7
        response = Agent7.query_futu(user_query)
    else:
        # 研究咨询走 Agent 1
        response = Agent1.consult(context, user_query)

    # 3. Harness 层：轻量校验（溯源检查）
    if not validate_citations(response, context):
        response = Agent1.retry_with_feedback("引用未匹配原文")

    return response
```

#### 慢循环 (System 2)：定时深度分析 + 共识门禁

```python
def workflow_system2_overnight():
    # 1. 候选股发现（LLM 判断，非量化筛选）
    candidates = Agent1.discover_candidates(market_data, news)

    for ticker in candidates:
        # 2. 情绪抓取 (Agent 2)
        sentiment = Agent2.analyze(ticker)

        # 3. 动态加载上下文
        context = ContextLoader.load(
            scenario="update_l5",
            ticker=ticker,
            extra_data={"sentiment": sentiment}
        )

        # 4. 深度估值分析 (Agent 1) - 跑 CoT DCF
        l2_proposal, l5_proposal = Agent1.analyze(context)

        # 5. Guardrail 第一道：数字溯源校验
        if not validate_data_anchoring(l5_proposal, context):
            l2_proposal, l5_proposal = Agent1.retry("数字未匹配原文页码")

        # 6. L2 落盘（早期阶段需 Sicong 确认，成熟阶段溯源校验后自动写）
        save_to_l2(ticker, l2_proposal)  # 进入待审队列

        # 7. 提交 L5 提案（status: proposed）
        save_proposed_l5(ticker, l5_proposal)

        # 8. 审计委员会 (Agent 3) 多视角审计
        audit = Agent3.audit(l5_proposal, context)

        # 9. IA#1 主提案 (Agent 4)
        ia1_verdict = Agent4.evaluate(l5_proposal, audit, sentiment)

        # 10. IA#2 魔鬼代言人 (Agent 5) 反驳
        ia2_rebuttal = Agent5.attack(ia1_verdict, l5_proposal)

        # 11. Guardrail 第二道：交易一致性校验
        ia1_verdict = validate_trade_consistency(ia1_verdict, l5_proposal)

        # 12. Guardrail 第三道：WACC/g 边界断言
        validate_dcf_bounds(l5_proposal)

        # 13. 共识等级判定 + 推送 Sicong
        consensus = determine_consensus(ia1_verdict, ia2_rebuttal)
        if consensus in ["🟢", "🟡"]:
            push_to_home(ticker, ia1_verdict, ia2_rebuttal, consensus)
        elif consensus == "🟠":
            push_confrontation_to_home(ticker, ia1_verdict, ia2_rebuttal)
        # 🔴 拦截待观望，不推送
```

#### 慢循环 (System 2)：操作复盘（季度/平仓触发）

```python
def workflow_system2_review():
    # 1. 加载 L7 历史操作
    context = ContextLoader.load(scenario="operation_review")

    # 2. 操作分析 Agent (Agent 6) 分析
    review = Agent6.analyze_operations(context)

    # 3. 生成 L3 画像更新提案（提案制，需 Sicong 确认）
    if review.has_blindspot_proposal:
        save_proposed_l3_update(review.profile_update_proposal)
        push_to_home("画像更新提案", review.blindspot_proposal)

    # 4. 季度复盘报告
    save_quarterly_review(review.quarterly_review)
```

#### 慢循环 (System 2)：交易执行（共识通过 + Sicong 确认后）

```python
def workflow_system2_execute_trade(consensus_verdict, sicong_confirmation):
    # 1. Harness 门禁校验
    if not sicong_confirmation:
        return {"error": "未经 Sicong 确认，拒绝执行"}

    if consensus_verdict["consensus_level"] in ["🟠", "🔴"]:
        return {"error": "共识等级不足，拒绝执行"}

    # 2. 高风险二次确认
    if has_high_risk_flags(consensus_verdict):
        if not sicong_confirmation.get("high_risk_confirmed"):
            return {"error": "高风险操作未二次确认，默认取消"}

    # 3. 紧急熔断检查
    if is_emergency_stop_loss(consensus_verdict):
        push_emergency_alert(consensus_verdict)
        # 无需共识投票，直接推送红色硬止损警报

    # 4. 富途 MCP 下单
    order_result = Agent7.execute_trade(consensus_verdict)

    # 5. L7 自动写入
    save_to_l7(order_result)

    # 6. 订单状态监控
    monitor_order_status(order_result["order_id"])
```

---

## 五、 业务生命周期设计

### 5.1 未买前：预测与准入 (Pre-Purchase)
- **买什么**：Agent 1 通过 LLM 判断候选股（非量化筛选），估值具备高安全边际
- **为什么**：Agent 1 提炼核心投资假设（Thesis）记录于 L5
- **怎么买**：Agent 4 计算安全边际，设定"买入击球区"与资金建仓步长
- **数据落盘**：核心假设与合理买入边界记录在 `L5-judgments/[Ticker]-judgment.md`

### 5.2 已买后：追踪与预警 (Post-Purchase)
- **知行合一追踪**：Sicong 录入交易后（Agent 7 执行），个股自动转为"持仓中 (Holding)"状态
- **锁定假设警报线 (L6)**：锁定买入时承诺的财务假设，如营收增速必须 > 15%、毛利率降幅不超过 2%
- **买了后做什么**：设定止盈止损策略，持续监控财报与电话会
- **出现变化做什么**：假设被证伪或估值飘移超限时，输出明确的操作预警与建议（加仓/减仓/清仓）

### 5.3 卖出操作完整设计 (Sell Operations)
卖出分**系统主动触发**与 **Sicong 主动发起**两类，均经过共识门禁。

**系统主动触发卖出的 4 种场景：**

| 触发类型 | 触发条件 | 建议操作 |
|---|---|---|
| **止损触发** | 价格跌破设定止损线（如 -12%） | 建议立即清仓 |
| **假设断裂** | 财报指标跌破买入红线（如营收增速 < 10%） | 建议减仓/清仓 |
| **止盈触发** | 价格超过估值中枢 30%+，进入高估区间 | 建议分批止盈 |
| **仓位失衡** | 大涨导致单股仓位超出上限 | 建议减仓至上限内 |

**紧急熔断例外**：价格跌破止损线超过 5%，无需共识投票，直接推送红色硬止损警报，要求 Sicong 即时确认。

---

## 六、 Sicong 强纠错保护机制

### 高风险操作二次确认门禁（默认选项为"取消执行"）：
- 追高：价格高于估值中枢 15%+ 仍要买入
- 超仓：单股仓位超出设定上限
- 亏损加仓：持仓亏损 > 8% 还选择加仓
- 极度恐慌期操作（VIX > 30）

### Sicong 个人画像盲区检测（`L3-profile/investor-profile.md`）：
- 包含：资金规模、风险边界、持仓上限、投资风格、历史盲区清单
- 首次启动时由 Investment Advisor 主动发起**对话式问卷**采集
- Agent 6 发现新盲区时自动生成"画像更新提案"，Sicong 确认后追加

### 操作纪律评分系统：
- 每次遵循系统建议 → +1分
- 每次被警告仍坚持 → -1分，记录案例及后续结果
- 定期向 Sicong 报告"本月操作纪律评分"与改进建议

---

## 七、 人工确认门禁完整清单

| # | 确认触发条件 | 频率 | 严重程度 |
|---|---|---|---|
| 1 | L1 原始素材入库确认（早期阶段） | 每次 | ⚠️ 普通 |
| 2 | L2 原子事实确认（早期阶段） | 每次 | ⚠️ 普通 |
| 3 | 股票晋级核心池 A（B→A 提案） | 每周 0-3次 | ⚠️ 普通 |
| 4 | Investment Advisor 给出买入建议（共识 ≥ 🟡） | 每周 0-5次 | ⚠️ 普通 |
| 5 | L5 估值模型参数调整提案（财报后重算） | 每季度/每家 | ⚠️ 普通 |
| 6 | 持仓假设断裂 → 减仓/止损建议 | 不定期 | 🔴 重要 |
| 7 | 高风险操作二次确认门禁（Sicong 主动触发） | 触发时 | 🔴 重要 |
| 8 | Sicong 个人画像更新提案（Agent 6 发现新盲区） | 不定期 | ⚠️ 普通 |
| 9 | L4 关联网络更新提案 | 不定期 | ⚠️ 普通 |
| 10 | L6 监控规则更新提案 | 不定期 | ⚠️ 普通 |
| 11 | 宏观乘数矩阵调整提案（宏观重大转折） | 每月 0-1次 | ⚠️ 普通 |

---

## 八、 Obsidian Vault 存储目录结构

```
touzi-agent-vault/
├── _inbox/                       # L1 原始痕迹（手动投喂区：PDF财报/分析网页/纪要）
├── L2-facts/                     # L2 原子事实
│   └── [Ticker]-facts.md
├── L3-profile/                   # L3 身份画像
│   ├── investor-profile.md       # Sicong 投资画像（资金/风险边界/盲区清单/操作纪律评分）
│   ├── persona-buffett.md        # 巴菲特模型（护城河、安全边际、DCF 现金流审计）
│   ├── persona-druckenmiller.md  # 德鲁肯米勒模型（动量趋势、流动性驱动、快速纠错）
│   ├── persona-serenity.md       # 白毛股神模型（产业链卡脖子瓶颈选股审计）
│   └── persona-sun.md            # 孙宇晨模型（叙事泡沫反向探测，FOMO 预警）
├── L4-relations/                 # L4 关联网络
│   ├── macro-multipliers.md      # 宏观传导乘数矩阵
│   └── supply-chain-[Sector].md  # 产业链上下游依赖图谱
├── L5-judgments/                 # L5 心智判断
│   └── [Ticker]-judgment.md      # 估值 + 买入假设 + 操作建议 + 大佬审计
├── L6-alerts/                    # L6 监控规则
│   └── [Ticker]-alerts.md        # 估值偏离阈值、假设红线、止盈止损线
├── L7-actions/                   # L7 行动记录
│   └── trades.md                 # 每笔操作日志（含复盘评价与经验教训）
├── _home.md                      # Sicong 日常视图（Dataview）
├── _views/                       # 视图目录
│   └── dashboard.md              # 仪表盘视图
├── harness/                      # Harness 层
│   ├── permissions.md            # 写入门禁权限表
│   ├── workflows/                # 工作流定义
│   └── scripts/
│       ├── guardrail_runner.py   # Guardrails 执行器
│       └── vault_check.py        # Vault 自检脚本
├── proposals/                    # 待审核提案临时区（PROP-*）
└── archive/                      # 历史提案决策归档日志
```

---

## 九、 Web 控制台核心功能

1. **每日早报推送**：Investment Advisor 主动汇报今日 3 件最重要的事（需处理的提案/市场异动/持仓预警）
2. **共识标签可视化**：每张提案卡片显示 🟢🟡🟠🔴 共识等级及各大脑的投票原因
3. **卖出建议专栏**：独立展示止损/止盈/假设断裂触发的卖出建议，明确呈现"系统建议 vs 你的成本价 vs 当前市价"三者关系
4. **操作纪律看板**：展示 Sicong 本月操作纪律评分及历史遵从率趋势图
5. **画像盲区警报区**：Sicong 个人盲区防线检测结论固定显示在审批页顶部，优先于大佬审计意见
6. **富途账户集成**：实时展示账户余额、持仓明细、挂单状态
7. **趋势预测面板**：Agent 1 的趋势预测结果展示，含置信度与关键假设

---

## 十、 落地与自检清单 (Verification Spec)

当新规格书投入物理实现时，开发人员必须在 `harness/scripts/vault_check.py` 中编码实现以下断言：

1. **断链检测**：扫描 `L5-judgments/` 中的所有 Ticker 提案，确保其引用的 `L2-facts` 文件物理存在
2. **门禁强验证**：测试通过模拟恶意的 LLM 响应，试图直接通过 API 修改 `L5-judgments/` 中的 `status: approved`，检查 Harness 是否能正确拦截并报错
3. **WACC 边界断言**：Agent 1 导出的估值中，折现率 WACC 必须在 $5.0\% \sim 15.0\%$ 之间，永续增长率 $g$ 必须在 $0.0\% \sim 3.0\%$ 之间，超出范围一律拦截
4. **溯源锚点验证**：所有 L2 事实必须包含 `<- [文件名#页码]` 锚点，且锚点指向的源文件必须在 Context 中存在
5. **共识等级一致性**：推送 Sicong 的提案，其共识等级必须与 IA#1/IA#2 输出一致
6. **富途 MCP 连通性**：交易执行前验证富途 MCP 连接正常，查询/交易/监控三个通道可用
7. **L7 即时写入验证**：交易成交后 L7 必须在 1 秒内追加记录，延迟超时告警
8. **画像提案 Diff 格式验证**：Agent 6 生成的 L3 画像更新提案必须为标准 Diff 格式，可被 `git apply` 解析

---

## 附录：与 V1.5 / V2 的差异说明

| 维度 | V1.5 | V2 | V3（本规格） |
|---|---|---|---|
| **架构模型** | 6 Agent + L1-L7 | 三层 + L1-L7 | 同心圆三层 + 双循环 + L1-L7 |
| **Agent 数量** | 6 | 5 | 7 |
| **量化筛选** | Python 量化初筛 | 引用但未详述 | 移除，改用 LLM 判断 |
| **趋势预测** | 无 | 无 | Agent 1 新增趋势预测能力 |
| **操作分析** | 无 | 无 | Agent 6 新增（分析/总结/画像优化） |
| **富途集成** | 无 | 无 | Agent 7 + 富途 MCP（查询/交易/监控） |
| **写入门禁** | 简单分层 | 固定权限表 | 分阶段权限（早期全确认，成熟后放松） |
| **双循环** | 无 | 无 | System 1 快循环 + System 2 慢循环 |
| **Guardrails** | 无 | 三道防线 | 三道防线（保留并细化） |
| **共识门禁** | 4 级共识 | 简化 | 4 级共识（保留） |
