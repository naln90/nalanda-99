"""五维能力画像 — 规则引擎计算，不依赖 LLM。

五个维度：
  识诈力 — 识别诈骗话术和风险信号的能力
  判断力 — 分析风险程度和做出正确判断的能力
  应对力 — 面对诈骗时的正确操作能力
  证据力 — 识别和保留证据的能力
  求助力 — 知道如何求助和止损的能力
"""

from __future__ import annotations

# 能力维度定义
ABILITY_DIMENSIONS = ["识诈力", "判断力", "应对力", "证据力", "求助力"]

# 维度描述
DIMENSION_DESCRIPTIONS = {
    "识诈力": "识别各类诈骗话术和风险信号的能力",
    "判断力": "分析风险程度并做出正确判断的能力",
    "应对力": "面对诈骗场景时采取正确操作的能力",
    "证据力": "识别关键风险证据并保留的能力",
    "求助力": "知道如何求助、举报和止损的能力",
}

# 维度改进建议
DIMENSION_SUGGESTIONS = {
    "识诈力": "多接触各类诈骗案例，熟悉常见话术模板和风险信号",
    "判断力": "训练分析能力，学会从多角度评估信息的真实性",
    "应对力": "掌握标准应对流程：不转账、不验证、不共享屏幕",
    "证据力": "学会识别和保存关键证据：聊天记录、转账凭证、对方信息",
    "求助力": "牢记求助渠道：96110反诈专线、110报警、辅导员求助",
}


def compute_ability_profile(answers: list[dict], questions: list[dict]) -> dict:
    """根据答题结果计算五维能力画像。

    Args:
        answers: [{"questionId": "q1", "selected": ["A"]}, ...]
        questions: [{"id": "q1", "abilityDim": "识诈力", "correctAnswer": ["A"], ...}, ...]

    Returns:
        {
            "scores": {"识诈力": 80, "判断力": 60, ...},
            "weakDimensions": ["判断力", "应对力"],
            "strongDimensions": ["识诈力"],
            "overallScore": 72,
            "descriptions": {"识诈力": "...", ...},
        }
    """
    question_map = {q["id"]: q for q in questions}

    dim_scores: dict[str, dict[str, int]] = {
        dim: {"correct": 0, "total": 0} for dim in ABILITY_DIMENSIONS
    }

    for ans in answers:
        q = question_map.get(ans.get("questionId", ""))
        if not q:
            continue
        dim = q.get("abilityDim", "识诈力")
        if dim not in dim_scores:
            dim_scores[dim] = {"correct": 0, "total": 0}
        dim_scores[dim]["total"] += 1
        selected = set(ans.get("selected", []))
        correct = set(q.get("correctAnswer", []))
        if selected == correct:
            dim_scores[dim]["correct"] += 1

    scores = {}
    for dim in ABILITY_DIMENSIONS:
        s = dim_scores[dim]
        if s["total"] > 0:
            scores[dim] = round(s["correct"] / s["total"] * 100)
        else:
            scores[dim] = 0

    overall = round(sum(scores.values()) / len(ABILITY_DIMENSIONS))

    weak = [dim for dim in ABILITY_DIMENSIONS if scores[dim] < 60]
    strong = [dim for dim in ABILITY_DIMENSIONS if scores[dim] >= 80]

    return {
        "scores": scores,
        "weakDimensions": weak,
        "strongDimensions": strong,
        "overallScore": overall,
        "descriptions": {dim: DIMENSION_DESCRIPTIONS[dim] for dim in ABILITY_DIMENSIONS},
        "suggestions": {dim: DIMENSION_SUGGESTIONS[dim] for dim in ABILITY_DIMENSIONS},
    }


def ability_delta(before: dict, after: dict) -> dict:
    """计算两次能力画像之间的变化。

    Returns:
        {"识诈力": +15, "判断力": -5, ...}
    """
    before_scores = before.get("scores", {})
    after_scores = after.get("scores", {})
    return {
        dim: after_scores.get(dim, 0) - before_scores.get(dim, 0)
        for dim in ABILITY_DIMENSIONS
    }
