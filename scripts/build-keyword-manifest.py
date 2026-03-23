"""
构建关键词到 chunk 的映射表，实现 O(1) 查询
输出到 wordcount_v2 目录，与词频数据一起管理

借鉴 useWordcountV2.ts 和 useVerifiedCache.ts 的实现模式:
1. 生成轻量级的 keyword_manifest.json (只包含映射关系)
2. 支持 hash 验证（通过 hash-manifest.json）
3. 详细的日志输出

输入: results/keyword_index/keyword_*.json
输出: results/wordcount_v2/keyword_manifest.json

映射表结构:
{
  "version": "v2",
  "timestamp": "2026-03-22T...",
  "statistics": {
    "total_keywords": 893638,
    "total_chunks": 894
  },
  "keywordToChunk": {
    "春风": 45,
    "明月": 67,
    ...
  }
}
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple


def calculate_file_hash(file_path: Path) -> str:
    """计算文件的 SHA256 hash"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]  # 取前16位足够用于验证


def build_keyword_manifest(input_dir: Path, output_dir: Path) -> Tuple[Path, Dict]:
    """
    构建关键词到 chunk 的映射表
    
    借鉴 useWordcountV2 的模式:
    - 轻量级 manifest 文件
    - 详细的统计信息
    - 支持 hash 验证
    """
    keyword_to_chunk: Dict[str, int] = {}
    total_keywords = 0
    
    chunk_files = sorted([f for f in input_dir.glob("keyword_*.json") if f.stem != "keyword_manifest"])
    print(f"[build-keyword-manifest] 找到 {len(chunk_files)} 个 chunk 文件")
    
    for chunk_file in chunk_files:
        # 从文件名提取 chunk_id
        chunk_id = int(chunk_file.stem.split('_')[1])
        
        # 读取 chunk 文件
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
        
        # 记录每个关键词对应的 chunk_id
        for keyword in chunk_data.keys():
            keyword_to_chunk[keyword] = chunk_id
            total_keywords += 1
        
        if (chunk_id + 1) % 100 == 0 or chunk_id == len(chunk_files) - 1:
            print(f"  已处理 {chunk_id + 1}/{len(chunk_files)} chunks, {total_keywords} 个关键词")
    
    # 构建 manifest（借鉴 useWordcountV2 的结构）
    manifest = {
        "version": "v2",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_keywords": total_keywords,
            "total_chunks": len(chunk_files)
        },
        "keywordToChunk": keyword_to_chunk
    }
    
    # 保存 manifest
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = output_dir / "keyword_manifest.json"
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(',', ':'))
    
    # 计算文件大小和 hash
    file_size = manifest_file.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    file_hash = calculate_file_hash(manifest_file)
    
    print(f"\n{'='*60}")
    print(f"[build-keyword-manifest] 构建完成!")
    print(f"  总关键词数: {total_keywords:,}")
    print(f"  总 chunk 数: {len(chunk_files)}")
    print(f"  映射表大小: {file_size_mb:.2f} MB")
    print(f"  文件 Hash: {file_hash}")
    print(f"  输出文件: {manifest_file}")
    print(f"{'='*60}")
    
    return manifest_file, manifest


def update_hash_manifest(manifest_file: Path, output_dir: Path):
    """
    更新 hash-manifest.json，添加 keyword_manifest.json 的 hash
    借鉴 useVerifiedCache 的 hash 验证机制
    """
    hash_manifest_path = output_dir / "hash-manifest.json"
    
    # 读取现有的 hash manifest
    if hash_manifest_path.exists():
        with open(hash_manifest_path, 'r', encoding='utf-8') as f:
            hash_manifest = json.load(f)
    else:
        hash_manifest = {
            "version": "1.0",
            "generatedAt": int(datetime.now().timestamp()),
            "files": {}
        }
    
    # 计算 keyword_manifest.json 的 hash
    file_hash = calculate_file_hash(manifest_file)
    
    # 更新 hash manifest
    hash_manifest["files"]["wordcount_v2/keyword_manifest.json"] = file_hash
    hash_manifest["generatedAt"] = int(datetime.now().timestamp())
    
    with open(hash_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(hash_manifest, f, ensure_ascii=False, indent=2)
    
    print(f"[build-keyword-manifest] 更新 hash-manifest.json: wordcount_v2/keyword_manifest.json = {file_hash}")


def test_lookup_performance(manifest: Dict, test_keywords: list):
    """
    测试查询性能
    借鉴 useKeywordIndex 的 O(1) 查询模式
    """
    keyword_to_chunk = manifest["keywordToChunk"]
    
    print(f"\n[build-keyword-manifest] 测试查询性能 (测试 {len(test_keywords)} 个关键词):")
    
    import time
    start = time.perf_counter()
    
    found = 0
    not_found = 0
    for keyword in test_keywords:
        if keyword in keyword_to_chunk:
            found += 1
        else:
            not_found += 1
    
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"  找到: {found}, 未找到: {not_found}")
    print(f"  总耗时: {elapsed:.4f} ms")
    print(f"  平均每次查询: {elapsed/len(test_keywords):.6f} ms")
    print(f"  复杂度: O(1) - Map 直接查找")


def compare_with_linear_search(manifest: Dict, test_keywords: list):
    """
    对比 O(1) 和 O(N) 的性能差异
    """
    keyword_to_chunk = manifest["keywordToChunk"]
    total_chunks = manifest["statistics"]["total_chunks"]
    
    print(f"\n[build-keyword-manifest] 性能对比 (O(1) vs O(N)):")
    
    import time
    
    # O(1) 查询
    start = time.perf_counter()
    for keyword in test_keywords:
        _ = keyword_to_chunk.get(keyword)
    o1_time = (time.perf_counter() - start) * 1000
    
    # 模拟 O(N) 线性搜索（假设平均需要遍历一半的 chunks）
    # 实际上线性搜索还需要加载每个 chunk 文件，这里只计算查找时间
    avg_chunks_to_search = total_chunks / 2
    simulated_on_time = o1_time * avg_chunks_to_search
    
    print(f"  O(1) 查询时间: {o1_time:.4f} ms ({len(test_keywords)} 次)")
    print(f"  模拟 O(N) 时间: ~{simulated_on_time:.0f} ms (平均搜索 {avg_chunks_to_search:.0f} chunks)")
    print(f"  性能提升: ~{simulated_on_time / o1_time:.0f}x")


if __name__ == "__main__":
    input_dir = Path("results/keyword_index")
    output_dir = Path("results/wordcount_v2")
    
    print("="*60)
    print("构建关键词到 chunk 的映射表 (O(1) 查询优化)")
    print("="*60)
    
    # 构建 manifest
    manifest_file, manifest = build_keyword_manifest(input_dir, output_dir)
    
    # 更新 hash manifest（支持 useVerifiedCache 的验证机制）
    update_hash_manifest(manifest_file, output_dir)
    
    # 性能测试
    test_keywords = ["春风", "明月", "有", "一", "人", "山", "水", "花", "天", "云"]
    test_lookup_performance(manifest, test_keywords)
    
    # 性能对比
    compare_with_linear_search(manifest, test_keywords)
    
    print(f"\n{'='*60}")
    print("完成! 前端可以使用 useKeywordIndex.ts 的 searchKeywordOptimized() 进行 O(1) 查询")
    print(f"{'='*60}")
