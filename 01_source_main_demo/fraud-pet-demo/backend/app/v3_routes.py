"""V3.0 双端口 API 路由。

包含：月度主题(校方发布端)、统一盾能账本、校园活动集体共建、校方数据看板。
所有路由以 `create_*_router(get_db)` 工厂返回 APIRouter，由 main.py 统一 include。
鉴权沿用 Demo 约定：以 ownerId 参数标识身份，校方接口校验 Account.role == 'school'。
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .activity_service import (
    contribute as activity_contribute,
    list_activities,
    my_contribution,
    release_notice as activity_release_notice,
    set_activity_status,
)
from .energy_service import get_balances, get_ledger
from .models import Account, CampusActivity, LearningPlan, LearningPlanItem, Theme, User
from .theme_service import (
    complete_theme_item,
    confirm_theme,
    create_theme,
    generate_theme_plan,
    get_active_theme,
    join_theme,
)
# 演示入口门控：生产环境（AUTH_REQUIRED=true）关闭校方演示登录，强制真实校方账号登录。
from .helpers import _auth_required


# ─────────────────────────── 鉴权辅助 ───────────────────────────
def _require_school(db: Session, owner_id: str) -> Account:
    acct = db.scalar(select(Account).where(Account.owner_id == owner_id))
    if not acct or acct.role != "school":
        raise HTTPException(status_code=403, detail="需要校方发布端权限")
    return acct


def _get_or_create_school(db: Session) -> dict[str, Any]:
    existing = db.scalar(select(Account).where(Account.username == "school-demo"))
    if existing:
        user = db.scalar(select(User).where(User.owner_id == existing.owner_id))
        return {"ownerId": existing.owner_id, "nickname": existing.nickname, "currentUser": _user_resp(user)}
    owner_id = f"S-{secrets.randbelow(9000) + 1000}**"
    # 校方演示账号不再以空明文口令落库：使用一次性随机口令哈希，消除空口令反模式（A20）
    acct = Account(
        username="school-demo",
        password_hash=hashlib.sha256(secrets.token_urlsafe(16).encode()).hexdigest(),
        owner_id=owner_id,
        nickname="校方发布端",
        role="school",
    )
    db.add(acct)
    user = User(owner_id=owner_id, role="school")
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"ownerId": owner_id, "nickname": "校方发布端", "currentUser": _user_resp(user)}


def _user_resp(user: User) -> dict[str, Any]:
    return {
        "ownerId": user.owner_id,
        "hasCompletedAssessment": user.has_completed_assessment,
        "hasPet": user.has_pet,
        "role": user.role,
    }


# ─────────────────────────── 序列化 ───────────────────────────
def _serialize_theme(theme: Theme) -> dict[str, Any]:
    return {
        "id": theme.id,
        "title": theme.title,
        "description": theme.description,
        "periodDays": theme.period_days,
        "targetAudience": theme.target_audience,
        "scope": theme.scope,
        "baseRequired": theme.base_required,
        "electiveDirection": theme.elective_direction,
        "expectedOutcome": theme.expected_outcome,
        "baseAssessment": theme.base_assessment,
        "publishTime": theme.publish_time,
        "status": theme.status,
        "creatorId": theme.creator_id,
        "planId": theme.plan_id,
        "aiMetadata": json.loads(theme.ai_metadata_json or "{}"),
        "publishedAt": theme.published_at.isoformat() if isinstance(theme.published_at, datetime) else None,
        "createdAt": theme.created_at.isoformat() if isinstance(theme.created_at, datetime) else None,
    }


def _serialize_item(it: LearningPlanItem) -> dict[str, Any]:
    return {
        "id": it.id,
        "planId": it.plan_id,
        "category": it.category,
        "title": it.title,
        "description": it.description,
        "resourceHint": it.resource_hint,
        "acceptanceCriteria": it.acceptance_criteria,
        "energyReward": it.energy_reward,
        "estimatedMinutes": it.estimated_minutes,
        "dueDay": it.due_day,
        "orderIndex": it.order_index,
        "status": "done" if it.status == "completed" else it.status,
        "completedAt": it.completed_at.isoformat() if isinstance(it.completed_at, datetime) else None,
    }


# ─────────────────────────── 请求模型 ───────────────────────────
class ThemeCreateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    periodDays: int = Field(default=7, ge=1, le=365)
    targetAudience: str = Field(default="在校大学生", max_length=60)
    scope: str = Field(default="全校", max_length=60)
    baseRequired: str = Field(default="", max_length=200)
    electiveDirection: str = Field(default="", max_length=100)
    expectedOutcome: str = Field(default="", max_length=500)
    baseAssessment: str = Field(default="", max_length=500)
    publishTime: str = Field(default="", max_length=40)


class ThemeConfirmRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    edits: dict[str, Any] | None = None


class ItemCompleteRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class ActivityCreateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=120)
    category: str = Field(default="校园公益", max_length=40)
    description: str = Field(default="", max_length=1000)
    organizer: str = Field(default="学校团委", max_length=60)
    interestDirection: str = Field(default="综合参与", max_length=60)
    targetEnergy: int = Field(default=1000, ge=0, le=1000000)
    noticeUrl: str = Field(default="", max_length=500)


class ActivityContributeRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    amount: int = Field(ge=1)


class ActivityNoticeRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    noticeText: str = Field(default="", max_length=1000)
    noticeUrl: str = Field(default="", max_length=500)


# ─────────────────────────── 主题路由 ───────────────────────────
def create_theme_router(get_db: Callable[[], Session]) -> APIRouter:
    router = APIRouter(prefix="/api/theme", tags=["V3 主题"])

    @router.post("/create")
    def api_create_theme(payload: ThemeCreateRequest, db: Session = Depends(get_db)):
        _require_school(db, payload.ownerId)
        theme = create_theme(
            db,
            payload.ownerId,
            {
                "title": payload.title,
                "description": payload.description,
                "periodDays": payload.periodDays,
                "targetAudience": payload.targetAudience,
                "scope": payload.scope,
                "baseRequired": payload.baseRequired,
                "electiveDirection": payload.electiveDirection,
                "expectedOutcome": payload.expectedOutcome,
                "baseAssessment": payload.baseAssessment,
                "publishTime": payload.publishTime,
            },
        )
        return _serialize_theme(theme)

    @router.post("/{theme_id}/generate")
    def api_generate(payload: ItemCompleteRequest, theme_id: str, db: Session = Depends(get_db)):
        _require_school(db, payload.ownerId)
        theme = generate_theme_plan(db, theme_id)
        return _serialize_theme(theme)

    @router.post("/{theme_id}/confirm")
    def api_confirm(payload: ThemeConfirmRequest, theme_id: str, db: Session = Depends(get_db)):
        _require_school(db, payload.ownerId)
        result = confirm_theme(db, theme_id, payload.edits)
        return {"theme": _serialize_theme(result["theme"]), "planId": result["plan"].id}

    @router.get("/list")
    def api_list(ownerId: str = Query(...), db: Session = Depends(get_db)):
        _require_school(db, ownerId)
        rows = db.scalars(select(Theme).where(Theme.creator_id == ownerId).order_by(Theme.created_at.desc())).all()
        return [_serialize_theme(t) for t in rows]

    @router.get("/active")
    def api_active(ownerId: str = Query(None), db: Session = Depends(get_db)):
        theme = get_active_theme(db)
        if not theme or not theme.plan_id:
            return {"theme": None, "items": [], "joined": False}
        # 已加入的学生返回其个人任务包条目；否则返回校方任务包作为预览
        personal = None
        if ownerId:
            personal = db.scalar(
                select(LearningPlan).where(
                    LearningPlan.owner_id == ownerId,
                    LearningPlan.goal_id == theme.id,
                    LearningPlan.source == "school-theme",
                )
            )
        if personal:
            items = db.scalars(
                select(LearningPlanItem)
                .where(LearningPlanItem.plan_id == personal.id)
                .order_by(LearningPlanItem.order_index)
            ).all()
            return {
                "theme": _serialize_theme(theme),
                "items": [_serialize_item(it) for it in items],
                "joined": True,
                "planId": personal.id,
            }
        items = db.scalars(
            select(LearningPlanItem).where(LearningPlanItem.plan_id == theme.plan_id).order_by(LearningPlanItem.order_index)
        ).all()
        return {"theme": _serialize_theme(theme), "items": [_serialize_item(it) for it in items], "joined": False, "planId": theme.plan_id}

    @router.post("/{theme_id}/join")
    def api_join(payload: ItemCompleteRequest, theme_id: str, db: Session = Depends(get_db)):
        plan = join_theme(db, payload.ownerId, theme_id)
        items = db.scalars(select(LearningPlanItem).where(LearningPlanItem.plan_id == plan.id).order_by(LearningPlanItem.order_index)).all()
        return {"planId": plan.id, "items": [_serialize_item(it) for it in items]}

    @router.post("/items/{item_id}/complete")
    def api_complete(payload: ItemCompleteRequest, item_id: str, db: Session = Depends(get_db)):
        result = complete_theme_item(db, payload.ownerId, item_id)
        if result.get("alreadyDone"):
            return {"alreadyDone": True, "balances": result["balances"]}
        item = result["item"]
        return {"item": _serialize_item(item), "balances": result["balances"]}

    return router


# ─────────────────────────── 盾能路由 ───────────────────────────
def create_energy_router(get_db: Callable[[], Session]) -> APIRouter:
    router = APIRouter(prefix="/api/energy", tags=["V3 盾能"])

    @router.get("/balance")
    def api_balance(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)):
        return get_balances(db, ownerId)

    @router.get("/ledger")
    def api_ledger(ownerId: str = Query("U-2408**"), limit: int = Query(50, le=200), db: Session = Depends(get_db)):
        return {"ownerId": ownerId, "ledger": get_ledger(db, ownerId, limit)}

    return router


# ─────────────────────────── 活动路由 ───────────────────────────
def create_activity_router(get_db: Callable[[], Session]) -> APIRouter:
    router = APIRouter(prefix="/api/activities", tags=["V3 活动"])

    @router.get("")
    def api_list(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)):
        acts = list_activities(db)
        out = []
        for a in acts:
            serialized = activity_public(a)
            serialized["myContribution"] = my_contribution(db, ownerId, a.id)
            out.append(serialized)
        return out

    @router.post("/create")
    def api_create(payload: ActivityCreateRequest, db: Session = Depends(get_db)):
        _require_school(db, payload.ownerId)
        act = CampusActivity(
            id=f"act-{secrets.token_hex(5)}",
            title=payload.title,
            category=payload.category,
            description=payload.description,
            organizer=payload.organizer,
            interest_direction=payload.interestDirection,
            notice_url=payload.noticeUrl,
            target_energy=payload.targetEnergy,
            current_progress=0,
            contributor_count=0,
            status="building",
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        return activity_public(act)

    @router.post("/{activity_id}/contribute")
    def api_contribute(payload: ActivityContributeRequest, activity_id: str, db: Session = Depends(get_db)):
        try:
            result = activity_contribute(db, payload.ownerId, activity_id, payload.amount)
        except ValueError as e:
            # 例如「当前可用盾能不足」——业务可预期错误，返回 400 友好提示，避免 500
            raise HTTPException(status_code=400, detail=str(e))
        out = dict(result["activity"])
        out["myContribution"] = my_contribution(db, payload.ownerId, activity_id)
        return {"activity": out, "balances": result["balances"]}

    @router.post("/{activity_id}/release-notice")
    def api_release(payload: ActivityNoticeRequest, activity_id: str, db: Session = Depends(get_db)):
        _require_school(db, payload.ownerId)
        out = activity_release_notice(db, activity_id, payload.noticeText, payload.noticeUrl or None)
        out["myContribution"] = my_contribution(db, payload.ownerId, activity_id)
        return out

    @router.post("/{activity_id}/status")
    def api_status(payload: ItemCompleteRequest, activity_id: str, status: str = Query(...), db: Session = Depends(get_db)):
        _require_school(db, payload.ownerId)
        return set_activity_status(db, activity_id, status)

    return router


def activity_public(a: CampusActivity) -> dict[str, Any]:
    """CampusActivity 公开序列化（含共建进度、边界说明）。"""
    target = a.target_energy or 0
    progress = a.current_progress or 0
    ratio = round(progress / target * 100, 1) if target > 0 else 0.0
    return {
        "id": a.id,
        "title": a.title,
        "category": a.category,
        "description": a.description,
        "organizer": a.organizer,
        "interestDirection": a.interest_direction,
        "noticeUrl": a.notice_url,
        "targetEnergy": a.target_energy,
        "currentProgress": a.current_progress,
        "contributorCount": a.contributor_count,
        "progressRatio": min(100.0, ratio),
        "status": a.status,
        "noticeText": a.notice_text,
        "releasedAt": a.released_at.isoformat() if isinstance(a.released_at, datetime) else None,
        "boundaryNotice": (
            "活动解锁仅代表获得活动认知、共同荣誉或参与资格，不等同于报名或实际参加；"
            "具体活动由学校团委统一组织，是否开展以团委正式通知为准。"
        ),
    }


# ─────────────────────────── 校方路由 ───────────────────────────
def create_school_router(get_db: Callable[[], Session]) -> APIRouter:
    router = APIRouter(prefix="/api/school", tags=["V3 校方"])

    @router.post("/demo-login")
    def api_demo_login(db: Session = Depends(get_db)):
        # 生产环境关闭演示入口，强制走真实校方账号登录。
        if _auth_required():
            raise HTTPException(status_code=403, detail="演示入口已在生产环境关闭，请使用校方账号登录")
        return _get_or_create_school(db)

    @router.get("/dashboard")
    def api_dashboard(ownerId: str = Query(...), db: Session = Depends(get_db)):
        _require_school(db, ownerId)
        total_users = db.scalar(select(func.count(User.id)))
        students = db.scalar(select(func.count(User.id)).where(User.role == "student"))
        # 任务包完成情况（基于 LearningPlanItem）
        total_items = db.scalar(select(func.count(LearningPlanItem.id)))
        completed_items = db.scalar(
            select(func.count(LearningPlanItem.id)).where(LearningPlanItem.status == "completed")
        )
        active_theme = get_active_theme(db)
        activities = list_activities(db)
        activity_out = [
            {
                "id": a.id,
                "title": a.title,
                "currentProgress": a.current_progress,
                "targetEnergy": a.target_energy,
                "status": a.status,
                "contributorCount": a.contributor_count,
            }
            for a in activities
        ]
        return {
            "totalUsers": total_users or 0,
            "studentCount": students or 0,
            "taskCompletionRate": round(completed_items / total_items * 100, 1) if total_items else 0.0,
            "activeTheme": _serialize_theme(active_theme) if active_theme else None,
            "activities": activity_out,
        }

    return router
