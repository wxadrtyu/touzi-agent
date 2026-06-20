# 投资研究 AI 系统规格说明书 (V2 - 深度融合三层架构与 L1-L7 数据层)

本文档是系统设计的终极物理实现指南。它将第一版的 **L1-L7 知识库数据层（唯一真相 Vault）** 与 **三层 Agent 架构（Prompt / Context / Harness）** 进行深度融合，明确每个 Agent 的提示词机制、上下文如何通过 L1-L7 动态组装、以及 Harness 如何通过工作流和写入门禁（Permissions）来调度与保障系统安全。

---

## 架构概览：数据层与执行层的映射关系

```
【Harness 执行层 (workflows/)】
   │ (调度 System1/System2)
   ▼
【Context Engineering (装配器)】 ◄── (动态拼装) ──► 【唯一真相：Vault (L1-L7 Markdown)】
   │                                                    ├─ L1 原始痕迹 (_inbox/)
   │ (动态注入)                                          ├─ L2 原子事实 (L2-facts/)
   ▼                                                    ├─ L3 身份画像 (L3-profiles/)
【Prompt Engineering (6P大脑)】                           ├─ L4-L6 心智/判断 (_views/, L5-judgments/)
   │                                                    └─ L7 行动记录 (L7-actions/)
   ▼ (物理生成)
【Harness Gate (permissions.md)】 ── (校验/拍板/落库) ──> 最终写入/提案
```

---

## 一、 唯一真相：L1 - L7 数据层定义与物理结构

知识库 Vault 物理上由纯 Markdown 文件和 Frontmatter 构成。Harness 不持有状态，所有的状态均存储于以下 L1-L7 的结构化 Markdown 中。

### 1. L1 原始痕迹 (Raw Inbox)
*   **物理路径**：`_inbox/*.md`
*   **来源**：网页剪报、微信聊天记录导出、Sicong 随手记的原始想法。
*   **Frontmatter 格式**：
    ```yaml
    type: L1-raw
    source: chrome-extension | manual | wechat
    captured_at: 2026-06-18T18:00:00+08:00
    status: unprocessed | processed
    ```

### 2. L2 原子事实 (Atomic Facts)
*   **物理路径**：`L2-facts/[Ticker]-facts.md`（例如：`L2-facts/AAPL-facts.md`）
*   **职责**：将 L1 零散表达与财报，抽成可检索、可合并的事实片段。
*   **Markdown 正文格式**：
    每一条事实必须是单行、自包含的陈述，并以 UUID 进行标识：
    ```markdown
    - [FACT_01cf3] 苹果 2025 年第四季度服务业营收为 250 亿美元，同比增长 12%。<- [2025-Q4-Earnings.pdf#Page_12]
    - [FACT_9a2ef] 库克在 Q4 电话会中指出，AI 智能体（Apple Intelligence）的变现周期可能比预期更长。<- [2025-Q4-Call-Transcript.md#Page_3]
    ```

### 3. L3 身份画像 (Profiles)
包含 Hugh (Sicong) 自己的画像与“白毛股神大师”的决策因子包。
*   **物理路径**：
    *   Hugh 个人画像：`L3-profile/investor-profile.md`
    *   巴菲特画像：`L3-profile/persona-buffett.md`
    *   德鲁肯米勒画像：`L3-profile/persona-druckenmiller.md`
    *   孙宇晨画像：`L3-profile/persona-sun.md`
*   **大师画像结构 (以巴菲特为例)**：
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

### 4. L4 - L6 心智与意图/判断层
*   **L4 会话摘要与心智**：`L4-sessions/`，保存每一轮与用户的交互要点。
*   **L5 主动判断层**：`L5-judgments/[Ticker]-judgment.md`。包含对股票的核心 thesis 与估值。
    *   **Frontmatter 格式**：
        ```yaml
        ticker: AAPL
        last_updated: 2026-06-18
        status: proposed | approved  # proposed 表示仅是 Agent 的提案，approved 表示 Hugh 拍板后落盘
        ```
    *   **正文结构**：
        ```markdown
        # 核心论点 (Thesis)
        依靠高粘性服务业，具备极宽护城河。
        
        # 估值区间 (Valuation)
        - 悲观 DCF: 190.5 美元
        - 中性 DCF (Base): 225.0 美元
        - 乐观 DCF: 250.0 美元
        ```
*   **L6 行动建议 (Watchlist)**：`L6-watchlist.md`，记录即将触发的提醒或买入点。

### 5. L7 行动记录 (Action Logs)
*   **物理路径**：`L7-actions/trades.md`
*   **职责**：机械层自动记录，Sicong 交易指令落盘。
    ```markdown
    - [TRADE_88aef] 2026-06-18 10:00:00 | BUY | AAPL | 100 股 | 价格: 201.2 美元 | 关联 L5 提案: [AAPL-judgment#L5]
    ```

---

## 二、 第一层：Prompt Engineering (与数据层映射的 6P 设计)

在此层中，核心 Agent 的 Prompt 必须直接感知数据层（L1-L7）的文件规范，并使用强类型指令来限制幻觉。

### 1. Agent 3：深度研究员 (Deep RAG Analyst)
*   **Persona**：CFA 股票估值专家。
*   **Purpose**：读取 L1 及外部财报资料，提炼 L2 原子事实，计算 DCF，输出 L5 判断层提案。
*   **Process**：
    1.  解析 Context 灌入的 `_inbox/` 临时文件与财报 PDF。
    2.  提取符合格式的 L2 原子事实，格式化为 `- [FACT_xxxx] ... <- [源文件#页码]`。
    3.  在 `<analysis_draft>` 中进行 DCF 数学计算：
        *   $FCF = \text{Operating Cash Flow} - \text{CapEx}$
        *   根据美债 10 年期收益率设定 WACC。
    4.  输出 L5 提案 Markdown Diff 以及符合 Schema 的 JSON 报告。
*   **Policy**：
    *   **溯源铁律**：严禁凭空写财务数字。凡是未能在 Context 原文中找到对应的 L2 事实，其数值在 JSON 中必须标记为 `null`。
    *   **只提案、不落盘**：Agent 3 严禁直接改写 `L5-judgments/` 中的 `status: approved` 文件。其只能生成 `status: proposed` 的新文件或 Diff 建议。
*   **Presentation**：
    必须输出两部分：
    1.  `<l2_facts_proposal>`：新提取的原子事实 Markdown。
    2.  `<l5_judgment_proposal>`：L5 判断层文件的完整草稿（包含 `status: proposed` 前言）。

---

### 2. Agent 4：IA#1 - 投资委员会主席 (Investment Committee Chair)
*   **Persona**：首席投资官。
*   **Purpose**：评估 Agent 3 生成的 L5 提案，结合 L3 中的 Hugh 画像和大师加权因子，并引入 Agent 2 的情绪，做出交易指令。
*   **Process**：
    1.  载入 Agent 3 的 L5 提案。
    2.  读取 `L3-profile/investor-profile.md` (Hugh 个人画像) 和激活的大师画像（如 `L3-profile/persona-buffett.md`）。
    3.  执行因子衰减计算：
        $$\text{Final Weight} = \text{Raw Weight} \times \text{Attenuator}$$
    4.  输出最终买卖/建仓提案。
*   **Policy**：
    *   **安全边际门禁**：若现价没有低于 Agent 3 中性估值的 15%，一律输出 `action: HOLD`。
    *   **个性化偏好强校验**：如果 Hugh 个人画像中包含“对回撤敏感”，必须自动将单股最大仓位上限从 15% 衰减至 8%。

---

### 3. Agent 5：IA#2 - 魔鬼代言人 (Devil's Advocate)
*   **Persona**：风控官。
*   **Purpose**：强行攻击 Agent 4 的买入提案，找出逻辑和估值假设的软肋。
*   **Process**：
    1.  载入 Agent 4 生成的 `BUY` 提案及 Agent 3 的 DCF 假设。
    2.  锁定 DCF 里的乐观因子（如：永续增长率 $g > 2.5\%$，折现率 $WACC < 7.5\%$）。
    3.  强行运行**悲观参数 DCF**，输出对比差值。
*   **Policy**：
    *   **必须反驳**：禁止附和 IA#1。必须指出至少 2 点核心反驳，且反驳逻辑中必须包含差值影响百分比（`rebuttal_impact_pct`）。

---

## 三、 第二层：Context Engineering (RAG 混合检索与上下文装配)

Context 层的核心任务是实现 **Context Loader** 的检索装配算法与本地轻量级 **RAG (Retrieval-Augmented Generation) 检索管道**。

```
【7大类原始数据 (PDF/MD)】 
        │
        ▼ [清洗与物理切片] ──> 财报表格转 Markdown Table / 电话会 QA 对提取
        ▼ 
【本地 Chunk 库 (带 Ticker/Year 标签)】
        │
    ┌───┴───┐
    ▼       ▼
 [向量编码] [BM25/FTS5]
    ▼       ▼
 [语义召回] [精确字/数召回]
    └───┬───┘
        ▼ [RRF 混合分数融合] ──> [轻量 Re-rank 重排] ──> 【注入 Agent 的 Context】
```

### 1. RAG 物理切片与结构化清洗规格 (Chunking & Parsing)
为了确保财报中的财务数字与上下文关联不丢失，所有文件在写入 Vault 索引前必须经过以下清洗和切片处理：

*   **财报 PDF 结构化清洗 (Table Preservation)**：
    *   **处理机制**：严禁直接将 PDF 转换为纯 text，因为多列财务报表转成 text 后行/列数据会错位，彻底废掉。
    *   **清洗规则**：使用 `pdfplumber` 物理识别表格区域，强行转化为 Markdown Table 或标准 CSV。
    *   **切片阈值 (Chunk Size)**：以 1500 tokens 为基本块，重叠（overlap）200 tokens。若切片切在 Markdown 表格中，必须自动向前或向后回溯，将**整个表格完整保留在一个 Chunk 中**。
*   **电话会纪要切片 (QA Pair Binding)**：
    *   **处理机制**：按“发言人-答复（Speaker-Response）”的问答对作为最小 Chunk 切片。
    *   **Metadata 绑定**：每个 QA 块必须携带 `{"ticker": "AAPL", "date": "2025-Q4", "speaker": "Cook", "type": "qa_call"}` 的元数据。

### 2. 混合检索管道规格 (Hybrid Search Pipeline)
投研 RAG 必须采用 **“语义检索 + 关键词精确数字检索” 双路召回**，以防向量相似度匹配稀释具体的百分比或财务数字。

#### 第一阶段：双路召回
1.  **Dense 语义召回**：
    *   使用本地轻量级 `BAAI/bge-small-zh-v1.5` 向量模型（384 维，仅占用 100MB 显存/内存）。
    *   计算 Query 向量与所有 Chunk 向量的余弦相似度，筛选前 $K_1 = 15$ 个语义最相关的 Chunks。
2.  **Sparse 关键词与数字召回**：
    *   利用 SQLite FTS5 (Full Text Search) 全文索引进行检索。
    *   针对 Query 提取的关键词及**关键数字**（如：“Q4”、“毛利率”、“8%”、“2025”）执行检索，召回前 $K_2 = 15$ 个 Chunks。

#### 第二阶段：互惠等级融合 (Reciprocal Rank Fusion, RRF)
对两路召回的 Chunks 使用 RRF 算法计算融合得分，避免因两路打分分值范围不同而无法加权的问题：
$$\text{RRF\_Score}(d) = \frac{1}{60 + r_{dense}(d)} + \frac{1}{60 + r_{sparse}(d)}$$
*其中 $r_{dense}(d)$ 和 $r_{sparse}(d)$ 是文档 $d$ 在两路检索结果中的排名。若文档未进入某路 Top 15，则其排名倒数视作无穷大。*

#### 第三阶段：动态 Re-ranking (重排过滤)
将融合得分前 15 名的 Chunks 送入重排阶段：
*   **重排策略**：使用轻量级的 Gemini Flash / Mini 对这 15 个 Chunks 进行相关度快速评分（0-10）。
*   **阈值拦截**：得分低于 5 分的噪声 Chunk 予以拦截丢弃，仅保留排名前 $N$ (最大 $N=8$, 总 Token 数限制在 6k tokens 内) 的极精炼 Chunk 注入 Claude 3.5 的上下文。

---

### 3. 动态 Context 装配矩阵 (Routing Matrix)

| 触发场景/工作流 (SOP) | 触发源 | 动态加载的 Vault 上下文组合 |
| :--- | :--- | :--- |
| **SOP: inbox-ingest (提取 L2)** | 定时任务 | `_inbox/` 目录下未处理的 L1 文件 + `L2-facts/[Ticker]-facts.md` (增量比对) |
| **SOP: update-l5-proposal (评估L5)** | 新增 L2 事实 | `L2-facts/[Ticker]-facts.md` 全集 + 宏观无风险利率 + 旧 `L5-judgments/[Ticker]-judgment.md` |
| **SOP: System 1 (Hugh 实时提问)** | 交互输入 | 匹配的 `L5-judgments/[Ticker]-judgment.md` + 通过 RAG 检索到的前 8 个 RRF 核心 Chunks + `L3-profile/investor-profile.md` + 活跃的大师语录库 |

### 4. Context 长度控制与自适应压缩
```python
def assemble_context_with_rag(ticker, query, raw_chunks):
    # Tier 1: 核心指标与 Hugh 画像 (强制不压缩，100% 导入)
    tier1 = load_core_metrics(ticker)
    
    # Tier 2: 运行 RAG 混合检索得到核心 Chunks
    core_chunks = run_hybrid_retrieval(ticker, query, raw_chunks)
    
    # Tier 3: 提取历史 30 天 L7 行动记录
    tier3 = get_aggregated_historical_logs(ticker)
    
    return f"Core Specs:\n{tier1}\n\nRetrieved Raw Context:\n{core_chunks}\n\nAction History:\n{tier3}"
```

---

## 四、 第三层：Harness Engineering (工作流与写入门禁安全地基)

Harness 是保障整个 Vault 唯一真相不受污染的安全锁，物理落实在 `workflows/` 和 `permissions.md`。

### 1. 物理写入门禁权限表 (`harness/permissions.md`)
本表为绝对不变量。任何 Agent 写入操作在落盘前，Harness 必须读取此配置实施拦截：

| 目标数据层 (Vault 物理目录) | 数据特性 | Agent 写入权限 | Hugh (Sicong) 确认要求 | 物理动作 |
| :--- | :--- | :--- | :--- | :--- |
| **L1 原始痕迹 (`_inbox/`)** | 原始素材 | **读/写**（可直接落盘） | 零确认 | 直接追加 |
| **L2 原子事实 (`L2-facts/`)** | 机械数据事实 | **读/写**（可自动落盘） | 零确认 | 脚本自动增量写入 |
| **L3 身份画像 (`L3-profile/`)** | 核心人设/偏好 | **只读** | **强确认**（必须 Hugh 同意） | 提案 Diff -> 确认后写入 |
| **L5 主动判断 (`L5-judgments/`)** | 交易方向/估值 | **只读** (Agent 只能读) | **强确认**（必须 Hugh 拍板） | 提案 Diff -> Hugh 修改 status 为 approved 后真正合并 |
| **L7 交易动作 (`L7-actions/`)** | 交易物理记录 | **只读/写**（配合券商API动作）| 零确认（交易发生时自动记录） | 机械层自动追加 |

### 2. Harness 双轨 Loop 执行伪代码

#### 慢路 (System 2): 定时增量更新 L2 事实与 L5 提案工作流
```python
def workflow_system2_overnight_loop():
    # 1. 量化筛选候选股 (Agent 1)
    candidates = run_python_screener()
    
    for ticker in candidates:
        # 2. 情绪抓取 (Agent 2)
        sentiment = fetch_sentiment(ticker)
        
        # 3. 动态加载上下文
        context = ContextLoader.load(
            workflow="update-l5-proposal", 
            ticker=ticker, 
            extra_data={"sentiment": sentiment}
        )
        
        # 4. 深度估值分析 (Agent 3) - 跑 CoT DCF
        draft, raw_l2_proposal, l5_proposal = Agent3.analyze(context)
        
        # 5. 数字溯源校验 (第一道 Guardrail)
        if not run_hallucination_guard(draft, context):
            # 自检重试
            draft, raw_l2_proposal, l5_proposal = Agent3.retry_with_feedback("数字未匹配原文页码")
            
        # 6. 安全无误后，自动落盘 L2 (因为 L2 是机械数据事实，允许 Agent 直接写)
        save_to_l2_facts(ticker, raw_l2_proposal)
        
        # 7. 提交 L5 提案 (注意：status 为 proposed)
        save_proposed_l5_judgment(ticker, l5_proposal)
        
        # 8. 主投委会决策 (Agent 4) 与 魔鬼代言人反驳 (Agent 5) 对决
        ia1_verdict = Agent4.evaluate(l5_proposal)
        ia2_rebuttal = Agent5.attack(ia1_verdict, l5_proposal)
        
        # 9. 校验交易一致性 (第二道 Guardrail)
        if ia1_verdict["action"] == "BUY" and (ia1_verdict["execution"]["target_price"] > l5_proposal["valuation"]["dcf_bear_mid_bull"][1] * 0.85):
            # 驳回，溢价过高，不符合 15% 安全边际
            ia1_verdict["action"] = "HOLD"
            
        # 10. 将冲突并列写入临时提案，推至 Hugh 的 _home.md 视图
        write_confrontation_report_to_home(ticker, ia1_verdict, ia2_rebuttal)
```

---

### 3. 三道 Guardrails 金融专防脚本细节
Harness 运行在 Node/Python 的沙箱中，每次 API 响应都必须经过本地 `harness/scripts/guardrail_runner.py` 的管道过滤：

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
```

---

## 五、 落地与自检清单 (Verification Spec)

当新规格书投入物理实现时，开发人员必须在 `harness/scripts/vault_check.py` 中编码实现以下断言：

1.  **断链检测**：扫描 `L5-judgments/` 中的所有 Ticker 提案，确保其引用的 `L2-facts` 文件物理存在。
2.  **门禁强验证**：测试通过模拟恶意的 LLM 响应，试图直接通过 API 修改 `L5-judgments/` 中的 `status: approved`，检查 Harness 是否能正确拦截并报错。
3.  **WACC 边界断言**：Agent 3 导出的估值中，折现率 WACC 必须在 $5.0\% \sim 15.0\%$ 之间，永续增长率 $g$ 必须在 $0.0\% \sim 3.0\%$ 之间，超出范围一律拦截。
