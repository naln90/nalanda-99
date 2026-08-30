from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    from app.main import create_app

    return TestClient(create_app(database_url=f"sqlite:///{tmp_path / 'learning.sqlite3'}"))


def test_learning_market_end_to_end_unlocks_activity(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    owner_id = "U-LEARN**"
    client.post("/api/auth/demo-login", json={"ownerId": owner_id})

    validation = client.post(
        "/api/learning/goals/validate",
        json={
            "theme": "大学生校园反诈",
            "periodDays": 14,
            "dailyMinutes": 20,
            "difficulty": "进阶",
            "expectedOutcome": "完成一张大学生兼职诈骗防范海报",
        },
    )
    assert validation.status_code == 200
    assert validation.json()["isExecutable"] is True

    created = client.post(
        "/api/learning/goals",
        json={
            "ownerId": owner_id,
            "theme": "大学生校园反诈",
            "learningType": "自主学习",
            "periodDays": 14,
            "dailyMinutes": 20,
            "difficulty": "进阶",
            "expectedOutcome": "完成一张大学生兼职诈骗防范海报",
            "majorDirection": "数字安全",
            "electiveTracks": ["情境挑战", "案例研判", "创意表达"],
        },
    )
    assert created.status_code == 200
    plan = created.json()["plan"]
    assert {item["category"] for item in plan["items"]} == {"required", "elective", "outcome"}

    required = [item for item in plan["items"] if item["category"] == "required"][:2]
    elective = next(item for item in plan["items"] if item["category"] == "elective")
    for item in [*required, elective]:
        completed = client.post(
            f"/api/learning/plan-items/{item['id']}/complete",
            json={"ownerId": owner_id, "completionNote": "测试完成"},
        )
        assert completed.status_code == 200
        assert completed.json()["awarded"] > 0

    artifact = client.post(
        "/api/learning/artifacts",
        json={
            "ownerId": owner_id,
            "planId": plan["id"],
            "title": "兼职诈骗防范海报",
            "artifactType": "海报",
            "description": "面向大学生的反诈主题成果",
            "visibility": "private",
        },
    ).json()["artifact"]
    uploaded = client.post(
        f"/api/learning/artifacts/{artifact['id']}/upload?ownerId={owner_id}",
        files={"file": ("poster-v1.png", b"demo-image-bytes", "image/png")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["size"] == len(b"demo-image-bytes")
    version = client.post(
        f"/api/learning/artifacts/{artifact['id']}/versions",
        json={
            "ownerId": owner_id,
            "fileName": "poster-v1.png",
            "contentSummary": "作品展示先垫付和高额返利风险，建议停止转账、保存证据并拨打96110核验。",
            "revisionNote": "",
        },
    )
    assert version.status_code == 200
    assert version.json()["review"]["score"] >= 70

    published = client.post(
        f"/api/learning/artifacts/{artifact['id']}/publish",
        json={"ownerId": owner_id, "visibility": "public"},
    )
    assert published.status_code == 200

    activities = client.get(f"/api/learning/activities?ownerId={owner_id}")
    assert activities.status_code == 200
    tree = next(item for item in activities.json()["activities"] if item["id"] == "activity-tree-planting")
    assert tree["status"] == "unlocked"
    assert "不等同于报名" in tree["boundaryNotice"]

    market = client.get("/api/learning/market?resourceType=artifact")
    assert market.status_code == 200
    assert any(item["resourceId"] == artifact["id"] for item in market.json()["listings"])
