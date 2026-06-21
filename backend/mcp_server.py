"""Radar MCP Server — 把 REST API 包装成 MCP 协议，供 Claude Desktop / Cursor 等 agent 直接调用。

启动方式：
    cd backend && venv/bin/python mcp_server.py

接入 Claude Desktop（~/Library/Application Support/Claude/claude_desktop_config.json）：
    {
      "mcpServers": {
        "radar": {
          "command": "/Users/liujin/Documents/hermesWorkspace/ai-radar/backend/venv/bin/python",
          "args": ["/Users/liujin/Documents/hermesWorkspace/ai-radar/backend/mcp_server.py"]
        }
      }
    }

接入 Cursor（Settings → MCP）：
    同上，加一行 type: "stdio"
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from models import Event
from seed import EVENTS


# ---------- MCP server ----------
app = Server("radar")


def _parse_since(since: str) -> float:
    """'30d' / '24h' / ISO date -> epoch seconds"""
    now = datetime.now(timezone.utc).timestamp()
    if since.endswith("d"):
        return now - int(since[:-1]) * 86400
    if since.endswith("h"):
        return now - int(since[:-1]) * 3600
    try:
        return datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _filter_events(
    domain: Optional[str] = None,
    category: Optional[str] = None,
    min_impact: int = 1,
    since: Optional[str] = None,
    limit: int = 20,
) -> list[Event]:
    results = list(EVENTS)
    if domain:
        results = [e for e in results if e.domain == domain]
    if category:
        results = [e for e in results if e.category == category]
    results = [e for e in results if e.impact_level >= min_impact]
    if since:
        cutoff = _parse_since(since)
        results = [e for e in results if e.timestamp.timestamp() >= cutoff]
    results.sort(key=lambda e: e.timestamp, reverse=True)
    return results[:limit]


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_events",
            description=(
                "查询 Radar AI 行业情报事件流。每个事件包含事实摘要、专家解读、对 OPC 创业者的影响、"
                "未来 30 天推演。agent 调用此工具相当于订阅 Radar 的实时情报。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": ["llm", "agent", "tooling", "infra", "application", "policy", "business"],
                        "description": "领域过滤。可选。",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "model_release", "model_capability", "funding", "acquisition",
                            "product_launch", "api_pricing", "research", "policy",
                            "open_source", "agent_framework", "benchmark", "partnership",
                        ],
                        "description": "类别过滤。可选。",
                    },
                    "min_impact": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 1,
                        "description": "最低影响等级。1=轻微, 5=改变格局。默认 1。",
                    },
                    "since": {
                        "type": "string",
                        "description": "时间窗口。格式: '7d' / '24h' / ISO date (如 '2026-06-01')。默认 '30d'。",
                        "default": "30d",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                        "description": "返回数量上限。默认 10, 最大 50。",
                    },
                },
            },
        ),
        Tool(
            name="get_event",
            description="按 event_id 获取单个事件的完整详情（含事实/解读/推演/信源/标签）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "事件 ID, 例如 evt_2026_0615_wechat_agent_wallet",
                    },
                },
                "required": ["event_id"],
            },
        ),
        Tool(
            name="get_top_impact",
            description=(
                "获取最近一段时间内影响等级最高 (impact=5) 的事件。适合 agent 主人想快速知道"
                "'过去一周必须知道的 AI 行业大事' 时使用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "since": {"type": "string", "default": "7d", "description": "时间窗口, 默认 '7d'"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_events":
        results = _filter_events(
            domain=arguments.get("domain"),
            category=arguments.get("category"),
            min_impact=arguments.get("min_impact", 1),
            since=arguments.get("since", "30d"),
            limit=arguments.get("limit", 10),
        )
        payload = {
            "total": len(results),
            "query": {
                k: v for k, v in arguments.items() if v is not None
            },
            "events": [e.model_dump(mode="json") for e in results],
        }
        return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

    elif name == "get_event":
        eid = arguments.get("event_id")
        event = next((e for e in EVENTS if e.id == eid), None)
        if not event:
            return [TextContent(type="text", text=json.dumps({"error": f"event not found: {eid}"}, ensure_ascii=False))]
        return [TextContent(type="text", text=json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))]

    elif name == "get_top_impact":
        results = _filter_events(
            min_impact=5,
            since=arguments.get("since", "7d"),
            limit=arguments.get("limit", 10),
        )
        payload = {
            "total": len(results),
            "time_window": arguments.get("since", "7d"),
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "headline": e.headline,
                    "summary_fact": e.summary_fact,
                    "summary_insight": e.summary_insight,
                    "summary_forecast": e.summary_forecast,
                    "tags": e.tags,
                }
                for e in results
            ],
        }
        return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]

    return [TextContent(type="text", text=json.dumps({"error": f"unknown tool: {name}"}, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
