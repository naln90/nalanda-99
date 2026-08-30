# -*- coding: utf-8 -*-
"""清空主题内容并按「AI 素养与智能工具应用」主题重建演示库。

策略（用户确认）：
- 保留 accounts / users（users 进度标志复位）
- 清空全部主题内容、种子与用户进度表
- 重新运行 seed_database（多主题均衡种子）
- 预置「AI 素养与智能工具应用」主题任务包（create → generate → confirm）
- 学生演示账号自动加入主题；发放初始演示盾能 100

运行方式（backend 目录下）：
  python rebuild_theme_data.py
"""
import datetime
import shutil
import sqlite3

DB = "data/demo_corrected.sqlite3"
BACKUP = "data/demo_corrected.sqlite3.bak.aitheme.20260827"

THEME_TITLE = "AI 素养与智能工具应用"

THEME_PAYLOAD = {
    "title": THEME_TITLE,
    "description": "围绕提示词技巧、AI 伦理与合规、AI 辅助学习规范，"
    "系统提升 AI 素养并产出可展示的学习成果。",
    "periodDays": 7,
    "targetAudience": "全校学生",
    "scope": "全校",
    "baseRequired": "提示词基础、AI 生成内容辨识、AI 学术使用规范",
    "electiveDirection": "AI 工具实战、伦理案例讨论、成果创作",
    "expectedOutcome": "AI 学习成果卡或应用案例海报",
    "baseAssessment": "AI 素养基础测评",
}

# 需要清空的表（保留 accounts / users）
CONTENT_TABLES = [
    # 种子/配置
    "pet_pool", "growth_rules", "training_tasks", "training_questions",
    "knowledge_items", "fraud_cases", "question_metadata",
    "scenario_templates", "scenario_turns", "risk_test_samples",
    "prompt_versions", "ai_call_logs",
    # 主题/任务包
    "themes", "task_packages", "task_package_items",
    "learning_goals", "learning_plans", "learning_plan_extensions",
    "learning_plan_items",
    # 用户内容/进度
    "pets", "training_records", "suspicious_checks",
    "assessment_results", "assessment_sessions", "assessment_answers",
    "ability_snapshots", "ability_events",
    "learning_artifacts", "learning_artifact_versions",
    "learning_market_listings", "market_likes", "market_favorites",
    "market_ratings", "market_comments",
    "campus_activities", "campus_activity_unlocks", "activity_contributions",
    "energy_ledgers", "scenario_training_sessions", "evidence_records",
    "review_reports", "wrong_items", "retrain_tasks", "retrain_schedules",
    "notifications", "teams", "team_members", "milestones", "project_issues",
    "friendships",
]


def phase1_clear() -> None:
    shutil.copyfile(DB, BACKUP)
    print(f"[备份] {DB} -> {BACKUP}")

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys=OFF")

    total = 0
    for tbl in CONTENT_TABLES:
        try:
            cur.execute(f"DELETE FROM {tbl}")
        except sqlite3.OperationalError as e:
            print(f"  [跳过] {tbl}: {e}")
            continue
        n = cur.rowcount
        if n:
            print(f"  DELETE {tbl}: {n} 行")
        total += n

    # 复位所有用户进度标志（保留账号行与令牌）
    cur.execute("UPDATE users SET has_completed_assessment=0, has_pet=0")
    con.commit()
    con.close()
    print(f"[清空] 共删除 {total} 行；users 进度标志已复位")


def phase2_rebuild() -> None:
    from app import database
    database.init(f"sqlite:///{DB}")
    from app import seed
    from app import theme_service

    db = database.SessionLocal()
    try:
        seed.seed_database(db)
        print("[种子] seed_database 完成（宠物池/训练任务/题库/知识库/排行榜）")

        # 校方账号
        school_owner = db.execute(
            __import__("sqlalchemy").text(
                "SELECT owner_id FROM accounts WHERE role='school' LIMIT 1"
            )
        ).scalar()
        if not school_owner:
            raise SystemExit("未找到校方账号（role=school），中止")

        theme = theme_service.create_theme(db, school_owner, THEME_PAYLOAD)
        theme = theme_service.generate_theme_plan(db, theme.id)
        result = theme_service.confirm_theme(db, theme.id)
        print(f"[主题] 已发布：{theme.title}（id={theme.id}, plan={result['plan'].id}）")

        # 学生演示账号加入主题
        student_owners = [
            r[0] for r in db.execute(
                __import__("sqlalchemy").text(
                    "SELECT owner_id FROM accounts WHERE role='student'"
                )
            ).fetchall()
        ]
        for owner in student_owners:
            plan = theme_service.join_theme(db, owner, theme.id)
            print(f"[加入] {owner} -> 任务包 {plan.id}")

        # 发放初始演示盾能
        now_iso = datetime.datetime.utcnow().isoformat()
        for owner in student_owners:
            db.execute(
                __import__("sqlalchemy").text(
                    "INSERT INTO energy_ledgers "
                    "(owner_id, tx_type, source_ref, delta, cumulative_after, "
                    " available_after, contributed_after, note, created_at) "
                    "VALUES (:o, 'init_grant', 'seed', 100, 100, 100, 0, '初始演示盾能', :t)"
                ),
                {"o": owner, "t": now_iso},
            )
        db.commit()
        print(f"[盾能] 已为 {len(student_owners)} 个学生账号发放初始 100 盾能")
    finally:
        db.close()


def phase3_verify() -> None:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    checks = {
        "themes": "SELECT COUNT(*) FROM themes",
        "published themes": "SELECT COUNT(*) FROM themes WHERE status='published'",
        "learning_plans": "SELECT COUNT(*) FROM learning_plans",
        "plan_items": "SELECT COUNT(*) FROM learning_plan_items",
        "training_tasks": "SELECT COUNT(*) FROM training_tasks",
        "training_questions": "SELECT COUNT(*) FROM training_questions",
        "knowledge_items": "SELECT COUNT(*) FROM knowledge_items",
        "knowledge 反诈安全": "SELECT COUNT(*) FROM knowledge_items WHERE theme='反诈安全'",
        "pets(排行榜)": "SELECT COUNT(*) FROM pets",
        "student energy": "SELECT owner_id, available_after FROM energy_ledgers",
    }
    for name, sql in checks.items():
        rows = cur.execute(sql).fetchall()
        print(f"[验证] {name}: {rows}")
    con.close()


if __name__ == "__main__":
    phase1_clear()
    phase2_rebuild()
    phase3_verify()
    print("[完成] 主题内容已按「%s」重建" % THEME_TITLE)
