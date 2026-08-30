from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
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


router = APIRouter(prefix="/api/v1/task-package", tags=["v1_task_package"])

@router.post("/generate")

def v1_generate_task_package(
        payload: TaskPackageGenerateRequest, db: Session = Depends(get_db)
    ) -> dict[str, object]:
        """生成个性化任务包（v1）。

        根据五维能力画像生成 7 天或 14 天训练计划。
        - 完全由规则引擎驱动（薄弱维度 → 对应训练）
        - 每项任务含目标、完成标准、验收方式
        - AI 仅在可用时填充激励文案
        """
        from ..task_planner import generate_plan_rule

        # 检查是否已有进行中的任务包
        existing = db.scalar(
            select(TaskPackage)
            .where(TaskPackage.owner_id == payload.ownerId, TaskPackage.status == "active")
        )
        if existing:
            items = (
                db.query(TaskPackageItem)
                .filter(TaskPackageItem.package_id == existing.id)
                .order_by(TaskPackageItem.day_index)
                .all()
            )
            return {
                "packageId": existing.id,
                "planType": existing.plan_type,
                "status": existing.status,
                "message": "已有进行中的任务包",
                "items": [
                    {
                        "id": it.id,
                        "dayIndex": it.day_index,
                        "taskType": it.task_type,
                        "taskRef": it.task_ref,
                        "taskTitle": it.task_title,
                        "targetAbility": it.target_ability,
                        "estimatedMinutes": it.estimated_minutes,
                        "status": it.status,
                    }
                    for it in items
                ],
            }

        # 获取最新能力画像
        latest = db.scalar(
            select(AssessmentResult)
            .where(AssessmentResult.owner_id == payload.ownerId)
            .order_by(AssessmentResult.created_at.desc())
        )
        if not latest:
            raise HTTPException(status_code=400, detail="请先完成测评，生成能力画像后再创建任务包")

        profile = {
            "scores": json.loads(latest.ability_profile_json),
            "weakDimensions": json.loads(latest.weak_dimensions_json),
        }

        # 规则引擎生成计划
        plan = generate_plan_rule(profile, payload.planType)

        # 保存到 TaskPackage + TaskPackageItem（复用现有表结构）
        now = datetime.utcnow()
        total_days = 7 if payload.planType == "7day" else 14
        from datetime import timedelta

        pkg = TaskPackage(
            id=f"pkg-{now.strftime('%Y%m%d')}-{secrets.randbelow(9000)+1000}",
            owner_id=payload.ownerId,
            plan_type=payload.planType,
            status="active",
            ability_profile_json=json.dumps(profile["scores"], ensure_ascii=False),
            generated_by="rule",
            total_items=len(plan.get("items", [])),
            completed_items=0,
            created_at=now,
            expires_at=now + timedelta(days=total_days),
        )
        db.add(pkg)
        db.flush()

        v1_items: list[dict[str, object]] = []
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
            v1_items.append({
                "id": item["id"],
                "dayIndex": item["dayIndex"],
                "taskType": item["taskType"],
                "taskRef": item["taskRef"],
                "taskTitle": item["taskTitle"],
                "targetAbility": item.get("targetAbility", "识诈力"),
                "estimatedMinutes": item.get("estimatedMinutes", 15),
                "objective": item.get("objective", ""),
                "completionCriteria": item.get("completionCriteria", ""),
                "acceptanceMethod": item.get("acceptanceMethod", ""),
                "retrainCondition": item.get("retrainCondition", "正确率 < 60% 触发复训"),
                "status": "pending",
            })

        db.commit()

        return {
            "packageId": pkg.id,
            "planType": pkg.plan_type,
            "status": pkg.status,
            "totalDays": total_days,
            "totalItems": len(v1_items),
            "items": v1_items,
            "weakDimensionSuggestions": plan.get("weakDimensionSuggestions", []),
            "motivationText": "坚持训练，每天进步一点点！",
            "createdAt": now.isoformat(),
            "expiresAt": pkg.expires_at.isoformat(),
        }


@router.get("/current")

def v1_current_task_package(
        ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)
    ) -> dict[str, object]:
        """获取当前进行中的 v1 任务包（含进度）。"""
        pkg = db.scalar(
            select(TaskPackage)
            .where(TaskPackage.owner_id == ownerId, TaskPackage.status == "active")
            .order_by(TaskPackage.created_at.desc())
        )
        if not pkg:
            return {"taskPackage": None, "hasActivePackage": False}

        items = (
            db.query(TaskPackageItem)
            .filter(TaskPackageItem.package_id == pkg.id)
            .order_by(TaskPackageItem.day_index)
            .all()
        )

        return {
            "taskPackage": {
                "packageId": pkg.id,
                "planType": pkg.plan_type,
                "status": pkg.status,
                "totalItems": pkg.total_items,
                "completedItems": pkg.completed_items,
                "progress": round(pkg.completed_items / pkg.total_items * 100, 1) if pkg.total_items > 0 else 0,
                "createdAt": pkg.created_at.isoformat(),
                "expiresAt": pkg.expires_at.isoformat(),
                "items": [
                    {
                        "id": it.id,
                        "dayIndex": it.day_index,
                        "taskType": it.task_type,
                        "taskRef": it.task_ref,
                        "taskTitle": it.task_title,
                        "targetAbility": it.target_ability,
                        "estimatedMinutes": it.estimated_minutes,
                        "status": it.status,
                        "score": it.score,
                        "completedAt": it.completed_at.isoformat() if it.completed_at else None,
                    }
                    for it in items
                ],
            },
            "hasActivePackage": True,
        }


