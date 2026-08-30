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


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary")

def dashboard_summary(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
        """首页聚合接口：当前能力、薄弱类型、任务进度、最近变化"""
        user = get_or_create_user(db, ownerId)
        pet = get_pet(db, ownerId)

        # 最近一次测评画像
        latest_assessment = db.scalar(
            select(AssessmentResult)
            .where(AssessmentResult.owner_id == ownerId)
            .order_by(AssessmentResult.created_at.desc())
        )
        profile = json.loads(latest_assessment.ability_profile_json) if latest_assessment else None
        weak_dims = json.loads(latest_assessment.weak_dimensions_json) if latest_assessment else []
        overall_score = round(sum(profile.values()) / len(profile)) if profile else 0

        # 当前任务包
        current_package = db.scalar(
            select(TaskPackage)
            .where(TaskPackage.owner_id == ownerId, TaskPackage.status == "active")
            .order_by(TaskPackage.created_at.desc())
        )
        package_progress = None
        if current_package:
            total_items = db.scalar(
                select(func.count(TaskPackageItem.id))
                .where(TaskPackageItem.package_id == current_package.id)
            ) or 0
            completed_items = db.scalar(
                select(func.count(TaskPackageItem.id))
                .where(TaskPackageItem.package_id == current_package.id, TaskPackageItem.status == "completed")
            ) or 0
            package_progress = {
                "id": current_package.id,
                "planType": current_package.plan_type,
                "totalItems": total_items,
                "completedItems": completed_items,
                "progressPercent": round(completed_items / max(total_items, 1) * 100),
            }

        # 最近能力变化（与上上次测评对比）
        previous_assessment = db.scalar(
            select(AssessmentResult)
            .where(AssessmentResult.owner_id == ownerId)
            .order_by(AssessmentResult.created_at.desc())
            .offset(1)
            .limit(1)
        )
        ability_change = None
        if latest_assessment and previous_assessment:
            from ..ability_profile import ability_delta
            before = {"scores": json.loads(previous_assessment.ability_profile_json)}
            after = {"scores": json.loads(latest_assessment.ability_profile_json)}
            ability_change = ability_delta(before, after)

        # 到期的复训任务
        from ..retrain_scheduler import get_due_retrains, schedule_retrain
        pending_retrains = db.scalars(
            select(RetrainTask)
            .where(RetrainTask.owner_id == ownerId, RetrainTask.status == "pending")
            .order_by(RetrainTask.scheduled_at)
        ).all()
        due_retrains = [rt for rt in pending_retrains if rt.scheduled_at <= datetime.utcnow()]

        # 最近的训练记录数
        recent_training_count = db.scalar(
            select(func.count(TrainingRecord.id))
            .where(TrainingRecord.owner_id == ownerId)
        ) or 0

        return {
            "ownerId": ownerId,
            "hasCompletedAssessment": user.has_completed_assessment,
            "hasPet": user.has_pet,
            "abilityProfile": profile,
            "overallScore": overall_score,
            "weakDimensions": weak_dims,
            "packageProgress": package_progress,
            "abilityChange": ability_change,
            "dueRetrainCount": len(due_retrains),
            "recentTrainingCount": recent_training_count,
            "pet": pet_to_response(pet) if pet else None,
        }


