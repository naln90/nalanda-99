from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
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


router = APIRouter(prefix="/api/task-package", tags=["task_package"])

@router.post("/generate")

def generate_task_package(payload: TaskPackageGenerateRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """生成 AI 任务包（7天/14天训练计划）"""
        from ..ability_profile import compute_ability_profile
        from ..task_planner import generate_plan_rule

        # 检查是否已有进行中的任务包
        existing = db.scalar(
            select(TaskPackage)
            .where(TaskPackage.owner_id == payload.ownerId, TaskPackage.status == "active")
        )
        if existing:
            return {"message": "已有进行中的任务包", "packageId": existing.id}

        # 获取能力画像
        latest = db.scalar(
            select(AssessmentResult)
            .where(AssessmentResult.owner_id == payload.ownerId)
            .order_by(AssessmentResult.created_at.desc())
        )
        if not latest:
            raise HTTPException(status_code=400, detail="请先完成测评")

        profile = {
            "scores": json.loads(latest.ability_profile_json),
            "weakDimensions": json.loads(latest.weak_dimensions_json),
        }

        # 使用规则引擎生成计划（同步，不依赖 AI）
        plan = generate_plan_rule(profile, payload.planType)
        plan["source"] = "rule"
        plan["motivationText"] = "坚持训练，每天进步一点点！"

        # 保存任务包和条目
        now = datetime.utcnow()
        total_days = 7 if payload.planType == "7day" else 14
        from datetime import timedelta
        pkg = TaskPackage(
            id=f"pkg-{now.strftime('%Y%m%d')}-{secrets.randbelow(9000)+1000}",
            owner_id=payload.ownerId,
            plan_type=payload.planType,
            status="active",
            ability_profile_json=json.dumps(profile["scores"], ensure_ascii=False),
            generated_by=plan.get("source", "rule"),
            total_items=len(plan.get("items", [])),
            completed_items=0,
            created_at=now,
            expires_at=now + timedelta(days=total_days),
        )
        db.add(pkg)
        db.flush()

        for item in plan.get("items", []):
            pkg_item = TaskPackageItem(
                id=item["id"],
                package_id=pkg.id,
                owner_id=payload.ownerId,
                day_index=item["dayIndex"],
                task_type=item["taskType"],
                task_ref=item["taskRef"],
                task_title=item["taskTitle"],
                target_ability=item.get("targetAbility", "识诈力"),
                estimated_minutes=item.get("estimatedMinutes", 15),
                status="pending",
            )
            db.add(pkg_item)

        db.commit()

        return {
            "packageId": pkg.id,
            "planType": pkg.plan_type,
            "motivationText": plan.get("motivationText", ""),
            "totalDays": total_days,
            "items": plan.get("items", []),
            "weakDimensionSuggestions": plan.get("weakDimensionSuggestions", []),
            "source": plan.get("source", "rule"),
        }


@router.get("/current")

def current_task_package(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
        """获取当前进行中的任务包"""
        pkg = db.scalar(
            select(TaskPackage)
            .where(TaskPackage.owner_id == ownerId, TaskPackage.status == "active")
            .order_by(TaskPackage.created_at.desc())
        )
        if not pkg:
            return {"package": None, "message": "暂无进行中的任务包"}

        items = db.scalars(
            select(TaskPackageItem)
            .where(TaskPackageItem.package_id == pkg.id)
            .order_by(TaskPackageItem.day_index)
        ).all()

        return {
            "package": {
                "id": pkg.id,
                "planType": pkg.plan_type,
                "status": pkg.status,
                "totalItems": pkg.total_items,
                "completedItems": pkg.completed_items,
                "createdAt": pkg.created_at.isoformat(),
                "expiresAt": pkg.expires_at.isoformat(),
            },
            "items": [
                {
                    "id": item.id,
                    "dayIndex": item.day_index,
                    "taskType": item.task_type,
                    "taskRef": item.task_ref,
                    "taskTitle": item.task_title,
                    "targetAbility": item.target_ability,
                    "estimatedMinutes": item.estimated_minutes,
                    "status": item.status,
                    "completedAt": item.completed_at.isoformat() if item.completed_at else None,
                }
                for item in items
            ],
        }


@router.post("/items/{item_id}/complete")

def complete_task_package_item(item_id: str, payload: TaskPackageItemCompleteRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """标记任务包条目完成"""
        item = db.get(TaskPackageItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Task item not found")

        item.status = "completed"
        item.completed_at = datetime.utcnow()
        item.score = payload.score

        # 更新任务包进度
        pkg = db.get(TaskPackage, item.package_id)
        if pkg:
            pkg.completed_items = db.scalar(
                select(func.count(TaskPackageItem.id))
                .where(TaskPackageItem.package_id == pkg.id, TaskPackageItem.status == "completed")
            ) or 0
            if pkg.completed_items >= pkg.total_items:
                pkg.status = "completed"

        db.commit()

        return {"item": {"id": item.id, "status": item.status, "completedAt": item.completed_at.isoformat()}}


