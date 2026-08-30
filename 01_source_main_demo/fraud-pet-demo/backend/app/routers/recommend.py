"""个性化推荐与学习督促（需求#27 / #17）。

- /recommend/market：按用户学习目标主题/专业方向匹配并排序集市任务包与成果。
- /recommend/study：汇总待办任务项、待复训、薄弱维度，形成个性化督促清单。
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/recommend", tags=["个性化推荐与督促"])


def _json_load(value: str, default) -> any:  # type: ignore[name-defined]
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


@router.get("/market")
def recommend_market(
    ownerId: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    goals = db.scalars(select(LearningGoal).where(LearningGoal.owner_id == ownerId)).all()
    user_themes = {g.theme for g in goals}
    user_major = {g.major_direction for g in goals}
    rows = db.scalars(
        select(LearningMarketListing)
        .where(LearningMarketListing.status == "published")
        .order_by(LearningMarketListing.created_at.desc())
    ).all()
    scored = []
    for r in rows:
        tags = _json_load(r.tags_json, [])
        score = 0
        if r.theme in user_themes:
            score += 3
        if r.theme in user_major:
            score += 2
        score += len(set(tags) & user_themes)
        scored.append((score, r))
    scored.sort(key=lambda x: (x[0], x[1].reuse_count), reverse=True)
    listings = [
        {
            "id": r.id,
            "title": r.title,
            "theme": r.theme,
            "summary": r.summary,
            "tags": _json_load(r.tags_json, []),
            "matchScore": s,
            "likes": r.likes,
            "ratingAvg": r.rating_avg,
        }
        for s, r in scored[:limit]
    ]
    return {"recommendations": listings}


@router.get("/study")
def study_reminders(ownerId: str = Query(min_length=1), db: Session = Depends(get_db)) -> dict:
    plans = db.scalars(
        select(LearningPlan).where(LearningPlan.owner_id == ownerId, LearningPlan.status == "active")
    ).all()
    pending_items = []
    for p in plans:
        items = db.scalars(
            select(LearningPlanItem).where(
                LearningPlanItem.plan_id == p.id,
                LearningPlanItem.status.in_(["not_started", "in_progress"]),
            ).order_by(LearningPlanItem.due_day)
        ).all()
        for it in items:
            pending_items.append(
                {"planId": p.id, "itemId": it.id, "title": it.title, "dueDay": it.due_day, "status": it.status}
            )
    retrain = db.scalars(
        select(RetrainTask)
        .where(RetrainTask.owner_id == ownerId, RetrainTask.status == "pending")
        .order_by(RetrainTask.scheduled_at)
    ).all()
    retrain_list = [
        {"id": rt.id, "fraudType": rt.fraud_type, "attempt": rt.attempt, "scheduledAt": rt.scheduled_at.isoformat()}
        for rt in retrain
    ]
    snap = db.scalars(
        select(AbilitySnapshot).where(AbilitySnapshot.owner_id == ownerId).order_by(AbilitySnapshot.created_at.desc())
    ).first()
    weak_dims = _json_load(snap.weak_dimensions_json, []) if snap else []
    return {
        "pendingItems": pending_items[:20],
        "retrainTasks": retrain_list[:20],
        "weakDimensions": weak_dims,
    }
