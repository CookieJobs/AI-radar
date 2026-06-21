# AI Radar — 项目根（v0.2 重写：调研 Skill）

> 这是一份"项目自带的工作手册"。
> 任何 session / 任何工具（Hermes / Claude Code / Cursor / 网页版）打开这个目录，先读这份 CLAUDE.md，立刻知道上下文。

---

## 一句话定义（**重写**）

**Radar 是给 agent 用的「AI 产品经理调研方法论 Skill」。**

不是数据 API，不是情报订阅——是**方法论分发**。用户装上 Radar skill，agent 在执行任何 AI 行业调研前**先调 Radar 拿框架**，然后按框架引导用户、收答案、按 AI PM 5 维度评估法输出报告。

类似调研界的"律师咨询清单 + 分诊问卷 + 麦肯锡 Discovery 模板"。

---

## 当前状态

- **阶段**：v0.1 调研 Skill demo 跑通（待装到 Claude Desktop 真实测试）
- **品牌**：Radar
- **目标用户**：AI 产品经理同行 + OPC 创业者 + 早期投资人
- **定价**：浅调研 ¥0.49/次 / 深调研 ¥0.98/次（按调用付费，agent 钱包扣）
- **付费协议**：支付宝 A2M 协议（HTTP 402，2026-04 蚂蚁官方 SDK 已发布）
- **阶段 0 状态**：模拟扣钱（payment_proof='PAID'），等真实商户资质
- **数据存储**：**0 持久化**——Radar 不存任何东西，用户自己存到 Notion/Obsidian/飞书

---

## 目录结构（v0.2）

```
ai-radar/
├── CLAUDE.md                      ← 你正在读
├── docs/
│   ├── 00-context.md              ← 接手文档（6 轮讨论浓缩）
│   ├── product-brief.md           ← 产品方案 v0.2（待重写为 v0.3）
│   ├── launch-roadmap.md          ← 90 天路线图（待重写）
│   ├── b2a-value-logic.md         ← B2A 价值逻辑（待重写）
│   ├── mcp-integration-guide.md   ← MCP 集成教程
│   └── launch-announcement-v0.1.md  ← 创刊宣言
├── backend/
│   ├── skills/                    ← 阶段 0：调研 Skill（核心）
│   │   ├── research_skill_v0.1.py   ← MCP server（手写 stdio JSON-RPC）
│   │   ├── content/                  ← 静态方法论
│   │   │   ├── questionnaire_rules.md  ← 问卷设计规则
│   │   │   ├── framework_quick.md      ← 浅调研框架 + 5 维度评估法
│   │   │   └── framework_deep.md       ← 深调研框架 + 4 增强维度
│   │   └── tests/test_demo.py       ← 3 步流程模拟测试
│   ├── main.py                    ← 阶段 2 用（数据 API）—— 暂不删
│   ├── seed.py / models.py        ← 阶段 2 用 —— 暂不删
│   ├── mcp_server.py              ← 旧版 MCP —— 暂不删
│   ├── ingest/                    ← 阶段 2 RSS fetcher —— 暂不删
│   ├── candidates/                ← fetcher 输出 —— 暂不删
│   └── venv/                      ← Python 3.9（mcp 包要 3.10+）
└── README.md
```

---

## 产品定位（**核心**）

### Radar 不做什么（**红线**）

- ❌ **不**替用户做调研
- ❌ **不**调 LLM
- ❌ **不**存用户数据
- ❌ **不**卖数据 / 卖事件
- ❌ **不**做"AI 替你查资料"——这是"数据 API"思维
- ❌ **不**做新闻聚合 / 周报 / 订阅
- ❌ **不**做 IP 限速 / 订阅档位

### Radar 做什么

- ✅ 提供「**AI 产品经理调研问卷设计规则**」
- ✅ 提供「**AI PM 5 维度评估方法论**」
- ✅ 提供「**调研报告输出模板**」
- ✅ 提供「**领域专有检查清单**」（调研公司/赛道/技术/产品/政策）
- ✅ 走 agent 钱包原生计费（按调用付费）
- ✅ 商业道德红线：只用公开信源 + 个人方法论

### Skill 3 步工作流

```
Step 1: 用户问 "调研 X"
        agent 调 Radar skill（不传 payment_proof）
        ↓
        Radar 返回 A402 账单（¥0.49 浅 / ¥0.98 深）
        ↓
Step 2: 用户在支付宝付款
        agent 重新调 skill（payment_proof='PAID'，不传 answers）
        ↓
        Radar 返回「调研问卷设计规则 + 建议问卷骨架」
        ↓
        agent 调自己的 LLM 生成具体问卷，问用户，收答案
        ↓
Step 3: agent 再次调 skill（payment_proof + answers）
        ↓
        Radar 返回「AI PM 调研框架 + 报告模板」
        ↓
        agent 调自己的 LLM 按框架执行调研，输出报告
        ↓
        agent 把报告给用户
        ↓
用户自己存到 Notion / Obsidian / 飞书
```

---

## 关键判断（不许改）

### 1. 卖方法论，不卖数据

- L1 数据（事实）：agent 自己能搜，不值钱
- L2 标签（分类）：agent 自己能做，值小钱
- **L3 解读方法论**：值钱 — Radar 卖这个
- **L4 推演框架**：值钱 — Radar 也卖这个
- **核心 IP**：「AI PM 5 维度评估法」+「调研问卷三段式」

### 2. 一次付费，3 步交付

- 不是"调一次 API 返回数据"
- 是"付一次费，走完 1 个完整调研"
- 用户填问卷是必走流程——这是**价值核心**

### 3. 化名出镜，不藏职业背景

- 品牌名 Radar，不暴露公司
- About 只写"AI 产品经理"

### 4. 商业道德红线（不许踩）

- ❌ 高途未公开的用户数据、教学内容、产品数据
- ❌ 客户名单、未公开产品规划、未公开财务
- ❌ 公司内部培训资料、NDA 覆盖的素材
- ✅ 公开信源 + 个人方法论 + 自购素材二次加工

---

## 当前 Todo

- [x] 调研 Skill v0.1 demo 跑通（test_demo.py 通过）
- [ ] 装到 Claude Desktop 真实测试
- [ ] 验证支付宝 A2M 协议链路（需要商户资质）
- [ ] 重写 docs/product-brief.md → v0.3（对齐"调研 Skill"定位）
- [ ] 重写 docs/launch-roadmap.md（v0.1 阶段 0 改为"调研 Skill 验证"）
- [ ] docs/b2a-value-logic.md 待重写

---

## 协作约定

### 给 AI 起草"调研问卷"或"调研框架"时的标准 prompt 模板

```
你是一名 AI 行业调研方法论顾问。基于以下调研问题，按 Radar 调研方法论
（见 backend/skills/content/questionnaire_rules.md）生成 5-7 个问题（浅调研）
或 10-15 个问题（深调研）的问卷，要求：
1) 包含三段式结构（范围 / 深度 / 意图）
2) 包含 5 个必问核心问题
3) 单选优先，选项互斥，不预设答案
4) 简短，单个问题不超过 30 字

调研问题：[用户问题]
调研深度：[浅 / 深]
```

### 质量校验 checklist

调研报告输出前：
- [ ] 摘要 3 句话，每句独立信息
- [ ] 关键事实每条带来源 URL
- [ ] AI PM 5 维度评估全部覆盖
- [ ] 行动建议每条有"为什么"和"何时做"
- [ ] 30 天预测给具体信号点
- [ ] 风险点评估概率和影响
- [ ] 不出现"很重要"/"值得关注"等无价值表述
- [ ] 商业道德过关（无公司机密）

---

## 项目元信息

- 创建日期：2026-06-18
- 重大转向：2026-06-20（v0.1 → v0.2：从"数据 API"切到"调研 Skill"）
- 核心 IP 文档：backend/skills/content/{questionnaire_rules,framework_quick,framework_deep}.md
- 工具栈：Hermes / Claude Code / Cursor 跨工具协作
- 工作目录：~/Desktop/HermesWS/AI-radar/
- Python：3.9+（3.10+ 需重装 venv 才能用 mcp 包，调研 skill 本身不依赖）
- 阶段 0 定价：浅调研 ¥0.49 / 深调研 ¥0.98（按调用付费）
