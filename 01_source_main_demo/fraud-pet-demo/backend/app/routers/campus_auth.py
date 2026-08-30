"""校园账号登录（需求#30）。

以「学号 + 学校」作为校园身份锚点。支持三种认证模式：
- demo：演示态，仅用学号 + 学校生成匿名 owner_id（默认，无需任何外部依赖）；
- cas：对接学校 CAS 2.0 统一认证（serviceValidate 校验 ticket）；
- oauth：对接学校 OAuth2 / OIDC（用授权码交换 token 并取用户态）。

认证模式由环境变量 CAMPUS_AUTH_MODE 控制；cas / oauth 所需端点通过环境变量配置。
未配置或不可达时，生产代码会抛出清晰错误，前端可提示切换演示态。
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/campus", tags=["校园认证登录"])

CAMPUS_AUTH_MODE = os.getenv("CAMPUS_AUTH_MODE", "demo").lower()
CAMPUS_SCHOOL_NAME = os.getenv("CAMPUS_SCHOOL_NAME", "示例大学")


def _campus_owner_id(student_id: str, school: str) -> str:
    h = hashlib.sha256(f"{school}::{student_id}".encode("utf-8")).hexdigest()[:10]
    return f"S-{h}"


def _auth_config() -> dict:
    if CAMPUS_AUTH_MODE == "cas":
        configured = bool(os.getenv("CAMPUS_CAS_BASE_URL"))
        return {"mode": "cas", "providerLabel": "学校 CAS 统一认证", "configured": configured}
    if CAMPUS_AUTH_MODE == "oauth":
        configured = bool(os.getenv("CAMPUS_OAUTH_TOKEN_URL") and os.getenv("CAMPUS_OAUTH_CLIENT_ID"))
        return {"mode": "oauth", "providerLabel": "学校 OAuth2 统一认证", "configured": configured}
    return {"mode": "demo", "providerLabel": "演示态（学号+学校）", "configured": True}


@router.get("/auth-config")
def campus_auth_config() -> dict:
    """返回当前校园认证方式，前端据此展示徽标或跳转学校 SSO。"""
    return _auth_config()


class CampusLoginRequest(BaseModel):
    studentId: str = Field(min_length=4, max_length=40)
    school: str = Field(min_length=2, max_length=80)
    department: str = ""
    password: str = ""
    # 生产态由前端 SSO 回调携带
    ticket: str = ""  # CAS service ticket
    code: str = ""  # OAuth authorization code


class CampusBindRequest(BaseModel):
    ownerId: str
    studentId: str = Field(min_length=4, max_length=40)
    school: str = Field(min_length=2, max_length=80)
    department: str = ""


def _apply_campus_user(db: Session, owner_id: str, student_id: str, school: str, department: str):
    user = get_or_create_user(db, owner_id)
    user.student_id = student_id
    user.school = school
    user.department = department or None
    user.token = gen_token()
    db.commit()
    return user


@router.post("/login")
def campus_login(payload: CampusLoginRequest, db: Session = Depends(get_db)) -> dict:
    mode = CAMPUS_AUTH_MODE

    if mode == "cas":
        if not payload.ticket:
            raise HTTPException(status_code=400, detail="缺少 CAS ticket，请由学校 CAS 登录回调携带。")
        cas_base = os.getenv("CAMPUS_CAS_BASE_URL")
        if not cas_base:
            raise HTTPException(status_code=500, detail="服务端未配置 CAMPUS_CAS_BASE_URL，无法校验 CAS ticket。")
        service = os.getenv("CAMPUS_CAS_SERVICE", "")
        student_id = _validate_cas_ticket(cas_base, payload.ticket, service)
        if not student_id:
            raise HTTPException(status_code=401, detail="CAS 票据校验失败或无有效用户。")
        school = CAMPUS_SCHOOL_NAME
        owner_id = _campus_owner_id(student_id, school)
        user = _apply_campus_user(db, owner_id, student_id, school, payload.department)
        return {
            "currentUser": user_to_response(user),
            "token": user.token,
            "message": "已通过学校 CAS 统一认证登录。",
        }

    if mode == "oauth":
        if not payload.code:
            raise HTTPException(status_code=400, detail="缺少 OAuth 授权码 code。")
        token_url = os.getenv("CAMPUS_OAUTH_TOKEN_URL")
        client_id = os.getenv("CAMPUS_OAUTH_CLIENT_ID")
        client_secret = os.getenv("CAMPUS_OAUTH_CLIENT_SECRET")
        redirect_uri = os.getenv("CAMPUS_OAUTH_REDIRECT_URI", "")
        if not (token_url and client_id):
            raise HTTPException(status_code=500, detail="服务端未配置 OAuth 端点或客户端ID。")
        userinfo = _exchange_oauth_code(token_url, client_id, client_secret, payload.code, redirect_uri)
        if not userinfo or not userinfo.get("studentId"):
            raise HTTPException(status_code=401, detail="OAuth 授权失败或未取得学号。")
        student_id = userinfo["studentId"]
        school = userinfo.get("school") or CAMPUS_SCHOOL_NAME
        owner_id = _campus_owner_id(student_id, school)
        user = _apply_campus_user(
            db, owner_id, student_id, school, userinfo.get("department", payload.department)
        )
        return {
            "currentUser": user_to_response(user),
            "token": user.token,
            "message": "已通过学校 OAuth 统一认证登录。",
        }

    # demo 模式（默认）：学号 + 学校匿名锚点，不存储姓名/证件
    owner_id = _campus_owner_id(payload.studentId, payload.school)
    user = _apply_campus_user(db, owner_id, payload.studentId, payload.school, payload.department)
    return {
        "currentUser": user_to_response(user),
        "token": user.token,
        "message": "校园账号登录成功（演示态：学号+学校认证；正式环境可对接 CAS/OAuth 统一认证）",
    }


def _validate_cas_ticket(cas_base: str, ticket: str, service: str) -> str | None:
    """CAS 2.0 serviceValidate，返回学号（user）或 None。

    兼容两种响应：标准带命名空间（cas:user）与部分学校省略命名空间（直接 <user>）。
    """
    url = (
        f"{cas_base.rstrip('/')}/serviceValidate"
        f"?ticket={urllib.parse.quote(ticket)}&service={urllib.parse.quote(service)}"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode("utf-8")
        root = ET.fromstring(data)
        # 优先带命名空间；失败时退回无命名空间查找（不同 CAS 实现差异）。
        user_el = root.find(".//{http://www.yale.edu/tp/cas}user")
        if user_el is None:
            user_el = root.find(".//user")
        if user_el is None or not user_el.text:
            return None
        return user_el.text.strip()
    except Exception:
        return None


def _exchange_oauth_code(
    token_url: str, client_id: str, client_secret: str, code: str, redirect_uri: str
) -> dict | None:
    """OAuth2 授权码换 token（脚手架），并占位获取用户态。"""
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        token_url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
        access_token = token_data.get("access_token")
        if not access_token:
            return None
        userinfo_url = os.getenv("CAMPUS_OAUTH_USERINFO_URL", "")
        if not userinfo_url:
            return {"studentId": ""}
        req2 = urllib.request.Request(
            userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            return json.loads(resp2.read().decode("utf-8"))
    except Exception:
        return None


@router.post("/bind")
def campus_bind(payload: CampusBindRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.owner_id == payload.ownerId))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.student_id = payload.studentId
    user.school = payload.school
    user.department = payload.department or None
    db.commit()
    return {"currentUser": user_to_response(user), "message": "已绑定校园账号信息"}
