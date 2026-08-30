# -*- coding: utf-8 -*-
import zipfile
import os
import shutil

zips = [
    ("守护犬", "守护犬五阶段360度形象图.zip"),
    ("数据探测员", "数据探测员五阶段360度形象图.zip"),
    ("反诈小卫士", "反诈小卫士五阶段360度形象图.zip"),
    ("巡逻机器人", "巡逻机器人五阶段360度形象图.zip"),
    ("灵巧兔", "灵巧兔五阶段360度形象图.zip"),
    ("校园猫", "校园猫五阶段360度形象图.zip"),
    ("麒麟", "麒麟五阶段360度形象图.zip"),
    ("玄鸟", "玄鸟五阶段高饱和度360度形象图.zip"),
    ("醒狮", "醒狮五阶段360度形象图.zip"),
]

downloads = r"C:\Users\33719\Downloads"
base = r"D:\个人\比赛\启智杯\启智杯参赛Demo包_防诈智研(1)\01_source_main_demo\fraud-pet-demo\设计参考\宠物形象原稿"

stage_names = {
    "01": "01_幼年态_Lv1-Lv3",
    "02": "02_学习态_Lv4-Lv7",
    "03": "03_成长态_Lv8-Lv12",
    "04": "04_进阶段_Lv13-Lv16",
    "05": "05_反诈守护者_Lv17-Lv20",
}

total = 0
for pet_name, zip_file in zips:
    zip_path = os.path.join(downloads, zip_file)
    pet_dir = os.path.join(base, pet_name)
    os.makedirs(pet_dir, exist_ok=True)
    # 只清理已有的图片文件（不删除子目录，避免安全拦截）
    for f in os.listdir(pet_dir):
        fp = os.path.join(pet_dir, f)
        if os.path.isfile(fp) and f.lower().endswith(('.png','.jpg','.jpeg','.webp')):
            try:
                os.remove(fp)
            except Exception:
                pass
    if not os.path.exists(zip_path):
        print(f"MISSING ZIP: {zip_path}")
        continue
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                fname = info.filename
                try:
                    fname_bytes = fname.encode('cp437')
                    for enc in ['gbk', 'utf-8']:
                        try:
                            fname = fname_bytes.decode(enc)
                            break
                        except Exception:
                            pass
                except Exception:
                    pass
                base_name = os.path.basename(fname)
                if not base_name or not base_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    continue
                prefix = base_name[:2]
                ext = os.path.splitext(base_name)[1]
                if prefix in stage_names:
                    out_name = stage_names[prefix] + ext
                else:
                    out_name = base_name
                out_path = os.path.join(pet_dir, out_name)
                with zf.open(info) as src, open(out_path, 'wb') as dst:
                    dst.write(src.read())
                total += 1
        count = len([f for f in os.listdir(pet_dir) if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])
        print(f"OK: {pet_name} -> {count} images")
    except Exception as e:
        print(f"ERROR {pet_name}: {e}")

print(f"TOTAL: {total} images extracted")
