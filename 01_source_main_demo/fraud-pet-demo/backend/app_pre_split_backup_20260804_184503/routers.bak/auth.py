"""认证相关路由：demo 直登、注册、登录。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import gen_token
from ..database import get_db
from ..models import Account, User
from ..schemas import DemoLoginRequest, LoginRequest, RegisterRequest
from ..services import get_or_create_user, user_to_response

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
    owner_id = _generate_owner_id(db)
    account = Account(
        username=username,
        password_hash=_hash_password(payload.password),
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
    if not account or not _verify_password(payload.password, account.password_hash):
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


# 复用 services 中的密码哈希与 owner_id 生成逻辑
from ..services import generate_owner_id as _generate_owner_id  # noqa: E402
from ..services import hash_password as _hash_password  # noqa: E402
from ..services import verify_password as _verify_password  # noqa: E402
