#!/usr/bin/env python3
"""
script: 01_correct_dynasty.py
stage: P1-数据预处理
artifact: 朝代修正后的预处理数据
purpose: 按规则修复预处理结果中的朝代字段异常。
inputs:
- results/preprocessed
outputs:
- results/preprocessed
depends_on:
- preprocess_poems.py
develop_date: 2026-03-17
last_modified_date: 2026-03-24
"""
import json
import csv
import sys
from pathlib import Path
from collections import defaultdict
def build_id_to_dynasty_mapping(data_dir: Path) -> dict:
    """
    读取全唐诗和宋词目录下的所有 JSON 文件，建立诗词 ID 到朝代的映射。
    文件名格式:
    - poet.song.*.json -> 宋
    - poet.tang.*.json -> 唐
    - ci.song.*.json -> 宋 (宋词)
    """
    id_to_dynasty = {}
    # 处理全唐诗目录
    quan_tang_shi_dir = data_dir / "chinese-poetry" / "全唐诗"
    if quan_tang_shi_dir.exists():
        json_files = list(quan_tang_shi_dir.glob("poet.*.json"))
        print(f"找到 {len(json_files)} 个全唐诗 JSON 文件")
        for idx, file in enumerate(json_files, 1):
            # 从文件名判断朝代
            if ".song." in file.name:
                dynasty = "宋"
            elif ".tang." in file.name:
                dynasty = "唐"
            else:
                print(f"  跳过未知类型文件: {file.name}")
                continue
            try:
                with open(file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for item in items:
                        poem_id = item.get("id", "")
                        if poem_id:
                            id_to_dynasty[poem_id] = dynasty
            except Exception as e:
                print(f"  错误: 无法读取 {file}: {e}")
            if idx % 50 == 0:
                print(f"  已处理 {idx}/{len(json_files)} 个文件，当前映射表大小: {len(id_to_dynasty)}")
    else:
        print(f"警告: 目录不存在 {quan_tang_shi_dir}")
    # 处理宋词目录
    song_ci_dir = data_dir / "chinese-poetry" / "宋词"
    if song_ci_dir.exists():
        json_files = list(song_ci_dir.glob("ci.song.*.json"))
        print(f"找到 {len(json_files)} 个宋词 JSON 文件")
        for idx, file in enumerate(json_files, 1):
            dynasty = "宋"  # 宋词都是宋代的
            try:
                with open(file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for item in items:
                        poem_id = item.get("id", "")
                        if poem_id:
                            id_to_dynasty[poem_id] = dynasty
            except Exception as e:
                print(f"  错误: 无法读取 {file}: {e}")
            if idx % 50 == 0:
                print(f"  已处理 {idx}/{len(json_files)} 个文件，当前映射表大小: {len(id_to_dynasty)}")
    else:
        print(f"警告: 目录不存在 {song_ci_dir}")
    print(f"\n共建立 {len(id_to_dynasty)} 条 ID->朝代 映射")
    # 统计各朝代数量
    dynasty_counts = defaultdict(int)
    for d in id_to_dynasty.values():
        dynasty_counts[d] += 1
    print("朝代分布:")
    for dynasty, count in sorted(dynasty_counts.items()):
        print(f"  {dynasty}: {count}")
    return id_to_dynasty
def update_csv_file(csv_path: Path, id_to_dynasty: dict) -> tuple:
    """
    更新单个 CSV 文件中的 dynasty 字段。
    Returns:
        (更新行数, 未匹配行数)
    """
    updated_count = 0
    not_found_count = 0
    rows = []
    # 使用 utf-8-sig 处理可能的 BOM
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            poem_id = row.get("id", "")
            if poem_id in id_to_dynasty:
                new_dynasty = id_to_dynasty[poem_id]
                if row.get("dynasty") != new_dynasty:
                    row["dynasty"] = new_dynasty
                    updated_count += 1
            else:
                not_found_count += 1
            rows.append(row)
    # 写回文件
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return updated_count, not_found_count
def update_all_csv_files(preprocessed_dir: Path, id_to_dynasty: dict):
    """更新所有 CSV 文件中的 dynasty 字段。"""
    csv_files = sorted(preprocessed_dir.glob("poems_chunk_*.csv"))
    print(f"\n找到 {len(csv_files)} 个 CSV 文件需要更新")
    total_updated = 0
    total_not_found = 0
    for idx, csv_file in enumerate(csv_files, 1):
        updated, not_found = update_csv_file(csv_file, id_to_dynasty)
        total_updated += updated
        total_not_found += not_found
        if updated > 0:
            print(f"  [{idx}/{len(csv_files)}] {csv_file.name}: 更新 {updated} 行")
        elif not_found > 0 and idx <= 5:  # 只显示前5个未匹配的文件
            print(f"  [{idx}/{len(csv_files)}] {csv_file.name}: 未匹配 {not_found} 行")
        elif idx % 50 == 0:
            print(f"  [{idx}/{len(csv_files)}] {csv_file.name}: 处理完成")
    print(f"\nCSV 更新完成: 共更新 {total_updated} 行, 未匹配 {total_not_found} 行")
    return total_updated, total_not_found
def update_meta_json(meta_path: Path, preprocessed_dir: Path):
    """更新 meta JSON 文件中的 dynasty 统计信息。"""
    print(f"\n更新 meta 文件: {meta_path}")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    # 重新统计每个 chunk 的朝代分布
    for chunk_info in meta.get("chunks", []):
        chunk_file = chunk_info.get("file", "")
        chunk_path = preprocessed_dir / chunk_file
        if not chunk_path.exists():
            continue
        dynasty_counts = defaultdict(int)
        with open(chunk_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dynasty = row.get("dynasty", "")
                if dynasty:
                    dynasty_counts[dynasty] += 1
        # 更新 chunk 的 dynasties 字段
        chunk_info["dynasties"] = sorted(dynasty_counts.keys()) if dynasty_counts else ["唐"]
    # 重新统计全局朝代分布
    all_dynasties = set()
    for chunk_info in meta.get("chunks", []):
        all_dynasties.update(chunk_info.get("dynasties", []))
    meta["stats"]["dynasties"] = sorted(all_dynasties)
    # 写回文件
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Meta 文件更新完成")
    print(f"全局朝代分布: {meta['stats']['dynasties']}")
def verify_ids_match(csv_path: Path, id_to_dynasty: dict, sample_size: int = 5):
    """验证 CSV 中的 ID 是否在映射表中存在"""
    print(f"\n验证 ID 匹配情况 (样本: {csv_path.name}):")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= sample_size:
                break
            poem_id = row.get("id", "")
            dynasty = row.get("dynasty", "")
            mapped_dynasty = id_to_dynasty.get(poem_id, "未找到")
            match_status = "✓" if poem_id in id_to_dynasty else "✗"
            print(f"  {match_status} ID: {poem_id[:30]}... | CSV朝代: {dynasty} | 映射朝代: {mapped_dynasty}")
def main():
    # 设置路径
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    preprocessed_dir = project_root / "results" / "preprocessed"
    meta_path = preprocessed_dir / "poems_chunk_meta.json"
    print("=" * 60)
    print("诗词 Dynasty 字段修正工具")
    print("=" * 60)
    # 步骤 1: 建立 ID->朝代 映射
    print("\n步骤 1: 从原始 JSON 文件建立 ID->朝代 映射...")
    id_to_dynasty = build_id_to_dynasty_mapping(data_dir)
    if not id_to_dynasty:
        print("错误: 无法建立映射表")
        sys.exit(1)
    # 验证 ID 匹配情况
    sample_csv = preprocessed_dir / "poems_chunk_0001.csv"
    if sample_csv.exists():
        verify_ids_match(sample_csv, id_to_dynasty)
    # 步骤 2: 更新所有 CSV 文件
    print("\n步骤 2: 更新 CSV 文件...")
    update_all_csv_files(preprocessed_dir, id_to_dynasty)
    # 步骤 3: 更新 meta JSON
    print("\n步骤 3: 更新 meta JSON 文件...")
    update_meta_json(meta_path, preprocessed_dir)
    print("\n" + "=" * 60)
    print("修正完成!")
    print("=" * 60)
if __name__ == "__main__":
    main()
