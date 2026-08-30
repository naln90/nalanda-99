"""AI 学习集市主链路。

该模块提供可配置主题的学习产品：
学习目标发布 -> 可编辑任务包 -> 过程记录 -> 成果迭代 -> 集市共享
-> 学习伙伴成长与校园实践活动解锁。

任务包内容按主题画像（THEME_TASK_PROFILES）生成，与所选主题直接相关；
反诈仅是可选主题之一，不作为默认主题。

校园实践活动仅由平台展示解锁资格与团委通知，不承担报名、组织、
签到或志愿时长认定。
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    CampusActivity,
    CampusActivityUnlock,
    LearningArtifact,
    LearningArtifactVersion,
    LearningGoal,
    LearningMarketListing,
    LearningPlan,
    LearningPlanExtension,
    LearningPlanItem,
)
from .storage import save_file, load_file_response  # noqa: E402
from .helpers import get_current_owner  # noqa: E402  # 安全鉴权：写操作以 token 解析出的权威 owner 为准
from .seed import pick_video_for_theme  # noqa: E402  # 微课视频库按主题命中
from .ai_service import is_llm_available, _call_llm  # noqa: E402  # 计划文件解析兜底


ACTIVITY_BOUNDARY_NOTICE = (
    "活动解锁仅代表获得活动认知、成长荣誉或参与资格，不等同于报名或实际参加。"
    "具体活动由学校团委统一组织；学生可按团委规定程序自主报名，也可仅保留解锁记录。"
)


TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "tpl-fraud-campus",
        "title": "14天大学生反诈主题学习包",
        "theme": "大学生校园反诈",
        "difficulty": "进阶",
        "periodDays": 14,
        "dailyMinutes": 20,
        "expectedOutcome": "完成一张大学生兼职诈骗防范海报",
        "summary": "以校园高发诈骗为主题，包含基础必修、兴趣选修、情境训练与成果创作。",
        "tags": ["反诈", "主题学习", "海报创作"],
        "electiveTracks": ["情境挑战", "案例研判", "创意表达"],
        "reuseCount": 126,
        "featured": True,
    },
    {
        "id": "tpl-python-starter",
        "title": "21天Python入门任务包",
        "theme": "Python编程入门",
        "difficulty": "入门",
        "periodDays": 21,
        "dailyMinutes": 35,
        "expectedOutcome": "完成一个可运行的校园信息查询小程序",
        "summary": "从语法基础、函数与数据结构逐步过渡到一个可演示的小项目。",
        "tags": ["Python", "编程", "项目学习"],
        "electiveTracks": ["代码实践", "项目挑战"],
        "reuseCount": 89,
        "featured": False,
    },
    {
        "id": "tpl-calculus-review",
        "title": "高数期末复习冲刺包",
        "theme": "高等数学复习",
        "difficulty": "进阶",
        "periodDays": 10,
        "dailyMinutes": 45,
        "expectedOutcome": "形成一份个人薄弱知识点复习手册",
        "summary": "按知识诊断、专项训练、错题复盘和模拟测验组织复习路径。",
        "tags": ["高数", "考试", "错题复盘"],
        "electiveTracks": ["错题专项", "模拟测验"],
        "reuseCount": 64,
        "featured": False,
    },
    {
        "id": "tpl-innovation-project",
        "title": "大学生创新项目启动包",
        "theme": "大学生创新项目",
        "difficulty": "挑战",
        "periodDays": 30,
        "dailyMinutes": 40,
        "expectedOutcome": "完成项目需求说明、原型与路演材料",
        "summary": "覆盖问题定义、用户调研、方案设计、原型验证和成果路演。",
        "tags": ["大创", "项目学习", "成果路演"],
        "electiveTracks": ["用户调研", "原型设计", "路演表达"],
        "reuseCount": 51,
        "featured": False,
    },
    {
        "id": "tpl-graduation-thesis",
        "title": "毕业设计撰写全流程包",
        "theme": "毕业设计(论文)",
        "difficulty": "挑战",
        "periodDays": 90,
        "dailyMinutes": 35,
        "expectedOutcome": "完成开题报告、中期检查与论文终稿",
        "summary": "覆盖选题、文献综述、方法设计、实验验证、论文撰写与答辩演练全链路。",
        "tags": ["毕业设计", "项目学习", "论文"],
        "electiveTracks": ["文献管理", "实验设计", "答辩演练"],
        "reuseCount": 58,
        "featured": True,
    },
    {
        "id": "tpl-cet46",
        "title": "英语四六级冲刺包",
        "theme": "大学英语四六级",
        "difficulty": "进阶",
        "periodDays": 28,
        "dailyMinutes": 30,
        "expectedOutcome": "完成一套完整四六级模拟卷与个性化提分计划",
        "summary": "词汇、听力、阅读、写作翻译分项突破，配真题精练与弱项追踪。",
        "tags": ["英语", "四六级", "考试"],
        "electiveTracks": ["听力精练", "写作模板", "阅读提速"],
        "reuseCount": 73,
        "featured": True,
    },
    {
        "id": "tpl-postgrad-politics",
        "title": "考研政治备考包",
        "theme": "考研政治",
        "difficulty": "进阶",
        "periodDays": 60,
        "dailyMinutes": 40,
        "expectedOutcome": "形成知识框架笔记与时政热点手册",
        "summary": "马原、毛中特、史纲、思修、当代分模块推进，配真题与框架梳理。",
        "tags": ["考研", "政治", "考试"],
        "electiveTracks": ["框架梳理", "真题精练", "时政追踪"],
        "reuseCount": 45,
        "featured": False,
    },
    {
        "id": "tpl-ds-algo",
        "title": "数据结构与算法训练包",
        "theme": "数据结构与算法",
        "difficulty": "挑战",
        "periodDays": 45,
        "dailyMinutes": 50,
        "expectedOutcome": "完成分类刷题训练与一份算法笔记",
        "summary": "数组、链表、树、图、动态规划循序渐进，配刷题实战与竞赛冲刺。",
        "tags": ["算法", "编程", "考研/竞赛"],
        "electiveTracks": ["刷题实战", "竞赛冲刺"],
        "reuseCount": 67,
        "featured": True,
    },
    {
        "id": "tpl-research-paper",
        "title": "科研论文写作入门包",
        "theme": "科研论文写作",
        "difficulty": "进阶",
        "periodDays": 40,
        "dailyMinutes": 30,
        "expectedOutcome": "产出一篇可投稿的综述或小型论文初稿",
        "summary": "选题、检索、综述、实验、图表规范与投稿流程的系统训练。",
        "tags": ["科研", "论文", "学术写作"],
        "electiveTracks": ["文献检索", "学术英语", "图表规范"],
        "reuseCount": 39,
        "featured": False,
    },
    {
        "id": "tpl-teacher-cert",
        "title": "教师资格证备考包",
        "theme": "教师资格证",
        "difficulty": "入门",
        "periodDays": 35,
        "dailyMinutes": 30,
        "expectedOutcome": "通过科目一科目二模拟并准备好面试试讲稿",
        "summary": "综合素质、教育知识与能力、学科知识与面试试讲的系统备考。",
        "tags": ["教资", "考证", "考试"],
        "electiveTracks": ["面试试讲", "材料分析"],
        "reuseCount": 41,
        "featured": False,
    },
    {
        "id": "tpl-resume-job",
        "title": "简历制作与求职准备包",
        "theme": "求职与职业发展",
        "difficulty": "入门",
        "periodDays": 21,
        "dailyMinutes": 25,
        "expectedOutcome": "完成一版可投递简历与模拟面试记录",
        "summary": "自我盘点、简历撰写、网申、笔试与面试准备全周期训练。",
        "tags": ["求职", "职业能力", "简历"],
        "electiveTracks": ["简历精修", "模拟面试"],
        "reuseCount": 52,
        "featured": False,
    },
    {
        "id": "tpl-ml-intro",
        "title": "机器学习入门包",
        "theme": "机器学习入门",
        "difficulty": "进阶",
        "periodDays": 50,
        "dailyMinutes": 40,
        "expectedOutcome": "完成一个端到端的机器学习小项目",
        "summary": "数学基础、Python 数据处理、经典模型与项目实战循序渐进。",
        "tags": ["机器学习", "AI工具学习", "项目学习"],
        "electiveTracks": ["数据处理", "模型实战"],
        "reuseCount": 48,
        "featured": True,
    },
]


# 需求#7：任务包配置结构化增强 —— 大纲 / 重难点 / 参考资料 / 考核标准。
# 集中维护，模块加载时合并进 TEMPLATES，避免污染模板主结构。
TEMPLATE_ENRICHMENT: dict[str, dict[str, Any]] = {
    "tpl-fraud-campus": {
        "outline": ["基础必修：班会导学 + 高发诈骗基础课 + 能力基线测评", "兴趣选修：情境挑战 / 案例研判 / 创意表达（三选）", "成果创作：反诈海报 / 短视频 / 案例报告"],
        "keyDifficulties": ["把“话术套路”抽象为可识别的风险信号", "在模拟对话中坚持“不转账、不共享屏幕、先核验”", "把知识点转化为受众能5秒看懂的视觉表达"],
        "referenceMaterials": [
            {"title": "校园高发诈骗类型清单", "detail": "刷单返利、冒充客服、游戏交易、AI换脸借钱、培训贷的典型话术与识别要点。"},
            {"title": "96110 与 110 求助流程", "detail": "什么情况立即拨打96110、如何保存聊天与转账证据。"},
            {"title": "反诈宣传合规边界", "detail": "不泄露他人隐私、不传播未经核实的案例。"},
        ],
        "assessmentCriteria": ["能正确识别≥3类高危信号并说明处置", "成果含“风险信号—核验方法—求助渠道”完整结构", "保留V1与修改版并依据AI建议迭代"],
    },
    "tpl-python-starter": {
        "outline": ["语法基础：变量/控制流/函数", "数据结构：列表/字典/集合", "项目实战：校园信息查询小程序"],
        "keyDifficulties": ["从“看懂”到“能写”的跨越", "调试报错信息并定位问题", "把需求拆成可编码的小步骤"],
        "referenceMaterials": [
            {"title": "Python 官方教程（中文）", "detail": "官方入门文档，覆盖语法与标准库。"},
            {"title": "真实项目样例：校园课表查询", "detail": "如何用 requests + 简单解析完成一个可运行脚本。"},
        ],
        "assessmentCriteria": ["独立完成≥3个练习脚本", "小程序可运行并输出正确结果", "代码有基本注释与异常处理"],
    },
    "tpl-calculus-review": {
        "outline": ["知识诊断：定位薄弱章节", "专项训练：极限/微分/积分", "错题复盘 + 模拟测验"],
        "keyDifficulties": ["概念理解而非套公式", "综合题的知识串联", "考试限时下的准确率"],
        "referenceMaterials": [
            {"title": "高等数学（同济）核心例题", "detail": "覆盖极限、导数、积分的经典题型。"},
            {"title": "错题复盘模板", "detail": "记录错因、正确思路与同类变式。"},
        ],
        "assessmentCriteria": ["薄弱章节正确率≥70%", "形成个人复习手册", "模拟测验达到目标分数"],
    },
    "tpl-innovation-project": {
        "outline": ["问题定义与选题", "用户调研与需求", "方案设计与原型", "路演材料"],
        "keyDifficulties": ["把想法收敛为可验证的问题", "调研样本的代表性", "原型可演示、路演有逻辑"],
        "referenceMaterials": [
            {"title": "大创申报书模板", "detail": "研究背景、内容、方法、预期成果的写法。"},
            {"title": "精益画布", "detail": "用一页纸梳理问题与价值主张。"},
        ],
        "assessmentCriteria": ["产出需求说明与原型", "完成路演PPT并演练", "明确下一步验证计划"],
    },
    "tpl-graduation-thesis": {
        "outline": ["选题与文献综述", "方法设计与实验", "论文撰写", "答辩演练"],
        "keyDifficulties": ["文献检索与综述能力", "实验可复现", "学术规范与查重"],
        "referenceMaterials": [
            {"title": "学校毕业论文格式规范", "detail": "章节结构、引用格式、查重要求。"},
            {"title": "文献管理工具入门", "detail": "Zotero / EndNote 的基本用法。"},
        ],
        "assessmentCriteria": ["开题、中期、终稿三阶段材料齐全", "实验数据可追溯", "答辩陈述清晰有条理"],
    },
    "tpl-cet46": {
        "outline": ["词汇积累", "听力精练", "阅读提速", "写作翻译模板"],
        "keyDifficulties": ["听力抓取关键信息", "长难句阅读速度", "写作模板的灵活运用"],
        "referenceMaterials": [
            {"title": "近五年真题", "detail": "按题型分项精练。"},
            {"title": "高频词汇与同义替换表", "detail": "听力阅读共现的核心词。"},
        ],
        "assessmentCriteria": ["完成一套完整模拟卷", "弱项追踪表更新", "形成个性化提分计划"],
    },
    "tpl-postgrad-politics": {
        "outline": ["马原框架", "毛中特脉络", "史纲时间线", "时政热点"],
        "keyDifficulties": ["概念辨析", "知识框架化记忆", "主观题答题结构"],
        "referenceMaterials": [
            {"title": "大纲解析", "detail": "官方知识点与权重。"},
            {"title": "真题主观题范式", "detail": "“原理+材料+结论”答题结构。"},
        ],
        "assessmentCriteria": ["完成分模块框架笔记", "真题正确率达标", "时政手册更新"],
    },
    "tpl-ds-algo": {
        "outline": ["数组/链表/栈队列", "树与图", "动态规划", "刷题实战"],
        "keyDifficulties": ["复杂度分析", "DP状态定义", "边界与极端用例"],
        "referenceMaterials": [
            {"title": "代码随想录", "detail": "按题型系统的刷题路线。"},
            {"title": "LeetCode 热门100", "detail": "高频面试题分类。"},
        ],
        "assessmentCriteria": ["分类刷题≥50道", "形成算法笔记", "能独立讲解思路"],
    },
    "tpl-research-paper": {
        "outline": ["选题与检索", "综述写作", "实验/调研", "投稿规范"],
        "keyDifficulties": ["找到研究空白", "学术英语表达", "图表规范与可重复性"],
        "referenceMaterials": [
            {"title": "Google Scholar 检索技巧", "detail": "关键词、引文追踪、期刊分区。"},
            {"title": "学术写作句型库", "detail": "摘要、方法、讨论的常用表达。"},
        ],
        "assessmentCriteria": ["完成综述或初稿", "图表符合期刊规范", "明确投稿目标"],
    },
    "tpl-teacher-cert": {
        "outline": ["综合素质", "教育知识与能力", "学科知识", "面试试讲"],
        "keyDifficulties": ["材料分析题结构", "试讲互动设计", "结构化问答"],
        "referenceMaterials": [
            {"title": "考试大纲", "detail": "三科考试范围与题型。"},
            {"title": "优秀试讲稿范例", "detail": "导入—新授—小结—作业的结构。"},
        ],
        "assessmentCriteria": ["科目一/二模拟通过", "准备面试试讲稿", "结构化问答演练"],
    },
    "tpl-resume-job": {
        "outline": ["自我盘点", "简历撰写", "网申与笔试", "模拟面试"],
        "keyDifficulties": ["量化成果表达", "匹配岗位JD", "面试表达与反问"],
        "referenceMaterials": [
            {"title": "STAR 法则模板", "detail": "用情境-任务-行动-结果描述经历。"},
            {"title": "常见面试题库", "detail": "行为面与技术面的高频问题。"},
        ],
        "assessmentCriteria": ["完成可投递简历", "记录模拟面试反馈", "明确求职目标清单"],
    },
    "tpl-ml-intro": {
        "outline": ["数学与Python基础", "数据清洗与可视化", "经典模型", "项目实战"],
        "keyDifficulties": ["特征工程直觉", "模型选型与评估", "从 Notebook 到工程"],
        "referenceMaterials": [
            {"title": "吴恩达 Machine Learning", "detail": "经典入门课程，建立整体认知。"},
            {"title": "scikit-learn 用户指南", "detail": "Pipeline、评估指标的最佳实践。"},
        ],
        "assessmentCriteria": ["完成端到端小项目", "模型有评估与对比", "代码可复现"],
    },
}

for _tpl in TEMPLATES:
    _enr = TEMPLATE_ENRICHMENT.get(_tpl["id"])
    if _enr:
        _tpl.update(_enr)

# 反诈模板仅作为 11 个可选主题之一，不置顶、不作默认推荐
for _tpl in TEMPLATES:
    if _tpl["id"] == "tpl-fraud-campus":
        _tpl["featured"] = False
TEMPLATES.sort(key=lambda _tpl: _tpl["id"] == "tpl-fraud-campus")


ACTIVITY_SEEDS: list[dict[str, Any]] = [
    {
        "id": "activity-tree-planting",
        "title": "校园公益植树活动",
        "category": "校园公益",
        "description": "以持续完成主题学习为基础，发现并解锁校园公益实践机会。",
        "interest_direction": "综合参与",
        "targetEnergy": 1000,
        "rule": {"required": 2, "electives": 1, "artifacts": 1},
    },
    {
        "id": "activity-community-fraud",
        "title": "社区主题学习宣讲实践",
        "category": "志愿传播",
        "description": "面向社区居民开展所学主题的知识分享，适合案例研判和表达方向学习者。",
        "interest_direction": "志愿传播",
        "targetEnergy": 1500,
        "rule": {"required": 3, "electives": 2, "artifacts": 1},
    },
    {
        "id": "activity-elderly-digital",
        "title": "银发数字生活指导",
        "category": "数字助老",
        "description": "帮助老年人掌握智能设备与常用线上服务的基本使用与安全习惯。",
        "interest_direction": "数字助老",
        "targetEnergy": 1200,
        "rule": {"required": 2, "electives": 2, "artifacts": 1},
    },
    {
        "id": "activity-fraud-exhibition",
        "title": "校园主题学习成果展",
        "category": "成果展示",
        "description": "展示学生创作的海报、短视频、案例报告等优秀主题学习成果。",
        "interest_direction": "内容创作",
        "targetEnergy": 800,
        "rule": {"required": 2, "electives": 1, "artifacts": 1},
    },
]


class GoalValidationRequest(BaseModel):
    theme: str = Field(min_length=2, max_length=120)
    periodDays: int = Field(default=14, ge=3, le=180)
    dailyMinutes: int = Field(default=20, ge=10, le=240)
    difficulty: str = "进阶"
    expectedOutcome: str = Field(min_length=2, max_length=180)


class GoalCreateRequest(GoalValidationRequest):
    ownerId: str = Field(min_length=1)
    learningType: str = Field(default="自主学习", max_length=40)
    majorDirection: str = Field(default="通识能力", max_length=40)
    electiveTracks: list[str] = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=20)  # 自定义标签（需求#4）


class PlanItemUpdateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    estimatedMinutes: int | None = Field(default=None, ge=5, le=240)
    dueDay: int | None = Field(default=None, ge=1, le=180)
    status: str | None = None
    completionNote: str | None = Field(default=None, max_length=500)


class PlanItemCompleteRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    completionNote: str = Field(default="", max_length=500)


class PlanItemReplaceRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    direction: str = Field(default="AI对练", max_length=40)


class ArtifactCreateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    planId: str = Field(min_length=1)
    title: str = Field(min_length=2, max_length=120)
    artifactType: str = Field(default="海报", max_length=40)
    description: str = Field(default="", max_length=800)
    visibility: str = "private"


class ArtifactVersionRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    fileName: str = Field(default="", max_length=200)
    contentSummary: str = Field(min_length=8, max_length=3000)
    revisionNote: str = Field(default="", max_length=1000)


class ArtifactPublishRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    visibility: str = "public"


class PlanShareRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class MarketReuseRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class PlanExtensionRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    extraDays: int = Field(default=3, ge=1, le=60)
    reason: str = Field(default="", max_length=500)


class CodeDebugRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    planId: str = ""
    language: str = Field(default="python", max_length=30)
    code: str = Field(default="", max_length=8000)
    question: str = Field(min_length=1, max_length=1000)


class ArtifactReviewRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    contentSummary: str = Field(min_length=8, max_length=3000)
    revisionNote: str = Field(default="", max_length=1000)
    fileName: str = Field(default="", max_length=200)


class CompanionRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    planId: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=1000)


def _json_load(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.randbelow(9000) + 1000}"


def _validate_goal(payload: GoalValidationRequest) -> dict[str, Any]:
    suggestions: list[str] = []
    score = 100
    if len(payload.theme.strip()) < 6:
        suggestions.append("建议将主题写得更具体，例如明确学习对象、应用场景或能力方向。")
        score -= 15
    if payload.periodDays <= 5 and payload.dailyMinutes < 30:
        suggestions.append("当前周期较短，可增加每日学习时长或缩小预期成果范围。")
        score -= 12
    if len(payload.expectedOutcome.strip()) < 8:
        suggestions.append("建议把预期成果改为可提交、可展示的具体作品。")
        score -= 15
    if not any(word in payload.expectedOutcome for word in ("完成", "制作", "形成", "通过", "掌握", "产出")):
        suggestions.append("可使用“完成/制作/形成/通过”等动词描述可验收成果。")
        score -= 8
    if not suggestions:
        suggestions.append("目标范围、周期与成果相互匹配，可以直接生成任务包。")
    return {
        "score": max(score, 45),
        "isExecutable": score >= 70,
        "normalizedGoal": (
            f"在{payload.periodDays}天内围绕“{payload.theme.strip()}”开展"
            f"{payload.difficulty}学习，每天投入约{payload.dailyMinutes}分钟，"
            f"最终{payload.expectedOutcome.strip()}。"
        ),
        "suggestions": suggestions,
        "source": "explainable-ai",
    }


def _ensure_activity_seeds(db: Session) -> None:
    for seed in ACTIVITY_SEEDS:
        existing = db.get(CampusActivity, seed["id"])
        if existing is None:
            db.add(
                CampusActivity(
                    id=seed["id"],
                    title=seed["title"],
                    category=seed["category"],
                    description=seed["description"],
                    organizer="学校团委",
                    interest_direction=seed["interest_direction"],
                    notice_url="",
                    unlock_rule_json=json.dumps(seed["rule"], ensure_ascii=False),
                    target_energy=seed["targetEnergy"],
                    current_progress=0,
                    contributor_count=0,
                    status="building",
                )
            )
        else:
            # 向后兼容：旧库 seed 行可能缺少共建字段（迁移加列时为 NULL），在此补齐；
            # 同时同步标题/分类/描述，保证旧库行与当前多主题 seed 文案一致。
            changed = False
            if existing.title != seed["title"]:
                existing.title = seed["title"]
                changed = True
            if existing.category != seed["category"]:
                existing.category = seed["category"]
                changed = True
            if existing.description != seed["description"]:
                existing.description = seed["description"]
                changed = True
            if existing.target_energy is None:
                existing.target_energy = seed.get("targetEnergy", 1000)
                changed = True
            if existing.current_progress is None:
                existing.current_progress = 0
                changed = True
            if existing.contributor_count is None:
                existing.contributor_count = 0
                changed = True
            if existing.status is None:
                existing.status = "building"
                changed = True
            if changed:
                db.add(existing)
    db.commit()


# 主题画像：按主题关键词匹配，生成与所选主题直接相关的任务包内容。
THEME_TASK_PROFILES: list[dict[str, Any]] = [
    {
        "match": ("AI", "人工智能", "智能工具", "提示词", "大模型", "智能素养"),
        "required": [
            ("AI工具能力边界认知", "了解大模型擅长与易错的任务类型，认识幻觉与过时信息现象。", "知识库 · AI素养专题", "完成边界判断练习并记录三个易错场景。"),
            ("提示词工程基础", "学习角色设定、任务拆解与输出约束的提示词写法。", "训练中心 · 提示词练习", "完成三个提示词改写任务并对比输出效果。"),
            ("AI生成内容核验与规范", "掌握信息溯源、交叉验证与学术申报要求。", "知识库 · AI使用规范", "完成一次生成内容核验并记录核验路径。"),
        ],
        "electives": {
            "提示词实践": ("提示词工坊实战", "围绕学习与创作场景迭代提示词，对比输出质量。", "训练中心 · 提示词练习", "沉淀三条个人提示词模板。"),
            "案例研判": ("AI误用案例研判", "复盘AI代写、虚假信息传播等典型误用事件。", "案例库 · AI伦理专题", "完成案例标注与改进建议。"),
            "AI对练": ("AI工具问答对练", "与学习伙伴多轮问答，练习任务拆解与追问技巧。", "学习伙伴 · 学习陪伴", "完成一次对练并总结三条使用经验。"),
            "创意表达": ("AI辅助创作表达", "用AI工具辅助完成主题成果初稿并做人工优化。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("网络安全", "信息安全", "网络攻防", "数字安全"),
        "required": [
            ("账号与密码安全自查", "排查弱口令、重复密码与多设备登录，掌握双因素认证设置。", "知识库 · 账号安全专题", "完成账号安全自查清单并开启至少一处双因素认证。"),
            ("钓鱼邮件与虚假热点识别", "学习钓鱼邮件特征、虚假Wi-Fi与证书告警的识别方法。", "训练中心 · 情景训练", "在模拟样本中识别全部钓鱼线索。"),
            ("网络安全基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "情境挑战": ("钓鱼攻击情境识别挑战", "在模拟邮件与消息中找出仿冒域名、紧急诱导与异常附件信号。", "训练中心 · AI情境模拟", "识别至少3个风险信号并说明正确处置方式。"),
            "案例研判": ("数据泄露事件案例研判", "复盘典型数据泄露事件，梳理攻击链路与防护盲区。", "案例库 · 数据泄露专题", "完成事件时间线标注并写出防护建议。"),
            "AI对练": ("安全习惯问答对练", "与学习伙伴多轮问答，巩固密码管理与安全上网习惯。", "学习伙伴 · 学习陪伴", "完成一次对练并形成三条个人安全原则。"),
            "创意表达": ("网络安全宣传素材整理", "围绕目标受众筛选案例、视觉重点和行动提示。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("心理", "情绪", "压力", "睡眠"),
        "required": [
            ("压力与情绪自我识别", "学习常见压力源与情绪信号，完成自我状态初评。", "知识库 · 心理健康专题", "完成情绪自查并记录三项个人信号。"),
            ("校园心理支持资源地图", "了解校内外心理咨询、朋辈支持与求助热线渠道。", "知识库 · 支持资源专题", "整理一份个人求助渠道清单。"),
            ("作息与睡眠基础管理", "掌握睡眠卫生要点与作息调节方法。", "训练中心 · 情景训练", "制定一周作息优化计划。"),
        ],
        "electives": {
            "情绪日记": ("七天情绪日记实践", "每天记录情绪触发点、身体反应与应对方式。", "训练中心 · 自助练习", "完成七天记录并总结个人情绪规律。"),
            "正念练习": ("正念与放松训练入门", "跟随引导完成呼吸与身体扫描练习。", "训练中心 · 自助练习", "完成三次练习并记录体验变化。"),
            "案例研判": ("心理困境案例研判", "分析大学生常见心理困境案例，练习识别求助信号。", "案例库 · 心理专题", "完成案例标注并写出支持路径。"),
            "创意表达": ("心理健康主题表达练习", "把心理健康知识转化为适合同学传播的内容。", "知识库 · 创作素材", "形成一版标题、核心文案和内容结构。"),
        },
    },
    {
        "match": ("消防", "火灾", "用电安全"),
        "required": [
            ("宿舍火灾隐患排查", "排查违规电器、私拉电线与堵塞通道等常见隐患。", "知识库 · 消防安全专题", "完成宿舍隐患自查清单。"),
            ("灭火器与逃生要领实训", "学习灭火器使用步骤、低姿逃生与防护要领。", "训练中心 · 情景训练", "通过模拟演练测验。"),
            ("消防基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "隐患随手拍": ("校园火灾隐患随手拍", "记录并上报校园公共区域的消防隐患。", "知识库 · 隐患上报", "提交至少三处隐患记录与改进建议。"),
            "案例研判": ("校园火灾案例研判", "复盘典型校园火灾事件，梳理起火原因与处置得失。", "案例库 · 消防专题", "完成时间线标注与改进建议。"),
            "创意表达": ("消防安全创意表达", "把消防知识转化为宿舍场景的提示内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("交通", "骑行", "出行安全"),
        "required": [
            ("通勤路线风险自查", "梳理日常通勤路线中的路口、照明与盲区风险。", "知识库 · 交通安全专题", "绘制个人通勤风险地图。"),
            ("骑行与电动车安全规范", "掌握头盔佩戴、限速、载人充电等规范要点。", "训练中心 · 情景训练", "完成规范测验并记录三项改进。"),
            ("交通安全基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "情境挑战": ("出行安全情境识别挑战", "在模拟场景中识别网约车核验、夜间出行与路口风险。", "训练中心 · AI情境模拟", "识别至少3个风险信号并说明处置方式。"),
            "案例研判": ("交通事故案例研判", "复盘典型校园交通事故，梳理成因与预防要点。", "案例库 · 交通专题", "完成时间线标注与预防建议。"),
            "创意表达": ("交通安全创意表达", "把出行安全知识转化为校园传播内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("求职", "就业", "招聘", "实习", "职场"),
        "required": [
            ("招聘信息真伪核验", "掌握企业资质查询、岗位信息交叉验证与黑名单检索。", "知识库 · 求职安全专题", "完成三份招聘信息核验练习。"),
            ("简历与个人信息保护", "学习简历投放中的隐私边界与必要信息取舍。", "知识库 · 隐私保护专题", "完成简历隐私自查。"),
            ("求职权益与法规基础", "了解三方协议、试用期与劳动合同基本权益。", "知识库 · 劳动权益专题", "完成权益知识测验。"),
        ],
        "electives": {
            "模拟面试": ("AI模拟面试对练", "围绕目标岗位进行多轮问答，练习表达与追问应对。", "训练中心 · 模拟面试", "完成一次模拟面试并复盘表现。"),
            "案例研判": ("求职陷阱案例研判", "复盘培训贷、押金骗局与虚假外包等典型陷阱。", "案例库 · 求职专题", "完成陷阱标注与避坑清单。"),
            "创意表达": ("个人求职作品集整理", "把学习成果整理为可展示的个人作品集。", "知识库 · 创作素材", "形成作品集提纲与三份样例说明。"),
        },
    },
    {
        "match": ("金融", "理财", "投资", "财商", "消费"),
        "required": [
            ("个人预算与记账入门", "建立月度收支记录与预算分配方法。", "知识库 · 金融素养专题", "完成一个月度预算表。"),
            ("校园贷与高息陷阱识别", "识别砍头息、套路贷与过度借贷营销话术。", "知识库 · 借贷风险专题", "完成陷阱识别测验。"),
            ("理财基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "记账实践": ("21天记账挑战", "坚持记录每日收支并每周复盘消费结构。", "训练中心 · 自助练习", "完成21天记录并输出一份消费分析。"),
            "案例研判": ("金融纠纷案例研判", "复盘校园金融纠纷事件，梳理风险点与维权路径。", "案例库 · 金融专题", "完成案例标注与改进建议。"),
            "创意表达": ("金融知识科普表达", "把理财常识转化为适合同学阅读的科普内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("学术", "诚信", "论文", "引用", "查重"),
        "required": [
            ("引用规范与查重规则", "掌握直接引用、转述与参考文献格式要求。", "知识库 · 学术规范专题", "完成引用格式改写练习。"),
            ("AI工具使用的学术边界", "明确AI辅助写作、数据与图像使用的申报要求。", "知识库 · AI使用规范", "形成个人AI使用守则三条。"),
            ("学术诚信基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "写作练习": ("论文段落改写练习", "练习把资料转述为规范表达并正确标注出处。", "训练中心 · 自助练习", "完成三个段落改写并互查引用。"),
            "案例研判": ("学术不端案例研判", "复盘典型学术不端事件，辨析边界与后果。", "案例库 · 学术诚信专题", "完成案例分析笔记。"),
            "创意表达": ("学术规范科普表达", "把学术规范要点转化为新生友好的指南内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("个人信息", "隐私", "数据保护"),
        "required": [
            ("个人信息盘点与自查", "梳理自己留下的账号、授权与公开信息。", "知识库 · 隐私保护专题", "完成个人信息盘点清单。"),
            ("App权限与隐私条款解读", "学会查看权限申请与隐私条款关键内容。", "训练中心 · 情景训练", "完成三款常用App权限审查。"),
            ("个人信息保护基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "权限清理实践": ("账号权限清理行动", "注销闲置账号、回收多余授权并更新密码。", "训练中心 · 自助练习", "完成清理记录并截图留档。"),
            "案例研判": ("信息泄露案例研判", "复盘信息泄露事件，梳理暴露途径与补救措施。", "案例库 · 隐私专题", "完成事件标注与防护建议。"),
            "创意表达": ("隐私保护创意表达", "把个人信息保护要点转化为校园传播内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("校园安全", "治安", "防盗", "宿舍安全"),
        "required": [
            ("校园高发安全事件概览", "了解盗窃、纠纷与突发事件的常见场景与预防。", "知识库 · 校园安全专题", "完成概览学习笔记。"),
            ("宿舍防盗与物品管理", "掌握贵重物品存放与出入锁门习惯。", "知识库 · 宿舍安全专题", "完成宿舍安全自查。"),
            ("校园安全基础测评", "从辨识力、判断力、应变力、实证力和协作力五个维度形成初始画像。", "训练中心 · 五维能力测评", "完成测评并查看个人薄弱方向。"),
        ],
        "electives": {
            "情境挑战": ("突发事件响应情境挑战", "在模拟场景中练习识别、求助与疏散决策。", "训练中心 · AI情境模拟", "识别关键信号并给出正确处置顺序。"),
            "案例研判": ("校园安全案例研判", "复盘盗窃、冲突等事件，梳理预防与处置要点。", "案例库 · 校园安全专题", "完成案例标注与改进建议。"),
            "创意表达": ("校园安全创意表达", "把安全要点转化为宿舍与班级场景的提示内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
    {
        "match": ("应急", "避险", "地震", "台风", "急救", "防灾"),
        "required": [
            ("预警信号解读", "掌握暴雨、台风、雷电等预警等级与响应动作。", "知识库 · 气象应急专题", "完成预警信号配对测验。"),
            ("地震与火灾避险要领", "学习室内避震、疏散路线与集合点规则。", "训练中心 · 情景训练", "通过避险流程测验。"),
            ("急救基础与AED使用", "了解心肺复苏步骤与AED位置查询方法。", "知识库 · 急救基础专题", "完成急救流程学习笔记。"),
        ],
        "electives": {
            "应急演练复盘": ("疏散演练复盘实践", "参与或观摩演练并复盘流程与个人表现。", "训练中心 · 情景训练", "完成复盘记录与两项改进。"),
            "案例研判": ("灾害应对案例研判", "复盘典型灾害事件，梳理预警传递与处置链路。", "案例库 · 应急专题", "完成时间线标注与改进建议。"),
            "创意表达": ("应急科普创意表达", "把避险要点转化为易懂的科普内容。", "知识库 · 创作素材", "形成成果提纲、核心文案和素材清单。"),
        },
    },
]


def _match_theme_profile(theme: str) -> dict[str, Any] | None:
    for profile in THEME_TASK_PROFILES:
        if any(word in theme for word in profile["match"]):
            return profile
    return None


def _profile_items(goal: LearningGoal, profile: dict[str, Any]) -> list[dict[str, Any]]:
    selected = _json_load(goal.elective_tracks_json, [])
    if not selected:
        selected = list(profile["electives"].keys())[:3]
    items: list[dict[str, Any]] = [
        {
            "category": "required",
            "title": title,
            "description": description,
            "resource": resource,
            "criteria": criteria,
            "minutes": 20 + index * 5,
            "day": index + 1,
        }
        for index, (title, description, resource, criteria) in enumerate(profile["required"])
    ]
    for index, track in enumerate(selected[:3]):
        title, description, resource, criteria = profile["electives"].get(
            track,
            (
                f"{track}：{goal.theme}",
                f"围绕{goal.theme}的{track}方向开展一次专项学习。",
                "学习资源库 · 兴趣专题",
                "完成学习并提交一段个人复盘。",
            ),
        )
        items.append(
            {
                "category": "elective",
                "title": title,
                "description": description,
                "resource": resource,
                "criteria": criteria,
                "minutes": min(max(goal.daily_minutes, 15), 45),
                "day": min(goal.period_days - 2, 5 + index * 2),
            }
        )
    items.append(
        {
            "category": "outcome",
            "title": goal.expected_outcome,
            "description": "将前期学习内容转化为可提交、可迭代、可公开展示的学习成果。",
            "resource": "成果工坊 · AI初审",
            "criteria": "至少提交两个版本，依据AI建议完成一次修改后发布。",
            "minutes": max(goal.daily_minutes * 2, 40),
            "day": goal.period_days,
        }
    )
    return items


def _generic_items(goal: LearningGoal) -> list[dict[str, Any]]:
    selected = _json_load(goal.elective_tracks_json, []) or ["知识梳理", "实操练习", "成果表达"]
    items = [
        {
            "category": "required",
            "title": f"{goal.theme}学习地图",
            "description": "梳理核心概念、先后依赖关系和阶段目标。",
            "resource": "AI生成知识大纲",
            "criteria": "确认知识地图并标注个人已有基础。",
            "minutes": goal.daily_minutes,
            "day": 1,
        },
        {
            "category": "required",
            "title": f"{goal.theme}基础能力诊断",
            "description": "通过基础问题或样例任务识别当前薄弱点。",
            "resource": "主题诊断材料",
            "criteria": "完成诊断并确认至少一个强化方向。",
            "minutes": goal.daily_minutes,
            "day": 2,
        },
    ]
    for index, track in enumerate(selected[:3]):
        items.append(
            {
                "category": "elective",
                "title": f"{track}：{goal.theme}",
                "description": f"根据个人兴趣选择“{track}”方向开展专项学习。",
                "resource": "AI推荐资源清单",
                "criteria": "完成一次专项实践并记录关键收获。",
                "minutes": goal.daily_minutes,
                "day": min(goal.period_days - 1, 4 + index * 2),
            }
        )
    items.append(
        {
            "category": "outcome",
            "title": goal.expected_outcome,
            "description": "提交最终学习成果，并依据AI初审建议完成至少一次迭代。",
            "resource": "成果工坊",
            "criteria": "成果完整、贴合学习目标并保留版本记录。",
            "minutes": max(goal.daily_minutes * 2, 40),
            "day": goal.period_days,
        }
    )
    return items


def _create_plan(
    db: Session,
    goal: LearningGoal,
    item_specs: list[dict[str, Any]] | None = None,
) -> LearningPlan:
    previous = db.scalars(
        select(LearningPlan).where(
            LearningPlan.owner_id == goal.owner_id,
            LearningPlan.status == "active",
        )
    ).all()
    for plan in previous:
        plan.status = "paused"

    plan = LearningPlan(
        id=_new_id("lplan"),
        goal_id=goal.id,
        owner_id=goal.owner_id,
        title=f"{goal.theme} · {goal.period_days}天个性化任务包",
        summary=(
            f"每天约{goal.daily_minutes}分钟，以基础必修保证学习底线，"
            f"以兴趣选修形成个性路径，最终{goal.expected_outcome}。"
        ),
        source="explainable-ai",
    )
    db.add(plan)
    db.flush()

    if item_specs is None:
        profile = _match_theme_profile(goal.theme)
        item_specs = _profile_items(goal, profile) if profile else _generic_items(goal)
    # 按主题命中一个微课视频（CC0 资源）；命中不到则留空，前端降级为模拟播放器
    video = pick_video_for_theme(db, goal.theme)
    for index, spec in enumerate(item_specs):
        db.add(
            LearningPlanItem(
                id=_new_id(f"litem{index + 1}"),
                plan_id=plan.id,
                owner_id=goal.owner_id,
                category=spec["category"],
                title=spec["title"],
                description=spec["description"],
                resource_hint=spec["resource"],
                acceptance_criteria=spec["criteria"],
                estimated_minutes=spec["minutes"],
                due_day=max(1, spec["day"]),
                order_index=index,
                video_url=video.url if video else None,
                video_thumbnail=video.thumbnail if video else None,
            )
        )
    db.flush()
    return plan


def _serialize_goal(goal: LearningGoal) -> dict[str, Any]:
    return {
        "id": goal.id,
        "ownerId": goal.owner_id,
        "theme": goal.theme,
        "learningType": goal.learning_type,
        "periodDays": goal.period_days,
        "dailyMinutes": goal.daily_minutes,
        "difficulty": goal.difficulty,
        "expectedOutcome": goal.expected_outcome,
        "majorDirection": goal.major_direction,
        "electiveTracks": _json_load(goal.elective_tracks_json, []),
        "tags": _json_load(goal.tags_json, []),
        "validation": _json_load(goal.validation_json, {}),
        "status": goal.status,
        "createdAt": goal.created_at.isoformat(),
    }


def _serialize_item(item: LearningPlanItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "planId": item.plan_id,
        "category": item.category,
        "title": item.title,
        "description": item.description,
        "resourceHint": item.resource_hint,
        "acceptanceCriteria": item.acceptance_criteria,
        "estimatedMinutes": item.estimated_minutes,
        "dueDay": item.due_day,
        "orderIndex": item.order_index,
        "status": item.status,
        "completionNote": item.completion_note,
        "completedAt": item.completed_at.isoformat() if item.completed_at else None,
        "videoUrl": item.video_url,
        "videoThumbnail": item.video_thumbnail,
    }


def _serialize_plan(db: Session, plan: LearningPlan) -> dict[str, Any]:
    items = db.scalars(
        select(LearningPlanItem)
        .where(LearningPlanItem.plan_id == plan.id)
        .order_by(LearningPlanItem.order_index)
    ).all()
    completed = sum(item.status == "completed" for item in items)
    progress = round(completed / len(items) * 100) if items else 0
    return {
        "id": plan.id,
        "goalId": plan.goal_id,
        "ownerId": plan.owner_id,
        "title": plan.title,
        "summary": plan.summary,
        "source": plan.source,
        "status": plan.status,
        "shieldEnergy": plan.shield_energy,
        "guardianValue": plan.guardian_value,
        "extensionDays": plan.extension_days,
        "progress": progress,
        "completedCount": completed,
        "totalCount": len(items),
        "items": [_serialize_item(item) for item in items],
        "createdAt": plan.created_at.isoformat(),
    }


def _serialize_artifact(db: Session, artifact: LearningArtifact) -> dict[str, Any]:
    versions = db.scalars(
        select(LearningArtifactVersion)
        .where(LearningArtifactVersion.artifact_id == artifact.id)
        .order_by(LearningArtifactVersion.version_no)
    ).all()
    return {
        "id": artifact.id,
        "planId": artifact.plan_id,
        "ownerId": artifact.owner_id,
        "title": artifact.title,
        "artifactType": artifact.artifact_type,
        "description": artifact.description,
        "visibility": artifact.visibility,
        "status": artifact.status,
        "latestVersion": artifact.latest_version,
        "aiReview": _json_load(artifact.ai_review_json, {}),
        "versions": [
            {
                "id": version.id,
                "versionNo": version.version_no,
                "fileName": version.file_name,
                "contentSummary": version.content_summary,
                "revisionNote": version.revision_note,
                "aiReview": _json_load(version.ai_review_json, {}),
                "createdAt": version.created_at.isoformat(),
            }
            for version in versions
        ],
        "createdAt": artifact.created_at.isoformat(),
        "attachments": _json_load(artifact.attachments_json, []),
        "updatedAt": artifact.updated_at.isoformat(),
    }


def _llm_artifact_review(summary: str, revision_note: str) -> dict[str, Any] | None:
    """可选真实 LLM 初审（需求#21）。

    当环境变量 OPENAI_API_KEY 配置时，调用 OpenAI 兼容接口对成果做初审；
    未配置或调用失败一律返回 None，由下方规则引擎降级，保证可用性。
    """
    import json as _json
    import os
    import urllib.request

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "你是一名大学生学习成果初审助手。请基于成果内容说明，给出客观、可执行的初审意见。"
        "只返回 JSON，格式：{\"score\":0-100,\"level\":\"可发布|建议修改\","
        "\"strengths\":[字符串],\"issues\":[字符串],\"suggestions\":[字符串]}。"
        "不要输出 JSON 以外的任何内容。"
        f"成果说明：{summary}\n修改说明：{revision_note}"
    )
    body = _json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        result = _json.loads(content)
        if not isinstance(result, dict) or "score" not in result:
            return None
        result["score"] = max(0, min(100, int(result.get("score", 0))))
        result["source"] = f"AI成果初审（LLM：{model}）"
        result["reviewedAt"] = datetime.utcnow().isoformat()
        return result
    except Exception:
        return None


def _artifact_review(payload: ArtifactVersionRequest, version_no: int) -> dict[str, Any]:
    summary = payload.contentSummary.strip()
    # 优先尝试真实 LLM 初审；未配置密钥或调用失败则降级到可解释规则引擎。
    llm = _llm_artifact_review(summary, payload.revisionNote)
    if llm:
        return llm
    score = 56
    strengths: list[str] = []
    issues: list[str] = []
    suggestions: list[str] = []
    if len(summary) >= 80:
        score += 18
        strengths.append("成果说明较完整，能够看出目标受众和核心内容。")
    else:
        issues.append("成果说明偏短，暂时难以判断内容结构是否完整。")
        suggestions.append("补充目标受众、核心内容要点，以及希望受众获得的收获或行动。")
    # 受众 / 目标明确性（主题中立，不绑定任何垂直领域）
    if any(word in summary for word in ("受众", "面向", "对象", "帮助", "提升", "学会", "掌握", "理解", "意识")):
        score += 8
        strengths.append("明确了目标受众或学习收获，主题导向清晰。")
    else:
        issues.append("目标受众或预期收获不够明确。")
        suggestions.append("说明这份成果面向谁、希望对方获得什么能力或认知。")
    # 可执行性 / 方法性（主题中立）
    if any(word in summary for word in ("步骤", "方法", "技巧", "如何", "建议", "行动", "练习", "案例", "示例")):
        score += 8
        strengths.append("包含可操作的方法或示例，便于他人借鉴。")
    else:
        issues.append("缺少可执行的方法或示例。")
        suggestions.append("补充一两个具体做法、案例或练习建议，增强实用性。")
    if payload.fileName:
        score += 6
        strengths.append("已形成可归档的成果文件。")
    if version_no >= 2 or payload.revisionNote.strip():
        score += 8
        strengths.append("保留了修改过程，能够体现成果迭代。")
    if not suggestions:
        suggestions.append("可继续优化标题层级和视觉重点，使关键信息在5秒内被识别。")
    return {
        "score": min(score, 96),
        "level": "可发布" if score >= 80 else "建议修改",
        "strengths": strengths,
        "issues": issues,
        "suggestions": suggestions,
        "reviewedAt": datetime.utcnow().isoformat(),
        "source": "AI成果初审（规则降级可用）",
    }


def _code_debug_analysis(language: str, code: str, question: str) -> dict[str, Any]:
    """代码调试答疑（需求#16）：规则化静态分析 + 安全提示，给出思路而非代写。"""
    issues: list[str] = []
    hints: list[str] = []
    safety: list[str] = []
    low = code.lower()

    if any(word in low for word in ("password", "secret", "api_key", "token", "ak=", "sk-")):
        safety.append("代码中出现了密钥/口令类字符串，请勿硬编码真实凭证，改用环境变量或配置中心统一管理。")
    if "eval(" in code or "exec(" in code:
        safety.append("使用了 eval / exec，存在代码注入风险，尽量避免对不可信输入直接执行。")
    if "http://" in code:
        safety.append("存在明文 http 链接，建议改用 https，避免中间人劫持与数据泄露。")

    lang = (language or "python").lower()
    if lang in ("python", "py"):
        if "import " not in code and ("def " in code or "print(" in code):
            hints.append("确认已导入所需模块（如 os、requests），缺失 import 会触发 NameError。")
        if "except:" in code or "except Exception:" in code:
            issues.append("使用了宽泛 except，会吞掉错误导致难以定位问题；建议捕获具体异常并打印日志。")
        if "= =" in code or " == =" in code or "= =" in code.replace("==", "=="):
            # 粗略检测赋值/比较混淆
            if "= =" in code:
                issues.append("注意区分赋值 = 与比较 ==，混用会在 Python 中直接报错。")
        if "print(" in code and "return" in code:
            hints.append("调试阶段可用 print 观察中间变量，但交付前建议改为 logging 或断言。")
        if "input(" in code:
            hints.append("脚本中的 input() 在自动化/Web 场景会阻塞，考虑改为函数参数传入。")
    elif lang in ("javascript", "js", "ts", "typescript"):
        if " == " in code and "===" not in code:
            hints.append("建议使用严格相等 === 代替 ==，避免隐式类型转换带来的坑。")
        if "var " in code:
            hints.append("优先使用 let / const 替代 var，避免变量提升与作用域问题。")
        if "console.log" in code and "return" in code:
            hints.append("调试用的 console.log 可在交付前清理或改为结构化日志。")
    elif lang in ("sql",):
        if "select *" in low:
            hints.append("避免 SELECT *，显式列出字段更易维护且减少不必要数据传输。")
        if "execute(" in code and "%" in code and "parameter" not in low:
            safety.append("SQL 拼接存在注入风险，请使用参数化查询（占位符 / 预编译语句）。")

    if code.strip() and not any(
        token in code for token in ("def ", "function", "class ", "=>", "import ", "#", "//", "select")
    ):
        issues.append("代码缺少结构（函数/类/注释），先拆成更小的函数会更易调试与测试。")

    hints.append("先复述“预期行为”和“实际上报的错误”，再把问题缩小到最小可复现片段，效率最高。")
    return {
        "language": lang,
        "detectedIssues": issues,
        "hints": hints,
        "safetyNotes": safety,
        "nextStep": "我不会替你直接改好代码；请先用以上检查点定位问题，再告诉我卡在哪一步。",
        "source": "代码调试答疑（规则降级可用）",
    }


def _activity_counts(db: Session, owner_id: str, plan_id: str) -> dict[str, int]:
    required_total = db.scalar(
        select(func.count(LearningPlanItem.id)).where(
            LearningPlanItem.plan_id == plan_id,
            LearningPlanItem.category == "required",
        )
    ) or 0
    required_completed = db.scalar(
        select(func.count(LearningPlanItem.id)).where(
            LearningPlanItem.plan_id == plan_id,
            LearningPlanItem.category == "required",
            LearningPlanItem.status == "completed",
        )
    ) or 0
    elective_completed = db.scalar(
        select(func.count(LearningPlanItem.id)).where(
            LearningPlanItem.plan_id == plan_id,
            LearningPlanItem.category == "elective",
            LearningPlanItem.status == "completed",
        )
    ) or 0
    artifact_count = db.scalar(
        select(func.count(LearningArtifact.id)).where(
            LearningArtifact.owner_id == owner_id,
            LearningArtifact.plan_id == plan_id,
            LearningArtifact.status == "published",
        )
    ) or 0
    return {
        "requiredTotal": int(required_total),
        "requiredCompleted": int(required_completed),
        "electiveCompleted": int(elective_completed),
        "artifactCount": int(artifact_count),
    }


def _evaluate_unlocks(db: Session, owner_id: str, plan_id: str) -> None:
    _ensure_activity_seeds(db)
    counts = _activity_counts(db, owner_id, plan_id)
    activities = db.scalars(
        select(CampusActivity).where(CampusActivity.enabled.is_(True))
    ).all()
    # 一次性取出该用户在该计划下的所有已解锁活动，避免逐活动查询（N+1 → 1 次）
    existing_rows = db.scalars(
        select(CampusActivityUnlock).where(
            CampusActivityUnlock.owner_id == owner_id,
            CampusActivityUnlock.plan_id == plan_id,
        )
    ).all()
    unlocked_ids = {row.activity_id for row in existing_rows}
    for activity in activities:
        rule = _json_load(activity.unlock_rule_json, {})
        meets = (
            counts["requiredCompleted"] >= int(rule.get("required", 0))
            and counts["electiveCompleted"] >= int(rule.get("electives", 0))
            and counts["artifactCount"] >= int(rule.get("artifacts", 0))
        )
        if meets and activity.id not in unlocked_ids:
            db.add(
                CampusActivityUnlock(
                    owner_id=owner_id,
                    activity_id=activity.id,
                    plan_id=plan_id,
                    unlock_reason_json=json.dumps(counts, ensure_ascii=False),
                )
            )
    db.commit()


def _serialize_activity(
    db: Session,
    activity: CampusActivity,
    owner_id: str,
    plan_id: str,
) -> dict[str, Any]:
    counts = _activity_counts(db, owner_id, plan_id)
    rule = _json_load(activity.unlock_rule_json, {})
    unlock = db.scalar(
        select(CampusActivityUnlock).where(
            CampusActivityUnlock.owner_id == owner_id,
            CampusActivityUnlock.activity_id == activity.id,
            CampusActivityUnlock.plan_id == plan_id,
        )
    )
    requirements = [
        {
            "label": f"完成基础必修 {rule.get('required', 0)} 项",
            "current": counts["requiredCompleted"],
            "target": int(rule.get("required", 0)),
            "completed": counts["requiredCompleted"] >= int(rule.get("required", 0)),
        },
        {
            "label": f"完成兴趣选修 {rule.get('electives', 0)} 项",
            "current": counts["electiveCompleted"],
            "target": int(rule.get("electives", 0)),
            "completed": counts["electiveCompleted"] >= int(rule.get("electives", 0)),
        },
        {
            "label": f"发布学习成果 {rule.get('artifacts', 0)} 项",
            "current": counts["artifactCount"],
            "target": int(rule.get("artifacts", 0)),
            "completed": counts["artifactCount"] >= int(rule.get("artifacts", 0)),
        },
    ]
    ratios = [
        min(req["current"] / req["target"], 1) if req["target"] else 1 for req in requirements
    ]
    return {
        "id": activity.id,
        "title": activity.title,
        "category": activity.category,
        "description": activity.description,
        "organizer": activity.organizer,
        "interestDirection": activity.interest_direction,
        "noticeUrl": activity.notice_url,
        "status": "unlocked" if unlock else "locked",
        "progress": round(sum(ratios) / len(ratios) * 100),
        "requirements": requirements,
        "unlockedAt": unlock.unlocked_at.isoformat() if unlock else None,
        "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
    }


def _serialize_activity_locked(activity: CampusActivity) -> dict[str, Any]:
    """无 active 计划时的活动序列化：状态强制为 locked 且进度归零。"""
    rule = _json_load(activity.unlock_rule_json, {})
    requirements = [
        {
            "label": f"完成基础必修 {rule.get('required', 0)} 项",
            "current": 0,
            "target": int(rule.get("required", 0)),
            "completed": False,
        },
        {
            "label": f"完成兴趣选修 {rule.get('electives', 0)} 项",
            "current": 0,
            "target": int(rule.get("electives", 0)),
            "completed": False,
        },
        {
            "label": f"发布学习成果 {rule.get('artifacts', 0)} 项",
            "current": 0,
            "target": int(rule.get("artifacts", 0)),
            "completed": False,
        },
    ]
    return {
        "id": activity.id,
        "title": activity.title,
        "category": activity.category,
        "description": activity.description,
        "organizer": activity.organizer,
        "interestDirection": activity.interest_direction,
        "noticeUrl": activity.notice_url,
        "status": "locked",
        "progress": 0,
        "requirements": requirements,
        "unlockedAt": None,
        "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
    }


def create_learning_market_router(get_db: Callable[..., Any]) -> APIRouter:
    router = APIRouter(prefix="/api/learning", tags=["AI学习集市"])

    @router.get("/templates")
    def get_templates() -> dict[str, Any]:
        return {"templates": TEMPLATES, "total": len(TEMPLATES)}

    @router.post("/goals/validate")
    def validate_goal(payload: GoalValidationRequest) -> dict[str, Any]:
        return _validate_goal(payload)

    @router.post("/goals")
    def create_goal(
        payload: GoalCreateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        validation = _validate_goal(payload)
        goal = LearningGoal(
            id=_new_id("goal"),
            owner_id=payload.ownerId,
            theme=payload.theme.strip(),
            learning_type=payload.learningType,
            period_days=payload.periodDays,
            daily_minutes=payload.dailyMinutes,
            difficulty=payload.difficulty,
            expected_outcome=payload.expectedOutcome.strip(),
            major_direction=payload.majorDirection,
            elective_tracks_json=json.dumps(payload.electiveTracks, ensure_ascii=False),
            tags_json=json.dumps(payload.tags, ensure_ascii=False),
            validation_json=json.dumps(validation, ensure_ascii=False),
        )
        db.add(goal)
        db.flush()
        plan = _create_plan(db, goal)
        db.commit()
        return {
            "goal": _serialize_goal(goal),
            "plan": _serialize_plan(db, plan),
            "message": "目标已校验，并生成可编辑的个性化任务包。",
        }

    # ===================== 计划文件导入（混合方案） =====================
    # 用户上传自己的计划文件（txt/md/docx 等），系统按以下优先级生成任务包：
    #   1) 文本结构化解析成功 → 直接用用户条目（user-file）
    #   2) 解析不出但大模型可用 → LLM 解析（user-file-llm）
    #   3) 都不可用 → 回退主题模板（theme-template），用户仍可手动调整
    def _is_plan_line(content: str) -> bool:
        # 行具备「列表标记 / 分隔符 / 含天数或分钟」任一特征才视为计划条目，
        # 避免把大段散文误当成任务项。
        if re.match(r"^[(\（]?\d+[)\）.、]", content):
            return True
        if re.match(r"^[\-\•\*\u2022]", content):
            return True
        if re.search(r"[:：\-—–｜|]", content):
            return True
        if re.search(r"\d+\s*天", content) or re.search(r"\d+\s*分钟", content):
            return True
        return False

    def _extract_plan_items_from_text(text: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for raw in [ln.strip() for ln in text.splitlines() if ln.strip()]:
            if len(raw) < 3:
                continue
            # 剥掉列表标记
            content = re.sub(r"^[(\（]?\d+[)\）.、]?\s*[-—–]?\s*", "", raw)
            content = re.sub(r"^[\-\•\*\u2022]\s*", "", content).strip()
            if not content or not _is_plan_line(content):
                continue
            # 类别识别 + 标题提取
            category = "required"
            # 行首即为类别关键词并接分隔符时，取其后内容作为标题（避免标题退化成关键词）
            lead = re.match(
                r"^(产出|成果|作品|展示|汇报|答辩|提交|终稿|选修|拓展|兴趣|自主|任选|自由)\s*[:：\-—–]\s*(.+)$",
                content,
            )
            if lead:
                kw = lead.group(1)
                rest = lead.group(2).strip()
                category = "outcome" if kw in ("产出", "成果", "作品", "展示", "汇报", "答辩", "提交", "终稿") else "elective"
                title = rest
                description = rest
            else:
                if re.search(r"(产出|成果|作品|展示|汇报|答辩|提交|终稿)", content):
                    category = "outcome"
                elif re.search(r"(选修|拓展|兴趣|自主|任选|自由)", content):
                    category = "elective"
                # 标题与说明拆分
                parts = re.split(r"[:：\-—–｜|]", content, maxsplit=1)
                title = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else title
            # 清理标题里残留的类别关键词（如「阅读PEP8（选修）」）
            title = re.sub(r"[（(](选修|拓展|兴趣|自主|任选|自由|产出|成果)[）)]", "", title).strip()
            if not title:
                title = description or "学习任务"
            # 天数 / 分钟
            day_match = re.search(r"第\s*(\d+)\s*天|(\d+)\s*天", content)
            day = int(day_match.group(1) or day_match.group(2)) if day_match else 1
            min_match = re.search(r"(\d+)\s*分钟", content)
            minutes = int(min_match.group(1)) if min_match else (40 if category == "outcome" else 30)
            if not description:
                description = title
            items.append(
                {
                    "category": category,
                    "title": title[:120],
                    "description": description[:500],
                    "resource": "根据您提交的计划文件生成",
                    "criteria": f"按计划在{'第' + str(day) + '天' if day_match else '周期内'}完成「{title}」",
                    "minutes": minutes,
                    "day": day,
                }
            )
        return items if len(items) >= 1 else []

    LLM_PLAN_SYSTEM = (
        "你是学习计划结构化助手。用户会提交一份自由文本的学习计划，"
        "请将其解析为 JSON 数组。每个元素包含："
        "category（required/elective/outcome 三选一）、title（简短任务名）、"
        "description（一句说明）、estimatedMinutes（整数分钟）、dueDay（整数，第几天完成）。"
        "只输出 JSON 数组本身，不要任何解释或 Markdown 代码块。"
    )

    async def _parse_plan_with_llm(text: str, theme: str) -> list[dict[str, Any]] | None:
        if not is_llm_available():
            return None
        try:
            resp = await _call_llm(
                LLM_PLAN_SYSTEM,
                f"主题：{theme}\n计划内容：\n{text[:4000]}",
                temperature=0.3,
                max_tokens=1500,
            )
            if not resp or not resp.get("content"):
                return None
            content = resp["content"]
            start = content.find("[")
            end = content.rfind("]")
            if start == -1 or end == -1 or end <= start:
                return None
            arr = json.loads(content[start : end + 1])
            items: list[dict[str, Any]] = []
            for el in arr:
                if not isinstance(el, dict):
                    continue
                cat = el.get("category", "required")
                if cat not in ("required", "elective", "outcome"):
                    cat = "required"
                title = str(el.get("title", "")).strip()
                if not title:
                    continue
                items.append(
                    {
                        "category": cat,
                        "title": title[:120],
                        "description": str(el.get("description", title))[:500],
                        "resource": "根据您提交的计划文件（AI解析）生成",
                        "criteria": f"完成「{title}」",
                        "minutes": max(5, min(240, int(el.get("estimatedMinutes", 30) or 30))),
                        "day": max(1, min(180, int(el.get("dueDay", 1) or 1))),
                    }
                )
            return items if items else None
        except Exception:  # noqa: BLE001
            return None

    @router.post("/goals/from-file")
    async def create_goal_from_file(
        ownerId: str = Form(...),
        theme: str = Form(...),
        expectedOutcome: str = Form(default=""),
        periodDays: int = Form(default=14),
        dailyMinutes: int = Form(default=20),
        difficulty: str = Form(default="进阶"),
        majorDirection: str = Form(default="通识能力"),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = (ownerId or "").strip()
        theme_val = (theme or "").strip()
        if not owner_id or not theme_val:
            raise HTTPException(status_code=400, detail="缺少 ownerId 或 theme")
        # 读取并尽力解码（中文环境兼容 gbk）
        raw = await file.read()
        text: str | None = None
        for enc in ("utf-8", "gbk", "latin-1"):
            try:
                text = raw.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if text is None:
            text = raw.decode("utf-8", errors="replace")
        # 原始文件留档
        goal_id = _new_id("goal")
        try:
            save_file(f"plan_files/{goal_id}/{file.filename or 'plan.txt'}", raw)
        except Exception:  # noqa: BLE001
            pass
        # 决定任务项来源（混合方案）
        plan_source = "user-file"
        item_specs = _extract_plan_items_from_text(text)
        if not item_specs:
            llm_items = await _parse_plan_with_llm(text, theme_val)
            if llm_items:
                item_specs = llm_items
                plan_source = "user-file-llm"
        if not item_specs:
            plan_source = "theme-template"

        expected = expectedOutcome.strip() or f"完成「{theme_val}」个人学习计划"
        goal = LearningGoal(
            id=goal_id,
            owner_id=owner_id,
            theme=theme_val,
            learning_type="自主学习",
            period_days=periodDays,
            daily_minutes=dailyMinutes,
            difficulty=difficulty,
            expected_outcome=expected,
            major_direction=majorDirection,
            elective_tracks_json="[]",
            tags_json=json.dumps(["计划文件导入"], ensure_ascii=False),
            validation_json=json.dumps({"source": plan_source, "fromFile": True}, ensure_ascii=False),
        )
        db.add(goal)
        db.flush()
        plan = _create_plan(db, goal, item_specs=item_specs if item_specs else None)
        db.commit()
        return {
            "goal": _serialize_goal(goal),
            "plan": _serialize_plan(db, plan),
            "planSource": plan_source,
            "parsedItemCount": len(item_specs) if item_specs else 0,
            "message": (
                "已根据您上传的计划文件生成任务包。"
                if plan_source != "theme-template"
                else "未能从文件中解析出具体计划，已按所选主题生成默认任务包，您可在工作台手动调整。"
            ),
        }

    @router.get("/dashboard")
    def learning_dashboard(
        ownerId: str = Query(min_length=1),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.scalar(
            select(LearningPlan)
            .where(LearningPlan.owner_id == ownerId, LearningPlan.status == "active")
            .order_by(LearningPlan.created_at.desc())
        )
        if not plan:
            return {
                "goal": None,
                "plan": None,
                "artifacts": [],
                "activities": [],
                "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
            }
        goal = db.get(LearningGoal, plan.goal_id)
        artifacts = db.scalars(
            select(LearningArtifact)
            .where(LearningArtifact.owner_id == ownerId, LearningArtifact.plan_id == plan.id)
            .order_by(LearningArtifact.updated_at.desc())
        ).all()
        _evaluate_unlocks(db, ownerId, plan.id)
        activities = db.scalars(
            select(CampusActivity)
            .where(CampusActivity.enabled.is_(True))
            .order_by(CampusActivity.created_at)
        ).all()
        return {
            "goal": _serialize_goal(goal) if goal else None,
            "plan": _serialize_plan(db, plan),
            "artifacts": [_serialize_artifact(db, artifact) for artifact in artifacts],
            "activities": [
                _serialize_activity(db, activity, ownerId, plan.id) for activity in activities
            ],
            "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
        }

    @router.patch("/plan-items/{item_id}")
    def update_plan_item(
        item_id: str,
        payload: PlanItemUpdateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        item = db.get(LearningPlanItem, item_id)
        if not item or item.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务不存在")
        values = payload.model_dump(exclude_none=True, by_alias=False)
        field_map = {
            "title": "title",
            "description": "description",
            "estimatedMinutes": "estimated_minutes",
            "dueDay": "due_day",
            "status": "status",
            "completionNote": "completion_note",
        }
        for key, target in field_map.items():
            if key in values:
                setattr(item, target, values[key])
        db.commit()
        return {"item": _serialize_item(item)}

    @router.post("/plan-items/{item_id}/complete")
    def complete_plan_item(
        item_id: str,
        payload: PlanItemCompleteRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        item = db.get(LearningPlanItem, item_id)
        if not item or item.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务不存在")
        plan = db.get(LearningPlan, item.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="任务包不存在")
        awarded = 0
        if item.status != "completed":
            item.status = "completed"
            item.completed_at = datetime.utcnow()
            item.completion_note = payload.completionNote
            awarded = 18 if item.category == "elective" else 12
            plan.shield_energy += awarded
            plan.guardian_value += awarded
        db.commit()
        _evaluate_unlocks(db, payload.ownerId, plan.id)
        return {
            "awarded": awarded,
            "message": f"完成有效学习，盾能 +{awarded}" if awarded else "该任务已经完成",
            "plan": _serialize_plan(db, plan),
        }

    @router.post("/plan-items/{item_id}/replace")
    def replace_plan_item(
        item_id: str,
        payload: PlanItemReplaceRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        item = db.get(LearningPlanItem, item_id)
        if not item or item.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务不存在")
        if item.category != "elective":
            raise HTTPException(status_code=400, detail="基础必修和成果任务不可直接替换")
        plan = db.get(LearningPlan, item.plan_id)
        goal = db.get(LearningGoal, plan.goal_id) if plan else None
        theme = (goal.theme if goal else "") or "所学主题"
        replacements = {
            "AI对练": (
                f"{theme}问答对练",
                "通过多轮问答巩固知识点、方法要点与行动原则。",
                "完成一次对练并整理三条个人心得。",
            ),
            "案例研判": (
                f"{theme}案例研判",
                "拆解典型案例，标注关键节点和正确处置方式。",
                "完成关键节点标注与处置复盘。",
            ),
            "创意表达": (
                f"{theme}创意表达练习",
                f"把{theme}的知识要点转化为适合大学生传播的文案与视觉表达。",
                "形成一版标题、核心文案和内容结构。",
            ),
            "情境挑战": (
                f"{theme}情境识别挑战",
                "在模拟情境中识别关键信号并作出合理决策。",
                "识别至少3个信号并作出决策说明。",
            ),
        }
        title, description, criteria = replacements.get(
            payload.direction,
            (
                f"{payload.direction}兴趣探索",
                f"围绕{payload.direction}开展一次自主主题学习。",
                "完成学习并提交个人复盘。",
            ),
        )
        item.title = title
        item.description = description
        item.acceptance_criteria = criteria
        item.resource_hint = "AI重新推荐 · 兴趣选修"
        item.status = "not_started"
        item.completed_at = None
        db.commit()
        return {"item": _serialize_item(item), "message": "已只替换当前选修任务。"}

    @router.post("/companion")
    def companion(
        payload: CompanionRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.get(LearningPlan, payload.planId)
        if not plan or plan.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务包不存在")
        items = db.scalars(
            select(LearningPlanItem)
            .where(
                LearningPlanItem.plan_id == plan.id,
                LearningPlanItem.status != "completed",
            )
            .order_by(LearningPlanItem.order_index)
        ).all()
        next_item = items[0] if items else None
        message = payload.message.strip()
        if any(word in message for word in ("今天", "安排", "先做", "下一步")) and next_item:
            reply = (
                f"今天建议先完成“{next_item.title}”，预计{next_item.estimated_minutes}分钟。"
                f"完成标准是：{next_item.acceptance_criteria}。我可以继续帮你拆成三个小步骤。"
            )
        elif any(word in message for word in ("不会", "困难", "看不懂", "答错")):
            reply = (
                "先不要急着找标准答案。请先写出你已理解的部分、卡住的具体环节和你的初步思路，"
                "我再根据你的判断补充遗漏点。"
            )
        elif any(word in message for word in ("海报", "成果", "作品")):
            reply = (
                "建议先明确受众与核心信息，再按“要点—方法—行动”组织内容。"
                "成果工坊会保留V1、V2版本，并给出贴合度和完整性建议。"
            )
        else:
            reply = (
                f"我已结合“{plan.title}”回答。你可以继续问我当前任务的知识点、"
                "完成标准或成果修改思路；我会提供方法引导，不直接代做最终成果。"
            )
        return {
            "reply": reply,
            "source": "小盾灵学习陪伴（规则降级可用）",
            "nextTask": _serialize_item(next_item) if next_item else None,
        }

    @router.post("/artifacts")
    def create_artifact(
        payload: ArtifactCreateRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = get_current_owner(request, db, payload.ownerId or None)
        plan = db.get(LearningPlan, payload.planId)
        if not plan or plan.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="任务包不存在")
        artifact = LearningArtifact(
            id=_new_id("artifact"),
            plan_id=payload.planId,
            owner_id=owner_id,
            title=payload.title,
            artifact_type=payload.artifactType,
            description=payload.description,
            visibility=payload.visibility,
        )
        db.add(artifact)
        db.commit()
        return {"artifact": _serialize_artifact(db, artifact)}

    @router.post("/artifacts/{artifact_id}/versions")
    def add_artifact_version(
        artifact_id: str,
        payload: ArtifactVersionRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = get_current_owner(request, db, payload.ownerId or None)
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="成果不存在")
        version_no = artifact.latest_version + 1
        review = _artifact_review(payload, version_no)
        version = LearningArtifactVersion(
            artifact_id=artifact.id,
            version_no=version_no,
            file_name=payload.fileName,
            content_summary=payload.contentSummary,
            revision_note=payload.revisionNote,
            ai_review_json=json.dumps(review, ensure_ascii=False),
        )
        db.add(version)
        artifact.latest_version = version_no
        artifact.ai_review_json = json.dumps(review, ensure_ascii=False)
        artifact.updated_at = datetime.utcnow()
        db.commit()
        return {
            "artifact": _serialize_artifact(db, artifact),
            "review": review,
            "message": f"V{version_no} 已归档并完成AI初审。",
        }

    @router.post("/artifacts/{artifact_id}/upload")
    async def upload_artifact_file(
        artifact_id: str,
        ownerId: str = Query(default=""),
        request: Request = None,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = get_current_owner(request, db, ownerId or None)
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="成果不存在")
        suffix = Path(file.filename or "").suffix.lower()
        allowed = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".mp4", ".zip"}
        if suffix not in allowed:
            raise HTTPException(status_code=400, detail="暂不支持该文件格式")
        content = await file.read(25 * 1024 * 1024 + 1)
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="成果文件不能超过25MB")
        storage_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}{suffix}"
        storage_key = f"{artifact_id}/{storage_name}"
        # 统一走存储后端（默认本地磁盘，可切换 S3），保证文件真实持久化。
        save_file(storage_key, content)
        # 持久化附件清单，便于前端回显与下载。
        try:
            attachments = json.loads(artifact.attachments_json or "[]")
        except (ValueError, TypeError):
            attachments = []
        if not isinstance(attachments, list):
            attachments = []
        attachments.append(
            {"fileName": file.filename or storage_name, "storageKey": storage_key, "size": len(content)}
        )
        artifact.attachments_json = json.dumps(attachments, ensure_ascii=False)
        db.commit()
        return {
            "fileName": file.filename or storage_name,
            "storageKey": storage_key,
            "size": len(content),
            "message": "成果文件已安全保存。",
        }

    @router.get("/artifacts/{artifact_id}/file/{storage_name}")
    def get_artifact_file(
        artifact_id: str,
        storage_name: str,
        viewerId: str = Query(default=""),
        db: Session = Depends(get_db),
    ) -> Any:
        """回读/下载已上传的成果文件（需求#19/#20 真实可取回）。

        隐私校验：作者本人始终可下载；他人仅当成果为 public 可见、或 friends 且确为好友时允许。
        """
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="成果不存在")
        if artifact.owner_id != (viewerId or ""):
            if artifact.visibility == "public":
                pass
            elif artifact.visibility == "friends" and viewerId and are_friends(db, artifact.owner_id, viewerId):
                pass
            else:
                raise HTTPException(status_code=403, detail="无权访问该文件（隐私设置不允许）")
        storage_key = f"{artifact_id}/{storage_name}"
        resp = load_file_response(storage_key)
        if resp is None:
            raise HTTPException(status_code=404, detail="文件不存在")
        return resp

    @router.post("/artifacts/{artifact_id}/publish")
    def publish_artifact(
        artifact_id: str,
        payload: ArtifactPublishRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = get_current_owner(request, db, payload.ownerId or None)
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="成果不存在")
        if artifact.latest_version < 1:
            raise HTTPException(status_code=400, detail="请先提交至少一个成果版本")
        first_publish = artifact.status != "published"
        artifact.status = "published"
        artifact.visibility = payload.visibility
        artifact.updated_at = datetime.utcnow()
        listing = db.scalar(
            select(LearningMarketListing).where(
                LearningMarketListing.resource_type == "artifact",
                LearningMarketListing.resource_id == artifact.id,
            )
        )
        goal = None
        plan = db.get(LearningPlan, artifact.plan_id)
        if plan:
            goal = db.get(LearningGoal, plan.goal_id)
        if payload.visibility == "public" and not listing:
            listing = LearningMarketListing(
                id=_new_id("listing"),
                owner_id=owner_id,
                resource_type="artifact",
                resource_id=artifact.id,
                title=artifact.title,
                theme=goal.theme if goal else "主题学习",
                summary=artifact.description or "学生主题学习成果",
                tags_json=json.dumps([artifact.artifact_type, "学习成果"], ensure_ascii=False),
            )
            db.add(listing)
        if first_publish and plan:
            plan.shield_energy += 30
            plan.guardian_value += 30
            outcome_item = db.scalar(
                select(LearningPlanItem).where(
                    LearningPlanItem.plan_id == plan.id,
                    LearningPlanItem.category == "outcome",
                )
            )
            if outcome_item and outcome_item.status != "completed":
                outcome_item.status = "completed"
                outcome_item.completed_at = datetime.utcnow()
                outcome_item.completion_note = f"成果《{artifact.title}》已发布"
        db.commit()
        _evaluate_unlocks(db, owner_id, artifact.plan_id)
        return {
            "artifact": _serialize_artifact(db, artifact),
            "message": "成果已发布至学习集市。" if payload.visibility == "public" else "成果已归档至个人档案。",
        }

    @router.post("/plans/{plan_id}/share")
    def share_plan(
        plan_id: str,
        payload: PlanShareRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.get(LearningPlan, plan_id)
        if not plan or plan.owner_id != payload.ownerId:
            raise HTTPException(status_code=404, detail="任务包不存在")
        goal = db.get(LearningGoal, plan.goal_id)
        listing = db.scalar(
            select(LearningMarketListing).where(
                LearningMarketListing.resource_type == "plan",
                LearningMarketListing.resource_id == plan.id,
            )
        )
        if not listing:
            listing = LearningMarketListing(
                id=_new_id("listing"),
                owner_id=payload.ownerId,
                resource_type="plan",
                resource_id=plan.id,
                title=plan.title,
                theme=goal.theme if goal else "自主学习",
                summary=plan.summary,
                tags_json=json.dumps(
                    [goal.difficulty, goal.learning_type, "可复用任务包"] if goal else ["可复用任务包"],
                    ensure_ascii=False,
                ),
            )
            db.add(listing)
            db.commit()
        return {"listingId": listing.id, "message": "任务包已公开，可供其他学生复用和二次修改。"}

    @router.get("/market")
    def get_market(
        resourceType: str = Query(default="all"),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        rows = db.scalars(
            select(LearningMarketListing)
            .where(LearningMarketListing.status == "published")
            .order_by(LearningMarketListing.created_at.desc())
        ).all()
        listings = [
            {
                "id": row.id,
                "ownerId": row.owner_id,
                "resourceType": row.resource_type,
                "resourceId": row.resource_id,
                "title": row.title,
                "theme": row.theme,
                "summary": row.summary,
                "tags": _json_load(row.tags_json, []),
                "likes": row.likes,
                "favorites": row.favorites,
                "ratingAvg": row.rating_avg,
                "ratingCount": row.rating_count,
                "reuseCount": row.reuse_count,
                "createdAt": row.created_at.isoformat(),
            }
            for row in rows
            if resourceType == "all" or row.resource_type == resourceType
        ]
        templates = TEMPLATES if resourceType in ("all", "plan") else []
        return {"templates": templates, "listings": listings}

    @router.post("/market/{resource_id}/reuse")
    def reuse_market_resource(
        resource_id: str,
        payload: MarketReuseRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        template = next((item for item in TEMPLATES if item["id"] == resource_id), None)
        if template:
            create_payload = GoalCreateRequest(
                ownerId=payload.ownerId,
                theme=template["theme"],
                periodDays=template["periodDays"],
                dailyMinutes=template["dailyMinutes"],
                difficulty=template["difficulty"],
                expectedOutcome=template["expectedOutcome"],
                learningType="自主学习",
                majorDirection="通识能力",
                electiveTracks=template["electiveTracks"],
            )
            validation = _validate_goal(create_payload)
            goal = LearningGoal(
                id=_new_id("goal"),
                owner_id=payload.ownerId,
                theme=create_payload.theme,
                learning_type=create_payload.learningType,
                period_days=create_payload.periodDays,
                daily_minutes=create_payload.dailyMinutes,
                difficulty=create_payload.difficulty,
                expected_outcome=create_payload.expectedOutcome,
                major_direction=create_payload.majorDirection,
                elective_tracks_json=json.dumps(create_payload.electiveTracks, ensure_ascii=False),
                validation_json=json.dumps(validation, ensure_ascii=False),
            )
            db.add(goal)
            db.flush()
            plan = _create_plan(db, goal)
            db.commit()
            return {
                "goal": _serialize_goal(goal),
                "plan": _serialize_plan(db, plan),
                "message": "模板已复用为你的任务包，可继续修改。",
            }

        listing = db.get(LearningMarketListing, resource_id)
        if not listing or listing.resource_type != "plan":
            raise HTTPException(status_code=404, detail="可复用任务包不存在")
        source_plan = db.get(LearningPlan, listing.resource_id)
        if not source_plan:
            raise HTTPException(status_code=404, detail="源任务包不存在")
        source_goal = db.get(LearningGoal, source_plan.goal_id)
        if not source_goal:
            raise HTTPException(status_code=404, detail="源学习目标不存在")
        goal = LearningGoal(
            id=_new_id("goal"),
            owner_id=payload.ownerId,
            theme=source_goal.theme,
            learning_type=source_goal.learning_type,
            period_days=source_goal.period_days,
            daily_minutes=source_goal.daily_minutes,
            difficulty=source_goal.difficulty,
            expected_outcome=source_goal.expected_outcome,
            major_direction=source_goal.major_direction,
            elective_tracks_json=source_goal.elective_tracks_json,
            validation_json=source_goal.validation_json,
        )
        db.add(goal)
        db.flush()
        plan = _create_plan(db, goal)
        listing.reuse_count += 1
        db.commit()
        return {
            "goal": _serialize_goal(goal),
            "plan": _serialize_plan(db, plan),
            "message": "已复制该任务包，修改不会影响原作者版本。",
        }

    @router.get("/activities")
    def get_activities(
        ownerId: str = Query(min_length=1),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        plan = db.scalar(
            select(LearningPlan)
            .where(LearningPlan.owner_id == ownerId, LearningPlan.status == "active")
            .order_by(LearningPlan.created_at.desc())
        )
        if not plan:
            return {"activities": [], "plan": None, "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE}
        _evaluate_unlocks(db, ownerId, plan.id)
        activities = db.scalars(
            select(CampusActivity)
            .where(CampusActivity.enabled.is_(True))
            .order_by(CampusActivity.created_at)
        ).all()
        return {
            "activities": [
                _serialize_activity(db, activity, ownerId, plan.id) for activity in activities
            ],
            "plan": {
                "id": plan.id,
                "shieldEnergy": plan.shield_energy,
                "guardianValue": plan.guardian_value,
            },
            "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
        }

    @router.get("/activities/{activity_id}")
    def get_activity(
        activity_id: str,
        ownerId: str = Query(min_length=1),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        activity = db.get(CampusActivity, activity_id)
        if not activity or not activity.enabled:
            raise HTTPException(status_code=404, detail="活动不存在或已下架")
        plan = db.scalar(
            select(LearningPlan)
            .where(LearningPlan.owner_id == ownerId, LearningPlan.status == "active")
            .order_by(LearningPlan.created_at.desc())
        )
        if not plan:
            return {
                "activity": _serialize_activity_locked(activity),
                "plan": None,
                "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
            }
        _evaluate_unlocks(db, ownerId, plan.id)
        return {
            "activity": _serialize_activity(db, activity, ownerId, plan.id),
            "plan": {
                "id": plan.id,
                "shieldEnergy": plan.shield_energy,
                "guardianValue": plan.guardian_value,
            },
            "boundaryNotice": ACTIVITY_BOUNDARY_NOTICE,
        }

    @router.post("/plans/{plan_id}/extend")
    def extend_plan(
        plan_id: str,
        payload: PlanExtensionRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = get_current_owner(request, db, payload.ownerId or None)
        plan = db.get(LearningPlan, plan_id)
        if not plan or plan.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="任务包不存在")
        extension = LearningPlanExtension(
            plan_id=plan_id,
            owner_id=owner_id,
            extra_days=payload.extraDays,
            reason=payload.reason,
            status="approved",  # 演示态自动通过；正式环境可改为辅导员审批
        )
        db.add(extension)
        plan.extension_days += payload.extraDays
        db.commit()
        extensions = db.scalars(
            select(LearningPlanExtension)
            .where(LearningPlanExtension.plan_id == plan_id)
            .order_by(LearningPlanExtension.created_at)
        ).all()
        return {
            "plan": _serialize_plan(db, plan),
            "extensions": [
                {
                    "id": ext.id,
                    "extraDays": ext.extra_days,
                    "reason": ext.reason,
                    "status": ext.status,
                    "createdAt": ext.created_at.isoformat(),
                }
                for ext in extensions
            ],
            "message": f"已批准延期 {payload.extraDays} 天（演示态自动通过）。",
        }

    @router.post("/code-debug")
    def code_debug(
        payload: CodeDebugRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _code_debug_analysis(payload.language, payload.code, payload.question)

    @router.post("/artifacts/{artifact_id}/review")
    def review_artifact(
        artifact_id: str,
        payload: ArtifactReviewRequest,
        request: Request,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        owner_id = get_current_owner(request, db, payload.ownerId or None)
        artifact = db.get(LearningArtifact, artifact_id)
        if not artifact or artifact.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="成果不存在")
        review = _artifact_review(
            ArtifactVersionRequest(
                ownerId=owner_id,
                fileName=payload.fileName,
                contentSummary=payload.contentSummary,
                revisionNote=payload.revisionNote,
            ),
            0,
        )
        return {
            "review": review,
            "message": "AI初审完成，可据此修改后再提交正式版本。",
        }

    return router
