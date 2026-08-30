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


router = APIRouter(prefix="/api/v1/assessment", tags=["v1_assessment"])

@router.post("/sessions")

def v1_create_session(payload: CreateSessionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """创建测评会话，按模式分层随机抽取题目。

        mode 可选：quick（10题快速）/ standard（20题标准）
        返回会话信息 + 完整题目列表（不含正确答案）。
        """
        if payload.mode not in MODE_CONFIG:
            raise HTTPException(400, f"Unknown mode: {payload.mode}. Valid: {list(MODE_CONFIG.keys())}")

        sess, questions = create_assessment_session(db, payload.ownerId, payload.mode)

        # 验证题库充足
        if len(questions) < MODE_CONFIG[payload.mode]["total_questions"]:
            raise HTTPException(500, "题库不足，请联系管理员补充题库")

        # 返回前端需要的题目格式（不含正确答案，由服务端事后判断）
        question_items: list[dict[str, object]] = []
        for q in questions:
            question_items.append({
                "id": q.id,
                "questionType": q.question_type,
                "fraudType": q.fraud_type,
                "abilityDim": q.ability_dim,
                "riskStage": q.risk_stage,
                "stem": q.stem,
                "options": json.loads(q.options_json),
                "difficulty": q.difficulty,
            })

        return {
            "sessionId": sess.id,
            "mode": sess.mode,
            "totalQuestions": sess.total_questions,
            "startedAt": sess.started_at.isoformat(),
            "questions": question_items,
        }


@router.get("/sessions/{session_id}")

def v1_get_session(session_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
        """获取测评会话状态和进度。"""
        sess = db.get(AssessmentSession, session_id)
        if not sess:
            raise HTTPException(404, f"Session not found: {session_id}")

        answers = (
            db.query(AssessmentAnswerRecord)
            .filter(AssessmentAnswerRecord.session_id == session_id)
            .order_by(AssessmentAnswerRecord.created_at)
            .all()
        )
        answered_ids = {a.question_id for a in answers}

        # 重新加载题目以构建完整题目列表
        all_qs = db.query(QuestionMetadata).filter(QuestionMetadata.enabled.is_(True)).all()

        return {
            "sessionId": sess.id,
            "ownerId": sess.owner_id,
            "mode": sess.mode,
            "status": sess.status,
            "totalQuestions": sess.total_questions,
            "completedQuestions": sess.completed_questions,
            "startedAt": sess.started_at.isoformat(),
            "completedAt": sess.completed_at.isoformat() if sess.completed_at else None,
            "answeredIds": list(answered_ids),
        }


@router.post("/sessions/answer")

def v1_submit_answer(payload: SubmitAnswerRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """提交单题答案，记录到 assessment_answers 表。

        返回反馈：correct, score（0-1）, correctAnswer, explanation。
        """
        sess = db.get(AssessmentSession, payload.sessionId)
        if not sess:
            raise HTTPException(404, f"Session not found: {payload.sessionId}")
        if sess.status != "in_progress":
            raise HTTPException(400, f"Session already {sess.status}")

        question = db.get(QuestionMetadata, payload.questionId)
        if not question:
            raise HTTPException(404, f"Question not found: {payload.questionId}")

        # 检查是否已答过此题
        existing = (
            db.query(AssessmentAnswerRecord)
            .filter(
                AssessmentAnswerRecord.session_id == payload.sessionId,
                AssessmentAnswerRecord.question_id == payload.questionId,
            )
            .first()
        )
        if existing:
            # 已答过，返回已有结果
            return {
                "isCorrect": existing.is_correct,
                "score": existing.score,
                "correctAnswer": json.loads(question.correct_answer_json),
                "explanation": question.explanation,
                "alreadyAnswered": True,
            }

        # 记录答案
        answer_record = record_assessment_answer(db, sess, question, payload.answer)

        return {
            "isCorrect": answer_record.is_correct,
            "score": answer_record.score,
            "correctAnswer": json.loads(question.correct_answer_json),
            "explanation": question.explanation,
            "alreadyAnswered": False,
        }


@router.post("/sessions/complete")

def v1_complete_session(payload: CompleteSessionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """完成测评会话，计算五维能力画像并返回评价结果。（幂等：重复调用安全）"""
        sess = db.get(AssessmentSession, payload.sessionId)
        if not sess:
            raise HTTPException(404, f"Session not found: {payload.sessionId}")

        # finalize_session 本身幂等：已完成的会话不再重复写入 AssessmentResult
        result = finalize_assessment_session(db, sess)

        user = get_or_create_user(db, sess.owner_id)
        growth_awarded = 30 if result["accuracy"] >= 0.6 else 20

        return {
            "sessionId": sess.id,
            "mode": result["mode"],
            "totalQuestions": result["total_questions"],
            "correctCount": result["correct_count"],
            "accuracy": result["accuracy"],
            "abilityProfile": {
                "scores": result["ability_profile"],
                "weakDimensions": result["weak_dimensions"],
                "overallScore": round(sum(result["ability_profile"].values()) / len(result["ability_profile"]), 1) if result["ability_profile"] else 0,
            },
            "weakAreas": result["weak_areas"][:3] if result["weak_areas"] else ["暂无明显薄弱项，建议保持学习"],
            "wrongQuestions": result["wrong_questions"],
            "growthAwarded": growth_awarded,
            "unlockedPetPool": True,
            "currentUser": user_to_response(user),
        }


@router.get("/ability-profile")

def v1_ability_profile(
        ownerId: str = Query("U-2408**"),
        includeHistory: bool = Query(False, alias="includeHistory"),
        db: Session = Depends(get_db),
    ) -> dict[str, object]:
        """获取用户五维能力画像（v1）。
        
        - 返回最新测评的画像数据
        - 可选返回历史快照数组用于趋势图
        - 能力等级完全由规则计算，不依赖 AI
        """
        from ..ability_profile import ABILITY_DIMENSIONS, DIMENSION_DESCRIPTIONS, DIMENSION_SUGGESTIONS

        latest = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.owner_id == ownerId)
            .order_by(AssessmentResult.created_at.desc())
            .first()
        )
        if not latest:
            return {"profile": None, "hasCompletedAssessment": False, "message": "尚未完成测评，请先参与能力测评"}

        scores = json.loads(latest.ability_profile_json)
        weak_dimensions = json.loads(latest.weak_dimensions_json)

        overall = round(sum(scores.values()) / len(ABILITY_DIMENSIONS), 1)
        strong_dimensions = [d for d in ABILITY_DIMENSIONS if scores.get(d, 0) >= 80]

        # 能力等级（与服务端规则一致）
        def _compute_level(score: float) -> str:
            if score >= 85:
                return "防诈达人"
            elif score >= 70:
                return "防诈能手"
            elif score >= 50:
                return "防诈新手"
            else:
                return "防诈入门"

        def _compute_pet_stage(score: float) -> str:
            if score >= 85:
                return "王者"
            elif score >= 70:
                return "精英"
            elif score >= 50:
                return "成长"
            else:
                return "萌新"

        dimensions = []
        for dim in ABILITY_DIMENSIONS:
            score = scores.get(dim, 0)
            dimensions.append({
                "dimension": dim,
                "score": score,
                "maxScore": 100,
                "percentage": score,
                "description": DIMENSION_DESCRIPTIONS.get(dim, ""),
                "suggestion": DIMENSION_SUGGESTIONS.get(dim, ""),
            })

        profile = {
            "dimensions": dimensions,
            "scores": scores,
            "overallScore": overall,
            "weakDimensions": weak_dimensions,
            "strongDimensions": strong_dimensions,
            "level": _compute_level(overall),
            "petStage": _compute_pet_stage(overall),
            "assessmentTime": latest.created_at.isoformat(),
        }

        response_data: dict[str, object] = {
            "profile": profile,
            "hasCompletedAssessment": True,
        }

        # 可选：历史快照趋势
        if includeHistory:
            snapshots = (
                db.query(AbilitySnapshot)
                .filter(AbilitySnapshot.owner_id == ownerId)
                .order_by(AbilitySnapshot.created_at.asc())
                .all()
            )
            history = []
            for snap in snapshots:
                snap_scores = json.loads(snap.scores_json)
                history.append({
                    "id": snap.id,
                    "scores": snap_scores,
                    "overallScore": round(sum(snap_scores.values()) / len(ABILITY_DIMENSIONS), 1),
                    "triggerEvent": snap.trigger_event,
                    "createdAt": snap.created_at.isoformat(),
                })
            response_data["history"] = history

        return response_data


