"""
词相似度 FlatBuffers 生成脚本 v3 (单次扫描版本)

功能:
1. 自动编译 FlatBuffers schema (如果未生成或 schema 已更新)
2. 单次扫描：读取 v2 chunk 同时构建词表并转换为 v3 chunk
3. 使用 FlatBuffers 二进制格式，分 chunk 保存
4. 只提高阈值，不限制相似词数量

输入:
- results/word_similarity_v2/word_chunk_*.json
- flatbuffers/WordSimilarity.fbs (schema 文件)

输出:
- results/word_similarity_v3/word_chunk_*.bin
- results/word_similarity_v3/metadata.json
- results/word_similarity_v3/vocab.json (用于查询)

命令行:
python scripts/word_sim_v3.py

结果:
============================================================
完成!
  v2 大小: ~1816 MB
  v3 大小: 123.02 MB
  压缩比: 14.8x
    - 二进制: 121.59 MB
    - 词表: 1.43 MB
  Chunk数: 231
  词表大小: 88227
============================================================
"""

import json
import sys
import os
import subprocess
import hashlib
from pathlib import Path
import flatbuffers
from flatbuffers_generated.WordSimilarity.WordSimilarityFile import (
    WordSimilarityFile, WordSimilarityFileStart, WordSimilarityFileAddWords,
    WordSimilarityFileEnd, WordSimilarityFileStartWordsVector
)
from flatbuffers_generated.WordSimilarity.WordEntry import (
    WordEntry, WordEntryStart, WordEntryAddWordId, WordEntryAddFrequency,
    WordEntryAddSimilarWords, WordEntryEnd, WordEntryStartSimilarWordsVector
)
from flatbuffers_generated.WordSimilarity.SimilarWord import (
    SimilarWord, SimilarWordStart, SimilarWordAddWordId, SimilarWordAddSimilarity, SimilarWordEnd
)

print("=" * 60)
print("词相似度 FlatBuffers 生成 v3 (单次扫描)")
print("=" * 60)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
FLATC_SCHEMA_PATH = PROJECT_ROOT / "flatbuffers" / "WordSimilarity.fbs"
GENERATED_DIR = SCRIPT_DIR / "flatbuffers_generated"
INPUT_DIR = PROJECT_ROOT / "results" / "word_similarity_v2"
OUTPUT_DIR = PROJECT_ROOT / "results" / "word_similarity_v3"

SIMILARITY_THRESHOLD = 0.7


def get_file_hash(filepath):
    """计算文件 MD5 hash"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def check_flatc_available():
    """检查 flatc 编译器是否可用"""
    try:
        result = subprocess.run(
            ["flatc", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  找到 flatc: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def compile_schema():
    """
    自动编译 FlatBuffers schema
    如果 schema 未改变且已生成代码，则跳过编译
    """
    print("\n[0/3] 检查并编译 FlatBuffers schema...")

    if not FLATC_SCHEMA_PATH.exists():
        print(f"  错误: 找不到 schema 文件: {FLATC_SCHEMA_PATH}")
        print("  请确保 flatbuffers/WordSimilarity.fbs 存在")
        sys.exit(1)

    # 计算当前 schema hash
    current_schema_hash = get_file_hash(FLATC_SCHEMA_PATH)
    hash_file = GENERATED_DIR / ".schema_hash"

    # 检查是否需要重新编译
    need_compile = False
    if GENERATED_DIR.exists() and hash_file.exists():
        with open(hash_file, "r") as f:
            saved_hash = f.read().strip()
        if saved_hash == current_schema_hash:
            # 检查关键生成文件是否存在
            required_files = [
                GENERATED_DIR / "WordSimilarity" / "__init__.py",
                GENERATED_DIR / "WordSimilarity" / "WordSimilarityFile.py",
                GENERATED_DIR / "WordSimilarity" / "WordEntry.py",
                GENERATED_DIR / "WordSimilarity" / "SimilarWord.py",
            ]
            if all(f.exists() for f in required_files):
                print("  Schema 未改变，使用已生成的代码")
                need_compile = False

    if need_compile:
        print("  需要编译 schema...")

        if not check_flatc_available():
            print("  错误: 找不到 flatc 编译器")
            print("  请安装 FlatBuffers 编译器:")
            print("    - Windows: 从 https://github.com/google/flatbuffers/releases 下载")
            print("    - macOS: brew install flatbuffers")
            print("    - Linux: apt-get install flatbuffers-compiler 或从源码编译")
            print("\n  或者手动运行:")
            print(f"    flatc --python -o {SCRIPT_DIR} {FLATC_SCHEMA_PATH}")
            sys.exit(1)

        # 创建/清空生成目录
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)

        # 清理旧的生成文件
        import shutil
        if (GENERATED_DIR / "WordSimilarity").exists():
            shutil.rmtree(GENERATED_DIR / "WordSimilarity")

        # 编译 schema
        print(f"  编译: {FLATC_SCHEMA_PATH.name}")
        try:
            result = subprocess.run(
                ["flatc", "--python", "-o", str(SCRIPT_DIR), str(FLATC_SCHEMA_PATH)],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stderr:
                print(f"  警告: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"  编译失败: {e}")
            print(f"  stdout: {e.stdout}")
            print(f"  stderr: {e.stderr}")
            sys.exit(1)

        # 保存 schema hash
        with open(hash_file, "w") as f:
            f.write(current_schema_hash)

        print("  Schema 编译成功!")

    # 添加到 Python 路径
    sys.path.insert(0, str(GENERATED_DIR))


class VocabBuilder:
    """动态词表构建器，按出现顺序分配 word_id"""

    def __init__(self):
        self.vocab = {}  # word -> id
        self.next_id = 0

    def get_or_add(self, word):
        """获取 word_id，如果不存在则添加"""
        if word not in self.vocab:
            self.vocab[word] = self.next_id
            self.next_id += 1
        return self.vocab[word]

    def __len__(self):
        return len(self.vocab)


def process_and_save_chunk(chunk_data, vocab_builder, threshold, output_path):
    """
    处理单个 chunk 的数据，动态构建词表，保存为 FlatBuffers
    返回处理的条目数
    """
    # 过滤低相似度词，同时构建词表
    filtered_data = []
    for item in chunk_data:
        word = item[0]
        word_index = item[1]  # FastText 内部索引，非真实词频
        similar_words = item[2]

        # 过滤相似度
        filtered = [sw for sw in similar_words if sw[1] > threshold]
        if not filtered:
            continue

        # 获取或添加主词 id
        word_id = vocab_builder.get_or_add(word)

        # 获取或添加相似词 id
        similar_with_ids = []
        for sw_word, sw_sim in filtered:
            sw_id = vocab_builder.get_or_add(sw_word)
            similar_with_ids.append((sw_id, sw_sim))

        filtered_data.append((word_id, word_index, similar_with_ids))

    if not filtered_data:
        return 0

    # 构建 FlatBuffers
    builder = flatbuffers.Builder(1024 * 1024 * 50)

    entries = []
    for word_id, word_index, similar_words in filtered_data:
        similar_offsets = []
        for sw_id, sw_sim in similar_words:
            sw_sim_int = int(sw_sim * 10000)

            SimilarWordStart(builder)
            SimilarWordAddWordId(builder, sw_id)
            SimilarWordAddSimilarity(builder, sw_sim_int)
            similar_offsets.append(SimilarWordEnd(builder))

        WordEntryStartSimilarWordsVector(builder, len(similar_offsets))
        for offset in reversed(similar_offsets):
            builder.PrependUOffsetTRelative(offset)
        similar_vec = builder.EndVector()

        WordEntryStart(builder)
        WordEntryAddWordId(builder, word_id)
        WordEntryAddFrequency(builder, word_index)  # 存储 FastText 内部索引
        WordEntryAddSimilarWords(builder, similar_vec)
        entries.append(WordEntryEnd(builder))

    WordSimilarityFileStartWordsVector(builder, len(entries))
    for offset in reversed(entries):
        builder.PrependUOffsetTRelative(offset)
    words_vec = builder.EndVector()

    WordSimilarityFileStart(builder)
    WordSimilarityFileAddWords(builder, words_vec)
    file_offset = WordSimilarityFileEnd(builder)

    builder.Finish(file_offset)

    # 保存到文件
    with open(output_path, 'wb') as f:
        f.write(builder.Output())

    return len(filtered_data)


def convert_all_chunks_single_pass(threshold, output_dir):
    """
    单次扫描：读取 v2 chunk，动态构建词表，立即写入 v3 chunk
    """
    print(f"\n[1/3] 单次扫描转换 chunk (阈值>{threshold})...")

    output_dir.mkdir(parents=True, exist_ok=True)

    chunk_files = sorted(INPUT_DIR.glob("word_chunk_*.json"))
    total_chunks = len(chunk_files)

    vocab_builder = VocabBuilder()
    processed_count = 0
    skipped_count = 0
    total_words = 0

    print(f"  共 {total_chunks} 个 chunk 待处理")

    for chunk_idx, chunk_file in enumerate(chunk_files):
        if chunk_idx % 20 == 0 or chunk_idx == total_chunks - 1:
            print(f"  处理进度: [{chunk_idx+1}/{total_chunks}] 词表大小: {len(vocab_builder)}")

        # 读取单个 v2 chunk
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)

        total_words += len(chunk_data)

        # 处理并保存 v3 chunk
        output_path = output_dir / f"word_chunk_{chunk_idx:04d}.bin"
        valid_count = process_and_save_chunk(chunk_data, vocab_builder, threshold, output_path)

        if valid_count == 0:
            skipped_count += 1
            # 删除空文件（如果有）
            if output_path.exists():
                output_path.unlink()
        else:
            processed_count += 1

    print(f"  转换完成: {processed_count} 个 chunk 已生成, {skipped_count} 个为空被跳过")
    print(f"  最终词表大小: {len(vocab_builder)}")

    return vocab_builder, total_words, processed_count


def save_vocab(vocab_builder, output_path):
    """保存词表"""
    print("\n[2/3] 保存词表...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vocab_builder.vocab, f, ensure_ascii=False)

    print(f"  词表已保存: {output_path} ({len(vocab_builder)} 个词)")


def save_metadata(total_words, total_chunks, threshold, vocab_size, output_path):
    """保存元数据"""
    print("\n[3/3] 保存元数据...")

    metadata = {
        "total_words": total_words,
        "total_chunks": total_chunks,
        "vocab_size": vocab_size,
        "similarity_threshold": threshold,
        "format": "flatbuffers",
        "file_pattern": "word_chunk_*.bin",
        "vocab": "vocab.json",
        "description": "FlatBuffers 二进制格式，每 chunk 独立文件 (单次扫描生成)",
        "similarity_unit": 0.0001
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  元数据已保存: {output_path}")


def main():
    print(f"Schema: {FLATC_SCHEMA_PATH}")
    print(f"输入: {INPUT_DIR}")
    print(f"输出: {OUTPUT_DIR}")
    print(f"相似度阈值: >{SIMILARITY_THRESHOLD}")

    # 步骤 0: 编译 schema
    compile_schema()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 步骤 1: 单次扫描，读取 v2 同时构建词表并写入 v3
    vocab_builder, total_words, total_chunks = convert_all_chunks_single_pass(
        SIMILARITY_THRESHOLD, OUTPUT_DIR
    )

    # 步骤 2: 保存词表
    vocab_path = OUTPUT_DIR / "vocab.json"
    save_vocab(vocab_builder, vocab_path)

    # 计算输出大小
    bin_size = sum(
        os.path.getsize(f) / 1024 / 1024
        for f in OUTPUT_DIR.glob("word_chunk_*.bin")
    )
    vocab_size = os.path.getsize(vocab_path) / 1024 / 1024
    total_size = bin_size + vocab_size

    # 步骤 3: 保存元数据
    metadata_path = OUTPUT_DIR / "metadata.json"
    save_metadata(total_words, total_chunks, SIMILARITY_THRESHOLD, len(vocab_builder), metadata_path)

    v2_size = 1816

    print(f"\n" + "=" * 60)
    print("完成!")
    print(f"  v2 大小: ~{v2_size} MB")
    print(f"  v3 大小: {total_size:.2f} MB")
    print(f"  压缩比: {v2_size/total_size:.1f}x")
    print(f"    - 二进制: {bin_size:.2f} MB")
    print(f"    - 词表: {vocab_size:.2f} MB")
    print(f"  Chunk数: {total_chunks}")
    print(f"  词表大小: {len(vocab_builder)}")
    print("=" * 60)


if __name__ == "__main__":
    print("HI")
    main()
