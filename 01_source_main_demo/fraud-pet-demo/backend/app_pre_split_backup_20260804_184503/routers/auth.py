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


router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/demo-login")

def demo_login(payload: DemoLoginRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        user = get_or_create_user(db, payload.ownerId)
        # 签发并持久化令牌：demo 直登也纳入统一令牌体系，便于后续接口按 Token 绑定身份
        user.token = gen_token()
        db.commit()
        return {
            "currentUser": user_to_response(user),
            "hasCompletedAssessment": user.has_completed_assessment,
            "hasPet": user.has_pet,
            "token": user.token,
        }


@router.post("/register")

def auth_register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        username = payload.username.strip()
        if db.scalar(select(Account).where(Account.username == username)):
            raise HTTPException(status_code=409, detail="该账号名已被注册，请更换")
        owner_id = generate_owner_id(db)
        account = Account(
            username=username,
            password_hash=hash_password(payload.password),
            owner_id=owner_id,
            nickname=payload.nickname.strip() or username,
        )
        db.add(account)
        # 同步创建 User 记录，保证后续业务可直接通过 owner_id 取到用户状态
        user = User(owner_id=owner_id)
        user.token = gen_token()
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "currentUser": user_to_response(user),
            "hasCompletedAssessment": user.has_completed_assessment,
            "hasPet": user.has_pet,
            "nickname": account.nickname,
            "token": user.token,
        }


@router.post("/login")

def auth_login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        account = db.scalar(select(Account).where(Account.username == payload.username.strip()))
        if not account or not verify_password(payload.password, account.password_hash):
            raise HTTPException(status_code=401, detail="账号或密码错误")
        user = get_or_create_user(db, account.owner_id)
        # 每次登录轮换令牌，旧令牌自动失效
        user.token = gen_token()
        db.commit()
        return {
            "currentUser": user_to_response(user),
            "hasCompletedAssessment": user.has_completed_assessment,
            "hasPet": user.has_pet,
            "nickname": account.nickname,
            "token": user.token,
        }


