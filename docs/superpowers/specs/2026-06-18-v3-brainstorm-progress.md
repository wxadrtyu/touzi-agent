# V3 架构重设计 - 头脑风暴进展记录

- **日期**: 2026-06-18
- **状态**: 进行中（待用户选择架构方案后继续）
- **目标**: 将 V1.5 规格（2026-06-14-stock-research-agent-design.md）升级为 V3 统一规格，融合同心圆三层架构（Prompt/Context/Harness），更完善、完整、健壮、可行性更强

---

## 已确认的决策

### 1. 规格关系
- **V3 统一规格**：重新设计 V1.5，将三层架构完整融入，最终只保留一个终极规格文档，V2（spec-v2-three-layer.md）作为参考归档

### 2. 技术栈
- **Obsidian + Python**：Obsidian Vault 作为唯一真相存储，Python 做 Agent/RAG/Guardrail 后端，Web 前端独立

### 3. Agent 重新划分（用户核心需求）
- **去掉重量化**：不再依赖 Python 量化筛选（Screener Agent），改用 LLM 自主判断
- **保留的原有角色**：
  - ✅ Sentiment Analyst（情绪分析）
  - ✅ Audit Council（白毛股神 + 孙宇晨 + Sicong 盲区检测）
  - ✅ 双 IA 共识门禁（IA#1 主提案 + IA#2 魔鬼代言人，4 级共识等级）
  - ✅ Deep RAG Analyst（增强为"研究咨询 Agent"，加趋势预测能力）
- **新增角色**：
  - 🆕 研究咨询 Agent（Deep RAG 增强）：自助 RAG 阅读 + 信息查询 + 给意见 + 预测未来趋势
  - 🆕 操作分析 Agent：分析用户操作 + 总结 + 优化画像（L3）+ 提供修正建议
  - 🆕 富途交易 MCP：查询（账户/持仓/订单）+ 交易（买/卖）

### 4. L1-L7 数据层定位
- L1-L7 是**唯一真相 Vault**，作为三层架构的核心数据地基
- **Context 层**：从 L1-L7 读取/检索，动态装配上下文注入 Agent
- **Harness 层**：控制对 L1-L7 的写入权限（permissions.md 门禁）
- **Prompt 层**：Agent 消费上下文后，产出提案回流到 L1-L7（经 Harness 门禁校验）

---

## 待决策：架构方案

### 方案 A：同心圆三层映射（推荐）
将 Agent 按其主要活跃层映射到同心圆模型，每个 Agent 都有 6P Prompt 定义、依赖的 Context 管道、受 Harness 约束。

```
【Harness 外层】工作流编排 + Guardrails + 富途 MCP + 写入门禁
     │                                          ↕ 写入权限控制
     ↕ 调度与约束                                │
【Context 中层】RAG 混合检索 + 情绪数据 + 装配矩阵
     │                                          ↕ 读取/检索
     ↕ 信息供给                                  │
【Prompt 内层】7 个 Agent 的 6P 大脑
     │                                          ↕ 产出提案落盘
     ↕ 生成                                     │
     │                                          ▼
     └────────────────► 【L1-L7 唯一真相 Vault】◄─┘
```

**7 个 Agent**：
1. 研究咨询 Agent（原 Deep RAG 增强，加趋势预测）
2. 情报分析 Agent（Sentiment）
3. 审计委员会（白毛股神+孙宇晨+盲区）
4. IA#1 主提案方
5. IA#2 魔鬼代言人
6. 操作分析 Agent（新增）
7. 交易执行 Agent（富途 MCP 桥接）

**优点**：最贴合同心圆模型，三层职责清晰，每层可独立优化
**缺点**：Agent 跨层协作需要明确定义接口

### 方案 B：功能域 + 三层横切 + L1-L7
按功能域组织（研究域/决策域/执行域/反思域），三层架构作为横切关注点贯穿每个域。

### 方案 C：双循环 + L1-L7
区分"快循环"（实时咨询/查询）和"慢循环"（定时深度分析/提案），每个循环内嵌三层架构。

---

## 参考文件
- V1.5 规格：`docs/superpowers/specs/2026-06-14-stock-research-agent-design.md`
- V2 规格：`docs/spec-v2-three-layer.md`
- 同心圆架构：`docs/superpowers/specs/同心圆架构.txt`
- Vault 宪法：`README.md`

---

## 下一步
- 等待用户选择架构方案（A/B/C/混合）
- 然后按选定方案展开详细设计（Prompt 层 6P / Context 层 RAG / Harness 层工作流）
- 最后写入 V3 规格文档
