from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
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


router = APIRouter(prefix="/api/assessment", tags=["assessment"])

@router.get("/questions")

def assessment_questions(count: int = Query(default=5, ge=3, le=10)) -> dict[str, object]:
        # 支持极速测评(3题)/默认测评(5题)/完整测评(8-10题)
        selected = ASSESSMENT_QUESTIONS[:count]
        return {
            "questions": [
                {
                    "id": q["id"],
                    "questionType": q["questionType"],
                    "fraudType": q["fraudType"],
                    "stem": q["stem"],
                    "options": q["options"],
                    "correctAnswer": q["correctAnswer"],
                    "explanation": q["explanation"],
                }
                for q in selected
            ]
        }


@router.post("/submit")

def submit_assessment(payload: AssessmentSubmitRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        user = get_or_create_user(db, payload.ownerId)
        user.has_completed_assessment = True
        user.updated_at = datetime.utcnow()
        db.commit()
        # 根据真实答案计算正确率、薄弱类型和五维能力画像
        question_map = {q["id"]: q for q in ASSESSMENT_QUESTIONS}
        correct_count = 0
        wrong_types: list[str] = []
        wrong_questions: list[str] = []
        for answer in payload.answers:
            question = question_map.get(answer.questionId)
            if not question:
                continue
            provided = normalize_answer(answer.answer)
            correct_answer = normalize_answer(question["correctAnswer"])
            if provided == correct_answer:
                correct_count += 1
            else:
                if question["fraudType"] not in wrong_types:
                    wrong_types.append(question["fraudType"])
                wrong_questions.append(question["id"])
        total = len(payload.answers) if payload.answers else 1
        accuracy = round(correct_count / total, 2)

        # 计算五维能力画像（整改核心升级）
        from ..ability_profile import compute_ability_profile
        answers_for_profile = [
            {
                "questionId": ans.questionId,
                "selected": list(normalize_answer(ans.answer)),
            }
            for ans in payload.answers
        ]
        profile = compute_ability_profile(answers_for_profile, ASSESSMENT_QUESTIONS)

        # 保存测评结果（含五维画像）
        result = AssessmentResult(
            owner_id=payload.ownerId,
            mode="quick" if total <= 5 else "standard",
            total_questions=total,
            correct_count=correct_count,
            accuracy=accuracy,
            ability_profile_json=json.dumps(profile["scores"], ensure_ascii=False),
            wrong_questions_json=json.dumps(wrong_questions, ensure_ascii=False),
            weak_dimensions_json=json.dumps(profile["weakDimensions"], ensure_ascii=False),
        )
        db.add(result)
        db.commit()

        growth_awarded = 30 if accuracy >= 0.6 else 20
        return {
            "accuracy": accuracy,
            "correctCount": correct_count,
            "totalCount": len(payload.answers),
            "weakAreas": wrong_types[:3] if wrong_types else ["暂无明显薄弱项，建议保持学习"],
            "abilityProfile": profile,
            "growthAwarded": growth_awarded,
            "unlockedPetPool": True,
            "currentUser": user_to_response(user),
        }


@router.get("/ability-profile")

def get_ability_profile(ownerId: str = Query("U-2408**"), db: Session = Depends(get_db)) -> dict[str, object]:
        """获取用户的五维能力画像"""
        latest = db.scalar(
            select(AssessmentResult)
            .where(AssessmentResult.owner_id == ownerId)
            .order_by(AssessmentResult.created_at.desc())
        )
        if not latest:
            return {"profile": None, "message": "尚未完成测评"}
        from ..ability_profile import ABILITY_DIMENSIONS, DIMENSION_DESCRIPTIONS, DIMENSION_SUGGESTIONS, normalize_profile_scores, normalize_dim_key
        scores = normalize_profile_scores(json.loads(latest.ability_profile_json))
        weak = [normalize_dim_key(d) for d in json.loads(latest.weak_dimensions_json)]
        return {
            "profile": {
                "scores": scores,
                "weakDimensions": weak,
                "overallScore": round(sum(scores.values()) / len(ABILITY_DIMENSIONS)),
                "descriptions": DIMENSION_DESCRIPTIONS,
                "suggestions": DIMENSION_SUGGESTIONS,
            },
            "assessmentTime": latest.created_at.isoformat(),
        }


