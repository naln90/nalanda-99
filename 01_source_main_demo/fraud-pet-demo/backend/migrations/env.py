"""Alembic 迁移环境配置 — 防诈智研项目

自动从 app.models 导入 Base.metadata，
从 DATABASE_URL 环境变量或默认值获取数据库连接。
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 将 backend/ 目录加入 sys.path，使得 app 包可被导入
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# 导入 Base 和所有模型（确保所有表定义都注册到 metadata）
# 注意：不能导入 app.main，因为它在模块级调用 Base.metadata.create_all()
from app.models import Base  # noqa: E402
from app import models  # noqa: E402, F401 — 触发所有模型定义

# Alembic 配置对象
config = context.config

# 设置数据库 URL（优先使用环境变量，其次检查 alembic.ini 中的非占位值，最后使用默认 SQLite 路径）
_BACKEND_SIBLING = BACKEND_DIR
_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    ini_url = config.get_main_option("sqlalchemy.url")
    if not ini_url or ini_url.startswith("driver://"):
        _data_dir = _BACKEND_SIBLING / "data"
        _data_dir.mkdir(exist_ok=True)
        _db_url = f"sqlite:///{_data_dir / 'demo.sqlite3'}"
    else:
        _db_url = ini_url
config.set_main_option("sqlalchemy.url", _db_url)

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata（用于 autogenerate）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：仅生成 SQL 脚本，不连接数据库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接数据库并执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
