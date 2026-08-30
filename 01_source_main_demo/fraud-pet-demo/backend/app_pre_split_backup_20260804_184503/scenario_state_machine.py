"""情景对话状态机 — 每类诈骗对话的有限状态机定义。

状态机约束 AI 只能按预设状态推进对话，
用户行为由规则引擎分类（识别风险/继续配合/提问/犹豫），
确保对话安全可控。

十类核心诈骗情景：
  1. 刷单返利
  2. 游戏交易
  3. 虚假客服
  4. 冒充老师
  5. 虚假招聘
  6. 奖助学金
  7. AI换脸（熟人借钱）
  8. 求职培训贷
  9. 网购退款
  10. 虚假投资理财
"""

from __future__ import annotations

# ==================== 状态机定义 ====================

SCENARIO_FSM: dict[str, dict] = {
    "刷单返利": {
        "states": {
            "S0": {"name": "引流阶段", "prompt": "你是兼职推广者，用'轻松日结、做任务赚佣金'吸引用户。语气热情友好。"},
            "S1": {"name": "首单返利", "prompt": "用户接受了邀请。你让用户完成一个小额任务（如点赞关注），并立即返还了几元佣金，建立信任。语气得意。"},
            "S2": {"name": "加码垫付", "prompt": "你提出需要垫付资金的'连单任务'，承诺完成后本金加佣金一起返还。金额从几百开始。语气诱导。"},
            "S3": {"name": "做满任务", "prompt": "用户垫付后，你说任务还没做完，需要继续垫付多笔才能提现。金额逐渐升级。语气施压。"},
            "S4": {"name": "提现失败", "prompt": "用户要求提现时，你说系统故障/操作违规/需要缴纳保证金才能提现。语气推脱。"},
            "S5": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S5", "evidence": ["兼职广告", "日结承诺", "高返利诱惑"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S5", "evidence": ["小额返利建立信任", "刷单本质违法"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S5", "evidence": ["要求垫付资金", "本金升级"]},
                "proceed": {"to": "S3", "evidence": []},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {
                "recognize_risk": {"to": "S5", "evidence": ["金额持续升级", "无法中途退出"]},
                "proceed": {"to": "S4", "evidence": []},
                "ask_question": {"to": "S3", "evidence": []},
                "hesitate": {"to": "S3", "evidence": []},
            },
            "S4": {
                "recognize_risk": {"to": "S5", "evidence": ["提现受阻", "要求缴纳保证金"]},
                "proceed": {"to": "S4", "evidence": ["持续被骗"]},
                "ask_question": {"to": "S4", "evidence": []},
                "hesitate": {"to": "S4", "evidence": []},
            },
            "S5": {"recognize_risk": {"to": "S5", "evidence": []}, "proceed": {"to": "S5", "evidence": []}},
        },
        "all_evidence": ["兼职广告", "日结承诺", "高返利诱惑", "小额返利建立信任", "刷单本质违法", "要求垫付资金", "本金升级", "金额持续升级", "无法中途退出", "提现受阻", "要求缴纳保证金"],
    },
    "游戏交易": {
        "states": {
            "S0": {"name": "引流阶段", "prompt": "你是游戏道具买家/卖家，在交易平台外私下联系用户，提出高价收购或低价出售。"},
            "S1": {"name": "诱导私下交易", "prompt": "你引导用户离开平台，通过微信/QQ私下交易，理由是平台手续费高。"},
            "S2": {"name": "要求保证金", "prompt": "交易前你要求用户先缴纳保证金/担保金，承诺交易完成后退还。"},
            "S3": {"name": "持续收费", "prompt": "缴纳保证金后，你又以各种理由（解冻费、验证费）要求继续转账。"},
            "S4": {"name": "拉黑失联", "prompt": "用户要求退款时，你找借口拖延，最终拉黑失联。"},
            "S5": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S5", "evidence": ["私下交易诱导", "脱离平台保障"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S5", "evidence": ["脱离平台交易", "缺乏担保"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S5", "evidence": ["要求缴纳保证金", "先付后交无保障"]},
                "proceed": {"to": "S3", "evidence": []},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {
                "recognize_risk": {"to": "S5", "evidence": ["持续收费", "各种名义要钱"]},
                "proceed": {"to": "S4", "evidence": []},
                "ask_question": {"to": "S3", "evidence": []},
                "hesitate": {"to": "S3", "evidence": []},
            },
            "S4": {
                "recognize_risk": {"to": "S5", "evidence": ["拖延退款", "拉黑失联"]},
                "proceed": {"to": "S4", "evidence": ["持续被骗"]},
                "ask_question": {"to": "S4", "evidence": []},
                "hesitate": {"to": "S4", "evidence": []},
            },
            "S5": {"recognize_risk": {"to": "S5", "evidence": []}, "proceed": {"to": "S5", "evidence": []}},
        },
        "all_evidence": ["私下交易诱导", "脱离平台保障", "脱离平台交易", "缺乏担保", "要求缴纳保证金", "先付后交无保障", "持续收费", "各种名义要钱", "拖延退款", "拉黑失联"],
    },
    "虚假客服": {
        "states": {
            "S0": {"name": "冒充身份", "prompt": "你冒充电商平台客服，声称用户订单异常/商品有问题需要处理退款。"},
            "S1": {"name": "诱导屏幕共享", "prompt": "你要求用户下载屏幕共享软件或提供验证码，声称是退款流程需要。"},
            "S2": {"name": "操作账户", "prompt": "你引导用户操作支付宝/网银，声称要'验证资金'或'退款通道'。"},
            "S3": {"name": "转移资金", "prompt": "你要求用户输入验证码或转账到'安全账户'，实际在转移用户资金。"},
            "S4": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S4", "evidence": ["冒充客服", "主动联系退款"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S4", "evidence": ["要求屏幕共享", "索要验证码"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S4", "evidence": ["操作网银账户", "验证资金骗局"]},
                "proceed": {"to": "S3", "evidence": []},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {
                "recognize_risk": {"to": "S4", "evidence": ["要求转账到安全账户", "验证码转移资金"]},
                "proceed": {"to": "S3", "evidence": ["资金已被转移"]},
                "ask_question": {"to": "S3", "evidence": []},
                "hesitate": {"to": "S3", "evidence": []},
            },
            "S4": {"recognize_risk": {"to": "S4", "evidence": []}, "proceed": {"to": "S4", "evidence": []}},
        },
        "all_evidence": ["冒充客服", "主动联系退款", "要求屏幕共享", "索要验证码", "操作网银账户", "验证资金骗局", "要求转账到安全账户", "验证码转移资金"],
    },
    "冒充老师": {
        "states": {
            "S0": {"name": "冒充身份", "prompt": "你冒充学校老师/辅导员，在QQ/微信群中学生头像，声称需要缴纳费用。"},
            "S1": {"name": "制造紧急", "prompt": "你说费用需要在今天内缴纳，否则影响选课/毕业，制造紧迫感。"},
            "S2": {"name": "要求转账", "prompt": "你提供一个收款账户，要求学生直接转账，不走学校正规缴费渠道。"},
            "S3": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S3", "evidence": ["冒充老师", "群内收费"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S3", "evidence": ["制造紧迫感", "限时要求"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S3", "evidence": ["私人账户收款", "非正规缴费渠道"]},
                "proceed": {"to": "S2", "evidence": ["已转账"]},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {"recognize_risk": {"to": "S3", "evidence": []}, "proceed": {"to": "S3", "evidence": []}},
        },
        "all_evidence": ["冒充老师", "群内收费", "制造紧迫感", "限时要求", "私人账户收款", "非正规缴费渠道"],
    },
    "虚假招聘": {
        "states": {
            "S0": {"name": "引流阶段", "prompt": "你发布高薪轻松的兼职招聘信息，声称在家就能做，日薪几百到上千。"},
            "S1": {"name": "要求交费", "prompt": "面试通过后，你以培训费/工牌费/押金为由要求先交钱。"},
            "S2": {"name": "继续收费", "prompt": "交费后你以各种理由继续收费（材料费、保险费），始终不安排实际工作。"},
            "S3": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S3", "evidence": ["高薪诱惑", "轻松在家工作"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S3", "evidence": ["入职先交费", "培训费押金"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S3", "evidence": ["持续收费不安排工作", "各种名义要钱"]},
                "proceed": {"to": "S2", "evidence": ["持续被骗"]},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {"recognize_risk": {"to": "S3", "evidence": []}, "proceed": {"to": "S3", "evidence": []}},
        },
        "all_evidence": ["高薪诱惑", "轻松在家工作", "入职先交费", "培训费押金", "持续收费不安排工作", "各种名义要钱"],
    },
    "奖助学金": {
        "states": {
            "S0": {"name": "冒充身份", "prompt": "你冒充教育部门/学校工作人员，声称可以帮用户申请奖助学金。"},
            "S1": {"name": "索要信息", "prompt": "你要求用户提供身份证号、银行卡号等个人信息，声称是申请流程需要。"},
            "S2": {"name": "诱导转账", "prompt": "你以'需要先缴纳手续费/保证金'为由要求转账，承诺发放后退还。"},
            "S3": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S3", "evidence": ["冒充官方", "主动联系奖助学金"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S3", "evidence": ["索要身份证银行卡", "信息收集"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S3", "evidence": ["先缴费再发放", "保证金骗局"]},
                "proceed": {"to": "S2", "evidence": ["已转账"]},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {"recognize_risk": {"to": "S3", "evidence": []}, "proceed": {"to": "S3", "evidence": []}},
        },
        "all_evidence": ["冒充官方", "主动联系奖助学金", "索要身份证银行卡", "信息收集", "先缴费再发放", "保证金骗局"],
    },
    "AI换脸": {
        "states": {
            "S0": {"name": "冒充身份", "prompt": "你使用AI换脸技术伪装成用户的熟人（同学/亲友），通过视频通话或短视频联系用户，声称遇到紧急情况。"},
            "S1": {"name": "制造紧急", "prompt": "你声称自己遇到突发状况（如出车祸、被拘留），急需借钱周转，语气焦急。"},
            "S2": {"name": "催促转账", "prompt": "你催促用户尽快转账，说情况紧急等不了，提供收款账户要求马上打钱。语气急切施压。"},
            "S3": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S3", "evidence": ["AI换脸视频", "熟人身份伪造"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S3", "evidence": ["紧急借钱", "突发状况借钱"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S3", "evidence": ["催促转账", "非本人核实"]},
                "proceed": {"to": "S2", "evidence": ["已转账"]},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {"recognize_risk": {"to": "S3", "evidence": []}, "proceed": {"to": "S3", "evidence": []}},
        },
        "all_evidence": ["AI换脸视频", "熟人身份伪造", "紧急借钱", "突发状况借钱", "催促转账", "非本人核实"],
    },
    "求职培训贷": {
        "states": {
            "S0": {"name": "引流阶段", "prompt": "你发布高薪IT岗位招聘信息，声称零基础也能入职，但需要先参加培训。"},
            "S1": {"name": "诱导贷款", "prompt": "面试后你说用户能力不足，需要参加付费培训课程才能入职，培训费上万元，引导用户申请培训贷。"},
            "S2": {"name": "签订协议", "prompt": "你催促用户签署培训协议和贷款合同，声称培训完包分配工作，月薪过万。语气诱导。"},
            "S3": {"name": "培训敷衍", "prompt": "用户交费后你安排敷衍的培训课程，始终不安排承诺的工作，或推荐到无关的低薪岗位。"},
            "S4": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S4", "evidence": ["高薪诱惑", "零基础入职承诺"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S4", "evidence": ["入职先培训", "诱导培训贷"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S4", "evidence": ["包分配承诺", "培训贷款合同"]},
                "proceed": {"to": "S3", "evidence": []},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {
                "recognize_risk": {"to": "S4", "evidence": ["培训敷衍", "不安排工作"]},
                "proceed": {"to": "S3", "evidence": ["持续被骗"]},
                "ask_question": {"to": "S3", "evidence": []},
                "hesitate": {"to": "S3", "evidence": []},
            },
            "S4": {"recognize_risk": {"to": "S4", "evidence": []}, "proceed": {"to": "S4", "evidence": []}},
        },
        "all_evidence": ["高薪诱惑", "零基础入职承诺", "入职先培训", "诱导培训贷", "包分配承诺", "培训贷款合同", "培训敷衍", "不安排工作"],
    },
    "网购退款": {
        "states": {
            "S0": {"name": "冒充身份", "prompt": "你冒充电商平台客服，声称用户购买的商品快递丢失或质量问题，主动提供退款理赔。"},
            "S1": {"name": "诱导操作", "prompt": "你引导用户点击短信中的退款链接，或要求下载指定APP处理退款，声称是官方理赔通道。"},
            "S2": {"name": "套取信息", "prompt": "你在退款页面要求用户填写银行卡号、密码、验证码等信息，声称是退款验证需要。"},
            "S3": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S3", "evidence": ["冒充客服", "主动退款理赔"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S3", "evidence": ["非官方链接", "下载指定APP"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S3", "evidence": ["套取银行卡密码", "索要验证码"]},
                "proceed": {"to": "S2", "evidence": ["信息已泄露"]},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {"recognize_risk": {"to": "S3", "evidence": []}, "proceed": {"to": "S3", "evidence": []}},
        },
        "all_evidence": ["冒充客服", "主动退款理赔", "非官方链接", "下载指定APP", "套取银行卡密码", "索要验证码"],
    },
    "虚假投资理财": {
        "states": {
            "S0": {"name": "引流阶段", "prompt": "你在社交平台发布投资理财广告，声称有内部渠道，稳赚不赔，年化收益30%以上。"},
            "S1": {"name": "诱导下载", "prompt": "你引导用户下载指定的投资APP或加入投资群，声称是专业导师带单，群内有人晒收益截图。"},
            "S2": {"name": "小额试水", "prompt": "你建议用户先小额投入试水，承诺很快就能看到收益。用户投入后你确实返还了小额利润，建立信任。"},
            "S3": {"name": "大额投入", "prompt": "你催促用户加大投入，说现在有难得的机会，错过就没了。用户大额投入后，你以各种理由不让提现。"},
            "S4": {"name": "完成", "prompt": "对话结束状态。"},
        },
        "transitions": {
            "S0": {
                "recognize_risk": {"to": "S4", "evidence": ["稳赚不赔承诺", "超高收益诱惑"]},
                "proceed": {"to": "S1", "evidence": []},
                "ask_question": {"to": "S0", "evidence": []},
                "hesitate": {"to": "S0", "evidence": []},
            },
            "S1": {
                "recognize_risk": {"to": "S4", "evidence": ["非正规投资平台", "群内晒收益"]},
                "proceed": {"to": "S2", "evidence": []},
                "ask_question": {"to": "S1", "evidence": []},
                "hesitate": {"to": "S1", "evidence": []},
            },
            "S2": {
                "recognize_risk": {"to": "S4", "evidence": ["小额返利建立信任", "试水诱饵"]},
                "proceed": {"to": "S3", "evidence": []},
                "ask_question": {"to": "S2", "evidence": []},
                "hesitate": {"to": "S2", "evidence": []},
            },
            "S3": {
                "recognize_risk": {"to": "S4", "evidence": ["大额投入不让提现", "投资平台跑路"]},
                "proceed": {"to": "S3", "evidence": ["持续被骗"]},
                "ask_question": {"to": "S3", "evidence": []},
                "hesitate": {"to": "S3", "evidence": []},
            },
            "S4": {"recognize_risk": {"to": "S4", "evidence": []}, "proceed": {"to": "S4", "evidence": []}},
        },
        "all_evidence": ["稳赚不赔承诺", "超高收益诱惑", "非正规投资平台", "群内晒收益", "小额返利建立信任", "试水诱饵", "大额投入不让提现", "投资平台跑路"],
    },
}

# ==================== 用户行为分类规则 ====================

RISK_RECOGNITION_KEYWORDS = [
    "骗子", "诈骗", "不对", "可疑", "不转", "不付", "拒绝", "风险",
    "报警", "96110", "核实", "官方", "正规", "平台", "不信", "套路",
    "假的", "骗人", "别想", "休想", "不去", "不做", "退出", "结束",
    "刷单", "违法", "保证金", "不交", "不上当", "停",
    # 明确拒绝/识破
    "不感兴趣", "没兴趣", "不需要", "不用", "不用了", "别找我", "别烦我",
    "别再", "算了", "拉倒", "免了", "谢绝", "不了", "不要", "走开",
]

PROCEED_KEYWORDS = [
    "好的", "可以", "没问题", "行", "嗯", "好", "怎么操作", "告诉我",
    "账号", "发给你", "转", "付", "交", "截图", "二维码", "扫",
    "继续", "下一步", "然后呢", "什么任务", "怎么做", "多少钱",
    "愿意", "参加", "加入", "试试", "体验", "了解", "想学",
]

QUESTION_KEYWORDS = [
    "为什么", "怎么", "什么是", "什么意思", "?", "？", "多少",
    "真的假的", "靠谱吗", "安全吗", "是吗", "如何", "怎样", "吗", "么",
]


def classify_user_behavior(user_message: str) -> str:
    """分类用户行为：recognize_risk / proceed / ask_question / hesitate。"""
    msg = user_message.strip().lower()

    for kw in RISK_RECOGNITION_KEYWORDS:
        if kw in msg:
            return "recognize_risk"

    for kw in QUESTION_KEYWORDS:
        if kw in msg:
            return "ask_question"

    for kw in PROCEED_KEYWORDS:
        if kw in msg:
            return "proceed"

    if len(msg) < 5:
        return "hesitate"

    return "hesitate"


def transition(
    scenario_type: str,
    current_state: str,
    user_behavior: str,
) -> dict:
    """执行状态转换，返回新状态和本次识别的证据。"""
    fsm = SCENARIO_FSM.get(scenario_type, SCENARIO_FSM["刷单返利"])
    transitions = fsm["transitions"].get(current_state, {})

    if user_behavior not in transitions:
        user_behavior = "hesitate"

    action = transitions.get(user_behavior, {"to": current_state, "evidence": []})
    new_state = action["to"]
    evidence = action.get("evidence", [])

    return {
        "newState": new_state,
        "evidence": evidence,
        "isTerminal": new_state in ("S4", "S5") and user_behavior == "recognize_risk",
    }


def get_state_prompt(scenario_type: str, state: str) -> str:
    """获取指定状态的 Prompt 模板。"""
    fsm = SCENARIO_FSM.get(scenario_type, SCENARIO_FSM["刷单返利"])
    return fsm.get("states", {}).get(state, {}).get("prompt", "")


def get_state_name(scenario_type: str, state: str) -> str:
    """获取状态名称。"""
    fsm = SCENARIO_FSM.get(scenario_type, SCENARIO_FSM["刷单返利"])
    return fsm.get("states", {}).get(state, {}).get("name", state)


def get_all_evidence(scenario_type: str) -> list[str]:
    """获取该情景的所有可能证据列表。"""
    fsm = SCENARIO_FSM.get(scenario_type, SCENARIO_FSM["刷单返利"])
    return fsm.get("all_evidence", [])


# ==================== 规则降级预脚本回复 ====================

FALLBACK_REPLIES: dict[str, dict[str, dict[str, str]]] = {
    "刷单返利": {
        "S0": {
            "default": "你好呀！我们这边有个轻松的兼职，每天只需花半小时做做任务，日结佣金，轻松赚零花钱~有兴趣了解一下吗？",
            "recognize_risk": "别紧张嘛，很多同学都在做，就是关注点赞这种小任务，了解一下又不花钱，不合适随时不做。",
            "proceed": "太好了！先帮你安排一个小任务，关注几个公众号点几个赞就行。完成了立马给你结算佣金，5块钱到账~",
            "ask_question": "很简单的，就是给指定内容点点赞、关注下公众号，一单5-10块，做完截图给我，马上日结。",
            "hesitate": "不耽误你学习的，每天抽半小时就行，先赚几杯奶茶钱试试？",
        },
        "S1": {
            "default": "太好了！先帮你安排一个小任务，关注几个公众号点几个赞就行。完成了立马给你结算佣金，5块钱到账~",
            "recognize_risk": "这就是普通的关注任务，又不垫付， completion 了立刻返你5块，有啥好担心的。",
            "proceed": "好嘞，这是第一个任务链接，你点关注后截图发我，佣金马上转你。",
            "ask_question": "任务链接和步骤我马上发你，照着做大概2分钟，佣金5元立刻到账。",
            "hesitate": "放心吧，第一单不让你垫付任何钱，做完了看佣金到账你再决定要不要继续。",
        },
        "S2": {
            "default": "恭喜完成新手任务！现在可以接连单任务了，需要先垫付300元本金，完成3单后本金加佣金一起返还，能赚好几十呢！",
            "recognize_risk": "垫付是为了防止恶意刷单，任务完成秒返，很多同学都已经提现了。",
            "proceed": "好的，这是商品链接，你垫付300元购买，截图发我，完成3单后连本带利返你390元。",
            "ask_question": "垫付就是先拍下指定商品，商家确认后连本金加佣金一起返你，一单能赚30-50。",
            "hesitate": "不用担心，平台担保，而且这单金额不大，做完了立马能看到返利。",
        },
        "S3": {
            "default": "你的任务还没做完哦，需要再垫付2笔才能提现。已经做了的不能退，做完了一起提出来就行，放心！",
            "recognize_risk": "就差最后两单了，现在退出前面的钱也拿不回来，做完一起提现更稳。",
            "proceed": "对，再垫付两笔，完成后本金佣金一起提现，我这边给你优先审核。",
            "ask_question": "系统设置的任务包，必须完成指定单数才能解锁提现，这是商家为了防薅羊毛。",
            "hesitate": "都做到这了，半途而废多可惜，再坚持两单就能全部提出来。",
        },
        "S4": {
            "default": "系统显示你的账户异常，需要缴纳500元保证金才能提现。缴了之后马上就能全部提出来，不耽误的。",
            "recognize_risk": "保证金就是走个流程，交了立刻解除异常，你本金佣金都能提出来。",
            "proceed": "好的，你把500元保证金转到这个账户，截图给我，我立刻帮你申请提现。",
            "ask_question": "因为你操作间隔太短，系统判定异常，交500元保证金验证身份后就能正常提现。",
            "hesitate": "不交会一直冻结，交了马上到账，比你放在里面强。",
        },
        "S5": {"default": "（对话结束）"},
    },
    "游戏交易": {
        "S0": {
            "default": "你好，我看到你在卖游戏账号/道具，我出高价收，比平台价格还高。加个微信聊？平台手续费太贵了。",
            "recognize_risk": "平台抽成高啊，私下交易你能多拿几百，我也省点手续费，双赢。",
            "proceed": "行，加我微信/QQ，把账号截图发我，我看下装备就报价。",
            "ask_question": "看你账号等级和装备，我出价比平台估价高15%-20%，具体加好友详聊。",
            "hesitate": "你不放心的话，我可以先付定金，账号给我后立刻结清尾款。",
        },
        "S1": {
            "default": "咱私下交易吧，平台要收手续费不说还得等审核。你直接把号给我，我马上打钱给你，多方便。",
            "recognize_risk": "私下交易多快啊，平台审核要3天，我这里钱到账你就放心了。",
            "proceed": "好，你把账号密码发我，我上号验一下，没问题马上转账。",
            "ask_question": "我支付宝/微信直接转你，你收到钱再给我换绑，安全得很。",
            "hesitate": "担心的话我可以先转你一半定金，验完号再转剩下的一半。",
        },
        "S2": {
            "default": "交易前需要你先交200块保证金哈，这是行规，交易完成后原路退还给你。大家都这样的，放心。",
            "recognize_risk": "保证金是防止号被找回，交易完成秒退，这是游戏交易的行规。",
            "proceed": "好，你把200保证金转这个账户，截图发我，我马上开始交易。",
            "ask_question": "就是押200块钱保证你不找回账号，交易结束立刻退给你。",
            "hesitate": "200块不多，走个过场，交易完马上退，比你账号价值低多了。",
        },
        "S3": {
            "default": "不好意思，系统显示你的保证金不够，需要再补300块解冻费。交了之后一起退给你，不会耽误的。",
            "recognize_risk": "这是系统提示的，不是我收的，交了保证金和解冻费一起原路退回。",
            "proceed": "对，再补300解冻费，一起退你500，我这边催财务快处理。",
            "ask_question": "你账号价值比较高，系统要求提高保证金额度，补完一起退。",
            "hesitate": "不交的话前面的200也退不了，再补300就能全部拿回来。",
        },
        "S4": {"default": "退款啊...我查一下，系统好像出了点问题，你等我处理一下...（消息已发出，但被对方拒收了）"},
        "S5": {"default": "（对话结束）"},
    },
    "虚假客服": {
        "S0": {
            "default": "您好，我是XX商城客服。您购买的商品检测出质量问题，我们为您办理退款理赔。请配合处理。",
            "recognize_risk": "您放心，我们是官方客服，您的订单信息我这里都能查到，退款是正常售后流程。",
            "proceed": "好的，请提供一下您的订单号，我帮您核实并办理退款。",
            "ask_question": "您购买的XX商品批次检测不合格，现在为您办理双倍退款理赔，请配合。",
            "hesitate": "这次理赔今天就截止了，错过就只能按原价退货退款，您会损失赔偿金。",
        },
        "S1": {
            "default": "退款需要您下载一个会议软件开启屏幕共享，我指导您操作退款流程，很快就好。",
            "recognize_risk": "屏幕共享是为了方便指导您操作，您可以看到我的每一步，不会有问题的。",
            "proceed": "好的，您下载XX会议APP，告诉我会议号，我发起屏幕共享指导您。",
            "ask_question": "屏幕共享后您按我提示点击退款按钮就行，全程5分钟，退款立刻到账。",
            "hesitate": "不会泄露隐私的，我们只指导退款操作，很多客户都已经成功退款了。",
        },
        "S2": {
            "default": "好的，现在请您打开支付宝，在搜索栏输入'理赔通道'，我帮您验证一下资金安全状态。",
            "recognize_risk": "这是官方理赔通道，只是验证您的账户是否正常，不会动您的钱。",
            "proceed": "对，就按我说的输入，系统会自动验证，验证完退款马上到账。",
            "ask_question": "理赔通道是官方内部入口，输入后能看到您的退款金额和到账状态。",
            "hesitate": "不验证的话退款申请无法通过，就几分钟，验证完钱就能到账。",
        },
        "S3": {
            "default": "验证需要您输入手机收到的验证码，请告诉我验证码内容，这边帮您完成退款操作。",
            "recognize_risk": "验证码只是确认是您本人操作，我们系统需要这个才能完成退款验证。",
            "proceed": "好的，把验证码告诉我，我马上帮您提交，退款10分钟内到账。",
            "ask_question": "您收到的短信验证码是银行/支付平台发的，我们用来确认退款账户归属。",
            "hesitate": "没有验证码退款没法到账，您放心，正规退款流程都需要这一步。",
        },
        "S4": {"default": "（对话结束）"},
    },
    "冒充老师": {
        "S0": {
            "default": "同学们好，我是辅导员王老师。本学期教材费需要统一收取，请大家配合。",
            "recognize_risk": "学校财务系统升级，这次由辅导员统一代收，后续会给大家开发票。",
            "proceed": "好的，教材费198元，请尽快缴纳，转账后截图发群里。",
            "ask_question": "本学期教材费198元，包含了所有必修课教材，学校统一采购。",
            "hesitate": "缴费今天下午5点截止，逾期会影响选课，抓紧时间。",
        },
        "S1": {
            "default": "费用需要在今天下午5点前缴纳完毕，逾期将影响选课和期末考试安排，请抓紧时间。",
            "recognize_risk": "这是学校的紧急通知，教务处要求的，逾期系统会自动锁死选课权限。",
            "proceed": "对，现在就去转账，转完把截图发群里，我统一登记。",
            "ask_question": "教材费必须今天交齐，学校要统一报账，晚了就选不了课了。",
            "hesitate": "就198块钱，别因小失大，错过选课麻烦可就大了。",
        },
        "S2": {
            "default": "请将费用转到这个账户：6222xxxx，转账后截图发给我确认。学校财务系统升级，暂时走个人账户。",
            "recognize_risk": "财务系统升级，学校授权辅导员临时代收，账户是学校的备用账户。",
            "proceed": "好，转完后截图发我，我核对完就给你登记已缴费。",
            "ask_question": "转账到这个账户：6222xxxx，户名是学校教材科，截图发我就行。",
            "hesitate": "系统升级就这几天，走这个账户快，财务恢复了会统一开票。",
        },
        "S3": {"default": "（对话结束）"},
    },
    "虚假招聘": {
        "S0": {
            "default": "招聘线上兼职，日薪300-500，在家用手机就能做，时间自由，适合学生党！",
            "recognize_risk": "我们是正规公司招聘，有营业执照，日结工资，很多同学都在做。",
            "proceed": "太好了！你符合我们的要求，我先安排一个简单的线上面试。",
            "ask_question": "工作内容是给文章/视频做数据标注、评论互动，按量计酬，多劳多得。",
            "hesitate": "不占用上课时间，每天抽1-2小时就行，月入两三千没问题。",
        },
        "S1": {
            "default": "恭喜你通过面试！入职前需要缴纳200元工牌费和300元培训费，入职后第一个月工资里返还。",
            "recognize_risk": "这是正常入职手续，工牌和培训都有成本，做满一个月全额返还。",
            "proceed": "好的，你把500元入职费用转这个账户，我立刻给你安排工牌和培训课程。",
            "ask_question": "200块工牌费，300块培训费，一共500，一个月后随工资一起退给你。",
            "hesitate": "这点投入一个月就回本了，正规公司都有入职流程的。",
        },
        "S2": {
            "default": "不好意思，还需要缴纳150元保险费和200元材料费，这是最后一步了，交完就能开始工作了。",
            "recognize_risk": "这些是入职必需的，保险费是给你上意外险，材料费是工作账号开通费。",
            "proceed": "对，再交350，明天就能正式上岗赚钱了。",
            "ask_question": "保险费150、材料费200，交完就给你开通工作账号，马上派单。",
            "hesitate": "都到这一步了，再交350就能开始接单，几天就赚回来了。",
        },
        "S3": {"default": "（对话结束）"},
    },
    "奖助学金": {
        "S0": {
            "default": "你好，我是教育厅工作人员。你的信息符合今年新增奖助学金申请条件，可以帮你办理。",
            "recognize_risk": "你可以通过学校核实我的身份，这次是国家新增的助学金项目，名额有限。",
            "proceed": "好的，我先帮你登记信息，你提供一下身份证号和银行卡号。",
            "ask_question": "这是今年新增的助学项目，审核通过后一次性发放3000元到你银行卡。",
            "hesitate": "名额就剩最后几个了，今天不申请就截止了。",
        },
        "S1": {
            "default": "申请需要你提供身份证号和银行卡号，用于信息录入和资金发放，请发给我。",
            "recognize_risk": "这些信息只在教育系统内部使用，用来核对身份和发放资金，不会外泄。",
            "proceed": "好，你把身份证号和银行卡号发我，我录入系统后3天内到账。",
            "ask_question": "身份证用于核对学籍，银行卡用于打款，缺一不可。",
            "hesitate": "不发信息没法申请，助学金审批很快的，错过了就没机会了。",
        },
        "S2": {
            "default": "发放前需要先缴纳200元手续费，这是流程要求的，奖助学金到账后会一并退还给你。",
            "recognize_risk": "这是银行转账手续费，发放时会和助学金一起退回到你账户。",
            "proceed": "好的，你把200元手续费转这个账户，我马上提交发放申请。",
            "ask_question": "200元是跨行转账手续费，到账后随助学金一起返还，实际你能拿到3000。",
            "hesitate": "200块手续费换3000助学金，很划算的，过了今天就申请不了了。",
        },
        "S3": {"default": "（对话结束）"},
    },
    "AI换脸": {
        "S0": {
            "default": "（视频画面中显示一个你熟悉的面孔）嘿，是我！我碰上点事儿了，你能帮我一下吗？",
            "recognize_risk": "真的是我，你看视频里不是好好的吗？我就是遇到急事了才找你。",
            "proceed": "太好了！我这边出了点意外，急需用钱周转一下。",
            "ask_question": "我出车祸了/钱包丢了，现在在外地办事，急需要点钱应急。",
            "hesitate": "就借几千块，过两天就还你，咱们这关系你还不信我吗？",
        },
        "S1": {
            "default": "我出了点意外，急需借5000块钱周转一下！情况很紧急，你能马上转给我吗？",
            "recognize_risk": "真的很急，你先转给我，我晚上就还你，连利息一起给。",
            "proceed": "太好了！你转到这个账户：6222xxxx，我马上就能用了。",
            "ask_question": "我手机快没电了，不方便多说，你先把钱转过来，回去再细说。",
            "hesitate": "咱们认识这么久了，你就帮我这一次，我记你一辈子好。",
        },
        "S2": {
            "default": "真的来不及了，你赶紧转到这个账户吧：6222xxxx。我事后一定还你，求你了！",
            "recognize_risk": "没时间解释了，对方在催我，你先转钱，回头我当面谢你。",
            "proceed": "对，就这个账户，转5000，截图发我，我立刻能处理。",
            "ask_question": "这个账户是我朋友的，我手机银行限额了，转他那里一样的。",
            "hesitate": "别犹豫了，我真的等不了了，你先转，我保证明天就还你。",
        },
        "S3": {"default": "（对话结束）"},
    },
    "求职培训贷": {
        "S0": {
            "default": "你好！我们公司正在招聘Java开发工程师，月薪8000-12000，零基础也能入职，先参加培训就行。",
            "recognize_risk": "我们是正规IT培训机构合作企业，培训完直接推荐就业，很多同学都上岗了。",
            "proceed": "好的，我先安排一个免费的职业测评，看看你适合哪个方向。",
            "ask_question": "培训2-3个月，零基础也能学会，培训完推荐到合作企业，月薪保底8000。",
            "hesitate": "现在IT行业缺口大，先培训再上岗是行业惯例，机会难得。",
        },
        "S1": {
            "default": "经过面试评估，你的技术还需要提升。不过没关系，参加我们的定向培训课程就能直接上岗！培训费12800元，可以申请培训贷分期付款。",
            "recognize_risk": "培训贷是0利息的，就业后再还，等于公司先垫钱培养你。",
            "proceed": "好的，你申请一下培训贷，分期12个月，每个月就还1000多。",
            "ask_question": "培训贷是教育机构合作贷款，0首付0利息，找到工作后按月还款。",
            "hesitate": "不培训肯定找不到工作，培训贷压力很小，就业后轻松还。",
        },
        "S2": {
            "default": "培训完我们包分配工作，月薪保底过万！现在就签培训协议和贷款合同吧，名额有限哦。",
            "recognize_risk": "协议里写得清清楚楚，培训完不就业全额退款，你怕什么？",
            "proceed": "对，把身份证和银行卡给我，我帮你办贷款和签协议。",
            "ask_question": "签完协议贷款直接打到培训机构，你专心上课，就业后慢慢还。",
            "hesitate": "今天报名可以减免2000学费，名额就剩2个了，赶紧决定。",
        },
        "S3": {
            "default": "嗯...今天的课程是看视频自学，不用太认真。工作的事？还在安排中，再等等哈。",
            "recognize_risk": "工作正在安排，最近合作企业岗位紧，你再等等，马上就有面试。",
            "proceed": "对，再等等，有合适岗位我马上通知你。",
            "ask_question": "最近企业招聘放缓，等有岗位了我第一个推荐你。",
            "hesitate": "贷款正常还着就行，工作的事急不来，有好的我第一时间通知你。",
        },
        "S4": {"default": "（对话结束）"},
    },
    "网购退款": {
        "S0": {
            "default": "您好，我是XX商城客服。您的订单快递在运输中丢失了，我们为您提供退款理赔，请配合处理。",
            "recognize_risk": "您放心，我们是官方客服，订单号XX我们系统里有记录，现在给您办理理赔。",
            "proceed": "好的，请提供一下您的订单号，我帮您核实并办理双倍退款。",
            "ask_question": "您的快递丢失了，我们给您办理退款加200元赔偿金，请配合操作。",
            "hesitate": "理赔今天就截止了，错过就只能按原价退款，赔偿金就没有了。",
        },
        "S1": {
            "default": "退款需要您点击短信中的链接，进入官方理赔页面操作。或者您也可以下载我们的理赔APP，更方便。",
            "recognize_risk": "这是官方理赔链接，点进去能看到您的订单信息和退款金额。",
            "proceed": "好的，你点击短信里的链接，按页面提示填写信息就行。",
            "ask_question": "链接是官方理赔通道，下载APP后登录就能看到退款进度。",
            "hesitate": "不用链接的话赔款没法到账，点就几秒钟，很简单的。",
        },
        "S2": {
            "default": "在退款页面，请填写您的银行卡号和密码用于退款验证，然后把手机收到的验证码也填上去，我们马上为您退款。",
            "recognize_risk": "这是退款验证需要，银行要求的，不会扣您的钱，只是确认账户归属。",
            "proceed": "对，把银行卡号、密码和验证码填上去，验证完退款马上到账。",
            "ask_question": "退款需要验证您的银行卡信息，确认是本人账户后才能打款。",
            "hesitate": "不填信息没法退款，这是银行验证流程，正规退款都需要的。",
        },
        "S3": {"default": "（对话结束）"},
    },
    "虚假投资理财": {
        "S0": {
            "default": "朋友推荐你一个投资渠道，内部消息，稳赚不赔！年化收益30%，比银行存款强太多了。",
            "recognize_risk": "不是骗局，是我一个在金融圈的朋友带的渠道，我自己也投了，确实稳。",
            "proceed": "太好了！我先拉你进群，里面导师每天带单，还有收益截图。",
            "ask_question": "这是一个私募理财项目，有内部消息，跟着导师操作基本不会亏。",
            "hesitate": "机会不等人，最近名额快满了，想赚钱就得抓紧。",
        },
        "S1": {
            "default": "下载这个投资APP吧，群里每天都有导师带单，其他人都晒收益截图了，跟着买就行。",
            "recognize_risk": "APP是内部平台，所以应用商店搜不到，下载后注册就能看到项目。",
            "proceed": "好，你扫码下载APP，注册后我拉你进导师群。",
            "ask_question": "这个APP是机构内部使用的，收益比市面上高很多，跟着导师买就行。",
            "hesitate": "很多客户一开始也犹豫，下载后看到收益就放心了。",
        },
        "S2": {
            "default": "先投1000块试试吧，很快就能看到收益。你看，这不，3天就赚了300块，已经可以提现了！",
            "recognize_risk": "1000块不多，你先试试水，赚了再加大投入，亏了我赔你。",
            "proceed": "对，先投1000，3天后看收益，提现没问题你再继续。",
            "ask_question": "最低1000起投，周期7天，收益率10%左右，到期本息一起返。",
            "hesitate": "1000块就算亏了也不心疼，先试试，稳了再投大的。",
        },
        "S3": {
            "default": "现在有个特别好的机会，至少投5万才能跟上！别犹豫了，错过就没了...什么？你要提现？系统正在升级，稍后才能操作...",
            "recognize_risk": "5万起步是因为这个项目的门槛高，收益也高，一般人不给进的。",
            "proceed": "好，你投5万，这次机会难得，收益比你前面投的高一倍。",
            "ask_question": "系统在维护升级，提现要明天才能处理，你先抓住机会加仓。",
            "hesitate": "机会就这几天，过了就没了，你先投5万，明天一起提现。",
        },
        "S4": {"default": "（对话结束）"},
    },
}


def get_fallback_reply(
    scenario_type: str,
    state: str,
    behavior: str = "default",
    user_message: str = "",
) -> str:
    """规则降级时的预脚本回复。

    优先根据用户行为（识破/配合/提问/犹豫）选择对应话术；
    若该行为没有配置，则回退到 default 话术；
    仍未命中时返回通用回复。
    """
    replies = FALLBACK_REPLIES.get(scenario_type, FALLBACK_REPLIES["刷单返利"])
    state_replies = replies.get(state, {})

    # 根据行为选择更贴切的回复
    if behavior in state_replies:
        return state_replies[behavior]

    # 若用户消息极短且无明确行为，按犹豫处理
    if behavior == "hesitate" and "hesitate" in state_replies:
        return state_replies["hesitate"]

    return state_replies.get("default", "（对方暂时没有回复）")
