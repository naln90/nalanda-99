"""图片分析模块 — 聊天截图上传与风险文本识别。

当前为模拟实现（Demo 环境无真实 OCR 引擎）：
- 接收图片文件，校验格式和大小
- 基于文件内容哈希从预置样本库中选取"模拟识别文本"
- 对识别文本进行关键词匹配，推断诈骗类型和风险等级
- 返回结构化分析结果供前端展示与搜索

生产环境可替换为真实 OCR + LLM 分析链路：
  1. OCR 提取图片文字（如 PaddleOCR / Tesseract / 云 API）
  2. NLP 分句与话术特征匹配
  3. LLM 辅助分类与风险评分
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

# 预置模拟样本：各类诈骗的典型聊天截图文本
# 文件内容哈希对样本数量取模，确保同一张图始终得到相同结果
SAMPLE_POOLS: dict[str, list[dict[str, Any]]] = {
    "刷单返利": [
        {"text": "亲，想做兼职吗？动动手指日赚300，先垫付500元立返650，稳赚不赔！", "keywords": ["垫付", "日赚", "立返"]},
        {"text": "你已完成第一单，佣金5元已到账。第二单需垫付2000元，完成后连本带利返还2800元。", "keywords": ["垫付", "佣金", "连本带利"]},
        {"text": "系统检测到您操作超时，需要再完成三单才能解冻之前的资金。", "keywords": ["超时", "解冻", "资金"]},
    ],
    "游戏交易": [
        {"text": "兄弟，我这有全套绝版皮肤号，走平台手续费太贵，微信直转我给你半价，先转钱我马上发号。", "keywords": ["走平台", "手续费", "微信直转", "先转钱"]},
        {"text": "账号已发出，但你需要缴纳2000元保证金才能解封账号使用权，交完即退。", "keywords": ["保证金", "解封", "交完即退"]},
        {"text": "低价出号，平台交易太麻烦，加我QQ，先发一半钱，我让你验号。", "keywords": ["低价出号", "平台交易", "验号"]},
    ],
    "虚假客服": [
        {"text": "您好，我是XX客服。您购买的商品存在质量问题，现为您办理双倍理赔，请点击链接填写退款信息。", "keywords": ["客服", "质量问题", "双倍理赔", "链接"]},
        {"text": "您的快递已丢失，我们将赔付300元。请下载XX会议APP开启屏幕共享，我们指导您操作退款。", "keywords": ["快递丢失", "赔付", "屏幕共享", "操作退款"]},
        {"text": "您开通了百万保障服务，今晚即将扣费，如需取消请按我要求操作。", "keywords": ["百万保障", "扣费", "取消"]},
    ],
    "冒充老师": [
        {"text": "各位家长，本学期资料费统一收取280元，请扫码转入此账户，备注孩子姓名。", "keywords": ["资料费", "扫码", "转入此账户"]},
        {"text": "学校临时通知，需缴纳200元体检费，请尽快转账，逾期影响学籍。", "keywords": ["体检费", "转账", "逾期", "学籍"]},
        {"text": "我是教务处王老师，你挂科了需要补交重修费500元到个人账户。", "keywords": ["教务处", "重修费", "个人账户"]},
    ],
    "虚假招聘": [
        {"text": "高薪诚聘打字员，日结300元，无需经验，在家即可。入职需缴纳399元培训费。", "keywords": ["高薪", "日结", "培训费"]},
        {"text": "恭喜通过面试！入职前需缴纳服装费500元和押金800元，满月全额退还。", "keywords": ["服装费", "押金", "满月退还"]},
        {"text": "兼职刷单，每单佣金15-50元，无需垫付，但需先交99元会员费。", "keywords": ["刷单", "佣金", "会员费"]},
    ],
    "奖助学金": [
        {"text": "同学你好，你有一笔国家助学金待领取，请登录指定网站填写银行卡号和验证码。", "keywords": ["助学金", "银行卡号", "验证码"]},
        {"text": "教育部通知：助学贷款退费，请添加QQ客服并提供身份证照片办理。", "keywords": ["助学贷款", "退费", "身份证照片"]},
        {"text": "学校奖学金发放，需先缴纳300元手续费到指定账户，24小时内到账。", "keywords": ["奖学金", "手续费", "指定账户"]},
    ],
    "AI换脸": [
        {"text": "爸，我换手机了，这是新微信。我急用钱，你先转我5000，晚上视频跟你说。", "keywords": ["换手机", "新微信", "急用钱", "转我"]},
        {"text": "视频里确实是他的脸，他说在国外被扣了，急需赎金，让我先转账。", "keywords": ["视频", "国外", "赎金", "转账"]},
        {"text": "亲爱的，我在外地出差出事了，别告诉爸妈，先给我转2万应急。", "keywords": ["出差", "别告诉", "转2万"]},
    ],
    "求职培训贷": [
        {"text": "培训结束包就业，月薪不低于8000。但培训费19800需办理分期，从工资里扣。", "keywords": ["包就业", "培训费", "分期", "工资里扣"]},
        {"text": "0元入学，先学后付！签订培训协议即可办理教育分期，无利息压力。", "keywords": ["0元入学", "先学后付", "教育分期"]},
        {"text": "课程费用可以贷款，我们合作银行秒批，你只需要在手机上签个字。", "keywords": ["贷款", "合作银行", "签个字"]},
    ],
    "网购退款": [
        {"text": "您的订单异常，请点击链接完善信息，否则无法发货。链接：xxx.com", "keywords": ["订单异常", "完善信息", "链接"]},
        {"text": "商家操作失误，给您开通了VIP会员，每月扣费500元，如需取消请提供验证码。", "keywords": ["VIP会员", "扣费", "验证码"]},
        {"text": "快递已到驿站，但需支付3元取件费，扫码支付后凭码取件。", "keywords": ["取件费", "扫码支付"]},
    ],
    "虚假投资理财": [
        {"text": "内幕消息，这只股票明天必涨，跟我操作稳赚。先投5万试试水，群里人都翻倍了。", "keywords": ["内幕消息", "必涨", "稳赚", "翻倍"]},
        {"text": "数字货币新风口，导师带单，入金1万送5000，提现秒到账。", "keywords": ["数字货币", "导师带单", "入金", "提现"]},
        {"text": "稳赚不赔的理财项目，年化收益30%，本金随时可取，名额有限。", "keywords": ["稳赚不赔", "年化收益30%", "名额有限"]},
    ],
}

# 非诈骗的正常聊天样本（用于对比/负样本）
SAFE_SAMPLES = [
    {"text": "明天下午三点在图书馆开会，记得带上笔记本和笔。", "keywords": []},
    {"text": "妈妈给我转生活费了，2000元已到账，谢谢妈！", "keywords": []},
    {"text": "快递已签收，麻烦给个五星好评，有问题联系客服。", "keywords": []},
    {"text": "这节课调到了周五上午，请大家注意查看课表。", "keywords": []},
    {"text": "周末聚餐AA，人均68元，收款码发群里了。", "keywords": []},
]


# 关键词 -> 诈骗类型映射（用于文本分类）
KEYWORD_TO_FRAUD: dict[str, str] = {
    "垫付": "刷单返利", "日赚": "刷单返利", "立返": "刷单返利", "佣金": "刷单返利",
    "连本带利": "刷单返利", "超时": "刷单返利", "解冻": "刷单返利",
    "走平台": "游戏交易", "手续费": "游戏交易", "微信直转": "游戏交易",
    "先转钱": "游戏交易", "保证金": "游戏交易", "解封": "游戏交易", "验号": "游戏交易",
    "客服": "虚假客服", "质量问题": "虚假客服", "双倍理赔": "虚假客服",
    "链接": "虚假客服", "快递丢失": "虚假客服", "赔付": "虚假客服",
    "屏幕共享": "虚假客服", "操作退款": "虚假客服", "百万保障": "虚假客服",
    "扣费": "虚假客服", "资料费": "冒充老师", "扫码": "冒充老师",
    "转入此账户": "冒充老师", "体检费": "冒充老师", "学籍": "冒充老师",
    "教务处": "冒充老师", "重修费": "冒充老师", "个人账户": "冒充老师",
    "高薪": "虚假招聘", "日结": "虚假招聘", "培训费": "虚假招聘",
    "服装费": "虚假招聘", "押金": "虚假招聘", "满月退还": "虚假招聘",
    "刷单": "虚假招聘", "会员费": "虚假招聘",
    "助学金": "奖助学金", "银行卡号": "奖助学金", "验证码": "奖助学金",
    "助学贷款": "奖助学金", "退费": "奖助学金", "身份证照片": "奖助学金",
    "奖学金": "奖助学金", "手续费": "奖助学金", "指定账户": "奖助学金",
    "换手机": "AI换脸", "新微信": "AI换脸", "急用钱": "AI换脸",
    "转我": "AI换脸", "视频": "AI换脸", "国外": "AI换脸", "赎金": "AI换脸",
    "出差": "AI换脸", "别告诉": "AI换脸",
    "包就业": "求职培训贷", "培训费": "求职培训贷", "分期": "求职培训贷",
    "工资里扣": "求职培训贷", "0元入学": "求职培训贷", "先学后付": "求职培训贷",
    "教育分期": "求职培训贷", "贷款": "求职培训贷", "签个字": "求职培训贷",
    "订单异常": "网购退款", "完善信息": "网购退款", "VIP会员": "网购退款",
    "取件费": "网购退款", "扫码支付": "网购退款",
    "内幕消息": "虚假投资理财", "必涨": "虚假投资理财", "稳赚": "虚假投资理财",
    "翻倍": "虚假投资理财", "数字货币": "虚假投资理财", "导师带单": "虚假投资理财",
    "入金": "虚假投资理财", "年化收益": "虚假投资理财", "名额有限": "虚假投资理财",
}

# 风险等级映射
RISK_LEVEL_MAP: dict[str, str] = {
    "刷单返利": "高风险", "游戏交易": "中风险", "虚假客服": "高风险",
    "冒充老师": "高风险", "虚假招聘": "高风险", "奖助学金": "高风险",
    "AI换脸": "高风险", "求职培训贷": "中风险", "网购退款": "中风险",
    "虚假投资理财": "高风险",
}


def _sample_from_hash(content_hash: str, pool: list[dict]) -> dict:
    """基于哈希从样本池中选取确定性样本。"""
    idx = int(content_hash[:8], 16) % max(len(pool), 1)
    return pool[idx]


def _classify_text(text: str) -> tuple[str, list[str], float]:
    """基于关键词匹配对文本进行分类。

    Returns:
        fraud_type: 诈骗类型（若无匹配则返回"未知"）
        matched_keywords: 匹配到的关键词列表
        confidence: 置信度 0.0-1.0
    """
    matched: dict[str, list[str]] = {}
    for keyword, fraud_type in KEYWORD_TO_FRAUD.items():
        if keyword in text:
            matched.setdefault(fraud_type, []).append(keyword)

    if not matched:
        return "未知", [], 0.0

    # 选择匹配关键词最多的类型
    best_type = max(matched, key=lambda k: len(matched[k]))
    best_keywords = matched[best_type]
    confidence = min(0.3 + len(best_keywords) * 0.15, 0.95)
    return best_type, best_keywords, round(confidence, 2)


def analyze_image(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """分析上传的图片，返回模拟 OCR 结果与风险分析。

    Args:
        file_bytes: 图片文件二进制内容
        filename: 原始文件名

    Returns:
        结构化分析结果字典
    """
    # 1. 基础校验
    if len(file_bytes) > 10 * 1024 * 1024:
        return {
            "success": False,
            "error": "图片大小超过 10MB 限制，请压缩后重新上传。",
            "filename": filename,
        }

    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in {"png", "jpg", "jpeg", "gif", "webp", "bmp"}:
        return {
            "success": False,
            "error": f"不支持的文件格式（.{ext}），请上传 PNG、JPG、GIF、WEBP 格式的图片。",
            "filename": filename,
        }

    # 2. 计算内容哈希，用于确定性采样
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    hash_int = int(content_hash[:16], 16)

    # 3. 从预置样本库选取模拟 OCR 文本
    # 30% 概率选取安全样本（负样本），70% 概率选取诈骗样本
    is_safe = (hash_int % 100) < 30

    if is_safe:
        sample = _sample_from_hash(content_hash, SAFE_SAMPLES)
        extracted_text = sample["text"]
        fraud_type = "正常文本"
        risk_level = "安全"
        matched_keywords: list[str] = []
        confidence = 0.0
    else:
        # 从 10 类诈骗中均匀选取
        fraud_types = list(SAMPLE_POOLS.keys())
        selected_type = fraud_types[hash_int % len(fraud_types)]
        pool = SAMPLE_POOLS[selected_type]
        sample = _sample_from_hash(content_hash, pool)
        extracted_text = sample["text"]

        # 再用关键词匹配做一次分类（可能与哈希选取不同，增加多样性）
        matched_type, matched_keywords, confidence = _classify_text(extracted_text)
        fraud_type = matched_type if matched_type != "未知" else selected_type
        risk_level = RISK_LEVEL_MAP.get(fraud_type, "中风险")

    # 4. 生成建议搜索关键词
    suggested_keywords = []
    if fraud_type != "正常文本" and fraud_type != "未知":
        suggested_keywords = [fraud_type] + matched_keywords[:2]
    else:
        # 从文本中提取可能的关键词（简单启发）
        words = ["兼职", "刷单", "退款", "客服", "转账", "验证码", "链接", "保证金", "培训"]
        suggested_keywords = [w for w in words if w in extracted_text][:3]

    # 5. 生成推荐分类
    suggested_categories = []
    if fraud_type in SAMPLE_POOLS:
        suggested_categories.append(fraud_type)
    # 补充相关分类
    related = {
        "刷单返利": ["刷流水诈骗"],
        "游戏交易": ["二手交易"],
        "虚假客服": ["冒充客服", "百万保障诈骗"],
        "冒充老师": ["冒充熟人", "冒充领导"],
        "虚假招聘": ["求职交费", "培训贷"],
        "奖助学金": ["贷款征信诈骗"],
        "AI换脸": ["冒充熟人", "冒充公检法"],
        "求职培训贷": ["培训贷", "求职交费"],
        "网购退款": ["虚假购物服务", "快递引流诈骗"],
        "虚假投资理财": ["杀猪盘", "虚拟货币诈骗", "虚假投资"],
    }
    if fraud_type in related:
        suggested_categories.extend(related[fraud_type])

    return {
        "success": True,
        "filename": filename,
        "fileSize": len(file_bytes),
        "extractedText": extracted_text,
        "fraudType": fraud_type,
        "riskLevel": risk_level,
        "confidence": confidence,
        "matchedKeywords": matched_keywords,
        "suggestedKeywords": suggested_keywords,
        "suggestedCategories": suggested_categories,
        "isSafe": is_safe,
        "analysisNote": "当前为 Demo 模拟识别，生产环境将接入 OCR + LLM 实现真实图片文字提取与风险分析。",
        "analyzedAt": datetime.utcnow().isoformat(),
    }
