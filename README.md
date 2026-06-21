# Radar

> **B2A（Business to Agent）模式的 AI 行业情报 API。**
> agent 调一次，拿到事件 + 解读 + 推演。**只做 API，不做人读版。**

[![MCP](https://img.shields.io/badge/MCP-compatible-blue)]()
[![Status](https://img.shields.io/badge/status-cold_start-yellow)]()
[![License](https://img.shields.io/badge/license-TBD-lightgrey)]()

---

## 🤖 For AI Agents — 接手必读

**如果你是另一个 AI agent 接手这个项目，按这个顺序读：**

1. **[CLAUDE.md](./CLAUDE.md)** ← 项目根手册（最先读，5 分钟拿到全局上下文）
2. **[docs/00-context.md](./docs/00-context.md)** ← 6 轮讨论的浓缩版，决策来源
3. **[docs/product-brief.md](./docs/product-brief.md)** ← 产品方案 v0.2 全文
4. **[docs/launch-roadmap.md](./docs/launch-roadmap.md)** ← 90 天冷启动路线图
5. **[docs/mcp-integration-guide.md](./docs/mcp-integration-guide.md)** ← 如果你要做 MCP 集成
6. **[backend/README.md](./backend/README.md)** ← 如果你要动代码

**不变量**（不许改的核心决策）：
- ✅ 卖**判断**不卖信息（L3 解读 + L4 推演，不是 L1 数据搬运）
- ✅ 一次生产，**只走 API**（不做周报 / 订阅 / 人读版）
- ✅ 化名 = **Radar**（不暴露公司名）
- ✅ 冷启动期**完全免费**，等微信/支付宝 agent 钱包上线再按调用 ¥0.1-0.5/次
- ✅ **人写判断**（insight / forecast），AI 只做事实摘要 + 格式转换

**商业道德红线**（绝对不能踩）：
- ❌ 前公司未公开的用户数据、教学内容、产品数据
- ❌ 客户名单、未公开产品规划、未公开财务
- ❌ 任何违反 NDA / 保密协议的素材
- ✅ 只用：公开信源 + 个人方法论 + 自购素材二次加工

---

## 📦 这是什么

**Radar** 是个 AI 行业情报 API。agent 可以通过 REST 或 MCP 协议调用它，拿到结构化的"事件 + 事实 + 解读 + 推演"。

**两条 SKU**：
1. **实时事件 API** (`GET /v1/events`) — 查询事件流（按 domain / category / impact / 时间窗口过滤）
2. **深度问答 API** (`POST /v1/ask`) — v0.2 是 stub，v0.3 接 RAG

**两条分发通道**：
1. **REST API** — 传统 HTTP，IP 限速 60/min + 1000/day
2. **MCP server** — 给 Claude Desktop / Cursor / Cline / Windsurf 等 agent host 直接调用

**当前状态**：MVP 已跑通（49 条种子事件 + REST + MCP），进入冷启动期。

---

## 🚀 快速开始

### 跑 REST API（后台服务）

```bash
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
# → http://127.0.0.1:8765
# → Swagger UI: http://127.0.0.1:8765/docs
```

### 跑 MCP server（让 agent 直接调）

```bash
cd backend
venv/bin/python mcp_server.py
# 然后在你的 MCP host 里配（详见 docs/mcp-integration-guide.md）
```

### 验证一切正常

```bash
cd backend
venv/bin/python examples/demo_agent.py   # REST demo
venv/bin/python examples/test_mcp.py     # MCP 协议层验证
```

---

## 📁 项目结构

```
ai-radar/
├── README.md                       ← 你正在读（GitHub 入口）
├── CLAUDE.md                       ← 项目根手册（AI 接手必读）
├── LICENSE                         ← 待定
├── .gitignore
├── docs/
│   ├── 00-context.md               ← 6 轮讨论浓缩版
│   ├── product-brief.md            ← 产品方案 v0.2
│   ├── launch-roadmap.md           ← 90 天路线图
│   ├── b2a-value-logic.md          ← B2A 价值逻辑（v0.1 待重写）
│   └── mcp-integration-guide.md    ← MCP 集成教程
├── data/
│   └── source-list-v0.1.md         ← 40 个信源清单（30 EN + 10 CN）
├── api/
│   └── schema-v0.1.md              ← API 字段设计（待重写）
├── backend/
│   ├── main.py                     ← FastAPI 入口 + 限速中间件
│   ├── mcp_server.py               ← MCP server（stdio）
│   ├── models.py                   ← Pydantic 数据模型
│   ├── seed.py                     ← 49 条种子事件（2026-06 上半月真实事件）
│   ├── examples/
│   │   ├── demo_agent.py           ← REST demo agent
│   │   └── test_mcp.py             ← MCP 协议层验证脚本
│   ├── README.md                   ← 后端启动说明
│   └── requirements.txt
└── archive/                        ← 已废弃版本
```

---

## 🛠️ 技术栈

| 层 | 选择 | 理由 |
|---|---|---|
| 后端框架 | FastAPI | 轻、文档自动生成、异步友好 |
| 数据 | SQLite（未来）+ in-memory（当前） | MVP 不引入依赖 |
| 协议 | REST + MCP（双通道） | REST 给传统调用，MCP 给 agent |
| LLM 框架 | 不依赖 | Radar 本身是数据源，不用 LLM |
| 部署 | 本地 `uvicorn`（未来 Cloudflare/Vercel） | 冷启动期不上云 |
| Python | 3.11+ | pydantic v2 + mcp 包 |

---

## 📊 当前进度（截至 2026-06-18）

✅ 已完成：
- 项目立项 + 商业模式决策（纯 B2A）
- 产品方案 v0.2（砍订阅/砍周报）
- 49 条种子事件入库
- REST API 4 个端点全部跑通
- MCP server 3 个工具，协议层验证通过
- MCP 集成教程文档
- 90 天路线图

⏳ 待办（roadmap 阶段 0）：
- [ ] 域名注册（radar.dev / getradar.io / radarai.cn）
- [ ] **RSS 抓取脚本 v0.1**（40 信源，每天入 1-2 条）
- [ ] Claude Desktop 本机接入验证
- [ ] 找 3 个 agent 主人内测
- [ ] SQLite 持久化
- [ ] `/v1/ask` 接 RAG
- [ ] `docs/b2a-value-logic.md` 同步 v0.2
- [ ] `api/schema-v0.1.md` 重写

详细见 [docs/launch-roadmap.md](./docs/launch-roadmap.md)。

---

## 💡 核心产品逻辑

**为什么 Radar 卖得动？**

1. **窗口期**：2026 H2 - 2027 H1 是"agent 数据源"赛道的窗口期，微信/支付宝 agent 钱包即将上线
2. **真实痛点**：OPC 创业者 / AI PM / 早期投资人的 agent 需要持续喂行业信息，自己刷 50 个信源太累
3. **不可替代**：判断 + 推演 = 大模型自己做不到的，必须人写
4. **规模效应**：事件库越大，调用频率越高，单位成本越低
5. **护城河**：品牌 + 个人 IP + 数据沉淀 + agent 生态卡位

**为什么不订阅 / 不做周报？**

- 周报是个人 IP 时代的产物，获客路径长
- 订阅对个人作者是负担（每周维护）
- 纯 B2A 直接对接 agent 钱包上线后的"按调用付费"基础设施
- 卖的是"情报给 agent 调"，不是"内容给读者"

---

## 🤝 贡献 / 接入

### 我想接入 Radar（agent 主人）

详见 [docs/mcp-integration-guide.md](./docs/mcp-integration-guide.md)

### 我想贡献事件数据 / 信源

PR 到 `data/source-list-v0.1.md`，附：
- 信源 URL
- 更新频率
- 一句话定位
- 评分（时效性 / 准确性 / 深度 / 独家 / 对 Radar 的价值，各 1-5 分）

### 我想动代码

1. Fork → 建 feature branch
2. 改 backend/ → 跑 examples/test_mcp.py 验证 MCP 不破
3. PR 描述里说明改了什么 + 为什么

---

## 📝 License

TBD（待定）

---

## 🏷️ 项目元信息

- **创建日期**：2026-06-18
- **品牌**：Radar
- **作者身份**：AI 产品经理（化名出镜，不暴露公司名）
- **工作目录**：`~/Documents/hermesWorkspace/ai-radar/`
- **GitHub**：https://github.com/CookieJobs/AI-radar.git
- **工具栈**：Hermes / Claude Code / Cursor 跨工具协作