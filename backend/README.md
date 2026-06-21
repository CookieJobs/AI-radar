# Radar Backend (v0.2)

B2A AI 行业情报 API 的最小可运行版本。

## 启动

```bash
cd ~/Documents/hermesWorkspace/ai-radar/backend
venv/bin/python main.py
```

服务跑在 `http://127.0.0.1:8765`。

## API 端点

| 端点 | 方法 | 用途 |
|---|---|---|
| `/` | GET | 服务元信息 |
| `/v1/events` | GET | 事件列表（支持 domain/category/min_impact/since/limit 过滤） |
| `/v1/events/{id}` | GET | 单个事件详情 |
| `/v1/ask` | POST | 深度问答（v0.2 stub） |
| `/docs` | GET | Swagger UI |

## 调用示例

```bash
# 最近 30 天 LLM 领域 impact >= 4 的事件
curl 'http://127.0.0.1:8765/v1/events?domain=llm&min_impact=4&since=30d&limit=5'

# 单个事件
curl 'http://127.0.0.1:8765/v1/events/evt_2026_0606_deepseek_r2'
```

## 限速

- 60 次/分钟 / IP
- 1000 次/天 / IP
- 触发后返回 429 + 提示

## Demo Agent

```bash
venv/bin/python examples/demo_agent.py
```

模拟一个 AI PM 的 agent：拉事件 → 拿详情 → 输出结构化报告。

## 目录

```
backend/
├── main.py              # FastAPI 入口 + 限速中间件
├── models.py            # Event / EventList 数据模型
├── seed.py              # 50 条种子事件（2026-06 上半月真实事件）
├── examples/
│   └── demo_agent.py    # demo agent 调通样例
├── data/
│   └── (后续: SQLite 持久化)
└── venv/                # Python 虚拟环境
```

## 已知 TODO（v0.3 路线）

- [ ] SQLite 持久化（现 50 条 in-memory）
- [ ] 真实 RSS / 信源抓取脚本
- [ ] MCP server 包装（暴露给 Claude Desktop / Cursor）
- [ ] 接入微信 / 支付宝 agent 钱包 SDK
- [ ] 深度问答 `/v1/ask` 接 RAG
