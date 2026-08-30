from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    from app.main import create_app

    db_url = f"sqlite:///{tmp_path / 'demo.sqlite3'}"
    return TestClient(create_app(database_url=db_url))


def test_demo_login_assessment_and_pet_claim_flow(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    login = client.post("/api/auth/demo-login", json={"ownerId": "U-2408**"})
    assert login.status_code == 200
    current_user = login.json()["currentUser"]
    assert current_user["ownerId"] == "U-2408**"
    assert current_user["hasCompletedAssessment"] is False
    assert current_user["hasPet"] is False
    # demo-login 现已下发 token（A17），用于后续请求鉴权
    assert isinstance(login.json().get("token"), str) and login.json()["token"]

    questions = client.get("/api/assessment/questions")
    assert questions.status_code == 200
    assert len(questions.json()["questions"]) >= 1

    assessment = client.post(
        "/api/assessment/submit",
        json={"ownerId": "U-2408**", "answers": [{"questionId": "assess-q1", "answer": "D"}]},
    )
    assert assessment.status_code == 200
    body = assessment.json()
    assert body["accuracy"] == 1.0
    assert body["growthAwarded"] == 30
    assert body["unlockedPetPool"] is True

    pool = client.get("/api/pets/pool")
    assert pool.status_code == 200
    assert len(pool.json()["pets"]) == 9

    claim = client.post("/api/pets/claim", json={"ownerId": "U-2408**", "petType": "反诈小卫士"})
    assert claim.status_code == 200
    pet = claim.json()["pet"]
    assert pet["petId"].startswith("PET-")
    assert pet["ownerId"] == "U-2408**"
    assert pet["type"] == "反诈小卫士"
    assert pet["level"] == 1
    assert pet["stage"] == "幼崽期"
    assert pet["growthValue"] == 30


def test_training_submission_awards_growth_then_blocks_duplicate_task(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post("/api/auth/demo-login", json={"ownerId": "U-2408**"})
    client.post("/api/assessment/submit", json={"ownerId": "U-2408**", "answers": []})
    client.post("/api/pets/claim", json={"ownerId": "U-2408**", "petType": "反诈小卫士"})

    first = client.post(
        "/api/training/submit",
        json={
            "ownerId": "U-2408**",
            "taskId": "ai-face",
            "answers": [{"questionId": "ai-face-q1", "answer": ["A", "B", "C", "D"]}],
            "mode": "recommended",
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["rewardStatus"] == "AWARDED"
    assert first_body["growth"]["finalGrowth"] > 0
    assert first_body["pet"]["growthValue"] == 30 + first_body["growth"]["finalGrowth"]

    duplicate = client.post(
        "/api/training/submit",
        json={
            "ownerId": "U-2408**",
            "taskId": "ai-face",
            "answers": [{"questionId": "ai-face-q1", "answer": ["A", "B", "C", "D"]}],
            "mode": "recommended",
        },
    )
    assert duplicate.status_code == 200
    duplicate_body = duplicate.json()
    assert duplicate_body["rewardStatus"] == "NO_REWARD"
    assert duplicate_body["growth"]["finalGrowth"] == 0
    assert "不再增加成长值" in duplicate_body["rewardMessage"]


def test_risk_analyze_scores_high_risk_and_awards_small_growth(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post("/api/auth/demo-login", json={"ownerId": "U-2408**"})
    client.post("/api/assessment/submit", json={"ownerId": "U-2408**", "answers": []})
    client.post("/api/pets/claim", json={"ownerId": "U-2408**", "petType": "反诈小卫士"})

    response = client.post(
        "/api/risk/analyze",
        json={
            "ownerId": "U-2408**",
            "text": "平台退款需要开启屏幕共享，请提供验证码，否则限时冻结账户。",
            "sourceType": "聊天记录",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["riskLevel"] == "高风险"
    assert body["riskScore"] >= 61
    assert body["fraudType"] == "冒充客服 / 网购退款"
    assert body["growthAwarded"] == 10
    assert any("屏幕共享" in item for item in body["evidence"])
    assert "系统仅用于校园反诈教育训练和风险提示" in body["complianceNotice"]


def test_ranking_is_sorted_and_privacy_safe(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post("/api/auth/demo-login", json={"ownerId": "U-2408**"})
    client.post("/api/assessment/submit", json={"ownerId": "U-2408**", "answers": []})
    client.post("/api/pets/claim", json={"ownerId": "U-2408**", "petType": "反诈小卫士"})

    response = client.get("/api/ranking?type=total")

    assert response.status_code == 200
    body = response.json()
    growth_values = [row["growthValue"] for row in body["list"]]
    assert growth_values == sorted(growth_values, reverse=True)
    assert body["privacyNotice"] == "不展示真实姓名、手机号、学号、身份证号和负面评价标签。"
    assert "realName" not in body["list"][0]
    assert "phone" not in body["list"][0]
    assert body["myRank"]["ownerId"] == "U-2408**"
