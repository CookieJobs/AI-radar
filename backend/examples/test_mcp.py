"""最小 MCP host：模拟 Claude Desktop 通过 stdio 调 Radar。

用法：venv/bin/python examples/test_mcp.py
"""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["/Users/liujin/Documents/hermesWorkspace/ai-radar/backend/mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1) initialize
            await session.initialize()
            print("[host] MCP handshake 完成\n")

            # 2) 列出工具
            tools = await session.list_tools()
            print(f"[host] 工具列表 ({len(tools.tools)} 个):")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description[:60]}...")
            print()

            # 3) 调用 list_events
            print("[host] 调用 list_events(domain=agent, min_impact=3, limit=5):")
            result = await session.call_tool("list_events", {"domain": "agent", "min_impact": 3, "limit": 5})
            data = json.loads(result.content[0].text)
            print(f"  命中: {data['total']} 条")
            for e in data["events"][:3]:
                print(f"    - [{e['timestamp'][:10]}] {e['headline']}")
            print()

            # 4) 调用 get_top_impact
            print("[host] 调用 get_top_impact(since=14d, limit=3):")
            result = await session.call_tool("get_top_impact", {"since": "14d", "limit": 3})
            data = json.loads(result.content[0].text)
            print(f"  top impact 事件: {data['total']} 条")
            for e in data["events"]:
                print(f"    - {e['headline']}")
            print()

            # 5) 调用 get_event
            print("[host] 调用 get_event(evt_2026_0606_deepseek_r2):")
            result = await session.call_tool("get_event", {"event_id": "evt_2026_0606_deepseek_r2"})
            data = json.loads(result.content[0].text)
            print(f"  headline: {data['headline']}")
            print(f"  insight: {data['summary_insight'][:80]}...")

    print("\n[host] MCP 协议层验证通过 ✓")


if __name__ == "__main__":
    asyncio.run(main())
