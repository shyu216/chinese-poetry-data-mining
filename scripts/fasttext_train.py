"""
FastText 词向量训练脚本

功能:
1. 读取 results/preprocessed/poems_chunk_*.csv 文件
2. 使用 jieba 分词结果 (words 字段) 训练 FastText 模型
3. 保存词向量模型和相关文件

输入:
- results/preprocessed/poems_chunk_*.csv

输出:
- results/fasttext/poetry.model (二进制模型)
- results/fasttext/vocab.json (词表)
- results/fasttext/metadata.json (元数据)

命令行:
python scripts/fasttext_train.py
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from gensim.models import FastText


VECTOR_SIZE = 100
MIN_COUNT = 5
WINDOW = 5
EPOCHS = 10


def load_chunk_file(chunk_path: Path):
    """加载单个chunk文件，返回词列表"""
    poems = []
    with open(chunk_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            words_str = row.get('words', '')
            if words_str:
                words = words_str.split()
                poems.append(words)
    return poems


def save_metadata(output_dir: Path, stats: dict):
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
    output_dir = Path("results/fasttext")

    print("=" * 60)
    print("FastText 训练脚本启动")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"向量维度: {VECTOR_SIZE}")
    print(f"最小词频: {MIN_COUNT}")
    print(f"窗口大小: {WINDOW}")
    print(f"训练轮数: {EPOCHS}")

    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))
    print(f"找到 {len(chunk_files)} 个chunk文件")

    if not chunk_files:
        print("错误: 未找到chunk文件")
        return

    all_sentences = []
    total_poems = 0

    print("\n" + "=" * 60)
    print("加载分词数据")
    print("=" * 60)

    for idx, chunk_file in enumerate(chunk_files, 1):
        if idx % 50 == 0:
            print(f"进度: [{idx}/{len(chunk_files)}] 已加载 {total_poems} 首诗")

        poems = load_chunk_file(chunk_file)
        all_sentences.extend(poems)
        total_poems += len(poems)

    print(f"\n>>> 加载完成!")
    print(f"  总诗数: {total_poems}")
    print(f"  句子数: {len(all_sentences)}")

    print("\n" + "=" * 60)
    print("训练 FastText 模型")
    print("=" * 60)

    model = FastText(
        sentences=all_sentences,
        vector_size=VECTOR_SIZE,
        window=WINDOW,
        min_count=MIN_COUNT,
        epochs=EPOCHS,
        workers=4,
        sg=0
    )

    vocab_size = len(model.wv)
    print(f"  词表大小: {vocab_size}")

    print("\n" + "=" * 60)
    print("保存模型和元数据")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    model.save(str(output_dir / "poetry.model"))
    print(f"  模型已保存: {output_dir / 'poetry.model'}")

    with open(output_dir / "vocab.json", 'w', encoding='utf-8') as f:
        json.dump(list(model.wv.key_to_index.keys()), f, ensure_ascii=False)
    print(f"  词表已保存: {output_dir / 'vocab.json'}")

    save_metadata(output_dir, {
        "vector_size": VECTOR_SIZE,
        "min_count": MIN_COUNT,
        "window": WINDOW,
        "epochs": EPOCHS,
        "vocab_size": vocab_size,
        "total_poems": total_poems
    })
    print(f"  元数据已保存: {output_dir / 'metadata.json'}")

    print("\n" + "=" * 60)
    print("完成!")
    print(f"  词表大小: {vocab_size}")
    print(f"  向量维度: {VECTOR_SIZE}")
    print(f"  输出目录: {output_dir}")
    print("=" * 60)

    print("\n>>> 可用示例:")
    print(f"  找相似词: model.wv.most_similar('明月')")
    print(f"  计算相似度: model.wv.similarity('明月', '圆月')")


if __name__ == "__main__":
    main()
