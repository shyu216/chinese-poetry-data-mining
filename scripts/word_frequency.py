"""
词频统计脚本

功能:
1. 读取 results/preprocessed/poems_chunk_*.csv 文件
2. 对每首诗进行分词统计
3. 在每个 chunk 文件中添加 words 字段
4. 创建关键词到诗 hash 的映射索引

输入:
- results/preprocessed/poems_chunk_*.csv

输出:
- results/preprocessed/poems_chunk_*.csv (更新后的文件，添加words字段)
- results/keyword_index/keyword_*.json (关键词索引文件)
- results/keyword_index/metadata.json (元数据)

命令行:
============================================================
完成!
  总记录数: 332712
  总chunk数: 333
  关键词数量: 893638
  索引chunk数: 894
  输出目录: results\keyword_index
============================================================
"""

import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from datetime import datetime
import jieba.posseg as pseg


def load_chunk_file(chunk_path: Path) -> List[Dict[str, str]]:
    """加载单个chunk文件"""
    poems = []
    with open(chunk_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            poems.append(row)
    return poems


def save_chunk_file(chunk_path: Path, poems: List[Dict[str, str]]):
    """保存chunk文件"""
    if not poems:
        return
    
    fieldnames = list(poems[0].keys())
    with open(chunk_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(poems)


def tokenize_poem(content: str) -> List[Tuple[str, str]]:
    """对诗词内容进行分词（使用jieba.posseg）"""
    if not content:
        return []
    
    words_with_pos = []
    for word, flag in pseg.cut(content):
        if word.strip():
            words_with_pos.append((word, flag))
    return words_with_pos


def count_words(words_with_pos: List[Tuple[str, str]]) -> str:
    """返回纯词列表格式"""
    words = [word for word, flag in words_with_pos]
    return " ".join(words)


def process_poem(poem: Dict[str, str]) -> Dict[str, str]:
    """处理单首诗词，添加词频统计"""
    content = poem.get('sentences_simplified', '')
    
    words_with_pos = tokenize_poem(content)
    words_str = count_words(words_with_pos)
    
    poem['words'] = words_str
    
    return poem, words_str


def build_keyword_index(all_poems: List[Dict[str, str]]) -> Dict[str, Set[str]]:
    """构建关键词到诗hash的索引"""
    keyword_index = defaultdict(set)
    
    for poem in all_poems:
        poem_hash = poem.get('hash', '')
        if not poem_hash:
            continue
        
        try:
            words_str = poem.get('words', '')
            if words_str:
                words = words_str.split()
                for word in words:
                    keyword_index[word].add(poem_hash)
        except Exception:
            continue
    
    return keyword_index


def save_keyword_index(keyword_index: Dict[str, Set[str]], output_dir: Path, chunk_size: int = 1000):
    """保存关键词索引"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    keywords = sorted(keyword_index.keys())
    total_chunks = (len(keywords) + chunk_size - 1) // chunk_size
    
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min((chunk_idx + 1) * chunk_size, len(keywords))
        chunk_keywords = keywords[start_idx:end_idx]
        
        chunk_data = {}
        for keyword in chunk_keywords:
            chunk_data[keyword] = sorted(list(keyword_index[keyword]))
        
        chunk_file = output_dir / f"keyword_{chunk_idx:04d}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        if (chunk_idx + 1) % 10 == 0 or chunk_idx == total_chunks - 1:
            print(f"  [{chunk_idx+1}/{total_chunks}] 保存关键词索引 chunk {chunk_idx}: {len(chunk_keywords)} 个关键词 -> {chunk_file}")
    
    return total_chunks


def save_metadata(output_dir: Path, total_poems: int, total_chunks: int, keyword_count: int, index_chunks: int):
    """保存元数据"""
    metadata = {
        "version": "v1",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_poems": total_poems,
            "total_chunks": total_chunks,
            "total_keywords": keyword_count,
            "index_chunks": index_chunks
        }
    }
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def main():
    input_dir = Path("results/preprocessed")
    output_dir = Path("results/keyword_index")
    
    print("=" * 60)
    print("词频统计脚本启动")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    
    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))
    print(f"找到 {len(chunk_files)} 个chunk文件")
    
    if not chunk_files:
        print("错误: 未找到chunk文件")
        return
    
    all_poems = []
    total_processed = 0
    
    print("\n" + "=" * 60)
    print("处理chunk文件")
    print("=" * 60)
    
    for idx, chunk_file in enumerate(chunk_files, 1):
        print(f"\n[{idx}/{len(chunk_files)}] 处理: {chunk_file.name}")
        
        poems = load_chunk_file(chunk_file)
        print(f"  读取: {len(poems)} 条记录")
        
        processed_poems = []
        for poem in poems:
            processed_poem, word_count = process_poem(poem)
            processed_poems.append(processed_poem)
        
        save_chunk_file(chunk_file, processed_poems)
        print(f"  保存: {len(processed_poems)} 条记录（已添加words字段）")
        
        all_poems.extend(processed_poems)
        total_processed += len(processed_poems)
        
        if idx % 10 == 0:
            print(f"  累计处理: {total_processed} 条记录")
    
    print(f"\n>>> chunk文件处理完成!")
    print(f"  总记录数: {total_processed}")
    
    print("\n" + "=" * 60)
    print("构建关键词索引")
    print("=" * 60)
    
    keyword_index = build_keyword_index(all_poems)
    print(f"  关键词数量: {len(keyword_index)}")
    
    print("\n保存关键词索引...")
    index_chunks = save_keyword_index(keyword_index, output_dir, chunk_size=1000)
    
    print("\n保存元数据...")
    save_metadata(output_dir, total_processed, len(chunk_files), len(keyword_index), index_chunks)
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"  总记录数: {total_processed}")
    print(f"  总chunk数: {len(chunk_files)}")
    print(f"  关键词数量: {len(keyword_index)}")
    print(f"  索引chunk数: {index_chunks}")
    print(f"  输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
