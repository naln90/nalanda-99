"""文件存储后端（需求 #19 / #20 真实落地）。

默认「本地磁盘」存储：``data/uploads/<artifact_id>/<file>``，零外部依赖、演示即用。
如需对象存储（S3 / 兼容 MinIO），设置环境变量 ``STORAGE_BACKEND=s3`` 并配置
``S3_BUCKET`` / ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` / ``S3_REGION`` /
``S3_ENDPOINT_URL``，届时 save/load 走 boto3；**未安装 boto3 时自动回退本地**，
保证代码在任何环境都能跑起来。

storage_key 统一形如 ``<artifact_id>/<filename>``，解析时做目录穿越防护。
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi.responses import FileResponse, StreamingResponse

logger = logging.getLogger(__name__)

LOCAL_ROOT = Path(__file__).resolve().parents[1] / "data" / "uploads"
BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()


def _safe_parts(storage_key: str) -> list[str]:
    """拆分 storage_key 并剔除危险片段，防止 ../../ 穿越。"""
    return [p for p in storage_key.split("/") if p not in ("", ".", "..")]


def _local_path(storage_key: str) -> Path:
    return LOCAL_ROOT.joinpath(*_safe_parts(storage_key))


def save_file(storage_key: str, content: bytes) -> None:
    """持久化一个文件。本地后端直接落盘；s3 后端走对象存储。

    设计原则：任何异常都不应让上传接口崩溃——s3 不可用时静默回退本地。
    """
    if BACKEND == "s3":
        try:
            _save_s3(storage_key, content)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("S3 存储失败，回退本地磁盘：%s", exc)
    path = _local_path(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def load_file_response(storage_key: str):
    """返回可用于下载/预览的 FastAPI 响应；文件不存在返回 None。"""
    if BACKEND == "s3":
        try:
            return _load_s3_response(storage_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("S3 读取失败：%s", exc)
            return None
    path = _local_path(storage_key)
    if not path.exists() or not path.is_file():
        return None
    return FileResponse(path)


def _save_s3(storage_key: str, content: bytes) -> None:
    import boto3  # 延迟导入：未配置 s3 时无需该依赖

    bucket = os.getenv("S3_BUCKET", "")
    if not bucket:
        raise RuntimeError("STORAGE_BACKEND=s3 但未配置 S3_BUCKET")
    client = boto3.client(
        "s3",
        region_name=os.getenv("S3_REGION"),
        endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    client.put_object(Bucket=bucket, Key=storage_key, Body=content)


def _load_s3_response(storage_key: str):
    import boto3

    bucket = os.getenv("S3_BUCKET", "")
    client = boto3.client(
        "s3",
        region_name=os.getenv("S3_REGION"),
        endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    obj = client.get_object(Bucket=bucket, Key=storage_key)
    return StreamingResponse(
        obj["Body"].iter_chunks(),
        media_type=obj.get("ContentType", "application/octet-stream"),
    )
