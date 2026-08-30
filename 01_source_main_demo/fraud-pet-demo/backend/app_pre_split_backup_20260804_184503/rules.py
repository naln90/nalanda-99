from __future__ import annotations

from datetime import datetime
from re import sub

DAILY_MAX_GROWTH = 300
TASK_MAX_GROWTH = 90
SUSPICIOUS_CHECK_DAILY_LIMIT = 3

STAGE_BY_LEVEL = [
    (1, 3, "幼崽期"),
    (4, 7, "学习期"),
    (8, 12, "成长期"),
    (13, 16, "进阶期"),
    (17, 20, "反诈守护者"),
]

RISK_RULES = [
    (("退款", "账户异常", "账户冻结"), 35, "冒充客服退款或账户异常诱导"),
    (("转账", "垫付", "保证金", "解冻费"), 25, "要求转账、垫付、保证金或解冻费"),
    (("高收益", "稳赚不赔", "日结", "返利"), 15, "承诺高收益或高返利"),
    (("私下", "扫码付款", "平台外"), 15, "要求平台外交易或私下付款"),
    (("验证码", "屏幕共享"), 20, "索要验证码或要求开启屏幕共享"),
    (("老师", "客服", "同学", "熟人"), 15, "冒充老师、客服、同学或熟人"),
    (("紧急", "保密", "限时", "冻结"), 10, "制造紧急压力或要求保密"),
    (("提现失败", "继续充值", "补单"), 20, "提现失败后要求继续充值或补单"),
]

COMPLIANCE_NOTICE = "系统仅用于校园反诈教育训练和风险提示，不替代公安机关、金融机构或学校管理部门判断。"


def pet_level(growth_value: int) -> int:
    return max(1, min(20, growth_value // 200 + 1))


def pet_stage(level: int) -> str:
    for start, end, stage in STAGE_BY_LEVEL:
        if start <= level <= end:
            return stage
    return "反诈守护者"


def level_bounds(level: int) -> tuple[int, int]:
    current_min = max(0, (level - 1) * 200)
    next_value = level * 200 if level < 20 else current_min
    return current_min, next_value


def training_growth(
    max_reward: int,
    difficulty: str,
    accuracy: float,
    task_max_growth: int = TASK_MAX_GROWTH,
) -> dict[str, int]:
    difficulty_bonus_map = {"低": 0, "中等": 10, "高": 20}
    base_points = round(max_reward * 0.6)
    accuracy_bonus = round(max_reward * 0.3 * accuracy)
    difficulty_bonus = difficulty_bonus_map.get(difficulty, 0)
    final_growth = min(max_reward, task_max_growth, base_points + accuracy_bonus + difficulty_bonus)
    return {
        "basePoints": base_points,
        "accuracyBonus": accuracy_bonus,
        "difficultyBonus": difficulty_bonus,
        "finalGrowth": final_growth,
    }


def risk_level(score: int) -> str:
    if score <= 30:
        return "低风险"
    if score <= 60:
        return "中风险"
    return "高风险"


def fraud_type_for_text(text: str) -> str:
    if "退款" in text or "客服" in text:
        return "冒充客服 / 网购退款"
    if "刷单" in text or "返利" in text:
        return "刷单返利"
    if "投资" in text or "理财" in text:
        return "虚假投资"
    if "老师" in text:
        return "冒充老师"
    if "游戏" in text or "保证金" in text:
        return "游戏交易"
    if "熟人" in text or "转账" in text:
        return "AI 换脸 / 熟人借钱"
    return "综合诈骗风险"


def analyze_text(text: str) -> dict[str, object]:
    score = 0
    evidence: list[str] = []
    for keywords, weight, description in RISK_RULES:
        hit_keywords = [keyword for keyword in keywords if keyword in text]
        if hit_keywords:
            score += weight
            evidence.append(f"{description}：{', '.join(hit_keywords)}")
    score = min(score, 100)
    return {
        "riskScore": score,
        "riskLevel": risk_level(score),
        "fraudType": fraud_type_for_text(text),
        "evidence": evidence or ["未命中明显高危关键词，但仍建议通过官方渠道核验。"],
        "suggestions": [
            "停止操作，不要按照对方指示进行任何转账或验证操作",
            "不提供验证码、密码、银行卡等敏感信息",
            "不共享屏幕，不下载对方提供的软件",
            "必要时拨打反诈专线 96110 咨询求助",
        ],
        "complianceNotice": COMPLIANCE_NOTICE,
    }


def mask_text(text: str) -> str:
    masked = sub(r"\d{4,}", "****", text)
    return masked[:500]


def same_day(left: datetime, right: datetime | None = None) -> bool:
    right = right or datetime.utcnow()
    return left.date() == right.date()
