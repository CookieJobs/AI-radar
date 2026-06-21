"""Radar API — B2A AI 行业情报服务"""
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from models import Event, EventList
from seed import EVENTS


# ---------- 限速（IP 60/min + 1000/day） ----------
MINUTE_LIMIT = 60
DAY_LIMIT = 1000

_ip_minute_log: dict[str, deque[float]] = defaultdict(deque)
_ip_day_log: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = Lock()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> Optional[str]:
    """返回 None 表示通过；返回字符串表示被拒原因"""
    now = time.time()
    with _rate_lock:
        mlog = _ip_minute_log[ip]
        dlog = _ip_day_log[ip]

        while mlog and now - mlog[0] > 60:
            mlog.popleft()
        while dlog and now - dlog[0] > 86400:
            dlog.popleft()

        if len(mlog) >= MINUTE_LIMIT:
            return f"minute_limit_exceeded ({MINUTE_LIMIT}/min)"
        if len(dlog) >= DAY_LIMIT:
            return f"day_limit_exceeded ({DAY_LIMIT}/day)"

        mlog.append(now)
        dlog.append(now)
        return None


# ---------- 数据索引 ----------
_EVENTS_BY_ID: dict[str, Event] = {e.id: e for e in EVENTS}


# ---------- lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[radar] loaded {len(EVENTS)} seed events")
    print(f"[radar] rate limits: {MINUTE_LIMIT}/min, {DAY_LIMIT}/day per IP")
    yield


app = FastAPI(
    title="Radar",
    description="B2A AI 行业情报 API —— agent 调一次，拿到事件 + 解读 + 推演",
    version="0.2.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        ip = _client_ip(request)
        reason = _check_rate_limit(ip)
        if reason:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "reason": reason,
                    "hint": "Radar 冷启动期全部免费，但有 IP 限速。等 agent 钱包上线后接入，按调用计费。",
                },
            )
    return await call_next(request)


# ---------- 异常处理 ----------
@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"error": "validation_error", "detail": exc.errors()})


# ---------- 路由 ----------
@app.get("/")
async def root():
    return {
        "service": "Radar",
        "version": "0.2.0",
        "description": "B2A AI 行业情报 API",
        "endpoints": {
            "events": "GET /v1/events — 事件列表",
            "event": "GET /v1/events/{event_id} — 单个事件详情",
            "deep_qa": "POST /v1/ask — 深度问答（stub）",
            "docs": "GET /docs",
        },
        "total_events": len(EVENTS),
        "rate_limit": f"{MINUTE_LIMIT}/min, {DAY_LIMIT}/day per IP",
    }


@app.get("/v1/events", response_model=EventList)
async def list_events(
    domain: Optional[str] = Query(None, description="llm / agent / tooling / infra / application / policy / business"),
    category: Optional[str] = Query(None, description="model_release / funding / acquisition / ..."),
    min_impact: int = Query(1, ge=1, le=5, description="最低 impact_level"),
    since: Optional[str] = Query(None, description="ISO date 或 '7d' / '24h'"),
    limit: int = Query(20, ge=1, le=100),
):
    results = list(EVENTS)

    if domain:
        results = [e for e in results if e.domain == domain]
    if category:
        results = [e for e in results if e.category == category]
    results = [e for e in results if e.impact_level >= min_impact]

    if since:
        now = datetime.now(timezone.utc)
        if since.endswith("d"):
            days = int(since[:-1])
            cutoff = now.timestamp() - days * 86400
            results = [e for e in results if e.timestamp.timestamp() >= cutoff]
        elif since.endswith("h"):
            hours = int(since[:-1])
            cutoff = now.timestamp() - hours * 3600
            results = [e for e in results if e.timestamp.timestamp() >= cutoff]
        else:
            try:
                cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
                results = [e for e in results if e.timestamp >= cutoff]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无法解析 since: {since}")

    results.sort(key=lambda e: e.timestamp, reverse=True)
    results = results[:limit]

    return EventList(
        events=results,
        total=len(results),
        query={
            "domain": domain,
            "category": category,
            "min_impact": min_impact,
            "since": since,
            "limit": limit,
        },
    )


@app.get("/v1/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    if event_id not in _EVENTS_BY_ID:
        raise HTTPException(status_code=404, detail=f"event not found: {event_id}")
    return _EVENTS_BY_ID[event_id]


@app.post("/v1/ask")
async def deep_qa_stub(payload: dict):
    """深度问答 API（v0.2 stub）。后续接入 RAG。"""
    return {
        "answer": "深度问答功能开发中。当前请使用 /v1/events 获取结构化事件。",
        "hint": "v0.3 会接入向量检索。",
        "received": payload,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
