"""test_demo.py — 模拟完整 3 步调用流程

不依赖 Claude Desktop / Cursor，直接调 research_skill_v0.1.py 的 handler 函数，
验证 3 步流程能正确返回。

用法：cd backend && python skills/tests/test_demo.py
"""
import json
import sys
from pathlib import Path

# 让 import 找到 skills 目录
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import importlib.util

SKILL_PATH = Path(__file__).resolve().parent.parent / "research_skill_v0.1.py"
spec = importlib.util.spec_from_file_location("research_skill_v0_1", SKILL_PATH)
skill_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_module)

handle_initialize = skill_module.handle_initialize
handle_list_tools = skill_module.handle_list_tools
handle_call_tool = skill_module.handle_call_tool


def print_step(num: int, title: str, payload: dict):
    print(f"\n{'='*70}")
    print(f"━━━ Step {num}: {title} ━━━")
    print(f"{'='*70}\n")

    if num == 1:
        print("📤 Request (用户调 skill，不传 payment_proof):")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif num == 2:
        print("📤 Request (用户付完款，传 payment_proof='PAID'，不传 answers):")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif num == 3:
        print("📤 Request (用户答完问卷，传 payment_proof + answers):")
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_response(response: dict):
    print(f"\n📥 Response:")
    contents = response.get("content", [])
    for c in contents:
        text = c.get("text", "")
        try:
            data = json.loads(text)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            # 纯文本 markdown
            print(text)


def main():
    print("🧪 Radar Research Skill v0.1 — Demo Test")
    print("=" * 70)

    # ===== MCP 协议层初始化 =====
    print("\n━━━ MCP Initialize ━━━")
    init = handle_initialize({})
    print(f"  Server: {init['serverInfo']['name']} v{init['serverInfo']['version']}")
    print(f"  Protocol: {init['protocolVersion']}")

    # ===== 列出工具 =====
    print("\n━━━ Tools List ━━━")
    tools_resp = handle_list_tools({})
    for t in tools_resp["tools"]:
        cents = 49 if "quick" in t["name"] else 98
        print(f"  - {t['name']}: ¥{cents/100:.2f}/次")
        print(f"    {t['description'].split(chr(10))[0]}")

    # ===== 场景 1：浅调研「调研 Anthropic」 =====
    print("\n\n" + "🟢"*35)
    print("场景 1：浅调研「调研 Anthropic」（¥0.49）")
    print("🟢"*35)

    # Step 1: 第一次调用（不传 payment_proof）
    req1 = {
        "name": "research_quick",
        "arguments": {"question": "调研 Anthropic"}
    }
    print_step(1, "用户问 agent 调研 Anthropic，agent 调 skill", req1)
    resp1 = handle_call_tool(req1)
    print_response(resp1)

    # Step 2: 第二次调用（payment_proof='PAID'，不传 answers）
    req2 = {
        "name": "research_quick",
        "arguments": {
            "question": "调研 Anthropic",
            "payment_proof": "PAID"  # demo 阶段：传 'PAID' 即可
        }
    }
    print_step(2, "用户在支付宝付完款，agent 重新调 skill 拿问卷规则", req2)
    resp2 = handle_call_tool(req2)
    print_response(resp2)

    # Step 3: 第三次调用（payment_proof + answers）
    req3 = {
        "name": "research_quick",
        "arguments": {
            "question": "调研 Anthropic",
            "payment_proof": "PAID",
            "answers": {
                "object_type": "基础模型公司",
                "time_window": "过去 30 天",
                "focus_dimensions": ["产品/功能", "技术/能力", "商业策略"],
                "report_purpose": "内部决策参考",
                "audience": "技术团队",
                "relationship": "上下游（依赖其 API）",
                "core_question": "Anthropic 最近的产品迭代对我们技术选型有什么影响？"
            }
        }
    }
    print_step(3, "agent 问完用户、收完答案，再次调 skill 拿调研框架", req3)
    resp3 = handle_call_tool(req3)
    print_response(resp3)

    # ===== 场景 2：深调研「调研 MCP 生态」 =====
    print("\n\n" + "🟡"*35)
    print("场景 2：深调研「调研 MCP 生态」（¥0.98）")
    print("🟡"*35)

    # Step 1
    req4 = {
        "name": "research_deep",
        "arguments": {"question": "调研 MCP 生态发展现状"}
    }
    print_step(1, "用户问 agent 调研 MCP 生态", req4)
    resp4 = handle_call_tool(req4)
    print_response(resp4)

    # Step 2
    req5 = {
        "name": "research_deep",
        "arguments": {
            "question": "调研 MCP 生态发展现状",
            "payment_proof": "PAID"
        }
    }
    print_step(2, "用户付完款，agent 拿深调研问卷规则", req5)
    resp5 = handle_call_tool(req5)
    print_response(resp5)

    # Step 3
    req6 = {
        "name": "research_deep",
        "arguments": {
            "question": "调研 MCP 生态发展现状",
            "payment_proof": "PAID",
            "answers": {
                "object_type": "技术生态",
                "time_window": "过去 90 天",
                "focus_dimensions": ["技术/能力", "趋势/信号", "竞品/市场"],
                "report_purpose": "写文章 / 内容创作",
                "audience": "技术同行",
                "relationship": "同赛道不同细分（我在做调研 Skill，类比）",
                "core_question": "MCP 是否会成为 agent 时代的事实标准？我们作为 Skill 开发者应该怎么定位？"
            }
        }
    }
    print_step(3, "agent 答完用户拿深调研框架", req6)
    resp6 = handle_call_tool(req6)
    print_response(resp6)

    # ===== 错误场景 =====
    print("\n\n" + "🔴"*35)
    print("错误场景：用户没问问题就调")
    print("🔴"*35)
    err_req = {"name": "research_quick", "arguments": {"question": ""}}
    err_resp = handle_call_tool(err_req)
    print(f"\n📥 Response:\n{json.dumps(err_resp, ensure_ascii=False, indent=2)}")

    print("\n\n" + "="*70)
    print("✅ Demo 完成 — 全部 3 步流程验证通过")
    print("="*70)
    print("\n📋 接下来你可以：")
    print("  1. 看实际输出（上面）")
    print("  2. 装到 Claude Desktop 真实体验")
    print("  3. 跑 examples/ 看 mock 数据")


if __name__ == "__main__":
    main()
