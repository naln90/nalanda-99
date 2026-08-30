"""训练 / 风险记录查询路由。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SuspiciousCheck, TrainingRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["records"])


@router.get("/records")
def records(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
    training_records = db.scalars(
        select(TrainingRecord).where(TrainingRecord.owner_id == ownerId).order_by(TrainingRecord.created_at.desc())
    ).all()
    checks = db.scalars(
        select(SuspiciousCheck).where(SuspiciousCheck.owner_id == ownerId).order_by(SuspiciousCheck.created_at.desc())
    ).all()
    return {
        "trainingRecords": [
            {
                "taskId": record.task_id,
                "score": record.score,
                "accuracy": record.accuracy,
                "finalGrowth": record.final_growth,
                "rewardStatus": record.reward_status,
                "rewardMessage": record.reward_message,
                "createdAt": record.created_at.isoformat(),
            }
            for record in training_records
        ],
        "suspiciousChecks": [
            {
                "riskLevel": check.risk_level,
                "riskScore": check.risk_score,
                "growthAwarded": check.growth_awarded,
                "rewardStatus": check.reward_status,
                "createdAt": check.created_at.isoformat(),
            }
            for check in checks
        ],
    }
