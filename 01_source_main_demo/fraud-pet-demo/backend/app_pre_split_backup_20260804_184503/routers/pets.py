from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import threading
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import create_engine, desc, func, inspect, select, text
from sqlalchemy.orm import Session

from ..database import get_db, get_submit_lock
from ..models import *
from ..schemas import *
from ..rules import *
from ..helpers import *
from ..seed import pet_to_response, seed_database
from ..ai_service import AIService, is_llm_available, MODEL_NAME
from ..assessment_service import *
from ..image_analysis import analyze_image
from ..question_bank import ALL_QUESTIONS
from ..risk_test_samples import seed_risk_test_samples
from ..scenarios import scenario_response
from ..ability_profile import *
from ..retrain_scheduler import *
from ..task_planner import *
from ..scenario_state_machine import *
from ..review_engine import *
from ..emergency_stop_loss import *
from ..ai_logger import *


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/pets", tags=["pets"])

@router.get("/pool")

def pets_pool(db: Session = Depends(get_db)) -> dict[str, object]:
        pets = db.scalars(select(PetPool).where(PetPool.enabled.is_(True)).order_by(PetPool.id)).all()
        return {
            "pets": [
                {
                    "name": pet.pet_type,
                    "category": pet.pet_category,
                    "desc": pet.description,
                }
                for pet in pets
            ]
        }


@router.post("/claim")

def claim_pet(payload: PetClaimRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        user = get_or_create_user(db, payload.ownerId)
        pool_pet = db.scalar(select(PetPool).where(PetPool.pet_type == payload.petType, PetPool.enabled.is_(True)))
        if not pool_pet:
            raise HTTPException(status_code=404, detail="Pet type not found")
        pet = get_pet(db, payload.ownerId)
        if not pet:
            next_id = int(db.scalar(select(func.count(Pet.id))) or 0) + 8294
            pet = Pet(
                pet_id=f"PET-{next_id}",
                owner_id=payload.ownerId,
                pet_type=pool_pet.pet_type,
                pet_category=pool_pet.pet_category,
                pet_name=payload.petName or None,
                avatar_emoji=payload.avatarEmoji or None,
                level=1,
                stage="幼崽期",
                growth_value=30,
                last_training_at=datetime.utcnow(),
            )
            db.add(pet)
        else:
            # 已有宠物：若请求中携带昵称/头像，则同步更新
            if payload.petName is not None:
                pet.pet_name = payload.petName or None
            if payload.avatarEmoji is not None:
                pet.avatar_emoji = payload.avatarEmoji or None
        user.has_pet = True
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pet)
        return {"pet": pet_to_response(pet), "currentUser": user_to_response(user)}


@router.patch("/profile")

def update_pet_profile(payload: PetProfileUpdateRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """更新宠物的自定义昵称与头像 emoji。"""
        pet = get_pet(db, payload.ownerId)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        if payload.petName is not None:
            trimmed = payload.petName.strip()
            pet.pet_name = trimmed or None
        if payload.avatarEmoji is not None:
            trimmed_emoji = payload.avatarEmoji.strip()
            pet.avatar_emoji = trimmed_emoji or None
        db.commit()
        db.refresh(pet)
        return {"pet": pet_to_response(pet)}


@router.get("/my")

def my_pet(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
        pet = get_pet(db, ownerId)
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        return {"pet": pet_to_response(pet)}


@router.get("/stages")

def pet_stages() -> dict[str, object]:
        return {
            "stages": [
                {"name": "幼崽期", "levelRange": "Lv.1-Lv.3", "appearance": "基础可爱形态"},
                {"name": "学习期", "levelRange": "Lv.4-Lv.7", "appearance": "增加书包、徽章、提示牌等学习元素"},
                {"name": "成长期", "levelRange": "Lv.8-Lv.12", "appearance": "增加护盾、警示灯、识别器等反诈元素"},
                {"name": "进阶期", "levelRange": "Lv.13-Lv.16", "appearance": "增加更明显的守护装备"},
                {"name": "反诈守护者", "levelRange": "Lv.17-Lv.20", "appearance": "完整守护形态"},
            ]
        }


