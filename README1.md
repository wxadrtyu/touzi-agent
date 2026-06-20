# Harness — vault 的执行层（外挂，非真相）

> **一句话定位：** Harness 是包在模型外面的「手、眼、调度器、质检员、运行环境」。
> 它负责**捕获 / 检索 / 调度 / 工具调用 / 质检 / 提案**；
> **唯一真相永远是 vault 里的 Markdown，Harness 不持有任何长期真相。**

本目录是「方案一」的落地：不装重型框架，用**纯文本工作流定义 + 轻量脚本 + CodeBuddy automation 定时任务**当 harness。
零外部依赖、完全可移植——把整个 vault 拷走，harness 规则也跟着走。等流程稳定，再按 `_home` roadmap 的 Phase C 决定是否接 OpenHarness 等专业框架。

---

## 0. 边界（不变量在宪法，门禁在 permissions.md）

harness 不重述全局规则，只指过去 + 守自己那条铁律：

- **全场景不变量**（单一真相 / 写入门禁原则 / 默认满量程思考 / 检索只呈现不预设框架）→ 见根 `README.md`（宪法）§0。
- **每层写入权限表** → 见 `permissions.md`（冲突时以那张表为准）。
- **harness 自己的铁律**：**不持有任何长期真相**——不建独立 memory store、不存自有 user profile、不存逐字稿快照。harness 越强越要守这条。

> 记住：**Harness 可以替你跑流程，不能替你成为你。** 它不决定你长期相信什么。

---

## 1. 架构（方案一·轻量形态）

```
你
  ↓  一句话 / 文件 / 链接 / 成交 / 想法
Harness（本目录）
  ├─ Context Loader     按宪法派发表加载：常驻底色 + 命中场景 rules/ 篇 + 相关 L5/L6；profile 大脑按需装载（见下）
  ├─ Profile Loader     load-profile：把 L3 当「可装载大脑」——思维方式 + 执行技能,点名才装、可提议不擅套
  ├─ Workflow Runner    跑 workflows/ 里的工作流（复用 rules/procedures/ 的权威流程）
  ├─ Permission Gate    permissions.md：判断/身份层只提案、机械层可落
  ├─ Schema Validator   scripts/vault_check.py：frontmatter / 断链 / inbox 体检
  └─ Scheduler          CodeBuddy automation 定时触发（每日 / 每周 / 每月）
  ↓  只读写 Markdown
knowledge-vault（唯一真相：L1–L7）
  ↓
Obsidian 视图（_home / _views：今天看什么 / 在信什么 / 谁该被压测 / 知行背离）
```

要点：
- **Workflow Runner 不重写流程**——`rules/procedures/` 已是权威 SOP，工作流只规定「何时触发、读哪些料、产出落到哪、权限是什么」，具体怎么抽 / 怎么压测仍引用 `rules/procedures/`。
- **Scheduler 只触发，不裁决**：定时任务跑完只产「提案 / 提醒 / 报告」，判断层等你拍板。
- **Schema Validator 是守门质检**，长期维护比搭建更重要。

---

## 2. 目录结构

```
harness/
├─ README.md            ← 本文件：定位 / 边界 / 架构
├─ permissions.md       ← 写入门禁权限表（最关键的安全地基）
├─ workflows/           ← 工作流定义（何时触发 / 读什么 / 落哪 / 权限）
│  ├─ inbox-ingest.md           _inbox → L1（机械，可自动落）
│  ├─ extract-l2.md             L1 → L2（机械，可自动落）
│  ├─ update-l5-proposal.md     新 L2 压测 L5 → 建议 diff（只提案）
│  ├─ review-l5.md              月度 L5 结构回顾 → L4 报告 + diff（只提案）
│  ├─ log-trade.md              一句话交易 → L7 + 即时判断（可自动落）
│  ├─ watchlist-reminder.md     L6 到期/即将触发 → 提醒（只提醒）
│  ├─ load-profile.md           按需装载一颗大脑 + 它的执行技能（只读 L3，不擅套）
│  └─ update-profile-proposal.md 对话中发现 → 提案进 L3（只提案，不静默改身份）
├─ scripts/
│  └─ vault_check.py    ← 纯标准库脚本：体检 frontmatter / 断链 / inbox 状态
└─ automations.md       ← 3 个 CodeBuddy 定时任务的配置说明与对应关系
```

---

## 3. System1 / System2 双轨（与 roadmap 一致）

- **System1（快路）= 读库即答**：你提问时，Context Loader 按**宪法派发表**加载常驻底色（`rules/style.md`）+ 命中场景的 `rules/` 篇 + 相关 L5/L6，直接作答。无需调度。
- **System2（慢路）= 定时深加工**：Scheduler 定时跑 `extract-l2` / `update-l5-proposal` / `review-l5` / `watchlist-reminder`，产出**提案 digest** 给你逐条拍板。

System1 自动跑、产出提案喂给 System2；vault 永远是唯一真相，引擎只是读写 MD 的外挂。

---

## 3.5 Profile = 可装载的大脑（思维方式 + 执行技能）

`L3-profile/` 里每篇都是一颗**可独立装载的大脑**：不只是「怎么想」（决策框架/思维方式），还带「会怎么干活」（frontmatter `skills` + 正文「执行技能」节）。harness 用两个工作流管它们：

- **`load-profile`（装载）**：点名才装、明显适合时**可提议但不擅自套用**；装载 = 换上它的脑子 + 激活它的执行技能。常驻默认开的只有 `load_trigger: always_on` 的底色（沟通偏好 + 身份背景）。persona 装载必标「以下为 <name> 视角的模拟」，用完交还决策权，绝不静默落库。
- **`update-profile-proposal`（沉淀）**：贯穿所有对话，发现可进 profile 的信号（新偏好/新纪律/新毛病/新技能习惯/新值得建的 persona）时**主动提案**给 Hugh 加入——不静默改、也不闷着不说。拍板后才落 L3 并在「源材料/演化」留痕。

> 对应 Hugh 的两条预期：① profile 是带技能的独立大脑、按需装载、可建议不擅套；② 对话中发现可沉淀的，主动提案加入。

---

## 4. 怎么用（最小操作）

- **手动跑某个工作流**：在 CodeBuddy 里说「跑 harness 的 extract-l2」/「按 harness 处理 inbox」/「给我今天的 watchlist 提醒」。
- **定时跑**：见 `automations.md`，已配每日 / 每周 / 每月三个任务。
- **体检 vault**：`python3 harness/scripts/vault_check.py`（或让 CodeBuddy 跑），输出 schema / 断链 / inbox 报告。

> 所有判断层产出都是**提案**，等你说「同意」才落盘。这是 harness 的默认纪律，不是例外。
