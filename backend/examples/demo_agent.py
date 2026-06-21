"""demo_agent.py — 模拟一个 AI 产品经理的 agent，调 Radar API"""
import sys
import httpx
import json

BASE = "http://127.0.0.1:8765"


def fetch_top_events(domain: str = "llm", min_impact: int = 4, since: str = "30d"):
    """agent 调 /v1/events 拿到最近 30 天的高影响力事件"""
    url = f"{BASE}/v1/events"
    params = {"domain": domain, "min_impact": min_impact, "since": since, "limit": 5}
    print(f"[agent] 调: GET {url}?{urlencode(params)}")
    r = httpx.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def urlencode(params: dict) -> str:
    return "&".join(f"{k}={v}" for k, v in params.items())


def summarize_for_user(data: dict):
    """agent 把 Radar 返回的 JSON 翻译成人话给用户"""
    print(f"\n[agent] 拿到 {data['total']} 条事件，按时间倒序：\n")
    for i, evt in enumerate(data["events"], 1):
        print(f"{i}. [{evt['timestamp'][:10]}] impact={evt['impact_level']}/5  {evt['headline']}")
        print(f"   事实: {evt['summary_fact'][:80]}...")
        print(f"   解读: {evt['summary_insight'][:80]}...")
        print(f"   推演: {evt['summary_forecast'][:80]}...")
        print()


def fetch_one_event(event_id: str):
    """agent 按 id 拿单个事件详情"""
    url = f"{BASE}/v1/events/{event_id}"
    print(f"[agent] 调: GET {url}")
    r = httpx.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def main():
    print("=" * 70)
    print("demo_agent — 模拟一个 AI 产品经理的 agent")
    print("目标: 看看最近 30 天 LLM 领域最值得关注的 5 条事件")
    print("=" * 70)

    # 1) 拉 top events
    data = fetch_top_events(domain="llm", min_impact=4, since="30d")
    summarize_for_user(data)

    # 2) 用户追问某一条详情
    if data["events"]:
        first_id = data["events"][0]["id"]
        print(f"\n[user] 那第一条 '{data['events'][0]['headline'][:30]}...' 我想看完整解读")
        detail = fetch_one_event(first_id)
        print(f"\n[agent] 完整事件: {json.dumps(detail, ensure_ascii=False, indent=2)[:800]}...")

    print("\n" + "=" * 70)
    print("demo 结束。结论: agent 调 Radar 一次，拿到结构化情报 + 解读 + 推演。")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print(f"\n[error] 连不上 {BASE}。请先启动 Radar 服务：")
        print("  cd backend && venv/bin/python main.py")
        sys.exit(1)
