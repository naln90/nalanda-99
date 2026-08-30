from __future__ import annotations

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


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

@router.get("/categories")

def knowledge_categories(db: Session = Depends(get_db)) -> dict[str, object]:
        categories = db.scalars(select(KnowledgeItem.category).distinct().order_by(KnowledgeItem.category)).all()
        return {"categories": categories}


@router.get("/items")

def knowledge_items(category: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
        query = select(KnowledgeItem)
        if category:
            query = query.where(KnowledgeItem.category == category)
        items = db.scalars(query.order_by(KnowledgeItem.id)).all()
        return {
            "items": [
                {
                    "id": item.id,
                    "category": item.category,
                    "title": item.title,
                    "riskLevel": item.risk_level,
                    "typicalPhrase": item.typical_phrase,
                    "recognitionPoints": item.recognition_points,
                    "suggestions": item.suggestions,
                    "relatedTaskId": item.related_task_id,
                }
                for item in items
            ]
        }


@router.post("/analyze-image")

async def knowledge_analyze_image(image: UploadFile = File(...)) -> dict[str, object]:
        """上传聊天截图，返回模拟 OCR 文本与诈骗类型识别结果。

        当前为 Demo 模拟识别：不依赖真实 OCR 引擎，基于文件哈希从预置样本库
        中抽取模拟文本并做关键词匹配。生产环境可替换为真实 OCR + LLM。
        """
        try:
            # 先按声明体积快速拦截，再分块读取并硬性封顶，避免超大文件占满内存（性能/健壮性 R2）
            max_bytes = 10 * 1024 * 1024
            if image.size is not None and image.size > max_bytes:
                return {
                    "success": False,
                    "error": "图片过大，请压缩后在 10MB 以内重试",
                    "filename": image.filename or "screenshot.png",
                }
            file_bytes = await image.read(max_bytes + 1)
            if len(file_bytes) > max_bytes:
                return {
                    "success": False,
                    "error": "图片过大，请压缩后在 10MB 以内重试",
                    "filename": image.filename or "screenshot.png",
                }
            result = analyze_image(file_bytes, image.filename or "screenshot.png")
            return result
        except Exception:
            logger.exception("图片分析失败")
            return {
                "success": False,
                "error": "图片分析失败，请稍后重试或检查图片格式",
                "filename": image.filename or "screenshot.png",
            }


