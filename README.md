# Radar

> **给 agent 用的「AI 产品经理调研方法论 Skill」。**
> 用户 agent 装上 Radar，按方法论做 AI 行业调研，按调用付费（支付宝 A2M 协议）。
> **调研执行 = 用户 agent + 用户的 LLM；Radar 只提供方法论 + 模板。**

[![MCP](https://img.shields.io/badge/MCP-compatible-blue)]()
[![Status](https://img.shields.io/badge/status-stage_0_demo-yellow)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/license-TBD-lightgrey)]()

---

## 一句话定义

**Radar 是 B2A（Business to Agent）模式的"调研方法论 Skill"。**

用户 agent 调 Radar 拿「AI 产品经理调研问卷设计规则」+「AI PM 5 维度评估框架」+「报告输出模板」。用户 agent 拿到这些规则后，调自己的 LLM 跑调研、生成报告。

**类比**：调研界的"律师咨询清单 + 分诊问卷 + 麦肯锡 Discovery 模板"。

---

## 这是什么 / 不是什么

### Radar 是什么 ✅

- 给 agent 用的方法论 Skill（MCP server，stdio 协议）
- 提供「AI 产品经理调研问卷设计规则」
- 提供「AI PM 5 维度评估法」（影响 / 趋势 / 行动 / 30 天预测 / 风险）
- 提供「调研报告 Markdown 输出模板」
- 浅调研 ¥0.49/次 / 深调研 ¥0.98/次（按调用付费）
- 走支付宝 A2M 协议（HTTP 402，2026-04 蚂蚁官方 SDK 已发布）

### Radar 不是什么 ❌

- ❌ 不是数据 API（不卖事件、不卖数据）
- ❌ 不替用户执行调研（用户 agent + 用户 LLM 才是执行者）
- ❌ 不调 LLM（不替你跑 AI）
- ❌ 不存数据（不存用户调研记录）
- ❌ 不是周报 / 订阅 / newsletter
- ❌ 不做"AI 替你查资料"——这是上一代产品思维

---

## 核心价值：为什么卖"方法论"卖得动

**用户没装的痛点**：调研质量 = 边界清晰度 × 维度完整度 × 意图理解度

没用 Radar：
- 用户问"帮我调研下 Anthropic" → agent 瞎搜一通 → 输出 200 字散乱内容
- 用户不知道调研边界在哪 → 报告泛泛而谈
- 用户不知道调研格式 → 报告没有结构

用了 Radar：
- agent 先问 5-7 个结构化问题（按 Radar 规则生成）
- 用户答完，agent 拿到 AI PM 5 维度评估框架
- agent 按框架跑调研、输出结构化报告
- **每一步都有方法论支撑，不靠 agent 心情**

**类比**：
- 没用 Radar = 让 agent"随便写篇文章"
- 用了 Radar = 让 agent 按《金字塔原理》写商业分析

---

## 3 步工作流（一次调研）

```
Step 1: 用户问 "调研 X"
        agent 调 Radar skill（不传 payment_proof）
        ↓
        Radar 返回 A402 账单（浅 ¥0.49 / 深 ¥0.98）
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

## 快速开始（装到 Claude Code）

### 前提

- Claude Code 已装（`claude` 命令可用）
- Python 3.9+（手写 stdio JSON-RPC，不依赖 mcp Python 包）
- macOS / Linux（未在 Windows 测试）

### 1. clone + 准备 venv

```bash
git clone https://github.com/CookieJobs/AI-radar.git
cd AI-radar/backend
python3 -m venv venv
venv/bin/pip install --upgrade pip
# v0.2 demo 不依赖第三方包（手写 stdio JSON-RPC），但 venv 准备好备用
```

### 2. 配置 Claude Code MCP server

编辑 `~/.claude.json`：

```json
{
  "mcpServers": {
    "radar": {
      "command": "/absolute/path/to/AI-radar/backend/venv/bin/python",
      "args": ["/absolute/path/to/AI-radar/backend/skills/research_skill_v0.1.py"],
      "env": {},
      "type": "stdio"
    }
  }
}
```

### 3. 验证

重启 Claude Code 会话后：

```
你：列出你现在可用的 mcp tools
Claude Code：会列出 mcp__radar__research_quick 和 mcp__radar__research_deep
```

### 4. 跑一次调研

```
你：帮我调研 Anthropic Claude 4.6，用浅调研
Claude Code：[调 Radar skill] → [收到 ¥0.49 账单] → [等你付钱]
你：已支付
Claude Code：[生成调研问卷] → [等你答] → [按框架跑调研] → [输出报告]
```

---

## 快速开始（手动测试 demo）

不装 Claude Code，也能直接看 Radar 的 3 步流程：

```bash
cd AI-radar/backend
venv/bin/python skills/tests/test_demo.py
```

会输出：
- MCP 协议初始化
- 2 个 tool 列表
- 浅调研「调研 Anthropic」完整 3 步
- 深调研「调研 MCP 生态」完整 3 步
- 错误场景

---

## 目录结构

```
AI-radar/
├── README.md                                ← 你正在读
├── CLAUDE.md                                ← 项目根手册（AI 接手必读）
├── backend/
│   ├── skills/                              ← v0.2 阶段 0：调研 Skill（核心）
│   │   ├── research_skill_v0.1.py             ← MCP server（手写 stdio JSON-RPC）
│   │   ├── content/                            ← 静态方法论资产
│   │   │   ├── questionnaire_rules.md           ← 调研问卷设计规则
│   │   │   ├── framework_quick.md               ← 浅调研框架 + AI PM 5 维度
│   │   │   └── framework_deep.md                ← 深调研框架 + 4 增强维度
│   │   └── tests/test_demo.py                  ← 3 步流程模拟测试
│   ├── main.py                              ← v0.1 阶段 2 素材（暂不删）
│   ├── mcp_server.py                        ← v0.1 旧版（暂不删）
│   ├── seed.py / models.py                  ← v0.1 阶段 2 素材
│   ├── ingest/                              ← v0.1 RSS fetcher（暂不删）
│   └── venv/                                ← Python 3.9+ 虚拟环境
├── docs/
│   ├── product-brief.md                     ← 待重写为 v0.3
│   ├── launch-roadmap.md                    ← 待重写
│   └── ...
└── archive/                                 ← v0.1 数据 API 旧版归档（未来）
```

---

## 当前状态（2026-06-21）

- ✅ **阶段 0 demo 跑通**：`test_demo.py` 验证 3 步流程
- ✅ **Claude Code 集成验证通过**：实测在 Claude Code 里走完 3 步，输出真实调研报告
- ✅ **核心方法论 IP 完成**：问卷设计规则 + 5 维度评估法 + 4 增强维度
- ⏳ **支付宝 A2M 真商户资质**：需要申请，等支付宝开放
- ⏳ **docs/ 文档重写**：v0.3 product-brief + roadmap
- ⏳ **2 个 tool 的 description 优化**：让 Claude Code 更倾向主动调 Radar

---

## License

TBD
