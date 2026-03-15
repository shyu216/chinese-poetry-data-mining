"""
多线程词频统计脚本 - Python版 (测试版)
"""

import csv
import multiprocessing as mp
from pathlib import Path
from collections import Counter
import time
import os
import psutil

def process_chunk(file_path):
    """处理单个chunk文件"""
    count = Counter()
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            words_str = row.get('words', '')
            if words_str:
                words = words_str.split()
                count.update(words)
    return count


def main():
    input_dir = Path("results/preprocessed")
    output_file = Path("results/wordcount_python/wordfreq.csv")

    print("=" * 60)
    print("Python 多进程 WordCount")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出文件: {output_file}")

    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))
    print(f"找到 {len(chunk_files)} 个 chunk 文件")

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024

    start = time.time()
    start_time_ns = time.perf_counter_ns()

    with mp.Pool(processes=8) as pool:
        results = pool.map(process_chunk, chunk_files)

    merged = Counter()
    for result in results:
        merged.update(result)

    end_time = time.time()
    end_time_ns = time.perf_counter_ns()

    total_words = sum(merged.values())
    unique_words = len(merged)

    mem_after = process.memory_info().rss / 1024 / 1024
    elapsed = end_time - start
    elapsed_ns = end_time_ns - start_time_ns

    print(f"\n统计完成!")
    print(f"总词数: {total_words:,}")
    print(f"不同词数: {unique_words:,}")

    sorted_items = merged.most_common()

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'count', 'rank'])
        for rank, (word, count) in enumerate(sorted_items, 1):
            writer.writerow([word, count, rank])

    print(f"\n完成! 耗时: {elapsed:.2f}秒")
    print(f"内存使用: {mem_before:.1f} MB -> {mem_after:.1f} MB (峰值约 {mem_after:.1f} MB)")
    print(f"输出: {output_file}")

    return {
        "total_words": total_words,
        "unique_words": unique_words,
        "elapsed": elapsed,
        "elapsed_ns": elapsed_ns,
        "mem_mb": mem_after
    }


if __name__ == "__main__":
    result = main()
    print(f"\n>>> RESULT: {result}")
