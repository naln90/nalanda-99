"""业务辅助函数与共享数据（从原 ``main.py`` 提取的纯函数层）。

这些函数均为「接收 ``db`` 参数、无闭包依赖」的纯逻辑，供各业务路由复用。
不含任何 FastAPI 路由定义。
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from .models import (
    Account,
    GrowthRule,
    Pet,
    SuspiciousCheck,
    TrainingQuestion,
    TrainingRecord,
    TrainingTask,
    User,
)
from .rules import pet_level, pet_stage, same_day
from .question_bank import ALL_QUESTIONS

logger = logging.getLogger(__name__)

# 管理端可在后台调整的成长规则键；保存时强制要求为数值，避免脏数据
_NUMERIC_RULE_KEYS = {"dailyMaxGrowth", "taskMaxGrowth", "suspiciousCheckDailyLimit"}

# 测评题库：从 question_bank.py 导入全部 35 题，将 snake_case 键名转换为 camelCase
# 以兼容 API 返回格式和 compute_ability_profile 函数
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


def get_numeric_rule_keys() -> set[str]:
    return _NUMERIC_RULE_KEYS


def get_rule_value(session: Any, key: str, default: int) -> int:
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


def user_to_response(user: User) -> dict[str, object]:
    return {
        "ownerId": user.owner_id,
        "hasCompletedAssessment": user.has_completed_assessment,
        "hasPet": user.has_pet,
        "role": getattr(user, "role", "student"),
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


def generate_owner_id(session: Any) -> str:
    """生成形如 U-XXXX** 的匿名主人ID，后两位脱敏，保护隐私。"""
    for _ in range(20):
        candidate = f"U-{secrets.randbelow(9000) + 1000}**"
        if not session.scalar(select(Account).where(Account.owner_id == candidate)) and not session.scalar(
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


def get_or_create_user(session: Any, owner_id: str) -> User:
    user = session.scalar(select(User).where(User.owner_id == owner_id))
    if user:
        return user
    user = User(owner_id=owner_id)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_pet(session: Any, owner_id: str) -> Pet | None:
    return session.scalar(select(Pet).where(Pet.owner_id == owner_id))


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


def score_answers(session: Any, task_id: str, answers: list[Any]) -> float:
    questions = session.scalars(select(TrainingQuestion).where(TrainingQuestion.task_id == task_id)).all()
    if not questions:
        return 0.0
    provided = {answer.questionId: normalize_answer(answer.answer) for answer in answers}
    correct = 0
    for question in questions:
        correct_answer = normalize_answer(json.loads(question.correct_answer_json))
        if provided.get(question.id, set()) == correct_answer:
            correct += 1
    return correct / len(questions)


def awarded_training_today(session: Any, owner_id: str, task_id: str | None = None) -> list[TrainingRecord]:
    # 将「今日 + 指定任务」下推到 SQL，避免随着使用时间推移把历史获奖记录全部捞回再在内存过滤（性能 R2）
    filters = [
        TrainingRecord.owner_id == owner_id,
        TrainingRecord.reward_status == "AWARDED",
        func.date(TrainingRecord.created_at) == func.current_date(),
    ]
    if task_id is not None:
        filters.append(TrainingRecord.task_id == task_id)
    records = session.scalars(select(TrainingRecord).where(*filters)).all()
    # 用 same_day 兜底，确保与既有 UTC 口径完全一致（防止 DB 时区与 func.current_date 偏差）
    return [record for record in records if same_day(record.created_at)]


def daily_awarded_growth(session: Any, owner_id: str) -> int:
    training = session.scalar(
        select(func.coalesce(func.sum(TrainingRecord.final_growth), 0)).where(
            TrainingRecord.owner_id == owner_id,
            TrainingRecord.reward_status == "AWARDED",
            func.date(TrainingRecord.created_at) == func.current_date(),
        )
    )
    checks = session.scalar(
        select(func.coalesce(func.sum(SuspiciousCheck.growth_awarded), 0)).where(
            SuspiciousCheck.owner_id == owner_id,
            SuspiciousCheck.reward_status == "AWARDED",
            func.date(SuspiciousCheck.created_at) == func.current_date(),
        )
    )
    return int(training or 0) + int(checks or 0)
