"""AI 调用日志 — 记录所有 AI 调用的输入、输出、Token、耗时和安全状态。

用于赛事证据中心展示。
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from .models import AICallLog

logger = logging.getLogger(__name__)


def log_ai_call(
    db: Session,
    *,
    call_type: str,
    model_name: str,
    prompt_version: str,
    input_summary: str,
    output_struct: dict[str, Any],
    knowledge_refs: list[str] | None = None,
    token_usage: int = 0,
    response_time_ms: int = 0,
    safety_blocked: bool = False,
    fallback_used: bool = False,
    error_message: str | None = None,
) -> AICallLog:
    """记录一次 AI 调用日志。

    Args:
        call_type: "dialogue" | "risk_analysis" | "task_planning" | "review"
        model_name: 模型名称和版本
        prompt_version: Prompt 版本号
        input_summary: 脱敏后的输入摘要（≤200字符）
        output_struct: 结构化输出（自动序列化为 JSON）
        knowledge_refs: 知识检索依据列表
        token_usage: Token 用量
        response_time_ms: 响应时间（毫秒）
        safety_blocked: 是否被安全拦截
        fallback_used: 是否降级
        error_message: 错误信息（如果有）

    Returns:
        AICallLog 实例
    """
    log = AICallLog(
        call_type=call_type,
        model_name=model_name,
        prompt_version=prompt_version,
        input_summary=input_summary[:200],
        output_struct=json.dumps(output_struct, ensure_ascii=False),
        knowledge_refs=json.dumps(knowledge_refs or [], ensure_ascii=False),
        token_usage=token_usage,
        response_time_ms=response_time_ms,
        safety_blocked=safety_blocked,
        fallback_used=fallback_used,
        error_message=error_message,
        created_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


class AICallTimer:
    """计时上下文管理器"""

    def __init__(self):
        self.start_time = 0.0
        self._end_time: float | None = None

    def __enter__(self):
        self.start_time = time.time()
        self._end_time = None
        return self

    def __exit__(self, *args):
        self._end_time = time.time()

    @property
    def elapsed_ms(self) -> int:
        end = self._end_time if self._end_time is not None else time.time()
        return int((end - self.start_time) * 1000)


def get_overview_stats(db: Session) -> dict[str, Any]:
    """获取 AI 调用概览统计。"""
    from sqlalchemy import func

    total = db.query(func.count(AICallLog.id)).scalar() or 0
    blocked = db.query(func.count(AICallLog.id)).filter(AICallLog.safety_blocked == True).scalar() or 0
    fallback = db.query(func.count(AICallLog.id)).filter(AICallLog.fallback_used == True).scalar() or 0
    avg_time = db.query(func.avg(AICallLog.response_time_ms)).scalar() or 0
    total_tokens = db.query(func.sum(AICallLog.token_usage)).scalar() or 0

    # 按类型统计
    by_type = {}
    rows = (
        db.query(
            AICallLog.call_type,
            func.count(AICallLog.id),
            func.avg(AICallLog.response_time_ms),
        )
        .group_by(AICallLog.call_type)
        .all()
    )
    for ct, cnt, avg_t in rows:
        by_type[ct] = {
            "count": cnt,
            "avgResponseTime": round(float(avg_t or 0), 1),
        }

    return {
        "totalCalls": total,
        "safetyBlocked": blocked,
        "fallbackUsed": fallback,
        "avgResponseTime": round(float(avg_time), 1),
        "totalTokens": total_tokens,
        "byType": by_type,
    }


def get_log_count(db: Session, call_type: str | None = None) -> int:
    """获取 AI 调用记录总数（用于分页）。"""
    from sqlalchemy import func

    query = db.query(func.count(AICallLog.id))
    if call_type:
        query = query.filter(AICallLog.call_type == call_type)
    return query.scalar() or 0


def get_recent_logs(db: Session, limit: int = 20, offset: int = 0, call_type: str | None = None) -> list[dict]:
    """获取 AI 调用记录列表。"""
    query = db.query(AICallLog)
    if call_type:
        query = query.filter(AICallLog.call_type == call_type)
    query = query.order_by(AICallLog.created_at.desc())
    logs = query.offset(offset).limit(limit).all()

    return [
        {
            "id": log.id,
            "callType": log.call_type,
            "modelName": log.model_name,
            "promptVersion": log.prompt_version,
            "inputSummary": log.input_summary,
            "outputStruct": json.loads(log.output_struct) if log.output_struct else {},
            "knowledgeRefs": json.loads(log.knowledge_refs) if log.knowledge_refs else [],
            "tokenUsage": log.token_usage,
            "responseTimeMs": log.response_time_ms,
            "safetyBlocked": log.safety_blocked,
            "fallbackUsed": log.fallback_used,
            "errorMessage": log.error_message,
            "createdAt": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
