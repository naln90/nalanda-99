"""持久化测试套件 — 共用 fixtures。

每个测试使用独立的临时 SQLite 库（不污染演示数据，也避免共享库文件锁导致
teardown 删除失败）；AUTH_REQUIRED 默认关闭以兼容演示链路，专门的鉴权用例单独开启。
"""
from __future__ import annotations

import os
import tempfile

# 测试期间关闭强制鉴权，确保 demo 回退路径可用；专门的鉴权用例单独开启。
os.environ.setdefault("AUTH_REQUIRED", "false")

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture()
def client():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    # 每个测试一个独立文件，避免跨测试污染与 Windows 下的文件锁冲突。
    tf = tempfile.NamedTemporaryFile(
        suffix=".sqlite", delete=False, dir=str(_DATA_DIR)
    )
    tf.close()
    db_path = tf.name
    app = create_app(database_url=f"sqlite:///{db_path}")
    with TestClient(app) as c:
        yield c
    # 清理：先释放引擎持有的连接以解除文件锁，再删除临时库。
    try:
        from app.database import get_engine

        get_engine().dispose()
    except Exception:
        pass
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture()
def owner_id() -> str:
    return "test_owner_001"
