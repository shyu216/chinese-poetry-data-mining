#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出数据用于GitHub Pages (分片版)
- 分片存储：每个文件约10MB
- 压缩
- 精简字段
- 生成manifest.json记录分片信息
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import gzip
import pandas as pd
from pathlib import Path
import math

# 目标分片大小：约10MB (10 * 1024 * 1024 bytes)
TARGET_CHUNK_SIZE = 10 * 1024 * 1024


def get_file_size_mb(file_path):
    """获取文件大小(MB)"""
    return file_path.stat().st_size / (1024 * 1024)


def export_poems_chunked():
    """导出诗词数据（分片版）"""
    print("导出诗词数据（分片）...")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_dir = project_root / "data" / "github_pages" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取CSV
    df = pd.read_csv(data_path, low_memory=False)
    total_poems = len(df)
    
    # 精简字段
    poems = []
    for _, row in df.iterrows():
        poem = {
            'i': str(row['id']),
            't': row['title'],
            'a': row['author'],
            'd': row['dynasty'],
            'g': row['genre'],
            'p': row['poem_type'],
            'm': row['meter_pattern'],
            'l': row['lines'].split('|') if isinstance(row['lines'], str) else [],
        }
        poems.append(poem)
    
    # 计算分片数量
    # 先测试一个文件的大小
    test_chunk = json.dumps(poems[:1000], ensure_ascii=False)
    test_size = len(test_chunk.encode('utf-8'))
    poems_per_chunk = max(1, int(1000 * TARGET_CHUNK_SIZE / test_size))
    total_chunks = math.ceil(total_poems / poems_per_chunk)
    
    print(f"  总诗词数: {total_poems}")
    print(f"  每片诗词数: {poems_per_chunk}")
    print(f"  总分片数: {total_chunks}")
    
    # 生成分片
    manifest = {
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
        
        file_size = get_file_size_mb(chunk_file)
        manifest['files'].append({
            'index': i,
            'file': f'poems_chunk_{i:03d}.json',
            'count': len(chunk_poems),
            'size_mb': round(file_size, 2)
        })
        print(f"  分片 {i+1}/{total_chunks}: {chunk_file.name} ({file_size:.2f} MB, {len(chunk_poems)}首)")
    
    # 保存manifest
    manifest_path = output_dir / 'poems_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  Manifest: {manifest_path}")
    
    return manifest


def export_structure_csv_chunked():
    """导出结构分析数据（分片版）"""
    print("\n导出结构分析数据（分片）...")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_dir = project_root / "data" / "github_pages" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取CSV
    df = pd.read_csv(data_path, low_memory=False)
    total_rows = len(df)
    
    # 计算分片数量
    # 先测试一个文件的大小
    test_chunk = df.head(1000).to_csv(index=False)
    test_size = len(test_chunk.encode('utf-8'))
    rows_per_chunk = max(1, int(1000 * TARGET_CHUNK_SIZE / test_size))
    total_chunks = math.ceil(total_rows / rows_per_chunk)
    
    print(f"  总行数: {total_rows}")
    print(f"  每片行数: {rows_per_chunk}")
    print(f"  总分片数: {total_chunks}")
    
    # 生成分片
    manifest = {
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
        
        file_size = get_file_size_mb(chunk_file)
        manifest['files'].append({
            'index': i,
            'file': f'structure_chunk_{i:03d}.csv',
            'count': len(chunk_df),
            'size_mb': round(file_size, 2)
        })
        print(f"  分片 {i+1}/{total_chunks}: {chunk_file.name} ({file_size:.2f} MB, {len(chunk_df)}行)")
    
    # 保存manifest
    manifest_path = output_dir / 'structure_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  Manifest: {manifest_path}")
    
    return manifest


def export_sample_poems():
    """导出sample版诗词（用于演示）"""
    print("\n导出Sample版诗词...")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_sample.csv"
    output_path = project_root / "data" / "github_pages" / "data" / "poems_sample.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取CSV
    df = pd.read_csv(data_path, low_memory=False)
    
    poems = []
    for _, row in df.iterrows():
        poem = {
            'id': str(row['id']),
            'title': row['title'],
            'author': row['author'],
            'dynasty': row['dynasty'],
            'genre': row['genre'],
            'poem_type': row['poem_type'],
            'meter_pattern': row['meter_pattern'],
            'lines': row['lines'].split('|') if isinstance(row['lines'], str) else [],
        }
        poems.append(poem)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(poems, f, ensure_ascii=False)
    
    file_size = get_file_size_mb(output_path)
    print(f"  已保存: {output_path} ({file_size:.2f} MB)")
    print(f"  诗词数: {len(poems)}")


def export_meter_stats():
    """导出格律统计"""
    print("\n导出格律统计...")
    
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "meter_position_stats.json"
    output_path = project_root / "data" / "github_pages" / "data" / "meter_stats.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    
    file_size = get_file_size_mb(output_path)
    print(f"  已保存: {output_path} ({file_size:.2f} MB)")


def export_basic_stats():
    """导出基本统计"""
    print("\n导出基本统计...")
    
    project_root = Path(__file__).parent.parent
    
    # 导出 full 版本统计
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_path = project_root / "data" / "github_pages" / "data" / "stats.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(data_path, low_memory=False)
    
    stats = {
        'total': len(df),
        'by_dynasty': df['dynasty'].value_counts().to_dict(),
        'by_genre': df['genre'].value_counts().to_dict(),
        'by_type': df['poem_type'].value_counts().to_dict(),
        'regular_count': int(df['is_regular'].sum()),
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False)
    
    file_size = get_file_size_mb(output_path)
    print(f"  已保存: {output_path} ({file_size:.2f} MB)")


def export_all_patterns():
    """导出所有格律模式"""
    print("\n导出所有格律模式...")
    
    project_root = Path(__file__).parent.parent
    
    # 导出 full 版本
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_path = project_root / "data" / "github_pages" / "data" / "all_patterns.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(data_path, low_memory=False)
    patterns = df['meter_pattern'].value_counts().to_dict()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False)
    
    file_size = get_file_size_mb(output_path)
    print(f"  已保存: {output_path} ({file_size:.2f} MB)")
    print(f"  格律模式数: {len(patterns)}")


def main():
    print("="*60)
    print("导出GitHub Pages数据 (分片版)")
    print("="*60)
    
    # 导出分片数据
    export_poems_chunked()
    export_structure_csv_chunked()
    
    # 导出其他数据
    export_sample_poems()
    export_meter_stats()
    export_basic_stats()
    export_all_patterns()
    
    print("\n" + "="*60)
    print("导出完成！")
    print("="*60)
    print("\n分片数据说明：")
    print("- poems_chunk_*.json: 诗词数据分片")
    print("- structure_chunk_*.csv: 结构数据分片")
    print("- poems_manifest.json: 诗词分片清单")
    print("- structure_manifest.json: 结构分片清单")
    print("\n前端加载时，先读取manifest，再按需加载分片")


if __name__ == "__main__":
    main()
