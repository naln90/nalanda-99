from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import threading
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import create_engine, desc, func, inspect, select, text
from sqlalchemy.orm import Session

from ..database import get_db, get_submit_lock
from ..models import *
from ..schemas import *
from ..rules import *
from ..helpers import *
from ..seed import pet_to_response, seed_database
from ..ai_service import AIService, is_llm_available, MODEL_NAME
from ..assessment_service import *
from ..image_analysis import analyze_image
from ..question_bank import ALL_QUESTIONS
from ..risk_test_samples import seed_risk_test_samples
from ..scenarios import scenario_response
from ..ability_profile import *
from ..retrain_scheduler import *
from ..task_planner import *
from ..scenario_state_machine import *
from ..review_engine import *
from ..emergency_stop_loss import *
from ..ai_logger import *


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
            for rt in pending if rt.scheduled_at <= now
        ]
        return {"retrains": due, "total": len(due)}


