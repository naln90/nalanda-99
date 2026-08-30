"""清空并重建知识库：删除 knowledge_items 全部数据后调用 seed_database 重新灌入。"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import delete

import os

from app import database
from app.seed import seed_database
from app.models import KnowledgeItem

DB_URL = "sqlite:///./data/demo_corrected.sqlite3"


def main():
    database.init(database_url=DB_URL)
    session = database.SessionLocal()

    before = session.query(KnowledgeItem).count()
    session.execute(delete(KnowledgeItem))
    session.commit()
    after_clear = session.query(KnowledgeItem).count()
    print(f"清空前: {before} 条; 清空后: {after_clear} 条")

    seed_database(session)
    session.commit()

    final = session.query(KnowledgeItem).count()
    print(f"重建完成，现有: {final} 条")

    from collections import Counter
    rows = session.query(KnowledgeItem.theme).all()
    c = Counter(theme for (theme,) in rows)
    for theme, n in c.most_common():
        print(f"  {theme}: {n}")

    session.close()


if __name__ == "__main__":
    main()
