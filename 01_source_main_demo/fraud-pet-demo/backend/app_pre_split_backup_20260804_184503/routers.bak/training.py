"""训练与情景对话训练路由（v0 与 v1）。

v0：传统训练任务提交与 AI 情景对话（/api/training/*）。
v1：状态机驱动的纯规则情景训练（/api/v1/training/*）。
"""

from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..ai_service import AIService, is_llm_available
from ..auth import resolve_owner_id
from ..database import get_db, get_submit_lock
from ..models import (
    AbilityEvent,
    AbilitySnapshot,
    EvidenceRecord,
    Pet,
    RetrainTask,
    ReviewReport,
    ScenarioTrainingSession,
    TrainingQuestion,
    TrainingRecord,
    TrainingTask,
)
from ..rules import DAILY_MAX_GROWTH, TASK_MAX_GROWTH, training_growth
from ..schemas import (
    ScenarioFinishRequest,
    ScenarioReplyRequest,
    ScenarioReplyV1Request,
    ScenarioStartRequest,
    ScenarioStartV1Request,
    TrainingSubmitRequest,
)
from ..seed import pet_to_response
from ..services import (
    apply_growth,
    awarded_training_today,
    daily_awarded_growth,
    get_or_create_user,
    get_pet,
    get_rule_value,
    normalize_answer,
    score_answers,
    task_to_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training", tags=["training"])
router_v1 = APIRouter(prefix="/api/v1/training", tags=["training-v1"])


@router.get("/tasks")
def training_tasks(db: Session = Depends(get_db)) -> dict[str, object]:
    tasks = db.scalars(select(TrainingTask).where(TrainingTask.enabled.is_(True)).order_by(TrainingTask.id)).all()
    return {"tasks": [task_to_response(task) for task in tasks]}


@router.get("/tasks/{task_id}")
def training_task(task_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    task = db.get(TrainingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")
    from ..scenarios import scenario_response

    questions = db.scalars(
        select(TrainingQuestion).where(TrainingQuestion.task_id == task_id).order_by(TrainingQuestion.id)
    ).all()
    return {
        "task": task_to_response(task),
        "scenario": scenario_response(task_id, task.fraud_type),
        "questions": [
            {
                "id": question.id,
                "questionType": question.question_type,
                "stem": question.stem,
                "options": json.loads(question.options_json),
                "correctAnswer": json.loads(question.correct_answer_json),
                "explanation": question.explanation,
            }
            for question in questions
        ],
    }


@router.post("/submit")
def submit_training(payload: TrainingSubmitRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    # 软绑定身份：携带合法 Bearer Token 时以 Token 对应 owner 为准，防止伪造 ownerId（A18）
    owner_id = resolve_owner_id(request, db, payload.ownerId)
    user = get_or_create_user(db, owner_id)
    pet = get_pet(db, owner_id)
    if not pet or not user.has_pet:
        raise HTTPException(status_code=409, detail="Claim a pet before training")
    task = db.get(TrainingTask, payload.taskId)
    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")

    accuracy = score_answers(db, payload.taskId, payload.answers)
    score = round(accuracy * 100)
    growth = training_growth(
        task.max_reward,
        task.difficulty,
        accuracy,
        get_rule_value(db, "taskMaxGrowth", TASK_MAX_GROWTH),
    )
    reward_status = "AWARDED"
    reward_message = "本次训练已完成，成长值已发放"

    # 并发安全：同一进程内多线程同时提交同一用户训练时，用进程内锁保证
    # 「幂等校验 + 发奖 + 落库」原子执行，避免重复发奖（边界/健壮性 A14）
    with get_submit_lock():
        if awarded_training_today(db, owner_id, payload.taskId):
            growth["finalGrowth"] = 0
            reward_status = "NO_REWARD"
            reward_message = "本次已完成学习，但重复完成同一任务不再增加成长值"
        else:
            remaining = max(0, get_rule_value(db, "dailyMaxGrowth", DAILY_MAX_GROWTH) - daily_awarded_growth(db, owner_id))
            if remaining <= 0:
                growth["finalGrowth"] = 0
                reward_status = "NO_REWARD"
                reward_message = "本次已完成学习，但今日奖励已达上限，不再增加成长值"
            elif growth["finalGrowth"] > remaining:
                growth["finalGrowth"] = remaining
                reward_message = "本次训练已完成，成长值按今日上限发放"

        apply_growth(pet, growth["finalGrowth"])
        record = TrainingRecord(
            owner_id=owner_id,
            pet_id=pet.pet_id,
            task_id=payload.taskId,
            mode=payload.mode,
            score=score,
            accuracy=accuracy,
            difficulty=task.difficulty,
            base_points=growth["basePoints"],
            accuracy_bonus=growth["accuracyBonus"],
            difficulty_bonus=growth["difficultyBonus"],
            final_growth=growth["finalGrowth"],
            reward_status=reward_status,
            reward_message=reward_message,
        )
        db.add(record)
        db.flush()  # 确保 record.created_at 可用
        db.commit()  # 锁内提交，保证并发请求立即看到本次发奖，杜绝重复发奖
        db.refresh(pet)

    # 生成错题复训任务（P1-1：复训触发）—— 在锁外执行，避免长事务占用锁
    from ..retrain_scheduler import schedule_retrain

    questions = db.scalars(select(TrainingQuestion).where(TrainingQuestion.task_id == payload.taskId)).all()
    provided = {answer.questionId: normalize_answer(answer.answer) for answer in payload.answers}
    wrong_items = []
    for question in questions:
        correct_answer = normalize_answer(json.loads(question.correct_answer_json))
        if provided.get(question.id, set()) != correct_answer:
            wrong_items.append({
                "questionId": question.id,
                "taskId": payload.taskId,
                "fraudType": task.fraud_type,
                "abilityDim": getattr(question, "ability_dim", "识诈力"),
            })

    if wrong_items:
        retrain_tasks = schedule_retrain(wrong_items, record.created_at)
        for rt in retrain_tasks:
            existing = db.scalar(
                select(RetrainTask).where(
                    RetrainTask.owner_id == owner_id,
                    RetrainTask.original_question_id == rt["originalQuestionId"],
                    RetrainTask.attempt == rt["attempt"],
                )
            )
            if not existing:
                retrain_task = RetrainTask(
                    owner_id=owner_id,
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
        db.commit()  # 持久化复训任务

    db.refresh(pet)

    retrain_count = len(wrong_items) * 3 if wrong_items else 0
    return {
        "score": score,
        "accuracy": accuracy,
        "growth": growth,
        "rewardStatus": reward_status,
        "rewardMessage": reward_message,
        "pet": pet_to_response(pet),
        "retrainScheduled": retrain_count,
    }


# ---------- Scenario Training (AI Dialogue) ----------
@router.post("/scenario/start")
def start_scenario(payload: ScenarioStartRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """开始一场 AI 情景对话训练"""
    from ..scenario_state_machine import (
        SCENARIO_FSM,
        get_all_evidence,
        get_fallback_reply,
        get_state_prompt,
    )

    task = db.get(TrainingTask, payload.taskId)
    if not task:
        raise HTTPException(status_code=404, detail="Training task not found")

    # 找到匹配的状态机类型
    fraud_type = task.fraud_type
    scenario_type = None
    for st in SCENARIO_FSM:
        if fraud_type in st or st in fraud_type:
            scenario_type = st
            break
    if not scenario_type:
        scenario_type = "刷单返利"  # 默认

    session_id = f"scn-{secrets.token_hex(8)}"

    # 初始消息：骗子开场白
    initial_state = "S0"
    fallback = get_fallback_reply(scenario_type, initial_state)

    # 创建会话
    now = datetime.utcnow()
    initial_messages = [
        {"role": "system", "content": f"情景训练开始：{scenario_type}", "state": initial_state, "timestamp": now.isoformat()},
        {"role": "scammer", "content": fallback, "state": initial_state, "timestamp": now.isoformat()},
    ]

    session = ScenarioTrainingSession(
        id=session_id,
        owner_id=payload.ownerId,
        task_id=payload.taskId,
        fraud_type=scenario_type,
        current_state=initial_state,
        messages_json=json.dumps(initial_messages, ensure_ascii=False),
        identified_evidence_json="[]",
        user_behaviors_json="[]",
        ai_enabled=is_llm_available(),  # 自动检测 LLM 可用性
        started_at=now,
    )
    db.add(session)
    db.commit()

    return {
        "sessionId": session_id,
        "scenarioType": scenario_type,
        "currentState": initial_state,
        "stateName": get_state_prompt(scenario_type, initial_state),
        "initialMessage": fallback,
        "allEvidence": get_all_evidence(scenario_type),
    }


@router.post("/scenario/{session_id}/reply")
async def scenario_reply(session_id: str, payload: ScenarioReplyRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """用户回复一轮 — 推进状态机，返回骗子回复（LLM 增强 or 规则降级）。"""
    from ..scenario_state_machine import (
        classify_user_behavior,
        get_all_evidence,
        get_fallback_reply,
        get_state_name,
        get_state_prompt,
        transition,
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

    # 生成骗子回复 — 优先尝试 LLM，失败时降级到规则
    scammer_reply = get_fallback_reply(session.fraud_type, new_state, behavior, payload.message)
    reply_source = "rule"

    if session.ai_enabled and not is_terminal:
        # 构建对话历史供 AI 参考
        state_prompt = get_state_prompt(session.fraud_type, new_state)
        conversation_history = json.loads(session.messages_json)
        messages_for_ai = [
            {"role": m["role"], "content": m.get("content", "")}
            for m in conversation_history[-6:]  # 最近6轮
        ]
        try:
            ai_result = await AIService.dialogue(
                db,
                scenario_type=session.fraud_type,
                current_state=new_state,
                state_prompt=state_prompt,
                user_message=payload.message,
                conversation_history=messages_for_ai,
            )
            if ai_result and ai_result.get("reply"):
                scammer_reply = ai_result["reply"]
                reply_source = ai_result.get("source", "ai")
        except Exception:
            logger.exception("scenario_reply: AI dialogue failed, falling back to rule engine")

    # 更新消息列表
    messages = json.loads(session.messages_json)
    now = datetime.utcnow()
    messages.append({"role": "user", "content": payload.message, "behavior": behavior, "timestamp": now.isoformat()})
    if not is_terminal:
        messages.append({"role": "scammer", "content": scammer_reply, "source": reply_source, "state": new_state, "timestamp": now.isoformat()})
        # 反诈守护者提示
        messages.append({"role": "guardian", "content": "【反诈守护者提示】请思考对方话术中的风险信号，及时识别并拒绝。", "timestamp": now.isoformat()})
    else:
        messages.append({"role": "system", "content": "恭喜！你成功识破了诈骗骗局！", "timestamp": now.isoformat()})

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
        "replySource": reply_source,
        "identifiedEvidence": identified,
        "newEvidence": new_evidence,
        "isTerminal": is_terminal,
        "isCompleted": session.status == "completed",
    }


@router.post("/scenario/{session_id}/finish")
async def scenario_finish(session_id: str, payload: ScenarioFinishRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """结束对话训练 — 生成复盘报告（AI 增强 or 规则降级）。"""
    from ..review_engine import generate_review_rule
    from ..retrain_scheduler import schedule_retrain

    session = db.get(ScenarioTrainingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 强制结束
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.commit()

    # 生成复盘报告 — 优先 AI
    session_data = {
        "fraudType": session.fraud_type,
        "scenarioType": session.fraud_type,
        "finalState": session.current_state,
        "identifiedEvidence": json.loads(session.identified_evidence_json),
        "userBehaviors": json.loads(session.user_behaviors_json),
        "messages": json.loads(session.messages_json),
    }

    review = None
    if session.ai_enabled:
        try:
            review = await AIService.generate_review(db, session_data=session_data)
        except Exception:
            logger.exception("scenario_review: AI review generation failed, falling back to rule engine")

    if not review:
        review = generate_review_rule(session_data)

    # 生成错题复训任务 — 情景训练结束也触发复训
    missed_evidence = review.get("missedEvidence", [])
    if missed_evidence:
        wrong_items = [{
            "questionId": f"scn-{session.id}",
            "taskId": session.task_id or "",
            "fraudType": session.fraud_type,
            "abilityDim": "识诈力",
        }]
        retrain_tasks = schedule_retrain(wrong_items, datetime.utcnow())
        for rt in retrain_tasks:
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
    }


# ---------- v1 情景训练 (State Machine + Rule-based) ----------
@router_v1.post("/scenario/start")
def v1_start_scenario(payload: ScenarioStartV1Request, db: Session = Depends(get_db)) -> dict[str, object]:
    """v1: 以 scenarioType 直接启动情景训练，无需 TrainingTask 查找。"""
    from ..scenario_state_machine import (
        SCENARIO_FSM,
        get_all_evidence,
        get_fallback_reply,
        get_state_prompt,
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


@router_v1.post("/scenario/{session_id}/reply")
def v1_scenario_reply(session_id: str, payload: ScenarioReplyV1Request, db: Session = Depends(get_db)) -> dict[str, object]:
    """v1: FSM 推进一轮 + 保存 EvidenceRecord（Phase 1 无 AI）。"""
    from ..scenario_state_machine import (
        classify_user_behavior,
        get_fallback_reply,
        get_state_name,
        transition,
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


@router_v1.post("/scenario/{session_id}/finish")
def v1_scenario_finish(session_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    """v1: 结束训练 — 生成复盘报告 + 保存 ReviewReport + 更新能力快照。"""
    from ..ability_profile import compute_ability_profile
    from ..review_engine import generate_review_rule
    from ..retrain_scheduler import schedule_retrain

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
    new_scores: dict[str, float] = {
        dim: prev_scores.get(dim, 0.0) for dim in ["识诈力", "判断力", "应对力", "证据力", "求助力"]
    }
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


@router_v1.get("/scenario/sessions/{session_id}")
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
