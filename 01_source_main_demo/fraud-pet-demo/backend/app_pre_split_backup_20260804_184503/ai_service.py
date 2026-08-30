"""AI 服务层 — 统一 AI 调用入口，支持 LLM 接入和规则降级。

架构：
  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
  │  业务层      │────▶│  AIService   │────▶│  LLM Client  │
  │  (main.py)  │     │  (本文件)     │     │  (可选)      │
  └─────────────┘     └──────┬───────┘     └──────────────┘
                             │ 失败时降级
                             ▼
                      ┌──────────────┐
                      │  RuleEngine  │
                      │  (规则降级)   │
                      └──────────────┘

LLM 接入方式（通过环境变量配置）：
  LLM_API_KEY  — API 密钥
  LLM_BASE_URL — API 地址（OpenAI 兼容格式）
  LLM_MODEL    — 模型名称

如果未配置 API Key，所有 AI 功能自动降级到规则引擎。
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from .ai_logger import AICallTimer, log_ai_call
from .prompts import get_prompt
from .safety_filter import check_output, filter_input

logger = logging.getLogger(__name__)

# Prompt 版本管理 — 从 prompts/ 目录加载
def _init_prompt_versions() -> dict[str, str]:
    """从 prompts/ 目录加载所有提示词版本号。"""
    versions = {}
    for name in ("dialogue", "risk_analysis", "task_planning", "review"):
        try:
            _, ver = get_prompt(name)
            versions[name] = ver
        except FileNotFoundError:
            versions[name] = "v1.0"  # 回退到硬编码版本
    return versions

PROMPT_VERSIONS = _init_prompt_versions()

# 当前模型信息
MODEL_NAME = os.getenv("LLM_MODEL", "rule-engine")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")


def is_llm_available() -> bool:
    """检查 LLM 是否可用（配置了 API Key 和 Base URL）。"""
    return bool(LLM_API_KEY and LLM_BASE_URL)


async def _call_llm(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> dict[str, Any] | None:
    """调用 LLM API（OpenAI 兼容格式）。

    返回:
        {"content": "模型回复", "tokens": 123} 或 None（失败时）
    """
    if not is_llm_available():
        return None

    try:
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)

        # 输出安全审查
        check = check_output(content)
        if not check.is_safe:
            return {"content": check.safe_output, "tokens": tokens, "safety_blocked": True}

        return {"content": content, "tokens": tokens, "safety_blocked": False}
    except Exception as e:
        logger.warning("LLM call failed: %s", e)
        return None


class AIService:
    """统一 AI 服务入口"""

    @staticmethod
    async def dialogue(
        db,
        *,
        scenario_type: str,
        current_state: str,
        state_prompt: str,
        user_message: str,
        conversation_history: list[dict],
    ) -> dict[str, Any]:
        """AI 对话 — 生成骗子角色的回复。

        降级策略：回退到 scenario_state_machine 中的预脚本回复。
        """
        timer = AICallTimer()
        timer.__enter__()

        input_summary = f"[{scenario_type}] 状态:{current_state} 用户:{user_message[:50]}"
        filter_result = filter_input(user_message)

        # 尝试 LLM
        if is_llm_available():
            system_prompt, _ = get_prompt("dialogue")
            system_prompt = system_prompt.format(
                scenario_type=scenario_type,
                current_state=current_state,
                state_prompt=state_prompt,
            )

            result = await _call_llm(
                system_prompt,
                filter_result.safe_text,
                temperature=0.8,
                max_tokens=200,
            )

            if result:
                timer.__exit__()
                output = {
                    "reply": result["content"],
                    "source": "ai",
                    "state": current_state,
                }
                log_ai_call(
                    db,
                    call_type="dialogue",
                    model_name=MODEL_NAME,
                    prompt_version=PROMPT_VERSIONS["dialogue"],
                    input_summary=input_summary,
                    output_struct=output,
                    token_usage=result.get("tokens", 0),
                    response_time_ms=timer.elapsed_ms,
                    safety_blocked=result.get("safety_blocked", False),
                    fallback_used=False,
                )
                return output

        # 降级：返回规则引擎回复（根据用户行为选择更贴切的话术）
        from .scenario_state_machine import get_fallback_reply, classify_user_behavior

        timer.__exit__()
        user_behavior = classify_user_behavior(filter_result.safe_text)
        fallback_reply = get_fallback_reply(scenario_type, current_state, user_behavior, filter_result.safe_text)
        output = {
            "reply": fallback_reply,
            "source": "rule",
            "state": current_state,
        }
        log_ai_call(
            db,
            call_type="dialogue",
            model_name="rule-engine",
            prompt_version=PROMPT_VERSIONS["dialogue"],
            input_summary=input_summary,
            output_struct=output,
            response_time_ms=timer.elapsed_ms,
            fallback_used=True,
        )
        return output

    @staticmethod
    async def analyze_risk(db, *, text: str) -> dict[str, Any]:
        """AI 增强风险分析。

        降级策略：回退到 rules.analyze_text 的纯规则分析。
        """
        from .rules import analyze_text

        timer = AICallTimer()
        timer.__enter__()

        filter_result = filter_input(text)
        rule_result = analyze_text(filter_result.safe_text)

        # 尝试 LLM 增强
        if is_llm_available():
            system_prompt, _ = get_prompt("risk_analysis")

            result = await _call_llm(
                system_prompt,
                f"请分析以下文本：\n{filter_result.safe_text}",
                temperature=0.3,
                max_tokens=300,
            )

            if result:
                timer.__exit__()
                try:
                    ai_analysis = json.loads(result["content"])
                except (json.JSONDecodeError, KeyError):
                    ai_analysis = {"aiExplanation": result["content"], "confidence": 0.5}

                output = {
                    **rule_result,
                    "aiAnalysis": ai_analysis,
                    "source": "ai",
                }
                log_ai_call(
                    db,
                    call_type="risk_analysis",
                    model_name=MODEL_NAME,
                    prompt_version=PROMPT_VERSIONS["risk_analysis"],
                    input_summary=filter_result.safe_text[:200],
                    output_struct=output,
                    token_usage=result.get("tokens", 0),
                    response_time_ms=timer.elapsed_ms,
                    fallback_used=False,
                )
                return output

        # 降级：纯规则
        timer.__exit__()
        output = {**rule_result, "source": "rule"}
        log_ai_call(
            db,
            call_type="risk_analysis",
            model_name="rule-engine",
            prompt_version=PROMPT_VERSIONS["risk_analysis"],
            input_summary=filter_result.safe_text[:200],
            output_struct=output,
            response_time_ms=timer.elapsed_ms,
            fallback_used=True,
        )
        return output

    @staticmethod
    async def generate_task_package(db, *, ability_profile: dict, plan_type: str) -> dict[str, Any]:
        """AI 任务包生成 — 生成个性化训练计划描述。

        降级策略：回退到 task_planner 中的规则生成。
        """
        from .task_planner import generate_plan_rule

        timer = AICallTimer()
        timer.__enter__()

        # 规则引擎先生成结构化计划
        plan = generate_plan_rule(ability_profile, plan_type)

        # 尝试 LLM 生成个性化描述
        if is_llm_available():
            weak_dims = ability_profile.get("weakDimensions", [])
            system_prompt, _ = get_prompt("task_planning")
            system_prompt = system_prompt.format(
                ability_scores=json.dumps(ability_profile.get('scores', {}), ensure_ascii=False),
                weak_dimensions=', '.join(weak_dims) if weak_dims else '无',
            )

            result = await _call_llm(system_prompt, f"计划类型：{plan_type}", temperature=0.7, max_tokens=100)

            if result:
                timer.__exit__()
                plan["motivationText"] = result["content"]
                plan["source"] = "ai"
                log_ai_call(
                    db,
                    call_type="task_planning",
                    model_name=MODEL_NAME,
                    prompt_version=PROMPT_VERSIONS["task_planning"],
                    input_summary=f"weak={weak_dims}, plan={plan_type}",
                    output_struct={"motivationText": result["content"], "items": len(plan.get("items", []))},
                    token_usage=result.get("tokens", 0),
                    response_time_ms=timer.elapsed_ms,
                    fallback_used=False,
                )
                return plan

        # 降级
        timer.__exit__()
        weak = ability_profile.get("weakDimensions", [])
        plan["motivationText"] = f"你的薄弱维度是{'、'.join(weak)}，坚持训练，每天进步一点点！"
        plan["source"] = "rule"
        log_ai_call(
            db,
            call_type="task_planning",
            model_name="rule-engine",
            prompt_version=PROMPT_VERSIONS["task_planning"],
            input_summary=f"weak={weak}, plan={plan_type}",
            output_struct={"items": len(plan.get("items", []))},
            response_time_ms=timer.elapsed_ms,
            fallback_used=True,
        )
        return plan

    @staticmethod
    async def generate_review(db, *, session_data: dict) -> dict[str, Any]:
        """AI 复盘生成 — 生成训练复盘总结。

        降级策略：回退到 review_engine 的模板生成。
        """
        from .review_engine import generate_review_rule

        timer = AICallTimer()
        timer.__enter__()

        # 规则引擎先生成结构化复盘
        review = generate_review_rule(session_data)

        # 尝试 LLM 生成个性化复盘总结
        if is_llm_available():
            system_prompt, _ = get_prompt("review")

            summary_input = json.dumps(
                {
                    "fraudType": session_data.get("fraudType"),
                    "identifiedEvidence": session_data.get("identifiedEvidence", []),
                    "missedEvidence": session_data.get("missedEvidence", []),
                    "userBehaviors": session_data.get("userBehaviors", []),
                },
                ensure_ascii=False,
            )

            result = await _call_llm(system_prompt, summary_input, temperature=0.6, max_tokens=150)

            if result:
                timer.__exit__()
                review["reviewSummary"] = result["content"]
                review["source"] = "ai"
                log_ai_call(
                    db,
                    call_type="review",
                    model_name=MODEL_NAME,
                    prompt_version=PROMPT_VERSIONS["review"],
                    input_summary=summary_input[:200],
                    output_struct=review,
                    token_usage=result.get("tokens", 0),
                    response_time_ms=timer.elapsed_ms,
                    fallback_used=False,
                )
                return review

        # 降级
        timer.__exit__()
        review["source"] = "rule"
        log_ai_call(
            db,
            call_type="review",
            model_name="rule-engine",
            prompt_version=PROMPT_VERSIONS["review"],
            input_summary=json.dumps({"fraudType": session_data.get("fraudType")}, ensure_ascii=False)[:200],
            output_struct=review,
            response_time_ms=timer.elapsed_ms,
            fallback_used=True,
        )
        return review
