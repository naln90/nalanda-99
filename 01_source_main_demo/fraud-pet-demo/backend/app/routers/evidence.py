from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..schemas import *
from ..rules import *
from ..helpers import *
# NOTE: `from ..helpers import *` skips underscore-prefixed names (Python
# semantics). Several module-level helpers used by routers start with `_`
# (e.g. _award_lock, _NUMERIC_RULE_KEYS, _KEY_MAP, _ADMIN_KEY_WARNED), so we
# import them explicitly to preserve the original single-module behaviour.
from ..assessment_service import *
from ..ability_profile import *
from ..retrain_scheduler import *
from ..task_planner import *
from ..scenario_state_machine import *
from ..review_engine import *
from ..emergency_stop_loss import *
from ..ai_logger import *


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/evidence", tags=["evidence"])

@router.get("/overview")

def evidence_overview(db: Session = Depends(get_db)) -> dict[str, object]:
        """赛事证据中心 — AI 调用概览统计"""
        from ..ai_logger import get_overview_stats
        stats = get_overview_stats(db)
        return {
            **stats,
            "promptVersions": {
                "dialogue": "v1.0",
                "risk_analysis": "v1.0",
                "task_planning": "v1.0",
                "review": "v1.0",
            },
            "modelInfo": {
                "name": os.getenv("LLM_MODEL", "rule-engine"),
                "baseUrl": os.getenv("LLM_BASE_URL", ""),
                "available": bool(os.getenv("LLM_API_KEY") and os.getenv("LLM_BASE_URL")),
            },
        }


@router.get("/ai-logs")

def evidence_ai_logs(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        call_type: str | None = None,
        db: Session = Depends(get_db),
    ) -> dict[str, object]:
        """赛事证据中心 — AI 调用记录列表"""
        from ..ai_logger import get_recent_logs, get_log_count
        logs = get_recent_logs(db, limit=limit, offset=offset, call_type=call_type)
        total = get_log_count(db, call_type=call_type)
        return {"logs": logs, "total": total}


@router.get("/prompt-versions")

def evidence_prompt_versions() -> dict[str, object]:
        """赛事证据中心 — Prompt 版本清单"""
        return {
            "versions": [
                {"type": "dialogue", "version": "v1.0", "description": "情景对话 Prompt — 约束 AI 按状态机生成骗子回复"},
                {"type": "risk_analysis", "version": "v1.0", "description": "风险分析 Prompt — LLM 语义理解风险信号"},
                {"type": "task_planning", "version": "v1.0", "description": "任务规划 Prompt — 生成个性化训练激励文案"},
                {"type": "review", "version": "v1.0", "description": "复盘 Prompt — 生成训练复盘总结"},
            ]
        }


