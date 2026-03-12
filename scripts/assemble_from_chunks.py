#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从分片重新组装完整数据文件
用于GitHub Actions或本地恢复
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import pandas as pd
from pathlib import Path


def assemble_poems_from_chunks():
    """从分片组装完整的诗词JSON"""
    print("从分片组装诗词数据...")
    
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "data" / "github_pages" / "data" / "poems_manifest.json"
    output_path = project_root / "data" / "github_pages" / "data" / "poems.json"
    
    if not manifest_path.exists():
        print(f"  ⚠️ Manifest不存在: {manifest_path}")
        return False
    
    # 读取manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    print(f"  总分片数: {manifest['chunks']}")
    print(f"  总诗词数: {manifest['total']}")
    
    # 组装所有分片
    all_poems = []
    data_dir = manifest_path.parent
    
    for chunk_info in manifest['files']:
        chunk_file = data_dir / chunk_info['file']
        if not chunk_file.exists():
            print(f"  ⚠️ 分片不存在: {chunk_file}")
            continue
        
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
        
        all_poems.extend(chunk_data)
        print(f"  ✅ 已加载: {chunk_info['file']} ({chunk_info['count']}首)")
    
    # 保存完整文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_poems, f, ensure_ascii=False)
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ 已保存: {output_path} ({file_size_mb:.2f}MB, {len(all_poems)}首)")
    
    return True


def assemble_structure_from_chunks():
    """从分片组装完整的结构CSV"""
    print("\n从分片组装结构数据...")
    
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "data" / "github_pages" / "data" / "structure_manifest.json"
    output_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    
    if not manifest_path.exists():
        print(f"  ⚠️ Manifest不存在: {manifest_path}")
        return False
    
    # 读取manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    print(f"  总分片数: {manifest['chunks']}")
    print(f"  总行数: {manifest['total']}")
    
    # 组装所有分片
    all_dfs = []
    data_dir = manifest_path.parent
    
    for chunk_info in manifest['files']:
        chunk_file = data_dir / chunk_info['file']
        if not chunk_file.exists():
            print(f"  ⚠️ 分片不存在: {chunk_file}")
            continue
        
        df = pd.read_csv(chunk_file, low_memory=False)
        all_dfs.append(df)
        print(f"  ✅ 已加载: {chunk_info['file']} ({chunk_info['count']}行)")
    
    # 合并并保存
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df.to_csv(output_path, index=False, encoding='utf-8')
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ 已保存: {output_path} ({file_size_mb:.2f}MB, {len(full_df)}行)")
    
    return True


def main():
    print("="*60)
    print("从分片组装完整数据")
    print("="*60)
    
    # 组装诗词数据
    poems_success = assemble_poems_from_chunks()
    
    # 组装结构数据
    structure_success = assemble_structure_from_chunks()
    
    print("\n" + "="*60)
    if poems_success and structure_success:
        print("组装完成！")
    else:
        print("部分组装失败，请检查分片文件")
    print("="*60)


if __name__ == "__main__":
    main()
