# 投资研究 AI 系统规格说明书 (V3.1 - 同心圆三层 + 双循环 + L1-L7 + 产业链卡点研究方法论)

- **日期**: 2026-06-18
- **状态**: Proposed (V3.1 — 在 V3 基础上新增产业链卡点研究方法论、证据等级体系、五段式研究流程、防幻觉检查)
- **核心定位**: 针对 **Sicong** 的私人投资教练 Agent。主动给出"买什么、为什么、怎么买、买了后做什么、变化后做什么、何时卖"的全生命周期决策，并通过**双 Investment Advisor 内部辩论**过滤低质建议，再推送给 Sicong 确认。
- **技术栈**: Obsidian Vault（唯一真相存储）+ Python（Agent / RAG / Guardrail 后端）+ Web 前端
- **架构模型**: 同心圆三层（Prompt / Context / Harness）+ 双循环执行（System 1 快循环 / System 2 慢循环）+ L1-L7 数据地基 + 产业链卡点研究方法论

---

## V3.1 相对 V3 的核心变化

| 变化项 | V3 | V3.1 |
|---|---|---|
| **研究方法论** | 无系统化方法论 | 新增五段式产业链卡点研究流程 |
| **证据等级** | 无 | L2 事实必须标注 A/B/C/D 证据等级 |
| **底层逻辑** | DCF 估值为主 | 新增底层逻辑三问（需求/瓶颈/映射） |
| **产业链拆解** | 无 | L0-L4 五层产业链拆解框架 |
| **公司分类** | 无标准 | 重点线索 / 观察线索 / 暂不适合 |
| **研究目标** | 投资建议 | **研究线索优先，不是投资建议** |
| **防幻觉** | 溯源校验 | 新增防幻觉检查表（独立 Guardrail） |
| **红队证伪** | IA#2 魔鬼代言人 | 新增研究阶段红队证伪流程 |
| **特殊信源** | 无 | 老黄/孙哥/特朗普 D 级信源可作线索 |

---

## 架构概览：同心圆三层 + 双循环 + L1-L7 + 研究方法论

```
┌─────────────────────────────────────────────────────────────┐
│  【Harness 外层】运行保障与优化闭环                              │
│  ├─ 工作流编排 (workflows/)                                    │
│  ├─ Guardrails 四道防线 (溯源/边界/一致性/防幻觉)  ← V3.1 新增  │
│  ├─ 写入门禁 (permissions.md) — 分阶段权限                      │
│  ├─ 富途 MCP 桥接 (查询/交易)                                  │
│  └─ 监控与可观测性                                              │
│                          ↕ 调度·约束·保障                       │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  【Context 中层】信息供给与知识基础                        │   │
│  │  ├─ RAG 混合检索 (Dense + Sparse + RRF + Rerank)       │   │
│  │  ├─ 情绪数据管道 (Sentiment)                            │   │
│  │  ├─ 证据等级标注 (A/B/C/D)  ← V3.1 新增                  │   │
│  │  ├─ Context 装配矩阵 (按场景动态组装)                    │   │
│  │  └─ 上下文压缩与长度控制                                 │   │
│  │                          ↕ 检索·装配·注入                 │   │
│  │  ┌───────────────────────────────────────────────┐    │   │
│  │  │  【Prompt 内层】7 个 Agent 的 6P 大脑             │    │   │
│  │  │  ├─ Agent 1: 研究咨询 Agent (五段式研究流程) ←增强│    │   │
│  │  │  ├─ Agent 2: 情报分析 Agent (Sentiment)         │    │   │
│  │  │  ├─ Agent 3: 审计委员会 (L0-L4 产业链拆解) ←增强  │    │   │
│  │  │  ├─ Agent 4: IA#1 主提案方                      │    │   │
│  │  │  ├─ Agent 5: IA#2 魔鬼代言人 (含红队证伪) ←增强   │    │   │
│  │  │  ├─ Agent 6: 操作分析 Agent (新增)               │    │   │
│  │  │  └─ Agent 7: 交易执行 Agent (富途 MCP 桥接)      │    │   │
│  │  └───────────────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────────┘   │
│                          ↕ 读取·写入·提案                       │
│  ══════════════ 【L1-L7 唯一真相 Vault】 ══════════════       │
│  L1 原始痕迹 │ L2 原子事实(含证据等级) │ L3 身份画像           │
│  L4 关联网络(含产业链图谱) │ L5 心智判断 │ L6 监控规则         │
│  L7 行动记录                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 零、 产业链卡点研究方法论（V3.1 核心新增）

### 0.1 研究哲学

**核心原则：先拆产业链，再找卡点，最后映射公司。**

1. **研究线索优先**：最终目标是输出研究线索，不是投资建议。投资建议需经共识门禁后才能推送。
2. **证据强制溯源**：所有关键数字必须写来源、日期和证据等级。没有来源的内容标为"待核验"，不能写成结论。
3. **公司分类标准**（只能用以下三类）：
   - **重点线索**：证据充分，业务纯度高，值得深度跟踪
   - **观察线索**：部分证据支撑，需补充数据验证
   - **暂不适合作为案例**：证据不足或业务纯度低

### 0.2 底层逻辑三问

任何研究必须先回答三个底层问题：

| 问题 | 核心检验点 |
|---|---|
| **1. 需求是否真实？** | 这个赛道的需求来自谁？是否有公告、财报、招标、资本开支、政策或行业数据支撑？需求是短期脉冲，还是可能持续 1-3 年？ |
| **2. 瓶颈在哪里？** | 哪一层扩产最慢？哪一层替代最难？哪一层客户认证周期最长？哪一层良率、设备、材料、工艺或供应商数量构成硬约束？ |
| **3. 股票映射是否有证据？** | 哪些 A 股公司真实覆盖这个卡点？相关业务是否有收入、订单、客户、产能、认证、募投或公告证据？是主营业务，还是边缘业务/概念蹭热点？ |

### 0.3 证据等级体系

| 等级 | 来源类型 | 定位 | 使用规则 |
|---|---|---|---|
| **A级** | 公告、年报、半年报、招股书、交易所互动、招标/中标公告 | 核心证据 | 可作为结论支撑 |
| **B级** | 机构调研、管理层交流、权威行业数据、客户供应链公开信息 | 辅助判断 | 可辅助判断，不可单独作结论 |
| **C级** | 券商研报、媒体报道、行业文章 | 参考线索 | 只能作为参考，需 A/B 级交叉验证 |
| **D级** | 社交媒体、KOL、论坛、传闻 | 线索 | 只能作为线索，不能当结论。**例外：老黄（黄仁勋）、孙哥（孙宇晨）、特朗普的公开发言可作为有效线索** |

### 0.4 五段式研究流程

#### 第一段：产业链拆解（先画地图，不先列股票）

按 **L0-L4** 拆解目标赛道产业链：

| 层级 | 定义 | 关注点 |
|---|---|---|
| **L0 终端需求** | 最终应用场景 | 需求真实性 |
| **L1 系统/集成** | 系统方案、整机、平台、交付、认证、客户导入 | 认证周期、客户壁垒 |
| **L2 核心部件** | 决定性能或交付的关键部件、技术、良率、产能 | 良率、产能瓶颈 |
| **L3 材料/工艺/设备** | 材料、工艺、设备、检测、国产化、扩产周期、设备约束 | 扩产周期、设备约束 |
| **L4 上游资源** | 原材料、能源、资源、基础设备 | 供给稳定性 |

**输出**：10-20 个候选卡点线索，并说明为什么可能影响产业链交付。

#### 第二段：证据复筛（用公告和财报穿透概念）

对候选公司逐个检查：
1. 近 4 个季度主营业务是否真的与卡点环节相关
2. 相关业务收入占比、毛利率、客户、订单、产能是否有公开披露
3. 募投、定增、CapEx、在建工程是否投向该卡点
4. 研报热度只能作为市场关注度线索，不能当作业绩证据

**输出表格**：

| 公司 | 代码 | 对应环节 | 业务纯度 | 公开证据 | 证据等级 | 不能证明什么 | 初步归类 |
|---|---|---|---|---|---|---|---|

*初步归类只能用：重点线索 / 观察线索 / 暂不适合作为案例*

#### 第三段：红队证伪（主动反驳）

对每个"重点线索"做反向审查：
- 大客户是否可能自研、二供、三供？
- 未来 12-18 个月是否可能被新技术路线替代？
- 同行是否可能打价格战？
- 公司收入是否真的来自该卡点，而不是低价值代工或边缘业务？
- 当前市场是否已经充分定价？

**输出表格**：

| 公司 | 最大风险 | 证据能否缓解 | 还缺什么数据 | 风险等级 |
|---|---|---|---|---|

*风险等级只能用：低 / 中 / 高 / 证据不足*

#### 第四段：防幻觉检查

把可能夸大的结论单独拎出来：

| 可能被夸大的结论 | 为什么可能夸大 | 谨慎表达方式 |
|---|---|---|

#### 第五段：最终输出结构

按以下结构输出，适合短视频展示：

1. **产业链卡点地图**（L0-L4 可视化）
2. **候选公司证据表**（含证据等级）
3. **红队反证表**（含风险等级）
4. **未来两个季度跟踪表**（关键催化剂与风险事件时间线）
5. **防幻觉检查表**

---

## 一、 唯一真相：L1-L7 数据层定义与物理结构

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

### 2. L2 原子事实层 (Atomic Facts) — V3.1 增加证据等级
- **物理路径**：`L2-facts/[Ticker]-facts.md`
- **职责**：将 L1 零散表达与财报，抽成可检索、可合并的事实片段
- **Markdown 正文格式**（V3.1 新增证据等级与日期字段）：
    ```markdown
    - [FACT_01cf3] (A级, 2026-06-18) 苹果 2025 年第四季度服务业营收为 250 亿美元，同比增长 12%。<- [2025-Q4-Earnings.pdf#Page_12]
    - [FACT_9a2ef] (B级, 2026-06-18) 库克在 Q4 电话会中指出，AI 智能体的变现周期可能比预期更长。<- [2025-Q4-Call-Transcript.md#Page_3]
    - [FACT_xxxxx] (待核验) 据传苹果正在研发折叠屏 iPhone。<- [社交媒体线索]
    ```
- **证据等级标注规则**：
    - 每条事实必须标注证据等级（A/B/C/D/待核验）
    - D 级信源中，老黄（黄仁勋）、孙哥（孙宇晨）、特朗普的公开发言可作有效线索
    - 无来源的事实必须标为"待核验"，不能写入结论性表述

### 3. L3 身份画像层 (Profiles)
包含 Sicong 自己的画像与大师决策因子包。
- **物理路径**：
    - Sicong 个人画像：`L3-profile/investor-profile.md`
    - 巴菲特画像：`L3-profile/persona-buffett.md`
    - 德鲁肯米勒画像：`L3-profile/persona-druckenmiller.md`
    - 白毛股神画像：`L3-profile/persona-serenity.md`（V3.1：内置 L0-L4 产业链拆解框架）
    - 孙宇晨画像：`L3-profile/persona-sun.md`
- **大师画像结构 (以白毛股神为例，V3.1 增强)**：
    ```yaml
    name: 白毛股神 (Serenity)
    load_trigger: on_supply_chain_audit
    core_framework: L0-L4_supply_chain_decomposition
    audit_checklist:
      - "L0 终端需求是否真实？持续 1-3 年？"
      - "L1 系统/集成的客户认证周期多长？"
      - "L2 核心部件的良率和产能瓶颈在哪？"
      - "L3 材料/工艺/设备的扩产周期多长？"
      - "L4 上游资源的供给稳定性如何？"
    forbidden_rules:
      - "严禁无证据映射公司到卡点环节"
      - "严禁将 D 级信源当结论（老黄/孙哥/特朗普除外）"
      - "严禁研报热度当作业绩证据"
    ```

### 4. L4 关联网络层 (Relations) — V3.1 增加产业链图谱
- **物理路径**：`L4-relations/`
    - 宏观传导乘数矩阵：`L4-relations/macro-multipliers.md`
    - 产业链上下游依赖图谱：`L4-relations/supply-chain-[Sector].md`
    - **V3.1 新增：产业链卡点图谱**：`L4-relations/bottleneck-map-[Sector].md`
- **产业链卡点图谱格式**：
    ```markdown
    # [赛道名称] 产业链卡点图谱

    ## L0 终端需求
    - 需求来源：[描述] (证据等级, 日期)
    - 持续性判断：1-3年 / 短期脉冲

    ## L1 系统/集成
    - 关键玩家：[公司列表]
    - 认证周期：[描述] (证据等级)

    ## L2 核心部件
    - 卡点环节：[描述]
    - 良率/产能瓶颈：[描述] (证据等级)

    ## L3 材料/工艺/设备
    - 扩产周期：[描述]
    - 设备约束：[描述] (证据等级)

    ## L4 上游资源
    - 供给稳定性：[描述] (证据等级)

    ## 候选卡点线索 (10-20个)
    1. [卡点1] - 为什么影响交付
    2. [卡点2] - 为什么影响交付
    ...
    ```

### 5. L5 心智判断层 (Judgments)
- **物理路径**：`L5-judgments/[Ticker]-judgment.md`
- **Frontmatter 格式**：
    ```yaml
    ticker: AAPL
    last_updated: 2026-06-18
    status: proposed | approved
    research_classification: 重点线索 | 观察线索 | 暂不适合  # V3.1 新增
    ```
- **正文结构**（V3.1 增加研究线索部分）：
    ```markdown
    # 研究线索 (Research Lead) — V3.1 新增
    ## 底层逻辑三问
    1. 需求是否真实：[分析] (证据等级)
    2. 瓶颈在哪里：[分析] (证据等级)
    3. 股票映射证据：[分析] (证据等级)

    ## 产业链定位
    - 对应环节：L2 核心部件
    - 业务纯度：[分析]
    - 公开证据：[列表]

    # 核心论点 (Thesis)
    [描述]

    # 估值区间 (Valuation)
    - 悲观 DCF: [价格]
    - 中性 DCF (Base): [价格]
    - 乐观 DCF: [价格]

    # 买入假设与建仓方案
    [描述]
    ```

### 6. L6 监控规则层 (Alerts)
- **物理路径**：`L6-alerts/[Ticker]-alerts.md`
- **V3.1 新增**：跟踪表格式
    ```markdown
    # 未来两个季度跟踪表 — V3.1 新增
    | 事件 | 预期时间 | 类型(催化剂/风险) | 关联假设 | 证据等级 |
    |---|---|---|---|---|
    | Q3 财报发布 | 2026-10 | 催化剂 | 营收增速 > 10% | A级 |
    | 竞品发布会 | 2026-09 | 风险 | 技术路线替代 | C级 |
    ```

### 7. L7 行动记录层 (Action Logs)
- **物理路径**：`L7-actions/trades.md`
- **格式**：（同 V3，无变化）

---

## 二、 第一层：Prompt Engineering (7 个 Agent 的 6P 设计)

### Agent 1：研究咨询 Agent (Deep RAG Analyst 增强) — V3.1 五段式研究流程

| 6P | 定义 |
|---|---|
| **Persona** | CFA 股票估值专家 + 投研顾问 + 产业链分析师。具备财报分析、DCF 估值、行业趋势预判、**L0-L4 产业链拆解**能力 |
| **Purpose** | ① 从 L1 及外部资料提炼 L2 原子事实（**含证据等级**）② 执行**五段式产业链卡点研究流程** ③ 计算 DCF/PE-Band 估值 ④ 输出 L5 判断提案（**含研究线索分类**）⑤ 回答 Sicong 实时咨询 ⑥ 基于历史数据与行业逻辑预测未来趋势 |
| **Process** | **五段式研究流程**：<br>1. **产业链拆解**：按 L0-L4 拆解目标赛道，输出 10-20 个候选卡点线索<br>2. **证据复筛**：用公告和财报穿透概念，输出候选公司证据表（含证据等级 A/B/C/D）<br>3. **红队证伪**：对每个"重点线索"做反向审查，输出红队反证表<br>4. **防幻觉检查**：把可能夸大的结论单独拎出来，输出防幻觉检查表<br>5. **最终输出**：产业链卡点地图 + 候选公司证据表 + 红队反证表 + 未来两季度跟踪表 + 防幻觉检查表<br><br>**估值分析**：在 `<analysis_draft>` 中跑 DCF 数学计算<br>**快循环模式**：直接回答用户咨询，引用 L2/L5 事实（含证据等级）<br>**趋势预测**：基于 L2 历史数据 + L4 关联网络，推演 3-6 个月趋势 |
| **Policy** | • 溯源铁律：未在 Context 原文找到的数字必须标 `null`<br>• **证据等级强制**：每条 L2 事实必须标注 A/B/C/D/待核验<br>• **无来源不结论**：无来源内容标"待核验"，不能写成结论<br>• **研究线索优先**：输出研究线索，不是投资建议。投资建议需经共识门禁<br>• **公司分类标准**：只能用 重点线索/观察线索/暂不适合<br>• **D 级信源例外**：老黄/孙哥/特朗普的公开发言可作有效线索<br>• 只提案不落盘：严禁直接改写 L5 `status: approved`<br>• 趋势预测必须标注置信度（高/中/低）和关键假设 |
| **Presentation** | ① `<l2_facts_proposal>` 新原子事实（含证据等级）<br>② `<supply_chain_map>` 产业链卡点地图（L0-L4）<br>③ `<evidence_table>` 候选公司证据表<br>④ `<red_team_table>` 红队反证表<br>⑤ `<tracking_table>` 未来两季度跟踪表<br>⑥ `<anti_hallucination_check>` 防幻觉检查表<br>⑦ `<l5_judgment_proposal>` L5 草稿（`status: proposed`，含研究线索分类）<br>⑧ **快循环**：直接 Markdown 回答 + 引用溯源 + 证据等级<br>⑨ `<trend_forecast>` 趋势预测（含置信度） |
| **Proof** | 输出前自检：所有数字是否有溯源锚点？证据等级是否标注？无来源是否标"待核验"？公司分类是否只用三类？WACC 在 5%-15%？g 在 0%-3%？防幻觉检查表是否完成？ |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：快循环（实时咨询）+ 慢循环（深度分析）

---

### Agent 2：情报分析 Agent (Sentiment Analyst)

| 6P | 定义 |
|---|---|
| **Persona** | 市场情绪分析师 |
| **Purpose** | 批量抓取并分类舆情，计算板块/个股的情绪共识强度，作为 Context 注入其他 Agent。**V3.1：舆情数据自动标注证据等级 C/D** |
| **Process** | 1. 从 Twitter/RSS/财经新闻抓取原始舆情<br>2. Gemini Flash 批量情感分类（看多/看空/中性）<br>3. 聚合计算板块情绪共识强度<br>4. **V3.1：标注证据等级**（财经新闻=C级，社交媒体/KOL=D级）<br>5. **V3.1：特殊信源识别**（老黄/孙哥/特朗普发言单独标记为有效线索）<br>6. 输出结构化情绪数据 |
| **Policy** | • 仅处理公开数据，不存储个人隐私<br>• 情绪数据有时效性，必须标注采集时间<br>• 情绪是参考因子，不是决策依据<br>• **V3.1：D 级信源不能当结论，老黄/孙哥/特朗普除外** |
| **Presentation** | JSON 格式：`{ticker, sentiment_score, volume, sources, collected_at, evidence_level, special_sources[]}` |
| **Proof** | 检查样本量是否足够（< 10 条标记低置信度）。V3.1：证据等级是否标注？特殊信源是否识别？ |

- **模型**：Gemini 1.5 Flash
- **活跃循环**：慢循环（定时批量处理）

---

### Agent 3：审计委员会 (Audit Council) — V3.1 白毛股神采用 L0-L4 拆解

| 6P | 定义 |
|---|---|
| **Persona** | 三脑合一的审计委员会：① 白毛股神（**L0-L4 产业链卡点审计**）② 孙宇晨（叙事泡沫反向探测）③ Sicong 盲区检测器 |
| **Purpose** | 对 Agent 1 的 L5 提案进行多视角审计，找出逻辑软肋、叙事泡沫风险、与 Sicong 历史盲区的冲突 |
| **Process** | 1. 载入 Agent 1 的 L5 提案 + L3 画像 + L4 产业链图谱<br>2. **白毛股神视角（V3.1 增强）**：<br>　• 按 L0-L4 逐层验证产业链拆解是否准确<br>　• L0：需求是否真实？持续 1-3 年还是短期脉冲？<br>　• L1：客户认证周期多长？<br>　• L2：良率和产能瓶颈在哪？<br>　• L3：扩产周期和设备约束如何？<br>　• L4：上游供给稳定性如何？<br>　• 验证公司映射是否有 A/B 级证据支撑<br>3. **孙宇晨视角**：这是叙事泡沫还是真实基本面驱动？FOMO 信号强度？<br>4. **盲区检测**：与 `L3-profile/investor-profile.md` 中的历史盲区清单比对<br>5. 输出三份审计意见 + 综合风险评级 |
| **Policy** | • persona 防火墙：装载大师大脑时必须标注「以下为 \<name\> 视角的模拟」，用完交还决策权<br>• 严禁静默把 persona 结论写进 L5 当成 Sicong 的判断<br>• 三脑必须独立输出，不得互相污染<br>• **V3.1：白毛股神审计必须逐层验证 L0-L4，不得跳过任何层级**<br>• **V3.1：公司映射必须有 A/B 级证据，C/D 级只能作线索** |
| **Presentation** | ① `<serenity_audit>` 白毛股神审计意见（含 L0-L4 逐层验证）<br>② `<sun_audit>` 孙宇晨审计意见<br>③ `<blindspot_check>` 盲区检测结果<br>④ `<risk_rating>` 综合风险评级（低/中/高/极高） |
| **Proof** | 自检：三脑是否各自独立输出？是否引用了 L3 画像？盲区比对是否覆盖全部清单？**V3.1：L0-L4 是否逐层验证？公司映射证据等级是否 ≥ B 级？** |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（L5 提案生成后触发）

---

### Agent 4：IA#1 主提案方 (Investment Advisor #1)

| 6P | 定义 |
|---|---|
| **Persona** | 首席投资官 |
| **Purpose** | 整合 Agent 1-3 所有情报（L5 提案 + 情绪 + 审计意见），结合 L3 画像和大师加权因子，生成完整操作建议草案。**V3.1：整合研究线索分类与证据等级** |
| **Process** | 1. 载入 Agent 1 的 L5 提案（含研究线索分类）+ Agent 2 情绪数据 + Agent 3 审计意见<br>2. 读取 `L3-profile/investor-profile.md`（Sicong 画像）和激活的大师画像<br>3. 执行因子衰减计算：$\text{Final Weight} = \text{Raw Weight} \times \text{Attenuator}$<br>4. **V3.1：按证据等级加权**（A级证据权重 1.0，B 级 0.7，C 级 0.4，D 级 0.1）<br>5. 计算安全边际、建仓步长、仓位上限<br>6. 输出买卖/建仓/减仓提案 |
| **Policy** | • 安全边际门禁：现价不低于中性估值 15% 一律 `HOLD`<br>• 个性化强校验：Sicong 画像含"对回撤敏感"→ 单股上限从 15% 衰减至 8%<br>• 高风险操作标记：追高/超仓/亏损加仓/VIX>30 需二次确认<br>• **V3.1：研究线索为"暂不适合"的标的，一律输出 `HOLD`**<br>• **V3.1：核心证据不足（无 A 级证据）的标的，仓位上限衰减 50%** |
| **Presentation** | JSON：`{action, ticker, target_price, position_size, rationale, risk_flags, consensus_level, research_classification, evidence_summary}` |
| **Proof** | 自检：安全边际是否满足？仓位是否超限？是否与盲区冲突？**V3.1：研究线索分类是否合理？证据等级加权是否正确？** |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（审计完成后触发）

---

### Agent 5：IA#2 魔鬼代言人 (Investment Advisor #2) — V3.1 整合红队证伪

| 6P | 定义 |
|---|---|
| **Persona** | 风控官 / 魔鬼代言人 / 红队证伪官 |
| **Purpose** | 强行攻击 Agent 4 的提案，找出逻辑和估值假设的软肋，达成共识才推送 Sicong。**V3.1：整合研究阶段红队证伪逻辑** |
| **Process** | 1. 载入 Agent 4 的提案 + Agent 1 的 DCF 假设 + 红队反证表<br>2. 锁定乐观因子（永续增长率 $g > 2.5\%$，折现率 $WACC < 7.5\%$）<br>3. 强行运行悲观参数 DCF，输出对比差值<br>4. 逐条审查：假设是否成立？忽略的风险？叙事泡沫？盲区冲突？<br>5. **V3.1 红队证伪增强**：<br>　• 大客户是否可能自研、二供、三供？<br>　• 未来 12-18 个月是否可能被新技术路线替代？<br>　• 同行是否可能打价格战？<br>　• 公司收入是否真的来自该卡点，而不是低价值代工或边缘业务？<br>　• 当前市场是否已经充分定价？<br>6. 输出共识等级 |
| **Policy** | • 必须反驳：禁止附和 IA#1，必须指出至少 2 点核心反驳<br>• 反驳必须含差值影响百分比 `rebuttal_impact_pct`<br>• 🔴 强烈反对时暂不推送，等待新数据窗口重新评估<br>• **V3.1：红队证伪必须覆盖 5 个标准问题**<br>• **V3.1：风险等级为"高"或"证据不足"时，自动降级共识等级** |
| **Presentation** | JSON：`{verdict, rebuttals[], rebuttal_impact_pct, consensus_level, conditions[], red_team_risks[], risk_level}` |
| **Proof** | 自检：是否至少 2 点反驳？差值百分比是否计算？共识等级是否合理？**V3.1：红队 5 问是否全覆盖？风险等级是否影响共识？** |

- **模型**：Claude 3.5 Sonnet
- **活跃循环**：慢循环（IA#1 提案后触发）

#### 四级共识等级与推送策略（V3.1 增加证据等级影响）

| 共识等级 | 条件 | 推送行为 | 标签 |
|---|---|---|---|
| 🟢 **高共识** | IA#1 与 IA#2 完全同意，**且核心证据 ≥ A 级** | 立即推送，强烈建议执行 | `强推` |
| 🟡 **有条件共识** | 同意但 IA#2 附加条件，**或核心证据为 B 级** | 推送，同时展示附加条件与风险提示 | `有条件同意` |
| 🟠 **存在争议** | IA#2 有重大异议，**或核心证据仅 C 级** | 两方观点同时呈现，Sicong 最终裁决 | `存在争议` |
| 🔴 **强烈反对** | IA#2 发现致命缺陷，**或核心证据不足/仅 D 级** | 暂不推送，等待新数据窗口重新评估 | `拦截待观望` |

---

### Agent 6：操作分析 Agent (新增)

| 6P | 定义 |
|---|---|
| **Persona** | 投资行为分析师 + 画像优化顾问 |
| **Purpose** | ① 分析 Sicong 的历史操作（L7）② 总结操作模式与纪律遵从率 ③ 发现认知盲区 ④ 生成 L3 画像优化提案 ⑤ 提供行为修正建议 |
| **Process** | 1. 读取 `L7-actions/trades.md` 近 30/90/180 天操作记录<br>2. 对比"系统建议 vs 实际操作"，计算纪律遵从率<br>3. 识别操作模式：追高/恐慌卖/一次性重仓/不按分批等<br>4. 与 `L3-profile/investor-profile.md` 盲区清单比对，发现新盲区<br>5. 生成画像更新提案（L3 提案制，必须 Sicong 确认）<br>6. 输出行为修正建议 + 季度复盘报告 |
| **Policy** | • L3 提案制铁律：只能生成画像更新提案，严禁直接改写 L3<br>• 客观不评判：分析行为模式时不带道德判断，只陈述事实与统计<br>• 盲区发现必须有 L7 数据支撑，不得臆测<br>• 复盘报告必须含"遵循系统 vs 自行决策"胜率对比 |
| **Presentation** | ① `<behavior_analysis>` 操作模式分析<br>② `<blindspot_proposal>` 新盲区发现提案<br>③ `<profile_update_proposal>` L3 画像更新提案（Diff 格式）<br>④ `<quarterly_review>` 季度复盘报告 |
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

### 1. RAG 物理切片与结构化清洗

| 数据类型 | 清洗规则 | 切片策略 |
|---|---|---|
| **财报 PDF** | `pdfplumber` 识别表格区域，转 Markdown Table / CSV | 1500 tokens/块，overlap 200。表格完整保留在一个 Chunk |
| **电话会纪要** | 按"发言人-答复"问答对切片 | 每个 QA 块绑定 metadata：`{ticker, date, speaker, type:qa_call}` |
| **新闻/舆情** | 去重 + 去噪 + **V3.1：标注证据等级 C/D** | 500 tokens/块，按时间窗口聚合 |
| **公告/年报** | **V3.1 新增**：按章节切片，标注证据等级 A | 按章节为最小单元（经营分析/财务报告/公司治理） |
| **L1-L7 Markdown** | 直接按 Frontmatter 分块 | 按层级行为最小单元 |

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
   V3.1：证据等级加权（A级 Chunk +2, B级 +1, C级 0, D级 -1）
   阈值拦截 < 5分
        │
   精炼 Top N (N≤8, ≤6k tokens)
        ▼
  注入 Agent Context
```

**V3.1 Re-rank 增强**：证据等级影响 Chunk 排序，A级证据 Chunk 优先注入。

### 3. 动态 Context 装配矩阵

| 触发场景 | 触发源 | 动态加载的 Vault 上下文组合 |
|---|---|---|
| **快循环：实时咨询** | Sicong 提问 | RAG Top 8 Chunks + L5 判断 + L3 画像 |
| **慢循环：产业链研究** | Sicong 指定赛道 | L4 产业链图谱 + RAG 检索（按 L0-L4 分层检索）+ L2 事实（按证据等级排序） |
| **慢循环：inbox 提取 L2** | 定时任务 | _inbox/ 未处理文件 + L2 增量比对 |
| **慢循环：更新 L5 提案** | 新增 L2 事实 | L2 全集 + 无风险利率 + 旧 L5 |
| **慢循环：共识门禁** | L5 提案生成 | L5 + 审计意见 + L3 大师画像 + 情绪 + **V3.1：红队反证表** |
| **慢循环：操作复盘** | 季度/平仓 | L7 30/90/180 天 + L3 盲区清单 |
| **快循环：交易查询** | Sicong 查询 | 富途 MCP 实时 + L7 近期记录 |
| **慢循环：交易执行** | 共识+确认 | 交易指令 + L5 + L6 假设红线 |

### 4. Context 长度控制与自适应压缩

```python
def assemble_context(ticker, query, scenario):
    # Tier 1: 核心指标与画像 (强制不压缩，100% 导入)
    tier1 = load_core_metrics(ticker) + load_profile()

    # Tier 2: RAG 混合检索 (动态压缩到 6k tokens)
    # V3.1：按证据等级排序，A级优先保留
    tier2 = run_hybrid_retrieval(ticker, query, sort_by_evidence=True)

    # Tier 3: 历史行动记录 (聚合摘要，非全量)
    tier3 = get_aggregated_historical_logs(ticker, days=30)

    # V3.1：产业链图谱（研究场景才加载）
    if scenario in ["supply_chain_research", "update_l5"]:
        tier_chain = load_supply_chain_map(ticker)

    return compress_and_assemble(tier1, tier2, tier3, max_tokens=12000)
```

---

## 四、 第三层：Harness Engineering (工作流·门禁·Guardrails·富途 MCP)

### 1. 物理写入门禁权限表 (`harness/permissions.md`)

| 目标数据层 | Agent 权限 | 早期阶段（当前） | 成熟阶段（后续） |
|---|---|---|---|
| **L1 `_inbox/`** | 读/写 | **Sicong 确认入库** | 零确认（直接追加） |
| **L2 `L2-facts/`** | 读/写 | **溯源校验 + 证据等级标注 + Sicong 确认** | 溯源校验 + 抽样审阅 |
| **L3 `L3-profile/`** | 提案制 | **强确认**（Sicong 拍板） | 强确认（始终需要） |
| **L4 `L4-relations/`** | 提案制 | **强确认**（Sicong 拍板） | 抽样确认 |
| **L5 `L5-judgments/`** | 提案制 | **强确认**（Sicong 改 `approved` 才合并） | 强确认（始终需要） |
| **L6 `L6-alerts/`** | 提案制 | **强确认**（Sicong 拍板） | 抽样确认 |
| **L7 `L7-actions/`** | 读/写 | 零确认（机械记录） | 零确认 |

### 2. 四道 Guardrails 金融专防 — V3.1 新增第四道防幻觉

| 防线 | 名称 | 校验内容 | 失败处理 |
|---|---|---|---|
| **第一道** | 正则溯源校验器 | 匹配 `<- [文件名#页码]`，验证源文件和页码在 Context 中存在 | 自检重试 1 次，仍失败则拦截 |
| **第二道** | 交易一致性校验 | `BUY` 时 `target_price ≤ DCF中性 × 0.85`（15% 安全边际） | 驳回为 `HOLD` |
| **第三道** | WACC/g 边界断言 | WACC ∈ [5.0%, 15.0%]，g ∈ [0.0%, 3.0%] | 超范围拦截，要求重算 |
| **第四道** | **防幻觉检查（V3.1 新增）** | ① 无来源结论拦截（必须标"待核验"）② D 级信源当结论拦截（老黄/孙哥/特朗普除外）③ 研报热度当业绩证据拦截 ④ 公司分类非三类标准拦截 | 拦截，要求修正表达 |

```python
# V3.1 第四道防线：防幻觉检查
def validate_anti_hallucination(output_text, l2_facts):
    # 1. 检查无来源结论
    conclusions = extract_conclusions(output_text)
    for conclusion in conclusions:
        if not has_source_anchor(conclusion):
            if "待核验" not in conclusion:
                return False, "存在无来源结论未标注'待核验'"

    # 2. 检查 D 级信源当结论
    d_level_facts = [f for f in l2_facts if f.evidence_level == "D"]
    special_sources = ["老黄", "黄仁勋", "孙哥", "孙宇晨", "特朗普"]
    for fact in d_level_facts:
        if fact.source not in special_sources:
            if is_used_as_conclusion(fact, output_text):
                return False, f"D 级信源 '{fact.source}' 被当作结论"

    # 3. 检查研报热度当业绩证据
    if "研报热度" in output_text and "业绩" in output_text:
        if not has_ab_level_evidence(output_text):
            return False, "研报热度被当作业绩证据"

    # 4. 检查公司分类标准
    classifications = extract_classifications(output_text)
    valid_classes = ["重点线索", "观察线索", "暂不适合作为案例", "暂不适合"]
    for cls in classifications:
        if cls not in valid_classes:
            return False, f"公司分类 '{cls}' 不在标准三类中"

    return True, "防幻觉检查通过"
```

### 3. 富途 MCP 集成设计

（同 V3，无变化）

### 4. 双循环工作流

#### 快循环 (System 1)：实时咨询/查询

```python
def workflow_system1_realtime(user_query):
    # 1. Context 层：RAG 检索 + 装配
    context = ContextLoader.load(
        scenario="realtime_consult",
        query=user_query,
        rag_top_k=8,
        sort_by_evidence=True  # V3.1：按证据等级排序
    )

    # 2. Prompt 层：研究咨询 Agent 直接回答
    if is_trading_query(user_query):
        response = Agent7.query_futu(user_query)
    else:
        response = Agent1.consult(context, user_query)

    # 3. Harness 层：轻量校验（溯源 + V3.1 防幻觉）
    if not validate_citations(response, context):
        response = Agent1.retry_with_feedback("引用未匹配原文")
    # V3.1：防幻觉轻量检查
    if not validate_anti_hallucination_light(response):
        response = Agent1.retry_with_feedback("存在无来源结论或D级信源当结论")

    return response
```

#### 慢循环 (System 2)：定时深度分析 + 五段式研究 + 共识门禁

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

        # 4. V3.1 五段式研究流程 (Agent 1)
        # 4.1 产业链拆解 (L0-L4)
        chain_map = Agent1.decompose_supply_chain(ticker, context)
        # 4.2 证据复筛
        evidence_table = Agent1.evidence_screening(chain_map, context)
        # 4.3 红队证伪
        red_team_table = Agent1.red_team_falsification(evidence_table)
        # 4.4 防幻觉检查
        anti_hallucination = Agent1.anti_hallucination_check(evidence_table)
        # 4.5 DCF 估值 + L5 提案
        l2_proposal, l5_proposal = Agent1.analyze_with_research(
            context, chain_map, evidence_table, red_team_table
        )

        # 5. Guardrail 第一道：数字溯源校验
        if not validate_data_anchoring(l5_proposal, context):
            l2_proposal, l5_proposal = Agent1.retry("数字未匹配原文页码")

        # 6. V3.1 Guardrail 第四道：防幻觉检查
        passed, reason = validate_anti_hallucination(l5_proposal, l2_proposal)
        if not passed:
            l5_proposal = Agent1.retry(f"防幻觉检查失败: {reason}")

        # 7. L2 落盘（早期需 Sicong 确认）
        save_to_l2(ticker, l2_proposal)

        # 8. 提交 L5 提案（status: proposed, 含研究线索分类）
        save_proposed_l5(ticker, l5_proposal)

        # 9. 审计委员会 (Agent 3) L0-L4 逐层审计
        audit = Agent3.audit_with_supply_chain(l5_proposal, chain_map, context)

        # 10. IA#1 主提案 (Agent 4) — 按证据等级加权
        ia1_verdict = Agent4.evaluate_with_evidence(
            l5_proposal, audit, sentiment
        )

        # 11. IA#2 魔鬼代言人 (Agent 5) — 含红队 5 问
        ia2_rebuttal = Agent5.attack_with_red_team(
            ia1_verdict, l5_proposal, red_team_table
        )

        # 12. Guardrail 第二道：交易一致性校验
        ia1_verdict = validate_trade_consistency(ia1_verdict, l5_proposal)

        # 13. Guardrail 第三道：WACC/g 边界断言
        validate_dcf_bounds(l5_proposal)

        # 14. 共识等级判定（V3.1：受证据等级影响）+ 推送
        consensus = determine_consensus_with_evidence(
            ia1_verdict, ia2_rebuttal, l5_proposal
        )
        if consensus in ["🟢", "🟡"]:
            push_to_home(ticker, ia1_verdict, ia2_rebuttal, consensus)
        elif consensus == "🟠":
            push_confrontation_to_home(ticker, ia1_verdict, ia2_rebuttal)
        # 🔴 拦截待观望，不推送
```

#### 慢循环 (System 2)：操作复盘（季度/平仓触发）

（同 V3，无变化）

#### 慢循环 (System 2)：交易执行（共识通过 + Sicong 确认后）

（同 V3，无变化）

---

## 五、 业务生命周期设计

### 5.1 未买前：预测与准入 (Pre-Purchase)
- **买什么**：Agent 1 通过 LLM 判断候选股 + **V3.1：五段式产业链研究**
- **为什么**：Agent 1 提炼核心投资假设（Thesis）+ **V3.1：底层逻辑三问**记录于 L5
- **怎么买**：Agent 4 计算安全边际，设定"买入击球区"与资金建仓步长
- **V3.1 研究线索分类**：标的必须分类为"重点线索"才进入买入流程

### 5.2 已买后：追踪与预警 (Post-Purchase)
- **知行合一追踪**：Sicong 录入交易后（Agent 7 执行），个股自动转为"持仓中 (Holding)"状态
- **锁定假设警报线 (L6)**：锁定买入时承诺的财务假设 + **V3.1：未来两季度跟踪表**
- **买了后做什么**：设定止盈止损策略，持续监控财报与电话会
- **出现变化做什么**：假设被证伪或估值飘移超限时，输出明确的操作预警

### 5.3 卖出操作完整设计 (Sell Operations)

**系统主动触发卖出的 4 种场景：**

| 触发类型 | 触发条件 | 建议操作 |
|---|---|---|
| **止损触发** | 价格跌破设定止损线（如 -12%） | 建议立即清仓 |
| **假设断裂** | 财报指标跌破买入红线（如营收增速 < 10%） | 建议减仓/清仓 |
| **止盈触发** | 价格超过估值中枢 30%+，进入高估区间 | 建议分批止盈 |
| **仓位失衡** | 大涨导致单股仓位超出上限 | 建议减仓至上限内 |

**V3.1 新增触发**：
| **产业链证伪** | 红队证伪发现卡点被替代/客户自研 | 建议减仓/清仓 |

**紧急熔断例外**：价格跌破止损线超过 5%，无需共识投票，直接推送红色硬止损警报。

---

## 六、 Sicong 强纠错保护机制

（同 V3，无变化）

---

## 七、 人工确认门禁完整清单

| # | 确认触发条件 | 频率 | 严重程度 |
|---|---|---|---|
| 1 | L1 原始素材入库确认（早期阶段） | 每次 | ⚠️ 普通 |
| 2 | L2 原子事实确认（早期阶段，**含证据等级**） | 每次 | ⚠️ 普通 |
| 3 | 股票晋级核心池 A（B→A 提案） | 每周 0-3次 | ⚠️ 普通 |
| 4 | Investment Advisor 买入建议（共识 ≥ 🟡） | 每周 0-5次 | ⚠️ 普通 |
| 5 | L5 估值模型参数调整提案 | 每季度/每家 | ⚠️ 普通 |
| 6 | 持仓假设断裂 → 减仓/止损建议 | 不定期 | 🔴 重要 |
| 7 | 高风险操作二次确认门禁 | 触发时 | 🔴 重要 |
| 8 | Sicong 个人画像更新提案 | 不定期 | ⚠️ 普通 |
| 9 | L4 关联网络更新提案（**含产业链图谱**） | 不定期 | ⚠️ 普通 |
| 10 | L6 监控规则更新提案 | 不定期 | ⚠️ 普通 |
| 11 | 宏观乘数矩阵调整提案 | 每月 0-1次 | ⚠️ 普通 |
| **12** | **V3.1：研究线索分类变更（重点→观察→不适合）** | **不定期** | **⚠️ 普通** |

---

## 八、 Obsidian Vault 存储目录结构

```
touzi-agent-vault/
├── _inbox/                       # L1 原始痕迹
├── L2-facts/                     # L2 原子事实（含证据等级）
│   └── [Ticker]-facts.md
├── L3-profile/                   # L3 身份画像
│   ├── investor-profile.md
│   ├── persona-buffett.md
│   ├── persona-druckenmiller.md
│   ├── persona-serenity.md       # V3.1：内置 L0-L4 框架
│   └── persona-sun.md
├── L4-relations/                 # L4 关联网络
│   ├── macro-multipliers.md
│   ├── supply-chain-[Sector].md
│   └── bottleneck-map-[Sector].md  # V3.1 新增：产业链卡点图谱
├── L5-judgments/                 # L5 心智判断（含研究线索分类）
│   └── [Ticker]-judgment.md
├── L6-alerts/                    # L6 监控规则（含跟踪表）
│   └── [Ticker]-alerts.md
├── L7-actions/                   # L7 行动记录
│   └── trades.md
├── _home.md                      # Sicong 日常视图
├── _views/                       # 视图目录
├── harness/                      # Harness 层
│   ├── permissions.md
│   ├── workflows/
│   └── scripts/
│       ├── guardrail_runner.py   # V3.1：含四道防线
│       └── vault_check.py
├── proposals/                    # 待审核提案临时区
└── archive/                      # 历史提案归档
```

---

## 九、 Web 控制台核心功能

1. **每日早报推送**：Investment Advisor 主动汇报今日 3 件最重要的事
2. **共识标签可视化**：每张提案卡片显示 🟢🟡🟠🔴 共识等级及各大脑投票原因
3. **卖出建议专栏**：止损/止盈/假设断裂/产业链证伪触发的卖出建议
4. **操作纪律看板**：Sicong 本月操作纪律评分及历史遵从率趋势图
5. **画像盲区警报区**：Sicong 个人盲区检测结论
6. **富途账户集成**：实时展示账户余额、持仓明细、挂单状态
7. **趋势预测面板**：Agent 1 的趋势预测结果，含置信度与关键假设
8. **V3.1 产业链卡点地图**：L0-L4 可视化展示，候选卡点线索
9. **V3.1 证据等级看板**：每条事实/结论标注 A/B/C/D 证据等级
10. **V3.1 研究线索分类视图**：重点线索/观察线索/暂不适合 分类展示
11. **V3.1 防幻觉检查报告**：可能被夸大的结论及谨慎表达方式

---

## 十、 落地与自检清单 (Verification Spec)

1. **断链检测**：L5 提案引用的 L2-facts 文件必须物理存在
2. **门禁强验证**：模拟恶意 LLM 改 L5 `status: approved`，Harness 必须拦截
3. **WACC 边界断言**：WACC ∈ [5.0%, 15.0%]，g ∈ [0.0%, 3.0%]
4. **溯源锚点验证**：L2 事实必须含 `<- [文件#页码]`，源文件在 Context 中存在
5. **共识等级一致性**：推送提案的共识等级与 IA#1/IA#2 输出一致
6. **富途 MCP 连通性**：交易前验证查询/交易/监控三通道可用
7. **L7 即时写入**：成交后 1 秒内追加 L7 记录
8. **画像提案 Diff 格式**：Agent 6 的 L3 更新提案可被 `git apply` 解析
9. **V3.1 证据等级标注率**：L2 事实证据等级标注率必须 100%
10. **V3.1 防幻觉检查**：无来源结论拦截率 100%，D 级信源当结论拦截率 100%（特殊信源除外）
11. **V3.1 公司分类标准**：分类只能用 重点线索/观察线索/暂不适合，违规率 0%
12. **V3.1 L0-L4 完整性**：白毛股神审计必须逐层验证 L0-L4，不得跳过
13. **V3.1 红队 5 问覆盖**：IA#2 红队证伪必须覆盖 5 个标准问题

---

## 附录：版本演进对照

| 维度 | V1.5 | V2 | V3 | V3.1（本规格） |
|---|---|---|---|---|
| **架构模型** | 6 Agent + L1-L7 | 三层 + L1-L7 | 同心圆三层 + 双循环 + L1-L7 | + 产业链卡点研究方法论 |
| **Agent 数量** | 6 | 5 | 7 | 7 |
| **研究方法论** | 无 | 无 | 无 | **五段式产业链卡点研究** |
| **证据等级** | 无 | 无 | 无 | **A/B/C/D 四级** |
| **底层逻辑** | DCF 为主 | DCF 为主 | DCF 为主 | + **底层逻辑三问** |
| **产业链拆解** | 无 | 无 | 无 | **L0-L4 五层** |
| **公司分类** | 无 | 无 | 无 | **重点/观察/暂不适合** |
| **研究目标** | 投资建议 | 投资建议 | 投资建议 | **研究线索优先** |
| **防幻觉** | 无 | 溯源校验 | 溯源校验 | **+ 防幻觉检查表（第四道 Guardrail）** |
| **红队证伪** | 无 | 无 | IA#2 反驳 | **+ 研究阶段红队 5 问** |
| **特殊信源** | 无 | 无 | 无 | **老黄/孙哥/特朗普 D 级有效** |
| **量化筛选** | Python 量化 | 引用未详述 | 移除，LLM 判断 | 移除，LLM 判断 |
| **趋势预测** | 无 | 无 | Agent 1 新增 | Agent 1 新增 |
| **操作分析** | 无 | 无 | Agent 6 新增 | Agent 6 新增 |
| **富途集成** | 无 | 无 | Agent 7 + MCP | Agent 7 + MCP |
| **写入门禁** | 简单分层 | 固定权限表 | 分阶段权限 | 分阶段权限 |
| **双循环** | 无 | 无 | System 1 + System 2 | System 1 + System 2 |
| **Guardrails** | 无 | 三道防线 | 三道防线 | **四道防线** |
| **共识门禁** | 4 级 | 简化 | 4 级 | **4 级 + 证据等级影响** |
