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


router = APIRouter(prefix="/api/v1/training", tags=["v1_training"])

@router.post("/scenario/start")

def v1_start_scenario(payload: ScenarioStartV1Request, db: Session = Depends(get_db)) -> dict[str, object]:
        """v1: 以 scenarioType 直接启动情景训练，无需 TrainingTask 查找。"""
        from ..scenario_state_machine import (
            SCENARIO_FSM,
            get_fallback_reply,
            get_state_prompt,
            get_all_evidence,
        )

        # 校验 scenario_type 是否支持
        if payload.scenarioType not in SCENARIO_FSM:
            valid = list(SCENARIO_FSM.keys())
            raise HTTPException(
                status_code=400,
                detail=f"不支持的情景类型：{payload.scenarioType}。支持的类型：{', '.join(valid)}",
            )

        session_id = f"scn-{secrets.token_hex(8)}"
        initial_state = "S0"
        fallback = get_fallback_reply(payload.scenarioType, initial_state)

        now = datetime.utcnow()
        initial_messages = [
            {
                "role": "system",
                "content": f"情景训练开始：{payload.scenarioType}",
                "state": initial_state,
                "timestamp": now.isoformat(),
            },
            {
                "role": "scammer",
                "content": fallback,
                "state": initial_state,
                "timestamp": now.isoformat(),
            },
        ]

        session = ScenarioTrainingSession(
            id=session_id,
            owner_id=payload.ownerId,
            task_id=f"v1-{payload.scenarioType}",
            fraud_type=payload.scenarioType,
            current_state=initial_state,
            messages_json=json.dumps(initial_messages, ensure_ascii=False),
            identified_evidence_json="[]",
            user_behaviors_json="[]",
            ai_enabled=False,  # Phase 1 全部规则驱动
            started_at=now,
        )
        db.add(session)
        db.commit()

        return {
            "sessionId": session_id,
            "scenarioType": payload.scenarioType,
            "currentState": initial_state,
            "stateName": get_state_prompt(payload.scenarioType, initial_state),
            "initialMessage": fallback,
            "allEvidence": get_all_evidence(payload.scenarioType),
        }


@router.post("/scenario/{session_id}/reply")

def v1_scenario_reply(session_id: str, payload: ScenarioReplyV1Request, db: Session = Depends(get_db)) -> dict[str, object]:
        """v1: FSM 推进一轮 + 保存 EvidenceRecord（Phase 1 无 AI）。"""
        from ..scenario_state_machine import (
            classify_user_behavior,
            transition,
            get_state_name,
            get_fallback_reply,
        )

        session = db.get(ScenarioTrainingSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Session is not active")

        # 分类用户行为
        behavior = classify_user_behavior(payload.message)

        # 推进状态机
        result = transition(session.fraud_type, session.current_state, behavior)
        new_state = result["newState"]
        new_evidence = result["evidence"]
        is_terminal = result["isTerminal"]

        # 更新已识别证据
        identified = json.loads(session.identified_evidence_json)
        for ev in new_evidence:
            if ev not in identified:
                identified.append(ev)

        # 更新用户行为记录
        behaviors = json.loads(session.user_behaviors_json)
        behaviors.append({
            "message": payload.message[:100],
            "behavior": behavior,
            "state": session.current_state,
        })

        # 生成骗子回复 — Phase 1 使用规则兜底（按用户行为和消息内容选择话术）
        scammer_reply = get_fallback_reply(session.fraud_type, new_state, behavior, payload.message)

        # 保存 EvidenceRecord（新增识别证据）
        turn_order = len(behaviors)
        for ev in new_evidence:
            evidence_rec = EvidenceRecord(
                owner_id=session.owner_id,
                session_id=session_id,
                turn_order=turn_order,
                evidence_tag=ev,
                identified=True,
                is_key=True,
            )
            db.add(evidence_rec)

        # 更新消息列表
        messages = json.loads(session.messages_json)
        now = datetime.utcnow()
        messages.append({
            "role": "user",
            "content": payload.message,
            "behavior": behavior,
            "timestamp": now.isoformat(),
        })
        if not is_terminal:
            messages.append({
                "role": "scammer",
                "content": scammer_reply,
                "source": "rule",
                "state": new_state,
                "timestamp": now.isoformat(),
            })
            # 反诈守护者提示
            messages.append({
                "role": "guardian",
                "content": "【反诈守护者提示】请思考对方话术中的风险信号，及时识别并拒绝。",
                "timestamp": now.isoformat(),
            })
        else:
            messages.append({
                "role": "system",
                "content": "恭喜！你成功识破了诈骗骗局！",
                "timestamp": now.isoformat(),
            })

        # 更新会话
        session.current_state = new_state
        session.messages_json = json.dumps(messages, ensure_ascii=False)
        session.identified_evidence_json = json.dumps(identified, ensure_ascii=False)
        session.user_behaviors_json = json.dumps(behaviors, ensure_ascii=False)

        if is_terminal or new_state in ("S4", "S5"):
            session.status = "completed"
            session.completed_at = now

        db.commit()

        return {
            "sessionId": session_id,
            "behavior": behavior,
            "newState": new_state,
            "stateName": get_state_name(session.fraud_type, new_state),
            "scammerReply": scammer_reply if not is_terminal else "（对话已结束）",
            "replySource": "rule",
            "identifiedEvidence": identified,
            "newEvidence": new_evidence,
            "isTerminal": is_terminal,
            "isCompleted": session.status == "completed",
        }


@router.post("/scenario/{session_id}/finish")

def v1_scenario_finish(session_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
        """v1: 结束训练 — 生成复盘报告 + 保存 ReviewReport + 更新能力快照。"""
        from ..review_engine import generate_review_rule
        from ..retrain_scheduler import schedule_retrain
        from ..ability_profile import compute_ability_profile
        from sqlalchemy import desc

        session = db.get(ScenarioTrainingSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 强制结束
        now = datetime.utcnow()
        session.status = "completed"
        session.completed_at = now
        db.commit()

        # 构建 session_data 供复盘引擎使用
        session_data = {
            "fraudType": session.fraud_type,
            "scenarioType": session.fraud_type,
            "finalState": session.current_state,
            "identifiedEvidence": json.loads(session.identified_evidence_json),
            "userBehaviors": json.loads(session.user_behaviors_json),
            "messages": json.loads(session.messages_json),
        }

        # 规则引擎生成复盘报告
        review = generate_review_rule(session_data)
        dim_scores = review.get("dimScores", {})
        evidence_dim_score = dim_scores.get("evidence", float(review.get("abilityChange", {}).get("证据力", 0)))

        # 保存 ReviewReport 到数据库
        report_id = f"rpt-{secrets.token_hex(8)}"
        report = ReviewReport(
            id=report_id,
            session_id=session_id,
            owner_id=session.owner_id,
            identified_evidence_json=json.dumps(review.get("identifiedEvidence", []), ensure_ascii=False),
            missed_evidence_json=json.dumps(review.get("missedEvidence", []), ensure_ascii=False),
            correct_behaviors_json=json.dumps(
                [b.get("behavior", "") for b in review.get("correctBehaviors", [])], ensure_ascii=False
            ),
            risk_behaviors_json=json.dumps(
                [b.get("behavior", "") for b in review.get("riskyBehaviors", [])], ensure_ascii=False
            ),
            recognition_score=float(review.get("abilityChange", {}).get("识诈力", 0)),
            judgment_score=float(dim_scores.get("judgment", 0)),
            response_score=float(review.get("abilityChange", {}).get("应对力", 0)),
            evidence_score=float(evidence_dim_score),
            help_score=float(dim_scores.get("help", 0)),
            total_score=float(review.get("score", 0)),
            next_suggestions_json=json.dumps(review.get("nextSteps", []), ensure_ascii=False),
            ai_generated=False,
            created_at=now,
        )
        db.add(report)

        # 更新能力快照（基于本次训练表现）
        ability_change = review.get("abilityChange", {})
        prev_snapshot = (
            db.query(AbilitySnapshot)
            .filter(AbilitySnapshot.owner_id == session.owner_id)
            .order_by(desc(AbilitySnapshot.created_at))
            .first()
        )
        prev_scores: dict[str, float] = json.loads(prev_snapshot.scores_json) if prev_snapshot else {}

        # 计算新得分：在旧得分基础上加 abilityChange 的增量
        new_scores: dict[str, float] = {dim: prev_scores.get(dim, 0.0) for dim in ["识诈力", "判断力", "应对力", "证据力", "求助力"]}
        for dim, delta in ability_change.items():
            if dim in new_scores:
                new_scores[dim] = min(100, new_scores[dim] + float(delta))

        overall = round(sum(new_scores.values()) / 5, 1)
        weak = [dim for dim, s in new_scores.items() if s < 50]

        snapshot = AbilitySnapshot(
            owner_id=session.owner_id,
            scores_json=json.dumps(new_scores, ensure_ascii=False),
            weak_dimensions_json=json.dumps(weak, ensure_ascii=False),
            weak_types_json="[]",
            total_growth=int(sum(float(v) for v in ability_change.values())),
            trigger_event="scenario",
            trigger_ref=session_id,
        )
        db.add(snapshot)
        db.flush()  # 获取 snapshot.id

        for dim in ["识诈力", "判断力", "应对力", "证据力", "求助力"]:
            score_before = prev_scores.get(dim, 0.0)
            score_after = new_scores[dim]
            delta_val = round(score_after - score_before, 1)
            event = AbilityEvent(
                snapshot_id=snapshot.id,
                owner_id=session.owner_id,
                dim_key=dim,
                score_before=score_before,
                score_after=score_after,
                delta=delta_val,
            )
            db.add(event)

        # 精简历史快照
        all_snaps = (
            db.query(AbilitySnapshot)
            .filter(AbilitySnapshot.owner_id == session.owner_id)
            .order_by(desc(AbilitySnapshot.created_at))
            .all()
        )
        if len(all_snaps) > 30:
            keep_ids = {s.id for s in all_snaps[:30]} | {all_snaps[-1].id}
            for s in all_snaps:
                if s.id not in keep_ids:
                    db.query(AbilityEvent).filter(AbilityEvent.snapshot_id == s.id).delete()
                    db.delete(s)

        # 生成错题复训任务（基于遗漏证据）
        missed_evidence = review.get("missedEvidence", [])
        if missed_evidence:
            wrong_items = [{
                "questionId": f"scn-{session.id}",
                "taskId": session.task_id or "",
                "fraudType": session.fraud_type,
                "abilityDim": "识诈力",
            }]
            retrain_tasks_data = schedule_retrain(wrong_items, now)
            for rt in retrain_tasks_data:
                retrain_task = RetrainTask(
                    owner_id=session.owner_id,
                    original_question_id=rt["originalQuestionId"],
                    original_task_id=rt["originalTaskId"],
                    fraud_type=rt["fraudType"],
                    target_ability=rt["targetAbility"],
                    attempt=rt["attempt"],
                    scheduled_at=datetime.fromisoformat(rt["scheduledAt"]),
                    status="pending",
                    variant_strategy=rt["variantStrategy"],
                )
                db.add(retrain_task)

        db.commit()

        return {
            "sessionId": session_id,
            "review": review,
            "abilitySnapshot": {
                "scores": new_scores,
                "overall": overall,
                "weakDimensions": weak,
                "growthThisRound": int(sum(float(v) for v in ability_change.values())),
            },
        }


@router.get("/scenario/sessions/{session_id}")

def v1_get_scenario_session(session_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
        """v1: 获取情景训练会话详情（页面恢复/刷新）。"""
        session = db.get(ScenarioTrainingSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "sessionId": session.id,
            "ownerId": session.owner_id,
            "scenarioType": session.fraud_type,
            "currentState": session.current_state,
            "status": session.status,
            "messages": json.loads(session.messages_json),
            "identifiedEvidence": json.loads(session.identified_evidence_json),
            "aiEnabled": session.ai_enabled,
            "startedAt": session.started_at.isoformat(),
            "completedAt": session.completed_at.isoformat() if session.completed_at else None,
        }


