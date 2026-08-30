"""个人中心消息通知（需求#29）。

列表、未读计数、单条已读、全部已读。其他模块通过 helpers.push_notification 写入。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/notifications", tags=["消息通知"])


class ReadRequest(BaseModel):
    ownerId: str


@router.get("")
def list_notifications(
    ownerId: str = Query(default=""),
    unreadOnly: bool = Query(default=False),
    request: Request = None,
    db: Session = Depends(get_db),
) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    stmt = select(Notification).where(Notification.owner_id == owner_id)
    if unreadOnly:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc())
    notes = db.scalars(stmt).all()
    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "content": n.content,
                "refId": n.ref_id,
                "isRead": n.is_read,
                "createdAt": n.created_at.isoformat(),
            }
            for n in notes
        ]
    }


@router.get("/unread-count")
def unread_count(
    ownerId: str = Query(default=""),
    request: Request = None,
    db: Session = Depends(get_db),
) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    cnt = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.owner_id == owner_id, Notification.is_read.is_(False)
        )
    )
    return {"unreadCount": cnt or 0}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, payload: ReadRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    note = db.get(Notification, notification_id)
    if not note or note.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="通知不存在")
    note.is_read = True
    db.commit()
    return {"message": "已标记为已读"}


@router.post("/read-all")
def mark_all_read(payload: ReadRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    notes = db.scalars(
        select(Notification).where(Notification.owner_id == owner_id, Notification.is_read.is_(False))
    ).all()
    for n in notes:
        n.is_read = True
    db.commit()
    return {"message": "已全部标记已读", "count": len(notes)}
