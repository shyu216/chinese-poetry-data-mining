"""
script: 03_wordcount_v2.py
stage: P2-特征构建
artifact: 词频分层分块数据
purpose: 将 wordfreq.csv 转换为按 rank 分层的 chunk JSON。
inputs:
- results/wordcount/wordfreq.csv
outputs:
- results/wordcount_v2
depends_on:
- wordcount.py
develop_date: 2026-03-15
last_modified_date: 2026-03-15
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple
INPUT_FILE = Path("results/wordcount/wordfreq.csv")
OUTPUT_DIR = Path("results/wordcount_v2")
# Chunk大小配置
CHUNK_CONFIG = [
    (1, 10000, 1000),      # rank 1-10000, 每chunk 1000词
    (10001, 100000, 10000), # rank 10001-100000, 每chunk 10000词
    (100001, float('inf'), 50000), # rank 100001+, 每chunk 50000词
]
def load_wordfreq() -> List[Tuple[str, int, int]]:
    """加载词频数据 [(word, count, rank), ...]"""
    print("加载词频数据...")
    data = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append((
                row['word'],
                int(row['count']),
                int(row['rank'])
            ))
    print(f"  共 {len(data):,} 个词")
    return data
def get_chunk_size(rank: int) -> int:
    """根据rank获取chunk大小"""
    for start, end, size in CHUNK_CONFIG:
        if start <= rank <= end:
            return size
    return CHUNK_CONFIG[-1][2]
def create_chunks(data: List[Tuple[str, int, int]]) -> Tuple[List[Dict], int]:
    """
    创建chunks
    返回: (meta列表, chunk数量)
    """
    print("\n创建chunks...")
    chunks_meta = []
    chunk_index = 0
    i = 0
    while i < len(data):
        rank = data[i][2]
        chunk_size = get_chunk_size(rank)
        # 获取当前chunk的数据
        chunk_data = data[i:i + chunk_size]
        end_i = i + len(chunk_data)
        # 紧凑格式: [[word, count, rank], ...]
        compact_data = [[word, count, r] for word, count, r in chunk_data]
        # 写入chunk文件
        chunk_file = f"chunk_{chunk_index:04d}.json"
        chunk_path = OUTPUT_DIR / chunk_file
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(compact_data, f, ensure_ascii=False, separators=(',', ':'))
        # 记录meta
        chunks_meta.append({
            "file": chunk_file,
            "index": chunk_index,
            "start_rank": chunk_data[0][2],
            "end_rank": chunk_data[-1][2],
            "count": len(chunk_data),
            "start_word": chunk_data[0][0],
            "end_word": chunk_data[-1][0],
            "total_count": sum(c for _, c, _ in chunk_data)  # 总出现次数
        })
        if chunk_index % 10 == 0 or end_i >= len(data):
            print(f"  进度: chunk_{chunk_index:04d}.json ({chunk_data[0][2]}-{chunk_data[-1][2]})")
        chunk_index += 1
        i = end_i
    return chunks_meta, chunk_index
def create_meta_json(chunks_meta: List[Dict], total_words: int):
    """创建meta.json"""
    print("\n创建meta.json...")
    meta = {
        "version": "2.0",
        "format": "compact",  # [[word, count, rank], ...]
        "total_words": total_words,
        "total_chunks": len(chunks_meta),
        "chunks": chunks_meta,
        # 快速查找索引
        "lookup": {
            "by_rank": {
                "min": chunks_meta[0]["start_rank"],
                "max": chunks_meta[-1]["end_rank"]
            },
            "by_count": {
                "max": chunks_meta[0]["total_count"],
                "min": chunks_meta[-1]["total_count"]
            }
        }
    }
    meta_path = OUTPUT_DIR / "meta.json"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {meta_path}")
def print_stats(chunks_meta: List[Dict]):
    """打印统计信息"""
    print("\n" + "=" * 60)
    print("WordCount v2 统计")
    print("=" * 60)
    total_size = 0
    for chunk in chunks_meta:
        chunk_path = OUTPUT_DIR / chunk["file"]
        size = chunk_path.stat().st_size
        total_size += size
    print(f"总词数: {sum(c['count'] for c in chunks_meta):,}")
    print(f"总chunk数: {len(chunks_meta)}")
    print(f"总大小: {total_size / 1024 / 1024:.2f} MB")
    print(f"平均chunk大小: {total_size / len(chunks_meta) / 1024:.1f} KB")
    print(f"\nchunk分布:")
    for i, chunk in enumerate(chunks_meta[:3]):
        print(f"  {chunk['file']}: rank {chunk['start_rank']}-{chunk['end_rank']}, {chunk['count']}词")
    print("  ...")
    for chunk in chunks_meta[-2:]:
        print(f"  {chunk['file']}: rank {chunk['start_rank']}-{chunk['end_rank']}, {chunk['count']}词")
def verify_chunks():
    """验证chunk数据完整性"""
    print("\n" + "=" * 60)
    print("验证数据完整性")
    print("=" * 60)
    # 加载meta
    with open(OUTPUT_DIR / "meta.json", 'r', encoding='utf-8') as f:
        meta = json.load(f)
    total_words = 0
    prev_end_rank = 0
    for chunk_info in meta["chunks"]:
        chunk_path = OUTPUT_DIR / chunk_info["file"]
        with open(chunk_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 验证数量
        assert len(data) == chunk_info["count"], f"{chunk_info['file']} count mismatch"
        # 验证rank连续性
        assert data[0][2] == chunk_info["start_rank"], f"{chunk_info['file']} start_rank mismatch"
        assert data[-1][2] == chunk_info["end_rank"], f"{chunk_info['file']} end_rank mismatch"
        # 验证rank连续
        if prev_end_rank > 0:
            assert data[0][2] == prev_end_rank + 1, f"Rank不连续: {prev_end_rank} -> {data[0][2]}"
        prev_end_rank = data[-1][2]
        total_words += len(data)
    print(f"  ✓ 所有chunk验证通过")
    print(f"  ✓ 总词数: {total_words:,}")
    print(f"  ✓ Rank范围: 1-{prev_end_rank}")
def demo_read():
    """演示如何读取"""
    print("\n" + "=" * 60)
    print("读取演示")
    print("=" * 60)
    # 加载meta
    with open(OUTPUT_DIR / "meta.json", 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print(f"总chunk数: {meta['total_chunks']}")
    # 示例1: 读取高频词chunk (前1000)
    chunk_0_path = OUTPUT_DIR / meta["chunks"][0]["file"]
    with open(chunk_0_path, 'r', encoding='utf-8') as f:
        top_words = json.load(f)
    print(f"\nTop 5高频词:")
    for word, count, rank in top_words[:5]:
        print(f"  [{rank}] {word}: {count}")
    # 示例2: 根据rank查找词
    target_rank = 5000
    for chunk in meta["chunks"]:
        if chunk["start_rank"] <= target_rank <= chunk["end_rank"]:
            chunk_path = OUTPUT_DIR / chunk["file"]
            with open(chunk_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 在chunk内查找
            idx = target_rank - chunk["start_rank"]
            word, count, rank = data[idx]
            print(f"\nRank {target_rank}: {word} ({count}次)")
            break
def main():
    print("=" * 60)
    print("WordCount v2 - 分chunk处理")
    print("=" * 60)
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # 加载数据
    data = load_wordfreq()
    # 创建chunks
    chunks_meta, total_chunks = create_chunks(data)
    # 创建meta.json
    create_meta_json(chunks_meta, len(data))
    # 打印统计
    print_stats(chunks_meta)
    # 验证
    verify_chunks()
    # 演示
    demo_read()
    print("\n" + "=" * 60)
    print("完成!")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)
if __name__ == "__main__":
    main()
