"""鉴权相关依赖与工具（从原 ``main.py`` 提取）。

包含登录令牌生成、基于 Bearer Token 的软绑定身份解析，以及管理端端点保护。
供 ``routers/auth.py`` 等路由复用。
"""

from __future__ import annotations

import logging
import os
import secrets

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User

logger = logging.getLogger(__name__)


def gen_token() -> str:
    """生成登录令牌。"""
    return secrets.token_urlsafe(24)


def resolve_owner_id(request: Request, db: Session, payload_owner_id: str) -> str:
    """软绑定身份：携带合法 Bearer Token 时以 Token 对应的 owner_id 为准，防止客户端伪造 ownerId；
    无 Token（demo 直登路径）则回退 payload.ownerId，保证演示链路不受影响。"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):].strip()
        if token:
            owner = db.scalar(select(User).where(User.token == token))
            if owner:
                return owner.owner_id
    return payload_owner_id


_ADMIN_KEY_WARNED = False


def require_admin_key(request: Request) -> None:
    """保护 /api/admin 管理端点。

    配置环境变量 ADMIN_API_KEY 后强制校验 X-Admin-Key 头；未配置时 fail-open 放行
    （仅告警一次），以保证未部署密钥的演示环境仍可正常演示。
    """
    global _ADMIN_KEY_WARNED
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        if not _ADMIN_KEY_WARNED:
            logger.warning("ADMIN_API_KEY 未配置，/api/admin 端点当前未受保护（演示态放行）")
            _ADMIN_KEY_WARNED = True
        return
    provided = request.headers.get("X-Admin-Key", "")
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="未授权的管理端访问")
