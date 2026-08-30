"""复盘引擎 — 训练后生成复盘报告。

输出：
  - 已识别证据
  - 遗漏证据
  - 正确行为
  - 风险行为
  - 下一步建议
  - 能力变化
  - 复盘总结（AI 生成或模板）
"""

from __future__ import annotations

from .scenario_state_machine import get_all_evidence, get_state_name


def generate_review_rule(session_data: dict) -> dict:
    """规则引擎生成复盘报告。"""
    fraud_type = session_data.get("fraudType", session_data.get("scenarioType", "刷单返利"))
    final_state = session_data.get("finalState", "S0")
    identified = set(session_data.get("identifiedEvidence", []))
    user_behaviors = session_data.get("userBehaviors", [])

    all_evidence = set(get_all_evidence(fraud_type))
    missed = all_evidence - identified
    identified_list = sorted(identified)
    missed_list = sorted(missed)

    correct_behaviors = []
    risky_behaviors = []

    for ub in user_behaviors:
        behavior = ub.get("behavior", "hesitate")
        message = ub.get("message", "")
        state = ub.get("state", "")

        if behavior == "recognize_risk":
            correct_behaviors.append({
                "behavior": "识别风险",
                "message": message[:50],
                "state": get_state_name(fraud_type, state),
            })
        elif behavior == "proceed":
            risky_behaviors.append({
                "behavior": "继续配合",
                "message": message[:50],
                "state": get_state_name(fraud_type, state),
            })
        elif behavior == "hesitate":
            risky_behaviors.append({
                "behavior": "犹豫未决",
                "message": message[:50],
                "state": get_state_name(fraud_type, state),
            })

    # 计算分数
    total_evidence = len(all_evidence) if all_evidence else 1
    evidence_score = round(len(identified_list) / total_evidence * 60)
    behavior_score = 0
    if correct_behaviors:
        behavior_score = min(40, len(correct_behaviors) * 15)
    elif not risky_behaviors:
        behavior_score = 20
    else:
        behavior_score = max(0, 40 - len(risky_behaviors) * 10)

    total_score = evidence_score + behavior_score

    # 是否成功识破
    is_success = final_state in ("S4", "S5") and bool(correct_behaviors)

    # 下一步建议
    next_steps = []
    if missed_list:
        next_steps.append(f"重点学习遗漏的证据：{', '.join(missed_list[:3])}")
    if risky_behaviors:
        next_steps.append("在遇到'继续配合'的场景时，应更早识别风险并拒绝")
    if not correct_behaviors:
        next_steps.append("建议先学习对应诈骗类型的基础知识，再进行情景训练")
    next_steps.append("完成错题复训以巩固薄弱知识点")
    if is_success:
        next_steps.append("表现优秀！可以尝试更高难度的诈骗情景训练")

    # 能力变化（基于表现，维度名主题无关）
    ability_change = {}
    if is_success:
        ability_change = {
            "辨识力": min(10, len(identified_list) * 2),
            "应变力": min(8, len(correct_behaviors) * 3),
        }
    else:
        ability_change = {
            "辨识力": min(3, len(identified_list)),
        }

    # 模板复盘总结
    if is_success:
        summary = f"你在本次{fraud_type}情景训练中成功识破了骗局！"
        if identified_list:
            summary += f"正确识别了{len(identified_list)}个风险证据。"
        if missed_list:
            summary += f"还有{len(missed_list)}个证据未能识别，继续加油。"
    else:
        summary = f"你在本次{fraud_type}情景训练中未能及时识破骗局。"
        if identified_list:
            summary += f"识别了{len(identified_list)}个风险证据，"
        else:
            summary += "未能识别风险证据，"
        summary += "建议回顾训练内容并完成复训。"

    # 分维度得分（0-100 标尺，供 ReviewReport 存储和前端展示）
    dim_scores = {
        "recognition": min(100, len(identified_list) * 15) if identified_list else 0,
        "judgment": min(100, behavior_score * 2 + (10 if is_success else 0)),
        "response": min(100, len(correct_behaviors) * 20 + (20 if is_success else 0)),
        "evidence": evidence_score + min(40, len(identified_list) * 5),
        "help": min(100, 30 + (len(correct_behaviors) * 20 if correct_behaviors else 0)),
    }

    return {
        "identifiedEvidence": identified_list,
        "missedEvidence": missed_list,
        "correctBehaviors": correct_behaviors,
        "riskyBehaviors": risky_behaviors,
        "nextSteps": next_steps,
        "abilityChange": ability_change,
        "reviewSummary": summary,
        "score": total_score,
        "isSuccess": is_success,
        "finalState": final_state,
        "finalStateName": get_state_name(fraud_type, final_state),
        "dimScores": dim_scores,
    }
