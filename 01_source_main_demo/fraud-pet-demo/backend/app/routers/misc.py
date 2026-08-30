from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
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


router = APIRouter(prefix="/api", tags=["misc"])

@router.get("/health")

def health() -> dict[str, str]:
        return {"status": "ok"}


@router.get("/ranking")

def ranking(type: str = Query("total"), ownerId: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
        pets = db.scalars(
            select(Pet).order_by(Pet.growth_value.desc(), Pet.level.desc(), Pet.last_training_at.desc())
        ).all()
        rows = [
            {
                "rank": idx + 1,
                "petId": pet.pet_id,
                "ownerId": pet.owner_id,
                "petType": pet.pet_type,
                "level": pet.level,
                "growthValue": pet.growth_value,
                "lastTrainingAt": pet.last_training_at.strftime("%Y-%m-%d %H:%M") if pet.last_training_at else "",
            }
            for idx, pet in enumerate(pets)
        ]
        target_owner = ownerId or "U-2408**"
        my_rank = next((row for row in rows if row["ownerId"] == target_owner), None)
        if my_rank:
            previous = next((row for row in rows if row["rank"] == my_rank["rank"] - 1), None)
            my_rank = {
                **my_rank,
                "distanceToPrevious": max(0, int(previous["growthValue"]) - int(my_rank["growthValue"])) if previous else 0,
            }
        return {
            "type": type,
            "myRank": my_rank,
            "list": rows,
            "sortRule": ["growth_value DESC", "level DESC", "last_training_at DESC"],
            "privacyNotice": "不展示真实姓名、手机号、学号、身份证号和负面评价标签。",
        }


@router.get("/records")

def records(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
        training_records = db.scalars(select(TrainingRecord).where(TrainingRecord.owner_id == ownerId).order_by(TrainingRecord.created_at.desc())).all()
        checks = db.scalars(select(SuspiciousCheck).where(SuspiciousCheck.owner_id == ownerId).order_by(SuspiciousCheck.created_at.desc())).all()
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


