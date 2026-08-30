"""鉴权基座与健壮性回归测试（锁定 A14/A17/A18/A19/A20 修复）。

这些测试不引入任何产品功能，只验证既有演示链路在以下加固后行为正确：
- A14 进程内锁保证并发提交只发奖一次（幂等）。
- A17 登录统一下发并持久化 token。
- A18 软绑定身份：携带合法 token 时忽略伪造的 ownerId；无 token 时回退 payload.ownerId（演示链路）。
- A19 admin 端点在未设置 ADMIN_API_KEY 时 fail-open 放行，设置后强制校验 X-Admin-Key。
- A20 校方 demo 账户口令为随机强口令哈希，不再为空明文。
"""

import os
import sqlite3
import threading
from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    from app.main import create_app

    db_url = f"sqlite:///{tmp_path / 'demo.sqlite3'}"
    return TestClient(create_app(database_url=db_url))


def bootstrap_user(client: TestClient, owner_id: str) -> dict:
    """完成 登录 -> 测评 -> 领宠物 的标准前置，返回 demo-login 的 token。"""
    login = client.post("/api/auth/demo-login", json={"ownerId": owner_id})
    token = login.json()["token"]
    client.post("/api/assessment/submit", json={"ownerId": owner_id, "answers": []})
    client.post("/api/pets/claim", json={"ownerId": owner_id, "petType": "反诈小卫士"})
    return token


# ---------------------------------------------------------------------------
# A17 + A21：登录下发 token，且后端可正常导入/启动
# ---------------------------------------------------------------------------
def test_demo_login_issues_token_and_app_imports(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    login = client.post("/api/auth/demo-login", json={"ownerId": "U-TOKEN01"})
    assert login.status_code == 200
    token = login.json().get("token")
    assert isinstance(token, str) and token, "A17: demo-login 必须返回非空 token"


# ---------------------------------------------------------------------------
# A18：软绑定身份——合法 token 优先于伪造的 ownerId
# ---------------------------------------------------------------------------
def test_soft_binding_ignores_forged_owner_id_with_valid_token(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    real = "U-REAL"
    evil = "U-EVIL"
    token = bootstrap_user(client, real)

    # 携带合法 token，但 payload.ownerId 伪造为 U-EVIL：
    # 服务端应以 token 真实持有者 U-REAL 为准，绝不把奖励记到 U-EVIL。
    resp = client.post(
        "/api/training/submit",
        json={
            "ownerId": evil,
            "taskId": "ai-face",
            "answers": [{"questionId": "ai-face-q1", "answer": ["A", "B", "C", "D"]}],
            "mode": "recommended",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rewardStatus"] == "AWARDED"
    # 关键断言：返回的宠物归属真实用户，而非伪造的 ownerId
    assert body["pet"]["ownerId"] == real, "A18: 软绑定必须忽略伪造的 ownerId"
    assert body["pet"]["ownerId"] != evil


# ---------------------------------------------------------------------------
# A18：无 token 时回退 payload.ownerId（演示链路默认行为不变）
# ---------------------------------------------------------------------------
def test_no_token_falls_back_to_payload_owner_id(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    owner = "U-FALLBACK"
    bootstrap_user(client, owner)

    resp = client.post(
        "/api/training/submit",
        json={
            "ownerId": owner,
            "taskId": "ai-face",
            "answers": [{"questionId": "ai-face-q1", "answer": ["A", "B", "C", "D"]}],
            "mode": "recommended",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rewardStatus"] == "AWARDED"
    assert body["pet"]["ownerId"] == owner


# ---------------------------------------------------------------------------
# A19：admin 端点 fail-open（未设置 ADMIN_API_KEY 时放行）
# ---------------------------------------------------------------------------
def test_admin_endpoints_fail_open_without_key(tmp_path: Path) -> None:
    # 确保运行时未设置 key
    os.environ.pop("ADMIN_API_KEY", None)
    client = make_client(tmp_path)
    resp = client.get("/api/admin/rules")
    assert resp.status_code == 200, "A19: 未设置 ADMIN_API_KEY 时 admin 应 fail-open 放行"


# ---------------------------------------------------------------------------
# A19：admin 端点设置 ADMIN_API_KEY 后强制校验
# ---------------------------------------------------------------------------
def test_admin_endpoints_require_key_when_set(tmp_path: Path) -> None:
    os.environ["ADMIN_API_KEY"] = "secret-123"
    try:
        client = make_client(tmp_path)
        # 缺失 key -> 401
        assert client.get("/api/admin/rules").status_code == 401
        # 错误 key -> 401
        assert (
            client.get("/api/admin/rules", headers={"X-Admin-Key": "wrong"}).status_code
            == 401
        )
        # 正确 key -> 200
        assert (
            client.get(
                "/api/admin/rules", headers={"X-Admin-Key": "secret-123"}
            ).status_code
            == 200
        )
    finally:
        os.environ.pop("ADMIN_API_KEY", None)


# ---------------------------------------------------------------------------
# A20：校方 demo 账户口令为随机强口令哈希（非空明文）
# ---------------------------------------------------------------------------
def test_school_demo_password_is_hashed_not_empty(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    login = client.post("/api/school/demo-login")
    assert login.status_code == 200

    db_path = tmp_path / "demo.sqlite3"
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT password_hash FROM accounts WHERE username = 'school-demo'"
        ).fetchone()
    finally:
        conn.close()

    assert row is not None, "校方 demo 账户应已创建"
    password_hash = row[0]
    assert password_hash, "A20: 校方口令不得为空"
    # 哈希值应为较长十六进制串（sha256 64 位），而非原始口令
    assert len(password_hash) >= 40, "A20: 校方口令应为哈希值而非明文"


# ---------------------------------------------------------------------------
# A14：并发提交只发奖一次（进程内锁保证幂等）
# ---------------------------------------------------------------------------
def test_concurrent_submit_awards_only_once(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    owner = "U-CONCURRENT"
    bootstrap_user(client, owner)

    payload = {
        "ownerId": owner,
        "taskId": "ai-face",
        "answers": [{"questionId": "ai-face-q1", "answer": ["A", "B", "C", "D"]}],
        "mode": "recommended",
    }

    results: list[dict] = []
    lock = threading.Lock()

    def fire() -> None:
        r = client.post("/api/training/submit", json=payload)
        with lock:
            results.append(r.json())

    threads = [threading.Thread(target=fire) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    awarded = [b for b in results if b.get("rewardStatus") == "AWARDED"]
    no_reward = [b for b in results if b.get("rewardStatus") == "NO_REWARD"]
    assert len(awarded) == 1, f"A14: 并发提交必须恰好发奖一次，实际 {len(awarded)} 次"
    assert len(no_reward) == 7, "A14: 其余并发提交应被幂等拦截为 NO_REWARD"
