"""综合能力画像 — 规则引擎计算，不依赖 LLM。

画像是对用户「已参与的全部主题 / 测评」的综合评估，而不是针对某一个主题。
五个通用能力维度（与具体主题解耦）：
  辨识力 — 识别风险信号、异常话术与不实信息的能力
  判断力 — 在压力与诱惑下保持理性、独立判断的能力
  应变力 — 面对突发或可疑情况时采取正确应对的能力
  实证力 — 核验信息、识别并留存关键证据的能力
  协作力 — 主动求助、协同处置与互助支持的能力
"""

from __future__ import annotations

# 能力维度定义（主题无关，适用于所有参与主题的综合画像）
ABILITY_DIMENSIONS = ["辨识力", "判断力", "应变力", "实证力", "协作力"]

# 维度描述
DIMENSION_DESCRIPTIONS = {
    "辨识力": "识别风险信号、异常话术与不实信息的能力",
    "判断力": "在压力与诱惑下保持理性、独立判断的能力",
    "应变力": "面对突发或可疑情况时采取正确应对的能力",
    "实证力": "核验信息、识别并留存关键证据的能力",
    "协作力": "主动求助、协同处置与互助支持的能力",
}

# 维度改进建议
DIMENSION_SUGGESTIONS = {
    "辨识力": "多接触不同主题的案例，熟悉常见风险信号与话术模式",
    "判断力": "训练多角度分析信息，先核实再行动的习惯",
    "应变力": "掌握标准应对流程：不轻信、不转账、不共享敏感信息",
    "实证力": "学会核验来源、识别并保存关键证据：记录、凭证、对方信息",
    "协作力": "牢记求助渠道：辅导员、家长、110 与官方平台",
}

# 旧维度名（去反诈化前）-> 新维度名的兼容映射，用于读取历史画像数据
DIMENSION_KEY_MAP = {
    "识诈力": "辨识力",
    "判断力": "判断力",
    "应对力": "应变力",
    "证据力": "实证力",
    "求助力": "协作力",
}


def normalize_dim_key(key: str) -> str:
    """将（可能来自旧题库/历史数据）的维度名归一为当前主题无关维度名。"""
    return DIMENSION_KEY_MAP.get(key, key)


def normalize_profile_scores(scores: dict) -> dict:
    """把任意来源的维度得分字典归一为当前维度键，合并冲突时取均值。"""
    if not isinstance(scores, dict):
        return {}
    out: dict[str, list[float]] = {}
    for raw_key, val in scores.items():
        new_key = normalize_dim_key(raw_key)
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        out.setdefault(new_key, []).append(v)
    return {k: round(sum(vs) / len(vs)) for k, vs in out.items()}


def compute_ability_profile(answers: list[dict], questions: list[dict]) -> dict:
    """根据答题结果计算综合能力画像（聚合所有参与主题）。

    Args:
        answers: [{"questionId": "q1", "selected": ["A"]}, ...]
        questions: [{"id": "q1", "abilityDim": "辨识力", "correctAnswer": ["A"], ...}, ...]

    Returns:
        {
            "scores": {"辨识力": 80, "判断力": 60, ...},
            "weakDimensions": ["判断力", "应变力"],
            "strongDimensions": ["辨识力"],
            "overallScore": 72,
            "descriptions": {"辨识力": "...", ...},
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
        dim = normalize_dim_key(q.get("abilityDim", "辨识力"))
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
        {"辨识力": +15, "判断力": -5, ...}
    """
    before_scores = normalize_profile_scores(before.get("scores", {}))
    after_scores = normalize_profile_scores(after.get("scores", {}))
    return {
        dim: after_scores.get(dim, 0) - before_scores.get(dim, 0)
        for dim in ABILITY_DIMENSIONS
    }
