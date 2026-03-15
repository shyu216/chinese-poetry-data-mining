"""
高频词相似词查找脚本

功能:
1. 加载 FastText 模型
2. 获取词表（按词频排序）
3. 查找每个词的相似词（相似度 > 阈值）
4. 分块输出结果

输入:
- results/fasttext/poetry.model

输出:
- results/word_similarity/word_similarity_summary.json
- results/word_similarity/word_chunk_*.json

命令行:
python scripts/find_word_similarity.py
"""

import json
from pathlib import Path
from datetime import datetime
from gensim.models import FastText

SIMILARITY_THRESHOLD = 0.5
CHUNK_SIZE = 1000

MODEL_PATH = Path("results/fasttext/poetry.model")
OUTPUT_DIR = Path("results/word_similarity")


def load_model():
    print("=" * 60)
    print("加载 FastText 模型")
    print("=" * 60)
    model = FastText.load(str(MODEL_PATH))
    print(f"  词表大小: {len(model.wv)}")
    return model


def get_sorted_vocab(model: FastText):
    print("\n" + "=" * 60)
    print("获取词表（按词频排序）")
    print("=" * 60)

    vocab_items = []
    for word in model.wv.key_to_index:
        count = model.wv.key_to_index[word]
        vocab_items.append((word, count))

    vocab_items.sort(key=lambda x: x[1], reverse=True)

    print(f"  总词数: {len(vocab_items)}")
    print(f"  Top 10: {[w[0] for w in vocab_items[:10]]}")

    return vocab_items


def find_similar_words(model: FastText, vocab_items, threshold=SIMILARITY_THRESHOLD):
    print("\n" + "=" * 60)
    print(f"查找相似词（阈值 > {threshold}）")
    print("=" * 60)

    results = []
    total = len(vocab_items)

    for idx, (word, freq) in enumerate(vocab_items, 1):
        if idx % 10000 == 0:
            print(f"  进度: [{idx}/{total}]")

        try:
            similar = model.wv.most_similar(word, topn=1000)

            similar_words = [
                {"word": w, "similarity": round(s, 4)}
                for w, s in similar if s > threshold and w != word
            ]

            if similar_words:
                results.append({
                    "word": word,
                    "frequency": freq,
                    "similar_words": similar_words
                })

        except Exception as e:
            continue

    print(f"  找到 {len(results)} 个词有相似词")

    return results


def save_results(results):
    print("\n" + "=" * 60)
    print("保存结果")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = OUTPUT_DIR / "word_similarity_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  已保存汇总: {summary_path}")
    print(f"  总词数: {len(results)}")

    chunk_size = CHUNK_SIZE
    for chunk_idx in range(0, len(results), chunk_size):
        batch = results[chunk_idx:chunk_idx + chunk_size]

        chunk_path = OUTPUT_DIR / f"word_chunk_{chunk_idx // chunk_size:04d}.json"
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)

    num_chunks = (len(results) + chunk_size - 1) // chunk_size
    print(f"  分块文件: {num_chunks} 个")


def main():
    print("=" * 60)
    print("高频词相似词查找")
    print("=" * 60)
    print(f"模型: {MODEL_PATH}")
    print(f"输出: {OUTPUT_DIR}")
    print(f"相似度阈值: >{SIMILARITY_THRESHOLD}")
    print(f"每chunk词数: {CHUNK_SIZE}")

    model = load_model()

    vocab_items = get_sorted_vocab(model)

    results = find_similar_words(model, vocab_items)

    save_results(results)

    print("\n" + "=" * 60)
    print("完成!")
    print(f"  输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
