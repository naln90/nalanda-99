"""校园活动集体共建解锁服务 — V3.0 核心。

机制（见方案§10）：全体注册用户将「当前可用盾能」自主投向感兴趣的活动，
所有投放量汇总为活动共建进度，达到目标盾能后状态由「共建中」变为「已共同解锁」。
系统只负责展示、共同解锁与官方通知连接，不自动创建报名/签到/志愿时长记录。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .energy_service import invest_energy
from .models import ActivityContribution, CampusActivity


def _serialize(activity: CampusActivity, contributor_energy: int | None = None) -> dict[str, Any]:
    progress = activity.current_progress or 0
    target = activity.target_energy or 0
    ratio = round(progress / target * 100, 1) if target > 0 else 0.0
    return {
        "id": activity.id,
        "title": activity.title,
        "category": activity.category,
        "description": activity.description,
        "organizer": activity.organizer,
        "interestDirection": activity.interest_direction,
        "noticeUrl": activity.notice_url,
        "targetEnergy": target,
        "currentProgress": progress,
        "contributorCount": activity.contributor_count,
        "progressRatio": min(100.0, ratio),
        "status": activity.status,
        "noticeText": activity.notice_text,
        "myContribution": contributor_energy or 0,
        "releasedAt": activity.released_at.isoformat() if isinstance(activity.released_at, datetime) else None,
        "boundaryNotice": (
            "活动解锁仅代表获得活动认知、共同荣誉或参与资格，不等同于报名或实际参加；"
            "具体活动由学校团委统一组织，是否开展以团委正式通知为准。"
        ),
    }


def get_activity(db: Session, activity_id: str) -> CampusActivity | None:
    return db.scalar(select(CampusActivity).where(CampusActivity.id == activity_id))


def list_activities(db: Session, include_disabled: bool = False) -> list[CampusActivity]:
    stmt = select(CampusActivity)
    if not include_disabled:
        stmt = stmt.where(CampusActivity.enabled.is_(True))
    return list(db.scalars(stmt.order_by(CampusActivity.created_at.asc())).all())


def my_contribution(db: Session, owner_id: str, activity_id: str) -> int:
    rows = db.scalars(
        select(ActivityContribution).where(
            ActivityContribution.owner_id == owner_id,
            ActivityContribution.activity_id == activity_id,
        )
    ).all()
    return sum(r.amount for r in rows)


def contribute(db: Session, owner_id: str, activity_id: str, amount: int) -> dict[str, Any]:
    """学生向活动投放盾能，触发共建进度更新与（可能）共同解锁。"""
    if amount <= 0:
        raise ValueError("投放数量必须为正数")
    activity = get_activity(db, activity_id)
    if activity is None:
        raise ValueError("活动不存在")
    if not activity.enabled:
        raise ValueError("活动已关闭，无法投放")

    # 1) 先扣减学生可用盾能（统一账本）
    balances = invest_energy(db, owner_id, activity_id, amount, note=f"投向活动【{activity.title}】")

    # 2) 写入贡献明细
    db.add(ActivityContribution(owner_id=owner_id, activity_id=activity_id, amount=amount))

    # 3) 更新活动共建进度
    # 判断：若这是该用户第一条贡献记录（即插入前为空）才增加参与人数
    before = (
        db.execute(
            select(ActivityContribution.id).where(
                ActivityContribution.owner_id == owner_id,
                ActivityContribution.activity_id == activity_id,
            )
        ).first()
    )
    first_contribution = before is None

    activity.current_progress = (activity.current_progress or 0) + amount
    if first_contribution:
        activity.contributor_count = (activity.contributor_count or 0) + 1
    # 达到目标盾能即共同解锁
    if activity.status in ("draft", "building") and (activity.current_progress or 0) >= (activity.target_energy or 0):
        activity.status = "unlocked"

    db.commit()
    db.refresh(activity)
    return {
        "activity": _serialize(activity, contributor_energy=amount),
        "balances": balances,
    }


def release_notice(
    db: Session,
    activity_id: str,
    notice_text: str,
    notice_url: str | None = None,
) -> dict[str, Any]:
    """校方/团委发布正式活动通知；仅改变展示与状态，不创建报名或签到记录。"""
    activity = get_activity(db, activity_id)
    if activity is None:
        raise ValueError("活动不存在")
    activity.notice_text = notice_text
    if notice_url is not None:
        activity.notice_url = notice_url
    activity.status = "notice_released"
    activity.released_at = datetime.utcnow()
    db.commit()
    db.refresh(activity)
    return _serialize(activity)


def set_activity_status(db: Session, activity_id: str, status: str) -> dict[str, Any]:
    activity = get_activity(db, activity_id)
    if activity is None:
        raise ValueError("活动不存在")
    activity.status = status
    db.commit()
    db.refresh(activity)
    return _serialize(activity)
