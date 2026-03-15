"""
分析唯一词：最短且只出现一次的词
"""

import csv
from pathlib import Path
from collections import Counter


def main():
    input_dir = Path("results/preprocessed")
    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))

    print(f"找到 {len(chunk_files)} 个chunk文件\n")

    word_counter = Counter()
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
                        word_counter[word] += 1

                processed += 1

    print(f"\n{'='*60}")
    print(f"统计完成!")
    print(f"总词数: {total_words}")
    print(f"总词种类: {len(word_counter)}")
    print(f"{'='*60}\n")

    unique_words = {word: count for word, count in word_counter.items() if count == 1}
    print(f"只出现一次的词数量: {len(unique_words)}\n")

    length_groups = {}
    for word, count in unique_words.items():
        length = len(word)
        if length not in length_groups:
            length_groups[length] = []
        length_groups[length].append(word)

    print(f"{'='*60}")
    print("按词长分组统计:")
    print(f"{'='*60}")
    for length in sorted(length_groups.keys()):
        words = length_groups[length]
        print(f"  长度 {length}: {len(words)} 个词")

    print(f"\n{'='*60}")
    print("最短且只出现一次的词:")
    print(f"{'='*60}")

    min_length = min(length_groups.keys())
    shortest_unique = length_groups[min_length]
    print(f"\n长度 {min_length} 的唯一词共 {len(shortest_unique)} 个，前30个:")
    for i, word in enumerate(shortest_unique[:30], 1):
        print(f"  {i}. {word}")

    if min_length <= 2:
        print(f"\n{'='*60}")
        print("长度 2 的唯一词 (前50个):")
        print(f"{'='*60}")
        for i, word in enumerate(length_groups.get(2, [])[:50], 1):
            print(f"  {i}. {word}")

    print(f"\n{'='*60}")
    print("按词长分布统计:")
    print(f"{'='*60}")
    print(f"{'词长':<6} {'唯一词数':<10} {'占比':<10}")
    print("-" * 30)
    for length in sorted(length_groups.keys()):
        count = len(length_groups[length])
        ratio = count / len(unique_words) * 100
        print(f"{length:<6} {count:<10} {ratio:.2f}%")


if __name__ == "__main__":
    main()
