# Radar API — 字段设计 v0.2

> 版本：v0.2（2026-06-20 同步 backend 实际实现，替代 v0.1）
> 状态：MVP 已上线（REST + MCP 双通道，49 条种子事件）
> 一句话：**B2A AI 行业情报 API —— agent 调一次，拿到事件 + 解读 + 推演**

---

## 〇、版本变化（vs v0.1）

v0.1 → v0.2 的核心转向：**从"订阅 + 周报"切到"纯 B2A 按调用"**。

| 维度 | v0.1 | v0.2 |
|---|---|---|
| 端点 | `/v1/events` / `/v1/events/{id}` / `/v1/daily` | `/v1/events` / `/v1/events/{id}` / `/v1/ask` (stub) |
| 字段 | 含 `url_article`（周报人读版 URL） | **删除** `url_article`，纯 API 交付 |
| 限速 | 按订阅档位（免费/¥39/¥199/企业） | **冷启动期一律 IP 60/min + 1000/day** |
| 鉴权 | API Key（Bearer Token） | 冷启动期**暂不鉴权**（钱包上线后切 key） |
| MCP | v1.0 计划项 | **v0.2 已落地**（stdio 协议，3 个 tool） |
| 数据 | in-memory | in-memory（v0.3 切 SQLite + RSS 抓取） |

**核心判断**：v0.1 假设"先做订阅、再加 API"——事实证明纯 API 才能搭上 agent 钱包的顺风车。直接砍。

---

## 一、API 设计原则

### 1.1 agent 优先

- **RESTful**——agent 最容易理解
- **JSON only**——不返回 HTML
- **字段名稳定**——一旦发布不轻易改
- **错误码清晰**——让 agent 能自动处理
- **冷启动期不鉴权**——降低接入摩擦（v0.3 接 key）

### 1.2 4 层数据结构

每条事件必须包含：

- **L1 事实**（`summary_fact`）——发生了什么
- **L2 标签**（`domain` / `category` / `tags` / `impact_level` / `confidence`）——分类、重要性、可信度
- **L3 解读**（`summary_insight`）——这意味着什么（**人写**）
- **L4 推演**（`summary_forecast`）——未来 30 天怎么演化（**人写**）

### 1.3 信任字段必填

每条数据必带：

- `confidence`：判断置信度（0-1）
- `source`：来源 URL 数组
- `timestamp`：事件发生时间 + `ingested_at` 入库时间

### 1.4 与 MCP tool 的关系

REST 端点 + MCP tool **1:1 对应**，schema 同步演进：

| REST 端点 | MCP tool | 说明 |
|---|---|---|
| `GET /v1/events` | `list_events` | 事件流查询（支持过滤） |
| `GET /v1/events/{id}` | `get_event` | 单个事件详情 |
| `POST /v1/ask` | （v0.3 加 `ask_radar`） | 深度问答（v0.2 stub，v0.3 接 RAG） |
| — | `get_top_impact` | MCP 专属便捷 tool（REST 等价于 list_events + min_impact=5） |

---

## 二、核心端点

### 2.1 `GET /v1/events` — 查询事件

**查询参数：**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `domain` | enum | 否 | all | `llm` / `agent` / `tooling` / `infra` / `application` / `policy` / `business` |
| `category` | enum | 否 | all | 11 个类别（见 models.py 的 `Category` Literal） |
| `min_impact` | int (1-5) | 否 | 1 | 最低重要性 |
| `since` | string | 否 | — | 时间窗口：`7d` / `24h` / ISO date |
| `limit` | int | 否 | 20 | 返回数量上限（max 100） |

**响应示例：**

```json
{
  "total": 3,
  "query": {"domain": "llm", "min_impact": 4, "since": "30d", "limit": 3},
  "events": [
    {
      "id": "evt_2026_0617_anthropic_claude45",
      "timestamp": "2026-06-17T08:30:00Z",
      "domain": "llm",
      "category": "model_release",
      "entities": ["Anthropic", "Claude"],
      "headline": "Anthropic 发布 Claude 4.5，编程能力 SOTA，定位 agent 工作流",
      "summary_fact": "（200-300 字事实摘要）",
      "summary_insight": "（200-300 字专家解读，对 OPC 创业者意味着什么）",
      "summary_forecast": "（60-150 字未来 30 天推演）",
      "impact_level": 5,
      "confidence": 0.95,
      "tags": ["model_release", "agent", "programming", "anthropic"],
      "source": [
        {"name": "Anthropic 官方", "url": "https://www.anthropic.com/news/claude-4-5"}
      ]
    }
  ]
}
```

### 2.2 `GET /v1/events/{id}` — 获取单个事件

**路径参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `id` | string | 事件 ID（如 `evt_2026_0617_anthropic_claude45`） |

**响应**：单个 event 对象（结构同上）。`404` 时返回 `{"detail": "event not found: <id>"}`。

### 2.3 `POST /v1/ask` — 深度问答（v0.2 stub）

**请求体：**

```json
{"q": "Anthropic Claude 4.5 之后呢?"}
```

**v0.2 响应（stub）：**

```json
{
  "answer": "深度问答功能开发中。当前请使用 /v1/events 获取结构化事件。",
  "hint": "v0.3 会接入向量检索。",
  "received": {"q": "Anthropic Claude 4.5 之后呢?"}
}
```

**v0.3 计划**：接 RAG（向量检索事件库 + LLM 综合），定价 5 credits/次 = ¥0.5/次。

### 2.4 `GET /` — 服务元信息

返回服务版本、事件总数、限速策略、端点列表。**不计限速**（用于健康检查）。

### 2.5 `GET /docs` — Swagger UI

FastAPI 自动生成。**不计限速**。

---

## 三、字段定义（详细）

### 3.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | ✅ | 唯一 ID，格式 `evt_YYYY_MMDD_<entity>_<slug>` |
| `timestamp` | ISO 8601 | ✅ | 事件发生时间（UTC） |
| `domain` | enum (7) | ✅ | llm / agent / tooling / infra / application / policy / business |
| `category` | enum (11) | ✅ | model_release / model_capability / funding / acquisition / product_launch / api_pricing / research / policy / open_source / agent_framework / benchmark / partnership |
| `entities` | string[] | ✅ | 涉及的实体（公司、产品、人名） |
| `headline` | string | ✅ | 标题（< 200 字） |

### 3.2 内容字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `summary_fact` | string | ✅ | 事实摘要（100-300 字） |
| `summary_insight` | string | ✅ | 解读（100-300 字，对 OPC 创业者意味着什么） |
| `summary_forecast` | string | ✅ | 推演（60-150 字，未来 30 天怎么演化） |
| `tags` | string[] | ✅ | 标签 |

### 3.3 信任字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `impact_level` | int (1-5) | ✅ | 重要性等级（1=低，5=改变格局） |
| `confidence` | float (0-1) | ✅ | 置信度 |
| `source` | object[] | ✅ | 来源列表 `[{name, url}]` |

### 3.4 v0.1 → v0.2 删除字段

| 字段 | 原因 |
|---|---|
| `url_article` | v0.2 不做人读版 |
| `price_credit` | 冷启动期全部免费，credits 字段不暴露 |
| `related_events` | v0.2 暂未实现 |
| `ingested_at`（响应中） | **保留**在数据库，但响应中暂不返回（待 v0.3 决定） |

---

## 四、错误处理

### 4.1 HTTP 状态码

| 状态码 | 含义 | 触发 |
|---|---|---|
| 200 | 成功 | — |
| 400 | 请求参数错误 | `since` 解析失败、参数越界 |
| 404 | 事件不存在 | `GET /v1/events/{id}` 找不到 |
| 422 | Pydantic 校验失败 | FastAPI 自动处理 |
| 429 | 调用次数超限 | 限速触发 |
| 500 | 服务器错误 | 未捕获异常 |

### 4.2 错误响应示例

**400（参数错误）：**
```json
{"detail": "无法解析 since: abc"}
```

**404（事件不存在）：**
```json
{"detail": "event not found: evt_xxx"}
```

**429（限速）：**
```json
{
  "error": "rate_limited",
  "reason": "minute_limit_exceeded (60/min)",
  "hint": "Radar 冷启动期全部免费，但有 IP 限速。等 agent 钱包上线后接入，按调用计费。"
}
```

---

## 五、限流策略

### 5.1 v0.2 冷启动期（**全部免费**）

| 维度 | 阈值 |
|---|---|
| 单 IP 每分钟 | 60 次 |
| 单 IP 每天 | 1000 次 |
| 鉴权 | **无**（钱包上线后切 key） |

### 5.2 v0.3+ 付费期（待定）

| 用户类型 | 限流 | 计费 |
|---|---|---|
| 免费 | 100 次/天、5 次/分钟 | — |
| Agent API（按调用） | 无 IP 限速 | ¥0.1-0.5/次 |

> **砍掉的 v0.1 档位**：个人订阅 ¥39/月、团队订阅 ¥199/月、企业 API ¥999/月起——全部作废。B2A 不做订阅。

### 5.3 实现细节

- 限速中间件：`backend/main.py` 的 `rate_limit_middleware`
- 计数存储：进程内 `defaultdict(deque)`（v0.3 切 Redis）
- 触发后返回 429 + 友好 hint 文案
- `/`、`/docs` 跳过限速

---

## 六、MCP 协议层（v0.2 新增）

### 6.1 工具清单

| Tool | 输入 | 说明 |
|---|---|---|
| `list_events` | `domain?, category?, min_impact?, since?, limit?` | 查询事件流 |
| `get_event` | `event_id` (必填) | 单个事件详情 |
| `get_top_impact` | `since?, limit?` | 高影响力事件（min_impact=5） |

### 6.2 协议细节

- **传输**：stdio（stdin/stdout JSON-RPC）
- **实现**：`backend/mcp_server.py`（Server 来自 `mcp>=1.0.0`）
- **host 接入**：Claude Desktop / Cursor / Cline / Windsurf（详见 `docs/mcp-integration-guide.md`）

### 6.3 tool schema（与 REST 对齐）

MCP `inputSchema` 的字段名、枚举值、默认值与 REST query params **完全一致**，方便 agent 主人切换。

---

## 七、技术实现

### 7.1 当前栈

| 层 | 选型 | 备注 |
|---|---|---|
| Web 框架 | FastAPI 0.128+ | 自动 OpenAPI 文档 |
| 数据模型 | Pydantic v2 | `Literal` 限定枚举 |
| 数据 | in-memory `EVENTS` 列表 | v0.3 切 SQLite |
| 协议 | REST + MCP 双通道 | — |
| Python | 3.10+ | mcp 包最低要求 |

### 7.2 v0.2 文件结构

```
backend/
├── main.py              # FastAPI 入口 + 限速中间件
├── mcp_server.py       # MCP server（stdio）
├── models.py            # Pydantic Event / EventList
├── seed.py              # 49 条种子事件
├── examples/
│   ├── demo_agent.py    # REST demo（已跑通）
│   └── test_mcp.py      # MCP 协议层验证（需 Python 3.10+）
└── requirements.txt
```

### 7.3 v0.2 验收 checklist

- [x] 5 个端点实现（`/` + `events` 列表/详情 + `ask` stub + `docs`）
- [x] 49 条种子事件入库
- [x] Swagger 文档自动生成
- [x] 限速 60/min + 1000/day 触发返回 429
- [x] MCP 3 个 tool 代码完成（3.10+ 跑过 handshake）
- [x] demo agent 跑通

---

## 八、待定项

- [ ] API key 发放机制（自建 vs 第三方如 Stripe / Paddle）
- [ ] Credits 计费系统
- [ ] SQLite 持久化（替代 in-memory）
- [ ] RSS 抓取脚本 v0.1
- [ ] RAG 接 `/v1/ask`
- [ ] 域名 + 公开 URL（radar.dev / getradar.io / radarai.cn）

详细见 `docs/launch-roadmap.md` 阶段 0 / 阶段 1。
