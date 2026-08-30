from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
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
from ..helpers import _NUMERIC_RULE_KEYS
from ..assessment_service import *
from ..ability_profile import *
from ..retrain_scheduler import *
from ..task_planner import *
from ..scenario_state_machine import *
from ..review_engine import *
from ..emergency_stop_loss import *
from ..ai_logger import *


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/cases")

def admin_cases(db: Session = Depends(get_db), admin_auth: None = Depends(require_admin_key)) -> dict[str, object]:
        cases = db.scalars(select(FraudCase).order_by(FraudCase.created_at.desc())).all()
        return {
            "cases": [
                {
                    "id": case.id,
                    "title": case.title,
                    "fraudType": case.fraud_type,
                    "sourceChannel": case.source_channel,
                    "riskLevel": case.risk_level,
                    "aiConfidence": case.ai_confidence,
                    "desensitized": case.desensitized,
                    "status": case.status,
                    "summary": case.summary,
                    "riskTags": json.loads(case.risk_tags_json),
                }
                for case in cases
            ]
        }


@router.post("/cases")

def admin_create_case(payload: CaseCreateRequest, db: Session = Depends(get_db), admin_auth: None = Depends(require_admin_key)) -> dict[str, object]:
        case_id = f"case-{int(datetime.utcnow().timestamp())}"
        risk = analyze_text(f"{payload.title} {payload.summary}")
        case = FraudCase(
            id=case_id,
            title=payload.title,
            fraud_type=payload.fraudType,
            source_channel=payload.sourceChannel,
            risk_level=payload.riskLevel,
            ai_confidence=0.75,
            desensitized=True,
            status="待解析",
            summary=payload.summary,
            risk_tags_json=json.dumps(risk["evidence"], ensure_ascii=False),
        )
        db.add(case)
        db.commit()
        return {"caseId": case.id, "status": case.status}


@router.post("/cases/{case_id}/analyze")

def admin_analyze_case(case_id: str, db: Session = Depends(get_db), admin_auth: None = Depends(require_admin_key)) -> dict[str, object]:
        case = db.get(FraudCase, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        risk = analyze_text(f"{case.title} {case.summary}")
        case.status = "已解析"
        case.risk_level = str(risk["riskLevel"])
        case.fraud_type = str(risk["fraudType"])
        case.risk_tags_json = json.dumps(risk["evidence"], ensure_ascii=False)
        db.commit()
        return {"caseId": case.id, "riskElements": risk["evidence"], "recommendedQuestionTypes": ["单选题", "多选题", "情景判断"]}


@router.post("/cases/{case_id}/generate-questions")

def admin_generate_questions(case_id: str, db: Session = Depends(get_db), admin_auth: None = Depends(require_admin_key)) -> dict[str, object]:
        case = db.get(FraudCase, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        case.status = "已生成训练题"
        db.commit()
        return {
            "caseId": case.id,
            "questions": [
                {
                    "stem": "本案例中最需要警惕的风险信号是什么？",
                    "options": ["A. 要求转账", "B. 拒绝核验", "C. 制造紧急压力", "D. 以上都是"],
                    "correctAnswer": "D",
                }
            ],
        }


@router.get("/rules")

def admin_rules(db: Session = Depends(get_db), admin_auth: None = Depends(require_admin_key)) -> dict[str, object]:
        rules = db.scalars(select(GrowthRule).order_by(GrowthRule.rule_key)).all()
        return {
            "rules": {rule.rule_key: rule.rule_value for rule in rules},
            "complianceNotice": COMPLIANCE_NOTICE,
        }


@router.put("/rules")

def admin_save_rules(payload: dict[str, Any], db: Session = Depends(get_db), admin_auth: None = Depends(require_admin_key)) -> dict[str, object]:
        invalid: list[str] = []
        for key, value in payload.items():
            # 数值型规则做边界校验，避免脏数据导致后续 int() 解析失败
            if key in _NUMERIC_RULE_KEYS:
                try:
                    int(str(value))
                except (ValueError, TypeError):
                    invalid.append(key)
                    continue
            rule = db.scalar(select(GrowthRule).where(GrowthRule.rule_key == key))
            if rule:
                rule.rule_value = str(value)
            else:
                db.add(GrowthRule(rule_key=key, rule_value=str(value), description="管理端新增规则"))
        db.commit()
        return {"saved": True, "invalid": invalid}


