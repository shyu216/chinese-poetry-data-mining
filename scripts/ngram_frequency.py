"""
N-gram 统计脚本

功能:
1. 读取 results/preprocessed/poems_chunk_*.csv 文件
2. 对每首诗的 words 字段进行 N-gram 提取
3. 生成 1-gram, 2-gram, 3-gram 索引
4. 创建 N-gram 到诗 hash 的映射索引

输入:
- results/preprocessed/poems_chunk_*.csv (需要先运行 word_frequency.py 生成 words 字段)

输出:
- results/ngram_index/ngram_1_*.json (1-gram 索引文件)
- results/ngram_index/ngram_2_*.json (2-gram 索引文件)
- results/ngram_index/ngram_3_*.json (3-gram 索引文件)
- results/ngram_index/metadata.json (元数据)
- results/ngram_index/checkpoint.json (中间态记录)

命令行:
python scripts/ngram_frequency.py

示例:
- 诗句 "明月几时有" 的分词结果: "明月 几时 有"
- 1-gram: 明月, 几时, 有
- 2-gram: 明月几时, 几时有
- 3-gram: 明月几时有

观测:
- 词汇丰富但组合爆炸

- 33万首诗只有89万不重复的词
- 但2词组合高达728万，3词组合高达1020万
- 说明诗词的组合非常丰富，符合语言学的齐夫定律
- 3-gram > 2-gram 的原因

- 短诗只能形成少量 N-gram
- 长诗可以形成大量 N-gram
- 组合空间巨大导致3-gram数量反而更多
- 实际应用价值

- 1-gram: 基础关键词检索
- 2-gram: 常用短语/意象组合
- 3-gram: 完整诗意片段、名句
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional
from datetime import datetime
import os


CHUNK_SIZE = 1000
N_VALUES = [1, 2, 3]


def load_checkpoint(output_dir: Path) -> Optional[Dict]:
    """加载中间态checkpoint"""
    checkpoint_file = output_dir / "checkpoint.json"
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_checkpoint(output_dir: Path, data: Dict):
    """保存中间态checkpoint"""
    checkpoint_file = output_dir / "checkpoint.json"
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_chunk_file(chunk_path: Path) -> List[Dict[str, str]]:
    """加载单个chunk文件"""
    poems = []
    with open(chunk_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            poems.append(row)
    return poems


def extract_ngrams(words: List[str], n: int) -> List[str]:
    """从词列表中提取N-gram"""
    if len(words) < n:
        return []
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ''.join(words[i:i+n])
        ngrams.append(ngram)
    return ngrams


def build_ngram_index(poems: List[Dict[str, str]], n: int, progress_callback=None) -> Dict[str, Set[str]]:
    """构建N-gram到诗hash的索引"""
    ngram_index = defaultdict(set)
    total = len(poems)

    for idx, poem in enumerate(poems):
        poem_hash = poem.get('hash', '')
        if not poem_hash:
            continue

        words_str = poem.get('words', '')
        if not words_str:
            continue

        words = words_str.split()
        ngrams = extract_ngrams(words, n)

        for ngram in ngrams:
            ngram_index[ngram].add(poem_hash)

        if progress_callback and (idx + 1) % 10000 == 0:
            progress_callback(idx + 1, total)

    return ngram_index


def save_ngram_index(ngram_index: Dict[str, Set[str]], output_dir: Path, prefix: str, chunk_size: int = 1000) -> int:
    """保存N-gram索引，返回chunk数量"""
    output_dir.mkdir(parents=True, exist_ok=True)

    ngrams = sorted(ngram_index.keys())
    total_chunks = (len(ngrams) + chunk_size - 1) // chunk_size

    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min((chunk_idx + 1) * chunk_size, len(ngrams))
        chunk_ngrams = ngrams[start_idx:end_idx]

        chunk_data = {}
        for ngram in chunk_ngrams:
            chunk_data[ngram] = sorted(list(ngram_index[ngram]))

        chunk_file = output_dir / f"{prefix}_{chunk_idx:04d}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)

        print(f"  [{prefix}] [{chunk_idx+1}/{total_chunks}] 保存 {len(chunk_ngrams)} 个 -> {chunk_file.name}")

    return total_chunks


def save_metadata(output_dir: Path, stats: Dict):
    """保存元数据"""
    metadata = {
        "version": "v1",
        "timestamp": datetime.now().isoformat(),
        "statistics": stats
    }

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def main():
    input_dir = Path("results/preprocessed")
    output_dir = Path("results/ngram_index")

    print("=" * 60)
    print("N-gram 统计脚本启动")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"N值: {N_VALUES}")
    print(f"Chunk大小: {CHUNK_SIZE}")

    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))
    print(f"找到 {len(chunk_files)} 个chunk文件")

    if not chunk_files:
        print("错误: 未找到chunk文件")
        return

    checkpoint = load_checkpoint(output_dir)
    if checkpoint:
        print(f"\n>>> 检测到中间态记录!")
        print(f"  已完成: {checkpoint.get('completed_ngrams', [])}")
        print(f"  最后处理chunk: {checkpoint.get('last_chunk_idx', -1)}")
        print(f"  时间: {checkpoint.get('timestamp', '')}")
    else:
        checkpoint = {"completed_ngrams": [], "last_chunk_idx": -1, "stats": {}}

    all_poems = []
    print("\n" + "=" * 60)
    print("加载chunk文件")
    print("=" * 60)

    for idx, chunk_file in enumerate(chunk_files, 1):
        print(f"[{idx}/{len(chunk_files)}] 加载: {chunk_file.name}")
        poems = load_chunk_file(chunk_file)
        all_poems.extend(poems)

    print(f"\n>>> 加载完成，总计 {len(all_poems)} 首诗")

    stats = {
        "total_poems": len(all_poems),
        "total_chunks": len(chunk_files),
        "ngram_counts": {}
    }

    for n in N_VALUES:
        prefix = f"ngram_{n}"
        print("\n" + "=" * 60)
        print(f"构建 {n}-gram 索引")
        print("=" * 60)

        if prefix in checkpoint.get("completed_ngrams", []):
            print(f">>> {n}-gram 已完成，跳过")
            stats["ngram_counts"][n] = checkpoint["stats"].get(f"ngram_{n}_count", 0)
            continue

        def progress(current, total):
            print(f"  进度: {current}/{total} ({current*100//total}%)")

        ngram_index = build_ngram_index(all_poems, n, progress_callback=progress)
        print(f"  {n}-gram 数量: {len(ngram_index)}")

        print("\n保存索引文件...")
        chunk_count = save_ngram_index(ngram_index, output_dir, prefix, CHUNK_SIZE)

        checkpoint["completed_ngrams"].append(prefix)
        checkpoint["stats"][f"ngram_{n}_count"] = len(ngram_index)
        checkpoint["stats"][f"ngram_{n}_chunks"] = chunk_count
        save_checkpoint(output_dir, checkpoint)

        stats["ngram_counts"][n] = len(ngram_index)

        print(f">>> {n}-gram 完成!")

    checkpoint["completed_ngrams"] = N_VALUES
    save_checkpoint(output_dir, checkpoint)

    print("\n" + "=" * 60)
    print("保存元数据")
    print("=" * 60)

    save_metadata(output_dir, stats)
    print(f"元数据已保存")

    checkpoint_file = output_dir / "checkpoint.json"
    if checkpoint_file.exists():
        os.remove(checkpoint_file)
        print("中间态记录已清除")

    print("\n" + "=" * 60)
    print("完成!")
    print(f"  总记录数: {stats['total_poems']}")
    for n in N_VALUES:
        print(f"  {n}-gram 数量: {stats['ngram_counts'].get(n, 0)}")
    print(f"  输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
