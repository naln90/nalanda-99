"""成果档案与隐私三级过滤（需求#32）。

- GET /api/artifacts：按 viewer 可见性（public / friends / private）过滤的成果列表。
- GET /api/artifacts/{id}：单条成果详情，越权返回 403。
复用 learning_market._serialize_artifact 保证与发布链路字段一致。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/artifacts", tags=["成果与隐私"])


@router.get("")
def list_artifacts(
    ownerId: str = Query(default=""),
    viewerId: str = Query(default=""),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(LearningArtifact).where(LearningArtifact.status != "draft")
    if ownerId:
        stmt = stmt.where(LearningArtifact.owner_id == ownerId)
    rows = db.scalars(stmt.order_by(LearningArtifact.created_at.desc())).all()
    viewer = viewerId or None
    visible = []
    for a in rows:
        if not can_view_resource(db, a.owner_id, a.visibility, viewer):
            continue
        visible.append(
            {
                "id": a.id,
                "ownerId": a.owner_id,
                "title": a.title,
                "artifactType": a.artifact_type,
                "visibility": a.visibility,
                "status": a.status,
                "createdAt": a.created_at.isoformat(),
            }
        )
    return {"artifacts": visible}


@router.get("/{artifact_id}")
def get_artifact(artifact_id: str, viewerId: str = Query(default=""), db: Session = Depends(get_db)) -> dict:
    a = db.get(LearningArtifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="成果不存在")
    if not can_view_resource(db, a.owner_id, a.visibility, viewerId or None):
        raise HTTPException(status_code=403, detail="无权查看该成果（隐私设置不允许）")
    from ..learning_market import _serialize_artifact

    return _serialize_artifact(db, a)
