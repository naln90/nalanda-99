# -*- coding: utf-8 -*-
import os, shutil

src_base = r"D:\个人\比赛\启智杯\启智杯参赛Demo包_防诈智研(1)\01_source_main_demo\fraud-pet-demo\设计参考\宠物形象原稿"
dst_base = r"D:\个人\比赛\启智杯\启智杯参赛Demo包_防诈智研(1)\01_source_main_demo\fraud-pet-demo\public\pets"

pets = ["守护犬","数据探测员","反诈小卫士","巡逻机器人","灵巧兔","校园猫","麒麟","玄鸟","醒狮"]

os.makedirs(dst_base, exist_ok=True)
for pet in pets:
    src_dir = os.path.join(src_base, pet)
    dst_dir = os.path.join(dst_base, pet)
    os.makedirs(dst_dir, exist_ok=True)
    if not os.path.exists(src_dir):
        print(f"MISSING src: {src_dir}")
        continue
    for f in os.listdir(src_dir):
        if f.lower().endswith(('.png','.jpg','.jpeg','.webp')):
            shutil.copy2(os.path.join(src_dir, f), os.path.join(dst_dir, f))
    count = len([f for f in os.listdir(dst_dir) if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])
    print(f"OK: {pet} -> {count} images")

print("Done")
