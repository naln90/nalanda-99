"""一次性脚本：重置默认演示账号 U-2408** 的学习进度，保留账号与知识库种子。

操作策略：
- 仅清除 owner_id = 'U-2408**' 的全部学习/进度数据
- 复位 users 表该账号的 has_completed_assessment / has_pet 标志
- 校园活动进度按该用户实际投放量回退，保持计数一致
- 不触碰 accounts / knowledge_items / 各 seed/config 表
"""
import sqlite3
import datetime

DB = "data/demo.sqlite3"
OWNER = "U-2408**"

# 1) owner_id 直接命中的表
SIMPLE_OWNER_TABLES = [
    "pets", "training_records", "suspicious_checks", "assessment_results",
    "task_packages", "task_package_items", "learning_goals", "learning_plans",
    "learning_plan_extensions", "learning_plan_items", "learning_artifacts",
    "learning_market_listings", "campus_activity_unlocks", "energy_ledgers",
    "activity_contributions", "scenario_training_sessions", "retrain_tasks",
    "assessment_sessions", "assessment_answers", "ability_snapshots",
    "ability_events", "evidence_records", "review_reports", "wrong_items",
    "retrain_schedules", "market_likes", "market_favorites", "market_ratings",
    "market_comments", "notifications", "teams", "team_members",
    "project_issues",
]

# 2) 通过子查询关联删除的表
SUBQUERY_DELETES = [
    ("learning_artifact_versions",
     "artifact_id IN (SELECT id FROM learning_artifacts WHERE owner_id=?)"),
    ("milestones",
     "team_id IN (SELECT id FROM teams WHERE owner_id=?)"),
]

# 3) 双字段命中（好友关系）
FRIENDSHIP_SQL = (
    "DELETE FROM friendships WHERE requester_id=? OR addressee_id=?"
)


def main():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys=OFF")  # 避免删除顺序导致的 FK 约束报错
    cur = con.cursor()

    print(f"[{datetime.datetime.now():%H:%M:%S}] 开始重置 owner_id={OWNER!r}")

    # 重置前计数
    cur.execute("SELECT has_completed_assessment, has_pet FROM users WHERE owner_id=?", (OWNER,))
    before = cur.fetchone()
    print(f"  users 行重置前: {before}")

    total_deleted = 0
    for tbl in SIMPLE_OWNER_TABLES:
        try:
            cur.execute(f"DELETE FROM {tbl} WHERE owner_id=?", (OWNER,))
        except sqlite3.OperationalError as e:
            print(f"  [跳过] {tbl}: {e}")
            continue
        n = cur.rowcount
        if n:
            print(f"  DELETE {tbl}: {n} 行")
        total_deleted += n

    for tbl, where in SUBQUERY_DELETES:
        cur.execute(f"DELETE FROM {tbl} WHERE {where}", (OWNER,))
        n = cur.rowcount
        if n:
            print(f"  DELETE {tbl}: {n} 行")
        total_deleted += n

    cur.execute(FRIENDSHIP_SQL, (OWNER, OWNER))
    n = cur.rowcount
    if n:
        print(f"  DELETE friendships: {n} 行")
    total_deleted += n

    # 校园活动：回退该用户投放量，保持计数一致
    cur.execute(
        "SELECT activity_id, SUM(amount), COUNT(*) FROM activity_contributions "
        "WHERE owner_id=? GROUP BY activity_id",
        (OWNER,),
    )
    for activity_id, total_amt, _cnt in cur.fetchall():
        cur.execute(
            "UPDATE campus_activities SET "
            "current_progress = MAX(0, current_progress - ?), "
            "contributor_count = MAX(0, contributor_count - 1) "
            "WHERE id=?",
            (total_amt, activity_id),
        )
        print(f"  回退活动 {activity_id}: 进度 -{total_amt}, 参与人数 -1")

    # 复位 users 标志（保留账号行，owner_id 稳定）
    cur.execute(
        "UPDATE users SET has_completed_assessment=0, has_pet=0 "
        "WHERE owner_id=?",
        (OWNER,),
    )
    print(f"  UPDATE users: 复位 has_completed_assessment/has_pet")

    # 发放初始演示盾能，保证重置后账号仍可演示「守护共建 / 投放盾能」
    # （energy_ledgers 已在上文随进度一并清空，这里重新写入一笔初始发放）
    cur.execute("SELECT COUNT(*) FROM energy_ledgers WHERE owner_id=?", (OWNER,))
    if cur.fetchone()[0] == 0:
        now_iso = datetime.datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO energy_ledgers "
            "(owner_id, tx_type, source_ref, delta, cumulative_after, "
            " available_after, contributed_after, note, created_at) "
            "VALUES (?, 'init_grant', 'seed', 100, 100, 100, 0, '初始演示盾能', ?)",
            (OWNER, now_iso),
        )
        print(f"  发放初始演示盾能 100 给 {OWNER!r}")

    con.commit()

    # 验证
    cur.execute("SELECT has_completed_assessment, has_pet FROM users WHERE owner_id=?", (OWNER,))
    after = cur.fetchone()
    print(f"  users 行重置后: {after}")
    cur.execute("SELECT COUNT(*) FROM pets WHERE owner_id=?", (OWNER,))
    pets_left = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM assessment_results WHERE owner_id=?", (OWNER,))
    assess_left = cur.fetchone()[0]
    print(f"  残留校验: pets={pets_left}, assessment_results={assess_left}")

    print(f"[{datetime.datetime.now():%H:%M:%S}] 完成。共清除 {total_deleted} 行进度数据。")
    con.close()


if __name__ == "__main__":
    main()
