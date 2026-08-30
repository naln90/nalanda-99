from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import FraudCase, GrowthRule, KnowledgeItem, Pet, PetPool, TrainingQuestion, TrainingTask, User
from .rules import level_bounds, pet_level, pet_stage


PET_POOL = [
    ("校园猫", "动物类", "机敏观察，擅长发现异常话术"),
    ("守护犬", "动物类", "可靠坚定，提醒你核验身份"),
    ("灵巧兔", "动物类", "反应迅速，识别限时诱导"),
    ("巡逻机器人", "机器人类", "扫描风险信号，守护账户安全"),
    ("反诈小卫士", "机器人类", "佩戴盾牌徽章，陪伴完成训练"),
    ("数据探测员", "机器人类", "用数据雷达发现高危话术"),
    ("麒麟", "守护兽类", "东方守护兽，象征安全与判断力"),
    ("醒狮", "守护兽类", "醒目警示，提醒识别骗局"),
    ("玄鸟", "守护兽类", "数据光翼，快速识别异常"),
]

TRAINING_TASKS = [
    ("ai-face", "AI 换脸借钱识别", "AI 换脸", "高风险", "中等", 6, 50, 80),
    ("brushing", "兼职刷单返利骗局", "刷单返利", "高风险", "中等", 5, 45, 70),
    ("refund", "网购退款屏幕共享", "冒充客服", "高风险", "中等", 5, 40, 60),
    ("game", "游戏账号交易保证金", "游戏交易", "中风险", "低", 4, 30, 40),
    ("investment", "虚假投资理财平台", "虚假投资", "高风险", "高", 8, 55, 90),
    ("teacher-fee", "冒充老师收费二维码", "冒充老师", "高风险", "低", 4, 35, 50),
    # —— 以下为知识库全覆盖新增训练任务 ——
    ("campus-loan", "校园贷款综合骗局识别", "校园贷", "高风险", "中等", 5, 45, 70),
    ("pubsecurity", "冒充公检法诈骗识别", "冒充公检法", "高风险", "中等", 5, 45, 70),
    ("impersonate-friend", "冒充熟人借钱识别", "冒充熟人", "高风险", "低", 4, 35, 50),
    ("concert-ticket", "演唱会门票诈骗识别", "演唱会门票", "中风险", "低", 4, 30, 40),
    ("flight-refund", "航班退改签诈骗识别", "航班退改签", "高风险", "低", 4, 35, 50),
    ("job-academic", "求职与学术诈骗识别", "求职交费", "中风险", "低", 4, 30, 40),
    ("secondhand", "二手交易诈骗识别", "二手交易", "中风险", "低", 4, 30, 40),
    ("free-gift", "免费领取诈骗识别", "免费领取", "高风险", "低", 4, 35, 50),
    ("financial-scam", "金融类诈骗综合识别", "贷款征信诈骗", "高风险", "高", 7, 55, 90),
    ("screen-nfc", "屏幕共享与NFC盗刷识别", "屏幕共享诈骗", "高风险", "中等", 5, 45, 70),
    ("delivery-lead", "快递引流诈骗识别", "快递引流诈骗", "中风险", "低", 3, 25, 35),
    ("bangxin", "帮信与两卡法律风险", "帮信与两卡", "高风险", "中等", 5, 40, 60),
    ("points-clear", "积分清零与虚假中奖", "积分清零诈骗", "中风险", "低", 3, 25, 35),
    ("anti-fraud-basics", "反诈基础知识综合测验", "反诈总则", "低风险", "低", 3, 25, 35),
]

# 每个训练任务配套 3-4 道题，覆盖风险识别、应对方式、情景判断、误区识别
TRAINING_QUESTIONS = {
    "ai-face": [
        {
            "id": "ai-face-q1",
            "question_type": "multiple",
            "stem": "本案例最关键的风险信号是什么？",
            "options": ["A. 对方只进行短暂视频确认", "B. 要求立即转账", "C. 拒绝电话二次核验", "D. 以上都是"],
            "correct_answer": ["A", "B", "C", "D"],
            "explanation": "熟人借钱、转账要求和拒绝电话二次核验叠加出现时，应立即暂停并通过独立渠道核验。三者同时出现是 AI 换脸借钱诈骗的典型组合信号。",
        },
        {
            "id": "ai-face-q2",
            "question_type": "single",
            "stem": "收到熟人通过短视频借钱，最稳妥的做法是？",
            "options": ["A. 视频看起来是本人就直接转账", "B. 通过原有电话号码拨打核实", "C. 在聊天里再追问一句确认", "D. 先转一部分试探对方"],
            "correct_answer": "B",
            "explanation": "AI 换脸可以伪造视频，但无法接听原号码的来电。通过独立渠道（原电话号码）核实是最可靠的方式。聊天里追问仍可能被对方用话术绕过。",
        },
        {
            "id": "ai-face-q3",
            "question_type": "single",
            "stem": "AI 换脸诈骗最常利用的心理弱点是？",
            "options": ["A. 贪图便宜", "B. 紧急感和对熟人的信任", "C. 好奇心驱使", "D. 对权威的服从"],
            "correct_answer": "B",
            "explanation": "AI 换脸借钱诈骗的核心是利用你对熟人的信任，再叠加「手机没电」「不方便接电话」等制造紧急感，让你来不及核验就转账。",
        },
        {
            "id": "ai-face-q4",
            "question_type": "multiple",
            "stem": "以下哪些情况应高度警惕 AI 换脸诈骗？",
            "options": ["A. 短暂视频后立即要求转账", "B. 拒绝电话或语音通话", "C. 制造紧急事由催促转账", "D. 通过常用社交账号正常聊天"],
            "correct_answer": ["A", "B", "C"],
            "explanation": "短暂视频+立即要求转账+拒绝电话+制造紧急事由，是 AI 换脸诈骗的典型组合。正常聊天不会触发这些信号。只要同时出现 ABC 三个信号，就应立即停止操作。",
        },
    ],
    "brushing": [
        {
            "id": "brushing-q1",
            "question_type": "multiple",
            "stem": "遇到「兼职日结、先垫付、做满三单才能提现」的信息，风险点是什么？",
            "options": ["A. 先垫付资金", "B. 承诺高额返利", "C. 做满任务才能提现", "D. 以上全是风险点"],
            "correct_answer": ["A", "B", "C", "D"],
            "explanation": "先垫付（资金风险）、高返利（诱导）、做满任务才能提现（锁定资金）是刷单诈骗的三大典型特征，同时出现时风险极高。任何要求先垫付资金的兼职都涉嫌诈骗。",
        },
        {
            "id": "brushing-q2",
            "question_type": "single",
            "stem": "遇到「先垫付后返利」的兼职应如何处理？",
            "options": ["A. 先小额试一次看看真假", "B. 立即停止，不垫付任何资金", "C. 跟对方讨价还价降低垫付金额", "D. 叫上朋友一起做分摊风险"],
            "correct_answer": "B",
            "explanation": "刷单诈骗的典型套路是第一单小额返利获取信任，后续加大金额后失联。任何「先垫付」都不应尝试，无论金额大小。小额试水正是骗子设下的第一步陷阱。",
        },
        {
            "id": "brushing-q3",
            "question_type": "single",
            "stem": "刷单骗局最典型的套路是？",
            "options": ["A. 第一单正常返利，后续加大金额后失联", "B. 从第一单就直接骗钱不返", "C. 只收取会员费不做任务", "D. 卖虚假的兼职课程"],
            "correct_answer": "A",
            "explanation": "刷单诈骗的核心是「放长线钓大鱼」：第一单甚至前几单都正常返利，让你放下戒备，之后以「任务未完成」「系统故障」等理由要求继续加大垫付金额，最终失联。这是最危险也是最常见的套路。",
        },
        {
            "id": "brushing-q4",
            "question_type": "multiple",
            "stem": "以下哪些是刷单诈骗的典型特征？",
            "options": ["A. 日结高薪、操作简单", "B. 无需经验、时间自由", "C. 需要先垫付资金", "D. 签订正式劳动合同并有社保"],
            "correct_answer": ["A", "B", "C"],
            "explanation": "高薪、简单、自由是诱饵，垫付资金是核心陷阱。正规兼职会签订劳动合同并缴纳社保，绝不会要求员工先垫付资金。ABC 同时出现即可判定为刷单诈骗。",
        },
    ],
    "refund": [
        {
            "id": "refund-q1",
            "question_type": "multiple",
            "stem": "网购退款诈骗的风险信号有哪些？",
            "options": ["A. 自称客服主动联系", "B. 要求开启屏幕共享", "C. 索要验证码或密码", "D. 以上全是"],
            "correct_answer": ["A", "B", "C", "D"],
            "explanation": "主动联系+屏幕共享+索要验证码是退款诈骗的标准三件套。正规平台客服不会要求屏幕共享，更不会索要验证码。遇到任何一个都应立即警惕。",
        },
        {
            "id": "refund-q2",
            "question_type": "single",
            "stem": "客服要求开启屏幕共享时应？",
            "options": ["A. 配合操作以免影响退款进度", "B. 立即拒绝，通过官方 App 自行核实", "C. 只共享部分屏幕配合操作", "D. 录屏后再配合操作"],
            "correct_answer": "B",
            "explanation": "屏幕共享会让对方看到你的验证码、密码、银行卡号等全部信息，相当于把账户控制权交出。正规退款不需要屏幕共享。正确做法是挂断后打开官方 App 自行查看订单和退款状态。",
        },
        {
            "id": "refund-q3",
            "question_type": "single",
            "stem": "正规的网购退款流程是？",
            "options": ["A. 客服远程操作你的手机完成退款", "B. 在原购买平台 App 内发起申请并等待审核", "C. 提供银行卡信息由客服代为退款", "D. 扫描对方发来的退款二维码"],
            "correct_answer": "B",
            "explanation": "正规退款全程在平台 App 内完成：发起申请→商家审核→原路退回支付账户。不需要客服远程操作、不扫二维码、不提供银行卡。任何脱离平台的退款流程都是诈骗。",
        },
        {
            "id": "refund-q4",
            "question_type": "multiple",
            "stem": "以下哪些是退款诈骗的典型特征？",
            "options": ["A. 称商品有质量问题主动联系退款", "B. 要求下载指定会议软件屏幕共享", "C. 索要验证码或支付密码", "D. 在平台 App 内发起退款申请"],
            "correct_answer": ["A", "B", "C"],
            "explanation": "主动联系+下载软件+索要验证码是诈骗组合。正规退款在平台 App 内操作（D 是正规流程），不需要额外下载软件，更不会索要验证码。",
        },
    ],
    "game": [
        {
            "id": "game-q1",
            "question_type": "multiple",
            "stem": "游戏账号交易的风险信号有哪些？",
            "options": ["A. 要求线下交易或私下转账", "B. 要求交纳保证金或解冻费", "C. 价格明显低于市场价", "D. 以上全是"],
            "correct_answer": ["A", "B", "C", "D"],
            "explanation": "线下交易无保障、保证金是陷阱、低价是诱饵，三者任一出现都应高度警惕。正规游戏交易平台有担保机制，不会要求私下转账或交保证金。",
        },
        {
            "id": "game-q2",
            "question_type": "single",
            "stem": "对方要求交纳保证金时应？",
            "options": ["A. 先交一部分看看对方是否守信", "B. 立即停止，通过官方平台交易", "C. 让对方先发货再交保证金", "D. 找朋友代交分摊风险"],
            "correct_answer": "B",
            "explanation": "保证金是游戏交易诈骗最常见的手段：交了第一笔还会有「解冻费」「验证费」等名目继续要钱。正确做法是立即停止，只在游戏官方交易平台进行交易。",
        },
        {
            "id": "game-q3",
            "question_type": "single",
            "stem": "安全的游戏账号交易方式是？",
            "options": ["A. 微信转账直接和卖家交易", "B. 通过游戏官方或正规第三方交易平台", "C. 扫描对方发来的二维码付款", "D. 提供账号密码让对方代操作"],
            "correct_answer": "B",
            "explanation": "官方平台有交易担保和客服介入机制，资金和账号安全有保障。私下转账、扫二维码、提供账号密码都存在极大风险，一旦被骗很难追回。",
        },
    ],
    "investment": [
        {
            "id": "investment-q1",
            "question_type": "multiple",
            "stem": "虚假投资平台的风险信号有哪些？",
            "options": ["A. 承诺稳赚不赔、高额回报", "B. 需要私下转账入金", "C. 群里有「老师」带单指导", "D. 以上全是"],
            "correct_answer": ["A", "B", "C", "D"],
            "explanation": "稳赚不赔是最大的谎言，私下转账意味着资金脱离监管，「老师带单」是群托配合的骗局。四者同时出现可百分百判定为虚假投资诈骗。",
        },
        {
            "id": "investment-q2",
            "question_type": "single",
            "stem": "遇到「稳赚不赔、年化收益 30%」的投资应该？",
            "options": ["A. 先小额试水看看收益是否到账", "B. 立即警惕，不存在稳赚不赔的投资", "C. 跟着群里其他「投资者」一起投", "D. 问客服要一份收益保障协议"],
            "correct_answer": "B",
            "explanation": "任何承诺「稳赚不赔」或远超市场平均收益的投资都是诈骗。正规投资有风险提示，收益与风险成正比。小额试水正是骗局的第一步——前期收益能提现，加大金额后平台就会以各种理由限制提现。",
        },
        {
            "id": "investment-q3",
            "question_type": "single",
            "stem": "正规的投资理财应通过？",
            "options": ["A. 对方推荐的投资 APP", "B. 银行或持牌金融机构官方渠道", "C. 微信群里的投资链接", "D. 朋友发的投资二维码"],
            "correct_answer": "B",
            "explanation": "正规理财通过银行、券商、基金公司等持牌机构的官方渠道进行，资金受银保监会监管。对方推荐的 APP、群链接、二维码都可能指向虚假平台，资金一旦转入个人账户即被骗。",
        },
        {
            "id": "investment-q4",
            "question_type": "multiple",
            "stem": "以下哪些是虚假投资平台的典型特征？",
            "options": ["A. 群里有「老师」带单、晒收益截图", "B. 收益远超银行理财和基金", "C. 要求转入个人账户或非监管渠道", "D. 在证监会备案并可公开查询"],
            "correct_answer": ["A", "B", "C"],
            "explanation": "带单老师+超高收益+转入个人账户是虚假投资的铁三角。正规持牌机构在证监会备案可查（D 是正规特征），绝不会要求转入个人账户，也不会承诺固定高收益。",
        },
    ],
    "teacher-fee": [
        {
            "id": "teacher-fee-q1",
            "question_type": "multiple",
            "stem": "冒充老师收费的风险信号有哪些？",
            "options": ["A. 班级群里突然发收款码", "B. 要求紧急交费、限时优惠", "C. 收款账户是个人账户", "D. 以上全是"],
            "correct_answer": ["A", "B", "C", "D"],
            "explanation": "群里发码+紧急催费+个人账户是冒充老师诈骗的典型组合。正规学校收费走财务系统，不会在群里发个人收款码，更不会催促「限时」。",
        },
        {
            "id": "teacher-fee-q2",
            "question_type": "single",
            "stem": "班级群里「老师」发了收款码要求交资料费，应该？",
            "options": ["A. 立即扫码交费以免耽误", "B. 通过电话或线下向老师本人核实", "C. 看其他同学交了再跟着交", "D. 先交一半剩下的之后再说"],
            "correct_answer": "B",
            "explanation": "骗子常混入班级群冒充老师。看到收款码第一反应应是核实，而不是付款。其他同学可能是群托或同样被骗。通过学校已知联系方式直接联系老师本人是最可靠的核实方式。",
        },
        {
            "id": "teacher-fee-q3",
            "question_type": "single",
            "stem": "如何有效核实群里「老师」的真实身份？",
            "options": ["A. 在群里@老师追问确认", "B. 通过学校已知联系方式直接联系老师本人", "C. 让其他同学帮忙问", "D. 看头像和昵称是否和老师一致"],
            "correct_answer": "B",
            "explanation": "群里追问可能被冒充者回复，看头像和昵称可以被仿冒，其他同学也可能被蒙蔽。只有通过学校已知的、独立的联系方式（如老师原有的手机号、办公室电话）直接联系老师本人，才能确认身份。",
        },
    ],
    # —— 以下为知识库全覆盖新增训练题（14 个训练任务，各 2-3 题） ——
    "campus-loan": [
        {
            "id": "campus-loan-q1",
            "question_type": "single",
            "stem": "校园贷最典型的诈骗手法是什么？",
            "options": ["A. 高额利息正常分期还款", "B. 无抵押低息宣传+砍头息+暴力催收", "C. 通过银行正规渠道放贷", "D. 只面向教职工发放"],
            "correct_answer": "B",
            "explanation": "校园贷的典型手法：以无抵押低息为诱饵，实际到手金额少于借款（砍头息），逾期后高额罚息并伴以暴力催收或诱导以贷养贷。国家已明令禁止向大学生发放校园贷。",
        },
        {
            "id": "campus-loan-q2",
            "question_type": "single",
            "stem": "接到自称注销校园贷的客服电话，要求下载APP验证还款能力，你应该？",
            "options": ["A. 配合操作以免影响征信", "B. 立即挂断，通过官方渠道核实", "C. 只下载APP不转账", "D. 先查一下对方工号再操作"],
            "correct_answer": "B",
            "explanation": "注销校园贷是典型的诈骗话术，个人征信由央行统一管理，不存在「注销洗白」。任何要求下载APP、屏幕共享、转账验证的都是诈骗。",
        },
    ],
    "pubsecurity": [
        {
            "id": "pubsecurity-q1",
            "question_type": "single",
            "stem": "接到自称公安局的电话，说你涉嫌洗钱需要将资金转入安全账户，你应该？",
            "options": ["A. 立即转账配合调查", "B. 挂断电话拨打110或96110核实", "C. 先询问具体案情", "D. 按照对方指引下载APP操作"],
            "correct_answer": "B",
            "explanation": "公检法机关不会通过电话办案，不存在所谓「安全账户」。任何要求转账自证清白或要求保密的都是诈骗。正确做法是立即挂断并拨打110或96110核实。",
        },
        {
            "id": "pubsecurity-q2",
            "question_type": "single",
            "stem": "以下哪项是冒充公检法诈骗的典型特征？",
            "options": ["A. 警方上门出示证件当面沟通", "B. 电话办案+安全账户+保密要求", "C. 在派出所接待大厅做笔录", "D. 110主动来电提示防骗"],
            "correct_answer": "B",
            "explanation": "电话办案、要求转账到安全账户、要求保密（不让告诉家人）是冒充公检法诈骗的三要素。真正的公检法不会通过电话办案，110是接警号码不会主动来电索要验证码。",
        },
    ],
    "impersonate-friend": [
        {
            "id": "impersonate-friend-q1",
            "question_type": "single",
            "stem": "同学的QQ号发消息说家属生病急用钱，让你帮忙转账，你应该？",
            "options": ["A. 看是同学的号就直接转", "B. 通过原有电话或当面核实后再决定", "C. 在QQ里再确认一下是不是本人", "D. 既然是急用先转一部分"],
            "correct_answer": "B",
            "explanation": "冒充熟人借钱是高频诈骗手段。在聊天软件里追问仍可能是骗子在回复，最稳妥的方式是通过原有电话或当面核实。",
        },
        {
            "id": "impersonate-friend-q2",
            "question_type": "single",
            "stem": "熟人通过短视频借钱，画面和声音都像本人，转账前最该做什么？",
            "options": ["A. 视频都看到了直接转", "B. 挂断后用原有号码回拨核实", "C. 发个消息再确认一下", "D. 在群里问问其他人"],
            "correct_answer": "B",
            "explanation": "AI换脸技术可伪造视频和声音，但无法接听回拨电话。最稳妥的方式是用该熟人原有的电话号码回拨核实，这是独立的验证渠道。",
        },
    ],
    "concert-ticket": [
        {
            "id": "concert-ticket-q1",
            "question_type": "single",
            "stem": "有人在社交平台称有演唱会内部票原价转让，要求微信转账，你应该？",
            "options": ["A. 先付定金锁票", "B. 只在官方票务平台购买", "C. 让对方发身份证照片再信任", "D. 先加微信聊聊看"],
            "correct_answer": "B",
            "explanation": "演唱会门票诈骗典型手法：声称有内部票/代理价、要求脱离官方平台私下转账。演唱会已实名制，唯一安全的方式是通过官方票务平台购买。",
        },
        {
            "id": "concert-ticket-q2",
            "question_type": "single",
            "stem": "买了演唱会票对方说没备注需重新转账，之前款项会退回，这是？",
            "options": ["A. 系统问题正常操作", "B. 典型的连环诈骗手法", "C. 先联系平台客服确认", "D. 换个人操作就行"],
            "correct_answer": "B",
            "explanation": "以「没备注」「账号异常」为由要求反复转账，是经典的连环诈骗。之前的钱不会退回，每一次转账都落入骗子口袋。一旦被要求重复转账，立即停止并报警。",
        },
    ],
    "flight-refund": [
        {
            "id": "flight-refund-q1",
            "question_type": "single",
            "stem": "收到航班取消短信，要求下载APP开启屏幕共享办退改签，你应该？",
            "options": ["A. 下载APP配合操作", "B. 通过航空公司官方APP核实航班状态", "C. 先共享屏幕看看是不是真的", "D. 回拨短信中的客服电话确认"],
            "correct_answer": "B",
            "explanation": "航班退改签诈骗特征：境外来电或短信、要求下载会议APP、开启屏幕共享。正确做法是通过航空公司官方APP或官网核实，正规退改签不要求屏幕共享和转账。",
        },
        {
            "id": "flight-refund-q2",
            "question_type": "single",
            "stem": "正规航空公司的退改签流程不包括以下哪项？",
            "options": ["A. 在官方APP内操作退改", "B. 要求开启屏幕共享指导操作", "C. 退款原路返回支付账户", "D. 提供官方客服电话供咨询"],
            "correct_answer": "B",
            "explanation": "正规退改签退款是原路返回的，绝不会要求开启屏幕共享、下载陌生APP或转账验证。任何要求屏幕共享的操作都是诈骗信号。",
        },
    ],
    "job-academic": [
        {
            "id": "job-academic-q1",
            "question_type": "single",
            "stem": "招聘广告称月薪8000无学历要求，但需先交培训押金入职后退还，这是？",
            "options": ["A. 正常公司流程", "B. 典型的求职诈骗", "C. 先交一半试试", "D. 正规公司都有押金"],
            "correct_answer": "B",
            "explanation": "《劳动合同法》明确规定用人单位不得向劳动者收取财物。任何以体检费、服装费、培训押金等名义在入职前收费的都是诈骗。",
        },
        {
            "id": "job-academic-q2",
            "question_type": "single",
            "stem": "有人联系你称交30万可保送名校/论文代发包录用，你应该？",
            "options": ["A. 先问问细节再考虑", "B. 走正规渠道申请，不轻信捷径", "C. 找老师确认是不是内部渠道", "D. 交一部分定金试试"],
            "correct_answer": "B",
            "explanation": "保研、论文发表、竞赛获奖都没有「钞能力」捷径。代写论文属于学术不端。遇到此类骗局应立即向学校和警方举报。",
        },
    ],
    "secondhand": [
        {
            "id": "secondhand-q1",
            "question_type": "single",
            "stem": "在闲鱼看中一台低价相机，卖家说走微信转账更便宜，你应该？",
            "options": ["A. 微信转账便宜当然选这个", "B. 坚持走闲鱼官方平台担保交易", "C. 先付定金看看", "D. 加了微信再谈"],
            "correct_answer": "B",
            "explanation": "二手交易诈骗核心套路：在正规平台发布信息后诱导到微信私下转账，收款后拉黑或发空包。必须坚持走官方平台的担保交易流程。",
        },
        {
            "id": "secondhand-q2",
            "question_type": "single",
            "stem": "二手交易中以下哪种行为最危险？",
            "options": ["A. 在平台内查看卖家信用和评价", "B. 脱离平台使用个人微信/支付宝直接转账", "C. 通过平台聊天功能沟通交易细节", "D. 选择见面交易并当场验货"],
            "correct_answer": "B",
            "explanation": "脱离平台的个人转账没有任何担保和售后保障，一旦转账资金无法追回。平台担保交易是保护买卖双方的基本防线。",
        },
    ],
    "free-gift": [
        {
            "id": "free-gift-q1",
            "question_type": "single",
            "stem": "社交媒体上看到免费领取品牌围巾/行李箱，只需加QQ按指引操作，这是？",
            "options": ["A. 品牌促销推广活动", "B. 典型的免费领取诈骗套路", "C. 先加QQ看看真假", "D. 可能是真的先试试"],
            "correct_answer": "B",
            "explanation": "免费领取诈骗套路：用免费礼品为诱饵→添加QQ/微信→引导开启屏幕共享→诱导充话费或开通借贷产品。天上不会掉馅饼。",
        },
        {
            "id": "free-gift-q2",
            "question_type": "single",
            "stem": "领取免费礼品时对方要求开启屏幕共享或语音指导操作，你应？",
            "options": ["A. 配合操作尽快领取", "B. 立即终止联系并举报", "C. 开着共享但不操作敏感信息", "D. 问清楚再决定"],
            "correct_answer": "B",
            "explanation": "免费领取+屏幕共享=诈骗公式。一旦开启屏幕共享，银行卡号、密码、验证码都会暴露。任何领礼品需下载APP或屏幕共享的都是诈骗。",
        },
    ],
    "financial-scam": [
        {
            "id": "financial-scam-q1",
            "question_type": "single",
            "stem": "接到电话称微信百万保障到期将扣费，要求下载会议APP关闭，你应？",
            "options": ["A. 按指引关闭以免扣费", "B. 立即挂断，百万保障是免费服务不会到期", "C. 先查一下微信设置", "D. 让对方指导操作"],
            "correct_answer": "B",
            "explanation": "微信/支付宝的百万保障是平台免费赠送的安全服务，永远不会到期、不会扣费、不影响征信。任何以百万保障到期为由要求操作的都是诈骗。",
        },
        {
            "id": "financial-scam-q2",
            "question_type": "single",
            "stem": "有人声称能帮你修复征信消除不良记录，收取2000元服务费，这是？",
            "options": ["A. 正规的信用修复服务", "B. 征信修复诈骗，征信只有央行能管理", "C. 先交一半试试效果", "D. 熟人介绍的可以信"],
            "correct_answer": "B",
            "explanation": "个人征信由中国人民银行统一管理，没有任何机构或个人能「修复」或「洗白」征信。声称可以修复征信的都是诈骗，切勿转账。",
        },
        {
            "id": "financial-scam-q3",
            "question_type": "single",
            "stem": "投资平台客服说系统升级无法线上转账，要求购买购物卡发卡密充值，这是？",
            "options": ["A. 临时的技术调整", "B. 典型的洗钱诈骗手法", "C. 正规平台的特殊充值方式", "D. 先买一张小的试试"],
            "correct_answer": "B",
            "explanation": "正规投资平台绝不会要求购买购物卡充值。要求大量购买购物卡并提供卡密=洗钱诈骗。一旦提供卡密资金无法追回。超市员工遇顾客大量购买购物卡应进行反诈提醒。",
        },
    ],
    "screen-nfc": [
        {
            "id": "screen-nfc-q1",
            "question_type": "single",
            "stem": "客服说退款需要下载会议APP并开启屏幕共享，你应该？",
            "options": ["A. 配合操作加快退款", "B. 立即拒绝，屏幕共享等于暴露所有信息", "C. 只共享部分屏幕", "D. 让朋友看着一起操作"],
            "correct_answer": "B",
            "explanation": "屏幕共享会让骗子实时看到银行卡号、密码、验证码等所有敏感信息，相当于把保险柜钥匙交给陌生人。任何客服要求屏幕共享的都是诈骗。",
        },
        {
            "id": "screen-nfc-q2",
            "question_type": "single",
            "stem": "有人电话指导你将银行卡贴在手机背面NFC区域进行验证，这是？",
            "options": ["A. 新出的安全验证方式", "B. NFC盗刷诈骗，用来读取卡片信息", "C. 银行新推出的功能", "D. 可能是同事在做测试"],
            "correct_answer": "B",
            "explanation": "NFC盗刷是新型诈骗手法：骗子诱导你将银行卡贴近手机NFC区域，配合恶意APP读取卡内信息并转移资金。正规银行和支付平台绝不会通过电话引导NFC验证。",
        },
    ],
    "delivery-lead": [
        {
            "id": "delivery-lead-q1",
            "question_type": "single",
            "stem": "收到没有购买过的快递，里面有扫码领奖的小卡片，你应该？",
            "options": ["A. 扫码试试万一真的呢", "B. 不扫码，这是快递引流诈骗", "C. 问快递员怎么回事", "D. 让室友帮忙扫码"],
            "correct_answer": "B",
            "explanation": "快递引流诈骗：向不特定人群寄送含中奖/领礼品卡片的陌生快递，扫描后会被引入刷单或投资诈骗群。未网购却收到包裹尤其需警惕。",
        },
        {
            "id": "delivery-lead-q2",
            "question_type": "single",
            "stem": "扫码领了红包后被拉入群，群里不断发布刷单返利任务，你应该？",
            "options": ["A. 先小额试试看", "B. 立即退群并删除，刷单就是诈骗", "C. 看别人都在赚就跟做", "D. 只做任务不投钱"],
            "correct_answer": "B",
            "explanation": "扫码领奖→加微信→拉群→刷单任务，是完整的诈骗引流链条。群里晒单的「托」都是骗子同伙。任何刷单做任务都是诈骗，立即退群删除。",
        },
    ],
    "bangxin": [
        {
            "id": "bangxin-q1",
            "question_type": "single",
            "stem": "有人出500元借你的银行卡转个账，说是正规用途，你应该？",
            "options": ["A. 500元不少借给他", "B. 坚决拒绝，这可能构成帮信罪", "C. 先问问转账用途", "D. 只借银行卡不告诉密码"],
            "correct_answer": "B",
            "explanation": "出租出借银行卡、电话卡给他人用于转账，如果被用于诈骗洗钱等犯罪活动，根据《刑法》第287条之二，可能构成帮助信息网络犯罪活动罪（帮信罪），最高可判三年有期徒刑。",
        },
        {
            "id": "bangxin-q2",
            "question_type": "single",
            "stem": "以下哪种行为可能让你成为「电诈工具人」？",
            "options": ["A. 用自己的卡帮不认识的人转账收取报酬", "B. 用自己的银行卡在正规商店刷卡消费", "C. 用支付宝给同学转AA制餐费", "D. 绑定自己的银行卡到微信支付"],
            "correct_answer": "A",
            "explanation": "「电诈工具人」指在不知情或明知的情况下为诈骗分子提供银行卡、电话卡、支付账户等帮助的人。用自己的卡帮陌生人转账并收取报酬是最典型的帮信行为。",
        },
    ],
    "points-clear": [
        {
            "id": "points-clear-q1",
            "question_type": "single",
            "stem": "收到短信称银行积分即将清零，点击链接可兑换现金，你应该？",
            "options": ["A. 点击链接抓紧兑换", "B. 删除短信，通过银行官方APP查看积分", "C. 先看看链接是不是银行的", "D. 回复短信问清楚"],
            "correct_answer": "B",
            "explanation": "积分清零诈骗：仿冒银行/运营商发送含钓鱼链接的短信，点击后会被窃取银行卡号、密码和验证码。正确的积分兑换方式是通过官方APP或官方网站。",
        },
        {
            "id": "points-clear-q2",
            "question_type": "single",
            "stem": "积分兑换页面要求输入银行卡密码和短信验证码才能领取，这是？",
            "options": ["A. 正常的身份验证", "B. 钓鱼页面，盗取支付信息", "C. 银行的安全措施", "D. 先看清楚再输入"],
            "correct_answer": "B",
            "explanation": "正规的积分兑换不需要银行卡密码和短信验证码。任何要求输入这些信息的积分兑换页面都是钓鱼页面，目的是盗取支付信息后盗刷。",
        },
    ],
    "anti-fraud-basics": [
        {
            "id": "anti-fraud-basics-q1",
            "question_type": "single",
            "stem": "反诈公式：「做任务+小额返利+大额投入」等于什么？",
            "options": ["A. 正常的兼职工作", "B. 刷单诈骗", "C. 平台推广活动", "D. 朋友推荐的生意"],
            "correct_answer": "B",
            "explanation": "「做任务+小额返利+大额投入=刷单诈骗」是最经典的反诈公式之一。骗子先用小额返利获取信任，诱导你投入大额资金后以各种理由拒绝返款。",
        },
        {
            "id": "anti-fraud-basics-q2",
            "question_type": "single",
            "stem": "以下哪项不属于正确的反诈做法？",
            "options": ["A. 下载国家反诈中心APP并开启来电预警", "B. 把验证码发给自称银行客服的人核验身份", "C. 接到96110来电认真接听", "D. 陌生链接不点击不扫描"],
            "correct_answer": "B",
            "explanation": "验证码是账户安全的最后一道防线，任何客服、银行、公安都不会索要。国家反诈中心APP来电预警可识别诈骗电话，96110是反诈预警劝阻专线。",
        },
        {
            "id": "anti-fraud-basics-q3",
            "question_type": "single",
            "stem": "反诈「六不」原则不包括以下哪项？",
            "options": ["A. 不点陌生链接", "B. 不透露身份和验证码", "C. 不信陌生人的高回报承诺", "D. 不接听所有陌生来电"],
            "correct_answer": "D",
            "explanation": "「六不」原则：不点陌生链接、不透露身份验证码、不信高回报、不向陌生账户转账、不办非正规校园贷、不提供敏感区域照片。不包括「不接听所有陌生来电」——96110等重要来电也需要接听。",
        },
    ],
}

RANKING_PETS = [
    ("PET-1001", "U-2301**", "麒麟", "守护兽类", 3560, datetime.utcnow() - timedelta(minutes=8)),
    ("PET-1048", "U-2402**", "守护犬", "动物类", 3420, datetime.utcnow() - timedelta(minutes=18)),
    ("PET-2207", "U-2315**", "数据探测员", "机器人类", 3150, datetime.utcnow() - timedelta(minutes=29)),
    ("PET-4432", "U-1765**", "反诈小卫士", "机器人类", 2800, datetime.utcnow() - timedelta(minutes=40)),
]


def seed_database(session: Session) -> None:
    if not session.scalar(select(PetPool).limit(1)):
        session.add_all(
            PetPool(pet_type=name, pet_category=category, description=description, enabled=True)
            for name, category, description in PET_POOL
        )

    if not session.scalar(select(TrainingTask).limit(1)):
        for task_id, title, fraud_type, risk_level, difficulty, duration, base_reward, max_reward in TRAINING_TASKS:
            session.add(
                TrainingTask(
                    id=task_id,
                    title=title,
                    fraud_type=fraud_type,
                    risk_level=risk_level,
                    difficulty=difficulty,
                    duration_minutes=duration,
                    base_reward=base_reward,
                    max_reward=max_reward,
                    enabled=True,
                )
            )

    # 训练题目：强制更新（先删后增），确保题目数量与题库定义一致
    for task_id, questions in TRAINING_QUESTIONS.items():
        existing = session.scalars(select(TrainingQuestion).where(TrainingQuestion.task_id == task_id)).all()
        existing_ids = {q.id for q in existing}
        expected_ids = {q["id"] for q in questions}
        if existing_ids == expected_ids:
            continue
        for old_q in existing:
            session.delete(old_q)
        for question in questions:
            session.add(
                TrainingQuestion(
                    id=question["id"],
                    task_id=task_id,
                    question_type=question["question_type"],
                    stem=question["stem"],
                    options_json=json.dumps(question["options"], ensure_ascii=False),
                    correct_answer_json=json.dumps(question["correct_answer"], ensure_ascii=False),
                    explanation=question["explanation"],
                )
            )

    if not session.scalar(select(GrowthRule).limit(1)):
        session.add_all(
            [
                GrowthRule(rule_key="formula", rule_value="最终成长值 = 基础完成分 + 正确率加成 + 难度加成", description="训练成长值计算公式"),
                GrowthRule(rule_key="dailyMaxGrowth", rule_value="300", description="每日总成长值上限"),
                GrowthRule(rule_key="taskMaxGrowth", rule_value="90", description="单任务成长值上限"),
                GrowthRule(rule_key="suspiciousCheckDailyLimit", rule_value="3", description="可疑信息判断每日奖励次数"),
            ]
        )

    # 知识条目：按 ID 增量补充，保证新条目也能进入已有数据库
    knowledge_items_seed = [
        KnowledgeItem(
            id="know-ai-face",
            category="AI换脸",
            title="短视频确认不能替代电话核验",
            risk_level="高风险",
            typical_phrase="刚才视频你也看到了，是本人，先转钱别打电话。",
            recognition_points="短暂视频、拒绝电话、催促转账同时出现。",
            suggestions="使用原有电话、线下同学或官方渠道二次确认。",
            related_task_id="ai-face",
        ),
        KnowledgeItem(
            id="know-refund",
            category="冒充客服",
            title="退款不需要屏幕共享和验证码",
            risk_level="高风险",
            typical_phrase="退款需要开启屏幕共享，请提供验证码。",
            recognition_points="屏幕共享、验证码、退款异常组合出现。",
            suggestions="停止共享屏幕，通过官方 App 或客服电话核实。",
            related_task_id="refund",
        ),
        KnowledgeItem(
            id="know-brushing",
            category="刷单返利",
            title="先垫付后返利的兼职都是诈骗",
            risk_level="高风险",
            typical_phrase="日结高薪、先垫付、做满三单才能提现。",
            recognition_points="垫付资金、高额返利、做满任务才提现三要素同时出现。",
            suggestions="任何要求先垫付资金的兼职都涉嫌诈骗，立即停止并删除。",
            related_task_id="brushing",
        ),
        KnowledgeItem(
            id="know-investment",
            category="虚假投资",
            title="稳赚不赔是不存在的投资谎言",
            risk_level="高风险",
            typical_phrase="稳赚不赔、年化收益30%、老师带单。",
            recognition_points="承诺高收益、私下转账入金、群里老师带单晒收益。",
            suggestions="通过银行或持牌金融机构官方渠道理财，不转入个人账户。",
            related_task_id="investment",
        ),
        KnowledgeItem(
            id="know-game",
            category="游戏交易",
            title="保证金和解冻费是无底洞",
            risk_level="中风险",
            typical_phrase="账号交易需要先交保证金才能解冻提现。",
            recognition_points="线下交易、保证金、解冻费、低价诱惑同时出现。",
            suggestions="只在游戏官方或正规第三方平台交易，不私下转账。",
            related_task_id="game",
        ),
        KnowledgeItem(
            id="know-teacher-fee",
            category="冒充老师",
            title="群里收款码要先核实再付款",
            risk_level="高风险",
            typical_phrase="班级群发收款码，限时交资料费，账户为个人账户。",
            recognition_points="群里突现收款码、催促限时交费、收款账户是个人账户。",
            suggestions="通过学校已知联系方式直接联系老师本人核实，不在群里直接扫码。",
            related_task_id="teacher-fee",
        ),
        KnowledgeItem(
            id="know-verify-code",
            category="账户安全",
            title="验证码是账户最后一道防线",
            risk_level="高风险",
            typical_phrase="请把收到的验证码发给我，用于身份验证。",
            recognition_points="任何人索要验证码，无论自称客服、银行还是公安。",
            suggestions="验证码绝不提供给任何人，客服、银行、公安都不会索要验证码。",
            related_task_id="anti-fraud-basics",
        ),
        KnowledgeItem(
            id="know-pubsecurity",
            category="冒充公检法",
            title="公检法不会电话办案到安全账户",
            risk_level="高风险",
            typical_phrase="你涉嫌洗钱，请配合调查将资金转入安全账户自证清白。",
            recognition_points="电话办案、安全账户、要求转账自证清白。",
            suggestions="立即挂断并拨打110或96110报警，公检法不会通过电话要求转账。",
            related_task_id="pubsecurity",
        ),
        # —— 以下为基于全网真实案例扩充的知识条目 ——
        KnowledgeItem(
            id="know-campus-loan",
            category="校园贷",
            title="“无抵押低息秒到账”背后是砍头息和高利贷",
            risk_level="高风险",
            typical_phrase="只需身份证，5分钟到账，零抵押零担保，月息仅1%。",
            recognition_points="无抵押低息宣传、砍头息（到手金额少于借款）、7天短周期高息、逾期后诱导“以贷养贷”、暴力催收。",
            suggestions="国家明令禁止向大学生发放校园贷；借款应通过银行等正规渠道；年利率超过LPR四倍（约14.8%）的部分不受法律保护；遇暴力催收向银保监会、教育部举报。",
            related_task_id="campus-loan",
        ),
        KnowledgeItem(
            id="know-cancel-campus-loan",
            category="注销校园贷",
            title="“注销校园贷记录否则影响征信”是新型诈骗",
            risk_level="高风险",
            typical_phrase="你大学期间注册过校园贷账户，不注销会影响个人征信，请按指引下载APP验证还款能力。",
            recognition_points="冒充金融平台客服、以影响征信恐吓、要求下载陌生APP、屏幕共享或转账验证还款能力。",
            suggestions="个人征信由央行统一管理，不存在“注销就能洗白”或“花钱修复”；接到此类电话通过官方APP核实，不下载陌生软件、不开启屏幕共享、不转账。",
            related_task_id="campus-loan",
        ),
        KnowledgeItem(
            id="know-training-loan",
            category="培训贷",
            title="“培训包就业分期付学费”是培训贷陷阱",
            risk_level="高风险",
            typical_phrase="包教包会短视频剪辑，轻松月入过万，可分期付学费，签订协议即安排兼职。",
            recognition_points="技能培训+兼职保障打包宣传、诱导签订贷款协议、课程质量差且无法退费、贷款平台与培训机构分离。",
            suggestions="警惕“先付费再推荐工作”的培训；《劳动合同法》规定用人单位不得向劳动者收取财物；签合同前看清贷款条款和退费规则，必要时联系辅导员确认。",
            related_task_id="campus-loan",
        ),
        KnowledgeItem(
            id="know-pig-butchering",
            category="杀猪盘",
            title="网恋交友+介绍投资是杀猪盘",
            risk_level="高风险",
            typical_phrase="我研究的这个投资/彩票稳赚不赔，带你一起赚钱，咱们将来买房安家。",
            recognition_points="婚恋交友软件结识、迅速确立恋爱关系、长期嘘寒问暖“养猪”、介绍投资或博彩“杀猪”、提现受阻后失联。",
            suggestions="没见过面的网友一谈钱即高度警惕；任何“稳赚”投资都是诈骗；网恋不转账；发现无法提现立即停止操作并报警。",
            related_task_id="investment",
        ),
        KnowledgeItem(
            id="know-impersonate-friend",
            category="冒充熟人",
            title="QQ/微信被盗冒充同学借钱要电话核验",
            risk_level="高风险",
            typical_phrase="我家属生病急用钱，微信没绑卡，你帮我转点到这个账号，再帮我充个话费。",
            recognition_points="账号被盗、家属生病或急事催促、提供二维码或手机号要求转账充值、拒绝电话或语音核验。",
            suggestions="任何熟人借钱都应通过原有电话或当面核实；留意账号语气、用词的异常变化；不扫来路不明的二维码；转账前务必二次确认对方身份。",
            related_task_id="impersonate-friend",
        ),
        KnowledgeItem(
            id="know-concert-ticket",
            category="演唱会门票",
            title="“内部票/代理费”演唱会门票诈骗",
            risk_level="高风险",
            typical_phrase="内部预留票原价转让，扫码支付锁定名额；或招募学生代理，交代理费赚生活费。",
            recognition_points="脱离官方平台交易、要求扫码或微信转账、伪造订单截图、招代理收代理费、“没备注需重新转账”反复索款。",
            suggestions="演唱会已实名制购票，只在官方票务平台购买；后援会从不私信集资；任何“内部票”都不靠谱；被要求连续转账即是诈骗，立即停止并报警。",
            related_task_id="concert-ticket",
        ),
        KnowledgeItem(
            id="know-flight-refund",
            category="航班退改签",
            title="“航班取消补偿退改签”是机票诈骗",
            risk_level="高风险",
            typical_phrase="您预订的航班因机械故障取消，请联系客服办理退改签并领取补偿金。",
            recognition_points="境外电话或短信、冒充航司客服、要求下载APP开启屏幕共享、引导输入银行密码、要求转账领取补偿金。",
            suggestions="通过航空公司官方APP或官网核实航班状态；正规退改签不要求屏幕共享、不要求转账；补偿金绝不会要求“先转账验证”；遇可疑电话直接挂断并致电航司官方客服。",
            related_task_id="flight-refund",
        ),
        KnowledgeItem(
            id="know-job-fee",
            category="求职交费",
            title="“入职先交保证金/体检费”是求职诈骗",
            risk_level="中风险",
            typical_phrase="岗位无学历要求月薪8000，入职需缴纳体检费、服装费、培训押金，入职后退还。",
            recognition_points="高薪低门槛诱饵、入职前收取各类费用（体检费/服装费/培训押金）、收费后以“岗位调整”拖延、最终失联。",
            suggestions="《劳动合同法》明确规定用人单位不得向劳动者收取财物；通过学校就业中心或正规招聘平台求职；坚决拒交任何抵押金、风险金、报名费、培训费。",
            related_task_id="job-academic",
        ),
        KnowledgeItem(
            id="know-secondhand",
            category="二手交易",
            title="“脱离平台先付定金”二手交易诈骗",
            risk_level="中风险",
            typical_phrase="走线下更便宜，先付定金留货，微信转账即可，发货单马上发你。",
            recognition_points="闲鱼/小红书联系后要求脱离平台交易、要求先付定金或全款、提供虚假发货单、收款后拉黑。",
            suggestions="二手交易必须走官方平台担保流程；不私下微信/支付宝转账；不购买无发票无保修的高价数码产品；对方催促脱离平台即警惕。",
            related_task_id="secondhand",
        ),
        KnowledgeItem(
            id="know-express-claim",
            category="冒充快递理赔",
            title="“包裹丢失理赔要屏幕共享”是升级版客服诈骗",
            risk_level="高风险",
            typical_phrase="您的包裹丢失可3倍赔偿，请下载会议APP开启屏幕共享办理理赔。",
            recognition_points="冒充快递/电商客服、先打小额理赔款获取信任、要求下载小众会议APP、屏幕共享窃取银行卡号和验证码、转账盗刷。",
            suggestions="屏幕共享等于“裸奔”，任何客服要求屏幕共享都是诈骗；通过快递公司或电商平台官方客服核实；不下载陌生人指定的APP；不向任何人提供验证码。",
            related_task_id="refund",
        ),
        KnowledgeItem(
            id="know-academic-fraud",
            category="学术诈骗",
            title="“论文代发/保研内定/竞赛包获奖”是学术骗局",
            risk_level="中风险",
            typical_phrase="30万打通关系保送名校，或交报名费保获奖，或论文代发包录用。",
            recognition_points="代写论文收定金发拼凑内容、保研黑幕伪造材料致申请禁入、竞赛内定山寨组委会卷款跑路。",
            suggestions="论文、竞赛、保研没有“钞能力”捷径；代写属于学术污点，被曝即开除；遇到此类骗局应举报，避免下一届同学受害。",
            related_task_id="job-academic",
        ),
        KnowledgeItem(
            id="know-free-gift",
            category="免费领取",
            title="“免费领取礼品+屏幕共享”是免费领诈骗",
            risk_level="高风险",
            typical_phrase="小红书免费领取围巾/行李箱，加QQ按指引操作即可，公司承担费用。",
            recognition_points="免费领取诱饵、QQ语音+屏幕共享、引导充话费或购买虚拟产品、诱导开通花呗/微博借钱等借贷产品。",
            suggestions="天上不会掉馅饼，不轻信“免费领取”；不与陌生人开启屏幕共享；不按陌生人指引开通借贷产品；发现被骗立即冻结账户并报警。",
            related_task_id="free-gift",
        ),
        # —— 以下为基于国家反诈中心《2025版防范电信网络诈骗宣传手册》新增条目 ——
        KnowledgeItem(
            id="know-million-protection",
            category="百万保障诈骗",
            title="「百万保障」到期自动扣费？完全是诈骗！",
            risk_level="高风险",
            typical_phrase="您的微信/支付宝/抖音「百万保障」服务已到期，不关闭将每月自动扣费800元，请下载会议APP由客服指导关闭。",
            recognition_points="冒充微信/支付宝/抖音平台客服、声称「百万保障」到期需续费或关闭、威胁自动扣费或影响征信、要求下载会议APP开启屏幕共享、引导转账验证资金。",
            suggestions="「百万保障」是微信/支付宝等平台的免费安全服务，不会到期、不会扣费、不影响征信；接到此类电话立即挂断，通过官方APP客服核实；任何要求下载APP、屏幕共享、转账的都是诈骗。",
            related_task_id="financial-scam",
        ),
        KnowledgeItem(
            id="know-loan-credit",
            category="贷款征信诈骗",
            title="无抵押低息贷款先交费？贷款未到钱先没",
            risk_level="高风险",
            typical_phrase="您已获批30万额度，无抵押低利率秒到账，但需先交保证金/解冻费/刷流水激活账户。",
            recognition_points="无抵押低息秒批宣传、要求先交保证金/解冻费/会员费、声称刷流水提升信用评级、「征信修复」骗局、放款前任何收费。",
            suggestions="正规贷款机构在放款前不收任何费用；个人征信由央行统一管理，任何声称可「修复征信」的都是诈骗；不要将银行卡号、验证码提供给陌生人；有贷款需求通过银行等正规渠道。",
            related_task_id="financial-scam",
        ),
        KnowledgeItem(
            id="know-fake-shopping",
            category="虚假购物服务",
            title="脱离平台私下交易？付款后拉黑失联",
            risk_level="中风险",
            typical_phrase="平台手续费太高，走微信转账更便宜，先付款马上发货，转账后发物流单号。",
            recognition_points="在社交平台（抖音/快手/小红书）看到低价商品广告、引诱脱离官方平台私下转账、付款后不发货或发空包、以「账号冻结/订单异常」为由诱导开启屏幕共享、教育机构退费名义诱导下载APP。",
            suggestions="购物只走官方平台担保交易；不向个人微信/支付宝转账；不相信「内部价」「友情价」等低价诱饵；教育退费通过官方渠道，不下载陌生APP；遭遇诈骗保存证据并拨打110。",
            related_task_id="financial-scam",
        ),
        KnowledgeItem(
            id="know-porn-trap",
            category="色情诱导诈骗",
            title="色情小卡片+刷单任务=连环陷阱",
            risk_level="高风险",
            typical_phrase="扫码进群即可同城约会，完成任务还能返利赚钱，先充会员再解锁。",
            recognition_points="色情小卡片/弹窗/短信引流、下载陌生APP或加群、以「完成任务即可获取色情服务」为诱饵要求垫资刷单、屏幕共享窃取通讯录后敲诈勒索。",
            suggestions="传播色情信息及刷单均属违法行为；不扫描来路不明的小卡片二维码；不下载非官方应用商店的APP；遭遇敲诈勿转账，第一时间报警；洁身自好是最好的防护。",
            related_task_id="brushing",
        ),
        KnowledgeItem(
            id="know-screen-share",
            category="屏幕共享诈骗",
            title="屏幕共享=你的手机在裸奔",
            risk_level="高风险",
            typical_phrase="为方便办理退款/注销服务/配合调查，请下载会议APP并开启屏幕共享，我需要指导您操作。",
            recognition_points="任何陌生人要求下载会议/远程控制类APP、要求开启屏幕共享或无障碍权限、以退款理赔/关闭扣费/配合调查为名、操作中手机突然黑屏或卡顿、提出「远程协助」「同步操作」。",
            suggestions="屏幕共享会暴露银行卡号、密码、验证码等所有信息，相当于把保险柜钥匙交给骗子；任何客服/公检法/贷款机构要求屏幕共享的都是诈骗；已开启立即关闭并卸载该APP；同时拔卡断网防止继续操作。",
            related_task_id="screen-nfc",
        ),
        KnowledgeItem(
            id="know-nfc-fraud",
            category="NFC盗刷",
            title="手机NFC贴靠银行卡就能盗刷？这个功能要当心",
            risk_level="高风险",
            typical_phrase="为了验证您的卡片真实性，请将银行卡贴在手机背面，系统会自动读取验证。",
            recognition_points="诱导将银行卡与手机NFC贴靠、声称「验证卡片」「激活账户」「绑定安全系统」、要求下载非官方APP开启NFC权限、后台读取并转移卡内资金。",
            suggestions="切勿随意将手机与银行卡进行贴靠操作；不向陌生APP授权NFC功能；正规银行和支付平台不会通过电话引导NFC验证；发现NFC异常交易立即冻结银行卡并报警。",
            related_task_id="screen-nfc",
        ),
        KnowledgeItem(
            id="know-cash-gold",
            category="寄送现金黄金",
            title="要求取现金/买黄金再寄送？这是洗钱新套路",
            risk_level="高风险",
            typical_phrase="线上转账会被风控拦截，为了您的资金安全，请取出现金或购买黄金，通过网约车/快递送到指定地点，我们帮您充值。",
            recognition_points="诱导线下取现或购买黄金/手机等高价值物品、要求通过网约车/快递/跑腿送达指定地点、以「避免风控」「安全充值」为理由、绝不使用正规线上支付渠道。",
            suggestions="正规投资理财绝不会要求购买黄金后邮寄；凡是要求取现金/买黄金并通过网约车或快递交给陌生人的，都是诈骗洗钱；发现已被诱导操作，立即停止并拨打96110；快递员/金店员工遇异常大额购金应提高警惕。",
            related_task_id="investment",
        ),
        KnowledgeItem(
            id="know-bangxin",
            category="帮信与两卡",
            title="出租出借电话卡/银行卡=帮信罪，三年起步",
            risk_level="高风险",
            typical_phrase="借你银行卡转个账，给你500元辛苦费；或高价收购闲置电话卡，用途正当不用担心。",
            recognition_points="高价收购/租借电话卡或银行卡、承诺「日结」「高额报酬」「不用干活」、提供两卡被用于诈骗/洗钱/赌博等犯罪活动。",
            suggestions="根据《刑法》第287条之二，帮信罪最高可判处三年有期徒刑；任何出租、出借、出售两卡的行为均涉嫌违法犯罪；切勿因贪图小利成为「电诈工具人」；发现买卖两卡行为拨打96110举报。",
            related_task_id="bangxin",
        ),
        KnowledgeItem(
            id="know-crypto",
            category="虚拟货币诈骗",
            title="虚拟币投资稳赚不赔？平台都是假的",
            risk_level="高风险",
            typical_phrase="跟着老师买虚拟币，内幕消息包赚，前期先少量尝试，看到收益了再加大投入。",
            recognition_points="宣称「内幕消息」「稳赚不赔」的虚拟币投资、搭建虚假交易平台显示虚假收益、前期小额可提现诱导大额投入、要求通过「币商」线下交易购买虚拟币、提现时以「缴税/解冻」为由再索款。",
            suggestions="虚拟货币交易在中国不受法律保护；所有声称「稳赚」的虚拟币投资都是诈骗；不下载非应用商店的虚拟币交易APP；任何要求线下买币或邮寄现金换币的都是诈骗；发现异常立即停止操作并报警。",
            related_task_id="investment",
        ),
        KnowledgeItem(
            id="know-fake-leader",
            category="冒充领导",
            title="微信上的「领导」让你转账？先打电话核实",
            risk_level="高风险",
            typical_phrase="我是XXX（单位领导），这是我的新号，有个急事需要你帮忙转一笔款，事后报销。",
            recognition_points="冒充单位领导/老师/上级、使用领导真实头像和职务信息、先嘘寒问暖后以「有急事」「不方便亲自操作」为由要求转账、「正在开会不方便接电话」拒绝语音核实。",
            suggestions="任何领导/老师通过微信QQ要求转账汇款的，必须通过原有电话或当面核实；不按对方要求修改备注名或通讯录；发现异常立即向单位保卫部门或110报警。",
            related_task_id="teacher-fee",
        ),
        KnowledgeItem(
            id="know-points-clear",
            category="积分清零诈骗",
            title="「积分即将清零」的短信，点链接就中招",
            risk_level="中风险",
            typical_phrase="【XX银行】您的账户积分即将清零，请点击链接兑换礼品，过期无效！",
            recognition_points="仿冒银行/运营商/电商平台发送积分清零短信、短信中含有钓鱼链接、点击后要求输入银行卡号/密码/验证码、跳转到仿冒页面窃取信息。",
            suggestions="不点击短信中的不明链接；积分兑换通过官方APP或官方网站操作；任何要求输入银行卡密码和验证码的「积分兑换」都是诈骗；收到可疑短信直接删除并向官方客服核实。",
            related_task_id="points-clear",
        ),
        KnowledgeItem(
            id="know-delivery-lead",
            category="快递引流诈骗",
            title="快递包裹里的「扫码领奖」小卡片是陷阱",
            risk_level="中风险",
            typical_phrase="【恭喜中奖】扫码添加客服领20元红包/水果/礼品，限时领取先到先得！",
            recognition_points="收到陌生快递中含有中奖/免费领礼品卡片、扫描二维码后添加陌生人微信拉入群聊、群内发布刷单或投资任务。",
            suggestions="天下没有免费的午餐；不扫描快递包裹中的不明二维码；不进陌生群聊；「转发可领礼品」「邀请进群领红包」都是诈骗引流手段；未网购却收到包裹更需高度警惕。",
            related_task_id="delivery-lead",
        ),
        KnowledgeItem(
            id="know-brush-flow",
            category="刷流水诈骗",
            title="贷款「包装账户刷流水」？你在帮骗子洗钱",
            risk_level="高风险",
            typical_phrase="你的银行流水不够，我们需要帮你「包装账户」刷流水才能放款，先转一笔钱到指定账户验证。",
            recognition_points="声称需「包装账户」「刷流水」「资质验资」才能放贷、要求向陌生账户转账制造虚假流水、「刷流水」本身是违法行为。",
            suggestions="刷流水是违法行为，参与可能构成帮信罪；正规贷款不看「流水包装」；任何要求先转账「刷流水」再放款的都是诈骗；已被诱导操作后立即停止并报警。",
            related_task_id="financial-scam",
        ),
        KnowledgeItem(
            id="know-gift-card",
            category="购物卡洗钱",
            title="大量购买购物卡并提供卡密？你在帮骗子套现",
            risk_level="高风险",
            typical_phrase="平台系统升级暂时无法线上转账，请到超市购买购物卡，把卡号和密码发给我完成充值。",
            recognition_points="要求大量购买超市购物卡/电商礼品卡、索要购物卡卡号和密码、「系统升级」「账户异常」等理由拒绝线上支付。",
            suggestions="凡是要求大量购买购物卡并提供卡号和密码的，都是诈骗洗钱手法；正规投资和消费不会要求用购物卡支付；超市/便利店员工遇顾客大量购买购物卡应进行防骗提醒。",
            related_task_id="financial-scam",
        ),
        KnowledgeItem(
            id="know-anti-fraud-tools",
            category="九大反诈利器",
            title="国家九大反诈利器——给你的钱包装上防火墙",
            risk_level="低风险",
            typical_phrase="（工具介绍类）国家反诈中心APP、96110、12381、一证通查、一键查卡、反诈名片、一证通查2.0、境外来电提醒、AI内容鉴定。",
            recognition_points="九大反诈利器全覆盖：①国家反诈中心APP（来电预警/APP自查/AI内容鉴定）②96110预警劝阻专线（来电请接听）③12381涉诈预警短信④全国移动电话卡一证通查⑤全国互联网账号一证通查2.0⑥云闪付一键查卡⑦反诈名片（标记警方来电）⑧境外来电提醒服务⑨2026新增：涉诈APP自检+AI内容鉴定。",
            suggestions="立即下载国家反诈中心APP并实名注册开启来电预警；接到96110来电务必接听；定期使用一证通查和互联网账号一证通查清理不明号码和账号；开通运营商境外来电拦截功能。",
            related_task_id="anti-fraud-basics",
        ),
        KnowledgeItem(
            id="know-20-keywords",
            category="二十个防诈关键词",
            title="公安部提炼20个防诈关键词——快速破译骗局密码",
            risk_level="高风险",
            typical_phrase="屏幕共享、百万保障、安全账户、NFC盗刷、两卡、帮信行为、刷流水、积分清零、修复征信、快递引流、现金黄金、购物卡、内幕消息、电诈工具人、虚拟货币、色情小卡片、刷单做任务、未知链接和二维码、小众聊天软件、境外来电。",
            recognition_points="听到这20个关键词立即警觉：1屏幕共享=裸奔 2百万保障=骗局 3安全账户=不存在 4NFC盗刷=新手法 5两卡=不能卖 6帮信罪=三年起步 7刷流水=违法 8积分清零=钓鱼 9修复征信=不可能 10快递引流=陷阱 11现金黄金=洗钱 12购物卡=套现 13内幕消息=谎言 14电诈工具人=帮凶 15虚拟货币=不受保护 16色情小卡片=刷单引流 17刷单做任务=诈骗 18未知链接和二维码=不点不扫 19小众聊天软件=规避监管 20境外来电=99%诈骗。",
            suggestions="牢记三不一多原则：未知链接不点击、陌生来电不轻信、个人信息不透露、转账汇款多核实；遇到任何20个关键词中的情形立即警惕；下载国家反诈中心APP开启来电预警；遇可疑拨打96110咨询；被骗后立即拨打110并保留证据。",
            related_task_id="anti-fraud-basics",
        ),
        KnowledgeItem(
            id="know-anti-fraud-rules",
            category="反诈总则",
            title="反诈公式速记与「六不」原则",
            risk_level="高风险",
            typical_phrase="反诈公式：做任务+小额返利+大额投入=刷单；网恋+投资=杀猪盘；涉嫌违法+安全账户=冒充公检法。",
            recognition_points="六不原则：不点陌生链接、不透露身份/验证码、不信高回报、不向陌生账户转账、不办非正规校园贷、不提供敏感区域照片。",
            suggestions="牢记反诈公式速记快速识别骗局类型；安装「国家反诈中心」APP并开启来电预警；遇疑拨打96110反诈专线；被骗后立即止损、保留聊天和转账证据、拨打110报警。",
            related_task_id="anti-fraud-basics",
        ),
    ]
    for item in knowledge_items_seed:
        if not session.get(KnowledgeItem, item.id):
            session.add(item)

    if not session.scalar(select(FraudCase).limit(1)):
        session.add(
            FraudCase(
                id="case-ai-face-001",
                title="AI 换脸冒充同学借钱",
                fraud_type="AI 换脸",
                source_channel="聊天记录",
                risk_level="高风险",
                ai_confidence=0.88,
                desensitized=True,
                status="已生成训练题",
                summary="冒充熟人通过短视频建立信任并要求立即转账。",
                risk_tags_json=json.dumps(["短暂视频", "拒绝电话核验", "立即转账"], ensure_ascii=False),
            )
        )

    for pet_id, owner_id, pet_type, category, growth, last_training_at in RANKING_PETS:
        user = session.scalar(select(User).where(User.owner_id == owner_id))
        if not user:
            user = User(owner_id=owner_id, has_completed_assessment=True, has_pet=True)
            session.add(user)
        if not session.scalar(select(Pet).where(Pet.pet_id == pet_id)):
            level = pet_level(growth)
            session.add(
                Pet(
                    pet_id=pet_id,
                    owner_id=owner_id,
                    pet_type=pet_type,
                    pet_category=category,
                    level=level,
                    stage=pet_stage(level),
                    growth_value=growth,
                    last_training_at=last_training_at,
                )
            )

    session.commit()


def pet_to_response(pet: Pet) -> dict[str, object]:
    current_min, next_value = level_bounds(pet.level)
    return {
        "petId": pet.pet_id,
        "ownerId": pet.owner_id,
        "type": pet.pet_type,
        "category": pet.pet_category,
        "petName": pet.pet_name or "",
        "avatarEmoji": pet.avatar_emoji or "",
        "level": pet.level,
        "stage": pet.stage,
        "growthValue": pet.growth_value,
        "currentLevelMin": current_min,
        "nextLevelValue": next_value,
        "lastTrainingAt": pet.last_training_at.strftime("%Y-%m-%d %H:%M") if pet.last_training_at else "",
    }
