"""安全护栏 — 输入脱敏 + 输出审查。

确保用户输入不包含敏感个人信息，
确保 AI 输出不包含诈骗教程或危险操作步骤。
"""

from __future__ import annotations

import re
from typing import NamedTuple

# 敏感信息检测正则
SENSITIVE_PATTERNS = [
    (re.compile(r"1[3-9]\d{9}"), "手机号"),
    (re.compile(r"\b\d{17}[\dXx]\b"), "身份证号"),
    (re.compile(r"\b\d{16,19}\b"), "银行卡号"),
    (re.compile(r"\d{4,8}\s*[验|验证]码"), "验证码"),
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "邮箱地址"),
    (re.compile(r"(?:密码|口令|password)[\s:：]*[^\s]+", re.IGNORECASE), "密码"),
]

# 危险输出检测关键词（关键词 + 上下文需同时出现才拦截，降低误报）
DANGEROUS_OUTPUT_PATTERNS = [
    ("具体操作步骤", "教程"),
    ("绕过", "监管"),
    ("如何实施", "诈骗"),
    ("详细步骤", "骗取"),
    ("安全保证", "绝对安全"),
    ("百分百", "稳赚"),
    ("必定获利", "投资"),
]

# 高风险固定短语：无需上下文即可判定为危险内容，防止拆分绕过（R4/S4）
STANDALONE_DANGEROUS_PHRASES = [
    "绕过监管",
    "如何实施诈骗",
    "详细步骤骗取",
    "百分百稳赚",
    "必定获利",
    "绝对安全保证",
    "安全保证绝对安全",
]

# 安全提示替换文案
SAFETY_REPLACEMENT = "该内容涉及敏感信息或潜在风险，已自动拦截。请通过官方渠道获取帮助。"


class FilterResult(NamedTuple):
    """输入过滤结果"""

    safe_text: str
    detected_types: list[str]
    is_blocked: bool


def filter_input(text: str) -> FilterResult:
    """检测并脱敏输入中的敏感信息。

    将手机号、身份证号、银行卡号等替换为 ****，
    返回安全文本和命中的敏感类型列表。
    """
    safe_text = text
    detected = []

    for pattern, label in SENSITIVE_PATTERNS:
        matches = pattern.findall(safe_text)
        if matches:
            detected.append(label)
            safe_text = pattern.sub("****", safe_text)

    return FilterResult(
        safe_text=safe_text[:500],
        detected_types=detected,
        is_blocked=len(detected) > 0,
    )


class OutputCheckResult(NamedTuple):
    """输出审查结果"""

    is_safe: bool
    blocked_reason: str | None
    safe_output: str


def check_output(text: str) -> OutputCheckResult:
    """检查 AI 输出是否包含危险内容。

    检测是否包含诈骗教程、绕过监管方法、绝对安全结论等。
    命中时替换为安全提示。

    双层检测：
    1. 关键词 + 上下文必须同时出现（降低教育场景误报）；
    2. 高风险固定短语无需上下文即可拦截，防止拆分绕过（R4/S4）。
    """
    for keyword, context in DANGEROUS_OUTPUT_PATTERNS:
        if keyword in text and context in text:
            return OutputCheckResult(
                is_safe=False,
                blocked_reason=f"检测到危险内容：{keyword}+{context}",
                safe_output=SAFETY_REPLACEMENT,
            )

    for phrase in STANDALONE_DANGEROUS_PHRASES:
        if phrase in text:
            return OutputCheckResult(
                is_safe=False,
                blocked_reason=f"检测到危险内容：{phrase}",
                safe_output=SAFETY_REPLACEMENT,
            )

    return OutputCheckResult(is_safe=True, blocked_reason=None, safe_output=text)


def is_safe_input(text: str) -> bool:
    """快速判断输入是否安全（不包含敏感信息）。"""
    return len(filter_input(text).detected_types) == 0
