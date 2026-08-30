from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..schemas import *
from ..rules import *
from ..helpers import *
# NOTE: `from ..helpers import *` skips underscore-prefixed names (Python
# semantics). Several module-level helpers used by routers start with `_`
# (e.g. _award_lock, _NUMERIC_RULE_KEYS, _KEY_MAP, _ADMIN_KEY_WARNED), so we
# import them explicitly to preserve the original single-module behaviour.
from ..assessment_service import *
from ..ability_profile import *
from ..retrain_scheduler import *
from ..task_planner import *
from ..scenario_state_machine import *
from ..review_engine import *
from ..emergency_stop_loss import *
from ..ai_logger import *


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/counselor", tags=["counselor"])

@router.get("/dashboard")

def counselor_dashboard(db: Session = Depends(get_db)) -> dict[str, object]:
        """辅导员看板 — 匿名学生画像、班级汇总"""
        # 所有学生数据汇总
        students = db.scalars(select(User)).all()
        total_students = len(students)
        assessed = sum(1 for u in students if u.has_completed_assessment)
        has_pets = sum(1 for u in students if u.has_pet)

        # 能力画像汇总
        all_assessments = db.scalars(
            select(AssessmentResult).order_by(AssessmentResult.created_at.desc())
        ).all()

        # 按维度聚合
        dim_avg: dict[str, list[float]] = {"辨识力": [], "判断力": [], "应变力": [], "实证力": [], "协作力": []}
        all_weak: dict[str, int] = {}
        owner_latest: dict[str, AssessmentResult] = {}
        for a in all_assessments:
            if a.owner_id not in owner_latest:
                owner_latest[a.owner_id] = a
        for a in owner_latest.values():
            scores = normalize_profile_scores(json.loads(a.ability_profile_json))
            for dim, val in scores.items():
                if dim in dim_avg:
                    dim_avg[dim].append(float(val))
            for dim in json.loads(a.weak_dimensions_json):
                all_weak[normalize_dim_key(dim)] = all_weak.get(normalize_dim_key(dim), 0) + 1

        avg_scores = {dim: round(sum(vals) / len(vals), 1) if vals else 0 for dim, vals in dim_avg.items()}

        # 训练统计
        total_training = db.scalar(select(func.count(TrainingRecord.id))) or 0
        avg_accuracy = db.scalar(select(func.avg(TrainingRecord.accuracy))) or 0

        # 诈骗类型分布（单次 GROUP BY，替代逐类型 COUNT 的 N+1）
        fraud_rows = db.execute(
            select(TrainingTask.fraud_type, func.count(TrainingRecord.id))
            .join(TrainingTask, TrainingRecord.task_id == TrainingTask.id)
            .group_by(TrainingTask.fraud_type)
        ).all()
        fraud_counts = {ft: int(c) for ft, c in fraud_rows if c}

        # 学生匿名画像列表
        owner_ids = list(owner_latest.keys())[:50]  # 最多50人
        # 一次性取出这些学生的宠物，避免逐人查询（N+1 → 1 次 IN 查询）
        pet_map: dict[str, object] = {}
        if owner_ids:
            pet_map = {
                p.owner_id: p
                for p in db.scalars(select(Pet).where(Pet.owner_id.in_(owner_ids))).all()
            }
        student_profiles = []
        for owner_id in owner_ids:
            a = owner_latest[owner_id]
            pet = pet_map.get(owner_id)
            student_profiles.append({
                "ownerId": owner_id,
                "overallScore": round(sum(json.loads(a.ability_profile_json).values()) / 5),
            "weakDimensions": [normalize_dim_key(d) for d in json.loads(a.weak_dimensions_json)],
            "accuracy": a.accuracy,
                "petLevel": pet.level if pet else 0,
                "lastAssessment": a.created_at.isoformat(),
            })

        # 训练趋势（最近7天）
        from datetime import timedelta
        training_trend = []
        for i in range(7):
            day = datetime.utcnow() - timedelta(days=6 - i)
            day_start = day.replace(hour=0, minute=0, second=0)
            day_end = day_start + timedelta(days=1)
            count = db.scalar(
                select(func.count(TrainingRecord.id))
                .where(TrainingRecord.created_at >= day_start, TrainingRecord.created_at < day_end)
            ) or 0
            training_trend.append({
                "date": day_start.strftime("%m-%d"),
                "count": count,
            })

        return {
            "overview": {
                "totalStudents": total_students,
                "assessedRate": round(assessed / max(total_students, 1) * 100),
                "petRate": round(has_pets / max(total_students, 1) * 100),
                "totalTraining": total_training,
                "avgAccuracy": round(avg_accuracy * 100, 1) if avg_accuracy else 0,
            },
            "avgScores": avg_scores,
            "weakDistribution": [{"dimension": k, "count": v} for k, v in sorted(all_weak.items(), key=lambda x: -x[1])[:5]],
            "fraudDistribution": [{"type": k, "count": v} for k, v in sorted(fraud_counts.items(), key=lambda x: -x[1])[:8]],
            "trainingTrend": training_trend,
            "studentProfiles": student_profiles,
        }


@router.get("/class-meeting")

def class_meeting_materials(db: Session = Depends(get_db)) -> dict[str, object]:
        """班会素材生成 — 基于班级数据生成讨论话题和教育建议"""
        # 获取高频薄弱维度
        all_assessments = db.scalars(select(AssessmentResult).order_by(AssessmentResult.created_at.desc())).all()
        owner_latest = {}
        for a in all_assessments:
            if a.owner_id not in owner_latest:
                owner_latest[a.owner_id] = a

        weak_counter: dict[str, int] = {}
        for a in owner_latest.values():
            for dim in json.loads(a.weak_dimensions_json):
                nk = normalize_dim_key(dim)
                weak_counter[nk] = weak_counter.get(nk, 0) + 1

        top_weak = sorted(weak_counter.items(), key=lambda x: -x[1])[:3]

        # 根据薄弱维度生成讨论问题
        DISCUSSION_TEMPLATES = {
            "辨识力": {
                "topic": "识别风险信号",
                "questions": [
                    "当你收到一条自称'客服退款'的短信时，你会怎么辨别真伪？",
                    "讨论：兼职刷单为什么是诈骗？你能识别出哪些危险信号？",
                ],
                "activity": "角色扮演：一人扮演骗子发布刷单兼职信息，其他人尝试识别风险点。",
            },
            "判断力": {
                "topic": "理性判断与决策",
                "questions": [
                    "如果有人承诺'稳赚不赔、年化30%收益'，你该如何判断？",
                    "讨论：为什么骗子喜欢利用'紧急'和'限时'来施压？",
                ],
                "activity": "案例分析：给出一段AI换脸视频借钱场景，讨论该如何核实与应对。",
            },
            "应变力": {
                "topic": "正确应对策略",
                "questions": [
                    "被要求开启屏幕共享时，正确的做法是什么？为什么？",
                    "讨论：收到验证码短信时，是否可以告诉任何人？为什么？",
                ],
                "activity": "情景模拟：收到'老师'在群里发收款码要求交费，分角色演练正确应对流程。",
            },
            "实证力": {
                "topic": "证据保留与举证",
                "questions": [
                    "如果真的遇到诈骗，应该保留哪些证据？",
                    "讨论：微信聊天记录和转账截图在报警时有什么作用？",
                ],
                "activity": "实战演练：模拟被骗后的证据收集流程，学会截图保存关键信息。",
            },
            "协作力": {
                "topic": "求助渠道与止损",
                "questions": [
                    "你知道哪些求助渠道？96110是什么电话？",
                    "讨论：发现被骗后，第一件事应该做什么？时间有多重要？",
                ],
                "activity": "知识竞赛：反诈热线、报警流程、银行紧急止付相关知识抢答。",
            },
        }

        topics = []
        for dim, count in top_weak:
            template = DISCUSSION_TEMPLATES.get(dim)
            if template:
                topics.append({"dimension": dim, "weakCount": count, **template})

        # 辅导员建议
        suggestions = [
            "定期在班级群发送反诈知识科普，重点针对班级高频薄弱维度",
            "组织反诈主题班会，每学期至少2次",
            "关注近期高发诈骗类型，及时向学生预警",
            "建立班级反诈联络员制度，发现可疑情况及时通知辅导员",
            "提醒学生遇到可疑情况第一时间拨打96110核实",
        ]

        return {
            "generatedAt": datetime.utcnow().isoformat(),
            "classProfile": {
                "totalAssessed": len(owner_latest),
                "topWeakDimensions": [{"dimension": d, "count": c} for d, c in top_weak],
            },
            "topics": topics,
            "suggestions": suggestions,
        }


