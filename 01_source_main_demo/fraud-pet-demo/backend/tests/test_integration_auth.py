"""持久化测试：第三方集成落地 + 鉴权强化。

覆盖：
- 文件真实存储（上传落盘 + 下载回读 + 隐私校验）
- 校园认证配置端点（demo/cas/oauth）
- 真实 LLM 初审降级（无密钥时走规则引擎）
- 强制鉴权 AUTH_REQUIRED=true 时对新端点返回 401
"""
from __future__ import annotations

import io


def _make_goal(client, owner_id: str) -> str:
    r = client.post(
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
    assert r.status_code == 200, r.text
    return r.json()["goal"]["id"]


def _make_artifact(client, owner_id: str) -> str:
    goal_id = _make_goal(client, owner_id)
    dash = client.get(f"/api/learning/dashboard?ownerId={owner_id}").json()
    plan_id = dash["plan"]["id"]
    r = client.post(
        "/api/learning/artifacts",
        json={
            "ownerId": owner_id,
            "planId": plan_id,
            "title": "反诈海报",
            "artifactType": "poster",
            "visibility": "public",
            "description": "展示三类高危信号",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["artifact"]["id"]


# ---------------- 文件真实存储 ----------------
def test_upload_and_download_file(client):
    owner = "up_owner"
    aid = _make_artifact(client, owner)
    content = b"%PDF-1.4 fake pdf content for test"
    r = client.post(
        f"/api/learning/artifacts/{aid}/upload?ownerId={owner}",
        files={"file": ("report.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["size"] == len(content)
    storage_key = body["storageKey"]
    assert storage_key.startswith(aid + "/")

    # 隐私：作者本人可下载
    dl = client.get(f"/api/learning/artifacts/{aid}/file/{storage_key.split('/')[-1]}?viewerId={owner}")
    assert dl.status_code == 200, dl.text
    assert dl.content == content

    # 隐私：他人对该 public 成果仍可下载
    dl2 = client.get(f"/api/learning/artifacts/{aid}/file/{storage_key.split('/')[-1]}?viewerId=someone_else")
    assert dl2.status_code == 200, dl2.text


def test_download_nonexistent_returns_404(client):
    owner = "up_owner2"
    aid = _make_artifact(client, owner)
    dl = client.get(f"/api/learning/artifacts/{aid}/file/does_not_exist.pdf?viewerId={owner}")
    assert dl.status_code == 404


def test_upload_rejects_bad_extension(client):
    owner = "up_owner3"
    aid = _make_artifact(client, owner)
    r = client.post(
        f"/api/learning/artifacts/{aid}/upload?ownerId={owner}",
        files={"file": ("evil.exe", io.BytesIO(b"x"), "application/octet-stream")},
    )
    assert r.status_code == 400


# ---------------- 校园认证配置 ----------------
def test_campus_auth_config_demo(client):
    r = client.get("/api/campus/auth-config")
    assert r.status_code == 200
    assert r.json()["mode"] == "demo"
    assert r.json()["configured"] is True


def test_campus_login_returns_token(client):
    r = client.post(
        "/api/campus/login",
        json={"studentId": "2021001", "school": "示例大学", "department": "计算机"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["token"]
    assert r.json()["currentUser"]["studentId"] == "2021001"


# ---------------- AI 初审（无密钥降级规则引擎） ----------------
def test_artifact_review_rule_fallback(client):
    owner = "rev_owner"
    aid = _make_artifact(client, owner)
    r = client.post(
        f"/api/learning/artifacts/{aid}/review",
        json={
            "ownerId": owner,
            "contentSummary": "本成果详细说明了诈骗 Risk 信号与核验方法，并给出报警与求助渠道。",
            "revisionNote": "V2 根据建议优化。",
        },
    )
    assert r.status_code == 200, r.text
    review = r.json()["review"]
    assert "score" in review and isinstance(review["score"], int)
    assert review["score"] <= 100


# ---------------- 强制鉴权（AUTH_REQUIRED=true） ----------------
def test_auth_required_blocks_tokenless_write(client, monkeypatch):
    # AUTH_REQUIRED 为运行时读取的环境变量（非模块常量），必须用 setenv 切换。
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    # 无 token / 无 ownerId -> 401（协作创建团队端点）
    r = client.post("/api/teams", json={"ownerId": "", "name": "测试团队"})
    assert r.status_code == 401, r.text


def test_auth_required_allows_valid_token(client, monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    # 先登录拿 token
    login = client.post("/api/campus/login", json={"studentId": "2021002", "school": "示例大学"})
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    # 用 token 创建团队，应成功（不再信任 body.ownerId）
    r = client.post("/api/teams", json={"ownerId": "ignored", "name": "令牌创建团队"}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["ownerId"] == login.json()["currentUser"]["ownerId"]
