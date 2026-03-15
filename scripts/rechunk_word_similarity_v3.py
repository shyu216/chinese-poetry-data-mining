"""
高效词相似度分块 v3

优化方案：
1. 提高相似度阈值 (0.5 → 0.7)
2. 限制每个词最多保留 20 个相似词
3. 用整数 ID 代替字符串（建立词表）
4. 相似度乘以10000转为整数

目标: 1.8GB → 300MB

输入:
- results/word_similarity_v2/word_chunk_*.json (或从v1)

输出:
- results/word_similarity_v3/
- results/word_similarity_v3/vocab.json (词表)
- results/word_similarity_v3/word_chunk_*.json

命令行:
python scripts/rechunk_word_similarity_v3.py
"""

import json
from pathlib import Path
from collections import Counter

INPUT_DIR = Path("results/word_similarity_v2")
OUTPUT_DIR = Path("results/word_similarity_v3")
CHUNK_SIZE = 500

SIMILARITY_THRESHOLD = 0.7
MAX_SIMILAR_WORDS = 20


def load_all_data():
    """加载所有v2数据"""
    print("=" * 60)
    print("加载 v2 数据")
    print("=" * 60)

    all_data = []
    chunk_files = sorted(INPUT_DIR.glob("word_chunk_*.json"))

    for i, chunk_file in enumerate(chunk_files):
        if i % 20 == 0:
            print(f"  进度: [{i}/{len(chunk_files)}]")

        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_data.extend(data)

    print(f"  总词数: {len(all_data)}")
    return all_data


def build_vocab_and_compact(data, threshold, max_words):
    """构建词表并转换为超紧凑格式"""
    print("\n" + "=" * 60)
    print("构建词表")
    print("=" * 60)

    word_counter = Counter()

    for item in data:
        word = item[0]
        similar_words = item[2]

        word_counter[word] += 1
        for sw in similar_words:
            word_counter[sw[0]] += 1

    vocab = {word: idx for idx, (word, _) in enumerate(word_counter.most_common())}
    print(f"  词表大小: {len(vocab)}")

    vocab_path = OUTPUT_DIR / "vocab.json"
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False)
    print(f"  词表已保存: {vocab_path}")

    print(f"\n转换为紧凑格式 (阈值>{threshold}, 最多{max_words}个相似词)...")

    result = []
    for item in data:
        word = item[0]
        freq = item[1]
        similar_words = item[2]

        filtered = [
            (sw[0], sw[1])
            for sw in similar_words
            if sw[1] > threshold
        ][:max_words]

        if filtered:
            word_id = vocab[word]
            similar_ids = [
                [vocab[sw[0]], int(sw[1] * 10000)]
                for sw in filtered
            ]

            result.append([word_id, freq, similar_ids])

    print(f"  有效词数: {len(result)}")
    return result, vocab


def save_chunks(data, output_dir, chunk_size):
    """分块保存"""
    print("\n" + "=" * 60)
    print("分块保存")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    total_chunks = (len(data) + chunk_size - 1) // chunk_size

    for i in range(total_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, len(data))
        chunk = data[start:end]

        chunk_path = output_dir / f"word_chunk_{i:04d}.json"
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False)

    print(f"  保存 {total_chunks} 个 chunk 文件")

    metadata = {
        "total_words": len(data),
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "max_similar_words": MAX_SIMILAR_WORDS,
        "format": "ultra-compact",
        "description": "[word_id(int), freq(int), [[similar_id(int), similarity_int(int)], ...]]",
        "similarity_unit": 0.0001
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  元数据已保存: {metadata_path}")
    return total_chunks


def main():
    print("=" * 60)
    print("高效词相似度分块 v3")
    print("=" * 60)
    print(f"输入: {INPUT_DIR}")
    print(f"输出: {OUTPUT_DIR}")
    print(f"相似度阈值: >{SIMILARITY_THRESHOLD}")
    print(f"最多相似词: {MAX_SIMILAR_WORDS}")

    all_data = load_all_data()

    compact_data, vocab = build_vocab_and_compact(
        all_data,
        SIMILARITY_THRESHOLD,
        MAX_SIMILAR_WORDS
    )

    total_chunks = save_chunks(compact_data, OUTPUT_DIR, CHUNK_SIZE)

    import os
    total_size = sum(
        os.path.getsize(f) / 1024 / 1024
        for f in OUTPUT_DIR.glob("*.json")
    )

    vocab_size = os.path.getsize(OUTPUT_DIR / "vocab.json") / 1024 / 1024

    print(f"\n" + "=" * 60)
    print("完成!")
    print(f"  v2 大小: ~1816 MB")
    print(f"  v3 大小: {total_size:.2f} MB")
    print(f"  压缩比: {1816/total_size:.1f}x")
    print(f"  词表: {vocab_size:.2f} MB")
    print(f"  Chunk数: {total_chunks}")
    print("=" * 60)


if __name__ == "__main__":
    main()
