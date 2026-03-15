"""
对比 Python 和 Go 版本词频统计结果
"""
import csv
from pathlib import Path


def load_wordcount(filepath):
    """加载词频文件"""
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row['word']
            count = int(row['count'])
            data[word] = count
    return data


def main():
    py_file = Path("results/wordcount_python/wordfreq.csv")
    go_file = Path("results/wordcount_go/wordfreq_go.csv")

    print("=" * 60)
    print("词频统计结果对比")
    print("=" * 60)

    print("\n加载 Python 版本结果...")
    py_data = load_wordcount(py_file)
    print(f"  总词数: {sum(py_data.values()):,}")
    print(f"  不同词数: {len(py_data):,}")

    print("\n加载 Go 版本结果...")
    go_data = load_wordcount(go_file)
    print(f"  总词数: {sum(go_data.values()):,}")
    print(f"  不同词数: {len(go_data):,}")

    print("\n对比结果...")

    py_words = set(py_data.keys())
    go_words = set(go_data.keys())

    only_py = py_words - go_words
    only_go = go_words - py_words

    print(f"\n仅 Python 有: {len(only_py)} 个词")
    print(f"仅 Go 有: {len(only_go)} 个词")

    if only_py:
        print("\n仅 Python 有的词示例 (前10个):")
        for word in list(only_py)[:10]:
            print(f"  '{word}': {py_data.get(word, 0)}")

    if only_go:
        print("\n仅 Go 有的词示例 (前10个):")
        for word in list(only_go)[:10]:
            print(f"  '{word}': {go_data.get(word, 0)}")

    common_words = py_words & go_words
    print(f"\n共有词数: {len(common_words):,}")

    diff_count = 0
    max_diff_word = None
    max_diff_val = 0

    for word in common_words:
        py_val = py_data[word]
        go_val = go_data[word]
        if py_val != go_val:
            diff_count += 1
            diff = abs(py_val - go_val)
            if diff > max_diff_val:
                max_diff_val = diff
                max_diff_word = word

    print(f"词频不同的词数: {diff_count}")

    if diff_count > 0:
        print(f"最大差异词: '{max_diff_word}' (Python: {py_data[max_diff_word]}, Go: {go_data[max_diff_word]})")
    else:
        print("结果完全一致!")

    py_top10 = sorted(py_data.items(), key=lambda x: x[1], reverse=True)[:10]
    go_top10 = sorted(go_data.items(), key=lambda x: x[1], reverse=True)[:10]

    print("\n" + "=" * 60)
    print("Top 10 对比")
    print("=" * 60)
    print(f"{'排名':<6}{'Python':<20}{'Go':<20}")
    print("-" * 46)
    for i, ((py_word, py_cnt), (go_word, go_cnt)) in enumerate(zip(py_top10, go_top10), 1):
        print(f"{i:<6}{py_word}({py_cnt:,})    {go_word}({go_cnt:,})")


if __name__ == "__main__":
    main()
