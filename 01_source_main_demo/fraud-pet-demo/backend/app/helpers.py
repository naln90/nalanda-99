"""原 main.py 的模块级辅助函数与常量（逐字迁移），供 routers/* 复用。"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import threading
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import *
from .rules import *
from .question_bank import ALL_QUESTIONS


logger = logging.getLogger(__name__)

_NUMERIC_RULE_KEYS = {"dailyMaxGrowth", "taskMaxGrowth", "suspiciousCheckDailyLimit"}


def get_rule_value(session: Session, key: str, default: int) -> int:
    """读取管理端配置的成长规则（GrowthRule）。

    让后台配置的成长值上限在训练结算、可疑信息判断等场景中真正生效；
    当规则缺失或取值无法解析为 int 时，安全回退到传入的默认值。
    """
    try:
        rule = session.scalar(select(GrowthRule).where(GrowthRule.rule_key == key))
        if rule is not None:
            return int(rule.rule_value)
    except (ValueError, TypeError):
        logger.warning("成长规则 %s 取值无法解析，回退默认值 %s", key, default)
    return default


def gen_token() -> str:
    """生成登录令牌。"""
    return secrets.token_urlsafe(24)


def resolve_owner_id(request: Request, db: Session, payload_owner_id: str) -> str:
    """软绑定身份：携带合法 Bearer Token 时以 Token 对应的 owner_id 为准，防止客户端伪造 ownerId；
    无 Token（demo 直登路径）则回退 payload.ownerId，保证演示链路不受影响。"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):].strip()
        if token:
            owner = db.scalar(select(User).where(User.token == token))
            if owner:
                return owner.owner_id
    return payload_owner_id


# 正式环境可设为 true：强制要求合法 Bearer Token，否则拒绝请求（替换软身份）。
# 运行时动态读取，便于按环境/测试切换。


def _auth_required() -> bool:
    return os.getenv("AUTH_REQUIRED", "false").lower() in ("1", "true", "yes", "on")


def get_current_owner(
    request: Request,
    db: Session,
    owner_id: str | None = None,
) -> str:
    """统一身份解析依赖（需求：安全与鉴权）。

    - 携带合法 Bearer Token：以 Token 对应的 owner_id 为准（防伪造）。
    - 未携带 Token：
        * 若 AUTH_REQUIRED=true → 401（生产强制鉴权）；
        * 否则回退到调用方传入的 owner_id（演示态兼容）。
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):].strip()
        if token:
            owner = db.scalar(select(User).where(User.token == token))
            if owner:
                return owner.owner_id
            # 提供了 token 但无效：无论是否强制都拒绝，避免凭空 ownerId。
            raise HTTPException(status_code=401, detail="登录令牌无效或已失效，请重新登录")
    if _auth_required():
        raise HTTPException(status_code=401, detail="请先登录后再操作（服务端已开启强制鉴权）")
    if not owner_id:
        raise HTTPException(status_code=400, detail="缺少身份标识 ownerId")
    return owner_id


_ADMIN_KEY_WARNED = False


def require_admin_key(request: Request) -> None:
    """保护 /api/admin 管理端点。

    配置环境变量 ADMIN_API_KEY 后强制校验 X-Admin-Key 头；未配置时 fail-open 放行
    （仅告警一次），以保证未部署密钥的演示环境仍可正常演示。
    """
    global _ADMIN_KEY_WARNED
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        if not _ADMIN_KEY_WARNED:
            logger.warning("ADMIN_API_KEY 未配置，/api/admin 端点当前未受保护（演示态放行）")
            _ADMIN_KEY_WARNED = True
        return
    provided = request.headers.get("X-Admin-Key", "")
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="未授权的管理端访问")


_KEY_MAP = {
    "question_type": "questionType",
    "fraud_type": "fraudType",
    "ability_dim": "abilityDim",
    "risk_stage": "riskStage",
    "evidence_tags": "evidenceTags",
    "correct_answer": "correctAnswer",
}


ASSESSMENT_QUESTIONS = [
    {_KEY_MAP.get(k, k): v for k, v in q.items()} for q in ALL_QUESTIONS
]


_award_lock = threading.Lock()


def user_to_response(user: User) -> dict[str, object]:
    return {
        "ownerId": user.owner_id,
        "hasCompletedAssessment": user.has_completed_assessment,
        "hasPet": user.has_pet,
        "role": getattr(user, "role", "student"),
        "studentId": getattr(user, "student_id", None),
        "school": getattr(user, "school", None),
        "department": getattr(user, "department", None),
    }


def hash_password(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(8)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    return hash_password(password, salt) == stored


def generate_owner_id(db: Session) -> str:
    """生成形如 U-XXXX** 的匿名主人ID，后两位脱敏，保护隐私。"""
    for _ in range(20):
        candidate = f"U-{secrets.randbelow(9000) + 1000}**"
        if not db.scalar(select(Account).where(Account.owner_id == candidate)) and not db.scalar(
            select(User).where(User.owner_id == candidate)
        ):
            return candidate
    # 极端情况下用时间戳兜底
    return f"U-{int(datetime.utcnow().timestamp()) % 10000}**"


def task_to_response(task: TrainingTask) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "fraudType": task.fraud_type,
        "riskLevel": task.risk_level,
        "difficulty": task.difficulty,
        "duration": f"{task.duration_minutes} 分钟",
        "reward": task.max_reward,
    }


def get_or_create_user(db: Session, owner_id: str) -> User:
    user = db.scalar(select(User).where(User.owner_id == owner_id))
    if user:
        return user
    user = User(owner_id=owner_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def are_friends(db: Session, a: str, b: str) -> bool:
    """判断两用户是否为已接受的好友关系（用于「仅好友」可见）。"""
    if not a or not b or a == b:
        return False
    return (
        db.scalar(
            select(Friendship).where(
                Friendship.status == "accepted",
                (
                    (Friendship.requester_id == a) & (Friendship.addressee_id == b)
                    | (Friendship.requester_id == b) & (Friendship.addressee_id == a)
                ),
            )
        )
        is not None
    )


def can_view_resource(db: Session, owner_id: str, visibility: str, viewer_id: str | None) -> bool:
    """隐私三级过滤（需求#32）：public 公开；friends 仅好友；private 仅自己。"""
    if visibility == "public":
        return True
    if viewer_id is None or viewer_id == owner_id:
        return viewer_id == owner_id
    if visibility == "friends":
        return are_friends(db, owner_id, viewer_id)
    return False


def push_notification(
    db: Session,
    owner_id: str,
    ntype: str,
    title: str,
    content: str,
    ref_id: str | None = None,
) -> None:
    """写入一条个人通知（需求#29）。"""
    db.add(
        Notification(
            owner_id=owner_id,
            type=ntype,
            title=title,
            content=content,
            ref_id=ref_id,
        )
    )


def get_pet(db: Session, owner_id: str) -> Pet | None:
    return db.scalar(select(Pet).where(Pet.owner_id == owner_id))


def apply_growth(pet: Pet, growth: int) -> None:
    if growth <= 0:
        return
    pet.growth_value += growth
    pet.level = pet_level(pet.growth_value)
    pet.stage = pet_stage(pet.level)
    pet.last_training_at = datetime.utcnow()


def normalize_answer(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item) for item in value}
    if value is None:
        return set()
    return {str(value)}


def score_answers(db: Session, task_id: str, answers: list[TrainingAnswer]) -> float:
    questions = db.scalars(select(TrainingQuestion).where(TrainingQuestion.task_id == task_id)).all()
    if not questions:
        return 0.0
    provided = {answer.questionId: normalize_answer(answer.answer) for answer in answers}
    correct = 0
    for question in questions:
        correct_answer = normalize_answer(json.loads(question.correct_answer_json))
        if provided.get(question.id, set()) == correct_answer:
            correct += 1
    return correct / len(questions)


def awarded_training_today(db: Session, owner_id: str, task_id: str | None = None) -> list[TrainingRecord]:
    # 将「今日 + 指定任务」下推到 SQL，避免随着使用时间推移把历史获奖记录全部捞回再在内存过滤（性能 R2）
    filters = [
        TrainingRecord.owner_id == owner_id,
        TrainingRecord.reward_status == "AWARDED",
        func.date(TrainingRecord.created_at) == func.current_date(),
    ]
    if task_id is not None:
        filters.append(TrainingRecord.task_id == task_id)
    records = db.scalars(select(TrainingRecord).where(*filters)).all()
    # 用 same_day 兜底，确保与既有 UTC 口径完全一致（防止 DB 时区与 func.current_date 偏差）
    return [record for record in records if same_day(record.created_at)]


def daily_awarded_growth(db: Session, owner_id: str) -> int:
    training = db.scalar(
        select(func.coalesce(func.sum(TrainingRecord.final_growth), 0)).where(
            TrainingRecord.owner_id == owner_id,
            TrainingRecord.reward_status == "AWARDED",
            func.date(TrainingRecord.created_at) == func.current_date(),
        )
    )
    checks = db.scalar(
        select(func.coalesce(func.sum(SuspiciousCheck.growth_awarded), 0)).where(
            SuspiciousCheck.owner_id == owner_id,
            SuspiciousCheck.reward_status == "AWARDED",
            func.date(SuspiciousCheck.created_at) == func.current_date(),
        )
    )
    return int(training or 0) + int(checks or 0)
