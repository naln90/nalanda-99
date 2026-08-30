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


router = APIRouter(prefix="/api/risk", tags=["risk"])

@router.post("/analyze")

def risk_analyze(payload: RiskAnalyzeRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
        # 软绑定身份：携带合法 Bearer Token 时以 Token 对应 owner 为准，防止伪造 ownerId（A18）
        owner_id = resolve_owner_id(request, db, payload.ownerId)
        result = analyze_text(payload.text)
        pet = get_pet(db, owner_id)
        # 并发安全：同一进程内多线程并发提交时，用锁保证「校验今日次数 + 发奖 + 落库」原子，避免重复发奖（A14）
        with _award_lock:
            checks_today = [
                check
                for check in db.scalars(
                    select(SuspiciousCheck).where(
                        SuspiciousCheck.owner_id == owner_id,
                        SuspiciousCheck.reward_status == "AWARDED",
                    )
                ).all()
                if same_day(check.created_at)
            ]
            growth_awarded = 10 if pet and len(checks_today) < get_rule_value(db, "suspiciousCheckDailyLimit", SUSPICIOUS_CHECK_DAILY_LIMIT) else 0
            reward_status = "AWARDED" if growth_awarded else "NO_REWARD"
            if pet:
                apply_growth(pet, growth_awarded)
            check = SuspiciousCheck(
                owner_id=owner_id,
                input_text_masked=mask_text(payload.text),
                fraud_type=str(result["fraudType"]),
                risk_score=int(result["riskScore"]),
                risk_level=str(result["riskLevel"]),
                evidence_json=json.dumps(result["evidence"], ensure_ascii=False),
                suggestions_json=json.dumps(result["suggestions"], ensure_ascii=False),
                growth_awarded=growth_awarded,
                reward_status=reward_status,
            )
            db.add(check)
            db.commit()
        response = dict(result)
        response.update({"growthAwarded": growth_awarded, "rewardStatus": reward_status})
        return response


@router.post("/analyze-ai")

def risk_analyze_ai(payload: RiskAnalyzeRequest, db: Session = Depends(get_db)) -> dict[str, object]:
        """AI 增强风险分析（规则引擎 + LLM 语义理解）"""
        # 使用规则引擎（同步，不依赖 AI）
        result = analyze_text(payload.text)
        pet = get_pet(db, payload.ownerId)
        growth_awarded = 10 if pet else 0

        return {**result, "growthAwarded": growth_awarded, "source": "rule"}


@router.get("/emergency-stop-loss/types")

def emergency_stop_loss_types() -> dict[str, object]:
        """获取所有可选的危险行为类型"""
        from ..emergency_stop_loss import get_all_risk_types
        return {"riskTypes": get_all_risk_types()}


@router.post("/emergency-stop-loss")

def emergency_stop_loss(payload: EmergencyStopLossRequest) -> dict[str, object]:
        """根据危险行为生成止损清单"""
        from ..emergency_stop_loss import get_stop_loss_checklist
        result = get_stop_loss_checklist(payload.selectedRisks)
        return result


