"""紧急止损模块 — 用户可能已被骗时的止损引导。

根据用户已发生的危险行为，生成对应的止损清单。
"""

from __future__ import annotations

import copy

# 止损清单库
STOP_LOSS_CHECKLIST: dict[str, list[dict]] = {
    "已转账": [
        {"action": "立即拨打110或96110报警", "urgent": True, "detail": "告知警方转账时间、金额、对方账户信息"},
        {"action": "联系银行客服申请紧急止付", "urgent": True, "detail": "提供转账凭证，请求冻结对方账户"},
        {"action": "保存转账凭证和聊天记录", "urgent": False, "detail": "截图保存所有转账记录、对方账号、聊天内容"},
        {"action": "前往就近派出所报案", "urgent": False, "detail": "携带身份证、手机、转账凭证前往报案"},
    ],
    "已泄露验证码": [
        {"action": "立即修改相关账户密码", "urgent": True, "detail": "修改收到验证码对应的账户密码"},
        {"action": "联系银行冻结关联银行卡", "urgent": True, "detail": "告知银行验证码已泄露，请求临时冻结"},
        {"action": "开启账户二次验证", "urgent": False, "detail": "为重要账户开启短信/邮箱二次验证"},
        {"action": "检查账户异常登录记录", "urgent": False, "detail": "查看近期是否有异常登录或操作"},
    ],
    "已安装陌生软件": [
        {"action": "立即卸载该软件", "urgent": True, "detail": "在设置-应用管理中彻底卸载"},
        {"action": "运行手机安全扫描", "urgent": True, "detail": "使用手机自带安全中心或可信安全软件扫描"},
        {"action": "修改手机支付密码", "urgent": False, "detail": "修改微信、支付宝等支付密码"},
        {"action": "检查是否有异常权限开启", "urgent": False, "detail": "检查设置-权限管理中是否有异常授权"},
    ],
    "已开启屏幕共享": [
        {"action": "立即关闭屏幕共享", "urgent": True, "detail": "在通知栏或会议软件中关闭屏幕共享功能"},
        {"action": "修改所有在共享期间可见的密码", "urgent": True, "detail": "包括银行密码、支付密码、社交账号密码等"},
        {"action": "检查账户是否有异常操作", "urgent": True, "detail": "查看银行、支付宝等账户是否有未知交易"},
        {"action": "联系银行确认是否有异常交易", "urgent": False, "detail": "主动致电银行客服核实近期交易"},
    ],
    "已泄露身份证信息": [
        {"action": "向公安机关报备身份证泄露", "urgent": True, "detail": "可拨打110或前往派出所说明情况"},
        {"action": "关注个人征信报告", "urgent": False, "detail": "定期查询征信，防止被冒名贷款"},
        {"action": "修改关联账户密码", "urgent": True, "detail": "修改使用身份证注册的各类账户密码"},
        {"action": "开启账户安全提醒", "urgent": False, "detail": "在银行和支付平台开启交易提醒"},
    ],
    "已点击不明链接": [
        {"action": "不要输入任何个人信息", "urgent": True, "detail": "如果页面要求输入信息，立即关闭"},
        {"action": "清除浏览器缓存和Cookie", "urgent": True, "detail": "在浏览器设置中清除数据"},
        {"action": "检查是否自动安装了软件", "urgent": False, "detail": "查看应用列表是否有不明应用"},
        {"action": "修改可能泄露的账户密码", "urgent": False, "detail": "如果在页面输入过密码，立即修改"},
    ],
}

# 紧急联系电话
EMERGENCY_CONTACTS = [
    {"name": "报警电话", "number": "110", "description": "紧急情况报警"},
    {"name": "反诈专线", "number": "96110", "description": "全国反诈预警劝阻专线"},
    {"name": "短信报警", "number": "12110", "description": "不方便语音通话时使用"},
]


def get_stop_loss_checklist(selected_risks: list[str]) -> dict:
    """根据用户选择的危险行为生成止损清单。

    Args:
        selected_risks: ["已转账", "已泄露验证码", ...]

    Returns:
        {
            "checklist": [
                {
                    "riskType": "已转账",
                    "items": [
                        {"action": "...", "urgent": True, "detail": "...", "completed": False},
                        ...
                    ],
                },
                ...
            ],
            "emergencyContacts": [...],
            "totalSteps": 8,
            "urgentSteps": 4,
        }
    """
    checklist = []
    total_steps = 0
    urgent_steps = 0

    for risk in selected_risks:
        # 深拷贝，避免运行时改写模块级常量 STOP_LOSS_CHECKLIST（R3 并发安全）
        items = copy.deepcopy(STOP_LOSS_CHECKLIST.get(risk, []))
        if not items:
            continue

        for item in items:
            item["completed"] = False
            total_steps += 1
            if item.get("urgent"):
                urgent_steps += 1

        checklist.append({
            "riskType": risk,
            "items": items,
        })

    return {
        "checklist": checklist,
        "emergencyContacts": EMERGENCY_CONTACTS,
        "totalSteps": total_steps,
        "urgentSteps": urgent_steps,
    }


def get_all_risk_types() -> list[dict]:
    """获取所有可选的危险行为类型。"""
    return [
        {"value": "已转账", "label": "已向对方转账"},
        {"value": "已泄露验证码", "label": "已向对方提供验证码"},
        {"value": "已安装陌生软件", "label": "已安装对方要求的软件"},
        {"value": "已开启屏幕共享", "label": "已开启屏幕共享"},
        {"value": "已泄露身份证信息", "label": "已提供身份证信息"},
        {"value": "已点击不明链接", "label": "已点击不明链接并输入信息"},
    ]
