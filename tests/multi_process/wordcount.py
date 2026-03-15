"""
多线程词频统计脚本

功能:
1. 使用 multiprocessing 多进程统计词频
2. 输出词频CSV文件
"""

import csv
import multiprocessing as mp
from pathlib import Path
from collections import Counter
import time


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
    output_file = Path("results/wordcount/wordfreq.csv")

    print("=" * 60)
    print("多进程 WordCount")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出文件: {output_file}")

    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))
    print(f"找到 {len(chunk_files)} 个 chunk 文件")

    start = time.time()

    with mp.Pool(processes=8) as pool:
        results = pool.map(process_chunk, chunk_files)

    merged = Counter()
    for result in results:
        merged.update(result)

    total_words = sum(merged.values())
    unique_words = len(merged)

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

    elapsed = time.time() - start
    print(f"\n完成! 耗时: {elapsed:.2f}秒")
    print(f"输出: {output_file}")


if __name__ == "__main__":
    main()
