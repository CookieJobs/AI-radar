"""RSS 抓取脚本 v0.1

目标：从 40 个信源抓最近 N 小时的新条目 → 关键词粗筛 → 输出候选 JSON。

v0.1 范围：
- 只抓有 RSS feed 的信源（sources.py 里 url 非 None 的）
- 不爬 HTML 页面（v0.3 接 RSSHub 时再扩）
- 不做 LLM 解读（**人写** —— Radar 核心红线）
- 候选去重：同 URL + 同标题只保留第一条
- 关键词粗筛：命中 AI/LLM/agent/model/funding 关键词才进候选

输出：
- backend/candidates/candidates_YYYYMMDD_HHMMSS.json
- 结构：[{source, url, title, summary, published, suggested_domain, suggested_category}]

用法：
    # 跑最近 24h 的所有信源
    venv/bin/python -m ingest.fetcher

    # 跑最近 72h、只跑核心信源
    venv/bin/python -m ingest.fetcher --since-hours 72 --tier core

    # 离线模式（不连网络，用 fixture 演示流程）
    venv/bin/python -m ingest.fetcher --offline
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# 让脚本既能 `python -m ingest.fetcher` 也能 `python ingest/fetcher.py` 跑
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from ingest.sources import ALL_SOURCES, active_sources, Source  # noqa: E402

# v0.1 不引入 feedparser 硬依赖（如果缺，给清晰错误）
try:
    import feedparser  # type: ignore
    _HAS_FEEDPARSER = True
except ImportError:
    _HAS_FEEDPARSER = False


# ---------- 关键词路由 ----------
# 命中关键词 → 建议 domain/category。不命中 → 跳过（避免噪声）。
# 这个表是 v0.1 粗糙版，v0.2 用 LLM 分类（v0.3 路线）。
_KEYWORDS = {
    "model_release": ["release", "launch", "announce", "debut", "introduce", "发布", "上线", "推出", "开源", "open source"],
    "model_capability": ["benchmark", "sota", "state-of-the-art", "reasoning", "突破", "刷榜"],
    "funding": ["funding", "raised", "valuation", "series a", "series b", "series c", "融资", "估值"],
    "acquisition": ["acquire", "acquisition", "merger", "并购", "收购"],
    "product_launch": ["product", "feature", "update", "ship", "rollout", "上线", "功能", "更新", "GA"],
    "api_pricing": ["api", "pricing", "price", "cost", "token price", "降价", "提价", "价格"],
    "research": ["paper", "arxiv", "study", "research", "论文", "研究"],
    "policy": ["regulation", "policy", "law", "ban", "compliance", "监管", "政策", "合规"],
    "agent_framework": ["agent", "mcp", "tool use", "function calling", "workflow", "智能体", "工作流"],
    "open_source": ["open source", "github", "repo", "开源", "仓库"],
    "partnership": ["partnership", "deal", "collaboration", "合作", "战略合作"],
}

_DOMAIN_HINTS = {
    "llm": ["llm", "gpt", "claude", "gemini", "llama", "deepseek", "qwen", "kimi", "大模型", "语言模型"],
    "agent": ["agent", "mcp", "tool use", "智能体", "工作流", "workflow"],
    "infra": ["gpu", "chip", "inference", "training", "datacenter", "cloud", "算力", "推理", "训练"],
    "tooling": ["ide", "editor", "copilot", "cursor", "windsurf", "cline", "工具"],
    "application": ["app", "product", "saas", "platform", "应用", "产品"],
    "policy": ["regulation", "policy", "law", "ban", "监管", "政策"],
    "business": ["funding", "raised", "valuation", "acquisition", "融资", "估值", "收购"],
}


def _classify(text: str, source: Source) -> tuple[str, str]:
    """根据文本 + 信源默认路由，返回 (domain, category)"""
    text_lower = text.lower()

    # 1) domain：先看 domain 关键词
    best_domain = source.default_domain
    best_domain_score = 0
    for d, kws in _DOMAIN_HINTS.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > best_domain_score:
            best_domain = d
            best_domain_score = score

    # 2) category：按出现次数最多决定
    best_cat = source.default_category
    best_cat_score = 0
    for c, kws in _KEYWORDS.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > best_cat_score:
            best_cat = c
            best_cat_score = score

    return best_domain, best_cat


# ---------- 抓取 ----------
def _entry_id(url: str, title: str) -> str:
    """稳定的 candidate id（不直接当 event id —— event id 要人写）"""
    h = hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()[:10]
    return f"cand_{h}"


def fetch_source(source: Source, since: datetime, timeout: int = 10) -> list[dict]:
    """抓单个信源，返回候选列表（已粗筛）"""
    if not source.url:
        return []
    try:
        feed = feedparser.parse(source.url, agent="Radar/0.1 (+https://github.com/CookieJobs/AI-radar)")
    except Exception as e:
        print(f"  [warn] {source.name}: 抓取失败 {e}", file=sys.stderr)
        return []

    if not feed.entries:
        return []

    out = []
    for e in feed.entries:
        # 1) 时间窗口
        published = _parse_published(e)
        if published is None or published < since:
            continue

        # 2) 标题/正文取
        title = (e.get("title") or "").strip()
        summary = (e.get("summary") or e.get("description") or "").strip()
        url = (e.get("link") or "").strip()
        if not title or not url:
            continue

        # 3) 关键词粗筛：title + summary 里出现 AI 相关词才要
        blob = f"{title} {summary}".lower()
        if not _is_ai_relevant(blob):
            continue

        # 4) 分类
        domain, category = _classify(blob, source)

        out.append({
            "candidate_id": _entry_id(url, title),
            "source_name": source.name,
            "source_url": source.url,
            "source_tier": source.tier,
            "source_lang": source.lang,
            "url": url,
            "title": title,
            "summary": _truncate(summary, 500),
            "published": published.isoformat(),
            "suggested_domain": domain,
            "suggested_category": category,
        })
    return out


def _parse_published(entry) -> Optional[datetime]:
    """feedparser 的 published_parsed 是 UTC struct_time"""
    pp = entry.get("published_parsed") or entry.get("updated_parsed")
    if pp is None:
        return None
    try:
        return datetime(*pp[:6], tzinfo=timezone.utc)
    except Exception:
        return None


def _is_ai_relevant(blob: str) -> bool:
    """v0.1 粗筛：白名单关键词命中才要"""
    whitelist = [
        "ai", "llm", "gpt", "claude", "gemini", "llama", "deepseek", "qwen", "kimi", "agent", "mcp",
        "model", "anthropic", "openai", "google", "meta", "mistral", "xai", "cursor", "copilot",
        "transformer", "diffusion", "rag", "embedding", "vector", "agentic", "tool use",
        "大模型", "智能体", "推理", "训练",
    ]
    return any(kw in blob for kw in whitelist)


def _truncate(s: str, n: int) -> str:
    s = re.sub(r"<[^>]+>", "", s)  # 去 HTML 标签
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n] + "…"


# ---------- 离线 fixture ----------
_OFFLINE_FIXTURE = [
    {
        "title": "Anthropic 发布 Claude 4.6，编程 benchmark 突破 80%",
        "url": "https://www.anthropic.com/news/claude-4-6",
        "summary": "Anthropic 6 月 22 日发布 Claude 4.6，SWE-bench 得分突破 80%，比 4.5 提升 2.5 个百分点。200K context，价格不变。重点强化 agent 长任务链能力。",
        "published": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
    },
    {
        "title": "OpenAI 完成新一轮融资，估值 3500 亿美元",
        "url": "https://www.theinformation.com/articles/openai-raises-funding",
        "summary": "OpenAI 完成 100 亿美元融资，估值升至 3500 亿美元。本轮由 Thrive Capital 领投，软银、微软跟投。资金用于推理算力扩张。",
        "published": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
    },
    {
        "title": "DeepSeek V4 发布，国产模型编程能力首次超越 Claude 4.5",
        "url": "https://api-docs.deepseek.com/news/v4",
        "summary": "DeepSeek V4 6 月 20 日发布，编程 benchmark 与 Claude 4.5 持平，价格只有 1/10。开源（MIT 协议），支持 128K context。",
        "published": (datetime.now(timezone.utc) - timedelta(hours=14)).isoformat(),
    },
    {
        "title": "今天天气不错",
        "url": "https://example.com/weather",
        "summary": "今天北京天气晴朗，气温 25 度。",
        "published": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
    },
]


def _offline_candidates(source: Source, since: datetime) -> list[dict]:
    """用 fixture 模拟抓取（用于演示流程 / CI / 网络不通时）"""
    out = []
    for f in _OFFLINE_FIXTURE:
        if f["title"] == "今天天气不错":  # 测试关键词粗筛会过滤
            continue
        published = datetime.fromisoformat(f["published"])
        if published < since:
            continue
        blob = f"{f['title']} {f['summary']}".lower()
        domain, category = _classify(blob, source)
        out.append({
            "candidate_id": _entry_id(f["url"], f["title"]),
            "source_name": source.name,
            "source_url": source.url or "https://example.com",
            "source_tier": source.tier,
            "source_lang": source.lang,
            "url": f["url"],
            "title": f["title"],
            "summary": f["summary"],
            "published": f["published"],
            "suggested_domain": domain,
            "suggested_category": category,
        })
    return out


# ---------- 主流程 ----------
def main():
    ap = argparse.ArgumentParser(description="Radar RSS 抓取 v0.1")
    ap.add_argument("--since-hours", type=int, default=24, help="抓最近 N 小时（默认 24）")
    ap.add_argument("--tier", choices=["core", "recommended", "bonus", "all"], default="all")
    ap.add_argument("--lang", choices=["en", "zh", "all"], default="all")
    ap.add_argument("--max-per-source", type=int, default=5, help="单信源最多保留多少条")
    ap.add_argument("--offline", action="store_true", help="离线模式（用 fixture 演示流程）")
    ap.add_argument("--out-dir", default=str(_BACKEND / "candidates"))
    args = ap.parse_args()

    if not args.offline and not _HAS_FEEDPARSER:
        print("[error] 需要 feedparser：pip install feedparser", file=sys.stderr)
        print("        或加 --offline 跑 fixture 演示", file=sys.stderr)
        sys.exit(1)

    # 1) 过滤信源
    sources = active_sources() if not args.offline else ALL_SOURCES
    if args.tier != "all":
        sources = [s for s in sources if s.tier == args.tier]
    if args.lang != "all":
        sources = [s for s in sources if s.lang == args.lang]
    print(f"[ingest] 目标信源 {len(sources)} 个，since={args.since_hours}h, tier={args.tier}, lang={args.lang}, offline={args.offline}")

    since = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)

    # 2) 抓
    all_candidates: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for s in sources:
        try:
            if args.offline:
                cands = _offline_candidates(s, since)
            else:
                cands = fetch_source(s, since)
        except Exception as e:
            print(f"  [warn] {s.name}: {e}", file=sys.stderr)
            continue

        # 跨信源去重（同 url + 同 title）
        new = []
        for c in cands:
            key = (c["url"], c["title"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            new.append(c)
        new = new[: args.max_per_source]
        if new:
            print(f"  ✓ {s.name}: {len(new)} 条候选")
        all_candidates.extend(new)

    # 3) 排序：按发布时间倒序
    all_candidates.sort(key=lambda c: c["published"], reverse=True)

    # 4) 输出
    os.makedirs(args.out_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out_dir) / f"candidates_{ts}.json"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "since_hours": args.since_hours,
        "sources_attempted": len(sources),
        "candidates_count": len(all_candidates),
        "candidates": all_candidates,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\n[ingest] 候选 {len(all_candidates)} 条 → {out_path}")
    print(f"[ingest] 下一步：人工 review → 改写 fact/insight/forecast → 入库")


if __name__ == "__main__":
    main()
