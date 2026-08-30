"""按主题从 Pexels 拉取真实、可商用的视频直链并写入 video_library 表。

这是「微课视频库」方案 (a) 中「Pexels/Pixabay 直链抓取」的正式落地工具：
- 不下载大文件，仅抓取 Pexels 返回的视频直链（video_files[].link）存入数据库；
- 按主题 upsert，运行一次即把对应主题的占位视频替换为真实主题视频；
- 未配置 API Key 或运行环境无外网时，脚本安全退出，不破坏已存在的种子数据
  （backend/app/seed.py 中的 CC0 兜底视频继续生效，前端降级/播放不受影响）。

使用方法
--------
1. 免费申请 Pexels API Key：https://www.pexels.com/api/ （注册后在 Dashboard 生成）
2. 在项目 backend 目录下运行：
       PEXELS_API_KEY=你的key \
       DATABASE_URL="sqlite:///./data/demo_corrected.sqlite3" \
       python fetch_videos.py
   或仅抓取单个主题：
       python fetch_videos.py --theme 消防安全
"""

from __future__ import annotations

import argparse
import os
import sys

import requests

# 复用项目既有数据库基础设施（引擎/Session 单例）
from app.database import init, SessionLocal  # noqa: E402
from app.models import VideoLibrary  # noqa: E402

PEXELS_API = "https://api.pexels.com/videos/search"
# 每个主题对应的 Pexels 英文检索词（Pexels 检索以英文最稳定）
THEME_QUERIES: dict[str, str] = {
    "AI素养与智能工具应用": "artificial intelligence technology",
    "反诈安全": "online scam warning security",
    "网络安全": "cyber security network",
    "心理健康": "meditation calm wellness",
    "消防安全": "fire safety extinguisher",
    "交通安全": "city traffic road safety",
    "求职就业": "job interview career office",
    "金融素养": "personal finance money saving",
    "学术诚信": "student study library",
    "个人信息保护": "privacy data protection",
    "校园安全": "university campus students",
    "应急避险": "emergency first aid",
}


def _pick_file(video_files: list[dict]) -> dict | None:
    """从 Pexels 返回的多个分辨率里挑一个适合网页播放的（≤1080p，优先接近 720p）。"""
    if not video_files:
        return None
    candidates = [f for f in video_files if f.get("width", 0) <= 1920 and f.get("height", 0) <= 1080]
    pool = candidates or video_files
    # 优先选最接近 1280x720 的，避免超大文件拖慢加载
    pool.sort(key=lambda f: abs((f.get("width", 0) or 0) - 1280) + abs((f.get("height", 0) or 0) - 720))
    return pool[0]


def fetch_pexels(query: str, api_key: str, per_page: int = 3) -> dict | None:
    """调用 Pexels 搜索接口，返回挑选出的 (url, duration, width, height)。"""
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "orientation": "landscape"}
    try:
        resp = requests.get(PEXELS_API, headers=headers, params=params, timeout=20)
    except requests.RequestException as exc:
        print(f"  [跳过] 网络请求失败（{query}）：{exc}")
        return None
    if resp.status_code != 200:
        print(f"  [跳过] Pexels 接口返回 {resp.status_code}（{query}）：{resp.text[:120]}")
        return None
    data = resp.json()
    videos = data.get("videos", [])
    if not videos:
        print(f"  [跳过] 未检索到视频（{query}）")
        return None
    for video in videos:
        picked = _pick_file(video.get("video_files", []))
        if picked and picked.get("link"):
            return {
                "url": picked["link"],
                "duration": int((video.get("duration") or 0)),
                "width": picked.get("width") or 0,
                "height": picked.get("height") or 0,
                "page": video.get("url", ""),
                "title": (video.get("user") or {}).get("name", "Pexels"),
            }
    return None


def upsert_video(db, theme: str, query: str, api_key: str) -> bool:
    """为一个主题抓取并写入/更新 video_library 行；成功返回 True。"""
    info = fetch_pexels(query, api_key)
    if not info:
        return False
    existing = db.query(VideoLibrary).filter(VideoLibrary.theme == theme).first()
    if existing:
        existing.url = info["url"]
        existing.duration_seconds = info["duration"] or existing.duration_seconds
        existing.source = f"Pexels（{info['title']}）"
        existing.source_url = info["page"]
        existing.enabled = True
        print(f"  [更新] {theme} -> {info['url'][:70]}")
    else:
        db.add(
            VideoLibrary(
                theme=theme,
                keywords=query,
                title=f"{theme}导学",
                url=info["url"],
                duration_seconds=info["duration"] or 0,
                source=f"Pexels（{info['title']}）",
                source_url=info["page"],
                enabled=True,
            )
        )
        print(f"  [新增] {theme} -> {info['url'][:70]}")
    db.commit()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="从 Pexels 拉取主题视频直链到 video_library")
    parser.add_argument("--theme", help="仅抓取指定主题（默认全部）", default=None)
    args = parser.parse_args()

    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("未设置 PEXELS_API_KEY，无法抓取真实视频。")
        print("申请免费 Key：https://www.pexels.com/api/")
        print("已保留 seed.py 中的 CC0 兜底视频，demo 仍可正常播放。")
        return 0

    # 初始化数据库（与运行后端时一致的 DATABASE_URL）
    init(os.getenv("DATABASE_URL"))
    if SessionLocal is None:
        print("数据库初始化失败。")
        return 1

    targets = {args.theme: THEME_QUERIES[args.theme]} if args.theme else THEME_QUERIES
    ok, fail = 0, 0
    with SessionLocal() as db:
        for theme, query in targets.items():
            print(f"主题：{theme}（检索词：{query}）")
            try:
                if upsert_video(db, theme, query, api_key):
                    ok += 1
                else:
                    fail += 1
            except Exception as exc:  # 单主题失败不影响其余
                db.rollback()
                print(f"  [异常] {theme}：{exc}")
                fail += 1
    print(f"\n完成：成功 {ok} 个，跳过/失败 {fail} 个。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
