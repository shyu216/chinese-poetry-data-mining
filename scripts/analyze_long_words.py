"""
分析 jieba 分词结果中 >3 字符的词统计
"""

import csv
from pathlib import Path
from collections import Counter


def main():
    input_dir = Path("results/preprocessed")
    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))

    print(f"找到 {len(chunk_files)} 个chunk文件\n")

    long_word_counter = Counter()
    total_words = 0
    processed = 0

    for idx, chunk_file in enumerate(chunk_files, 1):
        if idx % 50 == 0:
            print(f"进度: [{idx}/{len(chunk_files)}] 已处理 {processed} 首诗")

        with open(chunk_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                words_str = row.get('words', '')
                if words_str:
                    words = words_str.split()
                    for word in words:
                        total_words += 1
                        if len(word) > 5:
                            long_word_counter[word] += 1

                processed += 1

    print(f"\n{'='*60}")
    print(f"统计完成!")
    print(f"总词数: {total_words}")
    print(f">3 字符词数: {sum(long_word_counter.values())}")
    print(f">3 字符词种类: {len(long_word_counter)}")
    print(f"\n{'='*60}")
    print("前10个最常见的 >3 字符词:")
    print(f"{'排名':<4} {'词':<15} {'出现次数':<10}")
    print("-" * 35)

    for i, (word, count) in enumerate(long_word_counter.most_common(10), 1):
        print(f"{i:<4} {word:<15} {count:<10}")


if __name__ == "__main__":
    main()
