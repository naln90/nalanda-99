"""集市互动：点赞、收藏、评分、评论（需求#26）。

挂在 /api/market 命名空间，与 /api/learning/market（集市列表）解耦，
仅以 listing_id 关联同一集市条目。评论会向条目作者推送通知。

鉴权：所有写操作均以 token 解析出的权威 owner 为准（get_current_owner），
杜绝客户端伪造 ownerId 冒充他人点赞/评分/评论。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/market", tags=["集市互动"])


class RateRequest(BaseModel):
    ownerId: str
    score: int  # 1-5


class CommentRequest(BaseModel):
    ownerId: str
    content: str = ""


def _listing_or_404(db: Session, listing_id: str) -> LearningMarketListing:
    listing = db.get(LearningMarketListing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="集市条目不存在")
    return listing


@router.post("/{listing_id}/like")
def toggle_like(
    listing_id: str,
    request: Request,
    ownerId: str = Query(default=""),
    db: Session = Depends(get_db),
) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    listing = _listing_or_404(db, listing_id)
    existing = db.scalar(
        select(MarketLike).where(MarketLike.listing_id == listing_id, MarketLike.owner_id == owner_id)
    )
    if existing:
        db.delete(existing)
        listing.likes = max(0, listing.likes - 1)
        liked = False
    else:
        db.add(MarketLike(listing_id=listing_id, owner_id=owner_id))
        listing.likes += 1
        liked = True
    db.commit()
    return {"likes": listing.likes, "liked": liked}


@router.post("/{listing_id}/favorite")
def toggle_favorite(
    listing_id: str,
    request: Request,
    ownerId: str = Query(default=""),
    db: Session = Depends(get_db),
) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    listing = _listing_or_404(db, listing_id)
    existing = db.scalar(
        select(MarketFavorite).where(MarketFavorite.listing_id == listing_id, MarketFavorite.owner_id == owner_id)
    )
    if existing:
        db.delete(existing)
        listing.favorites = max(0, listing.favorites - 1)
        favorited = False
    else:
        db.add(MarketFavorite(listing_id=listing_id, owner_id=owner_id))
        listing.favorites += 1
        favorited = True
    db.commit()
    return {"favorites": listing.favorites, "favorited": favorited}


@router.post("/{listing_id}/rate")
def rate_listing(listing_id: str, payload: RateRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    listing = _listing_or_404(db, listing_id)
    score = max(1, min(5, int(payload.score)))
    existing = db.scalar(
        select(MarketRating).where(MarketRating.listing_id == listing_id, MarketRating.owner_id == owner_id)
    )
    if existing:
        existing.score = score
    else:
        db.add(MarketRating(listing_id=listing_id, owner_id=owner_id, score=score))
    db.flush()
    ratings = db.scalars(select(MarketRating).where(MarketRating.listing_id == listing_id)).all()
    listing.rating_count = len(ratings)
    listing.rating_avg = round(sum(r.score for r in ratings) / len(ratings), 2) if ratings else 0.0
    db.commit()
    return {"ratingAvg": listing.rating_avg, "ratingCount": listing.rating_count, "myScore": score}


@router.get("/{listing_id}/comments")
def list_comments(listing_id: str, db: Session = Depends(get_db)) -> dict:
    comments = db.scalars(
        select(MarketComment)
        .where(MarketComment.listing_id == listing_id)
        .order_by(MarketComment.created_at.desc())
    ).all()
    return {
        "comments": [
            {"id": c.id, "ownerId": c.owner_id, "content": c.content, "createdAt": c.created_at.isoformat()}
            for c in comments
        ]
    }


@router.post("/{listing_id}/comments")
def add_comment(listing_id: str, payload: CommentRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    listing = _listing_or_404(db, listing_id)
    content = (payload.content or "").strip()
    if len(content) < 1:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    comment = MarketComment(listing_id=listing_id, owner_id=owner_id, content=content)
    db.add(comment)
    db.commit()
    if listing.owner_id and listing.owner_id != owner_id:
        push_notification(
            db,
            listing.owner_id,
            "market_comment",
            "你的集市条目收到新评论",
            f"《{listing.title}》收到一条新评论",
            ref_id=listing_id,
        )
        db.commit()
    return {
        "id": comment.id,
        "ownerId": comment.owner_id,
        "content": comment.content,
        "createdAt": comment.created_at.isoformat(),
    }
