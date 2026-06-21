"""Radar event data model."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


Category = Literal[
    "model_release",      # 新模型/新版本
    "model_capability",   # 能力突破 (reasoning/vision/audio/etc)
    "funding",            # 融资
    "acquisition",        # 并购
    "product_launch",     # 产品上线
    "api_pricing",        # API 价格变动
    "research",           # 论文 / 研究突破
    "policy",             # 监管 / 政策
    "open_source",        # 开源
    "agent_framework",    # agent / MCP / 框架
    "benchmark",          # 评测 / SOTA
    "partnership",        # 战略合作
]

Domain = Literal[
    "llm",          # 基础大模型
    "agent",        # agent / workflow
    "tooling",      # 开发工具
    "infra",        # 算力 / 云
    "application",  # 应用层
    "policy",       # 政策
    "business",     # 商业 / 融资
]


class Source(BaseModel):
    name: str
    url: str


class Event(BaseModel):
    id: str = Field(..., description="evt_<date>_<entity>_<slug>")
    timestamp: datetime
    domain: Domain
    category: Category
    entities: list[str]
    headline: str = Field(..., max_length=200)
    summary_fact: str = Field(..., description="事实摘要 (推荐 100-300 字)")
    summary_insight: str = Field(..., description="专家解读 (推荐 100-300 字)")
    summary_forecast: str = Field(..., description="30 天推演 (推荐 60-150 字)")
    impact_level: int = Field(..., ge=1, le=5, description="1=轻微 5=改变格局")
    confidence: float = Field(..., ge=0, le=1)
    source: list[Source]
    tags: list[str]


class EventList(BaseModel):
    events: list[Event]
    total: int
    query: dict
