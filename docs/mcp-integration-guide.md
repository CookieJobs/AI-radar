# Radar MCP 集成教程（v0.2）

> 5 分钟让 Claude Desktop / Cursor / 其他 MCP 兼容 agent 调上 Radar 的 AI 行业情报。
> 适用版本：Radar v0.2（49 条种子事件 + REST + MCP 双通道）

---

## 一句话流程

**Radar 是个 MCP server**。任何支持 MCP 的 agent host（Claude Desktop、Cursor、Cline、Windsurf、Continue.dev 等）配 1 段 JSON，你的 agent 就**自动**获得"调用 Radar 拿 AI 行业情报"的能力。

agent 拿到这些工具后，会在对话里**自己判断**什么时候该调（比如你问"最近 AI 行业有什么大事"），你不用手动触发。

---

## 工具清单

Radar 暴露 3 个工具给 agent：

| 工具 | 用途 | 典型问题 |
|---|---|---|
| `list_events` | 查询事件流（domain/category/min_impact/since 过滤） | "最近 30 天 LLM 行业最重要的事件" |
| `get_event` | 按 ID 拿单个事件完整详情 | "DeepSeek R2 那条新闻完整解读" |
| `get_top_impact` | 拿最近 N 天 impact=5 的顶级事件 | "过去一周必须知道的 AI 大事" |

每个事件都包含 **summary_fact**（事实）+ **summary_insight**（专家解读）+ **summary_forecast**（30 天推演）三段——这是 Radar 的核心价值，agent 拿到的是"判断 + 推演"，不是"标题党"。

---

## 集成步骤

### 步骤 0：环境准备（**Python 3.10+**）

⚠️ **重要**：MCP Python SDK（`mcp>=1.0.0`）要求 Python 3.10+。macOS 自带的是 3.9，需要先装：

```bash
# 方式 A：Homebrew（推荐）
brew install python@3.11
which python3.11   # 应该是 /opt/homebrew/bin/python3.11

# 方式 B：pyenv
brew install pyenv
pyenv install 3.11.9
pyenv global 3.11.9
```

### 步骤 1：重建 venv（用 3.10+ Python）

⚠️ **如果你之前的 venv 是用 3.9 建的，必须重做**——里面装的 `mcp` 包是空的。

```bash
cd ~/Desktop/HermesWS/AI-radar/backend

# 把 venv 用 3.11 重建
rm -rf venv
python3.11 -m venv venv

# 装依赖
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# 验证 mcp 包就位
venv/bin/pip show mcp   # 应该看到 Version: 1.x
```

### 步骤 2：验证 MCP 协议层（可选但推荐）

```bash
cd ~/Desktop/HermesWS/AI-radar/backend
venv/bin/python examples/test_mcp.py
```

应该看到：

```
[host] MCP handshake 完成
[host] 工具列表 (3 个):
  - list_events: ...
  - get_event: ...
  - get_top_impact: ...
[host] MCP 协议层验证通过 ✓
```

如果报错，看文末"常见排错"。

### 步骤 3：MCP 走 stdio，**不需要起 REST**

> **关键澄清**：MCP 是 stdio 协议（stdin/stdout JSON-RPC），不走 HTTP。agent host 启动一个子进程来跑 `mcp_server.py`，所以 `main.py` **不需要**起来。

如果想顺带跑 REST 给你 curl 调试，可以另开一个 terminal：

```bash
cd ~/Desktop/HermesWS/AI-radar/backend
venv/bin/python main.py   # 跑在 http://127.0.0.1:8765
```

### 步骤 4：在 agent host 里配 MCP server

#### A) Claude Desktop

打开配置文件：

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

写入（或合并到 `mcpServers` 字段）：

```json
{
  "mcpServers": {
    "radar": {
      "command": "/Users/liujin/Desktop/HermesWS/AI-radar/backend/venv/bin/python",
      "args": ["/Users/liujin/Desktop/HermesWS/AI-radar/backend/mcp_server.py"]
    }
  }
}
```

**重启 Claude Desktop**。配成功后，工具列表里会看到 Radar 的 3 个工具（带小扳手图标）。

#### B) Cursor

`Settings` → `MCP` → `Add new MCP server`：

| 字段 | 值 |
|---|---|
| Name | `radar` |
| Type | `stdio` |
| Command | `/Users/liujin/Desktop/HermesWS/AI-radar/backend/venv/bin/python` |
| Args | `["/Users/liujin/Desktop/HermesWS/AI-radar/backend/mcp_server.py"]` |

保存后 Cursor 的 Composer/Agent 模式会自动获得 Radar 工具。

#### C) Cline（VS Code 插件）

VS Code `Settings` → 搜 `cline.mcpServers`：

```json
{
  "cline.mcpServers": {
    "radar": {
      "command": "/Users/liujin/Desktop/HermesWS/AI-radar/backend/venv/bin/python",
      "args": ["/Users/liujin/Desktop/HermesWS/AI-radar/backend/mcp_server.py"]
    }
  }
}
```

#### D) Windsurf

`Settings` → `MCP Servers` → 选 "Add new"：

```
Name: radar
Command: /Users/liujin/Desktop/HermesWS/AI-radar/backend/venv/bin/python
Args: /Users/liujin/Desktop/HermesWS/AI-radar/backend/mcp_server.py
```

#### E) 其他 MCP host

所有兼容 MCP 的 host 都用同一份配置 schema——把上面的 `command` + `args` 复制到它们的 MCP 配置位置即可。

### 步骤 5：测试

打开 Claude Desktop（或任何已配好的 host），问：

> "最近一周 AI 行业最重要的 3 件事是什么？"

agent 会**自动**调用 `get_top_impact`，然后给你返回 3 条带 fact / insight / forecast 的事件。

或者更直接：

> "用 Radar 查一下 DeepSeek 最新动态"

agent 会调 `list_events`，自动选 `domain=llm` + 关键词过滤。

---

## 高级用法

### 自定义 agent 的 prompt

你可以在 agent host 的 system prompt 里**显式引导**它用 Radar。比如在 Claude Desktop 的项目自定义指令里写：

```
当用户问 AI / 大模型 / agent 相关的行业动态、新闻、趋势时，
优先调用 Radar MCP 的工具来获取信息。Radar 的事件已经包含
事实 / 解读 / 推演三段，直接用其 insight 部分回答用户，
forecast 部分作为'未来 30 天会发生什么'的预测。
```

这样 agent 不会瞎猜，会优先走 Radar。

### 与其他 MCP 配合

Radar 是**只读**的情报源，可以跟其他 MCP 配合形成工作流：

- **Radar（情报）+ 飞书 MCP（写文档）**：agent 拿到 Radar 事件后自动写周报到飞书
- **Radar + 邮件 MCP**：每日自动发日报邮件
- **Radar + 浏览器 MCP**：拿到事件后自动深挖某条新闻的原文
- **Radar + 飞书 calendar MCP**：把高 impact 事件自动加到日程

具体看你 host 支持哪些 MCP。

### 限速说明

- **MCP 走 stdio**：MCP server 本身无限速（stdio 不走网络）。
- **REST API 走 HTTP**：限速在 `main.py`，按 IP 60/min + 1000/day。
- **当前状态**：冷启动期完全免费。
- **T+90d 后**：接微信/支付宝 agent 钱包，按调用 ¥0.1-0.5/次。

---

## 常见排错

### 1. `ModuleNotFoundError: No module named 'mcp'`

**原因**：venv 是用 Python 3.9 建的，mcp 包要 3.10+。

**解决**：
```bash
cd ~/Desktop/HermesWS/AI-radar/backend
rm -rf venv
python3.11 -m venv venv    # 或 3.12/3.13
venv/bin/pip install -r requirements.txt
venv/bin/pip show mcp      # 确认装上了
```

### 2. Claude Desktop 工具列表里看不到 Radar

排查顺序：

1. **路径写错**：用**绝对路径**，不要相对路径
2. **JSON 格式错**：用 [jsonlint.com](https://jsonlint.com) 验证你的 `claude_desktop_config.json`
3. **没重启**：Claude Desktop 必须重启才生效
4. **看 log**：
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - 看 stderr 里的报错信息
5. **手动跑一遍试试**：
   ```bash
   /Users/liujin/Desktop/HermesWS/AI-radar/backend/venv/bin/python \
     /Users/liujin/Desktop/HermesWS/AI-radar/backend/mcp_server.py
   ```
   正常会**什么都不输出**（MCP 等 stdin 指令），有报错会立刻看到。

### 3. Cursor 里 MCP 一直转圈

- 同样检查绝对路径
- Cursor 的 MCP log 在 `Settings` → `MCP` 页面下方
- 确认 `type` 字段是 `stdio`（Cursor 0.40+ 强制要求）

### 4. `feedparser` 缺失（如果跑 RSS 抓取脚本）

```bash
venv/bin/pip install feedparser
```

### 5. agent 调用了但返回空

- 检查 49 条种子事件是否还在：`curl http://127.0.0.1:8765/`
- 如果 `main.py` 重启过，新数据没动（当前 in-memory）；MCP server 进程是独立子进程，要重启 Claude Desktop / Cursor 才生效

---

## 验证清单

集成完成后，按这个清单自查：

- [ ] `python3.11 -m venv venv` 重建了 venv
- [ ] `venv/bin/pip show mcp` 能看到版本号
- [ ] `venv/bin/python examples/test_mcp.py` 跑通握手
- [ ] agent host 配置里 command + args 都是**绝对路径**
- [ ] agent host 重启过
- [ ] 对话里能看到 "Radar" 工具（扳手图标）
- [ ] 问"最近一周 AI 行业大事"能拿到 3 条事件

---

## 后续路线

- **v0.3**（T+30d）：加入 `ask_radar` 深度问答工具（SQLite + RAG）
- **T+60d**：注册到 [MCP 官方 registry](https://github.com/modelcontextprotocol/servers)，让 agent host 一键添加
- **T+90d**：接入微信/支付宝 agent 钱包，按调用计费
- **T+180d**：API 上架 WorkBuddy Skill / MCP 广场

集成问题或 bug，请记录到 `docs/issues.md`（v0.3 路线建）。
