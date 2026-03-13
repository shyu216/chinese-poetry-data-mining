"""
Web数据导出器

功能:
1. 将Silver层数据分片导出
2. 每片 ≤ 10MB
3. 生成 manifest.json
4. 支持增量导出

输出:
- data/output/web/poems_chunk_*.json
- data/output/web/manifest.json
"""

import json
import math
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd

from src.config import get_settings


def estimate_size(data: Dict[str, Any]) -> int:
    """估算数据大小（字节）"""
    return len(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def split_into_chunks(
    poems: List[Dict[str, Any]],
    max_chunk_size_mb: int = 10
) -> List[List[Dict[str, Any]]]:
    """将诗词分片
    
    Args:
        poems: 诗词列表
        max_chunk_size_mb: 每片最大MB
        
    Returns:
        List[List[Dict]]: 分片后的列表
    """
    max_size_bytes = max_chunk_size_mb * 1024 * 1024
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for poem in poems:
        poem_size = estimate_size(poem)
        
        # 如果当前片已满，开始新片
        if current_size + poem_size > max_size_bytes and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
        
        current_chunk.append(poem)
        current_size += poem_size
    
    # 添加最后一片
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def export_poems(df: pd.DataFrame, output_dir: Path, max_chunk_size_mb: int = 10):
    """导出诗词数据
    
    Args:
        df: 诗词数据框
        output_dir: 输出目录
        max_chunk_size_mb: 每片最大MB
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 转换为字典列表
    poems = df.to_dict("records")
    
    # 分片
    chunks = split_into_chunks(poems, max_chunk_size_mb)
    
    print(f"分片数量: {len(chunks)}")
    
    # 保存每片
    chunk_files = []
    for i, chunk in enumerate(chunks):
        filename = f"poems_chunk_{i:03d}.json"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        
        file_size = filepath.stat().st_size
        chunk_files.append({
            "filename": filename,
            "index": i,
            "count": len(chunk),
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2)
        })
        
        print(f"  {filename}: {len(chunk)} 首, {file_size / 1024:.1f} KB")
    
    return chunk_files


def create_manifest(
    output_dir: Path,
    chunk_files: List[Dict[str, Any]],
    stats: Dict[str, Any]
):
    """创建清单文件
    
    Args:
        output_dir: 输出目录
        chunk_files: 分片文件信息
        stats: 统计信息
    """
    manifest = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "total_poems": sum(c["count"] for c in chunk_files),
        "total_chunks": len(chunk_files),
        "chunks": chunk_files,
        "stats": stats
    }
    
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n清单: {manifest_path}")
    print(f"  总诗词: {manifest['total_poems']}")
    print(f"  总分片: {manifest['total_chunks']}")
    
    return manifest


def calculate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """计算统计信息"""
    return {
        "total_poems": len(df),
        "total_authors": df["author"].nunique(),
        "total_dynasties": df["dynasty"].nunique(),
        "genre_distribution": df["genre"].value_counts().to_dict(),
        "poem_type_distribution": df["poem_type"].value_counts().to_dict(),
        "regular_ratio": df["is_regular"].mean() if "is_regular" in df.columns else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Web数据导出")
    parser.add_argument(
        "--data",
        choices=["sample", "full"],
        default="sample",
        help="处理数据集类型"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成"
    )
    args = parser.parse_args()
    
    settings = get_settings()
    
    # 路径
    silver_dir = settings.data.silver_dir
    output_dir = settings.data.output_dir / "web"
    
    # 输入文件
    input_csv = silver_dir / "v2_poems_structured.csv"
    
    # 检查输入
    if not input_csv.exists():
        print(f"错误: 输入文件不存在 {input_csv}")
        print("请先运行: python scripts/steps/02_structure.py")
        return
    
    # 检查是否已存在
    manifest_path = output_dir / "manifest.json"
    if not args.force and manifest_path.exists():
        print(f"已存在: {manifest_path}，使用 --force 重新生成")
        return
    
    print("=" * 50)
    print("Web数据导出")
    print("=" * 50)
    
    # 加载数据
    print(f"\n加载数据: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"记录数: {len(df)}")
    
    # 计算统计
    print("\n计算统计...")
    stats = calculate_stats(df)
    
    # 导出分片
    print(f"\n导出分片 (最大 {settings.analysis.max_chunk_size_mb}MB/片)...")
    chunk_files = export_poems(df, output_dir, settings.analysis.max_chunk_size_mb)
    
    # 创建清单
    print("\n创建清单...")
    manifest = create_manifest(output_dir, chunk_files, stats)
    
    print("\n" + "=" * 50)
    print("完成!")
    print(f"输出目录: {output_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()
