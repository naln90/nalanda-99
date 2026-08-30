"""任务包规划器 — 根据能力画像生成 7天/14天 训练计划。

规则引擎部分（固定规则）：
  - 薄弱维度优先安排对应类型训练
  - 每天不超过2个任务，总时长不超过30分钟
  - 第1天安排薄弱维度最高优先级训练
  - 第3天插入复训（如果第1天有错题）
  - 最后1天安排综合测评验证能力变化

AI 增强部分（可降级）：
  - 根据画像生成个性化任务描述和激励文案
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from .ability_profile import ABILITY_DIMENSIONS, DIMENSION_SUGGESTIONS

# 训练任务与能力维度的映射
ABILITY_TASK_MAP: dict[str, list[dict]] = {
    "识诈力": [
        {
            "taskType": "scenario", "taskRef": "brushing",
            "title": "刷单返利情景训练", "minutes": 15,
            "objective": "通过模拟刷单诈骗场景，练习识别\"高薪兼职\"\"垫付返利\"等典型话术",
            "completionCriteria": "至少完成3轮对话，正确识别2个以上风险话术",
            "acceptanceMethod": "情景对话结束后，系统根据对话中的风险识别准确率自动评分",
        },
        {
            "taskType": "scenario", "taskRef": "ai-face",
            "title": "AI换脸识别训练", "minutes": 15,
            "objective": "识别AI换脸诈骗的异常信号（视频卡顿、面部不自然、要求转账等）",
            "completionCriteria": "至少完成3轮对话，正确拒绝诈骗请求",
            "acceptanceMethod": "系统根据对话中的判断正确性自动评分",
        },
        {
            "taskType": "knowledge", "taskRef": "kb-brushing",
            "title": "刷单返利知识学习", "minutes": 10,
            "objective": "系统学习刷单返利诈骗的常见变种和识别技巧",
            "completionCriteria": "阅读全部知识卡片",
            "acceptanceMethod": "浏览时长超过10分钟即标记完成",
        },
    ],
    "判断力": [
        {
            "taskType": "scenario", "taskRef": "investment",
            "title": "虚假投资判断训练", "minutes": 15,
            "objective": "练习判断投资信息的真实性，识别\"保本高收益\"\"内部消息\"等诈骗套路",
            "completionCriteria": "完成3个以上投资场景的判断，准确率≥60%",
            "acceptanceMethod": "系统自动评分",
        },
        {
            "taskType": "assessment", "taskRef": "risk-practice",
            "title": "风险信息判断练习", "minutes": 10,
            "objective": "通过专项测评强化风险信息判断能力",
            "completionCriteria": "完成全部测评题目",
            "acceptanceMethod": "测评提交后自动评分",
        },
        {
            "taskType": "knowledge", "taskRef": "kb-investment",
            "title": "投资诈骗知识学习", "minutes": 10,
            "objective": "了解常见投资诈骗类型和防范措施",
            "completionCriteria": "阅读全部知识卡片",
            "acceptanceMethod": "浏览时长超过10分钟即标记完成",
        },
    ],
    "应对力": [
        {
            "taskType": "scenario", "taskRef": "refund",
            "title": "客服退款应对训练", "minutes": 15,
            "objective": "模拟接到冒充客服退款电话，练习正确的应对流程",
            "completionCriteria": "正确完成不转账/不验证/不共享屏幕的应对流程",
            "acceptanceMethod": "系统根据应对步骤的正确性评分",
        },
        {
            "taskType": "scenario", "taskRef": "teacher-fee",
            "title": "冒充老师应对训练", "minutes": 15,
            "objective": "识别冒充老师/辅导员收费诈骗，练习正确的核实流程",
            "completionCriteria": "完成全部对话轮次，采取正确的核实和拒绝操作",
            "acceptanceMethod": "系统自动评分",
        },
        {
            "taskType": "knowledge", "taskRef": "kb-refund",
            "title": "正确应对策略学习", "minutes": 10,
            "objective": "学习面对各类诈骗时的标准应对流程",
            "completionCriteria": "阅读全部知识卡片",
            "acceptanceMethod": "浏览时长超过10分钟即标记完成",
        },
    ],
    "证据力": [
        {
            "taskType": "assessment", "taskRef": "evidence-practice",
            "title": "证据识别练习", "minutes": 15,
            "objective": "练习识别和分类反诈关键证据（聊天记录、转账凭证、对方信息等）",
            "completionCriteria": "完成全部练习题目，准确率≥60%",
            "acceptanceMethod": "系统自动评分",
        },
        {
            "taskType": "knowledge", "taskRef": "kb-evidence",
            "title": "证据保留知识学习", "minutes": 10,
            "objective": "学习如何正确保留电子证据和纸质证据",
            "completionCriteria": "阅读全部知识卡片",
            "acceptanceMethod": "浏览时长超过10分钟即标记完成",
        },
    ],
    "求助力": [
        {
            "taskType": "knowledge", "taskRef": "kb-help",
            "title": "求助渠道知识学习", "minutes": 10,
            "objective": "了解96110反诈专线、110报警、辅导员求助等渠道的正确使用方法",
            "completionCriteria": "阅读全部知识卡片",
            "acceptanceMethod": "浏览时长超过10分钟即标记完成",
        },
        {
            "taskType": "assessment", "taskRef": "emergency-practice",
            "title": "紧急止损模拟", "minutes": 15,
            "objective": "模拟被诈骗后的紧急止损流程（冻结账户、报警、保留证据）",
            "completionCriteria": "按正确顺序完成紧急止损步骤",
            "acceptanceMethod": "系统根据止损步骤完整度评分",
        },
    ],
}

# 综合测评任务
COMPREHENSIVE_ASSESSMENT = {
    "taskType": "assessment",
    "taskRef": "final-assessment",
    "title": "综合测评 — 能力变化验证",
    "minutes": 20,
    "targetAbility": "综合",
    "objective": "完成一轮全面测评，验证训练周期内的能力提升情况",
    "completionCriteria": "完成全部测评题目",
    "acceptanceMethod": "测评提交后自动生成新的能力画像并进行前后对比",
}


def generate_plan_rule(ability_profile: dict, plan_type: str) -> dict:
    """规则引擎生成训练计划。

    Args:
        ability_profile: compute_ability_profile 的返回值
        plan_type: "7day" | "14day"

    Returns:
        {
            "planType": "7day",
            "totalDays": 7,
            "items": [
                {
                    "id": "item-xxx",
                    "dayIndex": 1,
                    "taskType": "scenario_training",
                    "taskRef": "brushing",
                    "taskTitle": "刷单返利情景训练",
                    "targetAbility": "识诈力",
                    "estimatedMinutes": 15,
                    "status": "pending",
                },
                ...
            ],
            "motivationText": "...",
        }
    """
    total_days = 7 if plan_type == "7day" else 14
    weak_dims = ability_profile.get("weakDimensions", [])
    scores = ability_profile.get("scores", {})

    # 按薄弱程度排序所有维度（分数从低到高）
    sorted_dims = sorted(ABILITY_DIMENSIONS, key=lambda d: scores.get(d, 0))

    items = []
    now = datetime.utcnow()

    for day in range(1, total_days + 1):
        day_items = []

        if day == 1:
            # 第1天：安排最薄弱维度的训练
            target_dim = sorted_dims[0] if sorted_dims else "识诈力"
            tasks = ABILITY_TASK_MAP.get(target_dim, [])
            for task in tasks[:2]:
                day_items.append(_make_item(day, task, target_dim))

        elif day == total_days:
            # 最后一天：综合测评
            day_items.append(_make_item(day, COMPREHENSIVE_ASSESSMENT, "综合"))

        elif day == 3:
            # 第3天：复训 + 继续薄弱维度
            target_dim = sorted_dims[1] if len(sorted_dims) > 1 else sorted_dims[0]
            tasks = ABILITY_TASK_MAP.get(target_dim, [])
            if tasks:
                day_items.append(_make_item(day, tasks[0], target_dim))
            # 添加复训标记
            day_items.append(_make_item(day, {
                "taskType": "retrain",
                "taskRef": "retrain-day3",
                "title": "错题复训（第1轮）",
                "minutes": 15,
                "targetAbility": target_dim,
                "objective": "对前期训练中的错题进行第1轮间隔重复训练",
                "completionCriteria": "完成全部待复训错题",
                "acceptanceMethod": "系统自动记录每道错题的正确率变化",
            }, target_dim))

        elif day == 7 and total_days > 7:
            # 14天计划的第7天：第2轮复训
            day_items.append(_make_item(day, {
                "taskType": "retrain",
                "taskRef": "retrain-day7",
                "title": "错题复训（第2轮）",
                "minutes": 15,
                "targetAbility": "综合",
                "objective": "对前7天训练中的错题进行第2轮间隔重复训练，强化长期记忆",
                "completionCriteria": "完成全部待复训错题",
                "acceptanceMethod": "系统自动记录每道错题的正确率变化",
            }, "综合"))

        elif day == total_days - 1:
            # 倒数第二天：次薄弱维度
            target_dim = sorted_dims[1] if len(sorted_dims) > 1 else sorted_dims[0]
            tasks = ABILITY_TASK_MAP.get(target_dim, [])
            for task in tasks[:1]:
                day_items.append(_make_item(day, task, target_dim))

        else:
            # 其他天：轮转训练各维度
            dim_index = (day - 2) % len(ABILITY_DIMENSIONS)
            target_dim = sorted_dims[dim_index]
            tasks = ABILITY_TASK_MAP.get(target_dim, [])
            if tasks:
                day_items.append(_make_item(day, tasks[0], target_dim))

        items.extend(day_items)

    # 弱维度建议
    weak_suggestions = [
        f"{dim}：{DIMENSION_SUGGESTIONS.get(dim, '')}"
        for dim in weak_dims
    ]

    return {
        "planType": plan_type,
        "totalDays": total_days,
        "items": items,
        "weakDimensionSuggestions": weak_suggestions,
        "motivationText": "",  # AI 增强时填充
        "createdAt": now.isoformat(),
        "expiresAt": (now + timedelta(days=total_days)).isoformat(),
    }


def _make_item(day: int, task: dict, target_ability: str) -> dict:
    """生成单个任务条目（含富元数据）。"""
    return {
        "id": f"item-{uuid.uuid4().hex[:8]}",
        "dayIndex": day,
        "taskType": task.get("taskType", "knowledge"),
        "taskRef": task.get("taskRef", ""),
        "taskTitle": task.get("title", ""),
        "targetAbility": task.get("targetAbility", target_ability),
        "estimatedMinutes": task.get("minutes", 15),
        "objective": task.get("objective", ""),
        "completionCriteria": task.get("completionCriteria", ""),
        "acceptanceMethod": task.get("acceptanceMethod", ""),
        "retrainCondition": "训练正确率 < 60% 触发错题复训",
        "status": "pending",
    }
