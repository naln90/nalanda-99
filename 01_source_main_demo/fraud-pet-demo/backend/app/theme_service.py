"""月度主题与任务包服务 — V3.0 校方发布端核心。

流程（见方案§4、§5）：
校方输入月度学习主题 -> AI 校验并生成「基础必修 + 兴趣选修 + 成果任务」任务包草稿
-> 校方确认/增删 -> 发布为公开任务包 -> 学生进入主题任务包学习。

为兼顾演示稳定性，任务包生成采用「规则模板 + 可选 AI 增强」：LLM 不可用时回退到
确定性模板（参考方案附录 A），保证闭环始终可跑通。
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .energy_service import award_energy
from .models import LearningPlan, LearningPlanItem, Theme

_TX_BY_CATEGORY = {
    "required": "earn_task",
    "elective": "earn_elective",
    "outcome": "earn_outcome",
}


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6)}"


# 确定性任务包模板（参考方案附录 A，按主题名称做轻量参数化）
def _build_draft(theme: Theme) -> dict[str, Any]:
    title = theme.title or "学习主题"
    items: list[dict[str, Any]] = [
        # 基础必修
        {
            "key": "M1",
            "category": "required",
            "title": "主题导入微课",
            "description": f"了解「{title}」的核心概念、典型场景与学习目标。",
            "resourceHint": "校方资料 / 知识卡 / 安全提示视频",
            "acceptanceCriteria": "完成微课学习并通过基础检查",
            "estimatedMinutes": 10,
            "energyReward": 10,
            "dueDay": 1,
        },
        {
            "key": "M2",
            "category": "required",
            "title": "基础知识答题",
            "description": "完成基础选择题/判断题，检验核心知识点掌握情况。",
            "resourceHint": "题库自动组卷",
            "acceptanceCriteria": "完成不少于 8 题，正确率 ≥ 75%",
            "estimatedMinutes": 12,
            "energyReward": 20,
            "dueDay": 2,
        },
        {
            "key": "M3",
            "category": "required",
            "title": "关键要点辨析",
            "description": "从案例材料中辨析关键概念、常见误区与易混淆要点。",
            "resourceHint": "案例材料",
            "acceptanceCriteria": "标出规定数量的关键要点或常见误区",
            "estimatedMinutes": 15,
            "energyReward": 20,
            "dueDay": 3,
        },
        {
            "key": "M4",
            "category": "required",
            "title": "主题复盘",
            "description": "填写「我最需要巩固的三个要点」，形成自我提醒。",
            "resourceHint": "复盘模板",
            "acceptanceCriteria": "提交不少于 3 条要点复盘",
            "estimatedMinutes": 10,
            "energyReward": 15,
            "dueDay": 5,
        },
        {
            "key": "M5",
            "category": "outcome",
            "title": "基础成果创作",
            "description": f"制作一项可展示的学习成果：{theme.expected_outcome or '主题知识卡或成果海报'}。",
            "resourceHint": "创作工具 / 模板",
            "acceptanceCriteria": "提交成果并通过 AI 初审（完整性/准确性/贴合度）",
            "estimatedMinutes": 30,
            "energyReward": 40,
            "dueDay": 6,
        },
        # 兴趣选修
        {
            "key": "E1",
            "category": "elective",
            "title": "5 道情境判断题",
            "description": "完成情境判断并查看 AI 复盘。",
            "resourceHint": "情境题库",
            "acceptanceCriteria": "完成并查看 AI 复盘",
            "estimatedMinutes": 10,
            "energyReward": 15,
            "dueDay": 4,
        },
        {
            "key": "E2",
            "category": "elective",
            "title": "案例信息找茬",
            "description": "从案例材料中找出可疑或不合理的信息点。",
            "resourceHint": "案例样本",
            "acceptanceCriteria": "找出规定数量的可疑信息点",
            "estimatedMinutes": 10,
            "energyReward": 20,
            "dueDay": 4,
        },
        {
            "key": "E3",
            "category": "elective",
            "title": "AI 情景对话",
            "description": "在 AI 情景模拟对话中做出关键判断。",
            "resourceHint": "AI 情景模拟",
            "acceptanceCriteria": "完成关键节点判断",
            "estimatedMinutes": 15,
            "energyReward": 30,
            "dueDay": 5,
        },
        {
            "key": "E4",
            "category": "elective",
            "title": "主题知识竞赛",
            "description": "完成在线题组，巩固薄弱环节。",
            "resourceHint": "竞赛题组",
            "acceptanceCriteria": "完成在线题组",
            "estimatedMinutes": 15,
            "energyReward": 30,
            "dueDay": 6,
        },
        {
            "key": "E5",
            "category": "elective",
            "title": "成果升级优化",
            "description": "根据 AI 建议将知识卡升级为成果海报。",
            "resourceHint": "AI 初审建议",
            "acceptanceCriteria": "完成至少一次成果迭代",
            "estimatedMinutes": 20,
            "energyReward": 40,
            "dueDay": 7,
        },
    ]
    for i, it in enumerate(items):
        it["orderIndex"] = i + 1
    return {"items": items, "generated_by": "rule", "generated_at": datetime.utcnow().isoformat()}


def create_theme(db: Session, creator_id: str, payload: dict[str, Any]) -> Theme:
    theme = Theme(
        id=_gen_id("theme"),
        title=payload.get("title", "未命名主题"),
        description=payload.get("description", ""),
        period_days=int(payload.get("periodDays", 7)),
        target_audience=payload.get("targetAudience", "在校大学生"),
        scope=payload.get("scope", "全校"),
        base_required=payload.get("baseRequired", ""),
        elective_direction=payload.get("electiveDirection", ""),
        expected_outcome=payload.get("expectedOutcome", ""),
        base_assessment=payload.get("baseAssessment", ""),
        publish_time=payload.get("publishTime", ""),
        status="draft",
        creator_id=creator_id,
    )
    db.add(theme)
    db.commit()
    db.refresh(theme)
    return theme


def generate_theme_plan(db: Session, theme_id: str) -> Theme:
    theme = db.get(Theme, theme_id)
    if theme is None:
        raise ValueError("主题不存在")
    theme.status = "ai_generating"
    draft = _build_draft(theme)
    theme.ai_metadata_json = json.dumps(draft, ensure_ascii=False)
    theme.status = "pending_confirm"
    db.commit()
    db.refresh(theme)
    return theme


def confirm_theme(db: Session, theme_id: str, edits: dict[str, Any] | None = None) -> dict[str, Any]:
    """校方确认并发布任务包：用草稿（或校方修订）创建 LearningPlan 与条目。"""
    theme = db.get(Theme, theme_id)
    if theme is None:
        raise ValueError("主题不存在")
    meta = json.loads(theme.ai_metadata_json or "{}")
    items = (edits or {}).get("items") or meta.get("items") or _build_draft(theme)["items"]

    plan = LearningPlan(
        id=_gen_id("plan"),
        goal_id=theme.id,
        owner_id=theme.creator_id,
        title=f"{theme.title} · 任务包",
        summary=theme.description or "本月主题任务包（校方发布）",
        source="school-theme",
        status="published",
    )
    db.add(plan)
    db.flush()
    for it in items:
        db.add(
            LearningPlanItem(
                id=_gen_id("item"),
                plan_id=plan.id,
                owner_id=theme.creator_id,
                category=it.get("category", "required"),
                title=it.get("title", "未命名任务"),
                description=it.get("description", ""),
                resource_hint=it.get("resourceHint", ""),
                acceptance_criteria=it.get("acceptanceCriteria", ""),
                energy_reward=int(it.get("energyReward", 0)),
                estimated_minutes=int(it.get("estimatedMinutes", 20)),
                due_day=int(it.get("dueDay", 1)),
                order_index=int(it.get("orderIndex", 0)),
                status="not_started",
            )
        )
    theme.plan_id = plan.id
    theme.status = "published"
    theme.published_at = datetime.utcnow()
    db.commit()
    db.refresh(theme)
    return {"theme": theme, "plan": plan}


def get_active_theme(db: Session) -> Theme | None:
    return db.scalar(
        select(Theme)
        .where(Theme.status == "published")
        .order_by(Theme.published_at.desc().nullslast())
    )


def join_theme(db: Session, owner_id: str, theme_id: str) -> LearningPlan:
    """学生进入主题：将校方已发布的任务包克隆为个人任务包，复用既有完成逻辑。"""
    theme = db.get(Theme, theme_id)
    if theme is None or not theme.plan_id:
        raise ValueError("主题或任务包不存在")
    existing = db.scalar(
        select(LearningPlan).where(
            LearningPlan.owner_id == owner_id,
            LearningPlan.goal_id == theme.id,
            LearningPlan.source == "school-theme",
        )
    )
    if existing:
        return existing
    source = db.get(LearningPlan, theme.plan_id)
    source_items = list(
        db.scalars(
            select(LearningPlanItem).where(LearningPlanItem.plan_id == source.id).order_by(LearningPlanItem.order_index)
        ).all()
    )
    plan = LearningPlan(
        id=_gen_id("plan"),
        goal_id=theme.id,
        owner_id=owner_id,
        title=source.title,
        summary=source.summary,
        source="school-theme",
        status="active",
    )
    db.add(plan)
    db.flush()
    for idx, it in enumerate(source_items):
        db.add(
            LearningPlanItem(
                id=_gen_id("item"),
                plan_id=plan.id,
                owner_id=owner_id,
                category=it.category,
                title=it.title,
                description=it.description,
                resource_hint=it.resource_hint,
                acceptance_criteria=it.acceptance_criteria,
                energy_reward=it.energy_reward,
                estimated_minutes=it.estimated_minutes,
                due_day=it.due_day,
                order_index=it.order_index or idx + 1,
                status="not_started",
            )
        )
    db.commit()
    db.refresh(plan)
    return plan


def complete_theme_item(db: Session, owner_id: str, item_id: str) -> dict[str, Any]:
    """学生完成任务包条目：记录完成并发放对应盾能。"""
    item = db.get(LearningPlanItem, item_id)
    if item is None:
        raise ValueError("任务不存在")
    if item.owner_id != owner_id:
        raise ValueError("无权操作该任务")
    if item.status == "completed":
        from .energy_service import get_balances

        return {"alreadyDone": True, "balances": get_balances(db, owner_id)}
    item.status = "completed"
    item.completed_at = datetime.utcnow()
    db.commit()
    balances = None
    if item.energy_reward and item.energy_reward > 0:
        balances = award_energy(
            db,
            owner_id,
            item.energy_reward,
            _TX_BY_CATEGORY.get(item.category, "earn_task"),
            source_ref=item.id,
            note=f"完成任务【{item.title}】",
        )
    else:
        from .energy_service import get_balances

        balances = get_balances(db, owner_id)
    db.refresh(item)
    return {"item": item, "balances": balances}
