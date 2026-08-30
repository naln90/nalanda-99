from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(String, nullable=False, default="")
    # V3.0 双端口：student=学生端 / school=校方发布端
    role: Mapped[str] = mapped_column(String, nullable=False, default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    has_completed_assessment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_pet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # V3.0 双端口：student=学生端 / school=校方发布端
    role: Mapped[str] = mapped_column(String, nullable=False, default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    # 登录令牌（演示态：demo-login 也会签发并持久化；普通业务接口在携带合法 Bearer Token 时
    # 以 Token 绑定的 owner_id 为准，否则回退 payload.ownerId，保证演示链路不受影响）
    token: Mapped[str | None] = mapped_column(String, nullable=True, default=None, index=True)


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pet_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.owner_id"), nullable=False, index=True)
    pet_type: Mapped[str] = mapped_column(String, nullable=False)
    pet_category: Mapped[str] = mapped_column(String, nullable=False)
    # 用户自定义昵称与头像 emoji（可空：空时回退到 pet_type / 默认头像）
    pet_name: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    avatar_emoji: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stage: Mapped[str] = mapped_column(String, nullable=False, default="幼崽期")
    growth_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_training_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PetPool(Base):
    __tablename__ = "pet_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pet_type: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    pet_category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GrowthRule(Base):
    __tablename__ = "growth_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    rule_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class TrainingTask(Base):
    __tablename__ = "training_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    fraud_type: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    base_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    max_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TrainingQuestion(Base):
    __tablename__ = "training_questions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("training_tasks.id"), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer_json: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class TrainingRecord(Base):
    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pet_id: Mapped[str] = mapped_column(String, nullable=False)
    task_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    base_points: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_bonus: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_bonus: Mapped[int] = mapped_column(Integer, nullable=False)
    final_growth: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_status: Mapped[str] = mapped_column(String, nullable=False)
    reward_message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class SuspiciousCheck(Base):
    __tablename__ = "suspicious_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    input_text_masked: Mapped[str] = mapped_column(Text, nullable=False)
    fraud_type: Mapped[str] = mapped_column(String, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, nullable=False)
    suggestions_json: Mapped[str] = mapped_column(Text, nullable=False)
    growth_awarded: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class FraudCase(Base):
    __tablename__ = "fraud_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    fraud_type: Mapped[str] = mapped_column(String, nullable=False)
    source_channel: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    desensitized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_tags_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    typical_phrase: Mapped[str] = mapped_column(Text, nullable=False)
    recognition_points: Mapped[str] = mapped_column(Text, nullable=False)
    suggestions: Mapped[str] = mapped_column(Text, nullable=False)
    related_task_id: Mapped[str | None] = mapped_column(String, nullable=True)


# ==================== 整改新增模型 ====================


class AssessmentResult(Base):
    """测评结果 — 存储五维能力画像、错题列表"""

    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)  # "quick" | "standard"
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    # 五维能力画像 JSON: {"识诈力": 80, "判断力": 60, ...}
    ability_profile_json: Mapped[str] = mapped_column(Text, nullable=False)
    # 错题 ID 列表 JSON
    wrong_questions_json: Mapped[str] = mapped_column(Text, nullable=False)
    # 薄弱维度列表 JSON
    weak_dimensions_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class TaskPackage(Base):
    """AI 任务包 — 7天/14天训练计划"""

    __tablename__ = "task_packages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String, nullable=False)  # "7day" | "14day"
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")  # "active" | "completed" | "abandoned"
    # 生成时的五维画像快照
    ability_profile_json: Mapped[str] = mapped_column(Text, nullable=False)
    # AI 生成还是规则生成
    generated_by: Mapped[str] = mapped_column(String, nullable=False, default="rule")
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TaskPackageItem(Base):
    """任务包条目 — 每天的具体任务"""

    __tablename__ = "task_package_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    package_id: Mapped[str] = mapped_column(String, ForeignKey("task_packages.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 第几天 (1-14)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    # "assessment_review" | "scenario_training" | "risk_check" | "knowledge_read" | "retrain"
    task_ref: Mapped[str] = mapped_column(String, nullable=False)  # 对应的 task_id / knowledge_id
    task_title: Mapped[str] = mapped_column(String, nullable=False)
    target_ability: Mapped[str] = mapped_column(String, nullable=False)  # 目标能力维度
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    # "pending" | "in_progress" | "completed" | "skipped"
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)


# ==================== AI 学习集市 ====================
#
# 新版学习集市与原有反诈训练表并行存在。原有 TaskPackage 继续服务于旧版
# 7/14 日反诈训练；下面的表负责“目标—任务包—成果—集市—活动解锁”
# 的通用学习闭环，避免破坏已有演示数据。


class LearningGoal(Base):
    """学生自主发布的学习目标。"""

    __tablename__ = "learning_goals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String, nullable=False)
    learning_type: Mapped[str] = mapped_column(String, nullable=False, default="自主学习")
    period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    difficulty: Mapped[str] = mapped_column(String, nullable=False, default="进阶")
    expected_outcome: Mapped[str] = mapped_column(String, nullable=False)
    major_direction: Mapped[str] = mapped_column(String, nullable=False, default="通识能力")
    elective_tracks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    validation_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class LearningPlan(Base):
    """由学习目标生成、可编辑的通用学习任务包。"""

    __tablename__ = "learning_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    goal_id: Mapped[str] = mapped_column(String, ForeignKey("learning_goals.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="explainable-ai")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    shield_energy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    guardian_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class LearningPlanItem(Base):
    """任务包条目：基础必修、兴趣选修或成果任务。"""

    __tablename__ = "learning_plan_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("learning_plans.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # required | elective | outcome
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resource_hint: Mapped[str] = mapped_column(Text, nullable=False, default="")
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # V3.0 完成该任务可获得的盾能（见方案§9.2）
    energy_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="not_started")
    completion_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LearningArtifact(Base):
    """学习成果主记录。"""

    __tablename__ = "learning_artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("learning_plans.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    visibility: Mapped[str] = mapped_column(String, nullable=False, default="private")
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    latest_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_review_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class LearningArtifactVersion(Base):
    """成果迭代版本，保留每次修改与 AI 初审记录。"""

    __tablename__ = "learning_artifact_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(
        String, ForeignKey("learning_artifacts.id"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    content_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    revision_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_review_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LearningMarketListing(Base):
    """学习集市中的任务包或成果条目。"""

    __tablename__ = "learning_market_listings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)  # plan | artifact
    resource_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    theme: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    favorites: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reuse_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CampusActivity(Base):
    """由学校团委落地的校园实践活动。

    V3.0 改为「全体注册用户共同投放盾能、达到目标盾能后共同解锁」模式：
    系统只负责展示、共同解锁与官方通知连接，不承担报名、组织、签到或实践执行。
    状态流：draft -> building(共建中) -> unlocked(已共同解锁) -> notice_released(通知已发布) -> archived。
    """

    __tablename__ = "campus_activities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    organizer: Mapped[str] = mapped_column(String, nullable=False, default="学校团委")
    interest_direction: Mapped[str] = mapped_column(String, nullable=False, default="综合参与")
    notice_url: Mapped[str] = mapped_column(String, nullable=False, default="")
    unlock_rule_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # V3.0 集体共建字段
    target_energy: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)  # 目标盾能
    current_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 当前共建进度
    contributor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 参与投放人数
    status: Mapped[str] = mapped_column(String, nullable=False, default="building")
    # draft | building | unlocked | notice_released | archived
    notice_text: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 团委通知文案
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CampusActivityUnlock(Base):
    """学生完成学习条件后获得的活动解锁纪念。"""

    __tablename__ = "campus_activity_unlocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    activity_id: Mapped[str] = mapped_column(
        String, ForeignKey("campus_activities.id"), nullable=False, index=True
    )
    plan_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    unlock_reason_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ==================== V3.0 双端口 & 统一盾能体系 ====================
#
# V3.0 核心变更：
# 1. 校方发布端创建「月度反诈主题 Theme」，AI 生成任务包后由校方确认发布。
# 2. 统一盾能体系只使用一种成长资源「盾能」，同时记录三口径：
#    累计获得 / 当前可用 / 累计投放（见 EnergyLedger，作为唯一账本）。
# 3. 校园活动改为「全体注册用户共同投放盾能、达到目标后共同解锁」模式。


class Theme(Base):
    """校方发布的月度反诈主题。

    状态流：draft -> ai_generating -> pending_confirm -> published -> ended -> archived
    """

    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    target_audience: Mapped[str] = mapped_column(String, nullable=False, default="在校大学生")
    scope: Mapped[str] = mapped_column(String, nullable=False, default="全校")
    base_required: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 基础必修要求
    elective_direction: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 选修方向
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 预期成果
    base_assessment: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 基础考核要求
    publish_time: Mapped[str] = mapped_column(String, nullable=False, default="")  # 发布时间
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    creator_id: Mapped[str] = mapped_column(String, nullable=False, default="")
    # AI 生成记录（任务包结构草稿等）JSON
    ai_metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # 关联已确认发布的任务包（LearningPlan）id
    plan_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EnergyLedger(Base):
    """统一盾能账本 — 每一笔盾能变动都在此留痕，三口径由账本实时计算。

    三口径（见方案§9.1）：
    - 累计获得盾能 cumulative：历史上通过有效学习获得的总量，不因投放减少（用于个人等级）。
    - 当前可用盾能 available：当前可用于支持活动的余额，投放后减少。
    - 累计投放盾能 contributed：历史支持不同活动的总量，只增不减（个人共建记录）。
    """

    __tablename__ = "energy_ledgers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tx_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # earn_task | earn_elective | earn_outcome | earn_iteration | earn_featured | invest_activity | adjust
    source_ref: Mapped[str] = mapped_column(String, nullable=False, default="")  # 来源任务/活动 id
    delta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 变动量（可负）
    cumulative_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contributed_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ActivityContribution(Base):
    """活动贡献记录 — 学生向某活动投放盾能的明细。"""

    __tablename__ = "activity_contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    activity_id: Mapped[str] = mapped_column(
        String, ForeignKey("campus_activities.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ScenarioTrainingSession(Base):
    """AI 情景训练会话"""

    __tablename__ = "scenario_training_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String, nullable=False)  # 关联的训练任务
    fraud_type: Mapped[str] = mapped_column(String, nullable=False)
    # 状态机当前状态
    current_state: Mapped[str] = mapped_column(String, nullable=False, default="S0")
    # 对话消息 JSON 列表
    messages_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 已识别证据 JSON 列表
    identified_evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 用户行为记录 JSON
    user_behaviors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    # "active" | "completed" | "abandoned"
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 是否使用 AI (true) 或规则降级 (false)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RetrainTask(Base):
    """错题复训任务"""

    __tablename__ = "retrain_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    original_question_id: Mapped[str] = mapped_column(String, nullable=False)
    original_task_id: Mapped[str] = mapped_column(String, nullable=False)
    # 变式题 ID（生成后填入）
    variant_question_id: Mapped[str | None] = mapped_column(String, nullable=True)
    fraud_type: Mapped[str] = mapped_column(String, nullable=False)
    target_ability: Mapped[str] = mapped_column(String, nullable=False)
    # 第几次复训 (1/2/3)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    # "pending" | "completed" | "expired"
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    variant_strategy: Mapped[str | None] = mapped_column(String, nullable=True)


class AICallLog(Base):
    """AI 调用日志 — 赛事证据中心"""

    __tablename__ = "ai_call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # "dialogue" | "risk_analysis" | "task_planning" | "review"
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)  # 脱敏输入摘要
    output_struct: Mapped[str] = mapped_column(Text, nullable=False)  # 结构化输出 JSON
    knowledge_refs: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    token_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safety_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ==================== 阶段1 新增模型 — 支持完整核心闭环 ====================


class AssessmentSession(Base):
    """测评会话 — 支持10题快速测评与20-25题标准测评"""

    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)  # "quick"(10题) | "standard"(20-25题)
    status: Mapped[str] = mapped_column(String, nullable=False, default="in_progress")
    # "in_progress" | "completed" | "abandoned"
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AssessmentAnswer(Base):
    """测评答题记录 — 每题独立记录，支持部分得分"""

    __tablename__ = "assessment_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("assessment_sessions.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: "D" 或 ["A","B","C","D"]
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)  # 部分得分 (0.0-1.0)
    # 题目元数据快照（冗余存储，便于后续分析）
    fraud_type: Mapped[str] = mapped_column(String, nullable=False)
    ability_dim: Mapped[str] = mapped_column(String, nullable=False)
    risk_stage: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class QuestionMetadata(Base):
    """题目元数据 — 绑定诈骗类型、能力维度、风险阶段、风险证据"""

    __tablename__ = "question_metadata"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    question_type: Mapped[str] = mapped_column(String, nullable=False)  # "single" | "multiple"
    fraud_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ability_dim: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # "识诈力" | "判断力" | "应对力" | "证据力" | "求助力"
    risk_stage: Mapped[str] = mapped_column(String, nullable=False)
    # "诱导阶段" | "信任建立" | "操作诱导" | "支付转移" | "二次诈骗" | "结束"
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer_json: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 风险证据标签: ["垫付资金","高返利","做满任务提现"]
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False, default="中等")
    # "低" | "中等" | "高"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AbilitySnapshot(Base):
    """能力快照 — 每次能力变化时保存一份

    保存规则：
    - 每次完成测评或训练后生成新快照
    - 保留最近 30 个快照供趋势分析
    - 超过 30 个时，保留最早的 + 每3个取中间的 + 最近的
    """

    __tablename__ = "ability_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # 五维得分 JSON: {"识诈力": 80, "判断力": 75, "应对力": 60, "证据力": 55, "求助力": 70}
    scores_json: Mapped[str] = mapped_column(Text, nullable=False)
    # 薄弱维度 JSON: ["证据力", "应对力"]
    weak_dimensions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 薄弱诈骗类型 JSON: ["冒充客服", "刷单返利"]
    weak_types_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 总成长值
    total_growth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 触发事件类型
    trigger_event: Mapped[str] = mapped_column(String, nullable=False)
    # "assessment" | "training" | "scenario" | "retrain"
    trigger_ref: Mapped[str | None] = mapped_column(String, nullable=True)  # 关联的 session_id / record_id
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AbilityEvent(Base):
    """能力变化事件 — 记录每次能力维度分数的具体变化"""

    __tablename__ = "ability_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("ability_snapshots.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    dim_key: Mapped[str] = mapped_column(String, nullable=False)
    # 具体维度名称 "识诈力" 等
    score_before: Mapped[float] = mapped_column(Float, nullable=False)
    score_after: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)  # after - before
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ScenarioTemplate(Base):
    """情景对话状态机模板 — 定义6类诈骗场景的状态转换规则"""

    __tablename__ = "scenario_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    fraud_type: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    # "刷单返利" | "游戏交易" | "虚假客服" | "冒充老师" | "虚假招聘" | "奖助学金"
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # 场景背景介绍
    opening_message: Mapped[str] = mapped_column(Text, nullable=False)
    # 开场白（骗子角色说的第一句话）
    initial_state: Mapped[str] = mapped_column(String, nullable=False, default="contact")
    # 起始状态
    # 关键证据标签 JSON: ["垫付资金","高额返利","群聊拉人"]
    key_evidence_tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ScenarioTurn(Base):
    """情景对话轮次定义 — 每个状态下的可能输出和条件"""

    __tablename__ = "scenario_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[str] = mapped_column(String, ForeignKey("scenario_templates.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String, nullable=False)
    # "contact" | "trust" | "operation" | "payment" | "secondary" | "end"
    turn_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 该状态下的轮次序号
    # 系统提示词（给 AI 的场景上下文）
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # 用户正确回答的识别关键词 JSON
    correct_triggers_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 用户犹豫/不确定回答的关键词 JSON
    hesitation_triggers_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 用户错误回答的识别关键词 JSON
    wrong_triggers_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 进入下一状态的条件（正确回答后）
    next_state: Mapped[str | None] = mapped_column(String, nullable=True)
    # 本轮可识别的风险证据 JSON
    evidence_hints_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 正确应对策略文字
    correct_strategy: Mapped[str] = mapped_column(Text, nullable=False, default="")


class EvidenceRecord(Base):
    """证据识别记录 — 记录用户在每个情景训练中识别的证据"""

    __tablename__ = "evidence_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("scenario_training_sessions.id"), nullable=False, index=True)
    turn_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 第几轮的证据
    evidence_tag: Mapped[str] = mapped_column(String, nullable=False)  # 证据标签名称
    identified: Mapped[bool] = mapped_column(Boolean, nullable=False)  # 用户是否识别
    is_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # 是否为关键证据
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ReviewReport(Base):
    """训练复盘报告 — 情景训练结束后的自动复盘"""

    __tablename__ = "review_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("scenario_training_sessions.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # 复盘内容（规则引擎计算，AI 仅解释）
    # 已识别证据
    identified_evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 遗漏证据
    missed_evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 正确行为
    correct_behaviors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 风险行为
    risk_behaviors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 各维度得分（规则引擎计算）
    recognition_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 识诈力
    judgment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 判断力
    response_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 应对力
    evidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 证据力
    help_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 求助力
    # 总分
    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # 下一步建议（可 AI 生成）
    next_suggestions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 是否 AI 生成 (true) 或规则引擎 (false)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class WrongItem(Base):
    """错题本 — 所有答错的题目汇总"""

    __tablename__ = "wrong_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    question_stem: Mapped[str] = mapped_column(Text, nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    fraud_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ability_dim: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    # 来源: "assessment" | "training" | "retrain"
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    # 复训状态
    retrain_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    # "pending" | "scheduled" | "completed" | "mastered"
    retrain_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_retrain_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class RetrainSchedule(Base):
    """复训计划调度 — 按24小时、3天、7天安排变式复训"""

    __tablename__ = "retrain_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    wrong_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("wrong_items.id"), nullable=False, index=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)  # 第几次复训 (1/2/3)
    interval_hours: Mapped[int] = mapped_column(Integer, nullable=False)  # 间隔时长（小时）
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    # "pending" | "delivered" | "completed" | "expired"
    variant_question_id: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PromptVersion(Base):
    """Prompt 版本管理 — 所有 AI Prompt 的可追溯版本记录"""

    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # "dialogue" | "risk_analysis" | "task_planning" | "review"
    version: Mapped[str] = mapped_column(String, nullable=False)
    # "v1.0", "v1.1", "v2.0"
    title: Mapped[str] = mapped_column(String, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    # 变更说明
    changelog: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Prompt 设计思路
    design_rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 模型限定
    min_model: Mapped[str | None] = mapped_column(String, nullable=True)
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RiskTestSample(Base):
    """风险测试样本 — 用于安全护栏和效果验证的标注测试集"""

    __tablename__ = "risk_test_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 测试样本原文
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # 标注的诈骗类型
    fraud_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # 标注的风险等级
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    # "高风险" | "中风险" | "低风险" | "安全"
    # 标注的关键证据
    expected_evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # 标注的风险阶段
    risk_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    # 来源渠道
    source: Mapped[str] = mapped_column(String, nullable=False, default="人工标注")
    # 数据集标签
    dataset_label: Mapped[str] = mapped_column(String, nullable=False, default="baseline", index=True)
    # "baseline" | "challenge" | "edge_case"
    # 备注
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
