"""Radar Research Skill v0.1 — 调研界 Superpower

定位（不是数据 API，是方法论 Skill）：
- 用户 agent 调 Radar skill
- Radar 返回"调研问卷设计规则" / "AI PM 5 维度评估框架" / "报告模板"
- 用户 agent 拿到规则 → 调自己的 LLM → 生成问卷 → 问用户 → 收答案
- 用户 agent 再次调 Radar 拿框架 → 调自己 LLM 跑调研 → 输出报告

每个 tool 走 3 步：
1. 不传 payment_proof → 返回 A402 账单（模拟，阶段 0 不真扣钱）
2. 传 payment_proof="PAID" + 不传 answers → 返回调研问卷设计规则
3. 传 payment_proof="PAID" + answers → 返回 AI PM 调研框架 + 报告模板

技术栈：手写 stdio JSON-RPC（避免 mcp Python 包要 3.10+）
不依赖 LLM，不存数据，纯静态方法论分发。
"""
import json
import sys
from pathlib import Path
from typing import Optional


# ===== 加载静态方法论内容 =====
SKILLS_DIR = Path(__file__).resolve().parent
CONTENT_DIR = SKILLS_DIR / "content"

QUESTIONNAIRE_RULES = (CONTENT_DIR / "questionnaire_rules.md").read_text(encoding="utf-8")
FRAMEWORK_QUICK = (CONTENT_DIR / "framework_quick.md").read_text(encoding="utf-8")
FRAMEWORK_DEEP = (CONTENT_DIR / "framework_deep.md").read_text(encoding="utf-8")


# ===== 定价 =====
PRICE_QUICK_CENTS = 49       # ¥0.49
PRICE_DEEP_CENTS = 98        # ¥0.98
CURRENCY = "CNY"


# ===== 工具定义 =====
TOOLS = [
    {
        "name": "research_quick",
        "description": (
            "AI 产品经理调研 · 浅调研 · ¥0.49/次\n\n"
            "工作流程（3 步走完 1 次调研）：\n"
            "1. 第一次调用（不传 payment_proof）→ 返回 A402 账单（¥0.49）\n"
            "2. 第二次调用（payment_proof='PAID'，不传 answers）→ 返回调研问卷设计规则\n"
            "   用户 agent 拿到规则后，调自己的 LLM 生成具体问卷，问用户，收答案\n"
            "3. 第三次调用（payment_proof='PAID' + answers={...}）→ 返回 AI PM 浅调研框架 + 报告模板\n"
            "   用户 agent 拿到框架后，调自己的 LLM 按框架执行调研，输出报告\n\n"
            "输出：方法论 + 模板（不是执行结果）。\n"
            "真正的调研执行 = 用户 agent + 用户自己的 LLM。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "用户最初的调研问题，例如 '调研 Anthropic'"
                },
                "payment_proof": {
                    "type": "string",
                    "description": "支付宝 A2M 协议的 payment_proof。阶段 0 demo：传 'PAID' 即可"
                },
                "answers": {
                    "type": "object",
                    "description": "用户对调研问卷的答案。key = 问题 id，value = 答案"
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "research_deep",
        "description": (
            "AI 产品经理调研 · 深调研 · ¥0.98/次\n\n"
            "工作流程跟 research_quick 完全一样：\n"
            "1. 不传 payment_proof → 返回 A402 账单（¥0.98）\n"
            "2. payment_proof='PAID' → 返回调研问卷设计规则（10-15 题）\n"
            "3. payment_proof='PAID' + answers → 返回 AI PM 深调研框架（5 维度 + 4 增强维度）\n\n"
            "跟浅调研的差异：\n"
            "- 问卷 10-15 题（vs 浅 5-7）\n"
            "- 报告 1500-2500 字（vs 浅 800-1200）\n"
            "- 5 维度评估更详（每维度 2-3 段 + 引用）\n"
            "- 4 增强维度：多视角交叉验证、历史脉络、跨领域影响、反面观点\n"
            "- 适合：写文章、投融资材料、给老板的 brief"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "用户最初的调研问题"
                },
                "payment_proof": {
                    "type": "string",
                    "description": "支付宝 A2M 协议的 payment_proof。阶段 0 demo：传 'PAID' 即可"
                },
                "answers": {
                    "type": "object",
                    "description": "用户对调研问卷的答案"
                }
            },
            "required": ["question"]
        }
    }
]


# ===== 响应生成 =====
def payment_required_response(amount_cents: int, depth: str) -> str:
    """返回 A402 账单（阶段 0 模拟）"""
    return json.dumps({
        "status": "PAYMENT_REQUIRED",
        "http_status": 402,
        "amount_cents": amount_cents,
        "currency": CURRENCY,
        "amount_display": f"¥{amount_cents/100:.2f}",
        "description": f"Radar 调研 · {depth}调研 · ¥{amount_cents/100:.2f}",
        "protocol": "A2M (Alipay 402)",
        "merchant": "Radar Research Skill",
        "skill_action": "用户需在支付宝完成支付后，agent 携带 payment_proof='PAID' 重新调用",
        "next_step": "用户确认支付后，agent 调用同一个 tool 并传 payment_proof='PAID'"
    }, ensure_ascii=False, indent=2)


def render_questionnaire_response(question: str, depth: str) -> str:
    """返回调研问卷设计规则 + 建议结构"""
    return f"""# Radar 调研问卷设计规则（{depth}调研 · 已付费）

> 你最初的问题：**{question}**
>
> 用户 agent 拿到这份规则后，调自己的 LLM 生成具体问卷。
> 下面是基于 Radar 方法论生成的"问卷骨架"（按规则应该长这样）：

---

{QUESTIONNAIRE_RULES}

---

# 📋 建议的问卷骨架（{depth}调研）

按上面的规则，基于问题「{question}」，agent 应当生成以下结构的问卷：

```
# {depth}调研问卷（{depth}调研 · Radar Skill v0.1）

> 你最初的问题：{question}

## 问题 1: 调研对象是哪一类？
- [ ] 基础模型公司
- [ ] AI 应用层公司
- [ ] AI 基础设施
- [ ] 其他

## 问题 2: 时间窗口？
- [ ] 过去 7 天
- [ ] 过去 30 天
- [ ] 过去 90 天
- [ ] 过去 1 年
- [ ] 不限时间

## 问题 3: 重点关注哪些维度？（多选）
- [ ] 融资 / 商业
- [ ] 产品 / 功能
- [ ] 技术 / 能力
- [ ] 团队 / 高管
- [ ] 竞品 / 市场
- [ ] 趋势 / 信号

## 问题 4: 报告用途？
- [ ] 内部决策
- [ ] 投融资材料
- [ ] 写文章
- [ ] 个人了解
- [ ] 客户提案

## 问题 5: 你跟调研对象的关系？
- [ ] 直接竞品
- [ ] 上下游
- [ ] 同赛道不同细分
- [ ] 暂不相关
```

---

# 💡 agent 下一步

1. 调自己的 LLM，按上面的规则和骨架生成**完整问卷**（含"核心问题"等附加问题）
2. 把问卷用 markdown 展示给用户
3. 让用户回答
4. 把用户的答案**打包成 JSON**，再次调用 Radar skill（同一 tool）：

```json
{{
  "question": "{question}",
  "payment_proof": "PAID",
  "answers": {{
    "object_type": "...",
    "time_window": "...",
    "focus_dimensions": ["...", "..."],
    "report_purpose": "...",
    "relationship": "...",
    "core_question": "..."
  }}
}}
```

Radar 会返回"AI PM 调研框架 + 报告模板"，agent 按框架执行调研。

---

📊 已付费 {depth}调研 · ¥{PRICE_QUICK_CENTS/100 if depth == "浅" else PRICE_DEEP_CENTS/100:.2f}
🔗 https://github.com/CookieJobs/AI-radar
"""


def render_framework_response(question: str, answers: dict, depth: str) -> str:
    """返回 AI PM 调研框架 + 报告模板"""
    framework = FRAMEWORK_QUICK if depth == "浅" else FRAMEWORK_DEEP

    # 渲染调研边界（基于 answers）
    boundary = _render_boundary(answers)

    return f"""# Radar 调研框架（{depth}调研 · 已付费）

> 你最初的问题：**{question}**
>
> agent 收到用户的问卷答案后，调自己的 LLM 按下面的框架执行调研。
> 下面是**完整的框架 + 报告模板**——agent 必须严格按这个结构组织最终输出。

---

## 调研边界（基于用户答案）

{boundary}

---

{framework}

---

# ✅ agent 执行步骤总结

1. **Step 1: 信息收集**
   - 用 web search / 用户的数据源
   - 关键词：从 `core_question` 提取
   - 时间窗口：按 `time_window` 严格执行
   - 至少 3 个不同信源

2. **Step 2: 事实摘要**
   - 按 `focus_dimensions` 维度组织
   - 每维度 200 字内
   - 保留来源 URL

3. **Step 3: AI PM 5 维度评估**（**必须覆盖 5 个维度**）
   - 对你的具体影响
   - 行业趋势
   - 行动建议
   - 30 天演化预测
   - 风险点

4. **Step 4: 输出 Markdown 报告**
   - 按上面的"Markdown 报告输出模板"
   - 不要修改章节顺序
   - 不要省略任何维度

---

# 💾 持久化（可选）

Radar **不存**用户调研记录。agent 可以把这次调研结果写到：
- Notion 数据库
- Obsidian vault
- 飞书云文档
- 本地 markdown 文件

调研问题、答案、最终报告 = 用户的私人资产。

---

📊 已付费 {depth}调研 · ¥{PRICE_QUICK_CENTS/100 if depth == "浅" else PRICE_DEEP_CENTS/100:.2f}
🔗 https://github.com/CookieJobs/AI-radar
"""


def _render_boundary(answers: dict) -> str:
    """把用户答案渲染成调研边界"""
    lines = []
    if "object_type" in answers:
        lines.append(f"- **调研对象类型**：{answers['object_type']}")
    if "time_window" in answers:
        lines.append(f"- **时间窗口**：{answers['time_window']}")
    if "focus_dimensions" in answers:
        dims = answers["focus_dimensions"]
        if isinstance(dims, list):
            dims = "、".join(dims)
        lines.append(f"- **重点维度**：{dims}")
    if "report_purpose" in answers:
        lines.append(f"- **报告用途**：{answers['report_purpose']}")
    if "audience" in answers:
        lines.append(f"- **受众**：{answers['audience']}")
    if "relationship" in answers:
        lines.append(f"- **用户与对象关系**：{answers['relationship']}")
    if "core_question" in answers:
        lines.append(f"- **核心问题**：{answers['core_question']}")
    if "company_type" in answers:
        lines.append(f"- **公司类型**：{answers['company_type']}")
    return "\n".join(lines) if lines else "_（用户未提供完整答案，请 agent 提示用户补全）_"


# ===== MCP 协议实现（手写 stdio JSON-RPC，避开 mcp Python 包）=====
def handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": "radar-research",
            "version": "0.1.0"
        }
    }


def handle_list_tools(params: dict) -> dict:
    return {"tools": TOOLS}


def handle_call_tool(params: dict) -> dict:
    name = params.get("name")
    arguments = params.get("arguments", {})

    if name not in ("research_quick", "research_deep"):
        return {"content": [{"type": "text", "text": json.dumps({"error": f"unknown tool: {name}"}, ensure_ascii=False)}], "isError": True}

    question = arguments.get("question", "").strip()
    if not question:
        return {"content": [{"type": "text", "text": json.dumps({"error": "question 不能为空"}, ensure_ascii=False)}], "isError": True}

    payment_proof = arguments.get("payment_proof")
    answers = arguments.get("answers")

    depth_label = "浅" if name == "research_quick" else "深"
    amount = PRICE_QUICK_CENTS if name == "research_quick" else PRICE_DEEP_CENTS

    # Step 1: 没付钱 → 返回 402
    if not payment_proof:
        text = payment_required_response(amount, depth_label)
        return {"content": [{"type": "text", "text": text}]}

    # Step 2: 付了钱但没答问卷 → 返回问卷设计规则
    if not answers or not isinstance(answers, dict) or len(answers) == 0:
        text = render_questionnaire_response(question, depth_label)
        return {"content": [{"type": "text", "text": text}]}

    # Step 3: 付了钱 + 答完问卷 → 返回框架
    text = render_framework_response(question, answers, depth_label)
    return {"content": [{"type": "text", "text": text}]}


HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_list_tools,
    "tools/call": handle_call_tool,
}


def send_message(message: dict):
    """通过 stdio 发送 JSON-RPC 响应"""
    body = json.dumps(message, ensure_ascii=False)
    sys.stdout.write(body + "\n")
    sys.stdout.flush()


def main():
    """主循环：读 stdin 的 JSON-RPC 请求，返回响应"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            send_message({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"parse error: {e}"}, "id": None})
            continue

        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        handler = HANDLERS.get(method)
        if not handler:
            send_message({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"method not found: {method}"}, "id": req_id})
            continue

        try:
            result = handler(params)
            send_message({"jsonrpc": "2.0", "result": result, "id": req_id})
        except Exception as e:
            send_message({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"internal error: {e}"}, "id": req_id})


if __name__ == "__main__":
    main()
