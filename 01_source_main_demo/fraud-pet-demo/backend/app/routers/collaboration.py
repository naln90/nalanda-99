"""项目式学习协作管控（需求#13）。

团队创建/成员分工、阶段节点验收、项目问题记录。关联到 LearningGoal(项目式)。
负责人可管理成员与验收节点；成员可添加节点、记录问题。
"""
from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import *
from ..helpers import *


router = APIRouter(prefix="/api/teams", tags=["项目式协作"])


def _new_team_id() -> str:
    return f"team-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.randbelow(9000) + 1000}"


class TeamCreateRequest(BaseModel):
    ownerId: str
    goalId: str | None = None
    name: str = Field(min_length=2, max_length=80)
    description: str = ""


class MemberRequest(BaseModel):
    ownerId: str
    memberOwnerId: str
    role: str = "成员"


class MilestoneRequest(BaseModel):
    ownerId: str
    title: str = Field(min_length=2, max_length=120)
    dueDay: int = Field(default=1, ge=1, le=180)


class MilestoneVerifyRequest(BaseModel):
    ownerId: str
    status: str  # verified | rejected
    note: str = ""


class IssueRequest(BaseModel):
    ownerId: str
    title: str = Field(min_length=2, max_length=120)
    description: str = ""


class IssueUpdateRequest(BaseModel):
    ownerId: str
    status: str  # open | in_progress | resolved | closed


def _team_or_404(db: Session, team_id: str) -> Team:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    return team


def _is_member(db: Session, team_id: str, owner_id: str) -> bool:
    return (
        db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.owner_id == owner_id))
        is not None
    )


@router.post("")
def create_team(payload: TeamCreateRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    team = Team(
        id=_new_team_id(),
        goal_id=payload.goalId,
        owner_id=owner_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, owner_id=owner_id, role="负责人"))
    db.commit()
    return {"id": team.id, "name": team.name, "ownerId": team.owner_id}


@router.get("")
def list_teams(
    ownerId: str = Query(default=""), request: Request = None, db: Session = Depends(get_db)
) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    owned = db.scalars(select(Team).where(Team.owner_id == owner_id)).all()
    member_rows = db.scalars(select(TeamMember).where(TeamMember.owner_id == owner_id)).all()
    member_teams = (
        db.scalars(select(Team).where(Team.id.in_([m.team_id for m in member_rows]))).all()
        if member_rows
        else []
    )
    seen: set[str] = set()
    teams = []
    for t in list(owned) + list(member_teams):
        if t.id in seen:
            continue
        seen.add(t.id)
        teams.append({"id": t.id, "name": t.name, "goalId": t.goal_id, "ownerId": t.owner_id})
    return {"teams": teams}


@router.post("/{team_id}/members")
def add_member(team_id: str, payload: MemberRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    _team_or_404(db, team_id)
    if _is_member(db, team_id, payload.memberOwnerId):
        raise HTTPException(status_code=409, detail="该成员已在团队中")
    db.add(TeamMember(team_id=team_id, owner_id=payload.memberOwnerId, role=payload.role))
    db.commit()
    return {"message": "已添加成员", "memberOwnerId": payload.memberOwnerId, "role": payload.role}


@router.get("/{team_id}/members")
def list_members(team_id: str, db: Session = Depends(get_db)) -> dict:
    _team_or_404(db, team_id)
    members = db.scalars(select(TeamMember).where(TeamMember.team_id == team_id)).all()
    return {
        "members": [
            {"ownerId": m.owner_id, "role": m.role, "createdAt": m.created_at.isoformat()} for m in members
        ]
    }


@router.delete("/{team_id}/members/{member_owner_id}")
def remove_member(
    team_id: str,
    member_owner_id: str,
    ownerId: str = Query(default=""),
    request: Request = None,
    db: Session = Depends(get_db),
) -> dict:
    owner_id = get_current_owner(request, db, ownerId or None)
    team = _team_or_404(db, team_id)
    if team.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="只有团队负责人可移除成员")
    m = db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.owner_id == member_owner_id))
    if not m:
        raise HTTPException(status_code=404, detail="成员不存在")
    db.delete(m)
    db.commit()
    return {"message": "已移除成员"}


@router.post("/{team_id}/milestones")
def add_milestone(team_id: str, payload: MilestoneRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    _team_or_404(db, team_id)
    if not _is_member(db, team_id, owner_id):
        raise HTTPException(status_code=403, detail="仅团队成员可添加节点")
    m = Milestone(team_id=team_id, title=payload.title, due_day=payload.dueDay, status="pending")
    db.add(m)
    db.commit()
    return {"id": m.id, "title": m.title, "dueDay": m.due_day, "status": m.status}


@router.get("/{team_id}/milestones")
def list_milestones(team_id: str, db: Session = Depends(get_db)) -> dict:
    _team_or_404(db, team_id)
    ms = db.scalars(select(Milestone).where(Milestone.team_id == team_id).order_by(Milestone.due_day)).all()
    return {
        "milestones": [
            {"id": x.id, "title": x.title, "dueDay": x.due_day, "status": x.status, "note": x.verification_note}
            for x in ms
        ]
    }


@router.post("/{team_id}/milestones/{milestone_id}/verify")
def verify_milestone(
    team_id: str, milestone_id: int, payload: MilestoneVerifyRequest, request: Request, db: Session = Depends(get_db)
) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    team = _team_or_404(db, team_id)
    if team.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="仅团队负责人可验收节点")
    m = db.get(Milestone, milestone_id)
    if not m or m.team_id != team_id:
        raise HTTPException(status_code=404, detail="节点不存在")
    if payload.status not in ("verified", "rejected"):
        raise HTTPException(status_code=400, detail="验收状态仅支持 verified / rejected")
    m.status = payload.status
    m.verification_note = payload.note
    db.commit()
    return {"id": m.id, "status": m.status, "note": m.verification_note}


@router.post("/{team_id}/issues")
def add_issue(team_id: str, payload: IssueRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    _team_or_404(db, team_id)
    if not _is_member(db, team_id, owner_id):
        raise HTTPException(status_code=403, detail="仅团队成员可记录问题")
    issue = ProjectIssue(
        team_id=team_id, owner_id=owner_id, title=payload.title, description=payload.description, status="open"
    )
    db.add(issue)
    db.commit()
    return {"id": issue.id, "title": issue.title, "status": issue.status}


@router.get("/{team_id}/issues")
def list_issues(team_id: str, db: Session = Depends(get_db)) -> dict:
    _team_or_404(db, team_id)
    issues = db.scalars(
        select(ProjectIssue).where(ProjectIssue.team_id == team_id).order_by(ProjectIssue.created_at.desc())
    ).all()
    return {
        "issues": [
            {
                "id": x.id,
                "ownerId": x.owner_id,
                "title": x.title,
                "description": x.description,
                "status": x.status,
                "createdAt": x.created_at.isoformat(),
            }
            for x in issues
        ]
    }


@router.patch("/{team_id}/issues/{issue_id}")
def update_issue(
    team_id: str, issue_id: int, payload: IssueUpdateRequest, request: Request, db: Session = Depends(get_db)
) -> dict:
    owner_id = get_current_owner(request, db, payload.ownerId or None)
    _team_or_404(db, team_id)
    issue = db.get(ProjectIssue, issue_id)
    if not issue or issue.team_id != team_id:
        raise HTTPException(status_code=404, detail="问题不存在")
    if payload.status not in ("open", "in_progress", "resolved", "closed"):
        raise HTTPException(status_code=400, detail="非法状态")
    issue.status = payload.status
    db.commit()
    return {"id": issue.id, "status": issue.status}
