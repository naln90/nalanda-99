"""排行榜路由（/api/ranking）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Pet

router = APIRouter(prefix="/api", tags=["ranking"])


@router.get("/ranking")
def ranking(
    type: str = Query("total"),
    ownerId: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    pets = db.scalars(
        select(Pet).order_by(Pet.growth_value.desc(), Pet.level.desc(), Pet.last_training_at.desc())
    ).all()
    rows = [
        {
            "rank": idx + 1,
            "petId": pet.pet_id,
            "ownerId": pet.owner_id,
            "petType": pet.pet_type,
            "level": pet.level,
            "growthValue": pet.growth_value,
            "lastTrainingAt": pet.last_training_at.strftime("%Y-%m-%d %H:%M") if pet.last_training_at else "",
        }
        for idx, pet in enumerate(pets)
    ]
    target_owner = ownerId or "U-2408**"
    my_rank = next((row for row in rows if row["ownerId"] == target_owner), None)
    if my_rank:
        previous = next((row for row in rows if row["rank"] == my_rank["rank"] - 1), None)
        my_rank = {
            **my_rank,
            "distanceToPrevious": max(0, int(previous["growthValue"]) - int(my_rank["growthValue"])) if previous else 0,
        }
    return {
        "type": type,
        "myRank": my_rank,
        "list": rows,
        "sortRule": ["growth_value DESC", "level DESC", "last_training_at DESC"],
        "privacyNotice": "不展示真实姓名、手机号、学号、身份证号和负面评价标签。",
    }
