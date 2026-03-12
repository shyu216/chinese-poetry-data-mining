#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本过渡脚本：将现有大文件转换为分片格式
支持从旧版单文件迁移到新版分片格式

使用方法:
    python scripts/migrate_to_chunked.py

功能:
    1. 检测现有大文件 (>100MB)
    2. 转换为分片格式 (~10MB/片)
    3. 生成分片清单 (manifest)
    4. 保留原有小文件不变
    5. 可选择删除或备份原大文件
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import pandas as pd
from pathlib import Path
import math
import shutil
from datetime import datetime

# 目标分片大小：约10MB
TARGET_CHUNK_SIZE = 10 * 1024 * 1024
# GitHub限制：100MB
GITHUB_SIZE_LIMIT = 100 * 1024 * 1024


def get_file_size_mb(file_path):
    """获取文件大小(MB)"""
    return file_path.stat().st_size / (1024 * 1024)


def get_file_size_bytes(file_path):
    """获取文件大小(字节)"""
    return file_path.stat().st_size


def backup_file(file_path):
    """备份文件"""
    backup_dir = file_path.parent / 'backup'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
    
    shutil.copy2(file_path, backup_path)
    print(f"  已备份: {backup_path}")
    return backup_path


def migrate_poems_json(input_path, output_dir, backup=True, delete_original=False):
    """
    迁移诗词JSON文件到分片格式
    
    Args:
        input_path: 输入文件路径
        output_dir: 输出目录
        backup: 是否备份原文件
        delete_original: 是否删除原文件
    """
    print(f"\n迁移诗词数据: {input_path}")
    
    if not input_path.exists():
        print(f"  ⚠️ 文件不存在: {input_path}")
        return None
    
    file_size = get_file_size_bytes(input_path)
    if file_size < GITHUB_SIZE_LIMIT:
        print(f"  ✅ 文件大小 {get_file_size_mb(input_path):.2f}MB < 100MB，无需分片")
        return None
    
    print(f"  📦 原文件大小: {get_file_size_mb(input_path):.2f}MB")
    
    # 备份
    if backup:
        backup_file(input_path)
    
    # 读取数据
    print("  📖 读取数据...")
    with open(input_path, 'r', encoding='utf-8') as f:
        poems = json.load(f)
    
    total_poems = len(poems)
    print(f"  📝 总诗词数: {total_poems}")
    
    # 计算分片大小
    test_chunk = json.dumps(poems[:1000], ensure_ascii=False)
    test_size = len(test_chunk.encode('utf-8'))
    poems_per_chunk = max(1, int(1000 * TARGET_CHUNK_SIZE / test_size))
    total_chunks = math.ceil(total_poems / poems_per_chunk)
    
    print(f"  🔢 每片诗词数: {poems_per_chunk}")
    print(f"  🔢 总分片数: {total_chunks}")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成分片
    manifest = {
        'version': '2.0',
        'migrated_from': str(input_path.name),
        'migrated_at': datetime.now().isoformat(),
        'total': total_poems,
        'chunks': total_chunks,
        'files': []
    }
    
    for i in range(total_chunks):
        start_idx = i * poems_per_chunk
        end_idx = min((i + 1) * poems_per_chunk, total_poems)
        chunk_poems = poems[start_idx:end_idx]
        
        # 保存分片
        chunk_file = output_dir / f'poems_chunk_{i:03d}.json'
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_poems, f, ensure_ascii=False)
        
        file_size_mb = get_file_size_mb(chunk_file)
        manifest['files'].append({
            'index': i,
            'file': f'poems_chunk_{i:03d}.json',
            'count': len(chunk_poems),
            'size_mb': round(file_size_mb, 2)
        })
        print(f"  ✅ 分片 {i+1}/{total_chunks}: {chunk_file.name} ({file_size_mb:.2f}MB)")
    
    # 保存manifest
    manifest_path = output_dir / 'poems_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Manifest: {manifest_path}")
    
    # 删除原文件
    if delete_original:
        input_path.unlink()
        print(f"  🗑️ 已删除原文件: {input_path}")
    else:
        # 重命名为 .backup
        backup_path = input_path.with_suffix('.json.backup')
        input_path.rename(backup_path)
        print(f"  📦 原文件已重命名为: {backup_path.name}")
    
    return manifest


def migrate_structure_csv(input_path, output_dir, backup=True, delete_original=False):
    """
    迁移结构CSV文件到分片格式
    
    Args:
        input_path: 输入文件路径
        output_dir: 输出目录
        backup: 是否备份原文件
        delete_original: 是否删除原文件
    """
    print(f"\n迁移结构数据: {input_path}")
    
    if not input_path.exists():
        print(f"  ⚠️ 文件不存在: {input_path}")
        return None
    
    file_size = get_file_size_bytes(input_path)
    if file_size < GITHUB_SIZE_LIMIT:
        print(f"  ✅ 文件大小 {get_file_size_mb(input_path):.2f}MB < 100MB，无需分片")
        return None
    
    print(f"  📦 原文件大小: {get_file_size_mb(input_path):.2f}MB")
    
    # 备份
    if backup:
        backup_file(input_path)
    
    # 读取数据
    print("  📖 读取数据...")
    df = pd.read_csv(input_path, low_memory=False)
    total_rows = len(df)
    
    print(f"  📝 总行数: {total_rows}")
    
    # 计算分片大小
    test_chunk = df.head(1000).to_csv(index=False)
    test_size = len(test_chunk.encode('utf-8'))
    rows_per_chunk = max(1, int(1000 * TARGET_CHUNK_SIZE / test_size))
    total_chunks = math.ceil(total_rows / rows_per_chunk)
    
    print(f"  🔢 每片行数: {rows_per_chunk}")
    print(f"  🔢 总分片数: {total_chunks}")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成分片
    manifest = {
        'version': '2.0',
        'migrated_from': str(input_path.name),
        'migrated_at': datetime.now().isoformat(),
        'total': total_rows,
        'chunks': total_chunks,
        'columns': list(df.columns),
        'files': []
    }
    
    for i in range(total_chunks):
        start_idx = i * rows_per_chunk
        end_idx = min((i + 1) * rows_per_chunk, total_rows)
        chunk_df = df.iloc[start_idx:end_idx]
        
        # 保存分片
        chunk_file = output_dir / f'structure_chunk_{i:03d}.csv'
        chunk_df.to_csv(chunk_file, index=False, encoding='utf-8')
        
        file_size_mb = get_file_size_mb(chunk_file)
        manifest['files'].append({
            'index': i,
            'file': f'structure_chunk_{i:03d}.csv',
            'count': len(chunk_df),
            'size_mb': round(file_size_mb, 2)
        })
        print(f"  ✅ 分片 {i+1}/{total_chunks}: {chunk_file.name} ({file_size_mb:.2f}MB)")
    
    # 保存manifest
    manifest_path = output_dir / 'structure_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Manifest: {manifest_path}")
    
    # 删除原文件
    if delete_original:
        input_path.unlink()
        print(f"  🗑️ 已删除原文件: {input_path}")
    else:
        # 重命名为 .backup
        backup_path = input_path.with_suffix('.csv.backup')
        input_path.rename(backup_path)
        print(f"  📦 原文件已重命名为: {backup_path.name}")
    
    return manifest


def scan_large_files(project_root):
    """扫描项目中的大文件"""
    print("\n" + "="*60)
    print("扫描大文件 (>100MB)")
    print("="*60)
    
    large_files = []
    
    # 扫描目录
    scan_dirs = [
        project_root / 'data' / 'structure_analysis',
        project_root / 'data' / 'github_pages' / 'data',
        project_root / 'data' / 'processed_data',
    ]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        
        for file_path in scan_dir.iterdir():
            if file_path.is_file():
                file_size = get_file_size_bytes(file_path)
                if file_size > GITHUB_SIZE_LIMIT:
                    large_files.append({
                        'path': file_path,
                        'size_mb': get_file_size_mb(file_path),
                        'type': file_path.suffix.lower()
                    })
                    print(f"  ⚠️  {file_path.name}: {get_file_size_mb(file_path):.2f}MB")
    
    if not large_files:
        print("  ✅ 未发现大文件")
    
    return large_files


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='版本过渡脚本：将大文件转换为分片格式')
    parser.add_argument('--no-backup', action='store_true', help='不备份原文件')
    parser.add_argument('--delete-original', action='store_true', help='删除原文件（默认重命名）')
    parser.add_argument('--scan-only', action='store_true', help='仅扫描，不执行迁移')
    parser.add_argument('--poems-only', action='store_true', help='仅迁移诗词数据')
    parser.add_argument('--structure-only', action='store_true', help='仅迁移结构数据')
    
    args = parser.parse_args()
    
    print("="*60)
    print("版本过渡脚本 v2.0")
    print("将大文件转换为分片格式")
    print("="*60)
    
    project_root = Path(__file__).parent.parent
    
    # 扫描大文件
    large_files = scan_large_files(project_root)
    
    if args.scan_only:
        print("\n扫描完成，未执行迁移")
        return
    
    if not large_files:
        print("\n无需迁移")
        return
    
    # 确认执行
    print("\n" + "="*60)
    response = input("是否执行迁移? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("取消迁移")
        return
    
    # 执行迁移
    print("\n" + "="*60)
    print("开始迁移")
    print("="*60)
    
    backup = not args.no_backup
    delete_original = args.delete_original
    
    # 迁移诗词数据
    if not args.structure_only:
        poems_json = project_root / 'data' / 'github_pages' / 'data' / 'poems.json'
        if poems_json.exists() and get_file_size_bytes(poems_json) > GITHUB_SIZE_LIMIT:
            output_dir = project_root / 'data' / 'github_pages' / 'data'
            migrate_poems_json(poems_json, output_dir, backup, delete_original)
    
    # 迁移结构数据
    if not args.poems_only:
        structure_csv = project_root / 'data' / 'structure_analysis' / 'poetry_structure_full.csv'
        if structure_csv.exists() and get_file_size_bytes(structure_csv) > GITHUB_SIZE_LIMIT:
            output_dir = project_root / 'data' / 'github_pages' / 'data'
            migrate_structure_csv(structure_csv, output_dir, backup, delete_original)
    
    print("\n" + "="*60)
    print("迁移完成！")
    print("="*60)
    print("\n后续步骤:")
    print("1. 检查分片文件是否正确生成")
    print("2. 测试前端分片加载功能")
    print("3. 更新.gitignore忽略大文件")
    print("4. 提交代码到GitHub")


if __name__ == "__main__":
    main()
