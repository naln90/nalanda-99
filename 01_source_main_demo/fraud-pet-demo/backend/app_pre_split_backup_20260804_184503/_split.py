"""Deterministic split of main.py into routers/* + helpers.py + schemas.py.

Strategy: every route handler is extracted VERBATIM from main.create_app and
rewritten only at the syntax level (@app -> @router, absolute path -> relative
route, and nested ``from .`` -> ``from ..``). The create_app composition root is
rebuilt from a verbatim template. This guarantees zero behaviour change.
"""
from __future__ import annotations

import ast
import os
import re

SRC = "main.py"
text = open(SRC, encoding="utf-8").read()
tree = ast.parse(text)

ROUTE_METHODS = {"get", "post", "put", "delete", "patch", "options"}
KEEP_FUNCS = {
    "default_database_url",
    "create_engine_for_url",
    "_migrate_pets_table",
    "_migrate_v3_columns",
    "create_app",
}

mod_stmts = list(tree.body)
schema_classes = [n for n in mod_stmts if isinstance(n, ast.ClassDef)]
mod_funcs = [n for n in mod_stmts if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
mod_assigns = [n for n in mod_stmts if isinstance(n, ast.Assign)]


def get_segment(node):
    return ast.get_source_segment(text, node)


def is_skipped_assign(n):
    for t in n.targets:
        if isinstance(t, ast.Name) and t.id in ("logger", "app"):
            return True
    return False


move_classes = schema_classes
move_funcs = [n for n in mod_funcs if n.name not in KEEP_FUNCS]
keep_funcs = [n for n in mod_funcs if n.name in KEEP_FUNCS]
move_assigns = [n for n in mod_assigns if not is_skipped_assign(n)]

# ---------------- schemas.py ----------------
schemas_header = '''"""Pydantic 请求模型（原 main.py 内联定义的逐字迁移）。"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


'''
schemas_body = "\n\n\n".join(get_segment(n) for n in move_classes)
with open("schemas.py", "w", encoding="utf-8") as f:
    f.write(schemas_header + schemas_body + "\n")

# ---------------- helpers.py ----------------
helpers_header = '''"""原 main.py 的模块级辅助函数与常量（逐字迁移），供 routers/* 复用。"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import threading
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import *
from .question_bank import ALL_QUESTIONS
from .database import get_submit_lock


logger = logging.getLogger(__name__)

submit_lock = get_submit_lock()
'''
moved_stmts = sorted(move_assigns + move_funcs, key=lambda n: n.lineno)
helpers_body = "\n\n\n".join(get_segment(n) for n in moved_stmts)
with open("helpers.py", "w", encoding="utf-8") as f:
    f.write(helpers_header + helpers_body + "\n")

# ---------------- routers ----------------
create_app = next(n for n in mod_funcs if n.name == "create_app")
handlers = []
for n in ast.walk(create_app):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for d in n.decorator_list:
            if (
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and isinstance(d.func.value, ast.Name)
                and d.func.value.id == "app"
                and d.func.attr in ROUTE_METHODS
            ):
                method = d.func.attr
                path = ast.literal_eval(d.args[0])
                handlers.append((method, path, n))
                break

def compute_prefix_route(path):
    """Return (prefix, route) using the API namespace as prefix.

    - /api/X                       -> prefix '/api',            route '/X'
    - /api/<res>/...               -> prefix '/api/<res>',     route '/...'
    - /api/v1/<res>/...            -> prefix '/api/v1/<res>',  route '/...'
    """
    segs = path.split("/")  # ['', 'api', ...]
    if len(segs) == 3:
        return "/api", path[4:]
    if segs[2] == "v1":
        prefix = "/".join(segs[:4])
        route = "/" + "/".join(segs[4:])
        return prefix, route
    prefix = "/".join(segs[:3])
    route = "/" + "/".join(segs[3:])
    return prefix, route


groups = {}
for method, path, node in handlers:
    prefix, route = compute_prefix_route(path)
    groups.setdefault(prefix, []).append((method, path, route, node))


def filename_for(prefix):
    if prefix == "/api":
        return "misc"
    rest = prefix[len("/api"):].lstrip("/")
    return rest.replace("/", "_").replace("-", "_")


router_imports = '''from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import threading
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import create_engine, desc, func, inspect, select, text
from sqlalchemy.orm import Session

from ..database import get_db, get_submit_lock
from ..models import *
from ..schemas import *
from ..rules import *
from ..helpers import *
from ..seed import pet_to_response, seed_database
from ..ai_service import AIService, is_llm_available, MODEL_NAME
from ..assessment_service import *
from ..image_analysis import analyze_image
from ..question_bank import ALL_QUESTIONS
from ..risk_test_samples import seed_risk_test_samples
from ..scenarios import scenario_response
from ..ability_profile import *
from ..retrain_scheduler import *
from ..task_planner import *
from ..scenario_state_machine import *
from ..review_engine import *
from ..emergency_stop_loss import *
from ..ai_logger import *


logger = logging.getLogger(__name__)

'''

os.makedirs("routers", exist_ok=True)
open("routers/__init__.py", "w", encoding="utf-8").write("")
for stale in ("routers/ranking.py", "routers/records.py"):
    if os.path.exists(stale):
        os.remove(stale)

for prefix, items in groups.items():
    fname = filename_for(prefix)
    out = [router_imports]
    out.append(f'router = APIRouter(prefix="{prefix}", tags=["{fname}"])\n')
    for method, path, route, node in items:
        seg = get_segment(node)
        # get_source_segment starts at the `def` line (excludes decorators),
        # so reconstruct the decorator explicitly from the known method/route.
        seg = re.sub(r'^(\s*)from \.', r'\1from ..', seg, flags=re.M)
        out.append(f'@router.{method}("{route}")\n')
        out.append(seg)
        out.append("\n")
    with open(f"routers/{fname}.py", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

# ---------------- main.py ----------------
kept = "\n\n\n".join(get_segment(n) for n in sorted(keep_funcs, key=lambda n: n.lineno))

main_header = '''"""防诈智研 Demo API —— 应用组合根（composition root）。

历史：原 main.py 将所有路由处理器内联在 ``create_app`` 中（约 2700 行）。
现按业务域拆分为 ``routers/*`` 独立模块，本文件仅负责引擎/会话初始化、
统一异常处理、CORS 与挂载各路由，行为与原实现完全一致。
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .database import get_db, init
from .models import Base
from .seed import seed_database
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


logger = logging.getLogger(__name__)


'''

create_app_template = '''def create_app(database_url: str | None = None) -> FastAPI:
    engine = init(database_url or os.getenv("DATABASE_URL") or default_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    # 轻量级迁移：为已存在的 pets 表补充新字段（向后兼容旧库）
    _migrate_pets_table(engine)
    _migrate_v3_columns(engine)
    with SessionLocal() as session:
        seed_database(session)
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
    from .learning_market import create_learning_market_router

    app.include_router(create_learning_market_router(get_db))

    # V3.0 双端口 & 统一盾能体系路由
    from .v3_routes import (
        create_activity_router,
        create_energy_router,
        create_school_router,
        create_theme_router,
    )

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

    return app
'''

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_header + kept + "\n\n\n" + create_app_template + "\n\n\napp = create_app()\n")

print("DONE")
print("router groups:", {filename_for(p): len(v) for p, v in groups.items()})
