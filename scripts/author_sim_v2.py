"""
诗人数据分析脚本 v2 - FlatBuffers版本

功能:
1. 读取v1生成的JSON chunk文件
2. 转换为FlatBuffers格式流式写入
3. 支持流式读取FlatBuffers文件

输入:
- results/author/author_chunk_*.json (v1生成)

输出:
- results/author_v2/author_chunk_*.fbs (FlatBuffers格式)

命令行:
python scripts/author_sim_v2.py
"""

import csv
import json
import struct
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Iterator, Tuple
import flatbuffers

# 导入生成的FlatBuffers类
import sys
sys.path.insert(0, str(Path(__file__).parent / "flatbuffers_generated"))

from AuthorChunk.AuthorChunkFile import AuthorChunkFile, AuthorChunkFileStart, AuthorChunkFileAddAuthors, AuthorChunkFileAddChunkIndex, AuthorChunkFileAddTotalAuthors, AuthorChunkFileStartAuthorsVector, AuthorChunkFileEnd
from AuthorChunk.Author import Author, AuthorStart, AuthorAddAuthor, AuthorAddPoemCount, AuthorAddPoemIds, AuthorAddPoemTypeCounts, AuthorAddMeterPatterns, AuthorAddWordFrequency, AuthorAddSimilarAuthors, AuthorStartPoemIdsVector, AuthorStartPoemTypeCountsVector, AuthorStartMeterPatternsVector, AuthorStartWordFrequencyVector, AuthorStartSimilarAuthorsVector, AuthorEnd
from AuthorChunk.MeterPattern import MeterPattern, MeterPatternStart, MeterPatternAddPattern, MeterPatternAddCount, MeterPatternEnd
from AuthorChunk.SimilarAuthor import SimilarAuthor, SimilarAuthorStart, SimilarAuthorAddAuthor, SimilarAuthorAddSimilarity, SimilarAuthorEnd
from AuthorChunk.WordFreq import WordFreq, WordFreqStart, WordFreqAddWord, WordFreqAddCount, WordFreqEnd

# 路径配置
V1_INPUT_DIR = Path("results/author")
V2_OUTPUT_DIR = Path("results/author_v2")
CHUNK_SIZE = 50  # 每个chunk包含的作者数


class AuthorChunkWriter:
    """FlatBuffers格式作者数据写入器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_index = 0

    def _create_word_freq_vector(self, builder: flatbuffers.Builder, word_freqs: Dict[str, int]) -> int:
        """创建词频向量"""
        if not word_freqs:
            return 0

        # 创建所有WordFreq对象
        word_freq_offsets = []
        for word, count in word_freqs.items():
            word_str = builder.CreateString(word)
            WordFreqStart(builder)
            WordFreqAddWord(builder, word_str)
            WordFreqAddCount(builder, count)
            word_freq_offsets.append(WordFreqEnd(builder))

        # 创建向量
        AuthorStartWordFrequencyVector(builder, len(word_freq_offsets))
        for offset in reversed(word_freq_offsets):
            builder.PrependUOffsetTRelative(offset)
        return builder.EndVector()

    def _create_meter_pattern_vector(self, builder: flatbuffers.Builder, meter_patterns: List[Dict]) -> int:
        """创建格律模式向量"""
        if not meter_patterns:
            return 0

        pattern_offsets = []
        for mp in meter_patterns:
            pattern_str = builder.CreateString(mp['pattern'])
            MeterPatternStart(builder)
            MeterPatternAddPattern(builder, pattern_str)
            MeterPatternAddCount(builder, mp['count'])
            pattern_offsets.append(MeterPatternEnd(builder))

        AuthorStartMeterPatternsVector(builder, len(pattern_offsets))
        for offset in reversed(pattern_offsets):
            builder.PrependUOffsetTRelative(offset)
        return builder.EndVector()

    def _create_similar_author_vector(self, builder: flatbuffers.Builder, similar_authors: List[Dict]) -> int:
        """创建相似诗人向量"""
        if not similar_authors:
            return 0

        similar_offsets = []
        for sa in similar_authors:
            author_str = builder.CreateString(sa['author'])
            SimilarAuthorStart(builder)
            SimilarAuthorAddAuthor(builder, author_str)
            SimilarAuthorAddSimilarity(builder, sa['similarity'])
            similar_offsets.append(SimilarAuthorEnd(builder))

        AuthorStartSimilarAuthorsVector(builder, len(similar_offsets))
        for offset in reversed(similar_offsets):
            builder.PrependUOffsetTRelative(offset)
        return builder.EndVector()

    def _create_poem_ids_vector(self, builder: flatbuffers.Builder, poem_ids: List[str]) -> int:
        """创建诗ID向量"""
        if not poem_ids:
            return 0

        id_offsets = [builder.CreateString(pid) for pid in poem_ids]
        AuthorStartPoemIdsVector(builder, len(id_offsets))
        for offset in reversed(id_offsets):
            builder.PrependUOffsetTRelative(offset)
        return builder.EndVector()

    def _create_author(self, builder: flatbuffers.Builder, author_data: Dict) -> int:
        """创建单个Author对象"""
        # 创建字符串
        author_name = builder.CreateString(author_data['author'])

        # 创建向量
        poem_ids_vec = self._create_poem_ids_vector(builder, author_data.get('poem_ids', []))
        poem_type_vec = self._create_word_freq_vector(builder, author_data.get('poem_type_counts', {}))
        meter_vec = self._create_meter_pattern_vector(builder, author_data.get('meter_patterns', []))
        word_freq_vec = self._create_word_freq_vector(builder, author_data.get('word_frequency', {}))
        similar_vec = self._create_similar_author_vector(builder, author_data.get('similar_authors', []))

        # 创建Author对象
        AuthorStart(builder)
        AuthorAddAuthor(builder, author_name)
        AuthorAddPoemCount(builder, author_data.get('poem_count', 0))

        if poem_ids_vec:
            AuthorAddPoemIds(builder, poem_ids_vec)
        if poem_type_vec:
            AuthorAddPoemTypeCounts(builder, poem_type_vec)
        if meter_vec:
            AuthorAddMeterPatterns(builder, meter_vec)
        if word_freq_vec:
            AuthorAddWordFrequency(builder, word_freq_vec)
        if similar_vec:
            AuthorAddSimilarAuthors(builder, similar_vec)

        return AuthorEnd(builder)

    def write_chunk(self, authors: List[Dict], chunk_index: int) -> Path:
        """将作者列表写入FlatBuffers文件"""
        builder = flatbuffers.Builder(1024 * 1024)  # 1MB初始容量

        # 创建所有Author对象
        author_offsets = []
        for author_data in authors:
            offset = self._create_author(builder, author_data)
            author_offsets.append(offset)

        # 创建authors向量
        AuthorChunkFileStartAuthorsVector(builder, len(author_offsets))
        for offset in reversed(author_offsets):
            builder.PrependUOffsetTRelative(offset)
        authors_vec = builder.EndVector()

        # 创建AuthorChunkFile
        AuthorChunkFileStart(builder)
        AuthorChunkFileAddAuthors(builder, authors_vec)
        AuthorChunkFileAddChunkIndex(builder, chunk_index)
        AuthorChunkFileAddTotalAuthors(builder, len(authors))
        chunk_file = AuthorChunkFileEnd(builder)

        # 完成构建 (带文件标识符 "ATCH")
        builder.Finish(chunk_file, file_identifier=b'ATCH')

        # 写入文件
        output_path = self.output_dir / f"author_chunk_{chunk_index:04d}.fbs"
        with open(output_path, 'wb') as f:
            f.write(builder.Output())

        return output_path

    def write_from_v1_json(self, json_path: Path) -> Path:
        """从v1的JSON文件读取并转换为FlatBuffers"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 处理单作者和多作者格式
        if isinstance(data, list):
            authors = data
        else:
            authors = [data]

        output_path = self.write_chunk(authors, self.chunk_index)
        self.chunk_index += 1

        return output_path


class AuthorChunkReader:
    """FlatBuffers格式作者数据读取器"""

    def __init__(self, input_dir: Path):
        self.input_dir = input_dir

    def read_chunk(self, chunk_path: Path) -> Dict:
        """读取单个FlatBuffers chunk文件"""
        with open(chunk_path, 'rb') as f:
            buf = f.read()

        # 验证文件标识
        if not AuthorChunkFile.AuthorChunkFileBufferHasIdentifier(buf, 0):
            raise ValueError(f"Invalid file identifier: {chunk_path}")

        chunk = AuthorChunkFile.GetRootAs(buf, 0)

        authors = []
        for i in range(chunk.AuthorsLength()):
            author = chunk.Authors(i)
            authors.append(self._parse_author(author))

        return {
            'chunk_index': chunk.ChunkIndex(),
            'total_authors': chunk.TotalAuthors(),
            'authors': authors
        }

    def _parse_author(self, author: Author) -> Dict:
        """解析单个Author对象"""
        result = {
            'author': author.Author().decode('utf-8') if author.Author() else '',
            'poem_count': author.PoemCount(),
            'poem_ids': [],
            'poem_type_counts': {},
            'meter_patterns': [],
            'word_frequency': {},
            'similar_authors': []
        }

        # 诗ID
        for i in range(author.PoemIdsLength()):
            poem_id = author.PoemIds(i)
            if poem_id:
                result['poem_ids'].append(poem_id.decode('utf-8'))

        # 诗体类型计数
        for i in range(author.PoemTypeCountsLength()):
            wf = author.PoemTypeCounts(i)
            if wf:
                word = wf.Word().decode('utf-8') if wf.Word() else ''
                result['poem_type_counts'][word] = wf.Count()

        # 格律模式
        for i in range(author.MeterPatternsLength()):
            mp = author.MeterPatterns(i)
            if mp:
                pattern = mp.Pattern().decode('utf-8') if mp.Pattern() else ''
                result['meter_patterns'].append({
                    'pattern': pattern,
                    'count': mp.Count()
                })

        # 词频
        for i in range(author.WordFrequencyLength()):
            wf = author.WordFrequency(i)
            if wf:
                word = wf.Word().decode('utf-8') if wf.Word() else ''
                result['word_frequency'][word] = wf.Count()

        # 相似诗人
        for i in range(author.SimilarAuthorsLength()):
            sa = author.SimilarAuthors(i)
            if sa:
                similar_author = sa.Author().decode('utf-8') if sa.Author() else ''
                result['similar_authors'].append({
                    'author': similar_author,
                    'similarity': sa.Similarity()
                })

        return result

    def stream_all_authors(self) -> Iterator[Dict]:
        """流式读取所有作者数据"""
        chunk_files = sorted(self.input_dir.glob("author_chunk_*.fbs"))

        for chunk_path in chunk_files:
            chunk_data = self.read_chunk(chunk_path)
            for author in chunk_data['authors']:
                yield author

    def get_chunk_files(self) -> List[Path]:
        """获取所有chunk文件路径"""
        return sorted(self.input_dir.glob("author_chunk_*.fbs"))


def convert_v1_to_v2():
    """将v1 JSON数据转换为v2 FlatBuffers格式"""
    print("=" * 60)
    print("诗人数据 v1 -> v2 转换")
    print("=" * 60)

    writer = AuthorChunkWriter(V2_OUTPUT_DIR)

    # 查找所有v1 chunk文件
    v1_files = sorted(V1_INPUT_DIR.glob("author_chunk_*.json"))
    print(f"找到 {len(v1_files)} 个v1 chunk文件")

    total_authors = 0
    for idx, json_path in enumerate(v1_files, 1):
        output_path = writer.write_from_v1_json(json_path)

        # 统计作者数
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                num_authors = len(data)
            else:
                num_authors = 1
            total_authors += num_authors

        if idx % 10 == 0 or idx == len(v1_files):
            print(f"  进度: [{idx}/{len(v1_files)}] 已转换 {total_authors} 位诗人")

    print(f"\n>>> 转换完成!")
    print(f"  总作者数: {total_authors}")
    print(f"  输出目录: {V2_OUTPUT_DIR}")

    return total_authors


def verify_v2_data():
    """验证v2数据完整性"""
    print("\n" + "=" * 60)
    print("验证 v2 FlatBuffers 数据")
    print("=" * 60)

    reader = AuthorChunkReader(V2_OUTPUT_DIR)
    chunk_files = reader.get_chunk_files()

    print(f"找到 {len(chunk_files)} 个v2 chunk文件")

    total_authors = 0
    total_poems = 0

    for chunk_path in chunk_files:
        chunk_data = reader.read_chunk(chunk_path)
        total_authors += chunk_data['total_authors']

        for author in chunk_data['authors']:
            total_poems += author['poem_count']

    print(f"\n>>> 验证结果:")
    print(f"  总作者数: {total_authors}")
    print(f"  总诗数: {total_poems}")

    # 显示样本数据
    if chunk_files:
        sample_chunk = reader.read_chunk(chunk_files[0])
        if sample_chunk['authors']:
            sample = sample_chunk['authors'][0]
            print(f"\n>>> 样本数据 (第一位诗人):")
            print(f"  姓名: {sample['author']}")
            print(f"  诗数: {sample['poem_count']}")
            print(f"  诗体类型: {list(sample['poem_type_counts'].keys())[:5]}")
            print(f"  高频词: {list(sample['word_frequency'].keys())[:5]}")
            if sample['similar_authors']:
                print(f"  相似诗人: {sample['similar_authors'][0]}")

    return total_authors, total_poems


def stream_demo():
    """流式读取演示"""
    print("\n" + "=" * 60)
    print("流式读取演示")
    print("=" * 60)

    reader = AuthorChunkReader(V2_OUTPUT_DIR)

    count = 0
    poem_counts = []

    print("流式遍历所有作者...")
    for author in reader.stream_all_authors():
        count += 1
        poem_counts.append(author['poem_count'])

        if count <= 3:
            print(f"  [{count}] {author['author']}: {author['poem_count']}首诗")

    print(f"\n>>> 流式读取完成")
    print(f"  总作者数: {count}")
    print(f"  平均诗数: {sum(poem_counts)/len(poem_counts):.1f}")
    print(f"  最多诗数: {max(poem_counts)}")
    print(f"  最少诗数: {min(poem_counts)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='诗人数据v2 FlatBuffers工具')
    parser.add_argument('action', choices=['convert', 'verify', 'stream', 'all'],
                        default='all', nargs='?',
                        help='操作: convert=转换, verify=验证, stream=流式演示, all=全部')

    args = parser.parse_args()

    if args.action in ('convert', 'all'):
        convert_v1_to_v2()

    if args.action in ('verify', 'all'):
        verify_v2_data()

    if args.action in ('stream', 'all'):
        stream_demo()

    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
