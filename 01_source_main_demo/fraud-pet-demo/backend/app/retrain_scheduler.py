"""错题复训调度器 — 按间隔安排变式复训。

间隔策略（基于遗忘曲线）：
  第1次复训：24小时后
  第2次复训：3天后
  第3次复训：7天后
"""

from __future__ import annotations

from datetime import datetime, timedelta

# 复训间隔
RETRAIN_INTERVALS = [
    timedelta(hours=24),
    timedelta(days=3),
    timedelta(days=7),
]

# 变式生成策略
VARIANT_STRATEGIES = {
    1: "change_options_order",  # 改变选项顺序
    2: "change_scenario_detail",  # 改变场景细节
    3: "change_question_type",  # 改变提问方式
}


def schedule_retrain(
    wrong_items: list[dict],
    training_record_created_at: datetime,
) -> list[dict]:
    """为每道错题生成3次变式复训任务。

    Args:
        wrong_items: [{"questionId": "q1", "taskId": "brushing", "fraudType": "刷单返利", "abilityDim": "识诈力"}, ...]
        training_record_created_at: 训练记录创建时间

    Returns:
        [
            {
                "originalQuestionId": "q1",
                "originalTaskId": "brushing",
                "fraudType": "刷单返利",
                "targetAbility": "识诈力",
                "attempt": 1,
                "scheduledAt": "2026-07-23T12:00:00",
                "status": "pending",
                "variantStrategy": "change_options_order",
            },
            ...
        ]
    """
    retrain_tasks = []

    for item in wrong_items:
        for i, interval in enumerate(RETRAIN_INTERVALS):
            attempt = i + 1
            retrain_tasks.append({
                "originalQuestionId": item.get("questionId", ""),
                "originalTaskId": item.get("taskId", ""),
                "fraudType": item.get("fraudType", ""),
                "targetAbility": item.get("abilityDim", "识诈力"),
                "attempt": attempt,
                "scheduledAt": (training_record_created_at + interval).isoformat(),
                "status": "pending",
                "variantStrategy": VARIANT_STRATEGIES.get(attempt, "change_options_order"),
            })

    return retrain_tasks


def get_due_retrains(scheduled_items: list[dict], now: datetime | None = None) -> list[dict]:
    """获取已到期的复训任务。

    Args:
        scheduled_items: schedule_retrain 返回的任务列表
        now: 当前时间（默认 UTC now）

    Returns:
        已到期且状态为 pending 的任务列表
    """
    now = now or datetime.utcnow()
    due = []
    for item in scheduled_items:
        if item.get("status") != "pending":
            continue
        scheduled_at = datetime.fromisoformat(item["scheduledAt"])
        if scheduled_at <= now:
            due.append(item)
    return due


def generate_variant_question(original: dict, strategy: str) -> dict:
    """根据策略生成变式题。

    规则引擎实现，不依赖 LLM。
    LLM 增强可在 ai_service 中实现。

    Args:
        original: 原始题目 {"id": "q1", "stem": "...", "options": ["A", "B", "C", "D"], "correctAnswer": ["A"], ...}
        strategy: "change_options_order" | "change_scenario_detail" | "change_question_type"

    Returns:
        变式题目（带新 id 和 variant_of 字段）
    """
    import json
    import uuid

    variant = json.loads(json.dumps(original, ensure_ascii=False))  # 深拷贝
    variant["id"] = f"{original.get('id', 'q')}-v{uuid.uuid4().hex[:4]}"
    variant["variant_of"] = original.get("id", "")
    variant["variant_strategy"] = strategy

    if strategy == "change_options_order":
        # 打乱选项顺序
        options = variant.get("options", [])
        correct = set(variant.get("correctAnswer", []))
        correct_texts = [opt for opt in options if opt in correct]
        wrong_texts = [opt for opt in options if opt not in correct]

        import random
        random.shuffle(wrong_texts)
        new_options = correct_texts + wrong_texts
        random.shuffle(new_options)
        variant["options"] = new_options
        variant["correctAnswer"] = correct_texts  # 保持答案文本不变

    elif strategy == "change_scenario_detail":
        # 修改场景细节（金额、平台名等）
        import re
        stem = variant.get("stem", "")
        # 替换金额
        stem = re.sub(r"\d+元", lambda m: f"{int(m.group()[:-1]) * 2}元", stem)
        variant["stem"] = stem

    elif strategy == "change_question_type":
        # 将单选改为多选或反向提问
        if variant.get("questionType") == "single":
            variant["questionType"] = "multiple"
            variant["stem"] = "以下哪些是" + variant.get("stem", "").replace("以下哪个是", "")
        elif variant.get("questionType") == "multiple":
            variant["questionType"] = "single"
            variant["stem"] = "以下哪个是" + variant.get("stem", "").replace("以下哪些是", "")

    return variant
