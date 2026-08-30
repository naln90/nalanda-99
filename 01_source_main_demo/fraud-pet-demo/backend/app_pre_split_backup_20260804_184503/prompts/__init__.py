"""版本化提示词管理模块。

从 prompts/ 目录加载版本化的提示词模板文件，
替代 ai_service.py 中硬编码的提示词。

目录结构：
  prompts/
    __init__.py          — 本文件，提供加载接口
    dialogue_v1.json     — 情景对话提示词 v1.0
    risk_analysis_v1.json — 风险分析提示词 v1.0
    task_planning_v1.json — 任务包生成提示词 v1.0
    review_v1.json       — 复盘总结提示词 v1.0

使用方式：
  from .prompts import get_prompt
  prompt = get_prompt("dialogue")  # 返回 (system_prompt, version)
"""

from __future__ import annotations

import json
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent
_CACHE: dict[str, tuple[str, str]] = {}


def _load_json(filename: str) -> dict:
    filepath = _PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_prompt(name: str) -> tuple[str, str]:
    """获取指定名称的提示词模板。

    Args:
        name: 提示词名称 (dialogue / risk_analysis / task_planning / review)

    Returns:
        (system_prompt, version) 元组
    """
    if name in _CACHE:
        return _CACHE[name]

    # 按版本号优先级加载最新版本
    candidates = sorted(_PROMPTS_DIR.glob(f"{name}_v*.json"), reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No prompt template found for '{name}'")

    data = _load_json(candidates[0].name)
    system_prompt = data["system_prompt"]
    version = data.get("version", "unknown")
    _CACHE[name] = (system_prompt, version)
    return system_prompt, version


def list_prompts() -> list[dict[str, str]]:
    """列出所有可用提示词模板。"""
    result = []
    for f in sorted(_PROMPTS_DIR.glob("*_v*.json")):
        data = _load_json(f.name)
        result.append({
            "name": f.stem.rsplit("_v", 1)[0],
            "version": data.get("version", "unknown"),
            "file": f.name,
            "description": data.get("description", ""),
        })
    return result


def clear_cache() -> None:
    """清除提示词缓存（用于热重载）。"""
    _CACHE.clear()
