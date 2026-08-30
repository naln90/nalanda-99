"""Pydantic 请求模型（原 main.py 内联定义的逐字迁移）。"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class DemoLoginRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=40)
    nickname: str = Field(default="", max_length=20)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AssessmentAnswer(BaseModel):
    questionId: str
    answer: Any = None


class AssessmentSubmitRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    answers: list[AssessmentAnswer] = Field(default_factory=list)


class CreateSessionRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    mode: str = Field(default="quick")


class SubmitAnswerRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    questionId: str = Field(min_length=1)
    answer: Any


class CompleteSessionRequest(BaseModel):
    sessionId: str = Field(min_length=1)


class PetClaimRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    petType: str = Field(min_length=1)
    petName: str | None = Field(default=None, max_length=20)
    avatarEmoji: str | None = Field(default=None, max_length=8)


class PetProfileUpdateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    petName: str | None = Field(default=None, max_length=20)
    avatarEmoji: str | None = Field(default=None, max_length=8)


class TrainingAnswer(BaseModel):
    questionId: str
    answer: Any = None


class TrainingSubmitRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    taskId: str = Field(min_length=1)
    answers: list[TrainingAnswer] = Field(default_factory=list, max_length=500)
    mode: str = "recommended"


class RiskAnalyzeRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=2000)
    sourceType: str = "聊天记录"


class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    fraudType: str = "综合诈骗风险"
    sourceChannel: str = "手工录入"
    riskLevel: str = "中风险"
    summary: str = Field(default="", max_length=2000)


class ScenarioStartRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    taskId: str = Field(min_length=1)


class ScenarioReplyRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=1000)


class ScenarioFinishRequest(BaseModel):
    ownerId: str = Field(min_length=1)


class ScenarioStartV1Request(BaseModel):
    ownerId: str = Field(min_length=1)
    scenarioType: str = Field(min_length=1, max_length=40)


class ScenarioReplyV1Request(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class TaskPackageGenerateRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    planType: str = "7day"


class TaskPackageItemCompleteRequest(BaseModel):
    ownerId: str = Field(min_length=1)
    score: float | None = None


class EmergencyStopLossRequest(BaseModel):
    selectedRisks: list[str] = Field(default_factory=list, max_length=20)
