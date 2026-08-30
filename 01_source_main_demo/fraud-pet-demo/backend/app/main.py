"""防诈智研 Demo API —— 应用组合根（composition root）。

历史：原 main.py 将所有路由处理器内联在 ``create_app`` 中（约 2700 行）。
现按业务域拆分为 ``routers/*`` 独立模块，本文件仅负责引擎/会话初始化、
统一异常处理、CORS 与挂载各路由，行为与原实现完全一致。
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .database import get_db, init
from .models import Base, VideoLibrary
from .seed import seed_database, seed_video_library
from .assessment_service import seed_question_metadata
from .risk_test_samples import seed_risk_test_samples
from .learning_market import create_learning_market_router
from .v3_routes import (
    create_activity_router,
    create_energy_router,
    create_school_router,
    create_theme_router,
)
from .routers import (
    admin,
    assessment,
    auth,
    counselor,
    dashboard,
    evidence,
    knowledge,
    misc,
    pets,
    retrain,
    risk,
    task_package,
    training,
    v1_assessment,
    v1_task_package,
    v1_training,
)

# 缺口补齐：社交/通知/协作/校园认证/推荐 等新增路由
from .routers import (
    artifacts,
    campus_auth,
    collaboration,
    market_social,
    notifications,
    recommend,
    social,
)


logger = logging.getLogger(__name__)


def default_database_url() -> str:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(exist_ok=True)
    return f"sqlite:///{data_dir / 'demo.sqlite3'}"


def create_engine_for_url(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def _migrate_pets_table(engine: Engine) -> None:
    """为旧版数据库补充 pet_name / avatar_emoji 列，保持向后兼容。"""
    inspector = inspect(engine)
    if "pets" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("pets")}
    with engine.begin() as conn:
        if "pet_name" not in existing_columns:
            conn.execute(text("ALTER TABLE pets ADD COLUMN pet_name VARCHAR"))
        if "avatar_emoji" not in existing_columns:
            conn.execute(text("ALTER TABLE pets ADD COLUMN avatar_emoji VARCHAR"))


def _migrate_v3_columns(engine: Engine) -> None:
    """V3.0 向后兼容迁移：为已有库补充 role / 活动共建字段。"""
    inspector = inspect(engine)

    def _add(table: str, column: str, ctype: str) -> None:
        if table not in inspector.get_table_names():
            return
        cols = {c["name"] for c in inspector.get_columns(table)}
        if column not in cols:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ctype}"))

    _add("accounts", "role", "VARCHAR")
    _add("users", "role", "VARCHAR")
    _add("users", "token", "VARCHAR")
    _add("campus_activities", "target_energy", "INTEGER")
    _add("campus_activities", "current_progress", "INTEGER")
    _add("campus_activities", "contributor_count", "INTEGER")
    _add("campus_activities", "status", "VARCHAR")
    _add("campus_activities", "notice_text", "TEXT")
    _add("campus_activities", "released_at", "DATETIME")
    _add("learning_plan_items", "energy_reward", "INTEGER")
    # 缺口补齐：校园认证字段、目标标签、集市评分聚合
    _add("users", "student_id", "VARCHAR")
    _add("users", "school", "VARCHAR")
    _add("users", "department", "VARCHAR")
    _add("learning_goals", "tags_json",  "TEXT")
    _add("learning_market_listings", "rating_avg", "FLOAT")
    _add("learning_market_listings", "rating_count", "INTEGER")
    # 微课视频库：主题任务包挂载真实视频（CC0）所需字段
    _add("learning_plan_items", "video_url", "VARCHAR")
    _add("learning_plan_items", "video_thumbnail", "VARCHAR")
    # 缺口补齐：延期申请累计天数
    _add("learning_plans", "extension_days", "INTEGER")
    # 缺口补齐：成果附件持久化（真实文件存储落地）
    _add("learning_artifacts", "attachments_json", "TEXT")

    # 向后兼容：迁移加列时旧活动行的共建字段为 NULL，在此补齐默认值。
    if "campus_activities" in inspector.get_table_names():
        with engine.begin() as conn:
            conn.execute(text("UPDATE campus_activities SET target_energy = 1000 WHERE target_energy IS NULL"))
            conn.execute(text("UPDATE campus_activities SET current_progress = 0 WHERE current_progress IS NULL"))
            conn.execute(text("UPDATE campus_activities SET contributor_count = 0 WHERE contributor_count IS NULL"))
            conn.execute(text("UPDATE campus_activities SET status = 'building' WHERE status IS NULL"))

    # 知识库多主题改造：补充字段并给历史反诈条目写入默认来源
    _add("knowledge_items", "theme", "VARCHAR")
    _add("knowledge_items", "source", "VARCHAR")
    _add("knowledge_items", "source_url", "VARCHAR")
    if "knowledge_items" in inspector.get_table_names():
        with engine.begin() as conn:
            conn.execute(text("UPDATE knowledge_items SET theme = '网络安全' WHERE theme IS NULL OR theme = ''"))
            conn.execute(text("UPDATE knowledge_items SET source = '平台知识库整理' WHERE source IS NULL OR source = ''"))


def create_app(database_url: str | None = None) -> FastAPI:
    engine = init(database_url or os.getenv("DATABASE_URL") or default_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    # 轻量级迁移：为已存在的 pets 表补充新字段（向后兼容旧库）
    _migrate_pets_table(engine)
    _migrate_v3_columns(engine)
    with SessionLocal() as session:
        seed_database(session)
        seed_video_library(session)
        seed_question_metadata(session)
        seed_risk_test_samples(session)

    app = FastAPI(title="防诈智研 Demo API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 统一异常处理：避免将内部异常信息/堆栈直接暴露给前端（S6/R1）
    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("未捕获异常: %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": "服务器内部错误，请稍后重试"},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"success": False, "detail": "请求参数校验失败", "errors": exc.errors()},
        )
    # AI 学习集市主链路使用独立路由模块，保留原有反诈训练 API 的兼容性。
    app.include_router(create_learning_market_router(get_db))

    # V3.0 双端口 & 统一盾能体系路由
    app.include_router(create_theme_router(get_db))
    app.include_router(create_energy_router(get_db))
    app.include_router(create_activity_router(get_db))
    app.include_router(create_school_router(get_db))

    # 业务域路由（从 create_app 中提取，保持行为完全一致）
    app.include_router(auth.router)
    app.include_router(assessment.router)
    app.include_router(v1_assessment.router)
    app.include_router(pets.router)
    app.include_router(training.router)
    app.include_router(v1_training.router)
    app.include_router(risk.router)
    app.include_router(misc.router)
    app.include_router(knowledge.router)
    app.include_router(evidence.router)
    app.include_router(retrain.router)
    app.include_router(admin.router)
    app.include_router(task_package.router)
    app.include_router(v1_task_package.router)
    app.include_router(counselor.router)
    app.include_router(dashboard.router)

    # 缺口补齐新增路由
    app.include_router(market_social.router)
    app.include_router(social.router)
    app.include_router(notifications.router)
    app.include_router(collaboration.router)
    app.include_router(campus_auth.router)
    app.include_router(recommend.router)
    app.include_router(artifacts.router)

    @app.get("/api/video-library")
    def list_video_library(theme: str | None = None) -> dict[str, object]:
        """微课视频库 —— 按主题返回可播放视频（CC0 / 免费授权）。

        前端在「主题专区」任务页需要真实视频时调用；命中不到则回退通用兜底视频。
        """
        with Session(engine) as db:
            videos = db.scalars(select(VideoLibrary).where(VideoLibrary.enabled.is_(True))).all()
        if theme:
            matched = [v for v in videos if v.theme == theme or theme in v.keywords.split()]
            if not matched:
                matched = [v for v in videos if any(kw in theme for kw in v.keywords.split())]
            if not matched:
                matched = [v for v in videos if v.theme == "通用"]
            result = matched or videos
        else:
            result = videos
        return {
            "videos": [
                {
                    "id": v.id,
                    "theme": v.theme,
                    "title": v.title,
                    "url": v.url,
                    "thumbnail": v.thumbnail,
                    "durationSeconds": v.duration_seconds,
                    "source": v.source,
                    "sourceUrl": v.source_url,
                }
                for v in result
            ]
        }

    return app



app = create_app()
