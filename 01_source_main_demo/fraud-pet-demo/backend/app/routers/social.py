"""好友关系与隐私三级支撑（需求#30/#32）。

提供好友申请、接受、列表、删除；配合 helpers.can_view_resource 实现
「公开 / 私密 / 仅好友」可见性过滤。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/social", tags=["社交与好友"])


class FriendRequest(BaseModel):
    ownerId: str
    friendOwnerId: str


@router.post("/friends/request")
def friend_request(payload: FriendRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    if owner_id == payload.friendOwnerId:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")
    existing = db.scalar(
        select(Friendship).where(
            (Friendship.requester_id == owner_id) & (Friendship.addressee_id == payload.friendOwnerId)
            | (Friendship.requester_id == payload.friendOwnerId) & (Friendship.addressee_id == owner_id)
        )
    )
    if existing:
        return {"status": existing.status, "message": "好友关系已存在"}
    db.add(Friendship(requester_id=owner_id, addressee_id=payload.friendOwnerId, status="pending"))
    db.commit()
    return {"status": "pending", "message": "好友申请已发送"}


@router.post("/friends/accept")
def friend_accept(payload: FriendRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    rel = db.scalar(
        select(Friendship).where(
            Friendship.requester_id == payload.friendOwnerId,
            Friendship.addressee_id == owner_id,
            Friendship.status == "pending",
        )
    )
    if not rel:
        raise HTTPException(status_code=404, detail="未找到待处理的好友申请")
    rel.status = "accepted"
    db.commit()
    return {"status": "accepted", "message": "已添加为好友"}


@router.get("/friends")
def list_friends(ownerId: str = Query(default=""), request: Request = None, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    rels = db.scalars(
        select(Friendship).where(
            Friendship.status == "accepted",
            (Friendship.requester_id == owner_id) | (Friendship.addressee_id == owner_id),
        )
    ).all()
    friends = [r.addressee_id if r.requester_id == owner_id else r.requester_id for r in rels]
    pending = db.scalars(
        select(Friendship).where(Friendship.addressee_id == owner_id, Friendship.status == "pending")
    ).all()
    return {"friends": friends, "pendingRequests": [p.requester_id for p in pending]}


@router.delete("/friends")
def remove_friend(payload: FriendRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    rel = db.scalar(
        select(Friendship).where(
            Friendship.status == "accepted",
            (Friendship.requester_id == owner_id) & (Friendship.addressee_id == payload.friendOwnerId)
            | (Friendship.requester_id == payload.friendOwnerId) & (Friendship.addressee_id == owner_id)
        )
    )
    if not rel:
        raise HTTPException(status_code=404, detail="好友关系不存在")
    db.delete(rel)
    db.commit()
    return {"message": "已删除好友关系"}
