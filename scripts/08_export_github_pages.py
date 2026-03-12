#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出数据用于GitHub Pages (优化版)
- 压缩
- 分块
- 精简字段
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import gzip
import pandas as pd
from pathlib import Path


def export_poetry_data_compressed():
    """导出诗词数据（压缩版）"""
    print("导出诗词数据（压缩）...")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_path = project_root / "gh-pages" / "full" / "data" / "poems.json.gz"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取CSV
    df = pd.read_csv(data_path, low_memory=False)
    
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
    
    # 保存JSON
    json_str = json.dumps(poems, ensure_ascii=False)
    
    # 压缩
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        f.write(json_str)
    
    print(f"  已保存: {output_path}")
    
    return output_path


def export_sample_poems():
    """导出sample版诗词（用于演示）"""
    print("\n导出Sample版诗词...")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_sample.csv"
    output_path = project_root / "gh-pages" / "sample" / "data" / "poems_sample.json"
    
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
    
    print(f"  已保存: {output_path}")
    print(f"  诗词数: {len(poems)}")


def export_meter_stats():
    """导出格律统计"""
    print("\n导出格律统计...")
    
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "meter_position_stats.json"
    # 导出到 sample 和 full 两个版本
    for data_type in ['sample', 'full']:
        output_path = project_root / "gh-pages" / data_type / "data" / "meter_stats.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        print(f"  已保存: {output_path}")
    return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    
    print(f"  已保存: {output_path}")


def export_basic_stats():
    """导出基本统计"""
    print("\n导出基本统计...")
    
    project_root = Path(__file__).parent.parent
    
    # 导出 full 版本统计
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_path = project_root / "gh-pages" / "full" / "data" / "stats.json"
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
    
    print(f"  已保存 (full): {output_path}")
    
    # 导出 sample 版本统计
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_sample.csv"
    output_path = project_root / "gh-pages" / "sample" / "data" / "stats.json"
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
    
    print(f"  已保存 (sample): {output_path}")
    
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
    
    print(f"  已保存: {output_path}")


def export_all_patterns():
    """导出所有格律模式"""
    print("\n导出所有格律模式...")
    
    project_root = Path(__file__).parent.parent
    
    # 导出 full 版本
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    output_path = project_root / "gh-pages" / "full" / "data" / "all_patterns.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(data_path, low_memory=False)
    patterns = df['meter_pattern'].value_counts().to_dict()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False)
    
    print(f"  已保存 (full): {output_path}")
    print(f"  格律模式数: {len(patterns)}")
    
    # 导出 sample 版本
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_sample.csv"
    output_path = project_root / "gh-pages" / "sample" / "data" / "all_patterns.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(data_path, low_memory=False)
    patterns = df['meter_pattern'].value_counts().to_dict()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False)
    
    print(f"  已保存 (sample): {output_path}")
    print(f"  格律模式数: {len(patterns)}")
    
    df = pd.read_csv(data_path, low_memory=False)
    
    patterns = df['meter_pattern'].value_counts().to_dict()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False)
    
    print(f"  已保存: {output_path}")
    print(f"  格律模式数: {len(patterns)}")


def main():
    print("="*60)
    print("导出GitHub Pages数据 (优化版)")
    print("="*60)
    
    export_poetry_data_compressed()
    export_sample_poems()
    export_meter_stats()
    export_basic_stats()
    export_all_patterns()
    
    print("\n" + "="*60)
    print("导出完成！")
    print("="*60)


if __name__ == "__main__":
    main()
