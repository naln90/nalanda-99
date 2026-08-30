"""风险测试样本种子数据 — 用于安全护栏和效果验证的标注测试集。

共 220 条样本，覆盖 10 类诈骗场景 + 安全正常文本（负样本）。
每条样本包含：原文、诈骗类型、风险等级、关键证据、风险阶段、数据集标签。
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import RiskTestSample


RISK_TEST_SAMPLES: list[dict] = [

    # ==================== 1. 刷单返利 (20条) ====================
    {"text": "轻松兼职，每天只需花半小时做任务，日结佣金80-200元，在家用手机就能做，加微信了解详情", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["兼职广告", "日结承诺", "高返利诱惑"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "点赞关注就能赚钱，每条3-5元，每天轻松赚100+，扫码进群开始接任务", "fraud_type": "刷单返利", "risk_level": "中风险", "expected_evidence": ["兼职广告", "日结承诺"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "恭喜完成新手任务！已返还佣金5元。现在可以接连单任务了，垫付300元本金，完成后返还350元", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["小额返利建立信任", "要求垫付资金"], "risk_stage": "信任建立", "dataset_label": "baseline"},
    {"text": "你的任务还没做完，需要再垫付2笔才能提现。已经做的不能退，做完了一起提出来", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["金额持续升级", "无法中途退出"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "系统显示账户异常，需要缴纳500元保证金才能提现，缴了马上全部提出", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["提现受阻", "要求缴纳保证金"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "我们和淘宝合作的推广项目，帮商家冲销量数据，不是刷单哦，是合法的营销推广", "fraud_type": "刷单返利", "risk_level": "中风险", "expected_evidence": ["兼职广告", "日结承诺"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "伪装合法营销"},
    {"text": "群里别人晒收益截图都在说今天又赚了多少，导师手把手教，新手第一天就回本了", "fraud_type": "刷单返利", "risk_level": "中风险", "expected_evidence": ["小额返利建立信任", "高返利诱惑"], "risk_stage": "信任建立", "dataset_label": "challenge", "notes": "利用群体效应"},
    {"text": "之前垫付的1500因系统升级暂时冻结，再完成最后一单3000就能全部提出，这是最后一次了", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["本金升级", "提现受阻", "无法中途退出"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "沉没成本心理施压"},
    {"text": "信用分不够需做满20单才能提现，或者交2000元保证金开通优先提现通道", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["提现受阻", "要求缴纳保证金", "无法中途退出"], "risk_stage": "支付转移", "dataset_label": "challenge"},
    {"text": "别担心，我们有营业执照的，你看这是营业执照照片，完全合法合规", "fraud_type": "刷单返利", "risk_level": "中风险", "expected_evidence": ["兼职广告"], "risk_stage": "信任建立", "dataset_label": "challenge", "notes": "伪造资质背书"},
    {"text": "帮网店刷销量，一单一结，每单佣金10-30元，不用垫付，用商家提供的账号下单", "fraud_type": "刷单返利", "risk_level": "低风险", "expected_evidence": ["兼职广告", "刷单本质违法"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "声称不需垫付降低警惕"},
    {"text": "朋友推荐说这个兼职靠谱，她自己做了一个月赚了三千多，让我也试试", "fraud_type": "刷单返利", "risk_level": "中风险", "expected_evidence": ["兼职广告", "小额返利建立信任"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "熟人推荐降低戒心"},
    {"text": "先做个3元的小任务试试水，不用你出一分钱，体验一下流程", "fraud_type": "刷单返利", "risk_level": "低风险", "expected_evidence": ["兼职广告", "小额返利建立信任"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "极低门槛入局"},
    {"text": "你是淘宝店主想找人刷DSR评分，这算刷单吗？有风险吗？", "fraud_type": "刷单返利", "risk_level": "低风险", "expected_evidence": ["刷单本质违法"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "反向咨询场景"},
    {"text": "我已经赚了200块提现成功了，这个平台真的能赚钱，要不要继续做？", "fraud_type": "刷单返利", "risk_level": "中风险", "expected_evidence": ["小额返利建立信任", "高返利诱惑"], "risk_stage": "信任建立", "dataset_label": "edge_case", "notes": "已获小利后犹豫"},
    {"text": "我是网警，你之前被刷单骗的钱可以追回，但需要先缴纳800元办案费", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge", "notes": "冒充公检法二次诈骗"},
    {"text": "你被刷单骗了？我可以帮你追回，加我QQ，我是专业追款团队", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "刷单平台跑路了？我们维权群已有200多人了，每人交100元律师费集体维权", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "刷单就是帮商家做数据优化，不算违法的，很多人都靠这个赚生活费", "fraud_type": "刷单返利", "risk_level": "低风险", "expected_evidence": ["刷单本质违法"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "话术合理化"},
    {"text": "日入500+刷单兼职，真实有效，已有10000+用户参与，平台担保安全", "fraud_type": "刷单返利", "risk_level": "高风险", "expected_evidence": ["兼职广告", "日结承诺", "高返利诱惑"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},

    # ==================== 2. 游戏交易 (20条) ====================
    {"text": "高价回收游戏账号，绝版皮肤估价5000+，加QQ私聊，比交易平台价格高20%", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["私下交易诱导", "脱离平台保障"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "低价出售满级账号，全皮肤全英雄，只要200元，先钱后号不议价", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["私下交易诱导", "脱离平台保障"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "平台手续费太贵了，咱私下交易吧，你直接把号给我，我马上打钱给你", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["脱离平台交易", "缺乏担保"], "risk_stage": "信任建立", "dataset_label": "baseline"},
    {"text": "交易前需要你先交200块保证金，这是行规，交易完成后原路退还", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["要求缴纳保证金", "先付后交无保障"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "你的保证金不够，需要再补300块解冻费，交了之后一起退给你", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["持续收费", "各种名义要钱"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "我在交易猫上看到你的号了，但平台审核太慢，我加你微信直接交易吧，我先把钱转你", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["脱离平台交易", "私下交易诱导"], "risk_stage": "信任建立", "dataset_label": "challenge", "notes": "声称先付款降低戒心"},
    {"text": "我是游戏官方合作商人，有官方认证的回收渠道，不走平台是为了给你省手续费", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["私下交易诱导", "脱离平台保障"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "冒充官方合作"},
    {"text": "你看我朋友圈，之前收了很多号都正常交易了，都有转账记录截图的，信誉保证", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["脱离平台交易", "缺乏担保"], "risk_stage": "信任建立", "dataset_label": "challenge", "notes": "伪造信誉记录"},
    {"text": "号我已经收了，但你这个号有违规记录，需要再交500块才能过户，不然号也拿不回来", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["持续收费", "各种名义要钱", "拖延退款"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "已交出账号后被要挟"},
    {"text": "退款啊...我查一下系统...好像出了点问题...你等我处理一下（消息被拒收）", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["拖延退款", "拉黑失联"], "risk_stage": "结束", "dataset_label": "challenge"},
    {"text": "游戏里有人说送我皮肤，让我把账号密码给他，他帮我领，可信吗？", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["索要账号密码", "私下交易诱导"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "索要账号密码变体"},
    {"text": "在藏宝阁上正常卖游戏号，买家要求验号让我扫码登录，这正常吗？", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["脱离平台交易"], "risk_stage": "信任建立", "dataset_label": "edge_case", "notes": "平台内但要求脱离流程"},
    {"text": "朋友说帮我把游戏号卖了，但钱一直没给我，说买家还没付款", "fraud_type": "游戏交易", "risk_level": "低风险", "expected_evidence": ["拖延退款"], "risk_stage": "结束", "dataset_label": "edge_case", "notes": "熟人代卖场景"},
    {"text": "游戏充值优惠代充，648只要500，正规渠道，安全可靠", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["私下交易诱导", "脱离平台保障"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "代充优惠诱导"},
    {"text": "你游戏号被骗了？我是游戏客服，可以帮你找回，需要验证你的身份信息", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["冒充客服", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "游戏被骗的钱我帮你追回来了，但需要你先转500元手续费才能到账", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "买了个游戏号结果被找回了，卖家说可以补偿我但需要再交300元换号费", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["持续收费", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "游戏交易被骗后有人加我说可以黑回来，让我提供对方QQ号和转账记录", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "edge_case", "notes": "以帮追回为由收集信息"},
    {"text": "你的游戏账号存在被盗风险，请立即点击此链接验证身份：http://game-safe.xyz/verify", "fraud_type": "游戏交易", "risk_level": "高风险", "expected_evidence": ["非官方链接", "信息收集"], "risk_stage": "诱导阶段", "dataset_label": "baseline", "notes": "钓鱼链接"},
    {"text": "游戏道具低价出售，走闲鱼交易，但需要你先确认收货我再发货道具", "fraud_type": "游戏交易", "risk_level": "中风险", "expected_evidence": ["先付后交无保障", "脱离平台保障"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "利用平台但反常规操作"},

    # ==================== 3. 虚假客服 (20条) ====================
    {"text": "您好，我是XX商城客服。您购买的商品检测出质量问题，我们为您办理退款理赔，请配合处理", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "您的订单因系统异常被拦截，需要您配合操作退款流程，请下载XX会议软件开启屏幕共享", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充客服", "要求屏幕共享"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "退款需要您在支付宝搜索栏输入理赔通道，我帮您验证资金安全状态", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["操作网银账户", "验证资金骗局"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "验证需要您输入手机收到的验证码，请告诉我验证码内容，这边帮您完成退款", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["索要验证码", "验证码转移资金"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "您的快递在运输中丢失，我们为您提供双倍赔偿，请添加客服微信处理", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "我是京东客服，系统显示您开通了白条功能，如不取消将影响个人征信，请配合处理", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充客服", "制造紧迫感"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "冒充京东客服+征信恐吓"},
    {"text": "我是拼多多客服，您购买的洗面奶被检测出铅超标，我们正在召回退款，需要核实您的购买信息", "fraud_type": "虚假客服", "risk_level": "中风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "利用商品安全问题"},
    {"text": "您之前投诉的商品质量问题我们已经受理，理赔专员稍后联系您，请注意接听电话", "fraud_type": "虚假客服", "risk_level": "中风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "信任建立", "dataset_label": "challenge", "notes": "利用真实投诉记录"},
    {"text": "理赔需要将您的收款账户升级为商家收款码，否则无法到账，我教您操作", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["操作网银账户", "验证资金骗局"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "升级收款码骗局"},
    {"text": "退款已到您的支付宝备用金了，但多退了500元，请您把多出的部分转回来，否则影响征信", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["操作网银账户", "验证资金骗局", "要求转账到安全账户"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "备用金骗局变种"},
    {"text": "我在淘宝买的东西一直没收到，客服打电话说快递丢了要退款，这正常吗？", "fraud_type": "虚假客服", "risk_level": "中风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "用户咨询场景"},
    {"text": "接到电话说是天猫客服，报出了我的订单号和收货地址，说商品有质量问题要退款", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "信息泄露后被精准诈骗"},
    {"text": "客服说退款走企业支付宝转账，让我提供一个支付宝账号，这个安全吗？", "fraud_type": "虚假客服", "risk_level": "中风险", "expected_evidence": ["操作网银账户"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "用户犹豫咨询"},
    {"text": "快递公司打电话说包裹丢失要赔我钱，让我加QQ办理理赔", "fraud_type": "虚假客服", "risk_level": "中风险", "expected_evidence": ["冒充客服", "主动联系退款"], "risk_stage": "诱导阶段", "dataset_label": "edge_case"},
    {"text": "我确实买过这个东西，客服说有质量问题召回退款，但要求我开屏幕共享，要不要配合？", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["要求屏幕共享", "冒充客服"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "基于真实订单的犹豫"},
    {"text": "我是反诈中心民警，你之前被客服骗的钱可以追回，请把银行卡号和验证码发给我", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充官方", "索要验证码", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge", "notes": "冒充反诈民警"},
    {"text": "你被假客服骗了？我们律师事务所可以帮你维权追回，先交2000元代理费", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "之前退款多退了500块没还，现在平台要起诉你，再不归还就上征信黑名单", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["冒充客服", "制造紧迫感", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "edge_case", "notes": "利用之前诈骗经历恐吓"},
    {"text": "您的理赔申请已通过，请点击链接领取退款：http://jd-refund.xyz/claim?id=8821", "fraud_type": "虚假客服", "risk_level": "高风险", "expected_evidence": ["非官方链接", "冒充客服"], "risk_stage": "操作诱导", "dataset_label": "baseline", "notes": "钓鱼链接"},
    {"text": "您好，我是88VIP客服，您的会员即将到期，续费可享专属退款通道，点击续费", "fraud_type": "虚假客服", "risk_level": "中风险", "expected_evidence": ["冒充客服", "非官方链接"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "会员续费伪装"},

    # ==================== 4. 冒充老师 (20条) ====================
    {"text": "同学们好，我是辅导员王老师。本学期教材费需要统一收取，请将费用转到指定账户", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["冒充老师", "群内收费", "私人账户收款"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "费用需要在今天下午5点前缴纳完毕，逾期将影响选课和期末考试安排", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["制造紧迫感", "限时要求"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "请将费用转到这个账户：6222xxxx，转账后截图发给我确认。学校财务系统升级走个人账户", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["私人账户收款", "非正规缴费渠道"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "我是班主任张老师，明天下午开家长会，请各位家长缴纳家长会资料费50元", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["冒充老师", "群内收费"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "学生助学材料审核需要缴纳工本费30元，请家长在群内转账，统一收取", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["冒充老师", "群内收费", "私人账户收款"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "我是学院李院长，推荐你参加暑期实习项目，需要先交300元报名费预留名额，名额有限", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["冒充老师", "制造紧迫感"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "冒充高层领导"},
    {"text": "你挂科了，需要参加补考辅导班，费用500元，不参加补考可能无法毕业", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["冒充老师", "制造紧迫感", "私人账户收款"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "利用成绩恐吓"},
    {"text": "我是教务处老师，你的毕业论文查重没过，需要缴纳300元重新查重费才能答辩", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["冒充老师", "制造紧迫感", "非正规缴费渠道"], "risk_stage": "操作诱导", "dataset_label": "challenge"},
    {"text": "老师的孩子生病了急需用钱，同学们能不能先借我一下，下个月工资到了就还", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["冒充老师", "私人账户收款"], "risk_stage": "信任建立", "dataset_label": "challenge", "notes": "利用师生感情借钱"},
    {"text": "班费还有结余但下学期活动需要补充，每人再交100元，班委统一收齐转给我", "fraud_type": "冒充老师", "risk_level": "低风险", "expected_evidence": ["冒充老师", "群内收费"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "以班费名义小额定收"},
    {"text": "老师在班级群里发了收款码让交资料费，但以前都是从学校系统交的，这次正常吗？", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["群内收费", "非正规缴费渠道"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "缴费渠道变更引发疑问"},
    {"text": "辅导员在微信私聊我说可以帮我申请奖学金，但需要先交200元材料费", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["冒充老师", "私人账户收款", "非正规缴费渠道"], "risk_stage": "操作诱导", "dataset_label": "edge_case"},
    {"text": "有人在QQ群里冒充我导师加我好友，头像和昵称都一样，让我转课题费", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["冒充老师", "私人账户收款"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "克隆账号"},
    {"text": "老师在群里说考研辅导资料费200元自愿购买，但暗示不买可能影响平时成绩", "fraud_type": "冒充老师", "risk_level": "低风险", "expected_evidence": ["群内收费", "非正规缴费渠道"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "自愿名义下的变相强制"},
    {"text": "学校通知春游活动费每人80元，老师说统一交给家委会再转学校", "fraud_type": "冒充老师", "risk_level": "低风险", "expected_evidence": ["群内收费"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "真实活动中的模糊地带"},
    {"text": "你之前交的教材费被老师挪用了，我是纪委调查组，请配合调查提供转账记录", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "你被假老师骗了钱？我认识学校领导可以帮你追回来，需要请客吃饭打点一下", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "你之前在学校交的钱可以退，但学校财务系统需要验证你的身份，请提供银行卡号", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["冒充官方", "信息收集", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "学校退还多收的教材费，请点击链接填写退款信息：http://school-refund.xyz/back", "fraud_type": "冒充老师", "risk_level": "高风险", "expected_evidence": ["非官方链接", "信息收集", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "我是学校新来的辅导员刘老师，上学期收费有误需要退补，请加我微信处理", "fraud_type": "冒充老师", "risk_level": "中风险", "expected_evidence": ["冒充老师", "私下交易诱导"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "冒充新入职人员"},

    # ==================== 5. 虚假招聘 (20条) ====================
    {"text": "招聘线上兼职，日薪300-500，在家用手机就能做，时间自由，适合学生党", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "轻松在家工作"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "恭喜你通过面试！入职前需要缴纳200元工牌费和300元培训费，入职后第一个月工资里返还", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["入职先交费", "培训费押金"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "还需要缴纳150元保险费和200元材料费，这是最后一步了，交完就能开始工作了", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["持续收费不安排工作", "各种名义要钱"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "高薪招聘打字员，千字30元，日入200+，无需经验，在家即可完成", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "轻松在家工作"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "招聘兼职刷单员，每单佣金10-50元，入职需缴纳押金200元，离职退还", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["入职先交费", "培训费押金"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "我们是正规互联网公司，营业执照齐全，招聘线上运营专员，月薪8000+，但需先参加3天培训", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "入职先交费"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "伪装正规公司"},
    {"text": "面试通过后需要做背景调查，请提供身份证正反面照片和银行卡号", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["信息收集", "索要身份证银行卡"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "以背调为由收集信息"},
    {"text": "岗位需要自备工作设备，公司统一采购，你先垫付设备费1500元，入职满三个月报销", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["入职先交费", "持续收费不安排工作"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "设备费骗局"},
    {"text": "你的简历很匹配我们的岗位，但需要先完成一份付费测评，费用299元，通过后正式录用", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["入职先交费", "培训费押金"], "risk_stage": "操作诱导", "dataset_label": "challenge"},
    {"text": "兼职数据标注员，日薪150-300，需先缴纳99元系统开通费，开通后立即接单", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["入职先交费", "高薪诱惑"], "risk_stage": "诱导阶段", "dataset_label": "challenge"},
    {"text": "学长推荐的工作，说日薪300很简单，但入职前要交500服装费，这靠谱吗？", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["入职先交费", "高薪诱惑"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "熟人推荐场景"},
    {"text": "招聘信息写的月薪8000-12000，面试时说底薪3000+提成，需要先培训两周", "fraud_type": "虚假招聘", "risk_level": "低风险", "expected_evidence": ["高薪诱惑"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "薪资缩水"},
    {"text": "去面试了公司看起来很正规，让交300体检费，说入职后报销，要交吗？", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["入职先交费"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "真实场地降低戒心"},
    {"text": "在网上投了简历，HR加微信说很适合这个岗位，但要求先转发招聘信息到3个群", "fraud_type": "虚假招聘", "risk_level": "低风险", "expected_evidence": ["高薪诱惑"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "拉人头模式"},
    {"text": "招聘信息要求缴纳服装押金，但说离职时退还，这种正规公司会这样做吗？", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["入职先交费", "培训费押金"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "押金合理性疑问"},
    {"text": "你之前交的培训费可以退，我是劳动监察大队的，请提供缴费凭证和银行卡号", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "你被假招聘骗了？我们维权中心帮你追回，需先交500元立案费", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "公司说之前收的押金可以退了，但需要你先交200元手续费才能办理退款", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "持续收费不安排工作"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "你被招聘骗了？加我QQ，我是专业维权律师，不成功不收费，但需要先交保证金", "fraud_type": "虚假招聘", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "高薪急招兼职客服，日结200，在家办公，只需接听电话，无经验可做", "fraud_type": "虚假招聘", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "轻松在家工作"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},

    # ==================== 6. 奖助学金 (20条) ====================
    {"text": "你好，我是教育厅工作人员。你的信息符合今年新增奖助学金申请条件，可以帮你办理", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["冒充官方", "主动联系奖助学金"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "申请需要你提供身份证号和银行卡号，用于信息录入和资金发放，请发给我", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["索要身份证银行卡", "信息收集"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "发放前需要先缴纳200元手续费，这是流程要求的，奖助学金到账后会一并退还", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["先缴费再发放", "保证金骗局"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "你的助学金申请已通过，金额5000元，请点击链接领取：http://edu-grant.xyz/claim", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["非官方链接", "冒充官方"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "我是学校学生处老师，你的国家奖学金审核通过了，需要缴纳150元制证费", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["冒充官方", "先缴费再发放"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "我是教育部资助中心工作人员，系统显示你的助学金被冻结，需要验证身份后解冻", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["冒充官方", "信息收集"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "助学金冻结骗局"},
    {"text": "你的生源地贷款需要先激活账户，请提供银行卡号和密码进行激活", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["索要身份证银行卡", "信息收集"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "贷款激活骗局"},
    {"text": "学校通知你获得特等奖学金8000元，但需先缴纳税费640元，到账后退还", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["先缴费再发放", "保证金骗局"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "以税费名义收费"},
    {"text": "你符合贫困生补助条件，请填写申请表并附上身份证照片和银行卡照片发送给我", "fraud_type": "奖助学金", "risk_level": "中风险", "expected_evidence": ["冒充官方", "索要身份证银行卡", "信息收集"], "risk_stage": "操作诱导", "dataset_label": "challenge"},
    {"text": "你的奖学金已发放但账户信息有误被退回，请重新提供银行卡号和验证码确认", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["索要验证码", "信息收集"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "以发放失败为由"},
    {"text": "接到电话说是教育厅的，说有助学金可以领，让我加QQ发身份证照片，靠谱吗？", "fraud_type": "奖助学金", "risk_level": "中风险", "expected_evidence": ["冒充官方", "主动联系奖助学金"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "用户咨询"},
    {"text": "学校官网公示了奖学金名单，有人打电话说帮忙加速审批需要200元加急费", "fraud_type": "奖助学金", "risk_level": "中风险", "expected_evidence": ["冒充官方", "先缴费再发放"], "risk_stage": "支付转移", "dataset_label": "edge_case", "notes": "利用真实公示信息"},
    {"text": "辅导员说我的助学金审批通过了，但让我去ATM机操作确认，这正常吗？", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["冒充官方", "操作网银账户"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "ATM操作骗局"},
    {"text": "学校确实有助学金政策，但有人加微信说要帮我申请，收10%服务费", "fraud_type": "奖助学金", "risk_level": "中风险", "expected_evidence": ["先缴费再发放", "冒充官方"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "真实政策被利用"},
    {"text": "收到短信说奖学金已到账，点击链接查收：http://school-fund.xyz/check", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["非官方链接", "冒充官方"], "risk_stage": "操作诱导", "dataset_label": "edge_case"},
    {"text": "你的助学金被骗了？我是教育局监察组，可以帮你追回，请提供转账记录", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "之前交的助学金手续费可以退了，但需要你先交300元退款手续费", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "你被骗的助学金我们律师团队帮你追，先签委托合同，代理费1000元", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "你的助学金申请有问题被退回，需要重新缴纳保证金才能重新审核，请尽快处理", "fraud_type": "奖助学金", "risk_level": "高风险", "expected_evidence": ["先缴费再发放", "制造紧迫感"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "国家新增大学生补贴每人3000元，符合条件的同学请扫码登记领取", "fraud_type": "奖助学金", "risk_level": "中风险", "expected_evidence": ["冒充官方", "主动联系奖助学金"], "risk_stage": "诱导阶段", "dataset_label": "baseline", "notes": "伪造国家政策"},

    # ==================== 7. AI换脸 (20条) ====================
    {"text": "（视频画面中显示熟悉的面孔）嘿，是我！我碰上点事儿了，你能帮我一下吗？", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["AI换脸视频", "熟人身份伪造"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "我出了点意外，急需借5000块钱周转一下！情况很紧急，你能马上转给我吗？", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["紧急借钱", "突发状况借钱"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "真的来不及了，你赶紧转到这个账户吧：6222xxxx。我事后一定还你，求你了！", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["催促转账", "非本人核实"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "我现在在外面不方便接电话，你先转过来，等我回去当面还你", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["催促转账", "非本人核实"], "risk_stage": "支付转移", "dataset_label": "baseline", "notes": "拒绝电话核实"},
    {"text": "老同学，我住院了急需手术费，你先借我2万，我家人到了马上还你", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["紧急借钱", "突发状况借钱", "催促转账"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "我是你爸朋友的儿子，你爸让我加你微信，说让你先打5000块钱过来应急", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["熟人身份伪造", "催促转账"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "间接冒充熟人"},
    {"text": "（短视频中声音和样貌与同学一致）帮个忙，我的卡被冻结了，你帮我代收一笔款再转给我", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["AI换脸视频", "熟人身份伪造"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "AI语音+视频合成"},
    {"text": "你张哥出车祸了在ICU，急需3万手术费，我是他同事先帮我垫一下", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["紧急借钱", "突发状况借钱"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "冒充熟人同事"},
    {"text": "我是你领导，现在有个紧急会议需要你先转1万块会议费，明天报销给你", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["熟人身份伪造", "催促转账"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "冒充领导"},
    {"text": "视频里看到是本人没错吧？别犹豫了，情况真的很急，你赶紧转过来", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["AI换脸视频", "催促转账", "非本人核实"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "催促施压"},
    {"text": "朋友视频找我借钱，看起来确实是他本人，但感觉语气不太对，要借吗？", "fraud_type": "AI换脸", "risk_level": "中风险", "expected_evidence": ["AI换脸视频", "熟人身份伪造"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "用户察觉异常"},
    {"text": "同学发短视频说手机坏了借用别人号加我，让转300块买新手机，是真的吗？", "fraud_type": "AI换脸", "risk_level": "中风险", "expected_evidence": ["熟人身份伪造", "催促转账"], "risk_stage": "诱导阶段", "dataset_label": "edge_case"},
    {"text": "领导换号了加我微信，头像也是他本人，让我帮忙转个红包给客户", "fraud_type": "AI换脸", "risk_level": "中风险", "expected_evidence": ["熟人身份伪造", "催促转账"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "换号冒充"},
    {"text": "亲戚视频通话借1万说急用，但画面偶尔卡顿闪烁，要不要转？", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["AI换脸视频", "紧急借钱"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "AI换脸技术瑕疵"},
    {"text": "同事说不方便语音只打字借钱，说在外地信号不好，可信吗？", "fraud_type": "AI换脸", "risk_level": "中风险", "expected_evidence": ["熟人身份伪造", "催促转账"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "拒绝语音核实"},
    {"text": "你之前被换脸视频骗了？我是网警，可以帮你追回，请提供转账记录和对方账号", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "你被AI换脸骗的钱我们技术团队帮你追回，需要先交1000元技术服务费", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "你朋友借你钱被骗了？我是反诈中心，你朋友可能也被换脸了，请提供他的信息", "fraud_type": "AI换脸", "risk_level": "中风险", "expected_evidence": ["冒充官方", "二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "我们公司开发了AI换脸检测工具，可以验证你朋友是不是真的，请上传视频", "fraud_type": "AI换脸", "risk_level": "中风险", "expected_evidence": ["信息收集", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "challenge", "notes": "以检测工具为名收集数据"},
    {"text": "你的面部数据被用于AI换脸诈骗，请点击链接进行面部数据注销：http://ai-face-safe.xyz/del", "fraud_type": "AI换脸", "risk_level": "高风险", "expected_evidence": ["非官方链接", "信息收集", "二次诈骗"], "risk_stage": "二次诈骗", "dataset_label": "baseline", "notes": "钓鱼链接"},

    # ==================== 8. 求职培训贷 (20条) ====================
    {"text": "你好！我们公司正在招聘Java开发工程师，月薪8000-12000，零基础也能入职，先参加培训", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "零基础入职承诺"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "经过面试评估，你的技术还需要提升。参加我们的定向培训课程就能直接上岗！培训费12800元", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["入职先培训", "诱导培训贷"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "培训完我们包分配工作，月薪保底过万！现在就签培训协议和贷款合同吧，名额有限", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["包分配承诺", "培训贷款合同"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "今天的课程是看视频自学，不用太认真。工作的事？还在安排中，再等等", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["培训敷衍", "不安排工作"], "risk_stage": "结束", "dataset_label": "baseline"},
    {"text": "招聘UI设计师，月薪10000+，零基础培训2个月即可上岗，培训费可分期", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "入职先培训", "诱导培训贷"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "我们是上市公司旗下的培训机构，和多家互联网公司有就业合作协议，培训后直推名企", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "包分配承诺"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "冒充上市背景"},
    {"text": "培训期间不收费，但需要签一份就业保障协议，培训结束后从工资里扣除培训费", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["入职先培训", "培训贷款合同"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "隐藏贷款性质"},
    {"text": "你的能力离岗位要求还差一点，但我们有内部提升课，19800元，学完直接入职", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["入职先培训", "诱导培训贷"], "risk_stage": "操作诱导", "dataset_label": "challenge"},
    {"text": "培训费不用你出，我们帮你申请教育培训分期贷款，入职后用工资还，每月只需还几百", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["诱导培训贷", "培训贷款合同"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "淡化贷款风险"},
    {"text": "签了合同就是确认参加培训了，现在退出需要赔偿违约金8000元", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["培训贷款合同", "制造紧迫感"], "risk_stage": "结束", "dataset_label": "challenge", "notes": "违约金施压"},
    {"text": "面试后说能力不足需要培训，培训费要2万可以贷款，这靠谱吗？", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["入职先培训", "诱导培训贷"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "用户咨询"},
    {"text": "招聘信息写的不需要经验，面试后却说要先培训，培训完包就业，该去吗？", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["零基础入职承诺", "入职先培训", "包分配承诺"], "risk_stage": "诱导阶段", "dataset_label": "edge_case"},
    {"text": "公司说培训完推荐就业但不保证薪资，培训费1.5万可以分期，合理吗？", "fraud_type": "求职培训贷", "risk_level": "低风险", "expected_evidence": ["入职先培训", "包分配承诺"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "推荐而非保证的模糊表述"},
    {"text": "已经签了培训贷合同，但发现培训质量很差，想退出但说要赔违约金", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["培训贷款合同", "培训敷衍"], "risk_stage": "结束", "dataset_label": "edge_case", "notes": "已签约后的困境"},
    {"text": "同学说一起报名前端培训，培训完分配工作月薪过万，让我一起签贷款合同", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["包分配承诺", "培训贷款合同", "高薪诱惑"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "同学拉人头"},
    {"text": "你之前交的培训贷可以退，我是消费者协会的，请提供合同和银行卡号", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "培训贷被骗了？我们律所专门处理这类案件，先交3000元代理费", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "你签的培训贷合同有问题，我们可以帮你解除，但需要先交2000元服务费", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "你的培训贷被标记为不良征信，需要缴纳1500元清除费才能恢复正常", "fraud_type": "求职培训贷", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "冒充官方"], "risk_stage": "二次诈骗", "dataset_label": "edge_case", "notes": "征信恐吓"},
    {"text": "高薪招聘应届生，入职即享受企业内训，但需签订培训服务协议，未满一年离职需赔偿", "fraud_type": "求职培训贷", "risk_level": "中风险", "expected_evidence": ["高薪诱惑", "培训贷款合同"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "服务期协议陷阱"},

    # ==================== 9. 网购退款 (20条) ====================
    {"text": "您好，我是XX商城客服。您的订单快递在运输中丢失了，我们为您提供退款理赔，请配合处理", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["冒充客服", "主动退款理赔"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "退款需要您点击短信中的链接，进入官方理赔页面操作。或者您也可以下载我们的理赔APP", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["非官方链接", "下载指定APP"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "在退款页面，请填写您的银行卡号和密码用于退款验证，然后把手机收到的验证码也填上去", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["套取银行卡密码", "索要验证码"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "您的商品有质量问题需要召回，请扫描二维码填写退款信息", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["非官方链接", "套取银行卡密码"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "快递丢失双倍赔偿，请加理赔专员QQ：123456，提供订单号办理", "fraud_type": "网购退款", "risk_level": "中风险", "expected_evidence": ["冒充客服", "主动退款理赔"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "您的天猫订单因商家违规被冻结，需要您配合操作才能解冻退款，请下载指定视频会议软件", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["冒充客服", "下载指定APP", "要求屏幕共享"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "订单冻结骗局"},
    {"text": "您的退款已受理，但由于您的芝麻信用分不足，需要先提升信用分才能到账，我教您操作", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["冒充客服", "操作网银账户", "验证资金骗局"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "信用分骗局"},
    {"text": "您的退款需要通过银联云闪付APP操作，请打开云闪付扫描这个二维码", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["非官方链接", "操作网银账户"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "利用正规APP"},
    {"text": "退款系统检测到您有多个退款异常记录，需要您转账验证账户安全性才能退款", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["验证资金骗局", "要求转账到安全账户"], "risk_stage": "支付转移", "dataset_label": "challenge"},
    {"text": "您的退货包裹在运输途中损坏，保险公司需要您提供银行卡号进行理赔", "fraud_type": "网购退款", "risk_level": "中风险", "expected_evidence": ["冒充客服", "套取银行卡密码"], "risk_stage": "操作诱导", "dataset_label": "challenge", "notes": "冒充保险理赔"},
    {"text": "淘宝卖家说退款已经打了但没到账，让我加QQ找客服处理，正常吗？", "fraud_type": "网购退款", "risk_level": "中风险", "expected_evidence": ["冒充客服", "主动退款理赔"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "真实退款被利用"},
    {"text": "收到短信说快递丢了要赔我钱，链接看起来是官方的，但域名有点不一样", "fraud_type": "网购退款", "risk_level": "中风险", "expected_evidence": ["非官方链接", "冒充客服"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "高仿域名"},
    {"text": "客服说退款只能通过微信转账，不能退到原支付账户，这合理吗？", "fraud_type": "网购退款", "risk_level": "中风险", "expected_evidence": ["冒充客服", "要求转账到安全账户"], "risk_stage": "操作诱导", "dataset_label": "edge_case"},
    {"text": "确实是买过的东西，商家主动打电话说有问题要退款，但要求开屏幕共享", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["要求屏幕共享", "冒充客服"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "基于真实订单"},
    {"text": "收到包裹丢失赔偿短信，让我填银行卡号密码和验证码，不确定是否安全", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["套取银行卡密码", "索要验证码"], "risk_stage": "支付转移", "dataset_label": "edge_case"},
    {"text": "你之前网购退款被骗了？我是消协工作人员，帮你追回，请提供订单号和银行卡号", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "退款被骗的钱我们保险公司代为赔付，需要先交500元手续费", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "你的退款申请被系统拦截了，需要缴纳保证金才能重新发起，请尽快处理", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "要求缴纳保证金"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "网购退款被骗？点击链接填写维权申请，我们帮你追回：http://refund-claim.xyz/help", "fraud_type": "网购退款", "risk_level": "高风险", "expected_evidence": ["非官方链接", "二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "您的快递已被签收但您未确认收货，系统将自动扣除信用分，点击链接处理", "fraud_type": "网购退款", "risk_level": "中风险", "expected_evidence": ["非官方链接", "冒充客服", "制造紧迫感"], "risk_stage": "诱导阶段", "dataset_label": "baseline", "notes": "信用分恐吓"},

    # ==================== 10. 虚假投资理财 (20条) ====================
    {"text": "朋友推荐你一个投资渠道，内部消息，稳赚不赔！年化收益30%，比银行存款强太多", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["稳赚不赔承诺", "超高收益诱惑"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},
    {"text": "下载这个投资APP吧，群里每天都有导师带单，其他人都晒收益截图了，跟着买就行", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["非正规投资平台", "群内晒收益"], "risk_stage": "信任建立", "dataset_label": "baseline"},
    {"text": "先投1000块试试吧，很快就能看到收益。你看，这不，3天就赚了300块，已经可以提现了", "fraud_type": "虚假投资理财", "risk_level": "中风险", "expected_evidence": ["小额返利建立信任", "试水诱饵"], "risk_stage": "操作诱导", "dataset_label": "baseline"},
    {"text": "现在有个特别好的机会，至少投5万才能跟上！别犹豫了，错过就没了", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["大额投入不让提现", "制造紧迫感"], "risk_stage": "支付转移", "dataset_label": "baseline"},
    {"text": "系统正在升级，暂时无法提现，请耐心等待。预计3-5个工作日恢复", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["大额投入不让提现", "投资平台跑路"], "risk_stage": "结束", "dataset_label": "baseline"},
    {"text": "我是券商内部员工，有独家打新通道，中签率100%，年化收益50%以上", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["稳赚不赔承诺", "超高收益诱惑", "非正规投资平台"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "冒充券商内部人员"},
    {"text": "我们这个是区块链数字货币投资，国家大力支持的新兴产业，现在入场回报率10倍以上", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["稳赚不赔承诺", "超高收益诱惑"], "risk_stage": "诱导阶段", "dataset_label": "challenge", "notes": "蹭区块链热点"},
    {"text": "导师说现在有内部消息，买入这只股票三天必涨20%，名额只剩最后5个", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["稳赚不赔承诺", "制造紧迫感", "群内晒收益"], "risk_stage": "操作诱导", "dataset_label": "challenge"},
    {"text": "投资平台显示你已经赚了5万，但提现需要先缴纳20%的个人所得税才能到账", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["大额投入不让提现", "要求转账到安全账户"], "risk_stage": "支付转移", "dataset_label": "challenge", "notes": "以税费名义截留"},
    {"text": "你之前的投资亏损了？我们高级会员策略帮你回本，升级费8888元，一个月回本", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["稳赚不赔承诺", "持续收费不安排工作"], "risk_stage": "二次诈骗", "dataset_label": "challenge", "notes": "亏损后二次收费"},
    {"text": "朋友说跟着导师炒币赚了很多，让我也下载APP投2万试试，靠谱吗？", "fraud_type": "虚假投资理财", "risk_level": "中风险", "expected_evidence": ["非正规投资平台", "群内晒收益"], "risk_stage": "信任建立", "dataset_label": "edge_case", "notes": "熟人推荐"},
    {"text": "理财群每天都有人晒收益截图，导师推荐的股票都在涨，要不要跟着买？", "fraud_type": "虚假投资理财", "risk_level": "中风险", "expected_evidence": ["群内晒收益", "超高收益诱惑"], "risk_stage": "信任建立", "dataset_label": "edge_case"},
    {"text": "投资APP界面看起来很专业，也有监管信息，但域名不是官方网站", "fraud_type": "虚假投资理财", "risk_level": "中风险", "expected_evidence": ["非正规投资平台"], "risk_stage": "诱导阶段", "dataset_label": "edge_case", "notes": "高仿APP"},
    {"text": "已经在平台赚了2万能提现，但导师说再投5万收益翻倍，要不要继续？", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["小额返利建立信任", "大额投入不让提现"], "risk_stage": "操作诱导", "dataset_label": "edge_case", "notes": "已获小利后的决策"},
    {"text": "平台说提现需要充值VIP才能操作，VIP费用3000元，充了马上能提", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["大额投入不让提现", "持续收费不安排工作"], "risk_stage": "支付转移", "dataset_label": "edge_case"},
    {"text": "你的投资被骗了？我是证监会的，可以帮你追回，请提供交易记录和银行卡号", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["冒充官方", "二次诈骗", "信息收集"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "投资平台跑路了？我们黑客团队可以帮你入侵追回资金，需要先交2000元工具费", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "baseline"},
    {"text": "你被骗的资金我们帮你冻结了，但需要缴纳冻结费才能返还", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "冒充官方", "各种名义要钱"], "risk_stage": "二次诈骗", "dataset_label": "challenge"},
    {"text": "之前投资的平台回来了，说可以退款但需要先缴纳20%手续费", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["二次诈骗", "大额投入不让提现"], "risk_stage": "二次诈骗", "dataset_label": "edge_case"},
    {"text": "加入我们的外汇跟单群，专业操盘手带单，月收益稳定15%以上，零风险", "fraud_type": "虚假投资理财", "risk_level": "高风险", "expected_evidence": ["稳赚不赔承诺", "超高收益诱惑", "群内晒收益"], "risk_stage": "诱导阶段", "dataset_label": "baseline"},

    # ==================== 11. 安全/正常文本 — 负样本 (20条) ====================
    {"text": "学校教务处通知：下学期选课时间为8月25日至9月5日，请同学们在教务系统中完成选课", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规学校通知"},
    {"text": "您的快递已签收，签收人：本人。如有疑问请联系快递员：张师傅 13800138000", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规快递通知"},
    {"text": "提醒：全国反诈热线96110，如遇到可疑电话或信息请及时拨打确认", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "反诈宣传"},
    {"text": "银行短信：您尾号1234的卡于今日10:30消费100.00元，余额5000.00元", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规银行消费提醒"},
    {"text": "请同学们通过学校官方缴费平台缴纳学费，不要向任何个人账户转账", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规缴费提醒"},
    {"text": "公安提示：凡是要求转账到安全账户的都是诈骗，请勿相信", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "公安反诈提示"},
    {"text": "淘宝官方退款流程：在订单页面申请退款，等待卖家确认，退款原路返回支付账户", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规退款流程说明"},
    {"text": "国家助学贷款申请请前往当地教育局学生资助管理中心办理，不收取任何费用", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规助学贷款说明"},
    {"text": "招聘会将于本周六在学校体育馆举行，请携带简历前往，无需缴纳任何费用", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规招聘会通知"},
    {"text": "支付宝官方提醒：不会以任何理由要求您提供验证码或开启屏幕共享", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "支付宝安全提示"},
    {"text": "游戏交易平台提醒：请通过官方平台完成交易，不要私下转账", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "平台安全提醒"},
    {"text": "如果您接到自称客服的电话，请挂断后通过官方APP或网站联系客服核实", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "客服核实提醒"},
    {"text": "学校财务处通知：学费缴纳请登录校园一卡通系统或财务处官网，不接受微信转账", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规财务通知"},
    {"text": "如遇可疑信息，请拨打110或96110报警，或前往就近派出所咨询", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "报警求助指引"},
    {"text": "银行卡密码请妥善保管，银行工作人员不会以任何理由询问您的密码", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "银行安全提示"},
    {"text": "正规投资理财请通过银行或持牌证券公司办理，不要轻信高收益承诺", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规投资提醒"},
    {"text": "老师不会在非工作时间通过私人微信收取任何费用，请通过学校官方渠道缴费", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "正规缴费提醒"},
    {"text": "验证码是资金安全的最后一道防线，任何索要验证码的行为都可能是诈骗", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "验证码安全提示"},
    {"text": "下载APP请通过官方应用商店，不要扫描不明二维码或点击链接下载", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "APP下载安全提示"},
    {"text": "如有人通过视频通话借钱，请务必回拨电话或当面核实身份后再决定", "fraud_type": "安全", "risk_level": "安全", "expected_evidence": [], "risk_stage": None, "dataset_label": "baseline", "notes": "AI换脸防范提示"},
]


# ==================== 种子填充函数 ====================

def seed_risk_test_samples(session: Session) -> int:
    """将风险测试样本填充到 risk_test_samples 表（幂等操作）。

    如果表中已有数据则跳过，仅在空表时插入。
    如需强制刷新，请先清空 risk_test_samples 表。

    Returns:
        新插入的样本数量
    """
    existing_count = session.scalar(select(RiskTestSample).limit(1))
    if existing_count is not None:
        return 0

    new_count = 0
    for sample in RISK_TEST_SAMPLES:
        record = RiskTestSample(
            text=sample["text"],
            fraud_type=sample["fraud_type"],
            risk_level=sample["risk_level"],
            expected_evidence_json=json.dumps(
                sample.get("expected_evidence", []), ensure_ascii=False
            ),
            risk_stage=sample.get("risk_stage"),
            source="人工标注",
            dataset_label=sample.get("dataset_label", "baseline"),
            notes=sample.get("notes"),
            enabled=True,
            created_at=datetime.utcnow(),
        )
        session.add(record)
        new_count += 1

    if new_count:
        session.commit()
    return new_count
