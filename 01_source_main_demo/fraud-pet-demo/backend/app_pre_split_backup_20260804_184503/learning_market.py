"""AI 学习集市主链路。

该模块把现有反诈训练能力包装为可扩展的学习产品：
学习目标发布 -> 可编辑任务包 -> 过程记录 -> 成果迭代 -> 集市共享
-> 小盾灵成长与校园实践活动解锁。

校园实践活动仅由平台展示解锁资格与团委通知，不承担报名、组织、
签到或志愿时长认定。
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    CampusActivity,
    CampusActivityUnlock,
    LearningArtifact,
    LearningArtifactVersion,
    LearningGoal,
    LearningMarketListing,
    LearningPlan,
    LearningPlanItem,
)


ACTIVITY_BOUNDARY_NOTICE = (
    "活动解锁仅代表获得活动认知、成长荣誉或参与资格，不等同于报名或实际参加。"
    "具体活动由学校团委统一组织；学生可按团委规定程序自主报名，也可仅保留解锁记录。"
)


TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "tpl-fraud-campus",
        "title": "14天大学生反诈主题学习包",
        "theme": "大学生校园反诈",
        "difficulty": "进阶",
        "periodDays": 14,
        "dailyMinutes": 20,
        "expectedOutcome": "完成一张大学生兼职诈骗防范海报",
        "summary": "以校园高发诈骗为主题，包含基础必修、兴趣选修、情境训练与成果创作。",
        "tags": ["反诈", "主题学习", "海报创作"],
        "electiveTracks": ["情境挑战", "案例研判", "创意表达"],
        "reuseCount": 126,
        "featured": True,
    },
    {
        "id": "tpl-python-starter",
        "title": "21天Python入门任务包",
        "theme": "Python编程入门",
        "difficulty": "入门",
        "periodDays": 21,
        "dailyMinutes": 35,
        "expectedOutcome": "完成一个可运行的校园信息查询小程序",
        "summary": "从语法基础、函数与数据结构逐步过渡到一个可演示的小项目。",
        "tags": ["Python", "编程", "项目学习"],
        "electiveTracks": ["代码实践", "项目挑战"],
        "reuseCount": 89,
        "featured": False,
    },
    {
        "id": "tpl-calculus-review",
        "title": "高数期末复习冲刺包",
        "theme": "高等数学复习",
        "difficulty": "进阶",
        "periodDays": 10,
        "dailyMinutes": 45,
        "expectedOutcome": "形成一份个人薄弱知识点复习手册",
        "summary": "按知识诊断、专项训练、错题复盘和模拟测验组织复习路径。",
        "tags": ["高数", "考试", "错题复盘"],
        "electiveTracks": ["错题专项", "模拟测验"],
        "reuseCount": 64,
        "featured": False,
    },
    {
        "id": "tpl-innovation-project",
        "title": "大学生创新项目启动包",
        "theme": "大学生创新项目",
        "difficulty": "挑战",
        "periodDays": 30,
        "dailyMinutes": 40,
        "expectedOutcome": "完成项目需求说明、原型与路演材料",
        "summary": "覆盖问题定义、用户调研、方案设计、原型验证和成果路演。",
        "tags": ["大创", "项目学习", "成果路演"],
        "electiveTracks": ["用户调研", "原型设计", "路演表达"],
        "reuseCount": 51,
        "featured": False,
    },
]


ACTIVITY_SEEDS: list[dict[str, Any]] = [
    {
        "id": "activity-tree-planting",
        "title": "校园公益植树活动",
        "category": "校园公益",
        "description": "以持续完成主题学习为基础，发现并解锁校园公益实践机会。",
        "interest_direction": "综合参与",
        "targetEnergy": 1000,
        "rule": {"required": 2, "electives": 1, "artifacts": 1},
    },
    {
        "id": "activity-community-fraud",
        "title": "社区反诈宣传实践",
        "category": "志愿传播",
        "description": "面向社区居民开展防诈知识传播，适合案例研判和表达方向学习者。",
        "interest_direction": "志愿传播",
        "targetEnergy": 1500,
        "rule": {"required": 3, "electives": 2, "artifacts": 1},
    },
    {
        "id": "activity-elderly-digital",
        "title": "老年人数字安全指导",
        "category": "数字助老",
        "description": "帮助老年人识别养老、投资及远程控制等常见数字风险。",
        "interest_direction": "数字助老",
        "targetEnergy": 1200,
        "rule": {"required": 2, "electives": 2, "artifacts": 1},
    },
    {
        "id": "activity-fraud-exhibition",
        "title": "校园反诈作品展",
        "category": "成果展示",
        "description": "展示学生创作的海报、短视频、案例报告等优秀主题学习成果。",
        "interest_direction": "内容创作",
        "targetEnergy": 800,
        "rule": {"required": 2, "electives": 1, "artifacts": 1},
    },
]


class GoalValidationRequest(BaseModel):
    theme: str = Field(min_length=2, max_length=120)
    periodDays: int = Field(default=14, ge=3, le=180)
    dailyMinutes: int = Field(default=20, ge=10, le=240)
    difficulty: str = "进阶"
    expectedOutcome: str = Field(min_length=2, max_length=180)


class GoalCreateRequest(GoalValidationRequest):
    ownerId: str = Field(min_length=1)
    learningType: str = Field(default="自主学习", max_length=40)
    majorDirection: str = Field(default="通识能力", max_length=40)
    electiveTracks: list[str] = Field(default_factory=list, max_length=20)


class PlanItemUpdateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    estimatedMinutes: int | None = Field(default=None, ge=5, le=240)
    dueDay: int | None = Field(default=None, ge=1, le=180)
    status: str | None = None
    completionNote: str | None = Field(default=None, max_length=500)


class PlanItemCompleteRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    completionNote: str = Field(default="", max_length=500)


class PlanItemReplaceRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    direction: str = Field(default="AI对练", max_length=40)


class ArtifactCreateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    planId: str = Field(min_length=1)
    title: str = Field(min_length=2, max_length=120)
    artifactType: str = Field(default="海报", max_length=40)
    description: str = Field(default="", max_length=800)
    visibility: str = "private"


class ArtifactVersionRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    fileName: str = Field(default="", max_length=200)
    contentSummary: str = Field(min_length=8, max_length=3000)
    revisionNote: str = Field(default="", max_length=1000)


class ArtifactPublishRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    visibility: str = "public"


class PlanShareRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class MarketReuseRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class CompanionRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    planId: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=1000)


def _json_load(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.randbelow(9000) + 1000}"


def _validate_goal(payload: GoalValidationRequest) -> dict[str, Any]:
    suggestions: list[str] = []
    score = 100
    if len(payload.theme.strip()) < 6:
        suggestions.append("建议将主题写得更具体，例如明确学习对象、应用场景或能力方向。")
        score -= 15
    if payload.periodDays <= 5 and payload.dailyMinutes < 30:
        suggestions.append("当前周期较短，可增加每日学习时长或缩小预期成果范围。")
        score -= 12
    if len(payload.expectedOutcome.strip()) < 8:
        suggestions.append("建议把预期成果改为可提交、可展示的具体作品。")
        score -= 15
    if not any(word in payload.expectedOutcome for word in ("完成", "制作", "形成", "通过", "掌握", "产出")):
        suggestions.append("可使用“完成/制作/形成/通过”等动词描述可验收成果。")
        score -= 8
    if not suggestions:
        suggestions.append("目标范围、周期与成果相互匹配，可以直接生成任务包。")
    return {
        "score": max(score, 45),
        "isExecutable": score >= 70,
        "normalizedGoal": (
            f"在{payload.periodDays}天内围绕“{payload.theme.strip()}”开展"
            f"{payload.difficulty}学习，每天投入约{payload.dailyMinutes}分钟，"
            f"最终{payload.expectedOutcome.strip()}。"
        ),
        "suggestions": suggestions,
        "source": "explainable-ai",
    }


def _ensure_activity_seeds(db: Session) -> None:
    for seed in ACTIVITY_SEEDS:
        existing = db.get(CampusActivity, seed["id"])
        if existing is None:
            db.add(
                CampusActivity(
                    id=seed["id"],
                    title=seed["title"],
                    category=seed["category"],
                    description=seed["description"],
                    organizer="学校团委",
                    interest_direction=seed["interest_direction"],
                    notice_url="",
                    unlock_rule_json=json.dumps(seed["rule"], ensure_ascii=False),
                    target_energy=seed["targetEnergy"],
                    current_progress=0,
                    contributor_count=0,
                    status="building",
                )
            )
        else:
            # 向后兼容：旧库 seed 行可能缺少共建字段（迁移加列时为 NULL），在此补齐。
            changed = False
            if existing.target_energy is None:
                existing.target_energy = seed.get("targetEnergy", 1000)
                changed = True
            if existing.current_progress is None:
                existing.current_progress = 0
                changed = True
            if existing.contributor_count is None:
                existing.contributor_count = 0
                changed = True
            if existing.status is None:
                existing.status = "building"
                changed = True
            if changed:
                db.add(existing)
    db.commit()


def _fraud_items(goal: LearningGoal) -> list[dict[str, Any]]:
    selected = _json_load(goal.elective_tracks_json, [])
    if not selected:
        selected = ["情境挑战", "案例研判", "创意表达"]
    elective_library = {
        "情境挑战": (
            "兼职刷单诈骗情境识别挑战",
            "在模拟聊天中找出先垫付、返利承诺、脱离正规平台等高危信号。",
            "训练中心 · AI情境模拟",
            "识别至少3个风险信号并说明正确处置方式。",
        ),
        "案例研判": (
            "冒充客服退款案例研判",
            "拆解冒充客服、屏幕共享和虚假退款链接的完整诈骗链。",
            "案例库 · 冒充客服专题",
            "完成风险节点标注并写出核验路径。",
        ),
        "AI对练": (
            "小盾灵诈骗话术对练",
            "与小盾灵进行多轮问答，练习核验身份、拒绝转账和求助表达。",
            "小盾灵 · 学习陪伴",
            "完成一次对练并形成三条个人应对原则。",
        ),
        "创意表达": (
            "反诈成果创意与素材整理",
            "围绕目标受众筛选诈骗案例、视觉重点和行动提示。",
            "反诈知识库 · 创作素材",
            "形成成果提纲、核心文案和素材清单。",
        ),
        "老年防诈": (
            "老年人常见诈骗专题学习",
            "学习养老投资、冒充亲友和远程控制等数字安全风险。",
            "反诈知识库 · 数字助老",
            "完成专题学习并能用通俗语言解释风险。",
        ),
    }
    items: list[dict[str, Any]] = [
        {
            "category": "required",
            "title": "反诈主题班会导学",
            "description": "完成学校统一安排的主题班会内容，建立本阶段学习框架。",
            "resource": "主题学习 · 班会材料",
            "criteria": "完成主题要点阅读与3题导学检查。",
            "minutes": 20,
            "day": 1,
        },
        {
            "category": "required",
            "title": "校园高发诈骗基础课",
            "description": "学习兼职刷单、冒充客服、游戏交易和AI换脸等校园高发风险。",
            "resource": "反诈知识库 · 校园高发专题",
            "criteria": "完成基础课程并记录至少4类高危信号。",
            "minutes": 25,
            "day": 2,
        },
        {
            "category": "required",
            "title": "个人防诈能力基线测评",
            "description": "从识诈、判断、应对、证据和求助五个维度形成初始画像。",
            "resource": "训练中心 · 五维能力测评",
            "criteria": "完成测评并查看个人薄弱方向。",
            "minutes": 15,
            "day": 3,
        },
    ]
    for index, track in enumerate(selected[:3]):
        title, description, resource, criteria = elective_library.get(
            track,
            (
                f"{track}主题探索",
                f"围绕{track}开展一次自主选择的主题学习。",
                "学习资源库 · 兴趣专题",
                "完成学习并提交一段个人复盘。",
            ),
        )
        items.append(
            {
                "category": "elective",
                "title": title,
                "description": description,
                "resource": resource,
                "criteria": criteria,
                "minutes": min(max(goal.daily_minutes, 15), 45),
                "day": min(goal.period_days - 2, 5 + index * 2),
            }
        )
    items.append(
        {
            "category": "outcome",
            "title": goal.expected_outcome,
            "description": "将前期学习内容转化为可提交、可迭代、可公开展示的学习成果。",
            "resource": "成果工坊 · AI初审",
            "criteria": "至少提交两个版本，依据AI建议完成一次修改后发布。",
            "minutes": max(goal.daily_minutes * 2, 40),
            "day": goal.period_days,
        }
    )
    return items


def _generic_items(goal: LearningGoal) -> list[dict[str, Any]]:
    selected = _json_load(goal.elective_tracks_json, []) or ["知识梳理", "实操练习", "成果表达"]
    items = [
        {
            "category": "required",
            "title": f"{goal.theme}学习地图",
            "description": "梳理核心概念、先后依赖关系和阶段目标。",
            "resource": "AI生成知识大纲",
            "criteria": "确认知识地图并标注个人已有基础。",
            "minutes": goal.daily_minutes,
            "day": 1,
        },
        {
            "category": "required",
            "title": f"{goal.theme}基础能力诊断",
            "description": "通过基础问题或样例任务识别当前薄弱点。",
            "resource": "主题诊断材料",
            "criteria": "完成诊断并确认至少一个强化方向。",
            "minutes": goal.daily_minutes,
            "day": 2,
        },
    ]
    for index, track in enumerate(selected[:3]):
        items.append(
            {
                "category": "elective",
                "title": f"{track}：{goal.theme}",
                "description": f"根据个人兴趣选择“{track}”方向开展专项学习。",
                "resource": "AI推荐资源清单",
                "criteria": "完成一次专项实践并记录关键收获。",
                "minutes": goal.daily_minutes,
                "day": min(goal.period_days - 1, 4 + index * 2),
            }
        )
    items.append(
        {
            "category": "outcome",
            "title": goal.expected_outcome,
            "description": "提交最终学习成果，并依据AI初审建议完成至少一次迭代。",
            "resource": "成果工坊",
            "criteria": "成果完整、贴合学习目标并保留版本记录。",
            "minutes": max(goal.daily_minutes * 2, 40),
            "day": goal.period_days,
        }
    )
    return items


def _create_plan(db: Session, goal: LearningGoal) -> LearningPlan:
    previous = db.scalars(
        select(LearningPlan).where(
            LearningPlan.owner_id == goal.owner_id,
            LearningPlan.status == "active",
        )
    ).all()
    for plan in previous:
        plan.status = "paused"

    plan = LearningPlan(
        id=_new_id("lplan"),
        goal_id=goal.id,
        owner_id=goal.owner_id,
        title=f"{goal.theme} · {goal.period_days}天个性化任务包",
        summary=(
            f"每天约{goal.daily_minutes}分钟，以基础必修保证学习底线，"
            f"以兴趣选修形成个性路径，最终{goal.expected_outcome}。"
        ),
        source="explainable-ai",
    )
    db.add(plan)
    db.flush()

    is_fraud = any(word in goal.theme for word in ("反诈", "诈骗", "防骗", "数字安全"))
    item_specs = _fraud_items(goal) if is_fraud else _generic_items(goal)
    for index, spec in enumerate(item_specs):
        db.add(
            LearningPlanItem(
                id=_new_id(f"litem{index + 1}"),
                plan_id=plan.id,
                owner_id=goal.owner_id,
                category=spec["category"],
                title=spec["title"],
                description=spec["description"],
                resource_hint=spec["resource"],
                acceptance_criteria=spec["criteria"],
                estimated_minutes=spec["minutes"],
                due_day=max(1, spec["day"]),
                order_index=index,
            )
        )
    db.flush()
    return plan


def _serialize_goal(goal: LearningGoal) -> dict[str, Any]:
    return {
        "id": goal.id,
        "ownerId": goal.owner_id,
        "theme": goal.theme,
        "learningType": goal.learning_type,
        "periodDays": goal.period_days,
        "dailyMinutes": goal.daily_minutes,
        "difficulty": goal.difficulty,
        "expectedOutcome": goal.expected_outcome,
        "majorDirection": goal.major_direction,
        "electiveTracks": _json_load(goal.elective_tracks_json, []),
        "validation": _json_load(goal.validation_json, {}),
        "status": goal.status,
        "createdAt": goal.created_at.isoformat(),
    }


def _serialize_item(item: LearningPlanItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "planId": item.plan_id,
        "category": item.category,
        "title": item.title,
        "description": item.description,
        "resourceHint": item.resource_hint,
        "acceptanceCriteria": item.acceptance_criteria,
        "estimatedMinutes": item.estimated_minutes,
        "dueDay": item.due_day,
        "orderIndex": item.order_index,
        "status": item.status,
        "completionNote": item.completion_note,
        "completedAt": item.completed_at.isoformat() if item.completed_at else None,
    }


def _serialize_plan(db: Session, plan: LearningPlan) -> dict[str, Any]:
    items = db.scalars(
        select(LearningPlanItem)
        .where(LearningPlanItem.plan_id == plan.id)
        .order_by(LearningPlanItem.order_index)
    ).all()
    completed = sum(item.status == "completed" for item in items)
    progress = round(completed / len(items) * 100) if items else 0
    return {
        "id": plan.id,
        "goalId": plan.goal_id,
        "ownerId": plan.owner_id,
        "title": plan.title,
        "summary": plan.summary,
        "source": plan.source,
        "status": plan.status,
        "shieldEnergy": plan.shield_energy,
        "guardianValue": plan.guardian_value,
        "progress": progress,
        "completedCount": completed,
        "totalCount": len(items),
        "items": [_serialize_item(item) for item in items],
        "createdAt": plan.created_at.isoformat(),
    }


def _serialize_artifact(db: Session, artifact: LearningArtifact) -> dict[str, Any]:
    versions = db.scalars(
        select(LearningArtifactVersion)
        .where(LearningArtifactVersion.artifact_id == artifact.id)
        .order_by(LearningArtifactVersion.version_no)
    ).all()
    return {
        "id": artifact.id,
        "planId": artifact.plan_id,
        "ownerId": artifact.owner_id,
        "title": artifact.title,
        "artifactType": artifact.artifact_type,
        "description": artifact.description,
        "visibility": artifact.visibility,
        "status": artifact.status,
        "latestVersion": artifact.latest_version,
        "aiReview": _json_load(artifact.ai_review_json, {}),
        "versions": [
            {
                "id": version.id,
                "versionNo": version.version_no,
                "fileName": version.file_name,
                "contentSummary": version.content_summary,
                "revisionNote": version.revision_note,
                "aiReview": _json_load(version.ai_review_json, {}),
                "createdAt": version.created_at.isoformat(),
            }
            for version in versions
        ],
        "createdAt": artifact.created_at.isoformat(),
        "updatedAt": artifact.updated_at.isoformat(),
    }


def _artifact_review(payload: ArtifactVersionRequest, version_no: int) -> dict[str, Any]:
    summary = payload.contentSummary.strip()
    score = 56
    strengths: list[str] = []
    issues: list[str] = []
    suggestions: list[str] = []
    if len(summary) >= 80:
        score += 18
        strengths.append("成果说明较完整，能够看出目标受众和核心内容。")
    else:
        issues.append("成果说明偏短，暂时难以判断内容结构是否完整。")
        suggestions.append("补充目标受众、核心风险信号和希望受众采取的行动。")
    if any(word in summary for word in ("风险", "核验", "转账", "报警", "求助", "诈骗")):
        score += 12
        strengths.append("成果与反诈主题贴合，包含可执行的风险提示。")
    else:
        issues.append("主题关键词和行动建议不够突出。")
        suggestions.append("至少加入一种高危信号、一条核验方法和一个求助渠道。")
    if payload.fileName:
        score += 6
        strengths.append("已形成可归档的成果文件。")
    if version_no >= 2 or payload.revisionNote.strip():
        score += 8
        strengths.append("保留了修改过程，能够体现成果迭代。")
    if not suggestions:
        suggestions.append("可继续优化标题层级和视觉重点，使关键信息在5秒内被识别。")
    return {
        "score": min(score, 96),
        "level": "可发布" if score >= 80 else "建议修改",
        "strengths": strengths,
        "issues": issues,
        "suggestions": suggestions,
        "reviewedAt": datetime.utcnow().isoformat(),
        "source": "AI成果初审（规则降级可用）",
    }


def _activity_counts(db: Session, owner_id: str, plan_id: str) -> dict[str, int]:
    required_total = db.scalar(
        select(func.count(LearningPlanItem.id)).where(
            LearningPlanItem.plan_id == plan_id,
            LearningPlanItem.category == "required",
        )
    ) or 0
    required_completed = db.scalar(
        select(func.count(LearningPlanItem.id)).where(
            LearningPlanItem.plan_id == plan_id,
            LearningPlanItem.category == "required",
            LearningPlanItem.status == "completed",
        )
    ) or 0
    elective_completed = db.scalar(
        select(func.count(LearningPlanItem.id)).where(
            LearningPlanItem.plan_id == plan_id,
            LearningPlanItem.category == "elective",
            LearningPlanItem.status == "completed",
        )
    ) or 0
    artifact_count = db.scalar(
        select(func.count(LearningArtifact.id)).where(
            LearningArtifact.owner_id == owner_id,
            LearningArtifact.plan_id == plan_id,
            LearningArtifact.status == "published",
        )
    ) or 0
    return {
        "requiredTotal": int(required_total),
        "requiredCompleted": int(required_completed),
        "electiveCompleted": int(elective_completed),
        "artifactCount": int(artifact_count),
    }


def _evaluate_unlocks(db: Session, owner_id: str, plan_id: str) -> None:
    _ensure_activity_seeds(db)
    counts = _activity_counts(db, owner_id, plan_id)
    activities = db.scalars(
        select(CampusActivity).where(CampusActivity.enabled.is_(True))
    ).all()
    # 一次性取出该用户在该计划下的所有已解锁活动，避免逐活动查询（N+1 → 1 次）
    existing_rows = db.scalars(
        select(CampusActivityUnlock).where(
            CampusActivityUnlock.owner_id == owner_id,
            CampusActivityUnlock.plan_id == plan_id,
        )
    ).all()
    unlocked_ids = {row.activity_id for row in existing_rows}
    for activity in activities:
        rule = _json_load(activity.unlock_rule_json, {})
        meets = (
            counts["requiredCompleted"] >= int(rule.get("required", 0))
            and counts["electiveCompleted"] >= int(rule.get("electives", 0))
            and counts["artifactCount"] >= int(rule.get("artifacts", 0))
        )
        if meets and activity.id not in unlocked_ids:
            db.add(
                CampusActivityUnlock(
                    owner_id=owner_id,
                    activity_id=activity.id,
                    plan_id=plan_id,
                    unlock_reason_json=json.dumps(counts, ensure_ascii=False),
                )
            )
    db.commit()


def _serialize_activity(
    db: Session,
    activity: CampusActivity,
    owner_id: str,
    plan_id: str,
) -> dict[str, Any]:
    counts = _activity_counts(db, owner_id, plan_id)
    rule = _json_load(activity.unlock_rule_json, {})
    unlock = db.scalar(
        select(CampusActivityUnlock).where(
            CampusActivityUnlock.owner_id == owner_id,
            CampusActivityUnlock.activity_id == activity.id,
            CampusActivityUnlock.plan_id == plan_id,
        )
    )
    requirements = [
        {
            "label": f"完成基础必修 {rule.get('required', 0)} 项",
            "current": counts["requiredCompleted"],
            "target": int(rule.get("required", 0)),
            "completed": counts["requiredCompleted"] >= int(rule.get("required", 0)),
        },
        {
            "label": f"完成兴趣选修 {rule.get('electives', 0)} 项",
            "current": counts["electiveCompleted"],
            "target": int(rule.get("electives", 0)),
            "completed": counts["electiveCompleted"] >= int(rule.get("electives", 0)),
        },
        {
            "label": f"发布学习成果 {rule.get('artifacts', 0)} 项",
            "current": counts["artifactCount"],
            "target": int(rule.get("artifacts", 0)),
            "completed": counts["artifactCount"] >= int(rule.get("artifacts", 0)),
        },
    ]
    ratios = [
        min(req["current"] / req["target"], 1) if req["target"] else 1 for req in requirements
    ]
    return {
        "id": activity.id,
        "title": activity.title,
        "category": activity.category,
        "description": activity.description,
        "organizer": activity.organizer,
        "interestDirection": activity.interest_direction,
        "noticeUrl": activity.notice_url,
        "status": "unlocked" if unlock else "locked",
        "progress": round(sum(ratios) / len(ratios) * 100),
        "requirements": requirements,
        "unlockedAt": unlock.unlocked_at.isoformat() if unlock else None,
        "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
    }


def create_learning_market_router(get_db: Callable[..., Any]) -> APIRouter:
    router = APIRouter(prefix="/api/learning", tags=["AI学习集市"])

    @router.get("/templates")
    def get_templates() -> dict[str, Any]:
        return {"templates": TEMPLATES, "total": len(TEMPLATES)}

    @router.post("/goals/validate")
    def validate_goal(payload: GoalValidationRequest) -> dict[str, Any]:
        return _validate_goal(payload)

    @router.post("/goals")
    def create_goal(
        payload: GoalCreateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        validation = _validate_goal(payload)
        goal = LearningGoal(
            id=_new_id("goal"),
            owner_id=payload.ownerId,
            theme=payload.theme.strip(),
            learning_type=payload.learningType,
            period_days=payload.periodDays,
            daily_minutes=payload.dailyMinutes,
            difficulty=payload.difficulty,
            expected_outcome=payload.expectedOutcome.strip(),
            major_direction=payload.majorDirection,
            elective_tracks_json=json.dumps(payload.electiveTracks, ensure_ascii=False),
            validation_json=json.dumps(validation, ensure_ascii=False),
        )
        db.add(goal)
        db.flush()
        plan = _create_plan(db, goal)
        db.commit()
        return {
            "goal": _serialize_goal(goal),
            "plan": _serialize_plan(db, plan),
            "message": "目标已校验，并生成可编辑的个性化任务包。",
        }

    @router.get("/dashboard")
    def learning_dashboard(
        ownerId: str = Query(min_length=1),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.scalar(
            select(LearningPlan)
            .where(LearningPlan.owner_id == ownerId, LearningPlan.status == "active")
            .order_by(LearningPlan.created_at.desc())
        )
        if not plan:
            return {
                "goal": None,
                "plan": None,
                "artifacts": [],
                "activities": [],
                "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
            }
        goal = db.get(LearningGoal, plan.goal_id)
        artifacts = db.scalars(
            select(LearningArtifact)
            .where(LearningArtifact.owner_id == ownerId, LearningArtifact.plan_id == plan.id)
            .order_by(LearningArtifact.updated_at.desc())
        ).all()
        _evaluate_unlocks(db, ownerId, plan.id)
        activities = db.scalars(
            select(CampusActivity)
            .where(CampusActivity.enabled.is_(True))
            .order_by(CampusActivity.created_at)
        ).all()
        return {
            "goal": _serialize_goal(goal) if goal else None,
            "plan": _serialize_plan(db, plan),
            "artifacts": [_serialize_artifact(db, artifact) for artifact in artifacts],
            "activities": [
                _serialize_activity(db, activity, ownerId, plan.id) for activity in activities
            ],
            "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
        }

    @router.patch("/plan-items/{item_id}")
    def update_plan_item(
        item_id: str,
        payload: PlanItemUpdateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        item = db.get(LearningPlanItem, item_id)
        if not item or item.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务不存在")
        values = payload.model_dump(exclude_none=True, by_alias=False)
        field_map = {
            "title": "title",
            "description": "description",
            "estimatedMinutes": "estimated_minutes",
            "dueDay": "due_day",
            "status": "status",
            "completionNote": "completion_note",
        }
        for key, target in field_map.items():
            if key in values:
                setattr(item, target, values[key])
        db.commit()
        return {"item": _serialize_item(item)}

    @router.post("/plan-items/{item_id}/complete")
    def complete_plan_item(
        item_id: str,
        payload: PlanItemCompleteRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        item = db.get(LearningPlanItem, item_id)
        if not item or item.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务不存在")
        plan = db.get(LearningPlan, item.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="任务包不存在")
        awarded = 0
        if item.status != "completed":
            item.status = "completed"
            item.completed_at = datetime.utcnow()
            item.completion_note = payload.completionNote
            awarded = 18 if item.category == "elective" else 12
            plan.shield_energy += awarded
            plan.guardian_value += awarded
        db.commit()
        _evaluate_unlocks(db, payload.ownerId, plan.id)
        return {
            "awarded": awarded,
            "message": f"完成有效学习，盾能 +{awarded}" if awarded else "该任务已经完成",
            "plan": _serialize_plan(db, plan),
        }

    @router.post("/plan-items/{item_id}/replace")
    def replace_plan_item(
        item_id: str,
        payload: PlanItemReplaceRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        item = db.get(LearningPlanItem, item_id)
        if not item or item.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务不存在")
        if item.category != "elective":
            raise HTTPException(status_code=400, detail="基础必修和成果任务不可直接替换")
        replacements = {
            "AI对练": (
                "小盾灵诈骗话术对练",
                "通过多轮问答练习身份核验、拒绝转账和有效求助。",
                "完成一次对练并整理三条应对原则。",
            ),
            "案例研判": (
                "校园诈骗案例研判",
                "拆解诈骗链路，标注关键风险节点和正确处置方式。",
                "完成风险节点标注与处置复盘。",
            ),
            "创意表达": (
                "反诈创意表达练习",
                "把反诈知识转化为适合大学生传播的文案与视觉表达。",
                "形成一版标题、核心文案和内容结构。",
            ),
            "情境挑战": (
                "高压诈骗情境识别挑战",
                "在限时对话中识别催促、威胁、利诱和私下转账信号。",
                "识别至少3个信号并作出安全决策。",
            ),
        }
        title, description, criteria = replacements.get(
            payload.direction,
            (
                f"{payload.direction}兴趣探索",
                f"围绕{payload.direction}开展一次自主主题学习。",
                "完成学习并提交个人复盘。",
            ),
        )
        item.title = title
        item.description = description
        item.acceptance_criteria = criteria
        item.resource_hint = "AI重新推荐 · 兴趣选修"
        item.status = "not_started"
        item.completed_at = None
        db.commit()
        return {"item": _serialize_item(item), "message": "已只替换当前选修任务。"}

    @router.post("/companion")
    def companion(
        payload: CompanionRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.get(LearningPlan, payload.planId)
        if not plan or plan.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务包不存在")
        items = db.scalars(
            select(LearningPlanItem)
            .where(
                LearningPlanItem.plan_id == plan.id,
                LearningPlanItem.status != "completed",
            )
            .order_by(LearningPlanItem.order_index)
        ).all()
        next_item = items[0] if items else None
        message = payload.message.strip()
        if any(word in message for word in ("今天", "安排", "先做", "下一步")) and next_item:
            reply = (
                f"今天建议先完成“{next_item.title}”，预计{next_item.estimated_minutes}分钟。"
                f"完成标准是：{next_item.acceptance_criteria}。我可以继续帮你拆成三个小步骤。"
            )
        elif any(word in message for word in ("不会", "困难", "看不懂", "答错")):
            reply = (
                "先不要急着找标准答案。请先写出你能识别到的风险信号、需要核验的信息和安全底线，"
                "我再根据你的判断补充遗漏点。"
            )
        elif any(word in message for word in ("海报", "成果", "作品")):
            reply = (
                "建议先明确受众，再按“高危信号—核验方法—立即行动”组织内容。"
                "成果工坊会保留V1、V2版本，并给出贴合度和完整性建议。"
            )
        else:
            reply = (
                f"我已结合“{plan.title}”回答。你可以继续问我当前任务的知识点、"
                "完成标准或成果修改思路；我会提供方法引导，不直接代做最终成果。"
            )
        return {
            "reply": reply,
            "source": "小盾灵学习陪伴（规则降级可用）",
            "nextTask": _serialize_item(next_item) if next_item else None,
        }

    @router.post("/artifacts")
    def create_artifact(
        payload: ArtifactCreateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.get(LearningPlan, payload.planId)
        if not plan or plan.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务包不存在")
        artifact = LearningArtifact(
            id=_new_id("artifact"),
            plan_id=payload.planId,
            owner_id=payload.ownerId,
            title=payload.title,
            artifact_type=payload.artifactType,
            description=payload.description,
            visibility=payload.visibility,
        )
        db.add(artifact)
        db.commit()
        return {"artifact": _serialize_artifact(db, artifact)}

    @router.post("/artifacts/{artifact_id}/versions")
    def add_artifact_version(
        artifact_id: str,
        payload: ArtifactVersionRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="成果不存在")
        version_no = artifact.latest_version + 1
        review = _artifact_review(payload, version_no)
        version = LearningArtifactVersion(
            artifact_id=artifact.id,
            version_no=version_no,
            file_name=payload.fileName,
            content_summary=payload.contentSummary,
            revision_note=payload.revisionNote,
            ai_review_json=json.dumps(review, ensure_ascii=False),
        )
        db.add(version)
        artifact.latest_version = version_no
        artifact.ai_review_json = json.dumps(review, ensure_ascii=False)
        artifact.updated_at = datetime.utcnow()
        db.commit()
        return {
            "artifact": _serialize_artifact(db, artifact),
            "review": review,
            "message": f"V{version_no} 已归档并完成AI初审。",
        }

    @router.post("/artifacts/{artifact_id}/upload")
    async def upload_artifact_file(
        artifact_id: str,
        ownerId: str = Query(min_length=1),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != ownerId:
            raise HTTPException(status_code=404, detail="成果不存在")
        suffix = Path(file.filename or "").suffix.lower()
        allowed = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".mp4", ".zip"}
        if suffix not in allowed:
            raise HTTPException(status_code=400, detail="暂不支持该文件格式")
        content = await file.read(25 * 1024 * 1024 + 1)
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="成果文件不能超过25MB")
        upload_dir = Path(__file__).resolve().parents[1] / "data" / "learning_artifacts" / artifact_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}{suffix}"
        (upload_dir / storage_name).write_bytes(content)
        return {
            "fileName": file.filename or storage_name,
            "storageKey": f"{artifact_id}/{storage_name}",
            "size": len(content),
            "message": "成果文件已安全保存。",
        }

    @router.post("/artifacts/{artifact_id}/publish")
    def publish_artifact(
        artifact_id: str,
        payload: ArtifactPublishRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="成果不存在")
        if artifact.latest_version < 1:
            raise HTTPException(status_code=400, detail="请先提交至少一个成果版本")
        first_publish = artifact.status != "published"
        artifact.status = "published"
        artifact.visibility = payload.visibility
        artifact.updated_at = datetime.utcnow()
        listing = db.scalar(
            select(LearningMarketListing).where(
                LearningMarketListing.resource_type == "artifact",
                LearningMarketListing.resource_id == artifact.id,
            )
        )
        goal = None
        plan = db.get(LearningPlan, artifact.plan_id)
        if plan:
            goal = db.get(LearningGoal, plan.goal_id)
        if payload.visibility == "public" and not listing:
            listing = LearningMarketListing(
                id=_new_id("listing"),
                owner_id=payload.ownerId,
                resource_type="artifact",
                resource_id=artifact.id,
                title=artifact.title,
                theme=goal.theme if goal else "主题学习",
                summary=artifact.description or "学生主题学习成果",
                tags_json=json.dumps([artifact.artifact_type, "学习成果"], ensure_ascii=False),
            )
            db.add(listing)
        if first_publish and plan:
            plan.shield_energy += 30
            plan.guardian_value += 30
            outcome_item = db.scalar(
                select(LearningPlanItem).where(
                    LearningPlanItem.plan_id == plan.id,
                    LearningPlanItem.category == "outcome",
                )
            )
            if outcome_item and outcome_item.status != "completed":
                outcome_item.status = "completed"
                outcome_item.completed_at = datetime.utcnow()
                outcome_item.completion_note = f"成果《{artifact.title}》已发布"
        db.commit()
        _evaluate_unlocks(db, payload.ownerId, artifact.plan_id)
        return {
            "artifact": _serialize_artifact(db, artifact),
            "message": "成果已发布至学习集市。" if payload.visibility == "public" else "成果已归档至个人档案。",
        }

    @router.post("/plans/{plan_id}/share")
    def share_plan(
        plan_id: str,
        payload: PlanShareRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.get(LearningPlan, plan_id)
        if not plan or plan.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务包不存在")
        goal = db.get(LearningGoal, plan.goal_id)
        listing = db.scalar(
            select(LearningMarketListing).where(
                LearningMarketListing.resource_type == "plan",
                LearningMarketListing.resource_id == plan.id,
            )
        )
        if not listing:
            listing = LearningMarketListing(
                id=_new_id("listing"),
                owner_id=payload.ownerId,
                resource_type="plan",
                resource_id=plan.id,
                title=plan.title,
                theme=goal.theme if goal else "自主学习",
                summary=plan.summary,
                tags_json=json.dumps(
                    [goal.difficulty, goal.learning_type, "可复用任务包"] if goal else ["可复用任务包"],
                    ensure_ascii=False,
                ),
            )
            db.add(listing)
            db.commit()
        return {"listingId": listing.id, "message": "任务包已公开，可供其他学生复用和二次修改。"}

    @router.get("/market")
    def get_market(
        resourceType: str = Query(default="all"),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rows = db.scalars(
            select(LearningMarketListing)
            .where(LearningMarketListing.status == "published")
            .order_by(LearningMarketListing.created_at.desc())
        ).all()
        listings = [
            {
                "id": row.id,
                "ownerId": row.owner_id,
                "resourceType": row.resource_type,
                "resourceId": row.resource_id,
                "title": row.title,
                "theme": row.theme,
                "summary": row.summary,
                "tags": _json_load(row.tags_json, []),
                "likes": row.likes,
                "favorites": row.favorites,
                "reuseCount": row.reuse_count,
                "createdAt": row.created_at.isoformat(),
            }
            for row in rows
            if resourceType == "all" or row.resource_type == resourceType
        ]
        templates = TEMPLATES if resourceType in ("all", "plan") else []
        return {"templates": templates, "listings": listings}

    @router.post("/market/{resource_id}/reuse")
    def reuse_market_resource(
        resource_id: str,
        payload: MarketReuseRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        template = next((item for item in TEMPLATES if item["id"] == resource_id), None)
        if template:
            create_payload = GoalCreateRequest(
                ownerId=payload.ownerId,
                theme=template["theme"],
                periodDays=template["periodDays"],
                dailyMinutes=template["dailyMinutes"],
                difficulty=template["difficulty"],
                expectedOutcome=template["expectedOutcome"],
                learningType="自主学习",
                majorDirection="通识能力",
                electiveTracks=template["electiveTracks"],
            )
            validation = _validate_goal(create_payload)
            goal = LearningGoal(
                id=_new_id("goal"),
                owner_id=payload.ownerId,
                theme=create_payload.theme,
                learning_type=create_payload.learningType,
                period_days=create_payload.periodDays,
                daily_minutes=create_payload.dailyMinutes,
                difficulty=create_payload.difficulty,
                expected_outcome=create_payload.expectedOutcome,
                major_direction=create_payload.majorDirection,
                elective_tracks_json=json.dumps(create_payload.electiveTracks, ensure_ascii=False),
                validation_json=json.dumps(validation, ensure_ascii=False),
            )
            db.add(goal)
            db.flush()
            plan = _create_plan(db, goal)
            db.commit()
            return {
                "goal": _serialize_goal(goal),
                "plan": _serialize_plan(db, plan),
                "message": "模板已复用为你的任务包，可继续修改。",
            }

        listing = db.get(LearningMarketListing, resource_id)
        if not listing or listing.resource_type != "plan":
            raise HTTPException(status_code=404, detail="可复用任务包不存在")
        source_plan = db.get(LearningPlan, listing.resource_id)
        if not source_plan:
            raise HTTPException(status_code=404, detail="源任务包不存在")
        source_goal = db.get(LearningGoal, source_plan.goal_id)
        if not source_goal:
            raise HTTPException(status_code=404, detail="源学习目标不存在")
        goal = LearningGoal(
            id=_new_id("goal"),
            owner_id=payload.ownerId,
            theme=source_goal.theme,
            learning_type=source_goal.learning_type,
            period_days=source_goal.period_days,
            daily_minutes=source_goal.daily_minutes,
            difficulty=source_goal.difficulty,
            expected_outcome=source_goal.expected_outcome,
            major_direction=source_goal.major_direction,
            elective_tracks_json=source_goal.elective_tracks_json,
            validation_json=source_goal.validation_json,
        )
        db.add(goal)
        db.flush()
        plan = _create_plan(db, goal)
        listing.reuse_count += 1
        db.commit()
        return {
            "goal": _serialize_goal(goal),
            "plan": _serialize_plan(db, plan),
            "message": "已复制该任务包，修改不会影响原作者版本。",
        }

    @router.get("/activities")
    def get_activities(
        ownerId: str = Query(min_length=1),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.scalar(
            select(LearningPlan)
            .where(LearningPlan.owner_id == ownerId, LearningPlan.status == "active")
            .order_by(LearningPlan.created_at.desc())
        )
        if not plan:
            return {"activities": [], "plan": None, "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE}
        _evaluate_unlocks(db, ownerId, plan.id)
        activities = db.scalars(
            select(CampusActivity)
            .where(CampusActivity.enabled.is_(True))
            .order_by(CampusActivity.created_at)
        ).all()
        return {
            "activities": [
                _serialize_activity(db, activity, ownerId, plan.id) for activity in activities
            ],
            "plan": {
                "id": plan.id,
                "shieldEnergy": plan.shield_energy,
                "guardianValue": plan.guardian_value,
            },
            "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
        }

    return router
