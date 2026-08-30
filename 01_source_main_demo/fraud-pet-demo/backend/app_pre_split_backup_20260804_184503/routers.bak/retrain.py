"""复训任务路由：获取到期复训。"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RetrainTask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/retrain", tags=["retrain"])


@router.get("/due")
def get_due_retrains(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
    """获取到期的复训任务"""
    pending = db.scalars(
        select(RetrainTask)
        .where(RetrainTask.owner_id == ownerId, RetrainTask.status == "pending")
        .order_by(RetrainTask.scheduled_at)
    ).all()
    now = datetime.utcnow()
    due = [
        {
            "id": rt.id,
            "originalQuestionId": rt.original_question_id,
            "originalTaskId": rt.original_task_id,
            "fraudType": rt.fraud_type,
            "targetAbility": rt.target_ability,
            "attempt": rt.attempt,
            "scheduledAt": rt.scheduled_at.isoformat(),
            "variantStrategy": rt.variant_strategy,
        }
        for rt in pending
        if rt.scheduled_at <= now
    ]
    return {"retrains": due, "total": len(due)}
