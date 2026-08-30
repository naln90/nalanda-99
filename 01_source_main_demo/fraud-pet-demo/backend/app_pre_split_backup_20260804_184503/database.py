"""数据库引擎与会话基础设施。

将原先位于 ``main.create_app`` 内部的引擎创建、会话工厂、``get_db`` 依赖与
进程内并发锁提取到独立模块，使各业务路由（``routers/*``）可在模块级复用，
而不必依赖 ``create_app`` 闭包。``create_app`` 通过 :func:`init` 配置会话工厂。
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# 进程级单例：引擎、会话工厂、奖励发放并发锁
_engine: Engine | None = None
SessionLocal: sessionmaker | None = None
_submit_lock = threading.Lock()


def default_database_url() -> str:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(exist_ok=True)
    return f"sqlite:///{data_dir / 'demo.sqlite3'}"


def create_engine_for_url(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def init(database_url: str | None = None) -> Engine:
    """创建引擎与会话工厂（每次 ``create_app`` 调用时执行）。"""
    global _engine, SessionLocal
    url = database_url or os.getenv("DATABASE_URL") or default_database_url()
    _engine = create_engine_for_url(url)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("database not initialized; call init() first")
    return _engine


def get_db() -> Session:
    """FastAPI 依赖：提供请求级数据库会话（路由统一通过此依赖获取 db）。"""
    if SessionLocal is None:
        raise RuntimeError("database not initialized; call init() first")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_submit_lock() -> threading.Lock:
    """返回进程内奖励发放锁，保证同一进程内并发提交时的原子发奖。"""
    return _submit_lock
