"""持久化测试：学习集市主链路新端点（需求补齐项）。

覆盖模板增强、代码答疑、延期申请、协作/好友/通知/推荐等已接线功能。
鉴权已在 test_integration_auth.py 单独验证；此处走演示态（AUTH_REQUIRED=false）。
"""
from __future__ import annotations


def _login(client) -> tuple[str, str]:
    r = client.post("/api/campus/login", json={"studentId": "2021009", "school": "示例大学"})
    assert r.status_code == 200
    return r.json()["currentUser"]["ownerId"], r.json()["token"]


def _goal_and_plan(client, owner_id: str) -> tuple[str, str]:
    client.post(
        "/api/learning/goals",
        json={
            "ownerId": owner_id,
            "title": "反诈学习",
            "theme": "反诈",
            "periodDays": 7,
            "dailyMinutes": 20,
            "expectedOutcome": "能识别常见诈骗并正确处置",
            "difficulty": "入门",
            "summary": "x",
            "electiveTracks": ["a"],
        },
    )
    dash = client.get(f"/api/learning/dashboard?ownerId={owner_id}").json()
    # 返回真实 owner_id（避免调用方变量被 goal_id 遮蔽）与 plan_id
    return owner_id, dash["plan"]["id"]


def test_templates_have_rich_fields(client):
    r = client.get("/api/learning/templates")
    assert r.status_code == 200
    tpls = r.json()["templates"]
    assert len(tpls) >= 10
    first = tpls[0]
    for k in ("outline", "keyDifficulties", "referenceMaterials", "assessmentCriteria"):
        assert k in first and first[k], f"模板缺少字段 {k}"


def test_code_debug(client):
    r = client.post(
        "/api/learning/code-debug",
        json={"ownerId": "x", "language": "python", "code": "def f():\n  return y", "question": "为何报错"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "detectedIssues" in body and "hints" in body and "safetyNotes" in body


def test_plan_extend_accumulates(client):
    owner_id, plan_id = _goal_and_plan(client, "ext_owner")
    before = client.get(f"/api/learning/dashboard?ownerId={owner_id}").json()["plan"]["extensionDays"]
    r = client.post(
        f"/api/learning/plans/{plan_id}/extend",
        json={"ownerId": owner_id, "extraDays": 5, "reason": "考试冲突"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["plan"]["extensionDays"] == before + 5


def test_collaboration_flow(client):
    owner_id, _ = _goal_and_plan(client, "collab_owner")
    r = client.post("/api/teams", json={"ownerId": owner_id, "name": "反诈小组"})
    assert r.status_code == 200, r.text
    team_id = r.json()["id"]
    # 添加成员
    r2 = client.post(
        f"/api/teams/{team_id}/members",
        json={"ownerId": owner_id, "memberOwnerId": "member_a", "role": "成员"},
    )
    assert r2.status_code == 200 or r2.status_code == 409
    # 添加节点（成员也可添加）
    r3 = client.post(
        f"/api/teams/{team_id}/milestones",
        json={"ownerId": "member_a", "title": "完成海报", "dueDay": 3},
    )
    assert r3.status_code == 200, r3.text


def test_social_friend_flow(client):
    a, _ = _login(client)
    # 注册第二个用户
    r = client.post("/api/campus/login", json={"studentId": "2021010", "school": "示例大学"})
    b = r.json()["currentUser"]["ownerId"]
    r = client.post("/api/social/friends/request", json={"ownerId": a, "friendOwnerId": b})
    assert r.status_code == 200, r.text
    # b 接受
    r = client.post("/api/social/friends/accept", json={"ownerId": b, "friendOwnerId": a})
    assert r.status_code == 200, r.text
    # a 的好友列表包含 b
    lst = client.get(f"/api/social/friends?ownerId={a}").json()
    assert b in lst["friends"]


def test_notifications_and_recommend(client):
    owner_id, _ = _goal_and_plan(client, "notif_owner")
    # 触发一条评论通知：先有公开集市条目
    goal_id, plan_id = _goal_and_plan(client, "listing_owner")
    art_id = client.post(
        "/api/learning/artifacts",
        json={"ownerId": "listing_owner", "planId": plan_id, "title": "成果", "artifactType": "poster", "visibility": "public"},
    ).json()["artifact"]["id"]
    # 提交一个版本（publish 要求 latest_version >= 1）
    client.post(
        f"/api/learning/artifacts/{art_id}/versions",
        json={"ownerId": "listing_owner", "contentSummary": "这是一个用于演示的反诈主题学习成果初稿。"},
    )
    # 发布 -> 后端自动生成公开集市 listing
    pub = client.post(f"/api/learning/artifacts/{art_id}/publish", json={"ownerId": "listing_owner", "visibility": "public"})
    assert pub.status_code == 200, pub.text
    # 从市场列表取得该 listing
    listings = client.get("/api/learning/market").json()["listings"]
    listing = next((l for l in listings if l["resourceId"] == art_id), None)
    assert listing is not None, "发布后未生成集市条目"
    listing_id = listing["id"]
    # 评论 -> 作者收到通知
    c = client.post(f"/api/market/{listing_id}/comments", json={"ownerId": owner_id, "content": "很棒"})
    assert c.status_code == 200, c.text
    # 通知列表
    notes = client.get(f"/api/notifications?ownerId=listing_owner").json()
    assert any(n["type"] == "market_comment" for n in notes["notifications"])
    # 推荐
    rec = client.get(f"/api/recommend/market?ownerId={owner_id}").json()
    assert "recommendations" in rec
    study = client.get(f"/api/recommend/study?ownerId={owner_id}").json()
    assert "weakDimensions" in study
