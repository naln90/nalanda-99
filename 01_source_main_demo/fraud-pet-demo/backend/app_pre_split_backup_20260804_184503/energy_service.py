"""统一盾能账本服务 — V3.0 核心。

平台只使用一种成长资源「盾能」，同时维护三口径（见方案§9.1）：
- 累计获得盾能 cumulative：历史上通过有效学习获得的总量，不因投放减少（用于个人等级）。
- 当前可用盾能 available：当前可用于支持活动的余额，投放后减少。
- 累计投放盾能 contributed：历史支持不同活动的总量，只增不减（个人共建记录）。

所有盾能发放、投放与余额更新都经过本模块的统一函数，避免多个页面分别计算。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import EnergyLedger

# 个人等级阈值（累计获得盾能）。方案未给出固定表，这里采用递增档位，
# 等级 = 不超过累计值的最高档位序号（1 起）。可随产品调整。
LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500, 7500, 10000]


def compute_level(cumulative: int) -> int:
    """依据累计获得盾能计算个人等级（1 起）。"""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if cumulative >= threshold:
            level = i + 1
    return level


def _latest_entry(db: Session, owner_id: str) -> EnergyLedger | None:
    return db.scalar(
        select(EnergyLedger)
        .where(EnergyLedger.owner_id == owner_id)
        .order_by(EnergyLedger.id.desc())
    )


def get_balances(db: Session, owner_id: str) -> dict[str, Any]:
    """返回三口径余额与个人等级。"""
    entry = _latest_entry(db, owner_id)
    cumulative = entry.cumulative_after if entry else 0
    available = entry.available_after if entry else 0
    contributed = entry.contributed_after if entry else 0
    return {
        "ownerId": owner_id,
        "cumulativeEnergy": cumulative,
        "availableEnergy": available,
        "contributedEnergy": contributed,
        "level": compute_level(cumulative),
    }


def _write(
    db: Session,
    owner_id: str,
    tx_type: str,
    delta: int,
    *,
    cumulative: int,
    available: int,
    contributed: int,
    source_ref: str = "",
    note: str = "",
) -> EnergyLedger:
    entry = EnergyLedger(
        owner_id=owner_id,
        tx_type=tx_type,
        source_ref=source_ref,
        delta=delta,
        cumulative_after=cumulative,
        available_after=available,
        contributed_after=contributed,
        note=note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def award_energy(
    db: Session,
    owner_id: str,
    amount: int,
    tx_type: str,
    *,
    source_ref: str = "",
    note: str = "",
) -> dict[str, Any]:
    """发放盾能（学习行为产生）。累计获得与当前可用同时增加，累计投放不变。"""
    if amount <= 0:
        raise ValueError("发放数量必须为正数")
    prev = _latest_entry(db, owner_id)
    cumulative = (prev.cumulative_after if prev else 0) + amount
    available = (prev.available_after if prev else 0) + amount
    contributed = prev.contributed_after if prev else 0
    _write(
        db,
        owner_id,
        tx_type,
        amount,
        cumulative=cumulative,
        available=available,
        contributed=contributed,
        source_ref=source_ref,
        note=note,
    )
    return get_balances(db, owner_id)


def invest_energy(
    db: Session,
    owner_id: str,
    activity_id: str,
    amount: int,
    *,
    note: str = "",
) -> dict[str, Any]:
    """投放盾能到校园活动（共同解锁）。当前可用减少、累计投放增加、累计获得不变。"""
    if amount <= 0:
        raise ValueError("投放数量必须为正数")
    prev = _latest_entry(db, owner_id)
    available = prev.available_after if prev else 0
    if available < amount:
        raise ValueError("当前可用盾能不足")
    cumulative = prev.cumulative_after if prev else 0
    contributed = (prev.contributed_after if prev else 0) + amount
    _write(
        db,
        owner_id,
        "invest_activity",
        -amount,
        cumulative=cumulative,
        available=available - amount,
        contributed=contributed,
        source_ref=activity_id,
        note=note or f"投向活动 {activity_id}",
    )
    return get_balances(db, owner_id)


def adjust_energy(
    db: Session,
    owner_id: str,
    delta: int,
    *,
    note: str = "后台调整",
) -> dict[str, Any]:
    """后台修正（仅用于运维/演示微调），三口径按比例调整。"""
    prev = _latest_entry(db, owner_id)
    cumulative = (prev.cumulative_after if prev else 0) + (delta if delta > 0 else 0)
    available = (prev.available_after if prev else 0) + delta
    contributed = prev.contributed_after if prev else 0
    if available < 0:
        available = 0
    _write(
        db,
        owner_id,
        "adjust",
        delta,
        cumulative=cumulative,
        available=available,
        contributed=contributed,
        note=note,
    )
    return get_balances(db, owner_id)


def get_ledger(db: Session, owner_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """盾能流水（按时间倒序）。"""
    rows = (
        db.scalars(
            select(EnergyLedger)
            .where(EnergyLedger.owner_id == owner_id)
            .order_by(EnergyLedger.id.desc())
            .limit(limit)
        )
        .all()
    )
    return [
        {
            "id": r.id,
            "txType": r.tx_type,
            "sourceRef": r.source_ref,
            "delta": r.delta,
            "cumulativeAfter": r.cumulative_after,
            "availableAfter": r.available_after,
            "contributedAfter": r.contributed_after,
            "note": r.note,
            "createdAt": r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at),
        }
        for r in rows
    ]


def total_cumulative(db: Session) -> int:
    """全站累计获得盾能（用于展示共建总规模）。"""
    row = db.execute(
        select(func.coalesce(func.sum(EnergyLedger.delta), 0)).where(
            EnergyLedger.tx_type != "invest_activity"
        )
    ).scalar_one()
    return int(row or 0)
