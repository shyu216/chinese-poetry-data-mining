"""
词相似度 FlatBuffers 生成脚本 v3

功能:
1. 读取 v2 紧凑 JSON 数据
2. 使用 FlatBuffers 二进制格式
3. 只提高阈值，不限制相似词数量

输入:
- results/word_similarity_v2/word_chunk_*.json

输出:
- results/word_similarity_v3/word_similarity.bin
- results/word_similarity_v3/metadata.json
- results/word_similarity_v3/vocab.json (用于查询)

命令行:
python scripts/generate_flatbuffers.py
"""

import json
from pathlib import Path
from collections import Counter
import flatbuffers
from typing import List, Dict

INPUT_DIR = Path("results/word_similarity_v2")
OUTPUT_DIR = Path("results/word_similarity_v3")
SIMILARITY_THRESHOLD = 0.7


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


def build_vocab(data):
    """构建词表"""
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

    return vocab


def create_flatbuffers(data, vocab, threshold, output_path):
    """创建 FlatBuffers 二进制文件"""
    print(f"\n创建 FlatBuffers (阈值>{threshold})...")

    import WordSimilarity

    builder = flatbuffers.Builder(1024 * 1024 * 100)

    word_to_idx = {w: i for i, w in enumerate(sorted(vocab.keys(), key=lambda x: vocab[x]))}

    similar_words_list = []
    for item in data:
        word = item[0]
        freq = item[1]
        similar_words = item[2]

        filtered = [sw for sw in similar_words if sw[1] > threshold]

        if not filtered:
            continue

        word_id = vocab[word]

        similar_word_offsets = []
        for sw in filtered:
            sw_word = sw[0]
            sw_sim = int(sw[1] * 10000)

            sw_word_offset = builder.CreateString(sw_word)

            WordSimilarity.SimilarWordStart(builder)
            WordSimilarity.SimilarWordAddWordId(builder, vocab.get(sw_word, 0))
            WordSimilarity.SimilarWordAddSimilarity(builder, sw_sim)
            similar_word_offsets.append(WordSimilarity.SimilarWordEnd(builder))

        WordSimilarity.WordEntryStartSimilarWordsVector(builder, len(similar_word_offsets))
        for offset in reversed(similar_word_offsets):
            builder.PrependUOffsetTRelative(offset)
        similar_words_vec = builder.EndVector(builder, len(similar_word_offsets))

        WordSimilarity.WordEntryStart(builder)
        WordSimilarity.WordEntryAddWordId(builder, word_id)
        WordSimilarity.WordEntryAddFrequency(builder, freq)
        WordSimilarity.WordEntryAddSimilarWords(builder, similar_words_vec)
        similar_words_list.append(WordSimilarity.WordEntryEnd(builder))

    WordSimilarity.WordSimilarityFileStartWordsVector(builder, len(similar_words_list))
    for offset in reversed(similar_words_list):
        builder.PrependUOffsetTRelative(offset)
    words_vec = builder.EndVector(builder, len(similar_words_list))

    WordSimilarity.WordSimilarityFileStart(builder)
    WordSimilarity.WordSimilarityFileAddWords(builder, words_vec)
    file_offset = WordSimilarity.WordSimilarityFileEnd(builder)

    builder.Finish(file_offset)

    with open(output_path, 'wb') as f:
        f.write(builder.Output())

    print(f"  已保存: {output_path}")
    return len(similar_words_list)


def save_metadata(total_words, threshold, output_path):
    """保存元数据"""
    metadata = {
        "total_words": total_words,
        "similarity_threshold": threshold,
        "format": "flatbuffers",
        "file": "word_similarity.bin",
        "vocab": "vocab.json",
        "description": "FlatBuffers 二进制格式",
        "similarity_unit": 0.0001
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  元数据已保存: {output_path}")


def main():
    print("=" * 60)
    print("词相似度 FlatBuffers 生成 v3")
    print("=" * 60)
    print(f"输入: {INPUT_DIR}")
    print(f"输出: {OUTPUT_DIR}")
    print(f"相似度阈值: >{SIMILARITY_THRESHOLD}")

    all_data = load_all_data()

    vocab = build_vocab(all_data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bin_path = OUTPUT_DIR / "word_similarity.bin"
    total_words = create_flatbuffers(all_data, vocab, SIMILARITY_THRESHOLD, bin_path)

    metadata_path = OUTPUT_DIR / "metadata.json"
    save_metadata(total_words, SIMILARITY_THRESHOLD, metadata_path)

    import os
    bin_size = os.path.getsize(bin_path) / 1024 / 1024
    vocab_size = os.path.getsize(OUTPUT_DIR / "vocab.json") / 1024 / 1024
    total_size = bin_size + vocab_size

    print(f"\n" + "=" * 60)
    print("完成!")
    print(f"  v2 大小: ~1816 MB")
    print(f"  v3 大小: {total_size:.2f} MB")
    print(f"  压缩比: {1816/total_size:.1f}x")
    print(f"    - 二进制: {bin_size:.2f} MB")
    print(f"    - 词表: {vocab_size:.2f} MB")
    print(f"  有效词数: {total_words}")
    print("=" * 60)


if __name__ == "__main__":
    main()
