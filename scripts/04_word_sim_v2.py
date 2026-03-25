"""
script: 04_word_sim_v2.py
stage: P3-向量模型
artifact: 相似词紧凑分块
purpose: 将 v1 相似词数据重排为紧凑结构并分块存储。
inputs:
- results/word_similarity/word_similarity_summary.json
outputs:
- results/word_similarity_v2
depends_on:
- word_sim_v1.py
develop_date: 2026-03-15
last_modified_date: 2026-03-15
"""
import json
from pathlib import Path
INPUT_FILE = Path("results/word_similarity/word_similarity_summary.json")
OUTPUT_DIR = Path("results/word_similarity_v2")
CHUNK_SIZE = 500
def convert_to_compact(data):
    """转换为紧凑格式"""
    result = []
    for item in data:
        word = item["word"]
        freq = item["frequency"]
        similar = [
            [sw["word"], sw["similarity"]]
            for sw in item["similar_words"]
        ]
        result.append([word, freq, similar])
    return result
def save_compact_chunks(data, output_dir, chunk_size):
    """分块保存"""
    output_dir.mkdir(parents=True, exist_ok=True)
    total_chunks = (len(data) + chunk_size - 1) // chunk_size
    for i in range(total_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, len(data))
        chunk = data[start:end]
        chunk_path = output_dir / f"word_chunk_{i:04d}.json"
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False)
        print(f"  已保存: {chunk_path.name} ({len(chunk)} 条)")
    metadata = {
        "total_words": len(data),
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "format": "compact",
        "description": "每条格式: [word, frequency, [[word, similarity], ...]]"
    }
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"\n元数据已保存: {metadata_path}")
    return total_chunks
def main():
    print("=" * 60)
    print("高效词相似度分块")
    print("=" * 60)
    print(f"输入: {INPUT_FILE}")
    print(f"输出: {OUTPUT_DIR}")
    print(f"每chunk词数: {CHUNK_SIZE}")
    print("\n读取数据...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  总词数: {len(data)}")
    print("\n转换格式...")
    compact_data = convert_to_compact(data)
    print(f"  转换完成")
    print("\n分块保存...")
    total_chunks = save_compact_chunks(compact_data, OUTPUT_DIR, CHUNK_SIZE)
    import os
    original_size = os.path.getsize(INPUT_FILE) / 1024 / 1024
    new_size = sum(
        os.path.getsize(f) / 1024 / 1024
        for f in OUTPUT_DIR.glob("word_chunk_*.json")
    )
    print(f"\n" + "=" * 60)
    print("完成!")
    print(f"  原始大小: {original_size:.2f} MB")
    print(f"  新大小: {new_size:.2f} MB")
    print(f"  压缩比: {original_size/new_size:.1f}x")
    print(f"  Chunk数: {total_chunks}")
    print("=" * 60)
if __name__ == "__main__":
    main()
