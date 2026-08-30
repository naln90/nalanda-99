"""防诈智研 — 测评服务模块 (Phase 1.2)

提供基于 AssessmentSession 的完整会话生命周期管理：
- 种子填充 question_metadata
- 分层随机选题 (快速10题 / 标准20-25题)
- 逐题答题记录 + 部分得分
- 会话完成 + 五维能力画像计算

Phase 1 全部使用规则引擎评分，不依赖 AI。
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import (
    AbilityEvent,
    AbilitySnapshot,
    AssessmentAnswer,
    AssessmentResult,
    AssessmentSession,
    QuestionMetadata,
    User,
)
from app.question_bank import ALL_QUESTIONS
from app.ability_profile import normalize_dim_key


# ── 综合能力维度常量（主题无关，适用于所有参与主题的综合画像）──────────────
ABILITY_DIMENSIONS = ["辨识力", "判断力", "应变力", "实证力", "协作力"]

# 模式配置
MODE_CONFIG = {
    "quick": {
        "total_questions": 10,
        "per_dim": 2,       # 每维度至少 2 题
        "label": "10题快速测评",
        "description": "快速评估五大维度综合能力",
    },
    "standard": {
        "total_questions": 20,
        "per_dim": 4,       # 每维度至少 4 题
        "label": "20题标准测评",
        "description": "全面覆盖各类主题与风险阶段",
    },
}


# ── 种子填充 ──────────────────────────────────────────────────────
def seed_question_metadata(session: Session) -> int:
    """将题库数据填充到 question_metadata 表（幂等操作，且与代码题库保持同步）。

    同步策略：
    - 代码中已删除的题目（id 不在 ALL_QUESTIONS），从表中一并清除，
      避免「代码已移除、数据库残留」导致已下线主题（如「反诈安全」）的题目
      继续出现在测评中。
    - 代码中新增的题目，若表中缺失则插入。

    Returns:
        净变动的题目数量（删除记负、新增记正）
    """
    known_ids = {q["id"] for q in ALL_QUESTIONS}

    # 1) 清除代码中已下线的题目（孤儿行），保证数据库与代码一致
    orphan_count = 0
    for rec in session.query(QuestionMetadata).all():
        if rec.id not in known_ids:
            session.delete(rec)
            orphan_count += 1
    if orphan_count:
        session.flush()

    # 2) 新增缺失题目
    existing_ids = {q.id for q in session.query(QuestionMetadata).all()}
    new_count = 0
    for q in ALL_QUESTIONS:
        if q["id"] in existing_ids:
            continue
        record = QuestionMetadata(
            id=q["id"],
            question_type=q["question_type"],
            fraud_type=q["fraud_type"],
            ability_dim=normalize_dim_key(q["ability_dim"]),
            risk_stage=q["risk_stage"],
            stem=q["stem"],
            options_json=json.dumps(q["options"], ensure_ascii=False),
            correct_answer_json=json.dumps(q["correct_answer"], ensure_ascii=False),
            evidence_tags_json=json.dumps(q.get("evidence_tags", []), ensure_ascii=False),
            explanation=q["explanation"],
            difficulty=q.get("difficulty", "中等"),
            enabled=True,
            created_at=datetime.utcnow(),
        )
        session.add(record)
        new_count += 1

    if new_count or orphan_count:
        session.commit()
    return new_count - orphan_count


# ── 分层随机选题 ──────────────────────────────────────────────────
def select_questions(
    session: Session,
    mode: str,
    seed: int | None = None,
) -> list[QuestionMetadata]:
    """按维度分层随机抽取题目。

    策略：
    1. 先确保每个能力维度至少 N 题（quick=2, standard=4）
    2. 剩余名额从全部题库随机补充
    3. 每题不重复

    Args:
        session: DB session
        mode: "quick" 或 "standard"
        seed: 随机种子（可复现）

    Returns:
        选中的 QuestionMetadata 列表
    """
    config = MODE_CONFIG.get(mode, MODE_CONFIG["quick"])
    target_count = config["total_questions"]
    per_dim = config["per_dim"]

    rng = random.Random(seed)

    # 加载全部启用的题目
    all_qs = session.query(QuestionMetadata).filter(QuestionMetadata.enabled.is_(True)).all()
    if len(all_qs) < target_count:
        # 题库不足，返回全部
        return all_qs

    # 按维度分组
    dim_groups: dict[str, list[QuestionMetadata]] = {dim: [] for dim in ABILITY_DIMENSIONS}
    for q in all_qs:
        dim_groups.setdefault(q.ability_dim, []).append(q)

    selected: list[QuestionMetadata] = []
    selected_ids: set[str] = set()

    # 第一轮：每维度至少 per_dim 题
    for dim in ABILITY_DIMENSIONS:
        pool = [q for q in dim_groups.get(dim, []) if q.id not in selected_ids]
        rng.shuffle(pool)
        take = min(per_dim, len(pool))
        for q in pool[:take]:
            selected.append(q)
            selected_ids.add(q.id)

    # 第二轮：补充至目标数量
    if len(selected) < target_count:
        remaining = [q for q in all_qs if q.id not in selected_ids]
        rng.shuffle(remaining)
        need = target_count - len(selected)
        for q in remaining[:need]:
            selected.append(q)
            selected_ids.add(q.id)

    # 打乱顺序（避免同维度题目连续出现）
    rng.shuffle(selected)
    return selected[:target_count]


# ── 会话管理 ──────────────────────────────────────────────────────
def create_session(
    session: Session,
    owner_id: str,
    mode: str = "quick",
) -> tuple[AssessmentSession, list[QuestionMetadata]]:
    """创建测评会话并抽取题目。

    Returns:
        (AssessmentSession, 选中的题目列表)
    """
    config = MODE_CONFIG.get(mode, MODE_CONFIG["quick"])
    questions = select_questions(session, mode)

    sess = AssessmentSession(
        id=f"sess-{owner_id}-{int(datetime.utcnow().timestamp() * 1000)}",
        owner_id=owner_id,
        mode=mode,
        status="in_progress",
        total_questions=len(questions),
        completed_questions=0,
        started_at=datetime.utcnow(),
        completed_at=None,
    )
    session.add(sess)
    session.commit()

    return sess, questions


def record_answer(
    session: Session,
    sess: AssessmentSession,
    question: QuestionMetadata,
    user_answer: Any,
) -> AssessmentAnswer:
    """记录单题答题结果，计算正确性和得分。

    对于多选题，部分正确给部分得分（0.5），全对给1.0。
    """
    correct = json.loads(question.correct_answer_json)
    is_correct: bool
    score: float

    if question.question_type == "single":
        is_correct = _normalize_single(user_answer) == _normalize_single(correct)
        score = 1.0 if is_correct else 0.0
    else:
        # 多选题
        user_set = set(_normalize_multiple(user_answer))
        correct_set = set(_normalize_multiple(correct))
        if user_set == correct_set:
            is_correct = True
            score = 1.0
        elif user_set & correct_set:
            # 部分正确：有交集但非全对
            is_correct = False
            score = 0.5
        else:
            is_correct = False
            score = 0.0

    answer = AssessmentAnswer(
        session_id=sess.id,
        owner_id=sess.owner_id,
        question_id=question.id,
        user_answer=json.dumps(user_answer, ensure_ascii=False) if not isinstance(user_answer, str) else user_answer,
        is_correct=is_correct,
        score=score,
        fraud_type=question.fraud_type,
        ability_dim=normalize_dim_key(question.ability_dim),
        risk_stage=question.risk_stage,
        created_at=datetime.utcnow(),
    )
    session.add(answer)

    # 更新会话进度（不自动完成，由 finalize_session 显式完成）
    sess.completed_questions += 1
    session.commit()

    return answer


def finalize_session(
    session: Session,
    sess: AssessmentSession,
) -> dict[str, Any]:
    """完成测评会话，计算五维能力画像并保存结果。

    Returns:
        包含 accuracy, ability_profile, wrong_questions 等的结果字典
    """
    answers = (
        session.query(AssessmentAnswer)
        .filter(AssessmentAnswer.session_id == sess.id)
        .order_by(AssessmentAnswer.created_at)
        .all()
    )

    total = len(answers)
    correct_count = sum(1 for a in answers if a.is_correct)
    accuracy = correct_count / total if total > 0 else 0.0

    # 按维度统计
    dim_scores: dict[str, list[float]] = {dim: [] for dim in ABILITY_DIMENSIONS}
    wrong_questions: list[dict[str, Any]] = []

    for a in answers:
        dim_scores.setdefault(a.ability_dim, []).append(a.score)
        if not a.is_correct:
            wrong_questions.append({
                "question_id": a.question_id,
                "fraud_type": a.fraud_type,
                "ability_dim": a.ability_dim,
                "user_answer": a.user_answer,
            })

    # 五维能力画像（每维度满分100）
    ability_profile: dict[str, float] = {}
    for dim in ABILITY_DIMENSIONS:
        scores = dim_scores.get(dim, [])
        if scores:
            ability_profile[dim] = round(sum(scores) / len(scores) * 100, 1)
        else:
            ability_profile[dim] = 0.0

    # 弱势维度（< 60 分）
    weak_dimensions = [dim for dim, score in ability_profile.items() if score < 60]

    # 弱势诈骗类型
    fraud_types: dict[str, list[bool]] = {}
    for a in answers:
        fraud_types.setdefault(a.fraud_type, []).append(a.is_correct)
    weak_areas = [ft for ft, results in fraud_types.items() if not all(results)]

    # 写入 AssessmentResult（仅首次，幂等）
    existing = (
        session.query(AssessmentResult)
        .filter(AssessmentResult.owner_id == sess.owner_id)
        .order_by(desc(AssessmentResult.created_at))
        .first()
    )
    if existing is None or sess.status != "completed":
        result = AssessmentResult(
            owner_id=sess.owner_id,
            mode=sess.mode,
            total_questions=total,
            correct_count=correct_count,
            accuracy=accuracy,
            ability_profile_json=json.dumps(ability_profile, ensure_ascii=False),
            wrong_questions_json=json.dumps([wq["question_id"] for wq in wrong_questions], ensure_ascii=False),
            weak_dimensions_json=json.dumps(weak_dimensions, ensure_ascii=False),
            created_at=datetime.utcnow(),
        )
        session.add(result)
        session.flush()  # 确保 result.id 可用

        # ── 能力快照（Phase 1.3）──────────────────────────────────
        # 计算总分
        total_growth = int(sum(ability_profile.values()))

        # 获取上一次测评的能力分数（用于计算 delta）
        prev_snapshot = (
            session.query(AbilitySnapshot)
            .filter(AbilitySnapshot.owner_id == sess.owner_id)
            .order_by(desc(AbilitySnapshot.created_at))
            .first()
        )
        prev_scores: dict[str, float] = json.loads(prev_snapshot.scores_json) if prev_snapshot else {}

        snapshot = AbilitySnapshot(
            owner_id=sess.owner_id,
            scores_json=json.dumps(ability_profile, ensure_ascii=False),
            weak_dimensions_json=json.dumps(weak_dimensions, ensure_ascii=False),
            weak_types_json=json.dumps(weak_areas, ensure_ascii=False),
            total_growth=total_growth,
            trigger_event="assessment",
            trigger_ref=sess.id,
        )
        session.add(snapshot)
        session.flush()  # 确保 snapshot.id 可用

        # ── 能力变化事件（每维度 delta）─────────────────────────
        for dim in ABILITY_DIMENSIONS:
            score_before = prev_scores.get(dim, 0.0)
            score_after = ability_profile.get(dim, 0.0)
            delta_val = round(score_after - score_before, 1)
            event = AbilityEvent(
                snapshot_id=snapshot.id,
                owner_id=sess.owner_id,
                dim_key=dim,
                score_before=score_before,
                score_after=score_after,
                delta=delta_val,
            )
            session.add(event)

        # ── 精简旧快照（保留最近 30 个）─────────────────────────
        all_snapshots = (
            session.query(AbilitySnapshot)
            .filter(AbilitySnapshot.owner_id == sess.owner_id)
            .order_by(desc(AbilitySnapshot.created_at))
            .all()
        )
        if len(all_snapshots) > 30:
            to_delete = all_snapshots[30:]
            for old_snap in to_delete:
                # 先删除关联的 AbilityEvent
                session.query(AbilityEvent).filter(
                    AbilityEvent.snapshot_id == old_snap.id
                ).delete()
                session.delete(old_snap)

        # 更新用户状态（仅首次）
        user = session.query(User).filter(User.owner_id == sess.owner_id).first()
        if user:
            user.has_completed_assessment = True

    # 更新会话状态
    sess.status = "completed"
    sess.completed_at = datetime.utcnow()
    session.commit()

    return {
        "session_id": sess.id,
        "mode": sess.mode,
        "total_questions": total,
        "correct_count": correct_count,
        "accuracy": round(accuracy, 4),
        "ability_profile": ability_profile,
        "weak_dimensions": weak_dimensions,
        "weak_areas": weak_areas,
        "wrong_questions": wrong_questions,
    }


# ── 辅助函数 ──────────────────────────────────────────────────────
def _normalize_single(value: Any) -> str:
    """将单选题答案标准化为大写字母。"""
    if isinstance(value, str):
        v = value.strip().upper()
        # 取第一个字母（如果输入是 "A. xxx" 这样的格式）
        if v and v[0] in "ABCDEFGH":
            return v[0]
        return v
    if isinstance(value, list) and value:
        return _normalize_single(value[0])
    return str(value).strip().upper()


def _normalize_multiple(value: Any) -> list[str]:
    """将多选题答案标准化为字母列表。"""
    if isinstance(value, str):
        # 可能是 "ABC" 或 "A,B,C" 或 '["A","B"]'
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [_normalize_single(v) for v in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
        # 按逗号分割或逐字符提取
        parts = value.replace("，", ",").split(",")
        result = []
        for part in parts:
            part = part.strip().upper()
            if part and part[0] in "ABCDEFGH":
                result.append(part[0])
        return result
    if isinstance(value, list):
        return [_normalize_single(v) for v in value]
    return [_normalize_single(value)]
